"""Tests for LLMClient (mocked Anthropic SDK — no real network calls)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from anthropic import APIConnectionError, RateLimitError
from pydantic import BaseModel, ValidationError

from driftwatch.llm.client import (
    LLMClient,
    LLMResponseValidationError,
    LLMRetriesExhaustedError,
)


class SampleReply(BaseModel):
    """Throwaway schema used only by these unit tests."""

    summary: str
    score: int


def _tool_use_response(payload: dict[str, Any]) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.input = payload
    response = MagicMock()
    response.content = [block]
    return response


def _client_with_mock_sdk(
    monkeypatch: pytest.MonkeyPatch, mock_anthropic_cls: MagicMock
) -> tuple[LLMClient, MagicMock]:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    mock_sdk = MagicMock()
    mock_anthropic_cls.return_value = mock_sdk
    return LLMClient(max_retries=3), mock_sdk


def test_missing_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        LLMClient()


@patch("driftwatch.llm.client.Anthropic")
def test_get_structured_response_validates_tool_input(
    mock_anthropic_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, mock_sdk = _client_with_mock_sdk(monkeypatch, mock_anthropic_cls)
    mock_sdk.messages.create.return_value = _tool_use_response(
        {"summary": "ok", "score": 7}
    )

    result = client.get_structured_response("prompt", SampleReply)

    assert result == SampleReply(summary="ok", score=7)
    mock_sdk.messages.create.assert_called_once()
    call_kwargs = mock_sdk.messages.create.call_args.kwargs
    assert call_kwargs["tool_choice"] == {
        "type": "tool",
        "name": "emit_structured_response",
    }


@patch("driftwatch.llm.client.Anthropic")
def test_validation_failure_raises_without_retry(
    mock_anthropic_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, mock_sdk = _client_with_mock_sdk(monkeypatch, mock_anthropic_cls)
    mock_sdk.messages.create.return_value = _tool_use_response(
        {"summary": "ok", "score": "not-an-int"}
    )

    with pytest.raises(LLMResponseValidationError) as exc_info:
        client.get_structured_response("prompt", SampleReply)

    assert mock_sdk.messages.create.call_count == 1
    assert isinstance(exc_info.value.__cause__, ValidationError)


@patch("driftwatch.llm.client.time.sleep")
@patch("driftwatch.llm.client.Anthropic")
def test_retries_transient_error_then_succeeds(
    mock_anthropic_cls: MagicMock,
    mock_sleep: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, mock_sdk = _client_with_mock_sdk(monkeypatch, mock_anthropic_cls)
    mock_sdk.messages.create.side_effect = [
        APIConnectionError(request=MagicMock()),
        _tool_use_response({"summary": "recovered", "score": 1}),
    ]

    result = client.get_structured_response("prompt", SampleReply)

    assert result.summary == "recovered"
    assert mock_sdk.messages.create.call_count == 2
    mock_sleep.assert_called_once_with(1)


@patch("driftwatch.llm.client.time.sleep")
@patch("driftwatch.llm.client.Anthropic")
def test_retries_exhausted_raises_clear_error(
    mock_anthropic_cls: MagicMock,
    mock_sleep: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    mock_sdk = MagicMock()
    mock_anthropic_cls.return_value = mock_sdk
    client = LLMClient(max_retries=3)
    mock_sdk.messages.create.side_effect = RateLimitError(
        message="rate limited",
        response=MagicMock(status_code=429),
        body=None,
    )

    with pytest.raises(LLMRetriesExhaustedError, match="3 attempt"):
        client.get_structured_response("prompt", SampleReply)

    assert mock_sdk.messages.create.call_count == 3
    assert mock_sleep.call_count == 2
