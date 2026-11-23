from abc import ABC, abstractmethod
import time
from typing import Any, Dict, Optional, Type


class BaseLLMWrapper(ABC):
    _registry: Dict[str, Type["BaseLLMWrapper"]] = {}

    def __init_subclass__(cls, provider_name: Optional[str] = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if provider_name:
            cls._registry[provider_name.lower()] = cls

    @classmethod
    def create(cls, provider_name: str, **kwargs: Any) -> "BaseLLMWrapper":
        subclass = cls._registry.get(provider_name.lower())
        if not subclass:
            raise ValueError(
                f"Unknown provider '{provider_name}'. Available: {list(cls._registry.keys())}"
            )
        return subclass(**kwargs)

    def __init__(
        self,
        model: str,
        timeout: Any = 60.0,
        rate_limit_sleep: float = 15.0,
        max_attempts: int = 11,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self.rate_limit_sleep = rate_limit_sleep
        self.max_attempts = max_attempts
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self._init_client()
            self._initialized = True

    @abstractmethod
    def _init_client(self) -> None:
        """Initialize the underlying SDK client."""

    @abstractmethod
    def _extract_status_code(self, exc: Exception) -> Optional[int]:
        """Extract an HTTP status code from a provider exception if present."""

    @abstractmethod
    def _send_request(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        response_mime_type: Optional[str] = None,
        response_format: Optional[str] = None,
        addl_config_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a single provider call and return {'text': ..., 'model_version': ...}."""

    def prompt(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        response_mime_type: Optional[str] = None,
        response_format: Optional[str] = None,
        addl_config_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any] | str:
        self._ensure_initialized()

        for attempt in range(self.max_attempts):
            try:
                result = self._send_request(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    response_mime_type=response_mime_type,
                    response_format=response_format,
                    addl_config_args=addl_config_args,
                )
                if self.rate_limit_sleep > 0:
                    time.sleep(self.rate_limit_sleep)

                return {
                    "text": result.get("text") or "",
                    "model_version": result.get("model_version") or self.model,
                }
            except Exception as exc:
                status_code = self._extract_status_code(exc)
                should_retry_503 = status_code == 503 and attempt < 10
                should_retry_429 = status_code == 429 and attempt < 2

                if should_retry_503 or should_retry_429:
                    wait = 60 if status_code == 429 else 2
                    print(f"Error {status_code}, waiting {wait}s then retrying...")
                    time.sleep(wait)
                    continue

                print(f"API Error: {exc}")
                print("All attempts failed. Please check your API key and network connection.")
                raise

        return ""