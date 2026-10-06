from __future__ import annotations

import time
from collections.abc import Callable

from aavc.platform.credentials import CredentialStore
from aavc.providers.base import (
    AIProvider,
    ProviderError,
    ProviderExhaustedError,
    ProviderRequest,
    ProviderResponse,
)
from aavc.providers.context_builder import redact_sensitive_text
from aavc.providers.key_pool import ApiKeyPool


class ProviderManager:
    """Route one request through a secret-free key pool with bounded failover."""

    def __init__(
        self,
        *,
        provider: AIProvider,
        key_pool: ApiKeyPool,
        credentials: CredentialStore,
        max_attempts: int = 4,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self._provider = provider
        self._key_pool = key_pool
        self._credentials = credentials
        self._max_attempts = max_attempts
        self._clock = clock

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        attempted: set[str] = set()
        last_error: ProviderError | None = None
        last_credential_error: OSError | None = None
        attempt_limit = min(self._max_attempts, len(self._key_pool))
        for _ in range(attempt_limit):
            now = self._clock()
            entry = self._key_pool.acquire(now=now, excluded=attempted)
            if entry is None:
                break
            attempted.add(entry.key_id)
            try:
                secret = self._credentials.get_secret(entry.credential_ref)
            except OSError as exc:
                last_credential_error = exc
                self._key_pool.mark_failure(
                    entry.key_id,
                    now=now,
                    cooldown_seconds=0.0,
                    disable=True,
                )
                continue
            if not secret:
                self._key_pool.mark_failure(
                    entry.key_id,
                    now=now,
                    cooldown_seconds=0.0,
                    disable=True,
                )
                continue
            try:
                response = self._provider.generate(request, api_key=secret)
            except ProviderError as exc:
                last_error = exc
                cooldown = self._cooldown_for(exc, entry.consecutive_failures)
                self._key_pool.mark_failure(
                    entry.key_id,
                    now=now,
                    cooldown_seconds=cooldown,
                    disable=not exc.retryable,
                )
            else:
                self._key_pool.mark_success(entry.key_id)
                return response

        if last_error is not None:
            safe_message = redact_sensitive_text(str(last_error))
            raise ProviderExhaustedError(
                f"{self._provider.name} provider exhausted after {len(attempted)} attempt(s): "
                f"{safe_message}"
            ) from last_error
        if last_credential_error is not None:
            safe_message = redact_sensitive_text(str(last_credential_error))
            raise ProviderExhaustedError(
                f"{self._provider.name} credential store failed after "
                f"{len(attempted)} attempt(s): {safe_message}"
            ) from last_credential_error
        raise ProviderExhaustedError(
            f"{self._provider.name} provider has no usable configured credentials"
        )

    @staticmethod
    def _cooldown_for(error: ProviderError, previous_failures: int) -> float:
        if error.retry_after_seconds is not None:
            return float(min(900.0, error.retry_after_seconds))
        if error.quota_exhausted:
            return float(min(900.0, 60.0 * (previous_failures + 1)))
        if error.retryable:
            backoff = 5.0 * float(2 ** min(previous_failures, 4))
            return float(min(120.0, backoff))
        return 0.0
