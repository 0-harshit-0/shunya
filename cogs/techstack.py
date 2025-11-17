import discord
from discord.ext import commands

from utils import handle_rate_limit, generate_response

class TechStack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='techstack')
    async def get_tech_stack(self, ctx, *, company_domain: str):
        '''Finds the tech stack for a company, limited to about 100 words.'''
        if not await handle_rate_limit(ctx):
            return
        if len(company_domain) > 300:
            return

        await ctx.send(f"Searching for the tech stack of '{company_domain}'...")
        print(f"-> Received /techstack request for: {company_domain}")

        prompt = (
            f"In approximately 100 words, what is the likely technology stack used by the "
            f"company with the domain '{company_domain.strip()}'? Focus on the key technologies for "
            f"backend, frontend, database, and cloud infrastructure."
        )

        reply = await generate_response(prompt)
        await ctx.send(reply)

async def setup(bot):
    await bot.add_cog(TechStack(bot))
