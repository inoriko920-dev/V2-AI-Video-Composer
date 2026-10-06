from __future__ import annotations

import os

import pytest

from aavc.platform.credentials import (
    EnvironmentCredentialStore,
    InMemoryCredentialStore,
    _decode_windows_credential_blob,
)


def test_in_memory_credential_store_round_trip() -> None:
    store = InMemoryCredentialStore()
    store.set_secret("gemini/001", "secret-value")
    assert store.get_secret("gemini/001") == "secret-value"
    store.delete_secret("gemini/001")
    assert store.get_secret("gemini/001") is None


def test_environment_credential_store_is_read_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AAVC_SECRET_GEMINI_001", "from-env")
    store = EnvironmentCredentialStore()
    assert store.get_secret("gemini/001") == "from-env"
    with pytest.raises(RuntimeError):
        store.set_secret("gemini/001", "x")
    with pytest.raises(RuntimeError):
        store.delete_secret("gemini/001")
    os.environ.pop("AAVC_SECRET_GEMINI_001", None)



def test_windows_credential_blob_decode_accepts_valid_utf16() -> None:
    assert _decode_windows_credential_blob("secret".encode("utf-16-le")) == "secret"


def test_windows_credential_blob_decode_normalizes_corrupt_data() -> None:
    with pytest.raises(OSError, match="Credential Windows rusak"):
        _decode_windows_credential_blob(b"\xff")
