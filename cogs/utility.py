"""Utility cog: 15 slash commands. Pure Discord info, time and text tools."""
import discord, time, datetime, random
from discord import app_commands
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, it: discord.Interaction):
        await it.response.send_message(f"Pong! Latency: {round(self.bot.latency*1000)} ms")

    @app_commands.command(name="server-info", description="Show info about this server")
    async def server_info(self, it: discord.Interaction):
        if not it.guild: await it.response.send_message("Not in a server.", ephemeral=True); return
        g = it.guild
        await it.response.send_message(f"**{g.name}**\nID: {g.id}\nMembers: {g.member_count}\nChannels: {len(g.channels)}\nRoles: {len(g.roles)}\nCreated: {g.created_at.date()}")

    @app_commands.command(name="user-info", description="Show info about a user")
    async def user_info(self, it: discord.Interaction, user: discord.User = None):
        u = user or it.user
        await it.response.send_message(f"**{u.display_name}** (@{u.name})\nID: {u.id}\nBot: {u.bot}\nCreated: {u.created_at.date()}")

    @app_commands.command(name="avatar", description="Show a user's avatar link")
    async def avatar(self, it: discord.Interaction, user: discord.User = None):
        u = user or it.user
        await it.response.send_message(u.display_avatar.url)

    @app_commands.command(name="member-count", description="Show member count for this server")
    async def member_count(self, it: discord.Interaction):
        if not it.guild: await it.response.send_message("Not in a server.", ephemeral=True); return
        await it.response.send_message(f"{it.guild.name} has {it.guild.member_count} members.")

    @app_commands.command(name="my-roles", description="List your roles in this server")
    async def my_roles(self, it: discord.Interaction):
        if not it.guild: await it.response.send_message("Not in a server.", ephemeral=True); return
        await it.response.send_message(", ".join(r.name for r in it.user.roles) or "You have no roles.")

    @app_commands.command(name="timestamp-now", description="Show the current Unix timestamp and Discord timestamp")
    async def timestamp_now(self, it: discord.Interaction):
        now = int(time.time()); await it.response.send_message(f"Unix: {now}\nDiscord: <t:{now}:F> (<t:{now}:R>)")

    @app_commands.command(name="timezones", description="Show the time in several timezones")
    async def timezones(self, it: discord.Interaction):
        utc = datetime.datetime.now(datetime.timezone.utc)
        zones = {"UTC": 0, "WIB": 7, "WITA": 8, "WIT": 9, "Tokyo": 9}
        lines = []
        for name, off in zones.items():
            t = utc + datetime.timedelta(hours=off); lines.append(f"{name}: {t.strftime('%Y-%m-%d %H:%M')}")
        await it.response.send_message("\n".join(lines))

    @app_commands.command(name="remind-me", description="Set a simple in-bot reminder (message back in this channel)")
    async def remind_me(self, it: discord.Interaction, minutes: int, message: str):
        if not 1 <= minutes <= 1440: await it.response.send_message("Minutes must be 1-1440.", ephemeral=True); return
        await it.response.send_message(f"Reminder set for {minutes} minute(s): {message}")
        async def _remind():
            import asyncio; await asyncio.sleep(minutes * 60)
            try: await it.channel.send(f"⏰ Reminder for {it.user.mention}: {message}")
            except Exception: pass
        self.bot.loop.create_task(_remind())

    @app_commands.command(name="note-add", description="Save a private note for yourself (stored in SQLite)")
    async def note_add(self, it: discord.Interaction, text: str):
        import db, os; db.add_note(os.getenv("DB_PATH", "data.db"), it.user.id, text)
        await it.response.send_message("Note saved.", ephemeral=True)

    @app_commands.command(name="note-list", description="List your saved notes")
    async def note_list(self, it: discord.Interaction):
        import db, os; notes = db.list_notes(os.getenv("DB_PATH", "data.db"), it.user.id)
        await it.response.send_message("\n".join(f"{i}: {t}" for i, t in notes)[:1900] if notes else "No notes yet.", ephemeral=True)

    @app_commands.command(name="choose", description="Choose between two options at random")
    async def choose(self, it: discord.Interaction, first: str, second: str):
        await it.response.send_message(f"I choose: **{random.choice([first, second])}**")

    @app_commands.command(name="yesno", description="Answer yes or no at random")
    async def yesno(self, it: discord.Interaction, question: str):
        await it.response.send_message(f"{question}\nAnswer: **{random.choice(['Yes', 'No'])}**")

    @app_commands.command(name="emojify", description="Convert text to regional-indicator emojis")
    async def emojify(self, it: discord.Interaction, text: str):
        out = []
        for c in text.lower():
            if c.isalpha(): out.append(f":regional_indicator_{c}:")
            elif c == " ": out.append("  ")
            else: out.append(c)
        await it.response.send_message("".join(out)[:1900])

    @app_commands.command(name="embed-text", description="Send text as a styled embed")
    async def embed_text(self, it: discord.Interaction, title: str, text: str):
        await it.response.send_message(embed=discord.Embed(title=title, description=text, colour=discord.Colour.blurple()))

async def setup(bot):
    await bot.add_cog(Utility(bot))
