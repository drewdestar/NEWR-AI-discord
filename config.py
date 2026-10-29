"""Configuration from environment only. No secrets are hardcoded here."""
import os

def _env(name, default=""):
    v = os.getenv(name)
    return v if v not in (None, "") else default

DISCORD_TOKEN = _env("DISCORD_TOKEN")
GUILD_ID = _env("GUILD_ID")
# Optional: only included in the NEWR LABS gate message if set.
# Never invent an invite URL; leave this empty if there is none.
GUILD_INVITE_URL = _env("GUILD_INVITE_URL")
AI_API_URL = _env("AI_API_URL", "https://openrouter.ai/api/v1")  # FREE default: OpenRouter free tier
AI_API_KEY = _env("AI_API_KEY")
AI_MODEL = _env("AI_MODEL", "meta-llama/llama-3.1-8b-instruct:free")  # FREE default model; free model names change, see README
DB_PATH = _env("DB_PATH", "data.db")

def ai_configured() -> bool:
    return bool(AI_API_KEY)

def guild_id_int():
    try:
        return int(GUILD_ID) if GUILD_ID else None
    except ValueError:
        return None
