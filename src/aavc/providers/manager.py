from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from aavc.platform.credentials import CredentialStore
from aavc.providers.base import (
    AIProvider,
    ProviderCancelledError,
    ProviderError,
    ProviderExhaustedError,
    ProviderRequest,
    ProviderResponse,
)
from aavc.providers.context_builder import redact_sensitive_text
from aavc.providers.key_pool import ApiKeyPool, KeyPoolHealthSummary


@dataclass(frozen=True, slots=True)
class ProviderAttempt:
    key_id: str
    outcome: str
    cooldown_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class ProviderRunDiagnostics:
    provider: str
    attempts: tuple[ProviderAttempt, ...]
    successful_key_id: str | None
    pool_health: KeyPoolHealthSummary

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)


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
        response, _diagnostics = self.generate_with_diagnostics(request)
        return response

    def generate_with_diagnostics(
        self,
        request: ProviderRequest,
        *,
        cancel_requested: Callable[[], bool] | None = None,
        progress_callback: Callable[[float], None] | None = None,
    ) -> tuple[ProviderResponse, ProviderRunDiagnostics]:
        attempted: set[str] = set()
        attempts: list[ProviderAttempt] = []
        last_error: ProviderError | None = None
        last_credential_error: OSError | None = None
        attempt_limit = min(self._max_attempts, len(self._key_pool))

        for attempt_index in range(attempt_limit):
            self._raise_if_cancelled(cancel_requested)
            now = self._clock()
            entry = self._key_pool.acquire(now=now, excluded=attempted)
            if entry is None:
                break
            attempted.add(entry.key_id)
            if progress_callback is not None:
                progress_callback(attempt_index / max(1, attempt_limit))

            try:
                secret = self._credentials.get_secret(entry.credential_ref)
            except OSError as exc:
                last_credential_error = exc
                self._key_pool.mark_failure(
                    entry.key_id,
                    now=now,
                    cooldown_seconds=0.0,
                    disable=True,
                    failure_kind="credential-error",
                )
                attempts.append(ProviderAttempt(entry.key_id, "CREDENTIAL_ERROR"))
                self._report_progress(progress_callback, attempt_index + 1, attempt_limit)
                continue
            if not secret:
                self._key_pool.mark_failure(
                    entry.key_id,
                    now=now,
                    cooldown_seconds=0.0,
                    disable=True,
                    failure_kind="missing-credential",
                )
                attempts.append(ProviderAttempt(entry.key_id, "MISSING_CREDENTIAL"))
                self._report_progress(progress_callback, attempt_index + 1, attempt_limit)
                continue

            try:
                response = self._provider.generate(request, api_key=secret)
            except ProviderError as exc:
                last_error = exc
                cooldown = self._cooldown_for(exc, entry.consecutive_failures)
                if exc.quota_exhausted:
                    failure_kind = "quota"
                    outcome = "QUOTA"
                elif exc.retryable:
                    failure_kind = "retryable"
                    outcome = "RETRYABLE_ERROR"
                else:
                    failure_kind = "invalid"
                    outcome = "NONRETRYABLE_ERROR"
                self._key_pool.mark_failure(
                    entry.key_id,
                    now=now,
                    cooldown_seconds=cooldown,
                    disable=not exc.retryable,
                    failure_kind=failure_kind,
                )
                attempts.append(ProviderAttempt(entry.key_id, outcome, cooldown))
                self._report_progress(progress_callback, attempt_index + 1, attempt_limit)
                continue

            self._raise_if_cancelled(cancel_requested)
            self._key_pool.mark_success(entry.key_id)
            attempts.append(ProviderAttempt(entry.key_id, "SUCCESS"))
            if progress_callback is not None:
                progress_callback(1.0)
            diagnostics = ProviderRunDiagnostics(
                provider=self._provider.name,
                attempts=tuple(attempts),
                successful_key_id=entry.key_id,
                pool_health=self._key_pool.health_summary(now=self._clock()),
            )
            return response, diagnostics

        self._raise_if_cancelled(cancel_requested)
        diagnostics = ProviderRunDiagnostics(
            provider=self._provider.name,
            attempts=tuple(attempts),
            successful_key_id=None,
            pool_health=self._key_pool.health_summary(now=self._clock()),
        )
        health = diagnostics.pool_health
        health_text = (
            f"pool {health.available} available / {health.cooldown} cooldown / "
            f"{health.disabled} disabled"
        )
        if last_error is not None:
            safe_message = redact_sensitive_text(str(last_error))
            raise ProviderExhaustedError(
                f"{self._provider.name} provider exhausted after "
                f"{len(attempted)} attempt(s); {health_text}: {safe_message}"
            ) from last_error
        if last_credential_error is not None:
            safe_message = redact_sensitive_text(str(last_credential_error))
            raise ProviderExhaustedError(
                f"{self._provider.name} credential store failed after "
                f"{len(attempted)} attempt(s); {health_text}: {safe_message}"
            ) from last_credential_error
        raise ProviderExhaustedError(
            f"{self._provider.name} provider has no usable configured credentials; "
            f"{health_text}"
        )

    @staticmethod
    def _raise_if_cancelled(
        cancel_requested: Callable[[], bool] | None,
    ) -> None:
        if cancel_requested is not None and cancel_requested():
            raise ProviderCancelledError("Permintaan provider dibatalkan")

    @staticmethod
    def _report_progress(
        callback: Callable[[float], None] | None,
        completed_attempts: int,
        attempt_limit: int,
    ) -> None:
        if callback is not None:
            callback(completed_attempts / max(1, attempt_limit))

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
