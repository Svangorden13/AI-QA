from abc import abstractmethod
import time
from typing import Any, Dict, Optional

from .base_target import BaseTarget


class BasePolledPromptWrapper(BaseTarget):
    """Base class for targets that submit a prompt/turn and poll until completion."""

    def __init__(
        self,
        timeout: float = 60.0,
        poll_interval: float = 0.5,
        max_poll_attempts: Optional[int] = None,
    ) -> None:
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self._init_client()
            self._initialized = True

    @abstractmethod
    def _init_client(self) -> None:
        """Initialize the underlying HTTP/SDK client or session state."""

    @abstractmethod
    def _send_prompt(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        response_mime_type: Optional[str] = None,
        response_format: Optional[str] = None,
        addl_config_args: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Submit the prompt/turn and return a handle, job/thread ID, or cursor for polling."""

    @abstractmethod
    def _poll_response(
        self,
        job_handle: Any,
        deadline: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Poll once for progress/results using `job_handle`.

        Return a dict containing at least {'text': ..., 'model_version': ...} once
        complete, or None if still in progress and polling should continue.
        """

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

        job_handle = self._send_prompt(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            response_mime_type=response_mime_type,
            response_format=response_format,
            addl_config_args=addl_config_args,
        )

        deadline = time.monotonic() + self.timeout
        attempts = 0

        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"{type(self).__name__} timed out after {self.timeout}s while polling."
                )

            result = self._poll_response(job_handle=job_handle, deadline=deadline)
            if result is not None:
                return {
                    "text": result.get("text") or "",
                    "model_version": result.get("model_version") or type(self).__name__,
                }

            attempts += 1
            if self.max_poll_attempts is not None and attempts >= self.max_poll_attempts:
                raise TimeoutError(
                    f"{type(self).__name__} reached max_poll_attempts ({self.max_poll_attempts})."
                )

            if self.poll_interval > 0:
                time.sleep(self.poll_interval)