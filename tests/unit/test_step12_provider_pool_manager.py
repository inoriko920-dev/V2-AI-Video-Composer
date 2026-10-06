from __future__ import annotations

from aavc.platform.credentials import InMemoryCredentialStore
from aavc.providers import (
    ApiKeyPool,
    ProviderError,
    ProviderManager,
    ProviderRequest,
    ProviderResponse,
)


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.seen: list[str] = []

    def generate(self, request: ProviderRequest, *, api_key: str) -> ProviderResponse:
        self.seen.append(api_key)
        if api_key == "bad-secret":
            raise ProviderError(
                "quota exhausted",
                retryable=True,
                quota_exhausted=True,
                retry_after_seconds=30,
            )
        return ProviderResponse(text=request.prompt.upper(), provider=self.name, model=request.model)


def test_key_pool_rotates_without_storing_raw_secret() -> None:
    pool = ApiKeyPool(max_keys=100)
    pool.register(key_id="key-001", credential_ref="gemini/001")
    pool.register(key_id="key-002", credential_ref="gemini/002")
    credentials = InMemoryCredentialStore()
    credentials.set_secret("gemini/001", "bad-secret")
    credentials.set_secret("gemini/002", "good-secret")
    provider = FakeProvider()
    manager = ProviderManager(
        provider=provider,
        key_pool=pool,
        credentials=credentials,
        max_attempts=4,
        clock=lambda: 100.0,
    )

    response = manager.generate(ProviderRequest(prompt="halo", model="fake-model"))

    assert response.text == "HALO"
    assert provider.seen == ["bad-secret", "good-secret"]
    snapshot_text = repr(pool.snapshot())
    assert "bad-secret" not in snapshot_text
    assert "good-secret" not in snapshot_text
    assert pool.snapshot()[0].cooldown_until == 130.0
    assert pool.snapshot()[1].consecutive_failures == 0


def test_missing_credential_is_disabled_and_next_key_is_used() -> None:
    pool = ApiKeyPool()
    pool.register(key_id="missing", credential_ref="gemini/missing")
    pool.register(key_id="ready", credential_ref="gemini/ready")
    credentials = InMemoryCredentialStore()
    credentials.set_secret("gemini/ready", "good-secret")
    manager = ProviderManager(
        provider=FakeProvider(),
        key_pool=pool,
        credentials=credentials,
        clock=lambda: 1.0,
    )

    response = manager.generate(ProviderRequest(prompt="ok", model="m"))

    assert response.text == "OK"
    assert pool.snapshot()[0].disabled is True


class PartiallyBrokenCredentialStore(InMemoryCredentialStore):
    def __init__(self, broken_reference: str) -> None:
        super().__init__()
        self._broken_reference = broken_reference

    def get_secret(self, reference: str) -> str | None:
        if reference == self._broken_reference:
            raise OSError("corrupt credential blob")
        return super().get_secret(reference)


def test_credential_read_failure_disables_bad_key_and_fails_over() -> None:
    pool = ApiKeyPool()
    pool.register(key_id="broken", credential_ref="gemini/broken")
    pool.register(key_id="ready", credential_ref="gemini/ready")
    credentials = PartiallyBrokenCredentialStore("gemini/broken")
    credentials.set_secret("gemini/ready", "good-secret")
    provider = FakeProvider()
    manager = ProviderManager(
        provider=provider,
        key_pool=pool,
        credentials=credentials,
        clock=lambda: 1.0,
    )

    response = manager.generate(ProviderRequest(prompt="ok", model="m"))

    assert response.text == "OK"
    assert provider.seen == ["good-secret"]
    assert pool.snapshot()[0].disabled is True
