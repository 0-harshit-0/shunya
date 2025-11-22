import discord
from discord.ext import commands
import pyfiglet


class Ascii(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="asc")
    async def ascii_text(self, ctx, *, text: str):
        """
        Convert text to ASCII art, e.g. !asc gn -> big ASCII 'gn'.
        """
        # Guard so you don't blow past Discord's 2000‑char limit
        if len(text) > 20:
            await ctx.send("Please use 20 characters or fewer for ASCII art.")
            return

        # Delete the user's command message (requires Manage Messages permission)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("no permission")
            # Bot lacks permissions; optionally ignore or log
            pass
        except discord.HTTPException:
            # Some other deletion error; optionally ignore or log
            pass

        try:
            art = pyfiglet.figlet_format(text)
        except Exception as e:
            await ctx.send(f"Error while generating ASCII art: {e}")
            return

        # Wrap the art in a code block
        message = f"```{art}```"

        if len(message) > 2000:
            await ctx.send("The ASCII art is too large to send. Try a shorter text.")
            return

        await ctx.send(message)


async def setup(bot):
    await bot.add_cog(Ascii(bot))
