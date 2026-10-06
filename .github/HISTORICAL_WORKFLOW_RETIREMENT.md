# Historical release workflow retirement

The legacy 0.1.0 RC and final-release workflows are retained only for reproducibility.

- Both are manual-only (`workflow_dispatch`).
- RC verification is pinned to `release/step14-rc1`.
- Final 0.1.0 verification is pinned to `release/0.1.0`.
- Neither historical workflow can publish a GitHub Release.
- Neither historical workflow has `contents: write` permission.
- Generated artifacts are explicitly labeled as historical verification artifacts.

Canonical public releases remain `v0.1.0` and `v0.1.1`; do not move or overwrite their tags.
