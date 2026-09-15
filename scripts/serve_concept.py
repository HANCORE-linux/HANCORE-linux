#!/usr/bin/env python3
"""Serve the separate concept plus the existing comparison pages on loopback."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from serve_preview import Handler, ROOT, permitted

PUBLIC = {'concept.html', 'concept/preview.js', 'concept/assets/signature-dark.png', 'concept/assets/signature-light.png'}


class ConceptHandler(Handler):
    def send_head(self):
        parsed = urlsplit(self.path)
        if parsed.path == '/':
            self.path = '/concept.html' + ('?' + parsed.query if parsed.query else '')
        name = unquote(urlsplit(self.path).path).lstrip('/')
        target = (ROOT / name).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file() or not (name in PUBLIC or permitted(self.path)):
            self.send_error(404)
            return None
        return SimpleHTTPRequestHandler.send_head(self)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), ConceptHandler)
    print(f'Editorial concept: http://127.0.0.1:{args.port}/concept.html?view=readme', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
