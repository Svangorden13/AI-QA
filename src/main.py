import os
import logging
import structlog
from datetime import datetime
from dotenv import load_dotenv
from gemini_wrapper import prompt

def init():
    # Get path to .env and log files
    src_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    env_path = os.path.join(src_dir, '.env')
    logs_path = os.path.join(logs_dir, "log.jsonl")

    # Load environment variables from .env file
    load_dotenv(dotenv_path=env_path)

    # Define a standard Python FileHandler
    file_handler = logging.FileHandler(logs_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    # Setup a specific logger
    app_logger = logging.Logger("prompt_response_logger", level=logging.INFO)
    app_logger.addHandler(file_handler)
    app_logger.propagate = False 

    # Configure structlog to use new logger
    structlog.configure(
        processors=[
            structlog.processors.JSONRenderer()
        ],
        # Force structlog to bind to your clean, isolated app logger
        logger_factory=lambda: app_logger, 
    )

def main() -> None:
    init()
    text = input("Enter prompt: ")
    output = prompt(text)

    if output != None:
        # Log prompt/response
        logger = structlog.get_logger()
        logger.info("prompt/response",
                    prompt=text,
                    response=output.text,
                    time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                    model=output.model_version,
                    )

if __name__ == "__main__":
    main()