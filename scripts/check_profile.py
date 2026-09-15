#!/usr/bin/env python3
"""Read-only checks for the publication and local preview. No network required."""
import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.image_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ('src', 'href'):
            if key in attrs:
                self.links.append(attrs[key])
        if 'srcset' in attrs:
            self.links += [s.strip().split()[0] for s in attrs['srcset'].split(',')]
        if tag == 'img':
            self.image_count += 1
            assert attrs.get('alt'), 'Missing image alternative text'


def main():
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_profile.py'), '--check'], check=True)
    count = 0
    for name in ('README.md', 'THEMES.md', 'ACKNOWLEDGEMENTS.md', 'preview.html', 'themes.html', 'acknowledgements.html'):
        content = (ROOT / name).read_text()
        refs = References()
        refs.feed(content)
        if name.endswith('.md'):
            refs.links += re.findall(r'\]\(([^\s)]+)\)', content)
            assert not re.search(r'<(?:script|style)\b|\bstyle=', content, re.I), f'Nonportable README styling: {name}'
        for reference in refs.links:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = (ROOT / unquote(parsed.path)).resolve()
            assert path.is_relative_to(ROOT) and path.is_file(), f'Broken local reference in {name}: {reference}'
            count += 1
    manifest = json.loads((ROOT / '.review/preview-manifest.json').read_text())
    for name, expected in {**manifest['inputs'], **manifest['outputs']}.items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        assert actual == expected, f'Stale preview: {name}'
    assets = json.loads((ROOT / 'assets/provenance.json').read_text())['outputs']
    for name in assets:
        path = ROOT / name
        if path.parent == ROOT / 'assets/brand' and path.name.startswith('section-'):
            # Simple lossless title bands compress below the screenshot threshold.
            # Verify their geometry and rendered detail as well as their file size.
            width, height, colors = map(int, subprocess.check_output(
                ['magick', 'identify', '-format', '%w %h %k', str(path)], text=True).split())
            assert (width, height) == (900, 108) and colors > 32, f'Invalid section title: {name}'
            assert path.stat().st_size > 1000, f'Suspiciously empty title: {name}'
        else:
            assert path.stat().st_size > 3000, f'Suspiciously empty image: {name}'
    from serve_preview import permitted
    for blocked in ('/.git/config', '/.review/preview-manifest.json', '/data/themes.json', '/scripts/build_profile.py',
                    '/assets/sources/shibumi-bars.png', '/../README.md', '/%2e%2e/README.md', '/assets/', '/no-such-file'):
        assert not permitted(blocked), f'Preview exposed a private path: {blocked}'
    for allowed in ('/', '/preview.html?theme=dark', '/assets/brand/hero.webp', '/assets/provenance.json'):
        assert permitted(allowed), f'Preview blocks a public path: {allowed}'
    print(f'OK: {count} local references, alt text, preview freshness, nonempty images and server path restrictions')


if __name__ == '__main__':
    main()
