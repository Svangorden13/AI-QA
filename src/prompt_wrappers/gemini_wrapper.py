import os
from typing import Any, Dict, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError
from .base_one_shot_prompt_wrapper import BaseOSPWrapper

GEMINI_MODEL_2_5 = "models/gemini-2.5-flash"
GEMINI_MODEL_3_5 = "models/gemini-3.5-flash"
GEMINI_MODEL_3_5_LITE = "models/gemini-3.5-flash-lite"
GEMINI_MODEL_3_8 = "models/gemini-3.8-flash"
GEMMA_MODEL_4 = "models/gemma-4-31b-it"


class GeminiWrapper(BaseOSPWrapper, provider_name="gemini"):
    def __init__(
        self,
        model: str = GEMINI_MODEL_3_5_LITE,
        model_timeout: int = 60_000,
        rate_limit_sleep: float = 15.0,
        max_attempts: int = 11,
    ) -> None:
        super().__init__(
            model=model,
            timeout=model_timeout,
            rate_limit_sleep=rate_limit_sleep,
            max_attempts=max_attempts,
        )
        self.client: Optional[genai.Client] = None

    def _init_client(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(
            api_key=api_key,
            vertexai=False,
            http_options=types.HttpOptions(timeout=self.timeout),
        )

    def _extract_status_code(self, exc: Exception) -> Optional[int]:
        if isinstance(exc, APIError):
            return exc.code
        return None

    def _send_request(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        response_mime_type: Optional[str] = None,
        response_format: Optional[str] = None,
        addl_config_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        assert self.client is not None

        config_args: Dict[str, Any] = {
            "system_instruction": system_prompt,
        }
        if temperature is not None:
            config_args["temperature"] = temperature
        if response_mime_type is not None:
            config_args["response_mime_type"] = response_mime_type
        if response_format is not None:
            config_args["response_schema"] = response_format
        if addl_config_args:
            config_args.update(addl_config_args)

        chat = self.client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(**config_args),
        )
        response = chat.send_message(user_prompt)
        return {
            "text": response.text,
            "model_version": response.model_version,
        }