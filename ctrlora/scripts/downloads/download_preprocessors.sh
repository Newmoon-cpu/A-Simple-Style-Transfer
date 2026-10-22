#!/usr/bin/env bash
set -u
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1
HF="https://hf-mirror.com/lllyasviel/Annotators/resolve/main"
PXY="${HTTPS_PROXY:-${ALL_PROXY:-}}"

dl () {  # url out [use_proxy]
  local url="$1" out="$2" px="${3:-}"
  mkdir -p "$(dirname -- "$out")"
  echo "### $out"
  if [ -n "$px" ]; then
    curl -L -C - --retry 8 --retry-delay 3 -x "$PXY" -o "$out.part" "$url"
  else
    curl -sL -C - --retry 8 --retry-delay 3 -o "$out.part" "$url"
  fi && mv "$out.part" "$out" && echo "### done $out" || echo "### FAILED $out"
}

mkdir -p annotator/ckpts

# openpose（骨架）
dl "$HF/body_pose_model.pth" "annotator/ckpts/body_pose_model.pth"
dl "$HF/hand_pose_model.pth" "annotator/ckpts/hand_pose_model.pth"
dl "$HF/facenet.pth" "annotator/ckpts/facenet.pth"

# seg（分割）
dl "$HF/upernet_global_small.pth" "annotator/ckpts/upernet_global_small.pth"

# hed
dl "$HF/ControlNetHED.pth" "annotator/ckpts/ControlNetHED.pth"

# normal
dl "$HF/scannet.pt" "annotator/ckpts/scannet.pt"

# depth（Google Storage，需代理）
dl "https://storage.googleapis.com/sfr-unicontrol-data-research/annotator/ckpts/dpt_large_384.pt" \
   "annotator/ckpts/dpt_large_384.pt" proxy

echo "### PREPROCESSORS DOWNLOAD COMPLETE"
