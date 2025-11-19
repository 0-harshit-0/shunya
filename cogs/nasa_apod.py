import os
import json
import aiohttp
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
STATE_FILE = "global_cache/apod_state.json"

load_dotenv()

def load_last_post_time() -> datetime | None:
  if not os.path.exists(STATE_FILE):
    return None
  try:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
      data = json.load(f)
    ts = data.get("last_post_utc")
    if not ts:
      return None
    return datetime.fromisoformat(ts)
  except Exception:
    return None


def save_last_post_time(dt: datetime) -> None:
  data = {"last_post_utc": dt.replace(tzinfo=timezone.utc).isoformat()}
  with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f)


class Apod(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.channel_id = int(os.getenv("APOD_CHANNEL_ID")) # entertainment-channel-id
    self.apod_task.start()

  def cog_unload(self):
    self.apod_task.cancel()

  @tasks.loop(hours=1)  # check hourly, but enforce 24h via timestamp
  async def apod_task(self):
    if not self.channel_id:
        return

    last_post = load_last_post_time()
    now = datetime.now(timezone.utc)
    if last_post and now - last_post < timedelta(hours=24):
        return

    channel = self.bot.get_channel(self.channel_id)
    if channel is None:
        return

    data = await self.fetch_apod()
    if not data:
        await channel.send("Could not fetch NASA APOD.")
        return

    title = data.get("title", "Astronomy Picture of the Day")
    explanation = data.get("explanation", "")
    media_type = data.get("media_type")
    url = data.get("url")
    hdurl = data.get("hdurl")
    thumb = data.get("thumbnail_url")

    embed = discord.Embed(
        title=title,
        description=explanation[:2048],
        color=discord.Color.blue(),
    )
    embed.set_footer(text=f"Date: {data.get('date', 'Unknown')} • APOD")

    # Default: no extra content
    content = None

    if media_type == "image" and (hdurl or url):
        embed.set_image(url=hdurl or url)
        # just send the embed
        content = None

    elif media_type == "video" and url:
        # show a thumbnail if provided
        if thumb:
            embed.set_image(url=thumb)
        # put the video URL in message content so Discord auto-embeds it
        content = url

    # Send message
    await channel.send(content or "", embed=embed)

    save_last_post_time(now)

  @apod_task.before_loop
  async def before_apod_task(self):
    await self.bot.wait_until_ready()

  async def fetch_apod(self):
    api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    params = {"api_key": api_key, "thumbs": True}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(NASA_APOD_URL, params=params, timeout=15) as resp:
                if resp.status != 200:
                    print(f"[APOD] Error from NASA API: {resp.status} {await resp.text()}")
                    return None
                return await resp.json()
        except Exception as e:
            print(f"[APOD] Exception while fetching APOD: {e}")
            return None

async def setup(bot: commands.Bot):
  await bot.add_cog(Apod(bot))
