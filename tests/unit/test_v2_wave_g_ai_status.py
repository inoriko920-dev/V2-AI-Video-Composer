from __future__ import annotations

from aavc.application.services.ai_animation_service import ai_run_status_text
from aavc.providers.key_pool import KeyPoolHealthSummary
from aavc.providers.manager import ProviderAttempt, ProviderRunDiagnostics


def test_ai_run_status_text_is_human_readable_and_secret_free() -> None:
    diagnostics = ProviderRunDiagnostics(
        provider="gemini",
        attempts=(
            ProviderAttempt("slot-001", "QUOTA", 30.0),
            ProviderAttempt("slot-002", "SUCCESS"),
        ),
        successful_key_id="slot-002",
        pool_health=KeyPoolHealthSummary(
            total=3,
            available=2,
            cooldown=1,
            disabled=0,
        ),
    )

    text = ai_run_status_text(diagnostics)

    assert text == "2 attempt; 2 available / 1 cooldown / 0 disabled"
    assert "secret" not in text.lower()
