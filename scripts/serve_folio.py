#!/usr/bin/env python3
"""Serve the new README and old comparison preview on loopback only."""
import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit
from serve_preview import Handler, ROOT, permitted
from build_folio import popular_works
from folio_details import detail_cards
from folio_connections import specs as connection_specs

PUBLIC = {'folio.html','folio/preview.css','folio/preview.js','folio/public-avatar.png'}
PUBLIC.update({'register.html', 'register-profile.html'})
PUBLIC.update({'collection.html', 'identity.html'})
PUBLIC.add('folio-acknowledgements.html')
PUBLIC.update(f'folio/collection/assets/{theme["slug"]}-{mode}.png' for theme in json.loads((ROOT / 'data/themes.json').read_text()) for mode in ['dark', 'light'])
PUBLIC.update(f'folio/collection/assets/identity-{mode}.png' for mode in ['dark', 'light'])
PUBLIC.update(f'folio/studies/register/assets/solitude-{mode}.png' for mode in ['dark', 'light'])
PUBLIC.add('folio/assets/omarchy-wordmark-orange.png')
PUBLIC.update(f'folio/assets/total-stars-{mode}.png' for mode in ['dark', 'light'])
PUBLIC.update(f'folio/assets/palette-{theme["slug"]}.png' for theme in json.loads((ROOT / 'data/themes.json').read_text()))
PUBLIC.update(f'folio/assets/{name}-{mode}.png' for name in ['signature','shibumi','solitude','omaq','banish'] for mode in ['dark','light'])
PUBLIC.update(f'folio/assets/{name}-{mode}.png' for name in ['marketplace','waybar','qs-dots'] for mode in ['dark','light'])
PUBLIC.update(f'folio/assets/{prefix}-{work["theme_slug"]}-{mode}.png' for work in popular_works() for prefix in ['popular', 'badge'] for mode in ['dark','light'])
PUBLIC.update(f'folio/assets/wordmark-{variant["id"]}-{mode}.png' for variant in json.loads((ROOT / 'folio/identity.json').read_text())['variants'] for mode in ['dark','light'])
PUBLIC.update(f'folio/assets/mark-logo-{mode}.png' for mode in ['dark', 'light'])
PUBLIC.update(f'folio/assets/mark-core-{mode}.png' for mode in ['dark', 'light'])
PUBLIC.update(f'folio/assets/connected-{spec["slug"]}-{mode}.png' for spec in connection_specs(popular_works(), detail_cards(json.loads((ROOT / 'data/themes.json').read_text()), json.loads((ROOT / 'folio/highlights.json').read_text()))) for mode in ['dark', 'light'])
PUBLIC.update(f'folio/assets/label-{slug}-{mode}.png' for slug in ['subtitle', 'popular', 'archive', 'acknowledgements'] for mode in ['dark', 'light'])
PUBLIC.update(f'folio/assets/info-{slug}-{mode}.png' for slug in ['waybar', 'qs-dots', 'archive', *[t['slug'] for t in json.loads((ROOT / 'data/themes.json').read_text())]] for mode in ['dark', 'light'])
PUBLIC.update(f'folio/assets/social-{slug}-{mode}.png' for slug in ['discord', 'kofi', 'acknowledgements'] for mode in ['dark', 'light'])


class FolioHandler(Handler):
    def send_head(self):
        parsed = urlsplit(self.path)
        if parsed.path == '/':
            self.path = '/folio.html' + ('?' + parsed.query if parsed.query else '')
        name = unquote(urlsplit(self.path).path).lstrip('/')
        target = (ROOT / name).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file() or not (name in PUBLIC or permitted(self.path)):
            self.send_error(404)
            return None
        return SimpleHTTPRequestHandler.send_head(self)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1',args.port),FolioHandler)
    print(f'Compact GitHub profile: http://127.0.0.1:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
