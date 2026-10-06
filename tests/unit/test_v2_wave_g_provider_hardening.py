from __future__ import annotations

import pytest

from aavc.platform.credentials import InMemoryCredentialStore
from aavc.providers import (
    ApiKeyPool,
    ProviderCancelledError,
    ProviderError,
    ProviderExhaustedError,
    ProviderManager,
    ProviderRequest,
    ProviderResponse,
)


class SequenceProvider:
    name = "sequence"

    def __init__(self, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0
        self.seen: list[str] = []

    def generate(self, request: ProviderRequest, *, api_key: str) -> ProviderResponse:
        self.calls += 1
        self.seen.append(api_key)
        if self.calls <= self.failures_before_success:
            raise ProviderError(
                "quota synthetic-secret-must-not-leak",
                retryable=True,
                quota_exhausted=True,
                retry_after_seconds=30,
            )
        return ProviderResponse(
            text=request.prompt,
            provider=self.name,
            model=request.model,
        )


def _pool_and_store(count: int) -> tuple[ApiKeyPool, InMemoryCredentialStore]:
    pool = ApiKeyPool(max_keys=100)
    store = InMemoryCredentialStore()
    for index in range(1, count + 1):
        key_id = f"slot-{index:03d}"
        ref = f"gemini-slot-{index:03d}"
        pool.register(key_id=key_id, credential_ref=ref)
        store.set_secret(ref, f"secret-{index:03d}")
    return pool, store


def test_key_pool_health_is_secret_free_and_classified() -> None:
    pool, _store = _pool_and_store(3)
    pool.mark_failure(
        "slot-001",
        now=100.0,
        cooldown_seconds=30.0,
        failure_kind="quota",
    )
    pool.mark_failure(
        "slot-002",
        now=100.0,
        cooldown_seconds=0.0,
        disable=True,
        failure_kind="invalid",
    )

    health = pool.health_snapshot(now=110.0)
    summary = pool.health_summary(now=110.0)

    assert [item.state for item in health] == ["COOLDOWN", "DISABLED", "AVAILABLE"]
    assert health[0].cooldown_remaining_seconds == pytest.approx(20.0)
    assert health[0].last_failure_kind == "quota"
    assert summary.total == 3
    assert summary.available == 1
    assert summary.cooldown == 1
    assert summary.disabled == 1
    assert "secret-" not in repr(health)
    assert "secret-" not in repr(summary)


def test_provider_diagnostics_record_failover_without_secret_values() -> None:
    pool, store = _pool_and_store(3)
    provider = SequenceProvider(failures_before_success=2)
    manager = ProviderManager(
        provider=provider,
        key_pool=pool,
        credentials=store,
        max_attempts=3,
        clock=lambda: 100.0,
    )
    progress: list[float] = []

    response, diagnostics = manager.generate_with_diagnostics(
        ProviderRequest(prompt="ok", model="m"),
        progress_callback=progress.append,
    )

    assert response.text == "ok"
    assert diagnostics.attempt_count == 3
    assert [item.outcome for item in diagnostics.attempts] == [
        "QUOTA",
        "QUOTA",
        "SUCCESS",
    ]
    assert diagnostics.successful_key_id == "slot-003"
    assert diagnostics.pool_health.cooldown == 2
    assert diagnostics.pool_health.available == 1
    assert progress[0] == 0.0
    assert progress[-1] == 1.0
    text = repr(diagnostics)
    assert "secret-001" not in text
    assert "secret-002" not in text
    assert "secret-003" not in text


def test_provider_failover_can_use_all_100_registered_keys_once() -> None:
    pool, store = _pool_and_store(100)
    provider = SequenceProvider(failures_before_success=99)
    manager = ProviderManager(
        provider=provider,
        key_pool=pool,
        credentials=store,
        max_attempts=100,
        clock=lambda: 1.0,
    )

    response, diagnostics = manager.generate_with_diagnostics(
        ProviderRequest(prompt="done", model="m")
    )

    assert response.text == "done"
    assert diagnostics.attempt_count == 100
    assert diagnostics.successful_key_id == "slot-100"
    assert len(set(provider.seen)) == 100


def test_provider_cancellation_stops_before_next_key_attempt() -> None:
    pool, store = _pool_and_store(4)
    provider = SequenceProvider(failures_before_success=4)
    manager = ProviderManager(
        provider=provider,
        key_pool=pool,
        credentials=store,
        max_attempts=4,
        clock=lambda: 1.0,
    )

    with pytest.raises(ProviderCancelledError, match="dibatalkan"):
        manager.generate_with_diagnostics(
            ProviderRequest(prompt="cancel", model="m"),
            cancel_requested=lambda: provider.calls >= 1,
        )

    assert provider.calls == 1


def test_exhausted_error_contains_health_but_never_secret() -> None:
    pool, store = _pool_and_store(2)
    provider = SequenceProvider(failures_before_success=5)
    manager = ProviderManager(
        provider=provider,
        key_pool=pool,
        credentials=store,
        max_attempts=2,
        clock=lambda: 1.0,
    )

    with pytest.raises(ProviderExhaustedError) as caught:
        manager.generate(ProviderRequest(prompt="x", model="m"))

    message = str(caught.value)
    assert "2 attempt" in message
    assert "cooldown" in message
    assert "synthetic-secret-must-not-leak" not in message
    assert "secret-001" not in message
