import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

client = None
init_called = False

GEMINI_MODEL = "models/gemini-2.5-flash"
GEMINI_MODEL_WORKING = "models/gemini-3.5-flash"
GEMINI_MODEL_LATEST = "models/gemini-3.8-flash"

def init() -> None:
    global client, init_called

    if init_called == False:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(
            api_key=api_key,
            vertexai=False
        )
        init_called = True

def prompt(system_prompt, user_prompt):
    init()
    # Try up to 3 times if the server returns a 429 or 503 error
    for attempt in range(3):
        try:
            chat = client.chats.create(
                model=GEMINI_MODEL_WORKING,
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )
            response = chat.send_message(user_prompt)
            time.sleep(15) # Wait 15 seconds to avoid rate limiting
            return response
        except APIError as e:
            if e.code in (429, 503) and attempt < 2:
                wait = 60 if e.code == 429 else 2 # Wait full minute for 429 errors as it may be a per-minute rate limit
                print(f"Error {e.code}, waiting {wait}s then retrying...")
                time.sleep(wait)
                continue
            print(f"API Error: {e}")
            break

    # If we reach here, all attempts failed
    print("All attempts failed. Please check your API key and network connection.")
    return ""