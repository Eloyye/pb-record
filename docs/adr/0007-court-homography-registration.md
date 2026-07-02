# Court homography via registration, bootstrapped by assisted-manual calibration

The court homography (pixel ↔ court coordinates) that the tracking layer ([ADR-0002](0002-tracking-first-perception.md)) depends on is obtained by **registering the known court template**, not by detecting lines. Classical line detection (Hough) is too noisy on broadcast footage — crowd, ads, and texture edges swamp the court lines.

Two facts shrink the problem: the Main Angle is near-static, so H is solved **per camera setup, not per frame**; and the court is a fully known template, so RANSAC rejects noisy correspondences against it.

## v1 approach — assisted-manual, then flywheel to a model

- During ingest, the user clicks/confirms court points once per setup; H is solved and validated by overlaying the reprojected template (**reprojection error** is the quality check).
- Each calibration **auto-generates training labels**: reprojecting the known template yields perfect court keypoints and a court mask for free.
- A court model (keypoint-heatmap, or segmentation→homography) is trained later on that corpus to remove the manual step. Whichever model is chosen, its labels come from this reprojection — so assisted-manual is the on-ramp, not a detour.

This mirrors the heuristic-bootstrap → correction → train-later pattern used for the Shape classifier.

## Consequences

- If a setup pans/zooms, H drifts; detect it via rising reprojection error and re-calibrate that segment. The eventual model can re-estimate per-segment or per-frame.
- No pickleball-specific pretrained court model exists. The keypoint architecture is borrowable from tennis (e.g. `TennisCourtDetector`), with the keypoint set remapped for the kitchen lines.

## Not chosen

- **Classical Hough line detection** — too noisy on broadcast; the problem that prompted this decision.
- **Training a court model up front** — needs a labeled seed set that assisted-manual calibration would have to produce anyway.
