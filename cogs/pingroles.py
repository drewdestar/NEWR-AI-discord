"""Ping-role commands for the NEWR LABS server theme.

Verified server facts used here (names only, no IDs):
- The server already has bot roles NEWR AI and NEWR Support.
- Ping roles for AI models / prompts: GROK Ping, CHATGPT Ping,
  DEEPSEEK Ping, KIMI Ping, GEMINI Ping, New Prompt Ping, Prompt Share Ping.

Runtime detection is generic: roles are found by exact (case-insensitive)
name match in the guild where the command runs. No role ID is hardcoded,
so the same code works if Discord re-creates a role with the same name.
If a named role does not exist in the guild, the command says so instead
of failing silently.
"""
import discord
from discord import app_commands
from discord.ext import commands

PING_ROLES = [
    "GROK Ping", "CHATGPT Ping", "DEEPSEEK Ping", "KIMI Ping",
    "GEMINI Ping", "New Prompt Ping", "Prompt Share Ping",
]
BOT_ROLES = ["NEWR AI", "NEWR Support"]

def find_role(guild, name):
    if guild is None:
        return None
    lowered = name.lower()
    for r in guild.roles:
        if r.name.lower() == lowered:
            return r
    return None

def _need_guild(it):
    if it.guild is None:
        return "This command only works inside a server, not in DMs."
    return None

class PingRoles(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="pingroles", description="List all AI/prompt ping roles and whether you have each one")
    async def pingroles(self, it: discord.Interaction):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        lines = []
        for name in PING_ROLES:
            role = find_role(it.guild, name)
            if role is None:
                lines.append(f"❌ {name} — not found in this server")
            else:
                has = "✅ you have it" if role in it.user.roles else "— you do not have it"
                lines.append(f"{role.mention} — {has}")
        await it.response.send_message("\n".join(lines))

    @app_commands.command(name="pingrole-add", description="Add an AI/prompt ping role to yourself")
    async def pingrole_add(self, it: discord.Interaction, role: str):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        if role not in PING_ROLES:
            await it.response.send_message(f"'{role}' is not a known ping role. Use /pingroles to see: {', '.join(PING_ROLES)}", ephemeral=True); return
        r = find_role(it.guild, role)
        if r is None:
            await it.response.send_message(f"Role '{role}' was not found in this server.", ephemeral=True); return
        if r in it.user.roles:
            await it.response.send_message(f"You already have {r.mention}.", ephemeral=True); return
        try:
            await it.user.add_roles(r, reason="NEWR AI pingrole-add")
            await it.response.send_message(f"Added {r.mention} to you.")
        except discord.Forbidden:
            await it.response.send_message("I do not have permission to manage that role (bot role must be above it).", ephemeral=True)

    @app_commands.command(name="pingrole-remove", description="Remove an AI/prompt ping role from yourself")
    async def pingrole_remove(self, it: discord.Interaction, role: str):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        if role not in PING_ROLES:
            await it.response.send_message(f"'{role}' is not a known ping role.", ephemeral=True); return
        r = find_role(it.guild, role)
        if r is None:
            await it.response.send_message(f"Role '{role}' was not found in this server.", ephemeral=True); return
        if r not in it.user.roles:
            await it.response.send_message(f"You do not have {r.mention}.", ephemeral=True); return
        try:
            await it.user.remove_roles(r, reason="NEWR AI pingrole-remove")
            await it.response.send_message(f"Removed {r.mention} from you.")
        except discord.Forbidden:
            await it.response.send_message("I do not have permission to manage that role.", ephemeral=True)

    @app_commands.command(name="pingrole-toggle", description="Toggle an AI/prompt ping role on or off for yourself")
    async def pingrole_toggle(self, it: discord.Interaction, role: str):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        if role not in PING_ROLES:
            await it.response.send_message(f"'{role}' is not a known ping role.", ephemeral=True); return
        r = find_role(it.guild, role)
        if r is None:
            await it.response.send_message(f"Role '{role}' was not found in this server.", ephemeral=True); return
        try:
            if r in it.user.roles:
                await it.user.remove_roles(r, reason="NEWR AI pingrole-toggle")
                await it.response.send_message(f"Removed {r.mention} from you.")
            else:
                await it.user.add_roles(r, reason="NEWR AI pingrole-toggle")
                await it.response.send_message(f"Added {r.mention} to you.")
        except discord.Forbidden:
            await it.response.send_message("I do not have permission to manage that role.", ephemeral=True)

    @app_commands.command(name="my-pingroles", description="Show only the ping roles you currently have")
    async def my_pingroles(self, it: discord.Interaction):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        mine = [r for r in it.user.roles if r.name in PING_ROLES]
        if not mine:
            await it.response.send_message("You have no ping roles yet. Use /pingroles to see the list, then /pingrole-add.")
        else:
            await it.response.send_message("Your ping roles: " + ", ".join(r.mention for r in mine))

    @app_commands.command(name="pingrole-info", description="Show details for one ping role")
    async def pingrole_info(self, it: discord.Interaction, role: str):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        if role not in PING_ROLES:
            await it.response.send_message(f"'{role}' is not a known ping role.", ephemeral=True); return
        r = find_role(it.guild, role)
        if r is None:
            await it.response.send_message(f"Role '{role}' was not found in this server.", ephemeral=True); return
        await it.response.send_message(
            f"{r.mention}\nMembers with this role: {len(r.members)}\nColour: {r.colour}\nMentionable: {r.mentionable}\nYou have it: {'yes' if r in it.user.roles else 'no'}")

    @app_commands.command(name="pingrole-add-all", description="Add all AI/prompt ping roles to yourself")
    async def pingrole_add_all(self, it: discord.Interaction):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        added, missing = [], []
        for name in PING_ROLES:
            r = find_role(it.guild, name)
            if r is None: missing.append(name)
            elif r not in it.user.roles:
                try: await it.user.add_roles(r, reason="NEWR AI pingrole-add-all"); added.append(name)
                except discord.Forbidden: missing.append(name + " (no permission)")
        await it.response.send_message(f"Added: {', '.join(added) or 'none'}. Not added: {', '.join(missing) or 'none'}.")

    @app_commands.command(name="pingrole-remove-all", description="Remove all AI/prompt ping roles from yourself")
    async def pingrole_remove_all(self, it: discord.Interaction):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        removed = []
        for name in PING_ROLES:
            r = find_role(it.guild, name)
            if r and r in it.user.roles:
                try: await it.user.remove_roles(r, reason="NEWR AI pingrole-remove-all"); removed.append(name)
                except discord.Forbidden: pass
        await it.response.send_message(f"Removed: {', '.join(removed) or 'none'}.")

    @app_commands.command(name="bot-roles", description="Check the NEWR AI and NEWR Support bot roles in this server")
    async def check_bot_roles(self, it: discord.Interaction):
        err = _need_guild(it)
        if err:
            await it.response.send_message(err, ephemeral=True); return
        lines = []
        for name in BOT_ROLES:
            r = find_role(it.guild, name)
            lines.append(f"{r.mention} — {len(r.members)} member(s) with this role" if r else f"❌ {name} — not found in this server")
        await it.response.send_message("\n".join(lines))

async def setup(bot):
    await bot.add_cog(PingRoles(bot))
