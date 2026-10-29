"""Fun cog: 9 slash commands, all local."""
import discord, random
from discord import app_commands
from discord.ext import commands

JOKES = ["Why do programmers prefer dark mode? Because light attracts bugs.",
         "I told a UDP joke once. I am not sure if anyone got it.",
         "Why did the developer go broke? He used up all his cache.",
         "There are only 10 kinds of people: those who understand binary and those who do not."]
FACTS = ["Honey never spoils.", "Octopuses have three hearts.", "Bananas are berries, but strawberries are not.",
         "The first computer bug was a real moth.", "Sharks existed before trees."]
BALL = ["Yes.", "No.", "Ask again later.", "Definitely.", "Very doubtful.", "Most likely.", "Cannot predict now."]

class Fun(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="dice", description="Roll dice")
    async def dice(self, it: discord.Interaction, sides: int = 6, count: int = 1):
        if not 2 <= sides <= 100 or not 1 <= count <= 10: await it.response.send_message("Sides 2-100, count 1-10.", ephemeral=True); return
        rolls = [random.randint(1, sides) for _ in range(count)]
        await it.response.send_message(f"Rolled: {', '.join(map(str, rolls))} (total {sum(rolls)})")

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, it: discord.Interaction):
        await it.response.send_message(f"Coin: **{random.choice(['Heads', 'Tails'])}**")

    @app_commands.command(name="8ball", description="Ask the magic 8-ball")
    async def eightball(self, it: discord.Interaction, question: str):
        await it.response.send_message(f"{question}\n🎱 {random.choice(BALL)}")

    @app_commands.command(name="joke", description="Tell a programming joke")
    async def joke(self, it: discord.Interaction):
        await it.response.send_message(random.choice(JOKES))

    @app_commands.command(name="fact", description="Share a fun fact")
    async def fact(self, it: discord.Interaction):
        await it.response.send_message(random.choice(FACTS))

    @app_commands.command(name="rps", description="Play rock-paper-scissors against the bot")
    async def rps(self, it: discord.Interaction, choice: str):
        choice = choice.lower()
        if choice not in ("rock", "paper", "scissors"): await it.response.send_message("Choose rock, paper, or scissors.", ephemeral=True); return
        bot = random.choice(["rock", "paper", "scissors"])
        win = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        result = "Tie!" if bot == choice else ("You win!" if win[choice] == bot else "Bot wins!")
        await it.response.send_message(f"You: {choice} | Bot: {bot} | {result}")

    @app_commands.command(name="compliment", description="Give someone a compliment")
    async def compliment(self, it: discord.Interaction, user: discord.User = None):
        u = user or it.user
        await it.response.send_message(f"{u.mention}, you are doing great — keep it up! ✨")

    @app_commands.command(name="fortune", description="Get a fortune-cookie style message")
    async def fortune(self, it: discord.Interaction):
        await it.response.send_message(random.choice(["A pleasant surprise is coming.", "Your code will compile on the first try today.", "Good news arrives soon.", "Patience will pay off this week."]))

    @app_commands.command(name="would-you-rather", description="A would-you-rather question")
    async def would_you_rather(self, it: discord.Interaction):
        await it.response.send_message(random.choice(["Would you rather: fly or be invisible?", "Would you rather: always be 10 minutes early or 10 minutes late?", "Would you rather: code without internet or without coffee?"]))

async def setup(bot):
    await bot.add_cog(Fun(bot))
