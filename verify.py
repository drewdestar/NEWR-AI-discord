"""NEWR LABS membership verification gate for NEWR AI.

Rule (from the user): everyone may use the AI bot, BUT only if they
have joined the NEWR LABS server first.

This gate applies to AI commands only (see cogs/ai.py). Non-AI
commands (tools, fun, utility, ping roles, support-lite) are NOT
blocked by it.

How it works:
- The guild to check is GUILD_ID from the environment, falling back
  to the verified NEWR LABS guild ID 1465422166790242377 (the same
  value already in .env.example). No role ID is hardcoded; this is a
  plain guild-membership check, not a role check.
- Membership is checked with bot.get_guild(guild_id), then
  guild.get_member(user_id) from cache, falling back to
  guild.fetch_member(user_id) when the member is not cached.
  fetch_member needs the Server Members Intent: bot.py enables
  intents.members, and the same intent must be enabled in the
  Discord Developer Portal (Bot section) for this bot, otherwise
  fetch_member will fail and uncached members will be treated as
  not visible (see membership_status()).
- A non-member, or a user the bot cannot see in the guild at all
  (guild not found / bot not in the guild / fetch failed), gets the
  same ephemeral reply: join NEWR LABS first. No invite URL is ever
  invented: GUILD_INVITE_URL is included only if it is set in the
  environment; otherwise the reply says to ask the server owner
  for the invite link.
- No token, API key, password, or secret is read or stored here.
"""

import os

# Verified NEWR LABS guild ID (also the GUILD_ID in .env.example).
# Used only as a fallback when GUILD_ID is not set in the environment.
NEWR_LABS_GUILD_ID = 1465422166790242377
GUILD_NAME = "NEWR LABS"


def guild_id_int():
    """Return the guild ID to check, from GUILD_ID or the fallback."""
    raw = os.getenv("GUILD_ID")
    try:
        if raw:
            return int(raw)
    except ValueError:
        pass
    return NEWR_LABS_GUILD_ID


def join_message():
    """Ephemeral message for a user who is not a NEWR LABS member."""
    invite = os.getenv("GUILD_INVITE_URL", "").strip()
    if invite:
        return (
            f"You must join {GUILD_NAME} first to use the AI bot. "
            f"Join here: {invite} — then try the command again."
        )
    return (
        f"You must join {GUILD_NAME} first to use the AI bot. "
        "Please ask the server owner for the invite link, join the "
        "server, then try the command again."
    )


async def check_membership(bot, user_id):
    """Return (is_member, status) for user_id in the NEWR LABS guild.

    status is one of: "member", "not_member", "guild_not_found",
    "member_not_visible". The last two mean the bot could not see
    the guild/member at all, which the gate treats as not verified.
    """
    gid = guild_id_int()
    guild = bot.get_guild(gid) if bot is not None else None
    if guild is None:
        return False, "guild_not_found"
    member = guild.get_member(user_id)
    if member is not None:
        return True, "member"
    try:
        member = await guild.fetch_member(user_id)
    except Exception:
        # Covers NotFound (not a member), Forbidden (no Members
        # intent / permission) and HTTP errors alike: the bot
        # cannot confirm membership, so the gate does not open.
        return False, "member_not_visible"
    if member is not None:
        return True, "member"
    return False, "not_member"


async def membership_status(bot, user_id):
    """Human-readable membership status for /ai-status."""
    is_member, status = await check_membership(bot, user_id)
    if is_member:
        return "member"
    if status == "guild_not_found":
        return "unknown — bot cannot see NEWR LABS (check GUILD_ID and that the bot is in the server)"
    if status == "member_not_visible":
        return "not a member (or not visible to the bot — check the Server Members Intent)"
    return "not a member"


async def require_member(interaction):
    """Gate helper for AI commands.

    Returns True if the caller is a NEWR LABS member (command may
    proceed). Returns False and sends the ephemeral join message
    otherwise (command must stop). Safe to call before or after
    deferring: it uses followup if the interaction is already
    deferred/responded to.
    """
    bot = getattr(interaction, "client", None)
    is_member, _status = await check_membership(bot, interaction.user.id)
    if is_member:
        return True
    message = join_message()
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception:
        # If the ephemeral reply itself fails (e.g. interaction
        # already expired), the command still must not proceed.
        pass
    return False
