# Spike: ball-tracking feasibility

Throwaway spike. **Question it answers:** can an off-the-shelf small-ball tracker
produce a trajectory good enough to recover `Contact` events on real broadcast
pickleball? That is the load-bearing assumption of
[ADR-0002](../../docs/adr/0002-tracking-first-perception.md) (tracking-first
perception). If it fails, we reopen that ADR *before* building anything on it.

This directory is intentionally **outside the quality gate**
([ADR-0006](../../docs/adr/0006-toolchain-and-quality-gates.md)) — exploratory and
disposable.

## What it does

Given a live-play clip, it:

1. Gets a per-frame ball position — either the built-in YOLO smoke-test detector,
   or a CSV you exported from a real tracker (WASB / TrackNetV3).
2. Interpolates short gaps, derives velocity/speed, and detects candidate
   `Contact`s as sharp trajectory direction-changes.
3. Emits an annotated video (ball + fading trail + contact flashes), a
   speed-vs-time plot, a processed track CSV, and a printed coverage/contact report.

You then eyeball the outputs against the rubric below.

## Setup

Needs `uv`. No manual install — `uv run` resolves deps from the inline script header
on first run. (GPU is optional; a few short clips run fine on CPU.)

## Usage

**Quick smoke test — built-in YOLO (proves the harness, weak ball recall):**

    uv run spike.py --video clip.mp4

COCO "sports ball" is a *weak* detector for a tiny, fast pickleball. A poor result
here is **not** a verdict on the design — it only exercises the harness. The real
test uses a purpose-built tracker:

**Real evaluation — WASB (recommended):**

1. Clone https://github.com/nttcom/WASB-SBDT and follow its `GET_STARTED.md`.
2. Download weights: `./src/setup_scripts/setup_weights.sh`.
3. Run its inference on your clip (its **tennis** model transfers best to pickleball).
4. Map its per-frame output to the CSV format below, then:

       uv run spike.py --video clip.mp4 --predictions wasb.csv

`TrackNetV3` (qaz812345/TrackNetV3) works the same way — take its `predict.py`
output and reshape to the four columns below.

## Predictions CSV format (tracker-agnostic interchange)

    frame,x,y,visible
    0,,,0
    1,812.4,331.9,1
    2,815.0,330.1,1

- `frame` — 0-based index. `x,y` — ball centre in pixels (blank if not detected).
- `visible` — 1 detected, 0 missing. Map any tracker's output onto these 4 columns.

## Choosing clips

3–5 short (5–20 s) single-angle live-play clips, no replays/cutaways inside a clip.
Deliberately include BOTH fast baseline drives (motion blur) and slow kitchen dinks
(tiny, slow, low-contrast) — they fail differently, and dinks are the hard case.

## The rubric → ADR-0002 decision

Watch the annotated video and the speed plot, per clip:

- **GREEN — proceed with tracking-first.** Ball detected in most live-play frames
  (~≥75% coverage), gaps mostly < ~5 frames, and candidate contacts visibly line up
  with real hits.
- **YELLOW — viable, but fine-tune.** ~40–75% coverage or frequent short gaps, yet
  contacts are still mostly recoverable after interpolation. Keep the architecture;
  plan to fine-tune the tracker on pickleball.
- **RED — reopen ADR-0002.** <~40% coverage, long dropouts through rallies, or
  contacts not recoverable. The assumption fails; reconsider raw-video models or a
  heavier custom ball tracker before building on geometry.

Report coverage %, longest gap, and contact alignment for each clip — that's the
evidence for the decision.
