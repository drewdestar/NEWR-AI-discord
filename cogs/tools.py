"""Tools cog: 20 slash commands using only no-key public APIs or pure Python."""
import discord, ast, operator, random, hashlib, base64, uuid, re, json, urllib.request, urllib.parse
from discord import app_commands
from discord.ext import commands

def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NEWR-AI-bot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def _safe_eval(node):
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
    if isinstance(node, ast.Expression): return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in ops: return ops[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ops: return ops[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")

class Tools(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="calc", description="Calculate a math expression safely")
    async def calc(self, it: discord.Interaction, expression: str):
        try: await it.response.send_message(f"{expression} = {_safe_eval(ast.parse(expression, mode='eval'))}")
        except Exception as e: await it.response.send_message(f"Could not calculate that: {e}", ephemeral=True)

    @app_commands.command(name="convert-temp", description="Convert temperature between C and F")
    async def convert_temp(self, it: discord.Interaction, value: float, from_unit: str):
        if from_unit.upper() == "C": await it.response.send_message(f"{value}°C = {value*9/5+32:.2f}°F")
        elif from_unit.upper() == "F": await it.response.send_message(f"{value}°F = {(value-32)*5/9:.2f}°C")
        else: await it.response.send_message("Use C or F for from_unit.", ephemeral=True)

    @app_commands.command(name="convert-length", description="Convert metres to feet and vice versa")
    async def convert_length(self, it: discord.Interaction, value: float, from_unit: str):
        if from_unit.lower() in ("m", "metre", "meter"): await it.response.send_message(f"{value} m = {value*3.28084:.2f} ft")
        elif from_unit.lower() in ("ft", "feet"): await it.response.send_message(f"{value} ft = {value/3.28084:.2f} m")
        else: await it.response.send_message("Use m or ft.", ephemeral=True)

    @app_commands.command(name="convert-weight", description="Convert kg to lb and vice versa")
    async def convert_weight(self, it: discord.Interaction, value: float, from_unit: str):
        if from_unit.lower() == "kg": await it.response.send_message(f"{value} kg = {value*2.20462:.2f} lb")
        elif from_unit.lower() == "lb": await it.response.send_message(f"{value} lb = {value/2.20462:.2f} kg")
        else: await it.response.send_message("Use kg or lb.", ephemeral=True)

    @app_commands.command(name="convert-currency", description="Convert currency via a free no-key rates API")
    async def convert_currency(self, it: discord.Interaction, amount: float, from_currency: str, to_currency: str):
        try:
            data = _get_json(f"https://api.frankfurter.app/latest?from={from_currency.upper()}&to={to_currency.upper()}")
            rate = data["rates"][to_currency.upper()]
            await it.response.send_message(f"{amount} {from_currency.upper()} = {amount*rate:.2f} {to_currency.upper()} (rate {rate}, date {data.get('date')})")
        except Exception as e: await it.response.send_message(f"Currency conversion failed: {e}", ephemeral=True)

    @app_commands.command(name="weather-info", description="Current weather for a city, via Open-Meteo (no key)")
    async def weather_info(self, it: discord.Interaction, city: str):
        try:
            g = _get_json(f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1")
            if not g.get("results"): await it.response.send_message(f"City not found: {city}", ephemeral=True); return
            loc = g["results"][0]
            w = _get_json(f"https://api.open-meteo.com/v1/forecast?latitude={loc['latitude']}&longitude={loc['longitude']}&current=temperature_2m,wind_speed_10m,relative_humidity_2m,weather_code")
            c = w["current"]
            await it.response.send_message(f"Weather in {loc['name']}, {loc.get('country','')}: {c['temperature_2m']}°C, humidity {c['relative_humidity_2m']}%, wind {c['wind_speed_10m']} km/h, code {c['weather_code']}.")
        except Exception as e: await it.response.send_message(f"Weather lookup failed: {e}", ephemeral=True)

    @app_commands.command(name="define", description="Define an English word via a free dictionary API")
    async def define(self, it: discord.Interaction, word: str):
        try:
            data = _get_json(f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}")
            defs = []
            for meaning in data[0].get("meanings", [])[:2]:
                for d in meaning.get("definitions", [])[:2]: defs.append(f"({meaning.get('partOfSpeech','')}) {d['definition']}")
            await it.response.send_message(f"**{word}**\n" + "\n".join(defs) if defs else f"No definition found for {word}.")
        except Exception as e: await it.response.send_message(f"Definition lookup failed: {e}", ephemeral=True)

    @app_commands.command(name="search-web", description="Summarise the top DuckDuckGo instant answer for a query (no key)")
    async def search_web(self, it: discord.Interaction, query: str):
        try:
            data = _get_json(f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1")
            text = data.get("AbstractText") or data.get("Answer") or ""
            topics = [t.get("Text","") for t in data.get("RelatedTopics", [])[:3] if isinstance(t, dict)]
            out = text or ("Related: " + " | ".join(topics) if topics else "No instant answer found. Try a more specific query.")
            await it.response.send_message(out[:1900])
        except Exception as e: await it.response.send_message(f"Web search failed: {e}", ephemeral=True)

    @app_commands.command(name="base64-encode", description="Base64-encode text")
    async def b64e(self, it: discord.Interaction, text: str):
        await it.response.send_message(base64.b64encode(text.encode()).decode())

    @app_commands.command(name="base64-decode", description="Base64-decode text")
    async def b64d(self, it: discord.Interaction, text: str):
        try: await it.response.send_message(base64.b64decode(text).decode())
        except Exception as e: await it.response.send_message(f"Invalid base64: {e}", ephemeral=True)

    @app_commands.command(name="hash", description="Hash text with SHA-256")
    async def hash_cmd(self, it: discord.Interaction, text: str):
        await it.response.send_message(f"SHA-256: `{hashlib.sha256(text.encode()).hexdigest()}`")

    @app_commands.command(name="password", description="Generate a random password (shown only to you)")
    async def password(self, it: discord.Interaction, length: int = 16):
        if not 8 <= length <= 64: await it.response.send_message("Length must be 8-64.", ephemeral=True); return
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        await it.response.send_message(f"Your generated password: `{''.join(random.SystemRandom().choice(chars) for _ in range(length))}`", ephemeral=True)

    @app_commands.command(name="uuid", description="Generate a UUID")
    async def uuid_cmd(self, it: discord.Interaction):
        await it.response.send_message(f"`{uuid.uuid4()}`")

    @app_commands.command(name="random-number", description="Pick a random number in a range")
    async def random_number(self, it: discord.Interaction, minimum: int, maximum: int):
        if minimum > maximum: await it.response.send_message("Minimum must be <= maximum.", ephemeral=True); return
        await it.response.send_message(f"Random number: {random.randint(minimum, maximum)}")

    @app_commands.command(name="random-choice", description="Pick one item from a comma-separated list")
    async def random_choice(self, it: discord.Interaction, options: str):
        items = [x.strip() for x in options.split(",") if x.strip()]
        await it.response.send_message(f"Picked: **{random.choice(items)}**" if items else "Give at least one option.", ephemeral=True)

    @app_commands.command(name="count-words", description="Count words and characters in text")
    async def count_words(self, it: discord.Interaction, text: str):
        await it.response.send_message(f"Words: {len(text.split())}, characters: {len(text)}, lines: {text.count(chr(10))+1}")

    @app_commands.command(name="title-text", description="Convert text to Title Case")
    async def title_text(self, it: discord.Interaction, text: str):
        await it.response.send_message(text.title())

    @app_commands.command(name="url-encode", description="URL-encode text")
    async def url_encode(self, it: discord.Interaction, text: str):
        await it.response.send_message(urllib.parse.quote(text))

    @app_commands.command(name="binary", description="Convert text to binary")
    async def binary(self, it: discord.Interaction, text: str):
        await it.response.send_message(" ".join(format(ord(c), "08b") for c in text)[:1900])

    @app_commands.command(name="hex", description="Convert text to hex")
    async def hex_cmd(self, it: discord.Interaction, text: str):
        await it.response.send_message(text.encode().hex())

async def setup(bot):
    await bot.add_cog(Tools(bot))
