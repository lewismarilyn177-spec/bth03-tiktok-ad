#!/bin/sh
# build-video.sh — assemble rendered frames into final ad

set -eu

FRAMES_DIR="${FRAMES_DIR:-/tmp/bth03-frames}"
REF_CODE="${REF_CODE:-hy1jjda8}"
OUTPUT="makefun-ad.mp4"

BADGE="/root/makefun/bth03-assets/pk/make-fun-press-kit/brand-badge/9x16/makefun-badge-9x16.png"
CARD="/root/makefun/bth03-assets/pk/make-fun-press-kit/referral-card/9x16/makefun-card-9x16-transparent.webm"
FONT="/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"

ffmpeg -y \
  -framerate 30 -i "${FRAMES_DIR}/f%05d.png" \
  -i "${BADGE}" \
  -c:v libvpx-vp9 -i "${CARD}" \
  -filter_complex "
    [0:v][1:v]overlay=0:0:enable='lt(t,17.49)'[v0];
    [v0][2:v]overlay=0:0:enable='gte(t,17.5)':eof_action=repeat[v1];
    [v1]drawbox=x=206:y=1228:w=14:h=86:color=white:t=fill:enable='gte(t,17.5)'[v2];
    [v2]drawtext=fontfile=${FONT}:fontsize=62:fontcolor=#191419:
      text='${REF_CODE}':
      x=(w-text_w)/2:y=1232+(78-text_h)/2:
      enable='gte(t,18.933)'
  " \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -r 30 -an -movflags +faststart \
  "${OUTPUT}"

ffprobe -v error -show_entries format=duration,size -of default=nw=1:nk=1 "${OUTPUT}"