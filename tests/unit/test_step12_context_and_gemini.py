from __future__ import annotations

from collections.abc import Mapping

from aavc.providers import ContextBuilder, ProviderError, ProviderRequest
from aavc.providers.adapters import GeminiProvider, JsonHttpResponse


class FakeTransport:
    def __init__(self, response: JsonHttpResponse) -> None:
        self.response = response
        self.last_url = ""
        self.last_body: Mapping[str, object] = {}
        self.last_headers: Mapping[str, str] = {}

    def post_json(
        self,
        url: str,
        *,
        body: Mapping[str, object],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> JsonHttpResponse:
        del timeout_seconds
        self.last_url = url
        self.last_body = body
        self.last_headers = headers
        return self.response


def test_context_builder_redacts_common_secret_shapes_and_truncates() -> None:
    builder = ContextBuilder(max_command_chars=80, max_project_chars=60, max_scene_chars=60)
    context = builder.build(
        command="api_key=AIza1234567890ABCDEFGHIJKLMNO lakukan perubahan ini " * 2,
        project_summary="Bearer abcdefghijklmnopqrstuvwxyz0123456789",
        scene_summary="aman",
    )

    prompt = context.as_prompt()
    assert "AIza1234567890ABCDEFGHIJKLMNO" not in prompt
    assert "Bearer abcdefghijklmnopqrstuvwxyz0123456789" not in prompt
    assert "[REDACTED]" in prompt
    assert "[TRUNCATED]" in prompt


def test_gemini_adapter_parses_text_and_usage_without_live_network() -> None:
    transport = FakeTransport(
        JsonHttpResponse(
            status=200,
            payload={
                "candidates": [
                    {
                        "content": {"parts": [{"text": "hasil "}, {"text": "AI"}]},
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 7},
            },
            headers={},
        )
    )
    provider = GeminiProvider(transport=transport)

    response = provider.generate(
        ProviderRequest(
            prompt="buat rencana",
            system_instruction="jawab JSON",
            model="gemini-2.5-flash",
            temperature=0.1,
        ),
        api_key="synthetic-key",
    )

    assert response.text == "hasil AI"
    assert response.finish_reason == "STOP"
    assert response.input_tokens == 12
    assert response.output_tokens == 7
    assert "synthetic-key" not in transport.last_url
    assert "?" not in transport.last_url
    assert transport.last_headers["x-goog-api-key"] == "synthetic-key"
    assert transport.last_headers["Content-Type"] == "application/json"
    assert "systemInstruction" in transport.last_body


def test_gemini_429_maps_to_retryable_quota_error() -> None:
    provider = GeminiProvider(
        transport=FakeTransport(
            JsonHttpResponse(
                status=429,
                payload={"error": {"message": "quota"}},
                headers={"Retry-After": "17"},
            )
        )
    )

    try:
        provider.generate(ProviderRequest(prompt="x", model="m"), api_key="synthetic-key")
    except ProviderError as exc:
        assert exc.retryable is True
        assert exc.quota_exhausted is True
        assert exc.retry_after_seconds == 17.0
    else:
        raise AssertionError("ProviderError was expected")
