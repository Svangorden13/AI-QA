print("Python is running")
from gemini_wrapper import prompt

def main() -> None:
    print("Start")
    prompt("Explain how AI works in a few words")
    print("Done")

if __name__ == "__main__":
    main()