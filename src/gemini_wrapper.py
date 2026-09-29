import os
from google import genai

client = None

GEMINI_API_KEY = "AIzaSyCPEvlOBbI4SdmSepUepBox42ftLvUNJkM"

def init() -> None:
    global client
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    client = genai.Client(api_key=GEMINI_API_KEY)

def prompt(text):
    init()
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=text
    )
    print(interaction.output_text)