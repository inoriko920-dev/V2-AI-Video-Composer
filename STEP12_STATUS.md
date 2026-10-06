# STEP 12 — Integration & External Services

Status: **PASS**

Implemented:
- provider-neutral `ProviderRequest` / `ProviderResponse` / `AIProvider` contract
- Gemini REST adapter using an injectable JSON HTTP transport
- bounded API-key pool supporting up to 100 credential references
- deterministic key rotation, cooldown, retry and failover behavior
- credential-store boundary with in-memory test store, environment CI store, and Windows Credential Manager implementation
- context minimization plus common API-key/Bearer-token redaction before external calls
- provider errors are redacted before they reach user-facing exhaustion errors
- no real provider key is committed to the repository
- tests use only synthetic credentials and fake transports; CI performs no live Gemini request

Security rules locked:
- raw API keys are not stored in ProjectState or provider-pool snapshots
- raw secrets are resolved only immediately before a provider call
- provider/key diagnostics expose credential references and health state, never raw secrets
- missing credentials are disabled for the active pool instead of guessed or silently replaced
- quota/temporary provider failures rotate to the next eligible key and apply bounded cooldown

Validation evidence:
- Windows GitHub Actions CI run #122: SUCCESS
- compile: PASS
- Ruff: PASS
- strict mypy: PASS
- cheap pytest suite including STEP 12 provider/key/context/credential tests: PASS
- STEP 09 Qt capture and screenshot verification remain green in the same CI run

Gate decision:
- STEP 12 technical gate: PASS
- external-service architecture is ready for STEP 13 hardening/QA
- live-account smoke tests remain optional/manual and must never require committing secrets
