#!/usr/bin/env python3
"""Raster favicons and Open Graph cards from the self-hosted fonts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "site" / "fonts"
IMG = ROOT / "site" / "img"

BG = (11, 12, 15)
TEXT = (244, 240, 230)
MUTED = (196, 187, 170)
GOLD = (230, 201, 138)
INK = (22, 20, 15)


def ttf(woff_name: str) -> str:
    dest = Path(tempfile.gettempdir()) / (woff_name + ".ttf")
    if not dest.exists():
        font = TTFont(FONT_DIR / woff_name)
        font.flavor = None
        font.save(dest)
    return str(dest)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(ttf(name), size)


def stars(draw: ImageDraw.ImageDraw, ox: int, oy: int, scale: float = 1.0) -> None:
    def c(x, y, r, fill):
        x, y, r = ox + x * scale, oy + y * scale, r * scale
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    c(12.5, 21, 5.4, TEXT)
    c(25, 12.5, 3.15, GOLD)


def og(lang: str, headline: list[str], tagline: str, face: str, size: int) -> None:
    image = Image.new("RGB", (1200, 630), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1200, 6), fill=GOLD)
    stars(draw, 72, 64, 1.7)
    draw.text((150, 78), "STARCONOMY", font=font("ibm-plex-sans-500.woff2", 28), fill=GOLD)
    y = 210
    face_font = font(face, size)
    for line in headline:
        draw.text((72, y), line, font=face_font, fill=TEXT)
        y += int(size * 1.18)
    draw.rectangle((72, y + 28, 128, y + 30), fill=GOLD)
    draw.text((144, y + 10), tagline, font=font(face.replace("500", "400"), 32), fill=MUTED)
    legal = font("noto-sans-tc-400.woff2", 26)
    draw.text((72, 560), "渼科星聯科技有限公司", font=legal, fill=TEXT)
    draw.text((430, 562), "·  Taipei  ·  starconomy.com", font=font("ibm-plex-sans-400.woff2", 24), fill=MUTED)
    path = IMG / f"og-{lang}.png"
    image.save(path, "PNG", optimize=True)
    print(path, path.stat().st_size)


def icons() -> None:
    for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):
        image = Image.new("RGB", (size, size), BG)
        draw = ImageDraw.Draw(image)
        scale = size / 36
        stars(draw, size * 0.08, size * 0.08, scale)
        path = ROOT / "site" / name
        image.save(path, "PNG", optimize=True)
        print(path, path.stat().st_size)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    og("en", ["Two builds.", "One truth."], "Verifiable by design.", "ibm-plex-sans-500.woff2", 84)
    og("ja", ["二つのビルド、", "ひとつの真実。"], "検証できる信頼を。", "noto-sans-jp-500.woff2", 64)
    og("zh", ["兩次建置，", "一個真相。"], "看得見的信任。", "noto-sans-tc-500.woff2", 72)
    icons()


if __name__ == "__main__":
    main()
