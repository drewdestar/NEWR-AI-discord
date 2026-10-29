"""Pluggable OpenAI-compatible AI client.

Primary path: POST {AI_API_URL}/chat/completions with Bearer AI_API_KEY.
AI_API_URL may be a base URL (e.g. https://api.openai.com/v1,
https://generativelanguage.googleapis.com/v1beta/openai,
https://api.groq.com/openai/v1, https://openrouter.ai/api/v1)
or a full chat-completions URL; both are handled.

No-key path: there is NO free/no-key provider that can be relied on
without a key, and this module never fakes an answer. If no key is set
it raises AIConfigError with setup instructions, and callers surface
that message to the user. A local rule-based fallback is NOT used for
/ask-style answers, because that would present a canned answer as AI.
"""
import os, aiohttp

class AIConfigError(Exception):
    pass

SETUP_TEXT = (
    "AI is not configured yet. Set AI_API_KEY (and optionally AI_API_URL and AI_MODEL) "
    "in .env, then restart the bot. Free options (free tiers only, no paid key required): OpenRouter free tier (the default), Groq, "
    "OpenRouter free tier, or Hugging Face — see README.md for the exact steps. "
    "You can sign up for those free tiers with a Gmail account. No key is hardcoded in this bot."
)

def _url():
    base = os.getenv("AI_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"

def configured() -> bool:
    return bool(os.getenv("AI_API_KEY"))

async def chat(messages, model=None, system=None, temperature=0.7):
    """messages: list of {role, content}. Returns assistant text."""
    key = os.getenv("AI_API_KEY")
    if not key:
        raise AIConfigError(SETUP_TEXT)
    model = model or os.getenv("AI_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    payload_msgs = ([{"role": "system", "content": system}] if system else []) + messages
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    # OpenRouter-style providers appreciate these headers; harmless elsewhere.
    if "openrouter" in _url():
        headers["HTTP-Referer"] = "https://newrlabs.my.id"
        headers["X-Title"] = "NEWR AI"
    body = {"model": model, "messages": payload_msgs, "temperature": temperature}
    # trust_env=True: on this VM outbound TLS only works via the egress
    # proxy in the environment; without it the provider call fails with
    # SSL WRONG_VERSION_NUMBER even with a valid key.
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90), trust_env=True) as s:
        async with s.post(_url(), json=body, headers=headers) as r:
            data = await r.json(content_type=None)
            if r.status >= 400:
                err = data.get("error", {}) if isinstance(data, dict) else {}
                msg = err.get("message", str(data)) if isinstance(err, dict) else str(data)
                raise RuntimeError(f"AI provider returned HTTP {r.status}: {msg}")
            try:
                return data["choices"][0]["message"]["content"]
            except Exception:
                raise RuntimeError(f"Unexpected AI provider response: {data}")

async def list_models():
    """Return provider models if a key is set, else the documented free-tier list."""
    if not configured():
        return ["(no key configured — see README.md)", "google/gemini-2.0-flash (via Google AI Studio, OpenAI-compatible endpoint)",
                "llama-3.3-70b-versatile (via Groq)", "meta-llama/llama-3.1-8b-instruct:free (via OpenRouter free tier)"]
    base = os.getenv("AI_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
    url = base + "/models" if not base.endswith("/chat/completions") else base.replace("/chat/completions", "/models")
    headers = {"Authorization": f"Bearer {os.getenv('AI_API_KEY')}"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30), trust_env=True) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                ids = [m["id"] for m in data.get("data", [])] if isinstance(data, dict) else []
                return ids[:50] or ["(provider returned no models)"]
    except Exception as e:
        return [f"(could not list provider models: {e})"]
