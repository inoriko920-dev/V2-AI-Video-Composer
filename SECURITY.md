# Security Policy

## Supported versions

Security fixes are maintained on the current compatible `0.1.x` line. The currently published maintenance release is `0.1.1`.

| Version | Supported |
| --- | --- |
| `0.1.x` | Yes |
| `< 0.1.0` | No |

## Reporting a vulnerability

Do not publish API keys, tokens, passwords, private user files, or working exploit details in a public issue.

Preferred reporting path:

1. Use GitHub private vulnerability reporting / Security Advisories for this repository when that option is available.
2. If private reporting is not available, open a minimal public issue that says a security problem was found and requests a private contact path. Do not include secrets, exploit payloads, sensitive logs, or user data in that issue.
3. Include the affected AAVC version, operating system, minimal redacted reproduction steps, expected behavior, observed behavior, and whether the issue can expose credentials or user content.

## Credential handling

AAVC credentials must remain outside the repository and release artifacts.

- Never commit Gemini/API keys or other provider credentials.
- Never attach raw credentials to bug reports, diagnostics, screenshots, or reproduction bundles.
- Redact tokens and personally identifying local paths where practical.
- Provider/key-pool changes require tests that guard against raw-secret leakage.

The repository also runs a tracked-file credential-pattern scanner and CodeQL as defense-in-depth checks. These checks reduce risk but do not replace careful review.

## Security release handling

Security fixes on the stable line are patch releases when they preserve project/schema compatibility. Before publication, the normal maintenance gate still applies, including static checks, tests, representative UI verification, portable build verification, secret/runtime-file exclusion, and release checksum generation.

For the full maintenance and release rules, see `MAINTENANCE.md`, `BACKUP_AND_RECOVERY.md`, and `docs/RELEASE_PUBLISHING.md`.
