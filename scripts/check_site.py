#!/usr/bin/env python3
"""Static checks for the generated Starconomy site. No network."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

PAGES = {
    "en": SITE / "index.html",
    "ja": SITE / "ja" / "index.html",
    "zh": SITE / "zh" / "index.html",
}

REQUIRED = {
    "en": ["Two builds.", "One truth.", "Verifiable by design.", "hello@starconomy.com", "渼科星聯科技有限公司", "ArduPilot Copter 4.7.3", "CubeOrange", "Contact for pricing"],
    "ja": ["二つのビルド、ひとつの真実。", "検証できる信頼を。", "hello@starconomy.com", "渼科星聯科技有限公司", "ArduPilot Copter 4.7.3", "CubeOrange", "料金はお問い合わせください"],
    "zh": ["兩次建置，一個真相。", "看得見的信任。", "hello@starconomy.com", "渼科星聯科技有限公司", "ArduPilot Copter 4.7.3", "CubeOrange", "報價請來信"],
}

H1 = {
    "en": "Two builds.",
    "ja": "二つのビルド、ひとつの真実。",
    "zh": "兩次建置，一個真相。",
}

FORBIDDEN = [
    "googletagmanager",
    "google-analytics",
    "fonts.googleapis",
    "fonts.gstatic",
    "jsdelivr",
    "unpkg.com",
    "facebook.net",
    "doubleclick",
    "hotjar",
    "segment.com",
    "plausible",
    "cloudflareinsights",
    "gtag(",
    "<form",
    "cookie-banner",
]

# Currency / price signals. The tiers are deliberately unpriced.
PRICE = re.compile(r"(\$|€|£|¥|USD|NT\$|円|元／|價格為|料金は\s*[0-9])")

IDS = ["problem", "why", "method", "deliverables", "tiers", "proof", "about", "contact"]

TRACKER_HOST = re.compile(
    r"https?://(?!starconomy\.com)[^\"'\s>]+",
    re.I,
)


def visible_text(raw: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def cmap_of(path: Path) -> set[int]:
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    found: set[int] = set()
    for table in font["cmap"].tables:
        found.update(table.cmap.keys())
    return found


def main() -> int:
    errors: list[str] = []

    for lang, path in PAGES.items():
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        raw = path.read_text(encoding="utf-8")
        text = visible_text(raw)
        if raw.count("<h1") != 1:
            errors.append(f"{lang}: expected one h1, found {raw.count('<h1')}")
        if H1[lang] not in text:
            errors.append(f"{lang}: h1 copy missing")
        for needle in REQUIRED[lang]:
            if needle not in text and needle not in raw:
                errors.append(f"{lang}: missing {needle!r}")
        for bad in FORBIDDEN:
            if bad.lower() in raw.lower():
                errors.append(f"{lang}: forbidden markup {bad}")
        if PRICE.search(text):
            errors.append(f"{lang}: looks like a price: {PRICE.search(text).group(0)}")
        for anchor in IDS:
            if f'id="{anchor}"' not in raw:
                errors.append(f"{lang}: missing section #{anchor}")
        if 'rel="canonical"' not in raw:
            errors.append(f"{lang}: missing canonical")
        for hreflang in ("en", "ja", "zh-Hant", "x-default"):
            if f'hreflang="{hreflang}"' not in raw:
                errors.append(f"{lang}: missing hreflang {hreflang}")
        if "mailto:hello@starconomy.com" not in raw:
            errors.append(f"{lang}: missing mailto")
        # Asset links stay relative so project pages and the apex domain both work.
        for match in re.finditer(r'(?:href|src)="(/[^"]*)"', raw):
            errors.append(f"{lang}: root-absolute asset {match.group(1)}")
        external = [
            url
            for url in TRACKER_HOST.findall(raw)
            if not url.startswith("https://starconomy.com")
            and "schema.org" not in url
            and "w3.org" not in url
        ]
        # JSON-LD uses https://schema.org which the regex may catch via the negative lookahead only for starconomy.
        external = [url for url in external if "schema.org" not in url]
        if external:
            errors.append(f"{lang}: unexpected external URLs {external[:5]}")

    cname = (SITE / "CNAME").read_text(encoding="utf-8").strip()
    if cname != "starconomy.com":
        errors.append(f"CNAME is {cname!r}")
    if not (SITE / ".nojekyll").exists():
        errors.append("missing .nojekyll")
    for name in ("img/og-en.png", "img/og-ja.png", "img/og-zh.png", "favicon.svg", "favicon-32.png", "apple-touch-icon.png"):
        if not (SITE / name).exists():
            errors.append(f"missing {name}")
    if "Sitemap: https://starconomy.com/sitemap.xml" not in (SITE / "robots.txt").read_text(encoding="utf-8"):
        errors.append("robots.txt missing sitemap")

    font_dir = SITE / "fonts"
    needed = [
        "ibm-plex-sans-400.woff2",
        "ibm-plex-sans-500.woff2",
        "ibm-plex-mono-400.woff2",
        "noto-sans-tc-400.woff2",
        "noto-sans-tc-500.woff2",
        "noto-sans-jp-400.woff2",
        "noto-sans-jp-500.woff2",
    ]
    for name in needed:
        if not (font_dir / name).exists():
            errors.append(f"missing font {name}")

    if not any(err.startswith("missing font") for err in errors):
        plex = cmap_of(font_dir / "ibm-plex-sans-400.woff2") & cmap_of(font_dir / "ibm-plex-sans-500.woff2")
        mono = cmap_of(font_dir / "ibm-plex-mono-400.woff2")
        tc = cmap_of(font_dir / "noto-sans-tc-400.woff2") & cmap_of(font_dir / "noto-sans-tc-500.woff2")
        jp = cmap_of(font_dir / "noto-sans-jp-400.woff2") & cmap_of(font_dir / "noto-sans-jp-500.woff2")
        mei = ord("渼")  # U+6E3C, the first character of the legal name
        if mei not in tc:
            errors.append(f"Noto Sans TC subset does not contain U+{mei:04X} 渼")
        if mei not in jp:
            errors.append(f"Noto Sans JP subset does not contain U+{mei:04X} 渼")
        stacks = {"en": plex | mono | tc, "zh": plex | mono | tc, "ja": plex | mono | tc | jp}
        for lang, path in PAGES.items():
            raw = path.read_text(encoding="utf-8")
            missing = sorted({ch for ch in visible_text(raw) if ord(ch) >= 32 and ord(ch) not in stacks[lang] and not ch.isspace()})
            if missing:
                preview = "".join(missing[:24])
                errors.append(f"{lang}: characters missing from fonts: {preview}")

    css = (SITE / "css" / "site.css").read_text(encoding="utf-8")
    if "fonts.googleapis" in css or "http://" in css:
        errors.append("stylesheet references a remote or insecure resource")

    if errors:
        print("\n".join(errors))
        return 1
    print("site checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
