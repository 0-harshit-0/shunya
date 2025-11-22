# tarot_cog.py
import datetime
import discord
from discord.ext import commands, tasks

from utils.rate_limit import handle_rate_limit
from utils.tarot.tarot_cache import TarotStore

# Use your preferred timezone; Asia/Kolkata shown here
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30), name="IST")
MIDNIGHT = datetime.time(0, 0, tzinfo=IST) 

class Tarot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.store = TarotStore()
        self.daily_clear.start()

    def cog_unload(self):
        # Stop task and close LMDB on unload
        self.daily_clear.cancel()
        self.store.close()

    @tasks.loop(time=MIDNIGHT)
    async def daily_clear(self):
        # Clear all per-day entries at local midnight
        self.store.clear_all()

    @daily_clear.before_loop
    async def before_daily_clear(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name='tarot')
    async def tarot(self, ctx):
        """Draws 3 tarot cards per user per day; repeat calls return your previous draw for today."""
        if not await handle_rate_limit(ctx):
            return

        user_id = ctx.author.id
        try:
            cards = self.store.get_or_create_today_cards(user_id, IST)
            await ctx.send(self._format_cards(ctx.author.mention, cards))
        except Exception as e:
            await ctx.send(f"Could not retrieve cards right now: {e}")

    def _format_cards(self, mention: str, cards: list) -> str:
        lines = [f"{mention} your three cards:"]
        for idx, card in enumerate(cards[:3], start=1):
            name = card.get("name", "Unknown")
            meaning = card.get("meaning_up", "") or card.get("meaning_rev", "")
            lines.append(f"{idx}. {name} — {meaning}")
        return "\n".join(lines)

async def setup(bot):
    await bot.add_cog(Tarot(bot))
