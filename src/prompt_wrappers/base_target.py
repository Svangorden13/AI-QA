from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type


class BaseTarget(ABC):
    _registry: Dict[str, Type["BaseTarget"]] = {}

    def __init_subclass__(cls, provider_name: Optional[str] = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if provider_name:
            cls._registry[provider_name.lower()] = cls

    @classmethod
    def create(cls, provider_name: str, **kwargs: Any) -> "BaseTarget":
        subclass = cls._registry.get(provider_name.lower())
        if not subclass:
            raise ValueError(
                f"Unknown provider '{provider_name}'. Available: {list(cls._registry.keys())}"
            )
        return subclass(**kwargs)

    @abstractmethod
    def prompt(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        response_mime_type: Optional[str] = None,
        response_format: Optional[str] = None,
        addl_config_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any] | str:
        """Send a prompt/input to the target and return a response dict or string."""