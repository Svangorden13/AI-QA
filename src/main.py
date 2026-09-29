import os
from dotenv import load_dotenv
from gemini_wrapper import prompt

def init():
    # Get the directory where this script is saved
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Point directly to the .env file in the same directory
    env_path = os.path.join(script_dir, '.env')

    # Explicitly load the file from that absolute path
    load_dotenv(dotenv_path=env_path)

def main() -> None:
    init()
    prompt("Explain how AI works in a few words")

if __name__ == "__main__":
    main()