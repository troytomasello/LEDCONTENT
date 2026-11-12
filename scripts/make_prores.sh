#!/usr/bin/env bash
# Convert every master MP4 in the repo to ProRes 422 HQ (10-bit 4:2:2) for disguise.
# Usage (from the repo folder):   bash scripts/make_prores.sh
# Optional profile: bash scripts/make_prores.sh 2     (0=Proxy 1=LT 2=422 3=HQ, default 3)
# Output goes to ./prores/ with the same folder structure. Needs ffmpeg installed.
set -euo pipefail
PROFILE="${1:-3}"
find masters -name "*.mp4" | while read -r f; do
  out="prores/${f#masters/}"; out="${out%.mp4}_PRORES.mov"
  mkdir -p "$(dirname "$out")"
  if [ -f "$out" ]; then echo "skip  $out"; continue; fi
  echo "make  $out"
  ffmpeg -loglevel error -nostdin -y -i "$f" -c:v prores_ks -profile:v "$PROFILE" -vendor apl0 \
         -pix_fmt yuv422p10le -an "$out"
done
echo "done -> ./prores/"
