import os
from typing import Any, Dict, Optional
from openai import APIError, OpenAI
from .base_one_shot_prompt_wrapper import BaseOSPWrapper

OPEN_ROUTER_FREE = "openrouter/free"
META_LLAMA_3_3_70B_INSTRUCT = "meta-llama/llama-3.3-70b-instruct"


class OpenRouterWrapper(BaseOSPWrapper, provider_name="openrouter"):
    def __init__(
        self,
        model: str = OPEN_ROUTER_FREE,
        timeout: float = 60.0,
        rate_limit_sleep: float = 15.0,
        max_attempts: int = 11,
    ) -> None:
        super().__init__(
            model=model,
            timeout=timeout,
            rate_limit_sleep=rate_limit_sleep,
            max_attempts=max_attempts,
        )
        self.client: Optional[OpenAI] = None

    def _init_client(self) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=self.timeout,
        )

    def _extract_status_code(self, exc: Exception) -> Optional[int]:
        if isinstance(exc, APIError):
            return exc.status_code
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

        print(f"Response format: {response_format}")

        if "json" in str(response_mime_type).lower():
            print("It's a JSON request")
            response_type = "json_schema"
        else:
            response_type = response_mime_type
            print(f"It's a {response_type} request")

        request_args: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        if temperature is not None:
            request_args["temperature"] = temperature
        if (response_type == "json_schema") and (response_format is not None):
            if isinstance(response_format, dict):
                response_format["additionalProperties"] = False
            request_args["response_format"] = {
                "type": response_type,
                "json_schema": {
                    "name": "response_schema",
                    "strict": True,
                    "schema": response_format,
                },
            }
        elif response_type is not None:
            request_args["response_format"] = {"type": response_type}
        if addl_config_args:
            request_args.update(addl_config_args)

        response = self.client.chat.completions.create(**request_args)
        content = response.choices[0].message.content if response.choices else ""
        return {
            "text": content,
            "model_version": self.model,
        }