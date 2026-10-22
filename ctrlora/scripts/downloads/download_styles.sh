#!/usr/bin/env bash
set -u
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1
PXY="${HTTPS_PROXY:-${ALL_PROXY:-}}"

dl () {
  local url="$1" out="$2"
  mkdir -p "$(dirname -- "$out")"
  echo "### $out"
  curl -L -C - --retry 8 --retry-delay 3 -x "$PXY" -o "$out.part" "$url" \
    && mv "$out.part" "$out" && echo "### done $out ($(du -h "$out" | cut -f1))" || echo "### FAILED $out"
}

dl "https://civitai.com/api/download/models/23979"  "ckpts/sd15/oilPainting_v10.safetensors"
dl "https://civitai.com/api/download/models/220049" "ckpts/sd15/aziibpixelmix_v10.safetensors"
dl "https://civitai.com/api/download/models/348981" "ckpts/sd15/mistoonAnime_v30.safetensors"
dl "https://civitai.com/api/download/models/245598" "ckpts/sd15/realisticVisionV60B1.safetensors"

echo "### STYLE BASES DOWNLOAD COMPLETE"
