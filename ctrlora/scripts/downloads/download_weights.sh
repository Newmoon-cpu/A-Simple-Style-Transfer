#!/usr/bin/env bash
set -u
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1
MIRROR="https://hf-mirror.com"
BASE="$MIRROR/xyfJASON/ctrlora/resolve/main"
ANNOT="$MIRROR/lllyasviel/Annotators/resolve/main"
SD15="$MIRROR/runwayml/stable-diffusion-v1-5/resolve/main"

dl () {
  local url="$1" out="$2"
  mkdir -p "$(dirname -- "$out")"
  echo "### downloading $out"
  curl -L -C - --retry 8 --retry-delay 3 -o "$out.part" "$url" \
    && mv "$out.part" "$out" \
    && echo "### done $out ($(du -h "$out" | cut -f1))" \
    || echo "### FAILED $out"
}

dl "$BASE/ctrlora-basecn/ctrlora_sd15_basecn700k.ckpt" \
   "ckpts/ctrlora-basecn/ctrlora_sd15_basecn700k.ckpt"

dl "$BASE/ctrlora-loras/novel-conditions/ctrlora_sd15_basecn700k_lineart_rank128_1kimgs_1ksteps.ckpt" \
   "ckpts/ctrlora-loras/novel-conditions/ctrlora_sd15_basecn700k_lineart_rank128_1kimgs_1ksteps.ckpt"

dl "$BASE/ctrlora-loras/novel-conditions/ctrlora_sd15_basecn700k_palette_rank128_100kimgs_100ksteps.ckpt" \
   "ckpts/ctrlora-loras/novel-conditions/ctrlora_sd15_basecn700k_palette_rank128_100kimgs_100ksteps.ckpt"

dl "$SD15/v1-5-pruned-emaonly.ckpt" \
   "ckpts/sd15/v1-5-pruned-emaonly.ckpt"

mkdir -p annotator/ckpts
dl "$ANNOT/sk_model.pth"  "annotator/ckpts/sk_model.pth"
dl "$ANNOT/sk_model2.pth" "annotator/ckpts/sk_model2.pth"

echo "### ALL DOWNLOADS COMPLETE"
