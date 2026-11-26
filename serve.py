#!/usr/bin/env python3
"""Serve the site locally with a correct font MIME type.

    python3 serve.py
    python3 serve.py --port 8000
"""

from __future__ import annotations

import argparse
import http.server
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "site"


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".woff2": "font/woff2",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview the Starconomy site")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()
    os.chdir(ROOT)
    server = http.server.ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"Serving {ROOT} at http://{args.bind}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
