## Agent skills

### Issue tracker

Issues are tracked in this repo's GitHub Issues via the `gh` CLI. External PRs are not pulled into triage. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) — no overrides. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Quality checks

Toolchain and the pre-commit gate are defined in [ADR-0006](docs/adr/0006-toolchain-and-quality-gates.md): `uv` + `ruff` + `ty` (pinned) + `pytest` for `apps/api`; `pnpm` + Vite + `oxlint` + `oxfmt` + `vitest` for `apps/web`; enforced by `lefthook`, mirrored in CI. Run `just check` before proposing changes. Do not reintroduce ESLint / Prettier / mypy / Husky — the Rust toolchain is deliberate. Configs are created at scaffold time.
