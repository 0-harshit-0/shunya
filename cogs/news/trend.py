import discord
from discord.ext import commands

from utils.rate_limit import handle_rate_limit
from utils.ai import generate_response


class Trend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='trend')
    async def get_trend(self, ctx, *, topic: str):
        '''Provides the latest trends on a topic, limited to about 100 words.'''
        if not await handle_rate_limit(ctx):
            return
        if len(topic) > 100:
            return

        await ctx.send(f"Fetching the latest trends for '{topic}'...")
        print(f"-> Received /trend request for: {topic}")

        prompt = (
            f"Provide a concise, up-to-date summary in about 100 words on the latest trends "
            f"for '{topic.strip()}'. Focus on current popular information"
        )

        reply = await generate_response(prompt)
        await ctx.send(reply)

async def setup(bot):
    await bot.add_cog(Trend(bot))
