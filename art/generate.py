#!/usr/bin/env python3
"""Generate the Lunar Quest Omarchy wallpapers as SVG, then render them to PNG.

Follows the stock Omarchy wallpaper layout: 3840x2160, flat background, pixel
logo in the accent color, 1600px wide and centered.

    python3 art/generate.py
"""

import random
import re
import subprocess
from pathlib import Path

ART = Path(__file__).resolve().parent
BACKGROUNDS = ART.parent / "backgrounds"

W, H = 3840, 2160
LOGO_W, LOGO_H = 1215, 285
LOGO_SCALE = 1600 / LOGO_W

# Palette (colors.toml)
BACKGROUND = "#0a111d"
ACCENT = "#7ea3cf"
SELECTION = "#223855"
FOREGROUND = "#d3d1cf"
DARK_FOREGROUND = "#8f8c8d"
MUTED = "#757478"
BRIGHT_FOREGROUND = "#e8f0f8"
BRIGHT_BLUE = "#a7beda"
YELLOW = "#e0c48a"

# 5x7 pixel font for the subtitle, stepped like the Omarchy wordmark.
# "#" draws in the glyph color; "o" draws a crater (used by the moon Q).
FONT = {
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    # Q drawn as a cratered full moon with a tail dropping below the baseline.
    "Q": [".###.", "##o##", "#####", "###o#", "#o###", "#####", ".###.", "...##"],
    # The word gap holds a small four-point star.
    " ": [".....", ".....", "..*..", ".***.", "..*..", ".....", "....."],
}

# Pixel-art decorations scattered around the wordmark.
SPRITES = {
    "crescent": (FOREGROUND, [
        "..###.",
        ".###..",
        "###...",
        "###...",
        "###...",
        ".###..",
        "..###.",
    ]),
    "moon": (DARK_FOREGROUND, [
        "..###..",
        ".##o##.",
        "####o##",
        "#o#####",
        "####o##",
        ".#####.",
        "..###..",
    ]),
    "earth": (ACCENT, [
        "...##",
        "..#w#",
        ".##w.",
        ".#ww.",
        ".##w.",
        "..###",
        "...##",
    ]),
    "sparkle": (BRIGHT_FOREGROUND, [
        "..#..",
        "..#..",
        "##.##",
        "..#..",
        "..#..",
    ]),
    "star": (YELLOW, [
        ".#.",
        "###",
        ".#.",
    ]),
}

CRATER = {"moon": MUTED, "crescent": DARK_FOREGROUND}
HIGHLIGHT = {"earth": BRIGHT_FOREGROUND}


def logo_paths():
    svg = (ART / "omarchy-logo.svg").read_text()
    return re.search(r"<g[^>]*>(.*)</g>", svg, re.S).group(1)


def pixels(rows, x, y, size, color, extra=None):
    """Render a pixel grid as rects; `extra` maps glyph chars to other colors."""
    extra = extra or {}
    out = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            fill = color if ch == "#" else extra.get(ch, color)
            out.append(
                f'<rect x="{x + c * size:g}" y="{y + r * size:g}" '
                f'width="{size:g}" height="{size:g}" fill="{fill}"/>'
            )
    return out


def logo(y, scale=LOGO_SCALE, width=W):
    x = (width - LOGO_W * scale) / 2
    return (
        f'<g transform="translate({x:g} {y:g}) scale({scale:.6f})" '
        f'fill="{ACCENT}">{logo_paths()}</g>'
    )


SUBTITLE = "LUNAR QUEST"
SUBTITLE_ADVANCE = 7  # 5px glyph + 2px tracking


def subtitle_width(p):
    return (len(SUBTITLE) * SUBTITLE_ADVANCE - 2) * p


def subtitle(x, y, p):
    out = []
    for i, ch in enumerate(SUBTITLE):
        cx = x + i * SUBTITLE_ADVANCE * p
        if ch == " ":
            out += pixels(FONT[ch], cx, y, p, YELLOW, {"*": YELLOW})
        else:
            out += pixels(FONT[ch], cx, y, p, FOREGROUND, {"o": MUTED})
    return out


def document(body, width=W, height=H, background=BACKGROUND):
    fill = f'<rect width="{width}" height="{height}" fill="{background}"/>\n' if background else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">\n'
        + fill
        + "\n".join(body)
        + "\n</svg>\n"
    )


def plain():
    return document([logo((H - LOGO_H * LOGO_SCALE) / 2)])


def overlaps(box, boxes, margin):
    x, y, w, h = box
    return any(
        x < bx + bw + margin and bx < x + w + margin and
        y < by + bh + margin and by < y + h + margin
        for bx, by, bw, bh in boxes
    )


def lunar_quest():
    p = 16  # subtitle pixel size
    gap = 96

    logo_h = LOGO_H * LOGO_SCALE
    text_h = 7 * p
    top = (H - (logo_h + gap + text_h)) / 2
    text_y = top + logo_h + gap

    body = [logo(top)]
    body += subtitle((W - subtitle_width(p)) / 2, text_y, p)

    # Keep decorations clear of the wordmark block.
    blocked = [((W - 1600) / 2, top, 1600, logo_h + gap + text_h + 2 * p)]
    rng = random.Random(1972)  # Apollo 17, the last crewed lunar landing

    # Distant stars: single dim pixels.
    for _ in range(140):
        size = rng.choice([6, 6, 6, 9, 12])
        x, y = rng.randrange(0, W - size), rng.randrange(0, H - size)
        if overlaps((x, y, size, size), blocked, 40):
            continue
        color = rng.choice([BRIGHT_FOREGROUND, BRIGHT_BLUE, DARK_FOREGROUND, MUTED])
        opacity = rng.choice([0.35, 0.5, 0.7, 0.9])
        body.append(
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" '
            f'fill="{color}" opacity="{opacity}"/>'
        )

    # Larger sprites, each placed at a random free spot.
    placements = [
        ("moon", 20), ("crescent", 16), ("crescent", 12), ("earth", 18),
        ("sparkle", 14), ("sparkle", 10), ("sparkle", 10), ("sparkle", 8),
        ("star", 14), ("star", 12), ("star", 10), ("star", 10), ("star", 8),
    ]
    for name, size in placements:
        color, rows = SPRITES[name]
        w, h = len(rows[0]) * size, len(rows) * size
        for _ in range(500):
            x = rng.randrange(160, W - 160 - w)
            y = rng.randrange(140, H - 140 - h)
            if not overlaps((x, y, w, h), blocked, 140):
                break
        blocked.append((x, y, w, h))
        extra = {"o": CRATER.get(name, MUTED), "w": HIGHLIGHT.get(name, color)}
        body += pixels(rows, x, y, size, color, extra)

    return document(body)


# Plymouth/SDDM unlock mark: drawn at native size, centered, with the password
# field placed 40px below it. Stock marks are 800px wide on transparency.
UNLOCK_W = 800
UNLOCK_SCALE = UNLOCK_W / LOGO_W


def unlock():
    p = 8
    gap = 44
    margin = 8
    logo_h = LOGO_H * UNLOCK_SCALE
    text_y = margin + logo_h + gap
    height = round(text_y + 8 * p + margin)  # 8 rows: the moon Q's tail

    text_w = subtitle_width(p)
    text_x = (UNLOCK_W - text_w) / 2
    color, rows = SPRITES["sparkle"]
    sparkle_w = len(rows[0]) * 4
    sparkle_y = text_y + (7 * p - sparkle_w) / 2

    body = [logo(margin, UNLOCK_SCALE, UNLOCK_W)]
    body += subtitle(text_x, text_y, p)
    body += pixels(rows, text_x - 56 - sparkle_w, sparkle_y, 4, color)
    body += pixels(rows, text_x + text_w + 56, sparkle_y, 4, color)
    return document(body, UNLOCK_W, height, background=None), height


def render(svg, svg_name, png_path, width=W, height=H):
    svg_path = ART / svg_name
    svg_path.write_text(svg)
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(png_path), str(svg_path)],
        check=True,
    )
    print(f"{svg_path.relative_to(ART.parent)} -> {png_path.relative_to(ART.parent)}")


if __name__ == "__main__":
    render(plain(), "omarchy.svg", BACKGROUNDS / "omarchy.png")
    render(lunar_quest(), "omarchy-lunar-quest.svg", BACKGROUNDS / "0-omarchy-lunar-quest.png")
    # Theme picker preview, at the stock preview size.
    render(lunar_quest(), "omarchy-lunar-quest.svg", ART.parent / "preview.png", 1800, 1012)
    svg, height = unlock()
    render(svg, "unlock.svg", ART.parent / "unlock.png", UNLOCK_W, height)
