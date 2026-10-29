# NEWR AI — Discord bot (slash commands only)

A real, working AI Discord bot for the **NEWR LABS** server (guild-synced,
`GUILD_ID=1465422166790242377` in `.env.example`). Separate from the NEWR
Support bot: this bot does not create tickets or manage the server. It is
already in NEWR LABS, so do not re-invite it there.

## What it does

- **AI** (`cogs/ai.py`): `/ask`, `/chat` (with SQLite conversation memory),
  `/explain`, `/summarize`, `/translate`, `/code`, `/debug`, `/rewrite`,
  `/brainstorm`, `/quiz`, `/image-prompt` (writes a prompt only),
  `/story`, `/poem`, `/essay`, `/email`, `/caption`, `/title`, `/grammar`,
  `/simplify`, `/expand`, `/compare`, `/proscons`, `/plan`, `/study`,
  `/interview`, `/resume`, `/cover-letter`, `/sql`, `/regex`, `/test-cases`,
  `/docstring`, `/refactor`, plus `/aichat-clear`, `/aichat-history`,
  `/ai-status`, `/model-list`, `/model-set`.
- **Ping roles** (`cogs/pingroles.py`): `/pingroles`, `/pingrole-add`,
  `/pingrole-remove`, `/pingrole-toggle`, `/my-pingroles`, `/pingrole-info`,
  `/pingrole-add-all`, `/pingrole-remove-all`, `/bot-roles`.
  Roles are matched by **name at runtime**, never by hardcoded ID. Known
  ping roles: GROK Ping, CHATGPT Ping, DEEPSEEK Ping, KIMI Ping,
  GEMINI Ping, New Prompt Ping, Prompt Share Ping. Bot roles checked:
  NEWR AI, NEWR Support.
- **Tools** (`cogs/tools.py`): calculator, unit/currency conversion,
  weather (Open-Meteo, no key), dictionary, DuckDuckGo instant answer,
  base64, hash, password generator, UUID, random, text tools.
- **Utility** (`cogs/utility.py`): ping, server/user info, timestamps,
  timezones, reminders, private notes, embeds.
- **Fun** (`cogs/fun.py`): dice, coinflip, 8-ball, jokes, facts, RPS, etc.
- **Support-lite** (`cogs/support.py`): `/help`, `/faq`, `/report`,
  `/feedback`, `/suggest`, `/bug`, `/status`, `/about`, `/privacy`,
  `/terms`, `/version`. Reports are stored locally in SQLite for a human
  to follow up; this bot does not open tickets.

Total: **100 slash commands** — Discord caps a guild at 100 top-level slash commands, so 100 is the maximum that can actually sync (and it satisfies 99+) — see `python test_load.py`. No new slash command was added for the membership gate below, so the total stays at 100.

## NEWR LABS membership gate (AI commands only)

Everyone may use the AI bot, but only if they have joined **NEWR LABS**
(`GUILD_ID=1465422166790242377`) first. Implemented in `verify.py`
and applied in `cogs/ai.py`:

- Before any AI command runs, the bot checks guild membership with
  `bot.get_guild(GUILD_ID)`, then `guild.get_member(user_id)` from
  cache, falling back to `guild.fetch_member(user_id)`.
- If the caller is a member, the command runs normally. If not —
  or if the bot cannot see the guild/member at all — the command
  stops before any AI request and replies **ephemerally**: you must
  join NEWR LABS first to use the AI bot. If `GUILD_INVITE_URL` is
  set in `.env`, that link is included; otherwise the reply says to
  ask the server owner for the invite link. No invite URL is invented.
- Gated: all 32 AI-generation commands (`/ask`, `/chat`, `/explain`,
  `/summarize`, `/translate`, `/code`, `/debug`, `/rewrite`,
  `/brainstorm`, `/quiz`, `/image-prompt`, `/story`, `/poem`,
  `/essay`, `/email`, `/caption`, `/title`, `/grammar`, `/simplify`,
  `/expand`, `/compare`, `/proscons`, `/plan`, `/study`,
  `/interview`, `/resume`, `/cover-letter`, `/sql`, `/regex`,
  `/test-cases`, `/docstring`, `/refactor`) plus the AI-management
  commands `/aichat-clear`, `/aichat-history`, `/model-list`,
  `/model-set` — 36 commands in total.
- Not gated: `/ai-status` (intentionally ungated, so it can report
  the caller's membership status: `member` / `not a member` /
  `unknown` if the bot cannot see the guild) and all non-AI
  commands (tools, utility, fun, ping roles, support-lite).
- Requirement: **Server Members Intent** must be enabled both in
  code (`bot.py` sets `intents.members = True`) and in the Discord
  Developer Portal (Bot section, Privileged Gateway Intents),
  otherwise `fetch_member()` fails and uncached members will be
  treated as not visible to the bot.

## AI provider design — FREE tiers only

Pluggable OpenAI-compatible HTTP API (`ai_client.py`):

- Primary: `POST {AI_API_URL}/chat/completions` with `Bearer AI_API_KEY`
  and `AI_MODEL`. `AI_API_URL` may be a base URL or a full
  chat-completions URL.
- **Defaults are free:** `AI_API_URL=https://openrouter.ai/api/v1` and
  `AI_MODEL=meta-llama/llama-3.1-8b-instruct:free` in `.env.example` and
  in `config.py` / `ai_client.py`. No paid model is the default, and no
  key is hardcoded anywhere.

### Free providers documented (all free tiers, rate-limited, no paid key required)

| Provider | Sign up (free, with a Gmail account) | Endpoint | Example free model |
|---|---|---|---|
| OpenRouter (default) | https://openrouter.ai | https://openrouter.ai/api/v1 | `meta-llama/llama-3.1-8b-instruct:free` (any `:free` model) |
| Groq | https://console.groq.com | https://api.groq.com/openai/v1 | `llama-3.3-70b-versatile` |
| Google AI Studio / Gemini | https://aistudio.google.com | https://generativelanguage.googleapis.com/v1beta/openai | `gemini-2.0-flash` |
| Hugging Face | https://huggingface.co/settings/tokens | free inference tokens exist | availability varies; prefer the three above for a standard OpenAI-compatible call |

Free-tier honesty: free tiers have rate limits, quotas, and model
availability that changes over time. If a model returns 404 or a rate
limit error, check the provider's current free model list and update
`AI_MODEL` in `.env` — do not assume a paid upgrade is needed. This bot
never charges anything and never requires a paid key.

## Smart local mode — what happens with NO AI key

This bot does NOT just say "not configured" any more, and it does NOT
fake an AI answer either. With no key, every `/ask`-style command
(`cogs/ai.py` `_run`, via `smart_local.py`) replies with a clearly
labelled **local smart answer**: it restates your question, gives a
step-by-step approach and checklist for the kind of question it is
(code / study / Discord / language / writing / general), lists free
resources, suggests follow-up prompts, and explains how to enable free
AI. It is labelled "local smart answer — NOT an AI model reply" in
the message itself, so it can never be mistaken for a model.

Also free, with no key:
- **Daily tip:** `/ai-status` and `/help` show a rotating tip of the
  day (learning, prompts, safety, free AI) from `smart_local.py`.
- **Prompt suggestions:** `smart_local.prompt_suggestions(topic)`
  gives 5 starter prompts for any topic, used inside local answers.
- **Smart mode / remembered preferences:** your `/model-set` choice
  (and language/style if ever set) is stored in SQLite (`db.py`
  prefs table) and reused: for real AI calls it shapes the system
  prompt and model; for local answers it is shown back in
  `/ai-status` via `smart_local.smart_context()`. `/aichat-clear`
  clears conversation history; preferences are separate and persist.
- Non-AI commands (tools, utility, fun, ping roles, support-lite)
  always work with no AI key at all.

## Setup — the one step still needed from you: a FREE AI API key

This bot was built **without** signing up, logging in, or fetching any
key on your behalf, and **without** using any password. You need to do
this step yourself, once, and it costs nothing:

1. Pick a free tier from the table above and sign up with one of your
   Gmail accounts. Create a free API key (OpenRouter, Groq, or Google
   AI Studio are the recommended routes).
2. Copy `.env.example` to `.env` and fill in:
   ```
   DISCORD_TOKEN=<your NEWR AI bot token from the Developer Portal — never share it>
   GUILD_ID=1465422166790242377
   GUILD_INVITE_URL=<optional invite link shown to non-members by the gate; leave empty if none>
   AI_API_URL=https://openrouter.ai/api/v1
   AI_API_KEY=<your new FREE key>
   AI_MODEL=meta-llama/llama-3.1-8b-instruct:free
   ```
   To switch free provider, change only `AI_API_URL` and `AI_MODEL`
   to that provider's row in the table.
3. Install and run:
   ```
   pip install -r requirements.txt
   python test_load.py   # dry run, no token/key needed
   python bot.py
   ```
4. In Discord, check `/ai-status` — it shows configured: yes and the
   model, without ever showing the key. Then try `/ask`. Without a key,
   `/ask` still gives the labelled local smart answer above.

## Data

Conversation history, model preferences, notes and feedback live in
`data.db` (SQLite, local file only). Clear your AI history anytime with
`/aichat-clear`.

## Security notes

- No API key, bot token, password or secret is hardcoded anywhere.
- Never paste a token or API key into a Discord channel or chat — put
  it only in `.env`, which is not committed.
- The bot needs the "Manage Roles" permission and its bot role above
  the ping roles to add/remove them; otherwise those commands report
  the permission error instead of failing silently.

## Shared brain (one brain, two bots)

Both bots read and write the SAME SQLite file:
`~/workspace/bots/shared-brain/memory.db` (or `SHARED_BRAIN_DB` in
`.env`, which must be the same path for both bots). What Support
learns (tickets, reports, bugs, appeals) is visible to AI via
`recall_cross_bot`, and what AI learns (chats, preferences) is
visible to Support. The bots also talk to each other through the
`bot_messages` queue in that database: Support sends `ticket_update`
messages to AI, AI sends `ai_summary` messages to Support when a
user asks for staff/ticket help. Each bot polls its own inbox every
45 seconds, handles each message once, and marks it done in a
finally block; a bot never replies to a bot_message with a new
bot_message of the same kind, so the two bots cannot loop forever.
No passwords, tokens, or API keys are ever stored in the brain, and
`forget_user` deletes a user's rows across both bots.
