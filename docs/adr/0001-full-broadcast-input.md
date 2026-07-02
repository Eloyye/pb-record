# Input is the full raw broadcast match, not pre-trimmed clips

v1 ingests full, unedited professional broadcasts (PPA/MLP) rather than clips a human has already trimmed to live play. We chose this because the analytics goal needs real pro-match data at scale, and hand-trimming every match is a bottleneck that doesn't scale.

## Consequences

- A **broadcast-parsing front-end** is mandatory before any shot analysis: scene-cut detection, and classifying each segment as Live Play / Replay / Graphic / Cutaway, keeping only the Main Angle.
- **Replays must be filtered.** A slow-motion replay is the same rally a second time; if it leaks through it double-counts Shot events and corrupts every downstream statistic. Data being *wrong* is worse than data being absent.

## Considered options

- **Pre-trimmed live-play clips** — human trims each clip to one angle of continuous play. Rejected: less realistic, and the manual trim is the bottleneck we're trying to avoid.
- **Single fixed-camera footage** — no broadcast artifacts at all. Rejected: little single-angle professional footage exists.
