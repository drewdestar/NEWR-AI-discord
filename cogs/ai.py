"""AI cog: 37 slash commands. All /ask-style commands call the real
OpenAI-compatible provider via ai_client; with no key they reply with
the setup instructions instead of faking an answer.

NEWR LABS membership gate (verify.py): every AI command here is
gated except /ai-status, which is intentionally ungated so it can
report the caller's membership status. Non-AI commands in other
cogs are not gated."""
import discord
from discord import app_commands
from discord.ext import commands
import ai_client, db, os, smart_local, verify

DB = os.getenv("DB_PATH", "data.db")
NOT_CONFIG = ai_client.SETUP_TEXT

# --- Shared brain helpers (best-effort; never break an AI command) ---
def _brain():
    try:
        import memory
        return memory
    except Exception:
        return None

_TICKET_KEYWORDS = ("ticket", "lapor", "report", "bantuan staff", "need staff",
                    "open ticket", "support ticket", "hubungi staff",
                    "staff help", "minta bantuan staff", "butuh staff")

def _brain_context(user_id, guild_id):
    """Short shared-brain context for the system prompt, or ''."""
    brain = _brain()
    if brain is None:
        return ""
    try:
        cross = brain.recall_cross_bot(str(user_id))
        convo = brain.recall_conversation(str(user_id), limit=12)
        parts = []
        if cross.get("summary"):
            parts.append(cross["summary"])
        prefs = cross.get("preferences") or {}
        if prefs:
            parts.append("Shared preferences: " + ", ".join(f"{k}={v}" for k, v in prefs.items())[:300])
        for turn in convo[-6:]:
            txt = (turn.get("text") or "")[:200]
            if txt:
                parts.append(f"[{turn.get('source_bot') or '?'} {turn.get('role')}] {txt}")
        return "Shared brain context (NEWR Support + NEWR AI, do not reveal raw user IDs or other users' data): " + " | ".join(parts)[:1200] if parts else ""
    except Exception:
        return ""

def _brain_remember(it, user_text, assistant_text, guild_id=None):
    brain = _brain()
    if brain is None:
        return
    try:
        user = it.user
        roles = [r.name for r in getattr(user, "roles", [])] if getattr(it, "guild", None) else []
        brain.remember_user(str(user.id), str(guild_id) if guild_id else None,
                            getattr(user, "display_name", None) or str(user),
                            roles, source_bot="newr-ai")
        ch = getattr(it, "channel", None)
        brain.remember_conversation(str(user.id), str(guild_id) if guild_id else None,
                                    str(getattr(ch, "id", None)) if ch else None,
                                    "user", user_text, source_bot="newr-ai")
        if assistant_text:
            brain.remember_conversation(str(user.id), str(guild_id) if guild_id else None,
                                        str(getattr(ch, "id", None)) if ch else None,
                                        "assistant", assistant_text, source_bot="newr-ai")
    except Exception:
        pass

def _brain_handoff_if_ticket(it, user_text, assistant_text):
    """One ai_summary to Support if this looks like a support ticket."""
    brain = _brain()
    if brain is None:
        return
    low = (user_text or "").lower()
    if not any(k in low for k in _TICKET_KEYWORDS):
        return
    try:
        brain.send_bot_message("newr-ai", "newr-support", "ai_summary",
                               f"User {it.user.id} asked for staff/ticket help: {user_text[:300]}",
                               user_id=str(it.user.id),
                               guild_id=str(it.guild.id) if getattr(it, "guild", None) else None)
    except Exception:
        pass


async def _run(it, system, user_text, store=True):
    # NEWR LABS membership gate (verify.py): applies to every
    # AI-generation command that goes through _run. Checked BEFORE
    # deferring, so a non-member gets the ephemeral join message
    # and no AI request is made at all.
    if not await verify.require_member(it):
        return
    await it.response.defer(thinking=True)
    _ctx = _brain_context(it.user.id, it.guild.id if getattr(it, "guild", None) else None)
    if _ctx:
        system = system + " " + _ctx
    try:
        pref = db.get_pref(DB, it.user.id)
        # Smart mode: remembered SQLite preferences shape the real AI call.
        if pref.get("language") or pref.get("style"):
            system = system + " " + " ".join(
                [f"Reply in {pref['language']}." if pref.get("language") else "",
                 f"Use a {pref['style']} style." if pref.get("style") else ""]).strip()
        hist = db.get_history(DB, it.user.id, 8) if store else []
        msgs = hist + [{"role": "user", "content": user_text}]
        out = await ai_client.chat(msgs, model=pref.get("model") or None, system=system)
        if store:
            db.add_message(DB, it.user.id, "user", user_text)
            db.add_message(DB, it.user.id, "assistant", out)
            _brain_remember(it, user_text, out,
                            it.guild.id if getattr(it, "guild", None) else None)
            _brain_handoff_if_ticket(it, user_text, out)
        await it.followup.send(out[:1900] if len(out) > 1900 else out)
    except ai_client.AIConfigError:
        # Smart local fallback (FREE, no key, no model): a genuinely useful
        # structured answer, clearly labelled as local — never presented
        # as an AI model reply. The setup text follows so the user can
        # still enable real free AI afterwards.
        pref = db.get_pref(DB, it.user.id)
        local = smart_local.smart_answer(user_text, pref=pref)
        if store:
            _brain_remember(it, user_text, local,
                            it.guild.id if getattr(it, "guild", None) else None)
            _brain_handoff_if_ticket(it, user_text, local)
        await it.followup.send((local + "\n\n---\n" + NOT_CONFIG)[:1900])
    except Exception as e:
        await it.followup.send(f"AI request failed: {e}")

def _cmd(name, desc, system):
    async def handler(self, it: discord.Interaction, prompt: str):
        await _run(it, system, prompt)
    handler.__name__ = name
    return app_commands.command(name=name, description=desc)(handler)

class AI(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="ask", description="Ask the AI anything")
    async def ask(self, it: discord.Interaction, question: str):
        await _run(it, "You are NEWR AI, a helpful Discord assistant. Answer clearly and concisely.", question)

    @app_commands.command(name="chat", description="Chat with memory: remembers your recent conversation")
    async def chat(self, it: discord.Interaction, message: str):
        await _run(it, "You are NEWR AI, a friendly conversational assistant.", message)

    @app_commands.command(name="explain", description="Explain a topic simply")
    async def explain(self, it: discord.Interaction, topic: str):
        await _run(it, "Explain the topic clearly, with an example, at a beginner-friendly level unless asked otherwise.", topic, store=False)

    @app_commands.command(name="summarize", description="Summarize the given text")
    async def summarize(self, it: discord.Interaction, text: str):
        await _run(it, "Summarize the input faithfully in a few bullet points, keeping key facts and numbers.", text, store=False)

    @app_commands.command(name="translate", description="Translate text to a language")
    async def translate(self, it: discord.Interaction, text: str, language: str = "English"):
        await _run(it, f"Translate the input to {language}. Return only the translation.", text, store=False)

    @app_commands.command(name="code", description="Generate code for a task")
    async def code(self, it: discord.Interaction, task: str, language: str = "Python"):
        await _run(it, f"Write working {language} code for the task, with brief comments. Return code first, then a short explanation.", task, store=False)

    @app_commands.command(name="debug", description="Find bugs in code and suggest a fix")
    async def debug(self, it: discord.Interaction, code: str):
        await _run(it, "Analyse the code, list likely bugs with line-level reasoning, then give a corrected version.", code, store=False)

    @app_commands.command(name="rewrite", description="Rewrite text in a better style")
    async def rewrite(self, it: discord.Interaction, text: str, style: str = "clear and professional"):
        await _run(it, f"Rewrite the text in a {style} style, preserving meaning.", text, store=False)

    @app_commands.command(name="brainstorm", description="Brainstorm ideas for a topic")
    async def brainstorm(self, it: discord.Interaction, topic: str):
        await _run(it, "Brainstorm at least 10 distinct, practical ideas, numbered, with a one-line note each.", topic, store=False)

    @app_commands.command(name="quiz", description="Generate a quiz on a topic")
    async def quiz(self, it: discord.Interaction, topic: str):
        await _run(it, "Create a 5-question multiple-choice quiz on the topic, with answers at the end.", topic, store=False)

    @app_commands.command(name="image-prompt", description="Write a detailed image-generation prompt")
    async def image_prompt(self, it: discord.Interaction, idea: str):
        await _run(it, "Write a detailed, vivid image-generation prompt (subject, style, lighting, composition) for the idea. This writes a prompt only; it does not generate an image.", idea, store=False)

    @app_commands.command(name="story", description="Write a short story")
    async def story(self, it: discord.Interaction, theme: str):
        await _run(it, "Write an original short story on the theme, under 400 words.", theme, store=False)

    @app_commands.command(name="poem", description="Write a poem")
    async def poem(self, it: discord.Interaction, theme: str):
        await _run(it, "Write an original poem on the theme.", theme, store=False)

    @app_commands.command(name="essay", description="Draft a short essay outline and text")
    async def essay(self, it: discord.Interaction, topic: str):
        await _run(it, "Write a structured short essay on the topic: introduction, 3 body points, conclusion.", topic, store=False)

    @app_commands.command(name="email", description="Draft an email")
    async def email(self, it: discord.Interaction, purpose: str, tone: str = "polite"):
        await _run(it, f"Draft a {tone} email for the purpose, with subject line and greeting.", purpose, store=False)

    @app_commands.command(name="caption", description="Write a social-media caption")
    async def caption(self, it: discord.Interaction, topic: str):
        await _run(it, "Write 3 caption options for the topic, each with relevant hashtags.", topic, store=False)

    @app_commands.command(name="title", description="Suggest titles for content")
    async def title(self, it: discord.Interaction, topic: str):
        await _run(it, "Suggest 10 catchy titles for the topic.", topic, store=False)

    @app_commands.command(name="grammar", description="Fix grammar and spelling")
    async def grammar(self, it: discord.Interaction, text: str):
        await _run(it, "Correct grammar and spelling, return the corrected text, then list the changes briefly.", text, store=False)

    @app_commands.command(name="simplify", description="Simplify complex text")
    async def simplify(self, it: discord.Interaction, text: str):
        await _run(it, "Rewrite the text in plain, simple language without losing meaning.", text, store=False)

    @app_commands.command(name="expand", description="Expand a short idea into detail")
    async def expand(self, it: discord.Interaction, idea: str):
        await _run(it, "Expand the idea into a detailed explanation with examples.", idea, store=False)

    @app_commands.command(name="compare", description="Compare two things")
    async def compare(self, it: discord.Interaction, first: str, second: str):
        await _run(it, "Compare the two items in a table-like list: similarities, differences, and a verdict.", f"{first} vs {second}", store=False)

    @app_commands.command(name="proscons", description="List pros and cons")
    async def proscons(self, it: discord.Interaction, topic: str):
        await _run(it, "List pros and cons of the topic, balanced, then a short summary.", topic, store=False)

    @app_commands.command(name="plan", description="Make a step-by-step plan")
    async def plan(self, it: discord.Interaction, goal: str):
        await _run(it, "Make a practical step-by-step plan to achieve the goal, with milestones.", goal, store=False)

    @app_commands.command(name="study", description="Make study notes on a topic")
    async def study(self, it: discord.Interaction, topic: str):
        await _run(it, "Create study notes: key terms, summary, and 5 self-test questions with answers.", topic, store=False)

    @app_commands.command(name="interview", description="Generate interview questions")
    async def interview(self, it: discord.Interaction, role: str):
        await _run(it, "Generate 10 interview questions for the role, plus what a good answer looks like for each.", role, store=False)

    @app_commands.command(name="resume", description="Improve a resume bullet point")
    async def resume(self, it: discord.Interaction, bullet: str):
        await _run(it, "Rewrite the resume bullet to be stronger and achievement-focused, then explain the change.", bullet, store=False)

    @app_commands.command(name="cover-letter", description="Draft a cover letter paragraph")
    async def cover_letter(self, it: discord.Interaction, job: str):
        await _run(it, "Draft a concise cover-letter opening and body paragraph for the job.", job, store=False)

    @app_commands.command(name="sql", description="Write an SQL query")
    async def sql(self, it: discord.Interaction, request: str):
        await _run(it, "Write a correct SQL query for the request, explain it briefly, and note assumptions about tables.", request, store=False)

    @app_commands.command(name="regex", description="Write a regex pattern")
    async def regex(self, it: discord.Interaction, description: str):
        await _run(it, "Write a regex for the description, explain each part, and give 2 matching and 2 non-matching examples.", description, store=False)

    @app_commands.command(name="test-cases", description="Generate test cases for a feature")
    async def test_cases(self, it: discord.Interaction, feature: str):
        await _run(it, "Generate test cases for the feature: happy path, edge cases, and failure cases.", feature, store=False)

    @app_commands.command(name="docstring", description="Write a docstring for a function")
    async def docstring(self, it: discord.Interaction, function: str):
        await _run(it, "Write a clear docstring (purpose, args, returns) for the function described.", function, store=False)

    @app_commands.command(name="refactor", description="Suggest a refactor for code")
    async def refactor(self, it: discord.Interaction, code: str):
        await _run(it, "Suggest a refactor: cleaner structure, then the refactored code, then why it is better.", code, store=False)

    @app_commands.command(name="aichat-clear", description="Clear your AI conversation history")
    async def aichat_clear(self, it: discord.Interaction):
        if not await verify.require_member(it):
            return
        n = db.clear_history(DB, it.user.id)
        await it.response.send_message(f"Cleared {n} stored conversation messages for you.")

    @app_commands.command(name="aichat-history", description="Show how many AI messages are stored for you")
    async def aichat_history(self, it: discord.Interaction):
        if not await verify.require_member(it):
            return
        await it.response.send_message(f"You have {db.history_count(DB, it.user.id)} stored conversation messages (last 12 are used as context).")

    @app_commands.command(name="ai-status", description="Show AI provider configuration status (no key shown)")
    async def ai_status(self, it: discord.Interaction):
        # Intentionally NOT gated: this is how a non-member learns
        # they are not a member (see membership line below).
        import ai_client as ac
        url = os.getenv("AI_API_URL", "https://openrouter.ai/api/v1")
        member_status = await verify.membership_status(it.client, it.user.id)
        pref = db.get_pref(DB, it.user.id)
        await it.response.send_message(
            f"AI configured: {'yes' if ac.configured() else 'no (local smart answers only — see below)'}\nProvider URL: {url}\nModel: {os.getenv('AI_MODEL', 'meta-llama/llama-3.1-8b-instruct:free')}\n"
            f"NEWR LABS membership: {member_status}\n"
            f"{smart_local.smart_context(pref)}\n"
            f"💡 Tip of the day: {smart_local.daily_tip()}\n"
            + ("" if ac.configured() else ai_client.SETUP_TEXT))

    @app_commands.command(name="model-list", description="List available AI models")
    async def model_list(self, it: discord.Interaction):
        if not await verify.require_member(it):
            return
        await it.response.defer(thinking=True)
        models = await ai_client.list_models()
        await it.followup.send("\n".join(models)[:1900])

    @app_commands.command(name="model-set", description="Set your preferred AI model for this bot")
    async def model_set(self, it: discord.Interaction, model: str):
        if not await verify.require_member(it):
            return
        db.set_pref(DB, it.user.id, model=model)
        await it.response.send_message(f"Your preferred model is now set to: {model} (used when the provider supports it).")

async def setup(bot):
    await bot.add_cog(AI(bot))
