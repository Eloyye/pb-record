#!/usr/bin/env python3
"""Convert a tracker's per-frame output into the spike's `frame,x,y,visible` format.

Defaults assume a TrackNet/WASB-style `Frame,Visibility,X,Y` schema. If BlurBall names
its columns differently, inspect one row and override with the flags. Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import sys


def pick(header: list[str], *cands: str) -> str | None:
    low = {h.lower(): h for h in header}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="tracker output CSV")
    ap.add_argument("--out", default="predictions.csv")
    ap.add_argument("--frame-col")
    ap.add_argument("--x-col")
    ap.add_argument("--y-col")
    ap.add_argument("--vis-col")
    a = ap.parse_args()

    with open(a.input, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        fc = a.frame_col or pick(header, "frame", "idx", "frame_id")
        xc = a.x_col or pick(header, "x", "cx", "x_pred", "px")
        yc = a.y_col or pick(header, "y", "cy", "y_pred", "py")
        vc = a.vis_col or pick(header, "visible", "visibility", "visi", "vis", "score", "conf")
        if not (fc and xc and yc):
            sys.exit(f"couldn't find frame/x/y columns in {header}; pass --frame-col/--x-col/--y-col")

        rows: list[tuple[int, object, object, int]] = []
        for i, row in enumerate(reader):
            raw = row.get(fc, "")
            frame = int(float(raw)) if raw not in (None, "") else i
            try:
                xv: float | None = float(row.get(xc, ""))
                yv: float | None = float(row.get(yc, ""))
            except (TypeError, ValueError):
                xv = yv = None
            visible = 1
            if vc and row.get(vc, "") not in (None, ""):
                try:
                    visible = 1 if float(row[vc]) > 0 else 0
                except (TypeError, ValueError):
                    visible = 1
            if xv is None or yv is None or (xv == 0 and yv == 0):
                visible = 0
            rows.append((frame, "" if not visible else xv, "" if not visible else yv, visible))

    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "x", "y", "visible"])
        w.writerows(rows)
    detected = sum(v for *_, v in rows)
    print(f"wrote {len(rows)} rows ({detected} detected) -> {a.out}")


if __name__ == "__main__":
    main()
