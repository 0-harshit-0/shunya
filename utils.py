import time
from collections import defaultdict

# --- Rate Limiting Variables ---
user_last_request_times = defaultdict(list)  # Store last 3 request times
user_daily_request_count = defaultdict(lambda: 0)
last_daily_reset_time = time.time()

# --- Rate Limiting Constants ---
REQUESTS_PER_MINUTE = 15
REQUESTS_PER_DAY = 100


async def handle_rate_limit(ctx):
    """A helper function to check and enforce rate limits for a user."""
    global last_daily_reset_time
    user_id = ctx.author.id
    current_time = time.time()

    # Reset daily counts if 24 hours have passed
    if current_time - last_daily_reset_time > 86400:
        user_daily_request_count.clear()
        user_last_request_times.clear()
        last_daily_reset_time = current_time
        print("Daily rate limits have been reset for all users.")

    # Remove request times older than 60 seconds
    user_last_request_times[user_id] = [
        req_time for req_time in user_last_request_times[user_id]
        if current_time - req_time < 60
    ]

    # Check per-minute limit (3 requests per minute)
    if len(user_last_request_times[user_id]) >= REQUESTS_PER_MINUTE:
        oldest_request = user_last_request_times[user_id][0]
        wait_time = int(60 - (current_time - oldest_request))
        await ctx.send(f"Please wait {wait_time} more seconds before your next request.")
        return False

    # Check daily limit
    if user_daily_request_count[user_id] >= REQUESTS_PER_DAY:
        await ctx.send(f"You have reached your daily limit of {REQUESTS_PER_DAY} requests. Please try again tomorrow.")
        return False

    # If all checks pass, update user data and allow the command
    user_last_request_times[user_id].append(current_time)
    user_daily_request_count[user_id] += 1
    return True


# ai_utils.py
import os
from google import genai
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = "gemini-2.5-flash-lite"

# Single shared client; uses GEMINI_API_KEY/GOOGLE_API_KEY env automatically
client = genai.Client(api_key=GEMINI_API_KEY)

# Async helper for Discord commands
async def generate_response(prompt: str, enable_search: bool = True) -> str:
    tools = []
    if enable_search:
        # Enable Google Search grounding
        tools = [types.Tool(google_search=types.GoogleSearch())]

    # Use the async client
    aclient = client.aio
    resp = await aclient.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=tools,
        ),
    )
    # print(resp.text)
    return resp.text or "No response."
