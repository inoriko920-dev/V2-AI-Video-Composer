# Backup & Recovery — AAVC

## Canonical source
Git history is the canonical source. A final release must also preserve a source snapshot generated from the exact release commit.

## Release backup set
Keep these together for every final release:
- portable Windows ZIP;
- SHA256SUMS.txt;
- release notes;
- source-backup ZIP from the same commit;
- dependency/license records under `LICENSES/`;
- status files STEP09–STEP15 and architecture documentation.

## User-project recovery
Project documents use versioned `.aavcproj` JSON. Autosave/recovery files are runtime data and must never be packaged into a release artifact.

## Disaster recovery sequence
1. verify the source-backup checksum;
2. restore the repository at the recorded release commit;
3. install the pinned Python/dev dependencies;
4. run compile, Ruff, strict mypy and cheap pytest;
5. rebuild the Windows onedir package;
6. run portable verification and compare generated checksums;
7. restore user projects separately from their own backups.

## Secrets
API keys are not part of source or release backups. Windows Credential Manager entries must be recreated by the user after a machine/account migration.
