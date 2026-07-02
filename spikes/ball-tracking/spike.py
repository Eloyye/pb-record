# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ultralytics>=8.3",
#   "opencv-python>=4.10",
#   "numpy>=1.26",
#   "pandas>=2.2",
#   "matplotlib>=3.9",
# ]
# ///
"""Ball-tracking feasibility spike.

Runs (or ingests) a per-frame ball track over a pickleball clip, derives candidate
Contact events from trajectory kinematics, and emits evidence to judge whether
tracking-first perception (ADR-0002) is viable. Throwaway — see README.md.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


# --------------------------------------------------------------------------- #
# Ball position, per frame                                                     #
# --------------------------------------------------------------------------- #
def detect_with_yolo(video: Path, weights: str, ball_class: int) -> pd.DataFrame:
    """Smoke-test detector. Weak on tiny fast balls — see README."""
    from ultralytics import YOLO  # lazy: not needed for the --predictions path

    model = YOLO(weights)
    cap = cv2.VideoCapture(str(video))
    rows: list[dict] = []
    f = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        kw = {"verbose": False}
        if ball_class >= 0:
            kw["classes"] = [ball_class]
        res = model(frame, **kw)[0]
        x = y = np.nan
        vis = 0
        if res.boxes is not None and len(res.boxes) > 0:
            confs = res.boxes.conf.cpu().numpy()
            best = int(confs.argmax())
            cx, cy = res.boxes.xywh.cpu().numpy()[best][:2]
            x, y, vis = float(cx), float(cy), 1
        rows.append({"frame": f, "x": x, "y": y, "visible": vis})
        f += 1
    cap.release()
    return pd.DataFrame(rows)


def load_predictions_csv(path: Path, n_frames: int) -> pd.DataFrame:
    """Ingest any tracker's output, reshaped to frame,x,y,visible."""
    df = pd.read_csv(path)
    df = df.set_index("frame").reindex(range(n_frames))
    df["visible"] = df["visible"].fillna(0).astype(int)
    df.loc[df["visible"] == 0, ["x", "y"]] = np.nan
    return df.reset_index()


# --------------------------------------------------------------------------- #
# Track post-processing + contact detection                                    #
# --------------------------------------------------------------------------- #
def fill_short_gaps(vals: np.ndarray, valid: np.ndarray, max_gap: int) -> np.ndarray:
    """Linearly interpolate only gaps of <= max_gap frames; leave long gaps NaN."""
    out = vals.copy()
    idx = np.flatnonzero(valid)
    for a, b in zip(idx[:-1], idx[1:]):
        gap = b - a - 1
        if 0 < gap <= max_gap:
            out[a + 1 : b] = np.interp(range(a + 1, b), [a, b], [vals[a], vals[b]])
    return out


def moving_average(vals: np.ndarray, valid: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return vals
    out = vals.copy()
    half = window // 2
    for i in np.flatnonzero(valid):
        lo, hi = max(0, i - half), min(len(vals), i + half + 1)
        seg = vals[lo:hi][valid[lo:hi]]
        if len(seg):
            out[i] = seg.mean()
    return out


def angle_deg(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = float(v1 @ v2)
    cross = float(v1[0] * v2[1] - v1[1] * v2[0])
    return math.degrees(math.atan2(abs(cross), dot))


def detect_contacts(
    x: np.ndarray,
    y: np.ndarray,
    valid: np.ndarray,
    fps: float,
    angle_thresh: float,
    min_speed: float,
    refractory_s: float,
) -> list[int]:
    """Contact = sharp direction reversal in the trajectory, with a refractory gap."""
    p = np.stack([x, y], axis=1)
    refractory = max(1, int(refractory_s * fps))
    candidates: list[tuple[int, float]] = []
    for f in range(1, len(x) - 1):
        if not (valid[f - 1] and valid[f] and valid[f + 1]):
            continue
        v1, v2 = p[f] - p[f - 1], p[f + 1] - p[f]
        if max(np.linalg.norm(v1), np.linalg.norm(v2)) < min_speed:
            continue  # ball ~stationary/lost: direction is noise
        a = angle_deg(v1, v2)
        if a >= angle_thresh:
            candidates.append((f, a))
    # greedily keep the sharpest turn within each refractory window
    contacts: list[int] = []
    for f, _ in sorted(candidates, key=lambda c: -c[1]):
        if all(abs(f - c) >= refractory for c in contacts):
            contacts.append(f)
    return sorted(contacts)


# --------------------------------------------------------------------------- #
# Outputs                                                                       #
# --------------------------------------------------------------------------- #
def render_video(
    video: Path,
    out: Path,
    x: np.ndarray,
    y: np.ndarray,
    valid: np.ndarray,
    contacts: set[int],
    trail: int,
) -> None:
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter.fourcc(*"mp4v"), fps, (w, h))
    f = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        for k in range(max(0, f - trail), f + 1):  # fading trail
            if valid[k]:
                age = f - k
                r = max(2, 7 - age)
                shade = int(255 * (1 - age / max(1, trail)))
                cv2.circle(frame, (int(x[k]), int(y[k])), r, (0, shade, 255), -1)
        near = [c for c in contacts if abs(c - f) <= 3]
        if near and valid[f]:
            cv2.circle(frame, (int(x[f]), int(y[f])), 18, (0, 255, 0), 3)
            cv2.putText(
                frame,
                "CONTACT",
                (int(x[f]) + 22, int(y[f])),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
        cov = 100.0 * valid[: f + 1].mean() if f else 0.0
        cv2.putText(
            frame,
            f"f{f}  {f / fps:5.2f}s  cov {cov:4.1f}%",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        writer.write(frame)
        f += 1
    cap.release()
    writer.release()


def plot_speed(out: Path, x, y, valid, fps, contacts) -> None:
    n = len(x)
    t = np.arange(n) / fps
    speed = np.full(n, np.nan)
    for f in range(1, n):
        if valid[f] and valid[f - 1]:
            speed[f] = math.hypot(x[f] - x[f - 1], y[f] - y[f - 1]) * fps
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t, speed, lw=1.0, color="#378ADD", label="ball speed (px/s)")
    for c in contacts:
        ax.axvline(c / fps, color="#1D9E75", lw=1.0, alpha=0.8)
    for f in range(n):  # shade frames with no detection
        if not valid[f]:
            ax.axvspan(
                (f - 0.5) / fps, (f + 0.5) / fps, color="#E24B4A", alpha=0.12, lw=0
            )
    ax.set_xlabel("time (s)")
    ax.set_ylabel("speed (px/s)")
    ax.set_title("ball speed over time — green = detected contact, red = no detection")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    plt.close(fig)


def report(name: str, valid: np.ndarray, fps: float, contacts: list[int]) -> None:
    n = len(valid)
    detected = int(valid.sum())
    # longest run of consecutive misses
    longest = run = 0
    for v in valid:
        run = 0 if v else run + 1
        longest = max(longest, run)
    print(f"\n===== {name} =====")
    print(f"frames              : {n}  ({n / fps:.1f}s @ {fps:.1f} fps)")
    print(f"ball detected       : {detected}/{n}  ({100 * detected / n:.1f}% coverage)")
    print(f"longest gap          : {longest} frames  ({longest / fps:.2f}s)")
    print(f"candidate contacts  : {len(contacts)}")
    if contacts:
        times = ", ".join(f"{c / fps:.2f}s" for c in contacts)
        print(f"contact times        : {times}")
    print("verdict → compare coverage/gaps/contact-alignment against README rubric.")


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Ball-tracking feasibility spike.")
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--predictions", type=Path, help="tracker CSV; else built-in YOLO")
    ap.add_argument("--weights", default="yolo11n.pt", help="YOLO weights (smoke test)")
    ap.add_argument(
        "--ball-class", type=int, default=32, help="COCO sports-ball=32; -1=any"
    )
    ap.add_argument("--out-dir", type=Path, help="default: alongside the video")
    ap.add_argument(
        "--angle", type=float, default=100.0, help="contact turn threshold (deg)"
    )
    ap.add_argument(
        "--min-speed", type=float, default=4.0, help="min px/frame to trust direction"
    )
    ap.add_argument(
        "--max-gap", type=int, default=4, help="max frames to interpolate across"
    )
    ap.add_argument(
        "--smooth", type=int, default=3, help="moving-average window (1=off)"
    )
    ap.add_argument(
        "--refractory", type=float, default=0.15, help="min seconds between contacts"
    )
    ap.add_argument(
        "--trail", type=int, default=12, help="trajectory trail length (frames)"
    )
    ap.add_argument("--no-video", action="store_true", help="skip annotated render")
    args = ap.parse_args()

    if not args.video.exists():
        raise SystemExit(f"video not found: {args.video}")
    out_dir = args.out_dir or args.video.parent / f"{args.video.stem}_spike"
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(args.video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if args.predictions:
        df = load_predictions_csv(args.predictions, n_frames)
        source = args.predictions.name
    else:
        print(
            "running built-in YOLO smoke-test detector (see README — weak on small balls)…"
        )
        df = detect_with_yolo(args.video, args.weights, args.ball_class)
        source = f"yolo:{args.weights}"

    raw_valid = df["visible"].to_numpy() == 1
    x = fill_short_gaps(df["x"].to_numpy(float), raw_valid, args.max_gap)
    y = fill_short_gaps(df["y"].to_numpy(float), raw_valid, args.max_gap)
    valid = ~np.isnan(x) & ~np.isnan(y)
    x = moving_average(x, valid, args.smooth)
    y = moving_average(y, valid, args.smooth)

    contacts = detect_contacts(
        x, y, valid, fps, args.angle, args.min_speed, args.refractory
    )

    pd.DataFrame(
        {
            "frame": np.arange(len(x)),
            "x": x,
            "y": y,
            "detected": raw_valid.astype(int),
            "valid": valid.astype(int),
        }
    ).to_csv(out_dir / "track.csv", index=False)
    plot_speed(out_dir / "speed_plot.png", x, y, valid, fps, contacts)
    if not args.no_video:
        print("rendering annotated video…")
        render_video(
            args.video,
            out_dir / "annotated.mp4",
            x,
            y,
            valid,
            set(contacts),
            args.trail,
        )

    report(f"{args.video.name}  [{source}]", valid, fps, contacts)
    print(f"outputs → {out_dir}/  (annotated.mp4, speed_plot.png, track.csv)")


if __name__ == "__main__":
    main()
