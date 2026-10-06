from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

KeyHealthState = Literal["AVAILABLE", "COOLDOWN", "DISABLED"]


@dataclass(frozen=True, slots=True)
class KeyEntry:
    key_id: str
    credential_ref: str
    cooldown_until: float = 0.0
    consecutive_failures: int = 0
    disabled: bool = False
    last_failure_kind: str | None = None


@dataclass(frozen=True, slots=True)
class KeyHealth:
    key_id: str
    state: KeyHealthState
    consecutive_failures: int
    cooldown_remaining_seconds: float
    last_failure_kind: str | None = None


@dataclass(frozen=True, slots=True)
class KeyPoolHealthSummary:
    total: int
    available: int
    cooldown: int
    disabled: int


class ApiKeyPool:
    """Secret-free key registry with deterministic rotation and cooldown state."""

    def __init__(self, *, max_keys: int = 100) -> None:
        if max_keys < 1:
            raise ValueError("max_keys must be positive")
        self._max_keys = max_keys
        self._entries: list[KeyEntry] = []
        self._cursor = 0

    def register(self, *, key_id: str, credential_ref: str) -> None:
        if not key_id.strip() or not credential_ref.strip():
            raise ValueError("key_id and credential_ref are required")
        if any(entry.key_id == key_id for entry in self._entries):
            raise ValueError(f"duplicate key_id: {key_id}")
        if len(self._entries) >= self._max_keys:
            raise ValueError(f"key pool limit reached ({self._max_keys})")
        self._entries.append(KeyEntry(key_id=key_id, credential_ref=credential_ref))

    def acquire(self, *, now: float, excluded: set[str] | None = None) -> KeyEntry | None:
        if not self._entries:
            return None
        blocked = excluded or set()
        count = len(self._entries)
        for offset in range(count):
            index = (self._cursor + offset) % count
            entry = self._entries[index]
            if entry.key_id in blocked or entry.disabled or entry.cooldown_until > now:
                continue
            self._cursor = (index + 1) % count
            return entry
        return None

    def mark_success(self, key_id: str) -> None:
        index = self._index_of(key_id)
        self._entries[index] = replace(
            self._entries[index],
            cooldown_until=0.0,
            consecutive_failures=0,
            last_failure_kind=None,
        )

    def mark_failure(
        self,
        key_id: str,
        *,
        now: float,
        cooldown_seconds: float,
        disable: bool = False,
        failure_kind: str = "provider-error",
    ) -> None:
        index = self._index_of(key_id)
        current = self._entries[index]
        self._entries[index] = replace(
            current,
            cooldown_until=max(current.cooldown_until, now + max(0.0, cooldown_seconds)),
            consecutive_failures=current.consecutive_failures + 1,
            disabled=current.disabled or disable,
            last_failure_kind=failure_kind.strip() or "provider-error",
        )

    def health_snapshot(self, *, now: float) -> tuple[KeyHealth, ...]:
        health: list[KeyHealth] = []
        for entry in self._entries:
            if entry.disabled:
                state: KeyHealthState = "DISABLED"
            elif entry.cooldown_until > now:
                state = "COOLDOWN"
            else:
                state = "AVAILABLE"
            health.append(
                KeyHealth(
                    key_id=entry.key_id,
                    state=state,
                    consecutive_failures=entry.consecutive_failures,
                    cooldown_remaining_seconds=max(0.0, entry.cooldown_until - now),
                    last_failure_kind=entry.last_failure_kind,
                )
            )
        return tuple(health)

    def health_summary(self, *, now: float) -> KeyPoolHealthSummary:
        items = self.health_snapshot(now=now)
        return KeyPoolHealthSummary(
            total=len(items),
            available=sum(item.state == "AVAILABLE" for item in items),
            cooldown=sum(item.state == "COOLDOWN" for item in items),
            disabled=sum(item.state == "DISABLED" for item in items),
        )

    def snapshot(self) -> tuple[KeyEntry, ...]:
        """Return secret-free state suitable for diagnostics/UI."""
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def _index_of(self, key_id: str) -> int:
        for index, entry in enumerate(self._entries):
            if entry.key_id == key_id:
                return index
        raise KeyError(key_id)
