# Data model is analytics-oriented, not clip-oriented

The data model is structured for a future analytics foundation, not just for sorting clips. Entities: **Match → Segment** (`live | replay | cutaway | graphic`) **→ Rally → Shot**, where Shot carries the derived geometric attributes (Zone, ATP, Erne, Rally position, boundaries) plus Shape.

We chose this because the stated north star is an analytics foundation; a folders-of-files or flat-clip model would foreclose it.

## Consequences

- **Deferred scope is represented as nullable columns now.** `Shot.player_id` and `Shot.outcome` exist but stay null in v1, so player identification and shot success/failure slot in later with no migration.
- **Raw tracks are files, summaries are rows.** Per-frame ball/player court-coordinates live as parquet/npz files referenced from the DB; per-shot summary features are denormalized onto Shot so analytics queries stay fast.
- **Clips are virtual.** A Clip is a time-range into the source video, rendered to an actual file only on export — no wasted disk, consistent with "Clip is a view over Shot events."
