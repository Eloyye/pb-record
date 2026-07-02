# Toolchain and quality gates: Astral + Oxc, enforced by lefthook

We standardise on the Rust-based **Astral** (Python) and **Oxc** (JS/TS) toolchains rather than the mainstream defaults, and enforce them as a pre-commit quality gate mirrored in CI.

- **api (`apps/api`)**: `uv` (project + lockfile), `ruff` (lint + format), `ty` (type check), `pytest`.
- **web (`apps/web`)**: `pnpm` + Vite (React + TS), `oxlint` (lint), `oxfmt` (format), `vitest`.
- **Enforcement**: `lefthook` runs lint + format + type-check on staged files pre-commit; tests run pre-push and in CI; a `justfile` exposes shared one-liners (`just check`, `just fmt`); GitHub Actions runs the same commands as the source of truth.

## Why record this

The obvious path is ESLint + Prettier + mypy + Husky. We deliberately chose the faster Rust tools. This ADR exists to stop a future contributor from "fixing" the setup by reintroducing the mainstream stack — the deviation is intentional.

## Constraint

`ty` is pre-1.0 (0.0.x); its diagnostics can change between releases. Its version is therefore **pinned exactly** (via `uv`) and upgraded deliberately, never floated — otherwise an upstream release can break CI without a code change on our side.
