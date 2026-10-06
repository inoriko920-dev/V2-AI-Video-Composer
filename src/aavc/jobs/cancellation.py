from __future__ import annotations

from threading import Event


class CancellationRequested(RuntimeError):
    """Raised when cooperative cancellation has been requested."""


class CancellationToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise CancellationRequested("Pekerjaan dibatalkan")
