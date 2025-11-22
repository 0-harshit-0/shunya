import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from utils.terminal_ascii import outsourced1

# --- Configuration ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# --- Bot Subclass ---
# We subclass commands.Bot to use setup_hook correctly
class ShunyaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='/', intents=intents, help_command=None)

    async def setup_hook(self):
        """
        This is called ONCE when the bot starts, BEFORE on_ready.
        Load extensions (Cogs) here to ensure they are registered before sync.
        """
        print("Loading cogs...")
        for root, dirs, files in os.walk('./cogs'):
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            for filename in files:
                if filename.endswith('.py') and filename != '__init__.py' and filename != 'tagger.py':
                    file_path = os.path.join(root, filename)
                    module_name = os.path.relpath(file_path, '.').replace(os.path.sep, '.')[:-3]
                    try:
                        await self.load_extension(module_name)
                        print(f'✅ Successfully loaded: {module_name}')
                    except Exception as e:
                        print(f'❌ Failed to load: {module_name}')
                        print(f'   Error: {e}')
        
        # Optional: Sync strictly to a test guild for instant updates during dev
        # TEST_GUILD = discord.Object(id=YOUR_SERVER_ID_HERE)
        # self.tree.copy_global_to(guild=TEST_GUILD)
        # await self.tree.sync(guild=TEST_GUILD)

# --- Instantiate Bot ---
bot = ShunyaBot()

@bot.event
async def on_ready():
    """Event triggered when Shunya is ready."""
    # Syncing globally in on_ready is okay, but better to do it on demand or 
    # if you are sure everything is loaded. Since we loaded in setup_hook, we are safe.
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s) globally.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    print(outsourced1)
    print(f'Shunya logged in as {bot.user}')
    print('Ready with /trap, /shodan, /asc, /tarot, /weather, /ping, /dns, and /help commands.')


# --- Help Command ---
@bot.hybrid_command(name="help", description="Shows help message")
async def help_command(ctx):
    """Lists all available commands with a brief description."""
    embed = discord.Embed(
        title="Shunya – Command Reference",
        description=(
            "A calm, minimalist assistant for security, OSINT, utilities, and a bit of fun.\n"
            "Here is a list of all available commands and what they do:"
        ),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="/shodan",
        value=(
            "Searches Shodan for internet-facing devices.\n"
            "• Usage: `/shodan <query>`\n"
            "• Returns up to 5 summary results from the Shodan API"
        ),
        inline=False
    )

    embed.add_field(
        name="/asc",
        value=(
            "Converts text into big ASCII art.\n"
            "• Usage: `/asc <text>`\n"
            "• Max 20 characters; very large art may be refused"
        ),
        inline=False
    )

    embed.add_field(
        name="/tarot",
        value=(
            "Draws 3 tarot cards (per user, per day).\n"
            "• Repeat today: returns your original draw\n"
            "• Cache resets daily at 00:00 server time"
        ),
        inline=False
    )

    embed.add_field(
        name="/weather `<location>`",
        value=(
            "Get live weather and AQI for the location:\n"
            "• Now: temp, feels-like, condition; humidity, wind/gusts, precip chance\n"
            "• AQI: value & category; primary pollutant; brief health advice\n"
            "• Today: high/low; sunrise/sunset\n"
            "• Next 6–12h: brief outlook"
        ),
        inline=False
    )

    embed.add_field(
        name="/ping `<url>`",
        value=(
            "Checks whether a site is online and responding.\n"
            "• Useful for quick uptime checks on your services"
        ),
        inline=False
    )

    embed.add_field(
        name="/dns `<url>`",
        value=(
            "Resolves a domain to its IPv4 address using a custom DNS resolver.\n"
            "• Resolver created by @gromaxhi"
        ),
        inline=False
    )

    embed.add_field(
        name="/trap `<eth_address>`",
        value=(
            "Heuristically checks if an Ethereum wallet might behave like a trap/honeypot.\n"
            "• Usage: `/trap <0x-address> [limit]`\n"
            "• This is a weak heuristic only and **not** a guaranteed scam detector"
        ),
        inline=False
    )

    embed.add_field(
        name="/help",
        value="Shows this help message.",
        inline=False
    )

    embed.add_field(
        name="APOD (NASA Astronomy Picture of the Day)",
        value=(
            "Automatically posts the latest Astronomy Picture of the Day once every 24 hours "
            "to a configured channel."
        ),
        inline=False
    )

    embed.add_field(
        name="Random ping (fun cog)",
        value=(
            "Every 12 hours, randomly tags a non-bot member in a configured server/channel "
            "with a light, non-sensitive, Discord-style message."
        ),
        inline=False
    )

    embed.add_field(
        name="Source code",
        value="GitHub: https://github.com/0-harshit-0/shunya",
        inline=False
    )

    embed.set_footer(
        text="Shunya – calm automation with sharp tools | Rate limit: 15 req/min, 100 req/day per user."
    )

    await ctx.send(embed=embed)



# --- Main Entry ---
async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN is not set.")
    else:
        asyncio.run(main())


