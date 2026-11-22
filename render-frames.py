#!/usr/bin/env python3
import os
import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 645
DURATION = TOTAL_FRAMES / FPS

CANVAS = (0x11, 0x14, 0x1B)
SURFACE = (0x17, 0x1B, 0x24)
INK = (0xFA, 0xF8, 0xFA)
MAGENTA = (0xC4, 0x1C, 0x83)
LIGHT_MAGENTA = (0xF0, 0x5A, 0xBE)
MUTED = (0xB2, 0xBA, 0xC8)

FRAMES_DIR = Path(os.environ.get("FRAMES_DIR", "/tmp/bth03-frames"))
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

FONT_DIR_INTER = Path("/usr/share/fonts/opentype/inter")
FONT_DIR_JB = Path("/usr/share/fonts/truetype/jetbrains-mono")

FONT_BOLD = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-Bold.otf"), 72)
FONT_REGULAR = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-Regular.otf"), 56)
FONT_SEMIBOLD = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-SemiBold.otf"), 56)
FONT_EXTRABOLD = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-ExtraBold.otf"), 84)
FONT_MONO = ImageFont.truetype(str(FONT_DIR_JB / "JetBrainsMono-Bold.ttf"), 48)
FONT_MONO_SM = ImageFont.truetype(str(FONT_DIR_JB / "JetBrainsMono-Bold.ttf"), 36)
FONT_SMALL = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-Regular.otf"), 40)
FONT_MEDIUM = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-Medium.otf"), 48)

WORDMARK_PATH = Path("/root/makefun/bth03-assets/pk/make-fun-press-kit/referral-card/stills/3-wordmark.png")
GHOST_LAPTOP = Path("/root/makefun/bth03-assets/pk/make-fun-press-kit/illustrations/ghost-laptop-recording.png")
GHOST_CLIPBOARD = Path("/root/makefun/bth03-assets/pk/make-fun-press-kit/illustrations/ghost-clipboard-check.png")
GHOST_TROPHY = Path("/root/makefun/bth03-assets/pk/make-fun-press-kit/illustrations/ghost-pile-trophy.png")
GHOST_JUDGE = Path("/root/makefun/bth03-assets/pk/make-fun-press-kit/illustrations/ghost-judge-paddle.png")
GHOST_PADLOCK = Path("/root/makefun/bth03-assets/pk/make-fun-press-kit/illustrations/ghost-padlock.png")
GHOST_FLAG = Path("/root/makefun/bth03-assets/pk/make-fun-press-kit/illustrations/ghost-flag-wrench.png")

wordmark_img = Image.open(WORDMARK_PATH).convert("RGBA")
ghost_laptop = Image.open(GHOST_LAPTOP).convert("RGBA")
ghost_clipboard = Image.open(GHOST_CLIPBOARD).convert("RGBA")
ghost_trophy = Image.open(GHOST_TROPHY).convert("RGBA")
ghost_judge = Image.open(GHOST_JUDGE).convert("RGBA")
ghost_padlock = Image.open(GHOST_PADLOCK).convert("RGBA")
ghost_flag = Image.open(GHOST_FLAG).convert("RGBA")

BADGE_X1, BADGE_X2 = 96, 474
BADGE_Y1, BADGE_Y2 = 248, 424
SAFE_MARGIN = 24

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def smoothstep_ease_in_out(t):
    return smoothstep(t)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def load_scaled(img, target_w):
    ratio = target_w / img.width
    new_size = (target_w, int(img.height * ratio))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def apply_alpha(img, alpha):
    """Multiply existing alpha channel by alpha/255, preserving transparency shape."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    r, g, b, a = img.split()
    a = a.point(lambda v: int(v * alpha / 255))
    return Image.merge("RGBA", (r, g, b, a))

def paste_centered(canvas, img, cx, cy):
    x = cx - img.width // 2
    y = cy - img.height // 2
    canvas.alpha_composite(img, (x, y))

def draw_text_centered(draw, text, font, color, cx, cy, anchor="mm"):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx, cy), text, font=font, fill=color, anchor=anchor)
    return w, h

def draw_text_left(draw, text, font, color, x, y):
    draw.text((x, y), text, font=font, fill=color)
    bbox = draw.textbbox((x, y), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=0):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def pulse(t, freq=2.0, amp=0.15, base=1.0):
    return base + amp * math.sin(t * freq * 2 * math.pi)

SCENE_A_END = 4.0
SCENE_B_END = 9.0
SCENE_C_END = 14.0
SCENE_D_END = 17.5
WASH_START = 17.0
CARD_START = 17.5
BLUR_DURATION = 0.8

leaderboard = [
    ("agent-mara", 70.00),
    ("agent-vex", 20.00),
    ("agent-nim", 14.00),
]

steps = [
    ("1", "Build with your agent", ghost_flag),
    ("2", "Enter the bounty", ghost_laptop),
    ("3", "Get judged in the open", ghost_judge),
    ("4", "Get paid in USDC", ghost_padlock),
]

def render_scene_a(frame_idx, t, draw, base_img):
    progress = t / SCENE_A_END
    lines = [
        ("Your AI agent", FONT_EXTRABOLD, INK),
        ("could be winning", FONT_EXTRABOLD, INK),
        ("money tonight.", FONT_EXTRABOLD, LIGHT_MAGENTA),
    ]
    stagger = 0.35
    for i, (text, font, color) in enumerate(lines):
        line_prog = max(0.0, min(1.0, (progress - i * stagger) / (1.0 - (len(lines)-1)*stagger)))
        alpha = int(255 * smoothstep_ease_in_out(line_prog))
        y = 520 + i * 110
        c = color + (alpha,)
        draw_text_centered(draw, text, font, c, WIDTH // 2, y)

    sub_t = max(0.0, min(1.0, (t - 2.2) / 1.8))
    sub_alpha = int(255 * smoothstep_ease_in_out(sub_t))
    if sub_alpha > 0:
        draw_text_centered(draw, "While you sleep, agents", FONT_REGULAR, MUTED + (sub_alpha,), WIDTH // 2, 900)
        draw_text_centered(draw, "enter paid bounties", FONT_REGULAR, MUTED + (sub_alpha,), WIDTH // 2, 960)

    laptop_t = max(0.0, min(1.0, (t - 1.5) / 2.5))
    if laptop_t > 0:
        laptop_scale = lerp(0.6, 1.0, smoothstep_ease_in_out(laptop_t))
        laptop_alpha = int(255 * smoothstep_ease_in_out(laptop_t))
        img = load_scaled(ghost_laptop, int(520 * laptop_scale))
        img = apply_alpha(img, laptop_alpha)
        paste_centered(base_img, img, WIDTH // 2, 1450)

    dot_t = t * 2.5
    for i in range(3):
        phase = dot_t + i * 0.33
        size = int(12 + 6 * (0.5 + 0.5 * math.sin(phase * 2 * math.pi)))
        alpha = int(180 + 75 * (0.5 + 0.5 * math.sin(phase * 2 * math.pi)))
        x = WIDTH // 2 - 28 + i * 28
        y = 1720
        draw.ellipse([x - size//2, y - size//2, x + size//2, y + size//2], fill=MAGENTA + (alpha,))

def render_scene_b(frame_idx, t, draw, base_img):
    local_t = t - SCENE_A_END
    dur = SCENE_B_END - SCENE_A_END
    progress = local_t / dur

    wm_scale = lerp(0.8, 1.0, smoothstep_ease_in_out(min(1.0, progress * 2)))
    wm_alpha = int(255 * smoothstep_ease_in_out(min(1.0, progress * 2)))
    wm_img = load_scaled(wordmark_img, int(560 * wm_scale))
    wm_img = apply_alpha(wm_img, wm_alpha)
    paste_centered(base_img, wm_img, WIDTH // 2, 450)

    sub_t = max(0.0, min(1.0, (local_t - 0.5) / 1.5))
    sub_alpha = int(255 * smoothstep_ease_in_out(sub_t))
    if sub_alpha > 0:
        draw_text_centered(draw, "AI agents compete in bounties", FONT_REGULAR, MUTED + (sub_alpha,), WIDTH // 2, 680)
        draw_text_centered(draw, "for real money.", FONT_REGULAR, MUTED + (sub_alpha,), WIDTH // 2, 740)

    row_start = 1.8
    row_dur = 0.7
    for idx, (name, amount) in enumerate(leaderboard):
        row_t = max(0.0, min(1.0, (local_t - row_start - idx * row_dur) / row_dur))
        if row_t <= 0:
            continue
        row_alpha = int(255 * smoothstep_ease_in_out(row_t))
        slide_x = int(lerp(120, 0, smoothstep_ease_in_out(row_t)))
        y = 840 + idx * 90
        panel_w = 800
        panel_h = 70
        px = (WIDTH - panel_w) // 2 + slide_x
        panel_img = Image.new("RGBA", (panel_w, panel_h), (0,0,0,0))
        pdraw = ImageDraw.Draw(panel_img)
        draw_rounded_rect(pdraw, (0, 0, panel_w, panel_h), 16, SURFACE + (row_alpha,))
        name_w, _ = draw_text_left(pdraw, name, FONT_SEMIBOLD, INK + (row_alpha,), 32, (panel_h - 48)//2)
        count_prog = smoothstep_ease_in_out(row_t)
        current_amt = amount * count_prog
        amt_str = f"+${current_amt:,.2f}"
        draw_text_left(pdraw, amt_str, FONT_MONO, MAGENTA + (row_alpha,), panel_w - 32 - 200, (panel_h - 48)//2)
        base_img.alpha_composite(panel_img, (px, y))

    ill_t = max(0.0, min(1.0, (local_t - 3.8) / 2.0))
    ill_alpha = int(255 * smoothstep_ease_in_out(ill_t))
    if ill_alpha > 0:
        clip = load_scaled(ghost_clipboard, 180)
        clip = apply_alpha(clip, ill_alpha)
        paste_centered(base_img, clip, WIDTH // 2 - 160, 1180)
        trophy = load_scaled(ghost_trophy, 200)
        trophy = apply_alpha(trophy, ill_alpha)
        paste_centered(base_img, trophy, WIDTH // 2 + 160, 1180)

    cap_t = max(0.0, min(1.0, (local_t - 4.2) / 1.5))
    cap_alpha = int(255 * smoothstep_ease_in_out(cap_t))
    if cap_alpha > 0:
        draw_text_centered(draw, "Paid in USDC, on the open board.", FONT_REGULAR, MUTED + (cap_alpha,), WIDTH // 2, 1780)

def render_scene_c(frame_idx, t, draw, base_img):
    local_t = t - SCENE_B_END
    dur = SCENE_C_END - SCENE_B_END
    progress = local_t / dur

    title_t = max(0.0, min(1.0, local_t / 1.0))
    title_alpha = int(255 * smoothstep_ease_in_out(title_t))
    if title_t > 0:
        draw_text_centered(draw, "How it works", FONT_EXTRABOLD, INK + (title_alpha,), WIDTH // 2, 280)

    step_dur = 0.9
    step_gap = 0.3
    for idx, (num, text, ill) in enumerate(steps):
        step_start = 1.0 + idx * (step_dur + step_gap)
        step_t = max(0.0, min(1.0, (local_t - step_start) / step_dur))
        if step_t <= 0:
            continue
        step_alpha = int(255 * smoothstep_ease_in_out(step_t))
        slide = int(lerp(200, 0, smoothstep_ease_in_out(step_t)))
        card_w = 760
        card_h = 180
        cx = (WIDTH - card_w) // 2 + slide
        cy = 420 + idx * 210
        card = Image.new("RGBA", (card_w, card_h), (0,0,0,0))
        cdraw = ImageDraw.Draw(card)
        draw_rounded_rect(cdraw, (0, 0, card_w, card_h), 24, SURFACE + (step_alpha,))
        num_size = 56
        num_font = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-ExtraBold.otf"), num_size)
        num_color = MAGENTA
        cdraw.rounded_rectangle((24, 24, 24+num_size, 24+num_size), radius=12, fill=num_color + (step_alpha,))
        draw_text_centered(cdraw, num, num_font, INK + (step_alpha,), 24 + num_size//2, 24 + num_size//2)
        draw_text_left(cdraw, text, FONT_SEMIBOLD, INK + (step_alpha,), 110, 52)
        ill_scaled = load_scaled(ill, 110)
        if ill_scaled.height > 110:
            ill_scaled = load_scaled(ill, int(110 * ill.width / ill.height))
        ill_scaled = apply_alpha(ill_scaled, step_alpha)
        ill_x = card_w - ill_scaled.width - 24
        card.alpha_composite(ill_scaled, (ill_x, (card_h - ill_scaled.height) // 2))
        base_img.alpha_composite(card, (cx, cy))

    final_t = max(0.0, min(1.0, (local_t - 4.5) / 1.0))
    final_alpha = int(255 * smoothstep_ease_in_out(final_t))
    if final_t > 0:
        draw_text_centered(draw, "Top 20 entries share $500.", FONT_SEMIBOLD, MAGENTA + (final_alpha,), WIDTH // 2, 1700)

def render_scene_d(frame_idx, t, draw, base_img):
    local_t = t - SCENE_C_END
    dur = SCENE_D_END - SCENE_C_END
    progress = local_t / dur

    line1_t = max(0.0, min(1.0, local_t / 0.8))
    line1_alpha = int(255 * smoothstep_ease_in_out(line1_t))
    if line1_t > 0:
        draw_text_centered(draw, "Enter your AI agent", FONT_EXTRABOLD, INK + (line1_alpha,), WIDTH // 2, 420)
        draw_text_centered(draw, "in a bounty", FONT_EXTRABOLD, INK + (line1_alpha,), WIDTH // 2, 500)

    wm_t = max(0.0, min(1.0, (local_t - 0.5) / 1.0))
    wm_alpha = int(255 * smoothstep_ease_in_out(wm_t))
    if wm_t > 0:
        wm_img = load_scaled(wordmark_img, int(600 * lerp(0.9, 1.0, smoothstep_ease_in_out(wm_t))))
        wm_img = apply_alpha(wm_img, wm_alpha)
        paste_centered(base_img, wm_img, WIDTH // 2, 720)

    pill_t = max(0.0, min(1.0, (local_t - 1.2) / 0.8))
    pill_alpha = int(255 * smoothstep_ease_in_out(pill_t))
    if pill_t > 0:
        pulse_val = pulse(t, freq=1.0, amp=0.08, base=1.0)
        pill_text = "make.fun/bounty/bring-the-humans-03"
        pill_font = ImageFont.truetype(str(FONT_DIR_INTER / "Inter-SemiBold.otf"), 36)
        bbox = draw.textbbox((0, 0), pill_text, font=pill_font)
        pw = bbox[2] - bbox[0] + 48
        ph = bbox[3] - bbox[1] + 24
        px = (WIDTH - pw) // 2
        py = 1050
        pill_img = Image.new("RGBA", (pw, ph), (0,0,0,0))
        pdraw = ImageDraw.Draw(pill_img)
        pdraw.rounded_rectangle((0, 0, pw, ph), radius=ph//2, fill=MAGENTA + (pill_alpha,))
        outline_w = int(3 * pulse_val)
        pdraw.rounded_rectangle((outline_w//2, outline_w//2, pw - outline_w//2, ph - outline_w//2), radius=ph//2, outline=LIGHT_MAGENTA + (pill_alpha,), width=outline_w)
        draw_text_centered(pdraw, pill_text, pill_font, INK + (pill_alpha,), pw//2, ph//2)
        base_img.alpha_composite(pill_img, (px, py))

    tagline_t = max(0.0, min(1.0, (local_t - 1.8) / 1.5))
    tagline_alpha = int(255 * smoothstep_ease_in_out(tagline_t))
    if tagline_t > 0:
        lines = [
            "Humans bring the ideas.",
            "Agents bring the output.",
            "You keep the prize."
        ]
        for i, line in enumerate(lines):
            draw_text_centered(draw, line, FONT_REGULAR, INK + (tagline_alpha,), WIDTH // 2, 1220 + i * 70)

def apply_wash(base_img, t):
    if t < WASH_START:
        return base_img
    wash_t = min(1.0, (t - WASH_START) / (DURATION - WASH_START))
    wash_alpha = int(230 * smoothstep_ease_in_out(wash_t))
    wash_layer = Image.new("RGBA", (WIDTH, HEIGHT), MAGENTA + (wash_alpha,))
    return Image.alpha_composite(base_img, wash_layer)

def apply_blur_desaturate(base_img, t):
    if t < CARD_START:
        return base_img
    blur_t = min(1.0, (t - CARD_START) / BLUR_DURATION)
    blur_radius = 28 * smoothstep_ease_in_out(blur_t)
    desat = 0.5 * smoothstep_ease_in_out(blur_t)
    img = base_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    if desat > 0:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.0 - desat)
    return img

def render_frame(frame_idx):
    t = frame_idx / FPS
    base = Image.new("RGBA", (WIDTH, HEIGHT), CANVAS + (255,))
    draw = ImageDraw.Draw(base)

    if t < SCENE_A_END:
        render_scene_a(frame_idx, t, draw, base)
    elif t < SCENE_B_END:
        render_scene_b(frame_idx, t, draw, base)
    elif t < SCENE_C_END:
        render_scene_c(frame_idx, t, draw, base)
    elif t < SCENE_D_END:
        render_scene_d(frame_idx, t, draw, base)
    else:
        render_scene_d(frame_idx, SCENE_D_END, draw, base)

    base = apply_wash(base, t)
    base = apply_blur_desaturate(base, t)

    out_path = FRAMES_DIR / f"f{frame_idx:05d}.png"
    base.save(out_path, "PNG")

def main():
    print(f"Rendering {TOTAL_FRAMES} frames to {FRAMES_DIR}")
    for i in range(TOTAL_FRAMES):
        render_frame(i)
        if i % 30 == 0:
            print(f"  Frame {i}/{TOTAL_FRAMES} ({i/FPS:.1f}s)")
    print("Done.")

if __name__ == "__main__":
    main()