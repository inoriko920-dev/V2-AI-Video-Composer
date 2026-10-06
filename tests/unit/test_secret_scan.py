from __future__ import annotations

from pathlib import Path

from scripts.check_no_secrets import scan_text


def test_scan_text_detects_google_api_key_without_echoing_value() -> None:
    secret = "AIza" + ("A" * 35)
    findings = scan_text(f"token={secret}\n", Path("example.txt"))
    assert [(item.kind, item.line) for item in findings] == [("google-api-key", 1)]


def test_scan_text_detects_openrouter_key() -> None:
    secret = "sk-" + "or-v1-" + ("B" * 40)
    findings = scan_text(f"first line\nkey={secret}\n", Path("settings.txt"))
    assert [(item.kind, item.line) for item in findings] == [
        ("openai-or-openrouter-key", 2)
    ]


def test_scan_text_detects_aws_and_slack_credentials() -> None:
    aws_key = "AKIA" + ("C" * 16)
    slack_token = "xoxb-" + ("D" * 24)
    findings = scan_text(
        f"aws={aws_key}\nslack={slack_token}\n",
        Path("secrets.txt"),
    )
    assert [(item.kind, item.line) for item in findings] == [
        ("aws-access-key", 1),
        ("slack-token", 2),
    ]


def test_scan_text_ignores_documentation_placeholders() -> None:
    text = "GEMINI_KEY=YOUR_KEY_HERE\nOPENAI_KEY=<replace-me>\n"
    assert scan_text(text, Path("README.md")) == []
