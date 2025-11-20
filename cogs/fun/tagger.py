import os
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()

class RandomTagger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.random_ping.started = False
        # Start the loop when the cog is loaded
        # self.random_ping.start()

    @commands.Cog.listener()
    async def on_ready(self):
        # Start only once, after bot is fully ready
        if not self.random_ping.started:
            self.random_ping.start()
            self.random_ping.started = True

    def cog_unload(self):
        if self.random_ping.is_running():
            self.random_ping.cancel()

    @tasks.loop(hours=1)
    async def random_ping(self):
        """
        Every 12 hours, tag a random user in a specific channel
        with a light‑hearted, non‑sensitive message.
        """
        GUILD_ID = int(os.getenv("SERVER_ID"))
        CHANNEL_ID = int(os.getenv("GENERAL_2"))

        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            print("no guild")
            return  # Bot might not be in the guild yet

        channel = guild.get_channel(CHANNEL_ID)
        if channel is None:
            print("no channel")
            return

        # Get a list of human members only (exclude bots)
        members = [m for m in guild.members if not m.bot]
        if not members:
            return

        member = random.choice(members)

        # Super‑light, non‑sensitive, “Discord‑style” messages
        funny_templates = [
            "Hey {mention}, you just got picked by the randomness god. How’s it going?",
            "{mention}, friendly check‑in: have you touched grass today?",
            "Alert {mention}: you’ve been randomly selected for a free smile. 😄",
            "Breaking news, {mention}: you are officially the main character for the next 5 minutes.",
            "{mention}, this is your scheduled reminder that you’re pretty cool.",
            "Psst {mention}, if this was a cringe ping, blame RNG, not me.",
            "{mention}, fun fact: you’re today’s lucky ping winner. No prize, just vibes.",
            "Hey {mention}, I'm on a seafood diet. I see food, and I eat it.",
            "Psst {mention}, you smell like pasta. Stand back!",
            "{mention}, if history repeats itself, I’m getting a dinosaur pet.",
            "Hey {mention}, I’m out of my mind. Be back in 5 minutes.",
            "Hey {mention}, do you ever accidentally eat a whole pint of ice cream?",
            "{mention}, what’s the weirdest thing you’ve ever eaten?",
            "{mention}, if you could have any superpower, what would it be and why?",
            "Hey {mention}, what's your go-to karaoke song?",
            "{mention}, what's the most useless talent you have?",
            "{mention}, this is your refrigerator. Please speak very slowly, and I’ll stick your message to myself with one of these magnets.",
            "Hey {mention}, most likely to have 100 tabs open at once.",
            "{mention}, most likely to be sharing the wrong screen in a meeting.",
        ]


        template = random.choice(funny_templates)
        message = template.format(mention=member.mention)

        try:
            await channel.send(message)
        except discord.HTTPException:
            print("error")
            # If message fails (rate limits or perms), just ignore
            pass

    @random_ping.before_loop
    async def before_random_ping(self):
        # Wait until the bot is ready before starting the loop
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(RandomTagger(bot))
