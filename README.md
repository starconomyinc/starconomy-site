# Starconomy

Static site for [Starconomy](https://starconomy.com) (渼科星聯科技有限公司 / Starconomy INC.), Taipei. The page introduces **Binary Star (雙星)**: firmware assurance that rebuilds a release twice, independently, and reports one hash a buyer can check.

English, 日本語, and 繁體中文 are separate HTML pages. There is no build server in front of visitors, no cookie, and no third-party script.

## Preview locally

```bash
python3 serve.py
```

Then open:

- http://127.0.0.1:8000/ — English
- http://127.0.0.1:8000/ja/ — 日本語
- http://127.0.0.1:8000/zh/ — 繁體中文

The server sets the `font/woff2` MIME type. A plain `python3 -m http.server` run from `site/` also works in current browsers.

## Edit copy

Wording lives in `src/content.py`. Regenerate the HTML, then check it:

```bash
python3 src/build.py
python3 src/build.py --check
python3 scripts/check_site.py
```

The contact address is `hello@starconomy.com` (`EMAIL` in `src/content.py`). Change it there and regenerate. Pages link to it with `mailto:`; there is no form.

If you add characters, rebuild the CJK subsets so the self-hosted fonts still cover them, including 渼 (U+6E3C):

```bash
pip install fonttools brotli
python3 scripts/subset_fonts.py
```

Open Graph cards and the PNG icons are regenerated with `python3 scripts/render_images.py` (needs Pillow).

## GitHub Pages

The site is the `site/` directory. `.github/workflows/pages.yml` publishes it with GitHub Actions. `.github/workflows/ci.yml` checks that the committed HTML matches `src/build.py` and that the fonts cover the copy.

1. Merge this to `main` and push.
2. On GitHub, open **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. The **Deploy GitHub Pages** workflow runs on every push to `main`. The first run needs the Pages source set as above; until then the deployment job cannot create the `github-pages` environment.
5. When it succeeds, the project URL is `https://starconomyinc.github.io/starconomy-site/`.

`site/CNAME` contains `starconomy.com`. The workflow uploads that file, which sets the Pages custom domain. After GitHub redirects the `github.io` host to the custom domain, `starconomy.com` has to resolve or the redirect has nowhere to land. Publish the DNS records in the same window. If you need the `github.io` URL to keep serving before DNS is ready, remove the custom domain under Pages settings (that deletes the effect of `CNAME` until you put the domain back).

After the certificate is issued, turn on **Enforce HTTPS**.

## GoDaddy DNS

Use DNS records only. Turn off GoDaddy domain forwarding, and delete the parking A/AAAA records and any `www` record that points at GoDaddy’s parking host. Those records otherwise override the ones below.

Apex (`@`, `starconomy.com`) — four A records:

| Type | Host | Value |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

Apex AAAA records, optional but recommended:

| Type | Host | Value |
| --- | --- | --- |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |

`www` — one CNAME, not a forward:

| Type | Host | Value |
| --- | --- | --- |
| CNAME | `www` | `starconomyinc.github.io` |

The CNAME target is the account host, not `starconomyinc.github.io/starconomy-site`. GitHub serves the project site once the custom domain is attached. A short TTL (600 seconds) makes the cutover easier to correct. DNS propagation is independent of the Actions run; HTTPS stays pending until the records answer from GitHub’s addresses.

Canonical URLs on the pages are `https://starconomy.com/`, `/ja/`, and `/zh/`.

## Fonts

IBM Plex Sans, IBM Plex Mono, Noto Sans TC, and Noto Sans JP are self-hosted subsets under the SIL Open Font License. Notices are in `site/fonts/COPYRIGHT.txt` and `site/fonts/OFL.txt`. Noto Sans TC is what draws 渼 in the legal name, including on the Japanese page.

## Trademarks

ArduPilot and Cube are trademarks of their respective owners. The pilot section names them only to identify a public firmware image that was rebuilt. It is not a client engagement, a certification, or an endorsement.
