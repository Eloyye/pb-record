# Broadcast parsing is tracking-assisted, not custom-trained

We do **not** train custom models to segment the broadcast into Live Play / Replay / Cutaway / Graphic. Instead, live play is derived primarily from the tracking layer: a calibrated court plus a normal-speed ball track indicates Live Play; slow-motion shows up as a track velocity/timing mismatch; replays usually drop the live scorebug. This is combined with off-the-shelf scene-cut detection, and at most a small keyframe classifier for genuinely ambiguous frames.

This **reverses an earlier intent** to train full custom broadcast models, which tracking-first perception ([ADR-0002](0002-tracking-first-perception.md)) made largely redundant.

## Consequences

- Replay filtering — the guard against double-counting Shot events — now rests on derived signals rather than a dedicated model.
- If those signals prove unreliable in practice, the fallback is a **single focused replay/slow-mo classifier**, not a full broadcast-model suite.
