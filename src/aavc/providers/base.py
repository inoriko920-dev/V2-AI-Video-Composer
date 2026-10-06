from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    prompt: str
    model: str
    system_instruction: str | None = None
    temperature: float = 0.2
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    text: str
    provider: str
    model: str
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
        quota_exhausted: bool = False,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.quota_exhausted = quota_exhausted
        self.retry_after_seconds = retry_after_seconds


class ProviderExhaustedError(RuntimeError):
    """Raised when no configured provider credential can serve the request."""


class ProviderCancelledError(RuntimeError):
    """Raised when cooperative provider failover cancellation is requested."""


class AIProvider(Protocol):
    name: str

    def generate(self, request: ProviderRequest, *, api_key: str) -> ProviderResponse:
        """Generate one response. Implementations must never persist or log api_key."""
