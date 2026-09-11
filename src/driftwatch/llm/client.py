"""Generic Anthropic client that returns validated Pydantic models via tool use."""

from __future__ import annotations

import os
import time
from typing import Any, TypeVar, cast

from anthropic import (
    Anthropic,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OverloadedError,
    RateLimitError,
    ServiceUnavailableError,
)
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# Transient API failures worth retrying. Auth/bad-request errors are excluded
# so we fail fast on permanent client mistakes.
_TRANSIENT_ERRORS: tuple[type[BaseException], ...] = (
    RateLimitError,  # 429 — back off and retry
    APITimeoutError,  # request timed out
    APIConnectionError,  # network blip / DNS / connection reset
    InternalServerError,  # 5xx from Anthropic
    OverloadedError,  # provider overloaded
    ServiceUnavailableError,  # temporary unavailability
)

_TOOL_NAME = "emit_structured_response"


class LLMResponseValidationError(ValueError):
    """Raised when the model response cannot be validated as the target schema."""


class LLMRetriesExhaustedError(RuntimeError):
    """Raised when transient API failures persist beyond ``max_retries`` attempts."""


class LLMClient:
    """Thin Anthropic wrapper: prompt in, validated Pydantic model out."""

    def __init__(
        self, model: str = "claude-sonnet-4-5", max_retries: int = 3
    ) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it before constructing LLMClient."
            )
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._max_retries = max_retries

    def get_structured_response(
        self,
        prompt: str,
        response_model: type[T],
        system: str | None = None,
    ) -> T:
        """Call Anthropic with a forced tool and validate the tool input as ``T``."""
        last_transient: BaseException | None = None

        for attempt in range(self._max_retries):
            try:
                return self._request_and_validate(prompt, response_model, system)
            except _TRANSIENT_ERRORS as exc:
                last_transient = exc
                if attempt >= self._max_retries - 1:
                    break
                time.sleep(2**attempt)

        raise LLMRetriesExhaustedError(
            f"Anthropic API call failed after {self._max_retries} attempt(s) "
            f"due to transient errors; last error: {last_transient}"
        ) from last_transient

    def _request_and_validate(
        self,
        prompt: str,
        response_model: type[T],
        system: str | None,
    ) -> T:
        tool: dict[str, Any] = {
            "name": _TOOL_NAME,
            "description": (
                f"Emit a structured payload matching the "
                f"{response_model.__name__} schema."
            ),
            "input_schema": response_model.model_json_schema(),
        }
        # Anthropic SDK overloads are strict; cast dynamic tool payloads.
        tools = cast(Any, [tool])
        tool_choice = cast(Any, {"type": "tool", "name": _TOOL_NAME})
        messages = cast(Any, [{"role": "user", "content": prompt}])

        if system is None:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
            )
        else:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=messages,
                system=system,
                tools=tools,
                tool_choice=tool_choice,
            )

        tool_input = self._extract_tool_input(response)

        try:
            return response_model.model_validate(tool_input)
        except ValidationError as exc:
            raise LLMResponseValidationError(
                f"Model response did not match {response_model.__name__} schema: {exc}"
            ) from exc

    def _extract_tool_input(self, response: object) -> object:
        content = getattr(response, "content", None)
        if not content:
            raise LLMResponseValidationError(
                "Anthropic response contained no content blocks."
            )
        for block in content:
            if getattr(block, "type", None) == "tool_use":
                return block.input
        raise LLMResponseValidationError(
            "Anthropic response contained no tool_use block despite forced tool_choice."
        )
