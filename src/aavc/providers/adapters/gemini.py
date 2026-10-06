from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib import error, parse, request

from aavc.providers.base import ProviderError, ProviderRequest, ProviderResponse


@dataclass(frozen=True, slots=True)
class JsonHttpResponse:
    status: int
    payload: Mapping[str, Any]
    headers: Mapping[str, str]


class JsonHttpTransport(Protocol):
    def post_json(
        self,
        url: str,
        *,
        body: Mapping[str, object],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> JsonHttpResponse: ...


class UrllibJsonTransport:
    def post_json(
        self,
        url: str,
        *,
        body: Mapping[str, object],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> JsonHttpResponse:
        encoded = json.dumps(body).encode("utf-8")
        req = request.Request(url, data=encoded, headers=dict(headers), method="POST")
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                payload = cast(dict[str, Any], json.loads(raw)) if raw else {}
                return JsonHttpResponse(
                    status=int(response.status),
                    payload=payload,
                    headers=dict(response.headers.items()),
                )
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = cast(dict[str, Any], json.loads(raw)) if raw else {}
            except json.JSONDecodeError:
                payload = {"error": {"message": "provider HTTP error"}}
            return JsonHttpResponse(
                status=int(exc.code),
                payload=payload,
                headers=dict(exc.headers.items()) if exc.headers is not None else {},
            )
        except error.URLError as exc:
            raise ProviderError("Gemini transport unavailable", retryable=True) from exc


class GeminiProvider:
    name = "gemini"

    def __init__(
        self,
        *,
        transport: JsonHttpTransport | None = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 45.0,
    ) -> None:
        self._transport = transport or UrllibJsonTransport()
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def generate(self, request_data: ProviderRequest, *, api_key: str) -> ProviderResponse:
        if not api_key:
            raise ProviderError("Gemini credential is empty", retryable=False)
        model = parse.quote(request_data.model, safe="-._")
        url = f"{self._base_url}/models/{model}:generateContent"
        body: dict[str, object] = {
            "contents": [{"role": "user", "parts": [{"text": request_data.prompt}]}],
            "generationConfig": {"temperature": request_data.temperature},
        }
        if request_data.system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": request_data.system_instruction}]
            }
        response = self._transport.post_json(
            url,
            body=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            timeout_seconds=self._timeout_seconds,
        )
        if response.status >= 400:
            message = _error_message(response.payload)
            retry_after = _retry_after(response.headers)
            quota = response.status == 429
            raise ProviderError(
                message,
                retryable=quota or response.status >= 500,
                quota_exhausted=quota,
                retry_after_seconds=retry_after,
            )

        text, finish_reason = _extract_candidate(response.payload)
        usage = response.payload.get("usageMetadata")
        usage_map = usage if isinstance(usage, Mapping) else {}
        return ProviderResponse(
            text=text,
            provider=self.name,
            model=request_data.model,
            finish_reason=finish_reason,
            input_tokens=_int_or_none(usage_map.get("promptTokenCount")),
            output_tokens=_int_or_none(usage_map.get("candidatesTokenCount")),
        )


def _extract_candidate(payload: Mapping[str, Any]) -> tuple[str, str | None]:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ProviderError("Gemini response has no candidate", retryable=False)
    first = candidates[0]
    if not isinstance(first, Mapping):
        raise ProviderError("Gemini candidate is malformed", retryable=False)
    content = first.get("content")
    if not isinstance(content, Mapping):
        raise ProviderError("Gemini candidate content is missing", retryable=False)
    parts = content.get("parts")
    if not isinstance(parts, list):
        raise ProviderError("Gemini candidate parts are missing", retryable=False)
    text_parts: list[str] = []
    for part in parts:
        if isinstance(part, Mapping):
            value = part.get("text")
            if isinstance(value, str):
                text_parts.append(value)
    if not text_parts:
        raise ProviderError("Gemini response contains no text", retryable=False)
    finish = first.get("finishReason")
    return "".join(text_parts), finish if isinstance(finish, str) else None


def _error_message(payload: Mapping[str, Any]) -> str:
    error_value = payload.get("error")
    if isinstance(error_value, Mapping):
        message = error_value.get("message")
        if isinstance(message, str) and message:
            return message
    return "Gemini request failed"


def _retry_after(headers: Mapping[str, str]) -> float | None:
    value = headers.get("Retry-After") or headers.get("retry-after")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None
