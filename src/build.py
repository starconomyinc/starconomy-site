#!/usr/bin/env python3
"""Generate the static Starconomy site into ./site.

Usage:
  python3 src/build.py
  python3 src/build.py --check
"""

from __future__ import annotations

import difflib
import html
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import content  # noqa: E402

SITE = ROOT / "site"
ORIGIN = "https://starconomy.com"
TOKEN = re.compile(r"\[\[zh:([^\]]+)\]\]")

PATHS = {
    "en": {"out": "index.html", "href": "", "url": f"{ORIGIN}/", "og": "img/og-en.png"},
    "ja": {"out": "ja/index.html", "href": "ja/", "url": f"{ORIGIN}/ja/", "og": "img/og-ja.png"},
    "zh": {"out": "zh/index.html", "href": "zh/", "url": f"{ORIGIN}/zh/", "og": "img/og-zh.png"},
}

MARK = """<svg class="mark" viewBox="0 0 36 36" aria-hidden="true" focusable="false">
  <circle cx="12.5" cy="21" r="5.4" fill="#f4f0e6"/>
  <circle cx="25" cy="12.5" r="3.15" fill="#e6c98a"/>
</svg>"""

JSON_LD_DESC = {
    "en": "Firmware assurance. Two independent rebuilds, one hash a buyer can check.",
    "ja": "ファームウェアのビルド検証。独立した二つの再ビルドと、調達側が照合できる一つのハッシュ。",
    "zh": "韌體建置驗證。兩次獨立重建，交出一組採購方可核對的雜湊。",
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def rich(value: str) -> str:
    parts: list[str] = []
    pos = 0
    for match in TOKEN.finditer(value):
        parts.append(esc(value[pos : match.start()]))
        parts.append(f'<span lang="zh-Hant">{esc(match.group(1))}</span>')
        pos = match.end()
    parts.append(esc(value[pos:]))
    return "".join(parts)


def h1_html(value: str) -> str:
    return "<br>".join(esc(line) for line in value.split("\n"))


def legal() -> str:
    return f'<span class="legal" lang="zh-Hant" translate="no">{esc(content.LEGAL_NAME)}</span>'


def prefix_for(lang_id: str) -> str:
    return "" if lang_id == "en" else "../"


def href_between(current: str, target: str) -> str:
    target_href = PATHS[target]["href"]
    if current == "en":
        return "./" if target == "en" else target_href
    if target == "en":
        return "../"
    if target == current:
        return "./"
    return "../" + target_href


def mailto(page: dict) -> str:
    return f"mailto:{content.EMAIL}?subject={quote(page['subject'])}"


def lang_switcher(current: str) -> str:
    page = content.PAGES[current]
    links = []
    for item in content.LANG_LINKS:
        href = href_between(current, item["id"])
        current_attr = ' aria-current="page"' if item["id"] == current else ""
        links.append(
            f'<a href="{esc(href)}" hreflang="{esc(item["html_lang"])}" '
            f'lang="{esc(item["html_lang"])}"{current_attr}>{esc(item["label"])}</a>'
        )
    return (
        f'<nav class="lang" aria-label="{esc(page["lang_label"])}">'
        + "".join(links)
        + "</nav>"
    )


def schematic(page: dict) -> str:
    s = page["schematic"]
    return f"""
<figure class="schematic">
  <figcaption>{esc(s["kicker"])}</figcaption>
  <ol>
    <li>
      <span class="sn">01</span>
      <div>
        <p class="st">{esc(s["source_title"])}</p>
        <p class="sd">{esc(s["source_text"])}</p>
      </div>
    </li>
    <li>
      <span class="sn">02</span>
      <div class="pair">
        <div>
          <p class="st">{esc(s["build_a"])}</p>
          <span class="bar" aria-hidden="true"></span>
        </div>
        <div>
          <p class="st">{esc(s["build_b"])}</p>
          <span class="bar" aria-hidden="true"></span>
        </div>
        <p class="sd pair-note">{esc(s["build_text"])}</p>
      </div>
    </li>
    <li>
      <span class="sn">03</span>
      <div>
        <p class="st">{esc(s["hash_title"])}</p>
        <p class="sd">{esc(s["hash_text"])}</p>
      </div>
    </li>
    <li>
      <span class="sn">04</span>
      <div>
        <p class="st">{esc(s["report_title"])}</p>
        <p class="sd">{esc(s["report_text"])}</p>
      </div>
    </li>
  </ol>
  <p class="schematic-note">{esc(s["note"])}</p>
</figure>"""


def points(items: list[dict]) -> str:
    rows = []
    for index, item in enumerate(items, start=1):
        rows.append(
            "<li>"
            f'<span class="pn">0{index}</span>'
            "<div>"
            f"<h3>{esc(item['title'])}</h3>"
            f"<p>{esc(item['text'])}</p>"
            "</div></li>"
        )
    return '<ol class="points">' + "".join(rows) + "</ol>"


def timeline(events: list[dict]) -> str:
    rows = []
    for event in events:
        rows.append(
            "<li>"
            f'<time datetime="{esc(event["iso"])}">{esc(event["when"])}</time>'
            f"<p>{esc(event['text'])}</p>"
            "</li>"
        )
    return '<ol class="timeline">' + "".join(rows) + "</ol>"


def steps(items: list[dict]) -> str:
    rows = []
    for index, item in enumerate(items, start=1):
        rows.append(
            "<li>"
            f'<span class="sn">0{index}</span>'
            f"<h3>{esc(item['title'])}</h3>"
            f"<p>{esc(item['text'])}</p>"
            "</li>"
        )
    return '<ol class="steps">' + "".join(rows) + "</ol>"


def deliverable_list(items: list[dict]) -> str:
    rows = []
    for index, item in enumerate(items, start=1):
        rows.append(
            "<li>"
            f'<span class="sn">0{index}</span>'
            "<div>"
            f"<h3>{esc(item['title'])}</h3>"
            f"<p>{esc(item['text'])}</p>"
            "</div></li>"
        )
    return '<ol class="deliverables">' + "".join(rows) + "</ol>"


def tiers(page: dict, mail: str) -> str:
    block = page["tiers"]
    has_gloss = any(item["gloss"] for item in block["items"])
    cards = []
    for index, item in enumerate(block["items"], start=1):
        tag = f'<p class="tag">{esc(item["tag"])}</p>' if item["tag"] else ""
        gloss = f'<p class="gloss">{esc(item["gloss"])}</p>' if has_gloss else ""
        cards.append(
            "<li>"
            f'<div class="tier-kicker"><span class="sn">0{index}</span>{tag}</div>'
            f"<h3>{esc(item['name'])}</h3>"
            f"{gloss}"
            f'<p class="tier-copy">{esc(item["text"])}</p>'
            "</li>"
        )
    klass = "tiers with-gloss" if has_gloss else "tiers"
    return (
        f'<ol class="{klass}">'
        + "".join(cards)
        + "</ol>"
        + f'<p class="section-cta"><a class="btn btn-primary" href="{esc(mail)}">{esc(block["cta"])}</a></p>'
    )


def proof_table(rows: list[dict]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f'<th scope="row">{esc(row["label"])}</th>'
            f"<td>{esc(row['value'])}</td>"
            "</tr>"
        )
    return '<table class="spec"><tbody>' + "".join(body) + "</tbody></table>"


def about_facts(page: dict) -> str:
    about = page["about"]
    rows = [
        (about["legal_label"], legal()),
        (about["english_label"], esc(about["english_name"])),
        (about["place_label"], esc(about["place"])),
        (about["service_label"], rich(about["service"])),
    ]
    body = []
    for label, value in rows:
        body.append(f'<div><dt>{esc(label)}</dt><dd>{value}</dd></div>')
    return '<dl class="facts">' + "".join(body) + "</dl>"


def head_links(lang_id: str) -> str:
    links = []
    for item in content.LANG_LINKS:
        links.append(
            f'<link rel="alternate" hreflang="{esc(item["html_lang"])}" href="{PATHS[item["id"]]["url"]}">'
        )
    links.append(f'<link rel="alternate" hreflang="x-default" href="{PATHS["en"]["url"]}">')
    page_locale = LOCALES_SAFE[lang_id]
    others = [LOCALES_SAFE[item] for item in content.LANG_ORDER if item != lang_id]
    og_alt = "".join(f'<meta property="og:locale:alternate" content="{esc(code)}">' for code in others)
    return "\n  ".join(links), page_locale, og_alt


LOCALES_SAFE = {"en": "en_US", "ja": "ja_JP", "zh": "zh_TW"}


def json_ld(lang_id: str, page: dict) -> str:
    url = PATHS[lang_id]["url"]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{ORIGIN}/#org",
                "name": "Starconomy",
                "legalName": content.LEGAL_NAME,
                "alternateName": "Starconomy INC.",
                "url": f"{ORIGIN}/",
                "email": content.EMAIL,
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Taipei",
                    "addressCountry": "TW",
                },
                "description": JSON_LD_DESC[lang_id],
                "knowsLanguage": ["en", "ja", "zh-Hant"],
            },
            {
                "@type": "Service",
                "name": "Binary Star",
                "alternateName": "雙星",
                "serviceType": "Firmware assurance",
                "provider": {"@id": f"{ORIGIN}/#org"},
                "areaServed": ["TW", "JP", "EU", "US"],
                "url": url,
                "description": page["description"],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def render_page(lang_id: str) -> str:
    page = content.PAGES[lang_id]
    meta = PATHS[lang_id]
    pre = prefix_for(lang_id)
    mail = mailto(page)
    html_lang = {"en": "en", "ja": "ja", "zh": "zh-Hant"}[lang_id]
    alternates, locale, og_alt = head_links(lang_id)
    primary = "".join(
        f'<a href="#{esc(key)}">{esc(page["nav"][key])}</a>' for key in content.HEADER_NAV
    )
    footer_links = "".join(
        f'<a href="#{esc(key)}">{esc(page["nav"][key])}</a>' for key in content.FOOTER_NAV
    )
    paragraphs = "".join(f"<p>{rich(text)}</p>" for text in page["about"]["paragraphs"])
    preload_fonts = {
        "en": ("fonts/ibm-plex-sans-500.woff2", "fonts/ibm-plex-sans-400.woff2"),
        "ja": ("fonts/noto-sans-jp-500.woff2", "fonts/noto-sans-jp-400.woff2"),
        "zh": ("fonts/noto-sans-tc-500.woff2", "fonts/noto-sans-tc-400.woff2"),
    }[lang_id]
    preloads = "\n  ".join(
        f'<link rel="preload" href="{pre}{esc(font)}" as="font" type="font/woff2" crossorigin>'
        for font in preload_fonts
    )
    kicker_lang = "zh-Hant" if lang_id == "zh" else ("ja" if lang_id == "ja" else "en")
    mark_lang = "zh-Hant" if lang_id != "ja" else "ja"
    if lang_id == "zh":
        mark_lang = "en"
        kicker_lang = "zh-Hant"

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#0b0c0f">
  <meta name="format-detection" content="telephone=no">
  <meta name="referrer" content="no-referrer">
  <title>{esc(page["title"])}</title>
  <meta name="description" content="{esc(page["description"])}">
  <link rel="canonical" href="{meta["url"]}">
  {alternates}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Starconomy">
  <meta property="og:title" content="{esc(page["title"])}">
  <meta property="og:description" content="{esc(page["description"])}">
  <meta property="og:url" content="{meta["url"]}">
  <meta property="og:image" content="{ORIGIN}/{meta["og"]}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{esc(page["og_alt"])}">
  <meta property="og:locale" content="{locale}">
  {og_alt}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(page["title"])}">
  <meta name="twitter:description" content="{esc(page["description"])}">
  <meta name="twitter:image" content="{ORIGIN}/{meta["og"]}">
  <meta name="twitter:image:alt" content="{esc(page["og_alt"])}">
  <link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
  <link rel="icon" href="{pre}favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="{pre}apple-touch-icon.png">
  {preloads}
  <link rel="stylesheet" href="{pre}css/site.css">
  <script type="application/ld+json">{json_ld(lang_id, page)}</script>
  <script>document.documentElement.classList.add("js")</script>
</head>
<body>
  <a class="skip" href="#content">{esc(page["skip"])}</a>
  <header class="site-header">
    <div class="wrap header-wrap">
      <a class="brand" href="{esc(href_between(lang_id, lang_id))}">
        {MARK}
        <span class="brand-name">Starconomy</span>
      </a>
      <nav id="site-nav" class="site-nav" aria-label="{esc(page["nav_label"])}">
        {primary}
        <a class="nav-mail" href="{esc(mail)}">{esc(page["contact_label"])}</a>
      </nav>
      <div class="header-tools">
        {lang_switcher(lang_id)}
        <a class="btn btn-small header-cta" href="{esc(mail)}">{esc(page["contact_label"])}</a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" data-open-label="{esc(page["menu"])}" data-close-label="{esc(page["close"])}">
          <span class="bars" aria-hidden="true"></span>
          <span class="visually-hidden toggle-label">{esc(page["menu"])}</span>
        </button>
      </div>
    </div>
  </header>
  <main id="content">
    <section class="hero" aria-labelledby="hero-title">
      <div class="stars" aria-hidden="true">
        <i style="left:8%;top:18%"></i><i style="left:18%;top:72%"></i><i style="left:27%;top:30%"></i>
        <i style="left:36%;top:12%"></i><i style="left:48%;top:64%"></i><i style="left:61%;top:22%"></i>
        <i style="left:70%;top:78%"></i><i style="left:78%;top:14%"></i><i style="left:88%;top:40%"></i>
        <i style="left:93%;top:68%"></i><i class="bright" style="left:84%;top:10%"></i>
        <i class="warm" style="left:89%;top:16%"></i>
      </div>
      <div class="wrap hero-grid">
        <div class="hero-copy">
          <p class="eyebrow"><span lang="{kicker_lang}">{esc(page["hero_kicker"])}</span> <span class="dot" aria-hidden="true">·</span> <span lang="{mark_lang}">{esc(page["hero_kicker_mark"])}</span></p>
          <h1 id="hero-title">{h1_html(page["h1"])}</h1>
          <p class="lede">{esc(page["lede"])}</p>
          <div class="actions">
            <a class="btn btn-primary" href="#method">{esc(page["cta_method"])}</a>
            <a class="btn btn-ghost" href="{esc(mail)}">{esc(page["cta_pricing"])}</a>
          </div>
          <p class="tagline">{esc(page["tagline"])}</p>
          <p class="hero-meta">{legal()} <span aria-hidden="true">·</span> {esc(page["hero_place"])}</p>
        </div>
        {schematic(page)}
      </div>
    </section>

    <section id="problem" class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="idx">{esc(page["problem"]["index"])}</p>
          <div>
            <h2>{esc(page["problem"]["title"])}</h2>
            <p class="intro">{esc(page["problem"]["intro"])}</p>
          </div>
        </div>
        <div class="section-body">
          {points(page["problem"]["points"])}
        </div>
      </div>
    </section>

    <section id="why" class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="idx">{esc(page["why"]["index"])}</p>
          <div>
            <h2>{esc(page["why"]["title"])}</h2>
            <p class="intro">{esc(page["why"]["intro"])}</p>
          </div>
        </div>
        <div class="section-body">
          {timeline(page["why"]["events"])}
          <p class="closing">{esc(page["why"]["closing"])}</p>
        </div>
      </div>
    </section>

    <section id="method" class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="idx">{esc(page["method"]["index"])}</p>
          <div>
            <h2>{esc(page["method"]["title"])}</h2>
            <p class="intro">{esc(page["method"]["intro"])}</p>
          </div>
        </div>
        <div class="section-body">
          {steps(page["method"]["steps"])}
        </div>
      </div>
    </section>

    <section id="deliverables" class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="idx">{esc(page["deliverables"]["index"])}</p>
          <div>
            <h2>{esc(page["deliverables"]["title"])}</h2>
            <p class="intro">{esc(page["deliverables"]["intro"])}</p>
          </div>
        </div>
        <div class="section-body">
          {deliverable_list(page["deliverables"]["items"])}
        </div>
      </div>
    </section>

    <section id="tiers" class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="idx">{esc(page["tiers"]["index"])}</p>
          <div>
            <h2>{esc(page["tiers"]["title"])}</h2>
            <p class="intro">{esc(page["tiers"]["intro"])}</p>
          </div>
        </div>
        <div class="section-body">
          {tiers(page, mail)}
        </div>
      </div>
    </section>

    <section id="proof" class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="idx">{esc(page["proof"]["index"])}</p>
          <div>
            <p class="eyebrow">{esc(page["proof"]["kicker"])}</p>
            <h2>{esc(page["proof"]["title"])}</h2>
            <p class="intro">{esc(page["proof"]["intro"])}</p>
            <p class="coming">{esc(page["proof"]["coming"])}</p>
          </div>
        </div>
        <div class="section-body">
          {proof_table(page["proof"]["rows"])}
          <p class="note">{esc(page["proof"]["note"])}</p>
        </div>
      </div>
    </section>

    <section id="about" class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="idx">{esc(page["about"]["index"])}</p>
          <div>
            <h2>{esc(page["about"]["title"])}</h2>
            {paragraphs}
          </div>
        </div>
        <div class="section-body">
          {about_facts(page)}
        </div>
      </div>
    </section>

    <section id="contact" class="contact">
      <div class="wrap contact-grid">
        <p class="idx">{esc(page["contact"]["index"])}</p>
        <div>
          <h2>{esc(page["contact"]["title"])}</h2>
          <p class="intro">{esc(page["contact"]["intro"])}</p>
          <p><a class="email" href="{esc(mail)}">{esc(content.EMAIL)}</a></p>
          <p class="hero-meta">{legal()} <span aria-hidden="true">·</span> {esc(page["contact"]["place_label"])}</p>
          <p class="note">{esc(page["contact"]["noform"])}</p>
        </div>
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="wrap footer-grid">
      <div>
        <p class="brand-name">Starconomy</p>
        <p class="legal-line">{legal()}</p>
        <p>Starconomy INC.</p>
        <p>{esc(page["hero_place"])}</p>
      </div>
      <nav class="footer-nav" aria-label="{esc(page["footer_nav_label"])}">
        {footer_links}
      </nav>
      <div class="footer-meta">
        {lang_switcher(lang_id)}
        <p>{esc(page["footer"]["rights"])}</p>
        <p>{esc(page["footer"]["privacy"])}</p>
        <p>{esc(page["footer"]["trademark"])}</p>
      </div>
    </div>
  </footer>
  <script src="{pre}js/site.js"></script>
</body>
</html>
"""


def render_404() -> str:
    body = []
    for lang_id in content.LANG_ORDER:
        page = content.PAGES[lang_id]
        html_lang = {"en": "en", "ja": "ja", "zh": "zh-Hant"}[lang_id]
        path = PATHS[lang_id]["href"]
        body.append(
            f'<section lang="{html_lang}">'
            f"<h2>{esc(page['not_found_title'])}</h2>"
            f'<p><a data-path="{esc(path)}" href="{esc(PATHS[lang_id]["url"])}">{esc(page["not_found_back"])}</a></p>'
            "</section>"
        )
    sections = "".join(body)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="robots" content="noindex">
  <title>Not found | Starconomy</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin: 0; background: #0b0c0f; color: #f4f0e6; font: 400 1.05rem/1.6 "IBM Plex Sans", "Noto Sans TC", "Noto Sans JP", sans-serif; }}
    main {{ max-width: 40rem; margin: 0 auto; padding: 4.5rem 1.25rem 3rem; }}
    .brand {{ letter-spacing: 0.04em; color: #e6c98a; margin: 0 0 1.5rem; }}
    h1 {{ font-size: 1.4rem; font-weight: 500; margin: 0 0 1.5rem; }}
    h2 {{ font-size: 1.35rem; font-weight: 500; margin: 0 0 0.4rem; }}
    section {{ padding: 1rem 0; border-top: 1px solid rgba(244,240,230,0.16); }}
    a {{ color: #f4f0e6; }}
    a:focus-visible {{ outline: 2px solid #e6c98a; outline-offset: 3px; }}
  </style>
</head>
<body>
  <main>
    <p class="brand">Starconomy</p>
    <h1 lang="en">404</h1>
    {sections}
  </main>
  <script>
    (function () {{
      var root = "/";
      if (location.hostname.endsWith("github.io")) {{
        var seg = location.pathname.split("/").filter(Boolean)[0];
        if (seg && seg !== "ja" && seg !== "zh") root = "/" + seg + "/";
      }}
      document.querySelectorAll("a[data-path]").forEach(function (a) {{
        a.href = root + a.getAttribute("data-path");
      }});
    }})();
  </script>
</body>
</html>
"""


def render_sitemap() -> str:
    urls = []
    for lang_id in content.LANG_ORDER:
        loc = PATHS[lang_id]["url"]
        alternates = []
        for item in content.LANG_LINKS:
            alternates.append(
                f'    <xhtml:link rel="alternate" hreflang="{item["html_lang"]}" href="{PATHS[item["id"]]["url"]}"/>'
            )
        alternates.append(
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{PATHS["en"]["url"]}"/>'
        )
        urls.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            + "\n".join(alternates)
            + "\n  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def render_robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}/sitemap.xml\n"


GENERATED = {
    "index.html": lambda: render_page("en"),
    "ja/index.html": lambda: render_page("ja"),
    "zh/index.html": lambda: render_page("zh"),
    "404.html": render_404,
    "sitemap.xml": render_sitemap,
    "robots.txt": render_robots,
    "CNAME": lambda: "starconomy.com\n",
    ".nojekyll": lambda: "",
}


def write_tree(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for rel, factory in GENERATED.items():
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        text = factory()
        if rel.endswith(".html"):
            text = text.strip() + "\n"
        path.write_text(text, encoding="utf-8")


def check() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        write_tree(dest)
        failed = False
        for rel in GENERATED:
            expected = (dest / rel).read_text(encoding="utf-8")
            current_path = SITE / rel
            if not current_path.exists():
                print(f"missing {rel}")
                failed = True
                continue
            current = current_path.read_text(encoding="utf-8")
            if current != expected:
                print(f"out of date: {rel}")
                diff = difflib.unified_diff(
                    current.splitlines(keepends=True),
                    expected.splitlines(keepends=True),
                    fromfile=f"site/{rel}",
                    tofile=f"generated/{rel}",
                    n=2,
                )
                sys.stdout.writelines(list(diff)[:200])
                failed = True
        if failed:
            print("Run python3 src/build.py to regenerate.", file=sys.stderr)
            return 1
    print("site HTML is up to date")
    return 0


def main() -> int:
    if "--check" in sys.argv:
        return check()
    write_tree(SITE)
    print(f"wrote {len(GENERATED)} files into {SITE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
