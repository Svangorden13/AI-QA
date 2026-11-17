import os
import time
import logging
import structlog
import prompt_builder
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from llm_wrappers.openrouter_wrapper import prompt as openrouter_prompt
from llm_wrappers.gemini_wrapper import prompt as gemini_prompt
from validation.llm_validator import validate_response
from openpyxl import load_workbook

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
        n_prompt = input("Enter number of prompts to use (default -1 for all) or prompt range (0 indexed): ") or -1
        use_responses_in_file = True if input("Use model responses from file (y/n)? ").lower() == "y" else False
        update_file_with_response = True if input("Update file with responses (y/n)? ").lower() == "y" else False
        system_prompt = prompt_builder.build_system_prompt()
        ids, user_prompts, responses = prompt_builder.from_file(text, n_prompt=n_prompt)
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

    for i in range(len(user_prompts)):
        user_prompt = user_prompts[i]
        id = ids[i]

        try:
            user_prompt = str(user_prompt)
        except Exception as e:
            logger.error("Error converting user prompt to string", error=str(e))
            return

        if use_responses_in_file == False:
            output = gemini_prompt(user_prompt, system_prompt)
            response = output["text"]
            model = output["model_version"]
        else:
            response = responses[i]
            model = "Unknown"
            
        if response != None:
            
            # If from file, validate response:
            if from_file:
                is_valid = validate_response(user_prompt, response, text, system_prompt)

                if update_file_with_response:
                    try:
                        write_response_to_file(id, response, is_valid, text)
                    except KeyError:
                        print("Continuing with next id")

                if not is_valid:
                    logger.error("Response validation failed", 
                                 system_prompt=system_prompt,
                                 user_prompt=user_prompt,
                                 response=response,
                                 time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                                 model=model,
                                 )
                    continue

            # TODO: Implement validating response based on passing prompt and response to LLM
            else:
                continue

            # Log prompt/response
            logger.info("prompt/response",
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response=response,
                        time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                        model=model,
                        )

        time.sleep(2)  # Sleep for 2 seconds to avoid rate limiting

def write_response_to_file(id, response, is_valid, file_name, sheet_name="Test Set"):
    wb = load_workbook(file_name)
    ws = wb[sheet_name]
    id_colnum = -1
    response_colnum = -1
    valid_colnum = -1

    for cell in ws[1]:
        if "id" == cell.value.lower():
            id_colnum = cell.col_idx
        if "response" in cell.value.lower() and "observed" in cell.value.lower():
            response_colnum = cell.col_idx
        if "response" in cell.value.lower() and "valid" in cell.value.lower():
            valid_colnum = cell.col_idx

    if id_colnum == -1:
        raise KeyError(f"Could not save response with ID {id} to file because no ID column found")

    if response_colnum == -1:
        response_colnum = ws.max_column + 1
        ws.cell(row=1, column=response_colnum, value="Observed Response")

    if valid_colnum == -1:
        valid_colnum = ws.max_column + 1
        ws.cell(row=1, column=valid_colnum, value="Valid Response")

    for row in range(2, ws.max_row + 1):
        if str(ws.cell(row=row, column=id_colnum).value) == str(id):
            ws.cell(row=row, column=response_colnum, value=response)
            ws.cell(row=row, column=valid_colnum, value="PASS" if is_valid else "FAIL")
            break

    wb.save(file_name)

if __name__ == "__main__":
    main()