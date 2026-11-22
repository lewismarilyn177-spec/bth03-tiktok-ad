#!/bin/sh
# Assemble the ad: main frames -> badge overlay (first frame to card) ->
# referral end card overlay (last 2.5s) -> cover caret -> type referral code.
set -e
KIT=${PRESS_KIT:-/root/makefun/bth03-assets/pk/make-fun-press-kit}
FRAMES=${FRAMES_DIR:-/tmp/bth03-frames}
CODE=${REF_CODE:-hy1jjda8}
CARD_START=17.5
REST=1.433

ffmpeg -y -framerate 30 -i "$FRAMES/f%05d.png" \
  -i "$KIT/brand-badge/9x16/makefun-badge-9x16.png" \
  -c:v libvpx-vp9 -i "$KIT/referral-card/9x16/makefun-card-9x16-transparent.webm" \
  -filter_complex "\
[0:v][1:v]overlay=0:0:enable='lte(t,$CARD_START-0.01)'[m1];\
[m1][2:v]overlay=0:0:enable='gte(t,$CARD_START)':eof_action=repeat[m2];\
[m2]drawbox=x=206:y=1228:w=14:h=86:color=white@1:t=fill:enable='gte(t,$CARD_START)'[m3];\
[m3]drawtext=fontfile=/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf:text='$CODE':fontsize=62:fontcolor=#191419:x=210+((510-text_w)/2):y=1232+((78-text_h)/2):enable='gte(t,$CARD_START+$REST)'[vout]" \
  -map "[vout]" -an -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -r 30 -movflags +faststart makefun-ad.mp4
ffprobe -v error -show_entries format=duration,size -of default=nw=1 makefun-ad.mp4
