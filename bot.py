"""NEWR AI entry point. Slash commands only, guild-synced via GUILD_ID."""
import asyncio, os, sys, time
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
import db

# Shared brain: ONE memory.db for both bots (see Support bot.py for
# the same rule). If the module is missing, the bot still runs.
for _d in [Path(__file__).resolve().parent.parent / "shared-brain",
           Path.home() / "workspace" / "bots" / "shared-brain"]:
    if (_d / "memory.py").exists():
        sys.path.insert(0, str(_d)); break
try:
    import memory as _brain
except Exception:
    _brain = None

load_dotenv()
db.init_db(os.getenv("DB_PATH", "data.db"))

COGS = ["cogs.ai", "cogs.tools", "cogs.utility", "cogs.fun", "cogs.support", "cogs.pingroles"]

def _proxy_kwargs() -> dict:
    """VM egress goes through an HTTP proxy; direct TLS to Discord fails
    here (SSL WRONG_VERSION_NUMBER), while aiohttp with trust_env works.
    discord.py does not read proxy env vars itself, so pass them explicitly.
    Credentials stay in the environment, never in code or logs."""
    from urllib.parse import unquote, urlparse

    raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not raw:
        return {}
    parsed = urlparse(raw)
    proxy = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 3128}"
    kwargs: dict = {"proxy": proxy}
    if parsed.username:
        import aiohttp

        kwargs["proxy_auth"] = aiohttp.BasicAuth(
            unquote(parsed.username),
            unquote(parsed.password or ""))
    return kwargs


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Required for the NEWR LABS membership gate in verify.py:
        # guild.fetch_member() needs the Server Members Intent, which
        # must also be enabled in the Developer Portal (Bot section).
        intents.members = True
        # Slash-only bot: no prefix commands exist, so command_prefix=None
        # also silences the spurious "message content intent is missing"
        # warning (the bot never reads message content).
        super().__init__(command_prefix=None, help_command=None, intents=intents,
                         **_proxy_kwargs())
        self._started_at = int(time.time())
    async def setup_hook(self):
        self.shared_brain_path = None
        self.brain_available = False
        if _brain is not None:
            try:
                raw = os.getenv("SHARED_BRAIN_DB") or None
                self.shared_brain_path = _brain.init_memory(
                    os.path.expanduser(os.path.expandvars(raw)) if raw else None)
                self.brain_available = True
                print(f"[brain] shared memory: {self.shared_brain_path}")
            except Exception as e:
                print(f"[brain] disabled: {e}")
        for ext in COGS:
            await self.load_extension(ext)
        self._brain_task = asyncio.create_task(self._brain_inbox_loop())

    async def _brain_inbox_loop(self):
        """Poll the shared brain every 45s for messages to newr-ai.

        Each message is handled exactly once and marked done in a
        finally block. This bot does NOT reply to a bot_message with
        a new bot_message, so AI <-> Support cannot loop.
        """
        await self.wait_until_ready()
        while not self.is_closed():
            if self.brain_available and _brain is not None:
                try:
                    for msg in _brain.fetch_bot_messages("newr-ai"):
                        try:
                            _brain.remember_event(
                                msg.get("guild_id"), f"{msg.get('kind')}_received",
                                user_id=msg.get("user_id"),
                                details=(msg.get("text") or "")[:500],
                                source_bot="newr-ai")
                            print(f"[brain] inbox {msg.get('from_bot')} -> "
                                  f"newr-ai kind={msg.get('kind')} id={msg.get('id')}")
                        except Exception as e:
                            print(f"[brain] inbox handling failed: {e}")
                        finally:
                            try: _brain.mark_bot_message_done(msg["id"])
                            except Exception: pass
                except Exception as e:
                    print(f"[brain] inbox poll failed: {e}")
            await asyncio.sleep(45)
    async def on_ready(self):
        print(f"Logged in as {self.user} (NEWR AI)")
        if not getattr(self, "_synced", False):
            self._synced = True
            try:
                guild_id = int(os.getenv("GUILD_ID")) if os.getenv("GUILD_ID") else None
            except ValueError:
                guild_id = None
            if guild_id:
                # Commands are registered globally by the cogs; copy them
                # to the guild tree first, otherwise guild sync returns 0
                # (same pattern as the NEWR Support bot's on_ready).
                self.tree.copy_global_to(guild=discord.Object(id=guild_id))
                synced = await self.tree.sync(guild=discord.Object(id=guild_id))
                print(f"Synced {len(synced)} slash commands to guild {guild_id}")
            else:
                synced = await self.tree.sync()
                print(f"Synced {len(synced)} slash commands globally (no GUILD_ID set)")

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in (see README.md).")
    Bot().run(token)

if __name__ == "__main__":
    main()
