from __future__ import annotations

import os
import sys
from typing import Any, Protocol


def _decode_windows_credential_blob(raw_bytes: bytes) -> str:
    try:
        return raw_bytes.decode("utf-16-le")
    except UnicodeDecodeError as error:
        raise OSError("Credential Windows rusak atau tidak dapat dibaca") from error


class CredentialStore(Protocol):
    def get_secret(self, reference: str) -> str | None: ...

    def set_secret(self, reference: str, secret: str) -> None: ...

    def delete_secret(self, reference: str) -> None: ...


class InMemoryCredentialStore:
    """Test/development store. Never serialize this object to project files."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get_secret(self, reference: str) -> str | None:
        return self._values.get(reference)

    def set_secret(self, reference: str, secret: str) -> None:
        if not reference or not secret:
            raise ValueError("reference and secret are required")
        self._values[reference] = secret

    def delete_secret(self, reference: str) -> None:
        self._values.pop(reference, None)


class EnvironmentCredentialStore:
    """Read-only store useful for CI/manual smoke tests without committing secrets."""

    def __init__(self, *, prefix: str = "AAVC_SECRET_") -> None:
        self._prefix = prefix

    def get_secret(self, reference: str) -> str | None:
        key = self._prefix + reference.upper().replace("-", "_").replace("/", "_")
        return os.getenv(key)

    def set_secret(self, reference: str, secret: str) -> None:
        raise RuntimeError("environment credential store is read-only")

    def delete_secret(self, reference: str) -> None:
        raise RuntimeError("environment credential store is read-only")


class WindowsCredentialManagerStore:
    """Generic credentials stored through the Windows Credential Manager API."""

    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2

    def __init__(self, *, target_prefix: str = "AAVC/") -> None:
        if sys.platform != "win32":
            raise RuntimeError("Windows Credential Manager is available only on Windows")
        self._target_prefix = target_prefix

    def _target(self, reference: str) -> str:
        if not reference.strip():
            raise ValueError("credential reference is required")
        return f"{self._target_prefix}{reference}"

    @staticmethod
    def _api() -> tuple[Any, Any, Any, Any, Any]:
        import ctypes
        from ctypes import wintypes

        class Credential(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD),
                ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME),
                ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD),
                ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR),
                ("UserName", wintypes.LPWSTR),
            ]

        credential_pointer = ctypes.POINTER(Credential)
        advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        cred_write = advapi32.CredWriteW
        cred_write.argtypes = [credential_pointer, wintypes.DWORD]
        cred_write.restype = wintypes.BOOL
        cred_read = advapi32.CredReadW
        cred_read.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(credential_pointer),
        ]
        cred_read.restype = wintypes.BOOL
        cred_delete = advapi32.CredDeleteW
        cred_delete.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        cred_delete.restype = wintypes.BOOL
        cred_free = advapi32.CredFree
        cred_free.argtypes = [ctypes.c_void_p]
        cred_free.restype = None
        return ctypes, Credential, cred_write, cred_read, (cred_delete, cred_free)

    def get_secret(self, reference: str) -> str | None:
        ctypes, credential_type, _cred_write, cred_read, delete_and_free = self._api()
        _cred_delete, cred_free = delete_and_free
        pointer = ctypes.POINTER(credential_type)()
        if not cred_read(self._target(reference), self.CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
            error = ctypes.get_last_error()
            if error == 1168:  # ERROR_NOT_FOUND
                return None
            raise OSError(error, "CredReadW failed")
        try:
            credential = pointer.contents
            if credential.CredentialBlobSize == 0:
                return ""
            raw_bytes = bytes(
                ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
            )
            return _decode_windows_credential_blob(raw_bytes)
        finally:
            cred_free(pointer)

    def set_secret(self, reference: str, secret: str) -> None:
        if not secret:
            raise ValueError("secret is required")
        ctypes, credential_type, cred_write, _cred_read, _delete_and_free = self._api()
        encoded = secret.encode("utf-16-le")
        blob = ctypes.create_string_buffer(encoded)
        credential = credential_type()
        credential.Type = self.CRED_TYPE_GENERIC
        credential.TargetName = self._target(reference)
        credential.CredentialBlobSize = len(encoded)
        credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = self.CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = "AI Automatic Video Composer"
        if not cred_write(ctypes.byref(credential), 0):
            error = ctypes.get_last_error()
            raise OSError(error, "CredWriteW failed")

    def delete_secret(self, reference: str) -> None:
        ctypes, _credential_type, _cred_write, _cred_read, delete_and_free = self._api()
        cred_delete, _cred_free = delete_and_free
        if not cred_delete(self._target(reference), self.CRED_TYPE_GENERIC, 0):
            error = ctypes.get_last_error()
            if error != 1168:
                raise OSError(error, "CredDeleteW failed")
