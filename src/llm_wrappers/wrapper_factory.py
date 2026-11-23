# wrapper_factory.py
from . import gemini_wrapper      # noqa: F401 - triggers registration
from . import openrouter_wrapper  # noqa: F401 - triggers registration
from .base_wrapper import BaseLLMWrapper

def build_wrapper(provider: str, **kwargs) -> BaseLLMWrapper:
    return BaseLLMWrapper.create(provider, **kwargs)
