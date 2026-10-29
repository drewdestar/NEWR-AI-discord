"""Dry-run self-test: loads all cogs and counts slash commands.
Needs NO Discord token and NO AI key. Run: python test_load.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DB_PATH", "/tmp/newr-ai-test.db")
import discord
from discord.ext import commands
import db
db.init_db(os.environ["DB_PATH"])

COGS = ["cogs.ai", "cogs.tools", "cogs.utility", "cogs.fun", "cogs.support", "cogs.pingroles"]

async def main():
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
    for ext in COGS:
        await bot.load_extension(ext)
    total = 0
    print("Cog breakdown (slash commands):")
    for name, cog in bot.cogs.items():
        cmds = getattr(cog, "__cog_app_commands__", [])
        print(f"  {name}: {len(cmds)}")
        for c in cmds: print(f"    /{c.name}")
        total += len(cmds)
    tree_cmds = bot.tree.get_commands()
    print(f"Tree commands registered: {len(tree_cmds)}")
    print(f"TOTAL (cog app commands): {total}")
    assert 99 <= total <= 100, f"Total {total} outside the Discord-syncable 99-100 range"
    print("PASS: 99-100 slash commands (Discord guild cap), all cogs loaded without token or AI key.")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
