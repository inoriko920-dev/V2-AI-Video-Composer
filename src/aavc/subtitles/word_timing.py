from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WordTiming:
    word: str
    start_seconds: float
    end_seconds: float


def distribute_words(text: str, start_seconds: float, end_seconds: float) -> tuple[WordTiming, ...]:
    """Deterministic fallback used only when the user explicitly requests auto distribution.

    It does not claim speech alignment; it evenly distributes words across the cue duration.
    """
    words = [word for word in text.replace("\\N", " ").split() if word]
    if not words:
        return ()
    duration = max(0.001, end_seconds - start_seconds)
    step = duration / len(words)
    result = []
    for index, word in enumerate(words):
        start = start_seconds + index * step
        end = start_seconds + (index + 1) * step
        result.append(WordTiming(word, start, end))
    return tuple(result)
