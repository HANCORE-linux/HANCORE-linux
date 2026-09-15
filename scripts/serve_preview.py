#!/usr/bin/env python3
"""Serve only the public preview surface on loopback, never .git or review backups."""
from __future__ import annotations
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = {'index.html', 'preview.html', 'themes.html', 'acknowledgements.html', 'assets/provenance.json'}


def permitted(path: str) -> bool:
    name = unquote(urlsplit(path).path).lstrip('/') or 'index.html'
    parts = Path(name).parts
    if any(p.startswith('.') for p in parts) or '\\' in name:
        return False
    target = (ROOT / name).resolve()
    if not target.is_relative_to(ROOT) or not target.is_file():
        return False
    if name in PAGES:
        return True
    if len(parts) == 3 and parts[:2] in [('assets', 'brand'), ('assets', 'systems'), ('assets', 'themes')]:
        return target.suffix in {'.webp', '.png'}
    return name in {'scripts/preview/preview.css', 'scripts/preview/preview.js',
                    'scripts/preview/github-markdown.min.css', 'scripts/preview/github-markdown-themes.css',
                    'scripts/preview/LICENSE-github-markdown-css'}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        if not permitted(self.path):
            self.send_error(404)
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Profile preview: http://127.0.0.1:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
