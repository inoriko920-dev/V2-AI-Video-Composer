# STEP 12 Integration Scope

This step integrates external AI providers without coupling the domain/editor to any provider SDK.

## Contract
Presentation/Application -> ProviderManager -> ProviderAdapter -> HTTP transport
ProviderManager -> CredentialStore only when resolving a selected key reference.

## Initial provider
Gemini REST is the first adapter. Model name remains configurable; the provider boundary is intentionally not tied to one model generation.

## API-key pool
- maximum 100 key references per pool
- round-robin selection among eligible keys
- rate/quota failures place a key into cooldown
- authentication failures disable the affected key
- transient provider failures can rotate to another eligible key
- raw key values are never returned by status/snapshot APIs

## Credential policy
Windows production storage uses the native Credential Manager via the platform boundary. Tests use an in-memory store with synthetic secrets.

## Test policy
No live Gemini call is allowed in CI. Adapter tests use an injected fake HTTP transport.
