#!/usr/bin/env bash
# Prep + run WASB-family ball tracking on ONE custom clip, on the RTX 5080 (Linux) box.
# Output: BlurBall's per-frame predictions; convert with wasb_to_csv.py, then feed spike.py.
#
# Authored on a Mac and NOT executed there — see WASB_5080.md for the two likely first-run snags.
set -euo pipefail

CLIP="${1:?usage: bash run_wasb_5080.sh /path/to/live_play_clip.mp4}"
WORK="${WORK:-$HOME/wasb-spike}"
PY="${PY:-python3.10}"   # torch 2.7+/cu128 supports 3.10–3.12; NOT 3.14

echo ">> work dir: $WORK"
mkdir -p "$WORK"; cd "$WORK"

# 1. Repos: BlurBall = the video-inference harness WASB lacks; WASB-SBDT = the tennis weights.
[ -d blurball ]  || git clone https://github.com/cogsys-tuebingen/blurball.git
[ -d WASB-SBDT ] || git clone https://github.com/nttcom/WASB-SBDT.git

# 2. Env. Blackwell (sm_120 / RTX 5080) needs a CUDA 12.8 torch — NOT BlurBall's pinned torch 2.2.2.
"$PY" -m venv .venv; source .venv/bin/activate
pip install -U pip
grep -viE '^(torch|torchvision|torchaudio)==' blurball/requirements.txt > /tmp/blurball_reqs_notorch.txt
pip install -r /tmp/blurball_reqs_notorch.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128   # bump to current stable if needed

# 3. WASB tennis weights (closest public match to a pickleball ball).
( cd WASB-SBDT/src && sh setup_scripts/setup_weights.sh )   # if Google Drive blocks wget: `pip install gdown` and re-fetch
WEIGHTS="$WORK/WASB-SBDT/src/pretrained_weights/wasb_tennis_best.pth.tar"
[ -f "$WEIGHTS" ] || { echo "!! tennis weights missing at $WEIGHTS (check setup_weights.sh output)"; exit 1; }

# 4. Inference: BlurBall harness + WASB tennis checkpoint.
cd blurball
python main.py --config-name=inference_wasb \
  detector.model_path="$WEIGHTS" \
  +input_vid="$CLIP" \
  detector.step=1 || { echo "!! inference failed — see WASB_5080.md (torch/Blackwell or checkpoint-load)"; exit 1; }

# 5. BlurBall (hydra) writes under ./outputs/<date>/. Show recent CSVs to convert.
echo ">> done. recent CSVs BlurBall may have written:"
find "$PWD/outputs" -name '*.csv' -newermt '-10 min' 2>/dev/null || true
echo ">> next: run wasb_to_csv.py (in the spike dir) on that CSV --out predictions.csv,"
echo ">>       then: uv run spike.py --video \"$CLIP\" --predictions predictions.csv"
