"""Support-lite cog for NEWR AI: 10 slash commands.
This bot does not create tickets or manage the server — the dedicated
NEWR Support bot owns that. These commands give help info and store
feedback/report text in SQLite for a human to follow up."""
import discord, os
from discord import app_commands
from discord.ext import commands
import db, smart_local

DB = os.getenv("DB_PATH", "data.db")

class Support(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="help", description="Show NEWR AI help and command categories")
    async def help_cmd(self, it: discord.Interaction):
        await it.response.send_message(
            "NEWR AI — slash commands only.\n"
            "AI: /ask /chat /explain /summarize /translate /code /debug /rewrite /brainstorm /quiz /image-prompt /story /poem /essay /email /caption /title /grammar /simplify /expand /compare /proscons /plan /study /interview /resume /cover-letter /sql /regex /test-cases /docstring /refactor /aichat-clear /aichat-history /ai-status /model-list /model-set\n"
            "Ping roles: /pingroles /pingrole-add /pingrole-remove /pingrole-toggle /my-pingroles /pingrole-info /pingrole-add-all /pingrole-remove-all /bot-roles\n"
            "Tools, utility, fun and support-lite: use /commands-list.\n\n"
            f"💡 Smart tip of the day: {smart_local.daily_tip()}\n"
            "No AI key? /ask still gives a labelled local smart answer (steps + free resources), not a fake AI reply. "
            "Free AI: OpenRouter free tier (default), Groq free tier, or Google AI Studio Gemini free tier — see README.md. "
            "Your model preference from /model-set is remembered in SQLite and reused for real AI calls.")

    @app_commands.command(name="commands-list", description="List all command categories and counts")
    async def commands_list(self, it: discord.Interaction):
        counts = {}
        for cog in self.bot.cogs.values():
            counts[cog.__class__.__name__] = len(getattr(cog, "__cog_app_commands__", []))
        await it.response.send_message("\n".join(f"{k}: {v} commands" for k, v in counts.items()) + f"\nTotal: {sum(counts.values())}")

    @app_commands.command(name="support", description="How to get human support")
    async def support(self, it: discord.Interaction):
        await it.response.send_message("For human support, use the NEWR Support bot's ticket system in NEWR LABS, or use /report here to leave a report that a human can follow up. This AI bot does not open tickets itself.")

    @app_commands.command(name="report", description="Leave a report for a human to follow up (stored locally)")
    async def report(self, it: discord.Interaction, issue: str):
        db.add_feedback(DB, it.user.id, "report", issue)
        await it.response.send_message("Report saved. A human from the NEWR team can follow it up.", ephemeral=True)

    @app_commands.command(name="feedback", description="Leave feedback about the bot (stored locally)")
    async def feedback(self, it: discord.Interaction, text: str):
        db.add_feedback(DB, it.user.id, "feedback", text)
        await it.response.send_message("Thanks! Feedback saved.", ephemeral=True)

    @app_commands.command(name="suggest", description="Suggest a feature (stored locally)")
    async def suggest(self, it: discord.Interaction, idea: str):
        db.add_feedback(DB, it.user.id, "suggestion", idea)
        await it.response.send_message("Suggestion saved. Thanks!", ephemeral=True)

    @app_commands.command(name="bug", description="Report a bug (stored locally)")
    async def bug(self, it: discord.Interaction, description: str):
        db.add_feedback(DB, it.user.id, "bug", description)
        await it.response.send_message("Bug report saved. Thanks!", ephemeral=True)

    @app_commands.command(name="status", description="Bot status: latency and AI configuration (no key shown)")
    async def status(self, it: discord.Interaction):
        import ai_client
        await it.response.send_message(f"Latency: {round(self.bot.latency*1000)} ms\nAI configured: {'yes' if ai_client.configured() else 'no — see README.md to set AI_API_KEY'}")

    @app_commands.command(name="about", description="About NEWR AI")
    async def about(self, it: discord.Interaction):
        await it.response.send_message("NEWR AI is a slash-command-only Discord bot for the NEWR LABS community: AI chat and tools, utilities, fun, and ping-role management. Built with discord.py. No API key is hardcoded.")

    @app_commands.command(name="privacy", description="What this bot stores")
    async def privacy(self, it: discord.Interaction):
        await it.response.send_message("This bot stores, in local SQLite only: your /chat history (clearable with /aichat-clear), your model preference, your notes, and feedback/reports you submit with /report, /feedback, /suggest or /bug. It does not read your DMs or other servers.")

async def setup(bot):
    await bot.add_cog(Support(bot))
