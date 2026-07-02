# Shot perception is tracking-first, not end-to-end video

The system perceives play through a **geometry layer** — off-the-shelf player pose + ball tracking + court homography convert pixels into court coordinates — rather than feeding raw video into end-to-end models. Contact, Shot boundaries, Zone, ATP, and Rally Position are *derived geometrically*. Only Shape (and possibly Erne) use small custom-trained classifiers over trajectory + player-crop features.

We chose this because it slashes the labeling burden for a solo builder, generalizes across matches better than pixel models, and — decisively for the analytics goal — the court-coordinate tracks it produces (ball speed, placement, player positioning) *are themselves* the substrate every future analytic will need.

## Consequences

- Depends on off-the-shelf trackers; the fragile step is **ball tracking** (the ball is small, fast, and often occluded). Tracking errors propagate into Contact and boundary detection.
- Requires **court calibration / homography** per camera setup.
- The one clearly-custom pickleball model is the **Shape classifier**. This narrows what must be labeled.

## Considered options

- **Raw-video end-to-end custom models** — learn boundaries + every attribute from labeled video. Rejected: most data-hungry, nothing derived for free, tiny fast ball is hard for pixel models.
- **Tracking-first with custom-trained trackers** — same structure but train pose/ball trackers from scratch. Rejected: frame-by-frame ball/pose labeling is a large data burden the off-the-shelf route avoids.
