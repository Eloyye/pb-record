# Pickleball Shot Analysis

The domain of turning professional pickleball broadcasts into a structured stream of shot events that can be sorted, reviewed, and (later) analysed. This glossary is the shared language for that domain. It is a glossary only — no implementation details.

## Language

### Broadcast structure

**Broadcast Match**:
A full, unedited professional pickleball broadcast (e.g. PPA, MLP) as ingested — containing live play interleaved with replays, graphics, and cutaways. The raw input to the system.
_Avoid_: video, clip, footage (too vague)

**Live Play**:
A continuous segment of the broadcast showing an actual point being contested, seen from the Main Angle. The only segments that yield real shot events.
_Avoid_: gameplay, action

**Replay**:
A re-showing — often slow-motion, sometimes from a secondary angle — of a point that was just played live. Must be excluded from shot events to avoid double-counting.
_Avoid_: highlight, slow-mo (slow-mo is a property, not the concept)

**Cutaway**:
Any non-play broadcast segment: crowd, players between points, commentators, coaching timeouts. Carries no shot events.

**Graphic**:
A broadcast overlay or full-screen element — the persistent scorebug, replay wipes, sponsor cards, stat panels. The scorebug's presence is a signal of Live Play.
_Avoid_: overlay, HUD

**Main Angle**:
The canonical high, wide camera behind the court used for live play. Shot events are counted only from this angle.
_Avoid_: main camera, broadcast angle

### Shots & rallies

**Shot**:
One player's single contact with the ball — an event, timestamped at the moment of Contact. The atomic unit the system detects, counts, and analyses.
_Avoid_: hit, stroke, swing

**Contact**:
The instant a paddle strikes the ball; the timestamp that identifies a Shot.
_Avoid_: strike, impact

**Rally**:
An ordered sequence of Shots making up one contested point, from serve to the ball going dead. Typically what one Live Play segment contains.
_Avoid_: point (that is the scoring outcome), exchange

**Clip**:
A rendered video projection of a Shot (or Rally) — typically Contact to next Contact plus padding — produced for viewing or export. A view over Shot events, never the unit itself.
_Avoid_: segment, cut

### Shot attributes

Every Shot carries these independent attributes. Zone, Shape, and Special describe one Shot; Rally Position is derived from Shot order.

**Zone**:
Where the striking player stands at Contact: `baseline` (back of court), `transition` (mid-court, between baseline and Kitchen), or `kitchen` (at the Kitchen line).
_Avoid_: position, court area

**Kitchen**:
The non-volley zone — the 7-foot area either side of the net where volleying is forbidden. The "Kitchen line" is its back edge, where dinking happens.
_Avoid_: NVZ, no-volley zone

**Shape**:
The character and arc of the ball a Shot produces: `drive | drop | dink | lob | volley | other`. Independent of Zone and Special.

**Drive**:
A hard, flat, fast groundstroke meant to attack or pressure; the ball travels low and quick.
_Avoid_: smash, power shot

**Drop**:
A soft shot with a high-to-low arc landing in or near the opponent's Kitchen, resetting the point. A "third-shot drop" is a Drop taken from the baseline.
_Avoid_: dropshot, reset

**Dink**:
A soft, low shot from at/near the Kitchen line that lands in the opponent's Kitchen, kept below attackable height.
_Avoid_: tap, soft shot

**Lob**:
A shot hit high and deep to push opponents off the Kitchen line.

**Volley**:
A Shot struck out of the air before the ball bounces, when not better described as a dink or drop — e.g. a block, punch, or put-away.
_Avoid_: block, punch, put-away (these are Volley subtypes, not separate Shapes in v1)

**Special Play**:
A named tactical play a Shot may be, orthogonal to Shape: `none | atp | erne`.

**ATP** (Around-the-Post):
A Shot whose ball path travels around the *outside* of the net post, below net height, rather than over the net. Defined by ball trajectory, not court position.
_Avoid_: around the net

**Erne**:
A Shot where the player is positioned at (or has jumped to) the sideline edge just outside the Kitchen, to volley near the net. Defined by player position, not ball trajectory.
_Avoid_: bert, Erne shot

**Rally Position**:
Which Shot this is within its Rally, derived from Shot order: `serve` (first), `return` (second), or `rally` (all subsequent). Gives serve/return/third-shot analytics for free.
_Avoid_: shot number, sequence index

### Review & labeling

**Candidate Shot**:
A Shot proposed by the pipeline but not yet human-reviewed. Its geometric attributes are derived automatically; its Shape is a heuristic (later, model) guess.
_Avoid_: prediction, proposal

**Confirmed Shot**:
A Candidate Shot a human has reviewed, correcting any wrong attribute. Confirmed Shots are both the trustworthy analytics data and the training labels for the Shape classifier.
_Avoid_: verified, approved

**Correction**:
A human edit to a Candidate Shot's attribute during review. The unit from which training labels are generated.
_Avoid_: fix, annotation
