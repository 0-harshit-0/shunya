import discord
from discord.ext import commands

from utils.rate_limit import handle_rate_limit
from utils.ai import generate_response


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='weather')
    async def get_weather(self, ctx, *, location: str):
        """Provides the latest local weather and AQI for a location in ~100 words."""
        if not await handle_rate_limit(ctx):
            return
        if len(location) > 100:
            return

        await ctx.send("Fetching the latest weather report...")
        print(f"-> Received /weather request for: {location}")

        prompt = f"""
Act as a real-time weather reporter.
Provide an up-to-date report for '{location.strip()}' using the location's local time now.
Keep it around 90–110 words.

Output exactly these labeled lines, with no code fences:

Weather — {location.strip()}
• Now: <temp °C> (feels <feels °C>), <condition>; humidity <H%>, wind <S km/h> <dir>, gusts <G km/h>; precip <PoP%>.
• AQI: <value> — <category> (0–50 Good, 51–100 Moderate, 101–150 Unhealthy for Sensitive Groups, 151–200 Unhealthy, 201–300 Very Unhealthy, 301–500 Hazardous); primary: <pollutant>; advice: <short guidance>.
• Today: high <Hi °C>/low <Lo °C>; sunrise <time>, sunset <time>.
• Next 6–12h: <brief forecast>.

Notes:
- Use concise units (°C, km/h, %) and 24-hour local times.
- Include the AQI category name per the standard scale above and one-line health advice.
- If data is unavailable, state briefly which part is unavailable.
"""
        reply = await generate_response(prompt)
        await ctx.send(reply)

async def setup(bot):
    await bot.add_cog(Weather(bot))
