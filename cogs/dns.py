import discord
from discord.ext import commands

from dns.main import resolver  # Import from your custom dns module
from utils import handle_rate_limit

class Dns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dns')
    async def resolve_dns(self, ctx, *, url: str):
        """Checks if a website is up or down."""
        if not await handle_rate_limit(ctx):
            return

        # if not url.startswith(('http://', 'https://')):
        #     url = 'https://' + url

        await ctx.send(f"Resolving '{url}'...")
        print(f"-> Received /dns request for: {url}")

        try:
            data = resolver(url)
            ips = list(map(lambda x: x[0], data))
            print(ips, "ip")
            await ctx.send(f"ips: {ips}")
        except Exception as e:
            print(e, "exception")
            await ctx.send(f"❌ somthing went wrong")

async def setup(bot):
    await bot.add_cog(Dns(bot))
