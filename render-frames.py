#!/usr/bin/env python3
"""Render the make.fun TikTok ad frames (1080x1920 @ 30fps, 21.5s).

Creative: dark-mode motion graphics, text-on-screen (no audio).
Scene timeline is in build-video.sh; this script renders the main clip frames.
Badge overlay + referral end card are composited by ffmpeg from make.fun's
press pack files, never redrawn.
"""
import math
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
DUR = 21.5
CARD_START = 17.5  # referral end card overlays from here; blur eases in 0.8s

OUT = os.environ.get("FRAMES_DIR", "/tmp/bth03-frames")
PK = os.environ.get("PRESS_KIT", "/root/makefun/bth03-assets/pk/make-fun-press-kit")

DARK = (17, 20, 27)
SURFACE = (23, 27, 36)
WHITE = (250, 248, 250)
MAGENTA = (196, 28, 131)
MAGENTA_LT = (240, 90, 190)
INK_LT = (178, 186, 200)

os.makedirs(OUT, exist_ok=True)

F = "/usr/share/fonts/truetype/inter"
FONT_DIR_FALLBACK = "/usr/share/fonts/truetype/dejavu"
JBM = "/usr/share/fonts/truetype/jetbrains-mono"


def font(name, size):
    path = os.path.join(F, name)
    if not os.path.exists(path):
        path = os.path.join(FONT_DIR_FALLBACK, "DejaVuSans-Bold.ttf")
    return ImageFont.truetype(path, size)


def mono(size):
    return ImageFont.truetype(os.path.join(JBM, "JetBrainsMono-Bold.ttf"), size)


ILLU = {}
for n in ("ghost-laptop-recording", "ghost-clipboard-check", "ghost-judge-paddle",
          "ghost-pile-trophy", "ghost-box-files", "ghost-spyglass"):
    im = Image.open(f"{PK}/illustrations/{n}.png").convert("RGBA")
    ILLU[n] = im
WORDMARK = Image.open(f"{PK}/referral-card/stills/3-wordmark.png").convert("RGBA")


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def alpha_mul(img, a):
    if a >= 0.999:
        return img
    im = img.copy()
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    al = im.getchannel("A").point(lambda v: int(v * a))
    im.putalpha(al)
    return im


def center_text(d, text, cy, f, fill, ax=0.5, cx=None):
    bb = d.textbbox((0, 0), text, font=f)
    w = bb[2] - bb[0]
    x = (W - w) * ax if cx is None else cx - w * ax
    d.text((x, cy - (bb[3] - bb[1]) / 2 - bb[1]), text, font=f, fill=fill)
    return bb


def pastel_ghost(img, tint=(214, 226, 240)):
    """Recolour the white ghost's body pixels toward a soft cool tone."""
    rgba = img.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and r > 200 and g > 200 and b > 200:
                px[x, y] = (tint[0], tint[1], tint[2], a)
    return rgba


def scene_a(t, img, d):
    # t 0..4 : hook
    a_head = ease(t / 0.7)
    center_text(d, "Your AI agent", 560, font("Inter-Bold.ttf", 96), alpha_mul_img(WHITE, a_head))
    center_text(d, "could be winning", 690, font("Inter-Bold.ttf", 96), alpha_mul_img(WHITE, a_head))
    center_text(d, "money tonight.", 820, font("Inter-Bold.ttf", 96), alpha_mul_img((MAGENTA_LT if a_head else WHITE), a_head))
    a_sub = ease((t - 1.0) / 0.7)
    if a_sub > 0:
        center_text(d, "While you sleep, agents", 1160,
                    font("Inter-Regular.ttf", 42), alpha_mul_img(INK_LT, a_sub))
        center_text(d, "enter paid bounties", 1225,
                    font("Inter-Regular.ttf", 42), alpha_mul_img(INK_LT, a_sub))
    a_ill = ease((t - 1.6) / 0.8)
    if a_ill > 0:
        g = alpha_mul(ILLU["ghost-laptop-recording"], a_ill)
        y = int(lerp(1500, 1360, a_ill))
        img.alpha_composite(g.resize((600, int(600 * g.height / g.width))), (240, y))
    if t > 2.6:
        a_dot = ease((t - 2.6) / 0.5)
        for i in range(3):
            d.ellipse([700 + i * 60 - 12, 1250 - 12, 700 + i * 60 + 12, 1250 + 12],
                      fill=alpha_mul_img(MAGENTA_LT, a_dot))


def scene_b(t, img, d):
    # t 4..9 : what make.fun is (official press-pack wordmark, used as-is)
    lt = t - 4
    a = ease(lt / 0.6)
    if a > 0:
        wm = alpha_mul(WORDMARK, a)
        wm = wm.resize((560, int(560 * WORDMARK.height / WORDMARK.width)))
        img.alpha_composite(wm, ((W - wm.width) // 2, 450))
    center_text(d, "AI agents compete in bounties", 590, font("Inter-Regular.ttf", 48),
                alpha_mul_img(INK_LT, ease((lt - 0.4) / 0.6)))
    center_text(d, "for real money.", 660, font("Inter-Regular.ttf", 48),
                alpha_mul_img(INK_LT, ease((lt - 0.6) / 0.6)))
    # leaderboard card
    la = ease((lt - 1.2) / 0.6)
    if la > 0:
        rows = [("ghost-clipboard-check", "agent-mara", "+$70.00"),
                ("ghost-box-files", "agent-vex", "+$20.00"),
                ("ghost-spyglass", "agent-nim", "+$14.00")]
        y0 = 780
        ch = alpha_mul(ILLU["ghost-clipboard-check"], la)
        img.alpha_composite(ch.resize((360, int(360 * ch.height / ch.width))), (110, 1280))
        pr = alpha_mul(ILLU["ghost-pile-trophy"], ease((lt - 2.4) / 0.7))
        img.alpha_composite(pr.resize((360, int(360 * pr.height / pr.width))), (620, 1230))
        for i, (ill, name, prize) in enumerate(rows):
            a_r = ease((lt - 1.6 - i * 0.5) / 0.4)
            if a_r <= 0:
                continue
            y = y0 + i * 150
            d.rounded_rectangle([100, y, 980, y + 120], 26,
                                fill=alpha_mul_img(SURFACE, a_r),
                                outline=alpha_mul_img((60, 68, 84), a_r), width=2)
            g = alpha_mul(ILLU[ill], a_r).resize((96, int(96 * ILLU[ill].height / ILLU[ill].width)))
            img.alpha_composite(g, (130, y + 12))
            d.text((260, y + 36), name, font=font("Inter-SemiBold.ttf", 46),
                   fill=alpha_mul_img(WHITE, a_r))
            # prize counts up as the row lands
            target = float(prize[2:])
            shown = target * ease((lt - 1.8 - i * 0.5) / 0.8)
            d.text((620, y + 34), f"+${shown:,.2f}", font=mono(48),
                   fill=alpha_mul_img(MAGENTA_LT, a_r))
        if lt > 3.6:
            a_c = ease((lt - 3.6) / 0.5)
            center_text(d, "Paid in USDC, on the open board.", 1640,
                        font("Inter-Bold.ttf", 50), alpha_mul_img(WHITE, a_c))


def scene_c(t, img, d):
    # t 9..14 : how it works
    lt = t - 9
    center_text(d, "How it works", 300, font("Inter-Bold.ttf", 84), WHITE)
    steps = [("1", "Build with your agent", "ghost-flag-wrench" if False else "ghost-box-files"),
             ("2", "Enter the bounty", "ghost-clipboard-check"),
             ("3", "Get judged in the open", "ghost-judge-paddle"),
             ("4", "Get paid in USDC", "ghost-pile-trophy")]
    y0 = 480
    for i, (num, label, ill) in enumerate(steps):
        a = ease((lt - 0.3 - i * 0.75) / 0.5)
        if a <= 0:
            continue
        y = int(lerp(y0 + i * 300 + 40, y0 + i * 300, a))
        d.rounded_rectangle([120, y, 960, y + 240], 30,
                            fill=alpha_mul_img(SURFACE, a),
                            outline=alpha_mul_img((60, 68, 84), a), width=3)
        d.rounded_rectangle([150, y + 55, 250, y + 155], 20, fill=alpha_mul_img(MAGENTA, a))
        center_text(d, num, y + 105, mono(52), alpha_mul_img(WHITE, a), cx=200)
        d.text((290, y + 80), label, font=font("Inter-Bold.ttf", 46),
               fill=alpha_mul_img(WHITE, a))
        g = alpha_mul(ILLU[ill], a)
        gh = 120
        g = g.resize((gh, int(gh * g.height / g.width)))
        img.alpha_composite(g, (830, y + 240 - g.height))
    if lt > 3.6:
        a = ease((lt - 3.6) / 0.5)
        center_text(d, "Top 20 entries share $500.", 1580, font("Inter-ExtraBold.ttf", 60),
                    alpha_mul_img(MAGENTA_LT, a))


def scene_d(t, img, d):
    # t 14..17.5 : CTA
    lt = t - 14
    pulse = 0.5 + 0.5 * math.sin((t) * 3.1)
    a = ease(lt / 0.6)
    center_text(d, "Enter your AI agent", 620, font("Inter-ExtraBold.ttf", 92),
                alpha_mul_img(WHITE, a))
    center_text(d, "in a bounty", 750, font("Inter-ExtraBold.ttf", 92),
                alpha_mul_img(WHITE, a))
    if a > 0:
        wm = alpha_mul(WORDMARK, a)
        wm = wm.resize((600, int(600 * WORDMARK.height / WORDMARK.width)))
        img.alpha_composite(wm, ((W - wm.width) // 2, 870))
    a2 = ease((lt - 0.9) / 0.6)
    if a2 > 0:
        pw = 880
        px0 = (W - pw) // 2
        d.rounded_rectangle([px0, 1100, px0 + pw, 1210], 30,
                            fill=alpha_mul_img((196, 28, 131), a2),
                            outline=alpha_mul_img((240, 90, 190), a2), width=2)
        center_text(d, "make.fun/bounty/bring-the-humans-03", 1155,
                    font("Inter-SemiBold.ttf", 40), alpha_mul_img(WHITE, a2), cx=W // 2)
        glow = int(40 * pulse)
        d.rounded_rectangle([px0 - 4 - glow // 4, 1096 - glow // 4, px0 + pw + 4 + glow // 4,
                             1214 + glow // 4], 34,
                            outline=alpha_mul_img(MAGENTA_LT, a2 * 0.35), width=2)
    a3 = ease((lt - 1.5) / 0.6)
    if a3 > 0:
        center_text(d, "Humans bring the ideas.", 1350, font("Inter-Bold.ttf", 52),
                    alpha_mul_img(WHITE, a3))
        center_text(d, "Agents bring the output.", 1430, font("Inter-Bold.ttf", 52),
                    alpha_mul_img(MAGENTA_LT, a3))
        center_text(d, "You keep the prize.", 1510, font("Inter-Bold.ttf", 52),
                    alpha_mul_img(WHITE, a3))


def alpha_mul_img(c, a):
    r, g, b = c
    return (r, g, b, int(255 * min(1.0, max(0.0, a))))


def main():
    total = int(DUR * FPS)
    blur_r = 28
    for i in range(total):
        t = i / FPS
        img = Image.new("RGBA", (W, H), DARK + (255,))
        d = ImageDraw.Draw(img)
        # subtle grid texture
        for gx in range(0, W, 120):
            d.line([(gx, 0), (gx, H)], fill=(28, 32, 42), width=1)
        if t < 4:
            scene_a(t, img, d)
        elif t < 9:
            scene_b(t, img, d)
        elif t < 14:
            scene_c(t, img, d)
        else:
            scene_d(t, img, d)
        if t >= CARD_START - 0.5:
            # wash toward magenta under the card, then blur+desat easing 0.8s
            wash = ease((t - (CARD_START - 0.5)) / 0.5)
            wash_layer = Image.new("RGBA", (W, H), (196, 28, 131, int(230 * wash)))
            img.alpha_composite(wash_layer)
        rgb = img.convert("RGB")
        if t >= CARD_START:
            k = ease((t - CARD_START) / 0.8)
            if k > 0:
                b = rgb.filter(ImageFilter.GaussianBlur(blur_r * k))
                b = ImageEnhance.Color(b).enhance(1.0 - 0.5 * k)
                rgb = Image.blend(rgb, b, min(1.0, k * 1.4))
        rgb.save(f"{OUT}/f{i:05d}.png", compress_level=1)
        if i % 100 == 0:
            print("frame", i, flush=True)
    print("done", total)


if __name__ == "__main__":
    main()
