# pb-record — decisions so far (PRD input)

Condensed decision log to seed the PRD. The "why" for each lives in `docs/adr/`; the
glossary in [`CONTEXT.md`](../CONTEXT.md). Nothing here is final until the ball-tracking
spike clears — see **Status**.

> **PRD:** drafted as [Eloyye/pb-record#1](https://github.com/Eloyye/pb-record/issues/1) — `needs-info` (draft, gated on the spike).

## Product
- **What:** turn professional pickleball broadcasts into a structured stream of shot events, surfaced as sorted per-shot clips.
- **North star:** an **analytics foundation** (structured, queryable shot data), not just a clip library. This lens drives the data-model choices.

## Scope (v1)
- **In:** ingest a full broadcast → parse to live play → track → derive shots → human review/correct → sort & export clips.
- **Out — nullable hooks kept:** player identity, shot success/failure, analytics UI, real-time/live, score parsing, handedness & contact-type.

## Domain (→ CONTEXT.md)
- **Shot = one contact**, an event timestamped at contact. **Rally** = ordered Shots. **Clip** = a rendered view over Shots (virtual until export).
- **Attributes:** Zone `baseline|transition|kitchen` · Shape `drive|drop|dink|lob|volley|other` · Special `none|atp|erne` · Rally-position `serve|return|rally` (derived from order).
- **Review lifecycle:** Candidate Shot → (Correction) → Confirmed Shot. Confirmed Shots are both trusted data and training labels.

## Perception pipeline
- **Input:** full raw broadcast match, not pre-trimmed clips — [ADR-0001](adr/0001-full-broadcast-input.md).
- **Tracking-first**, not end-to-end video: off-the-shelf pose + ball tracking + court homography → court coordinates; contact, boundaries, zone, ATP, erne, rally-position all **derived by geometry** — [ADR-0002](adr/0002-tracking-first-perception.md).
- **Broadcast parsing** (live/replay/cutaway/graphic) is **tracking-assisted, not custom-trained**; replays filtered to avoid double-counting — [ADR-0003](adr/0003-tracking-assisted-broadcast-parsing.md).
- **Court homography** by template registration, bootstrapped with assisted-manual calibration → flywheel to a keypoint/segmentation model; **not** Hough line detection — [ADR-0007](adr/0007-court-homography-registration.md).
- **Only one trained model:** the **Shape classifier** — heuristic cold-start, then trained from review corrections (the flywheel). Everything else is off-the-shelf or derived.

## Architecture (→ ADR-0004 / ADR-0005)
- **Local single-machine monolith:** localhost, no auth; heavy work runs in a background GPU **worker + job queue** (processing is async, never in a request).
- **Stack:** Python **FastAPI** + **React** SPA in a monorepo (`apps/api`, `apps/web`) + worker; **Postgres**.
- **Data model:** `Match → Segment → Rally → Shot`. `Shot.player_id` & `Shot.outcome` are nullable now (deferred scope, no future migration). Raw per-frame tracks as parquet/npz files; per-shot summaries denormalized into the DB. Clips virtual.

## Dashboard
- Ingest (point at file/URL) → job progress → **rally-timeline review** (fix shot boundaries *and* Shape) → browse/filter → export per-attribute folders. No analytics surface in v1.

## Tooling & quality (→ ADR-0006)
- **api:** uv · ruff · ty (version-pinned, it is pre-1.0) · pytest. **web:** pnpm · Vite · oxlint · oxfmt · vitest.
- **Gate:** lefthook pre-commit (lint/format/typecheck), tests pre-push + CI, `just check`; GitHub Actions mirrors. No ESLint/Prettier/mypy/Husky.

## Hardware
- Model training + inference on an **RTX 5080** (Blackwell → needs a CUDA 12.8 torch build). Dev/orchestration on macOS; heavy GPU work on the 5080 box.

## Status — the one gate before building
- The whole design rests on **ball-tracking reliability** ([ADR-0002](adr/0002-tracking-first-perception.md)). A throwaway spike exists in [`spikes/ball-tracking/`](../spikes/ball-tracking) with a GREEN/YELLOW/RED rubric; it needs a real live-play clip and a run on the 5080 box (WASB tennis weights via the BlurBall harness).
- **The PRD should treat "proceed" as conditional on a GREEN/YELLOW spike result.** A RED result reopens the perception approach before any monolith is built.
