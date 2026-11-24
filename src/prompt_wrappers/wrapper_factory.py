# wrapper_factory.py
from . import gemini_wrapper      # noqa: F401 - triggers registration
from . import openrouter_wrapper  # noqa: F401 - triggers registration
from .base_target import BaseTarget

def build_wrapper(provider: str, **kwargs) -> BaseTarget:
    return BaseTarget.create(provider, **kwargs)
