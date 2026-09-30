import os
import time
from google import genai
from google.genai.types import HttpOptions
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

def prompt(text):
    init()
    # Try up to 3 times if the server returns a 503 overload error
    for attempt in range(3):
        try:
            chat = client.chats.create(model=GEMINI_MODEL_WORKING)
            response = chat.send_message(text)
            print(response.text)
            return response
        except APIError as e:
            if e.code == 503 and attempt < 2:
                time.sleep(2)  # Wait 2 seconds and try again
                continue
            print(f"API Error: {e}")
            break