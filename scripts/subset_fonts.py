#!/usr/bin/env python3
"""Build self-hosted woff2 files covering every character the site renders.

IBM Plex files are copied from a local download cache when present, or fetched
from the fontsource CDN once, at build time for the fonts — never at page view.
Noto Sans TC and JP are subset through the Google Fonts CSS API so U+6E3C (渼)
and the rest of the copy are real glyphs, not tofu.
"""

from __future__ import annotations

import html
import re
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
FONT_DIR = SITE / "fonts"
CACHE = Path("/tmp/fontsrc")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

PLEX = {
    "ibm-plex-sans-400.woff2": "https://cdn.jsdelivr.net/fontsource/fonts/ibm-plex-sans@5.2.6/latin-400-normal.woff2",
    "ibm-plex-sans-500.woff2": "https://cdn.jsdelivr.net/fontsource/fonts/ibm-plex-sans@5.2.6/latin-500-normal.woff2",
    "ibm-plex-mono-400.woff2": "https://cdn.jsdelivr.net/fontsource/fonts/ibm-plex-mono@5.2.6/latin-400-normal.woff2",
}

EXTRA = set("渼科星聯科技有限公司雙星繁體中文日本語・—–")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def page_chars(path: Path) -> set[str]:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return set(html.unescape(raw))


def non_latin(chars: set[str]) -> str:
    keep = []
    for ch in sorted(chars):
        code = ord(ch)
        if code < 32 or ch.isspace():
            continue
        # Latin, digits, and the punctuation already in IBM Plex can stay out.
        if code < 0x250:
            continue
        keep.append(ch)
    return "".join(keep)


def css_faces(css: str) -> list[tuple[str, str]]:
    faces = []
    for block in css.split("@font-face")[1:]:
        weight = re.search(r"font-weight:\s*(\d+)", block)
        src = re.search(r"url\(([^)]+)\)", block)
        if weight and src:
            faces.append((weight.group(1), src.group(1).strip("\"'")))
    return faces


def download_subset(family: str, text: str, dest_prefix: str) -> None:
    from urllib.parse import quote
    from fontTools.ttLib import TTFont
    import io

    needed = {ord(ch) for ch in text}
    for weight in ("400", "500"):
        url = (
            "https://fonts.googleapis.com/css2?family="
            + quote(family)
            + f":wght@{weight}&display=swap&text="
            + quote(text)
        )
        css = fetch(url).decode("utf-8")
        faces = css_faces(css)
        if len(faces) != 1:
            raise SystemExit(f"unexpected CSS for {family} {weight}: {css[:400]}")
        blob = fetch(faces[0][1])
        font = TTFont(io.BytesIO(blob))
        cmap = set((font.getBestCmap() or {}))
        missing = sorted(needed - cmap)
        if missing:
            preview = "".join(chr(cp) for cp in missing[:30])
            raise SystemExit(f"{family} {weight} missing {len(missing)} characters: {preview}")
        mei = ord("渼")
        glyph = font.getBestCmap()[mei]
        contours = font["glyf"][glyph].numberOfContours
        if contours <= 0:
            raise SystemExit(f"{family} {weight} has an empty glyph for 渼")
        out = FONT_DIR / f"{dest_prefix}-{weight}.woff2"
        out.write_bytes(blob)
        print(f"wrote {out.name} ({len(blob)} bytes, {len(cmap)} glyphs)")


def copy_plex() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, url in PLEX.items():
        cached = CACHE / name
        if not cached.exists():
            cached.write_bytes(fetch(url))
        target = FONT_DIR / name
        shutil.copyfile(cached, target)
        print(f"copied {name}")


def write_licenses() -> None:
    notice = """IBM Plex Sans and IBM Plex Mono
Copyright © 2017 IBM Corp.
Licensed under the SIL Open Font License, Version 1.1.

Noto Sans TC and Noto Sans JP
Copyright 2022 The Noto Project Authors
Licensed under the SIL Open Font License, Version 1.1.

The full license text is in OFL.txt. These files are subsets that contain
only the characters used on this site, including U+6E3C (渼).
"""
    (FONT_DIR / "COPYRIGHT.txt").write_text(notice, encoding="utf-8")
    ofl = FONT_DIR / "OFL.txt"
    if not ofl.exists():
        ofl.write_bytes(fetch("https://raw.githubusercontent.com/notofonts/latin-greek-cyrillic/main/OFL.txt"))
        print("wrote OFL.txt")


def main() -> int:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    en = page_chars(SITE / "index.html")
    ja = page_chars(SITE / "ja" / "index.html")
    zh = page_chars(SITE / "zh" / "index.html")
    # 404.html is self-contained and uses system fonts, so it is not subsetted.
    tc_text = non_latin(en | zh | EXTRA)
    jp_text = non_latin(ja | EXTRA)
    print(f"TC subset {len(tc_text)} chars, JP subset {len(jp_text)} chars")
    if "渼" not in tc_text or "渼" not in jp_text:
        raise SystemExit("渼 missing from subset text")
    copy_plex()
    download_subset("Noto Sans TC", tc_text, "noto-sans-tc")
    download_subset("Noto Sans JP", jp_text, "noto-sans-jp")
    write_licenses()
    return 0


if __name__ == "__main__":
    sys.exit(main())
