import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

client = None
init_called = False

GEMINI_MODEL_2_5 = "models/gemini-2.5-flash"
GEMINI_MODEL_3_5 = "models/gemini-3.5-flash"
GEMINI_MODEL_3_5_LITE = "models/gemini-3.5-flash-lite"
GEMINI_MODEL_3_8 = "models/gemini-3.8-flash"
GEMMA_MODEL_4 = "models/gemma-4-31b-it"

def init() -> None:
    global client, init_called

    if init_called == False:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(
            api_key=api_key,
            vertexai=False,
            http_options=types.HttpOptions(timeout=60_000),
        )
        init_called = True

def prompt(user_prompt, system_prompt="", model=GEMINI_MODEL_3_5_LITE, temperature=None, response_mime_type=None, addl_config_args=None) -> str:
    init()
    # Try up to 3 times if the server returns a 429 or 503 error
    for attempt in range(11):
        try:
            config_args = {
                "system_instruction": system_prompt,
            }

            if temperature is not None:
                config_args["temperature"] = temperature
            if response_mime_type is not None:
                config_args["response_mime_type"] = response_mime_type

            if addl_config_args:
                for key, value in addl_config_args.items():
                    config_args[key] = value

            chat = client.chats.create(
                model=model,
                config = types.GenerateContentConfig(**config_args)
            )
            response = chat.send_message(user_prompt)
            time.sleep(15) # Wait 15 seconds to avoid rate limiting
            return {"text": response.text,
                    "model_version": response.model_version}
        except APIError as e:
            if e.code == 503 and attempt < 10 or e.code == 429 and attempt < 2:
                wait = 60 if e.code == 429 else 2 # Wait full minute for 429 errors as it may be a per-minute rate limit
                print(f"Error {e.code}, waiting {wait}s then retrying...")
                time.sleep(wait)
                continue
            else:
                print(f"API Error: {e}")
                print("All attempts failed. Please check your API key and network connection.")
                raise e
            break

    # If we reach here, all attempts failed
    return ""