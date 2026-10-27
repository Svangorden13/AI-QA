import os
import time
import logging
import structlog
import prompt_builder
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from gemini_wrapper import prompt
from response_validator import validate_response

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

    prompt_builder.create_user_prompts()

def main() -> None:
    init()
    logger = structlog.get_logger()
    from_file = False
    text = input("Enter prompt or file: ")

    if text == "":
        system_prompt = prompt_builder.build_system_prompt()
        user_prompts = prompt_builder.build_user_prompt()
    elif text.isdigit():
        system_prompt = prompt_builder.build_system_prompt()
        user_prompts = prompt_builder.build_user_prompt(int(text))
    elif Path(text).exists() and Path(text).is_file():
        system_prompt = prompt_builder.build_system_prompt()
        user_prompts = prompt_builder.from_file(text, n_prompt=1)
        from_file = True
    else:
        system_prompt = ""
        user_prompts = text

    try:
        system_prompt = str(system_prompt)
    except Exception as e:
        logger.error("Error converting system prompt to string", error=str(e))
        return

    if isinstance(user_prompts, str):
        user_prompts = [user_prompts]

    for user_prompt in user_prompts:

        try:
            user_prompt = str(user_prompt)
        except Exception as e:
            logger.error("Error converting user prompt to string", error=str(e))
            return

        output = prompt(system_prompt, user_prompt)
        if output != None:
            
            # If from file, validate response:
            if from_file:
                is_valid = validate_response(user_prompt, output.text, text, system_prompt)
                if not is_valid:
                    logger.error("Response validation failed", 
                                 system_prompt=system_prompt,
                                 user_prompt=user_prompt,
                                 response=output.text,
                                 time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                                 model=output.model_version,
                                 )
                    continue

            # Log prompt/response
            logger.info("prompt/response",
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response=output.text,
                        time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                        model=output.model_version,
                        )

        time.sleep(2)  # Sleep for 2 seconds to avoid rate limiting

if __name__ == "__main__":
    main()