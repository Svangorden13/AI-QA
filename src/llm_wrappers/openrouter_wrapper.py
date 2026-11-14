import os
import time
from openai import OpenAI, APIError

client = None
init_called = False

OPEN_ROUTER_FREE="openrouter/free"

def init() -> None:
    global client, init_called

    if init_called == False:
        api_key = os.getenv("OPENROUTER_API_KEY")
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        init_called = True

def prompt(user_prompt, system_prompt="", model=OPEN_ROUTER_FREE, temperature=None, response_mime_type=None, addl_config_args=None) -> str:
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

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role":"system", "content":system_prompt},
                    {"role":"user", "content":user_prompt}
                ],
                response_format={"type":"json_object"},
            )
            time.sleep(15) # Wait 15 seconds to avoid rate limiting
            return {"text":response.choices[0].message.content,
                    "model_version":model}
        except APIError as e:
            if (e.status_code == 503 and attempt < 10) or (e.status_code == 429 and attempt < 2):
                wait = 60 if e.status_code == 429 else 2 # Wait full minute for 429 errors as it may be a per-minute rate limit
                print(f"Error {e.status_code}, waiting {wait}s then retrying...")
                time.sleep(wait)
                continue
            else:
                print(f"API Error: {e}")
                print("All attempts failed. Please check your API key and network connection.")
                raise e
            break

    # If we reach here, all attempts failed
    return ""