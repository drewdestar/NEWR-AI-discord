"""Local smart helpers for NEWR AI — free, no API key, no model call.

IMPORTANT HONESTY RULE: nothing here is an AI model reply. When the
bot has no AI key configured, callers must label the output as a
"local smart answer" so users never mistake a template for a model.
The value is real anyway: structured steps, checklists, free
resources, and prompt suggestions — the same scaffolding a good
assistant would give before a model is connected.

Contents:
- DAILY_TIPS: rotating free-learning / Discord / safety tips.
- prompt_suggestions(topic): starter prompts for a topic.
- smart_answer(question, pref=None): a genuinely useful local answer:
  restates the question, gives a step-by-step approach, a checklist
  for common kinds of questions (code, study, Discord, writing),
  free resources, and how to enable free AI.
- smart_context(pref): one line summarising stored user preferences
  from SQLite (model/language/style), so the bot remembers them.
"""
from __future__ import annotations

import re
from datetime import date

DAILY_TIPS = [
    "Free learning tip: for programming, start with the official docs and one small project — docs.python.org, MDN Web Docs, and freeCodeCamp are all free and stay current.",
    "Free AI tip: OpenRouter's free tier, Groq's free tier, and Google AI Studio (Gemini) all offer free API keys with rate limits. No paid key is needed to try this bot — see README.md.",
    "Discord tip: keep your token and API keys out of channels and screenshots. A leaked token must be reset immediately in the Developer Portal.",
    "Study tip: explain a topic back in your own words, then do 5 practice questions. /study and /quiz on this bot can help once AI is enabled — without a key, try the steps in /ask's local answer.",
    "Writing tip: a good prompt has a goal, an audience, and a format. Example: 'Explain X for a beginner, in 5 bullet points, with one example.' That works for AI and for humans.",
    "Safety tip: a DM offering 'free Nitro' or asking you to scan a QR code to verify is phishing. Report it, don't click it.",
    "Code tip: when stuck, isolate the smallest failing example, read the exact error message top to bottom, and change one thing at a time.",
    "Prompt tip: if an AI answer is too vague, add constraints — length, format, audience, and an example of what 'good' looks like.",
]

PROMPT_IDEAS = [
    "Explain {topic} for a beginner, with one real example",
    "Give me a step-by-step plan to learn {topic} in 2 weeks, free resources only",
    "What are the 5 most common mistakes with {topic}, and how do I avoid them?",
    "Summarise {topic} in 5 bullet points, then quiz me with 3 questions",
    "Compare {topic} with its closest alternative, pros and cons",
]


def daily_tip(on: date | None = None) -> str:
    d = on or date.today()
    return DAILY_TIPS[d.toordinal() % len(DAILY_TIPS)]


def prompt_suggestions(topic: str) -> list[str]:
    t = (topic or "this topic").strip() or "this topic"
    return [p.format(topic=t) for p in PROMPT_IDEAS]


def smart_context(pref: dict | None) -> str:
    if not pref:
        return "No stored preferences yet — set a model with /model-set and it will be remembered here."
    bits = []
    if pref.get("model"):
        bits.append(f"preferred model: {pref['model']}")
    if pref.get("language"):
        bits.append(f"language: {pref['language']}")
    if pref.get("style"):
        bits.append(f"style: {pref['style']}")
    return "Your remembered preferences: " + (", ".join(bits) if bits else "none set yet")


def _kind(question: str) -> str:
    q = question.lower()
    if re.search(r"\b(python|javascript|code|error|bug|debug|function|sql|regex)\b", q):
        return "code"
    if re.search(r"\b(study|learn|exam|quiz|school|homework)\b", q):
        return "study"
    if re.search(r"\b(discord|server|role|bot|channel|member)\b", q):
        return "discord"
    if re.search(r"\b(translate|language|indonesian|english|grammar)\b", q):
        return "language"
    if re.search(r"\b(write|essay|email|caption|story|poem|resume)\b", q):
        return "writing"
    return "general"


_CHECKLISTS = {
    "code": [
        "1. Paste the exact error message and the smallest code that reproduces it.",
        "2. Check the line the error points to, then the line above it — most syntax errors live one line up.",
        "3. Change one thing at a time and re-run, so you know what fixed it.",
        "4. Free help: official docs, Stack Overflow, and MDN — search the exact error text in quotes.",
    ],
    "study": [
        "1. Write what you already know about the topic in 3 sentences.",
        "2. List the terms you can't define yet — those are your study targets.",
        "3. Do 5 practice questions, then re-explain the answers in your own words.",
        "4. Free resources: Khan Academy, freeCodeCamp, and your course's official docs.",
    ],
    "discord": [
        "1. For server help, use the NEWR Support bot: /ticket_create for private help, /faq for common questions.",
        "2. For AI help here, you must be a member of NEWR LABS first (see /ai-status).",
        "3. Never share tokens, passwords, or QR-code logins — staff never ask for them.",
    ],
    "language": [
        "1. Write the sentence you want, then the language you want it in.",
        "2. Check one word at a time for words with double meanings — those are where translations break.",
        "3. Free tools: Google Translate for a rough draft, then a dictionary (e.g. KBBI for Indonesian) to verify key words.",
    ],
    "writing": [
        "1. Decide the goal (inform? persuade? apply?) and the reader first.",
        "2. Outline: one idea per paragraph, strongest point first.",
        "3. Draft fast, then edit once for clarity and once for grammar — never both at once.",
    ],
    "general": [
        "1. Restate the goal in one sentence: what does 'done' look like?",
        "2. Break it into the smallest next step you can do in 10 minutes.",
        "3. List what you already tried, so the next helper doesn't repeat it.",
    ],
}

_FREE_RESOURCES = (
    "Free resources to try right now: OpenRouter free models, Groq free tier, "
    "Google AI Studio (Gemini) free tier, Hugging Face free inference, "
    "freeCodeCamp, Khan Academy, MDN Web Docs, and docs.python.org. "
    "All have rate limits on free tiers — if one is busy, try another."
)


def smart_answer(question: str, pref: dict | None = None) -> str:
    """A useful local answer, clearly NOT an AI model reply."""
    q = (question or "").strip()
    kind = _kind(q)
    steps = "\n".join(_CHECKLISTS[kind])
    suggestions = "\n".join(f"• {s}" for s in prompt_suggestions(q[:80]))
    return (
        "🧠 Local smart answer — this is NOT an AI model reply, because no AI key "
        "is configured yet. It is a structured local guide, so it is still useful "
        "while free AI is being set up.\n\n"
        f"**What you asked:** {q}\n\n"
        f"**Step-by-step approach ({kind}):**\n{steps}\n\n"
        f"**Free resources:**\n{_FREE_RESOURCES}\n\n"
        f"**Try these prompts once free AI is enabled:**\n{suggestions}\n\n"
        f"{smart_context(pref)}\n\n"
        "To enable real AI for free: set AI_API_KEY in .env from OpenRouter "
        "(free tier, default), Groq (free tier), or Google AI Studio (Gemini, "
        "free tier) — see README.md. No paid key is required."
    )
