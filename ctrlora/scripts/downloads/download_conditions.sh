#!/usr/bin/env bash
set -u
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1
MIRROR="https://hf-mirror.com/xyfJASON/ctrlora/resolve/main"

dl () {
  local url="$1" out="$2"
  mkdir -p "$(dirname -- "$out")"
  echo "### $out"
  curl -sL -C - --retry 8 --retry-delay 3 -o "$out.part" "$url" \
    && mv "$out.part" "$out" && echo "### done $out" || echo "### FAILED $out"
}

mkdir -p ckpts/ctrlora-loras/base-conditions ckpts/ctrlora-loras/novel-conditions

for c in canny depth hed normal openpose seg; do
  dl "$MIRROR/ctrlora-loras/base-conditions/ctrlora_sd15_basecn700k_${c}_rank128.ckpt" \
     "ckpts/ctrlora-loras/base-conditions/ctrlora_sd15_basecn700k_${c}_rank128.ckpt"
done

for n in illusion_rank128_100kimgs_100ksteps pixel_rank128_100kimgs_100ksteps deraindrop_rank128_861imgs_100ksteps llie_rank128_100kimgs_100ksteps; do
  dl "$MIRROR/ctrlora-loras/novel-conditions/ctrlora_sd15_basecn700k_${n}.ckpt" \
     "ckpts/ctrlora-loras/novel-conditions/ctrlora_sd15_basecn700k_${n}.ckpt"
done

echo "### CONDITIONS DOWNLOAD COMPLETE"
