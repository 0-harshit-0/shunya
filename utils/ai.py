
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
