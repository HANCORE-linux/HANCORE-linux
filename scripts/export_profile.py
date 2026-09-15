#!/usr/bin/env python3
"""Export the approved folio to the GitHub profile root; never commit or push."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('README.md', 'THEMES.md', 'ACKNOWLEDGEMENTS.md')
HEADER = '<!-- Generated from folio/ by scripts/export_profile.py --write. -->\n'


def publication_source(name):
    source = (ROOT / 'folio' / name).read_text()
    # Markdown cross-links stay at the root; only image paths move one level.
    return HEADER + re.sub(r'\b(src|srcset)="\./(assets|collection)/',
                           r'\1="./folio/\2/', source)


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = 0
        self.links = []
        self.local = set()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        assert tag not in {'script', 'style', 'iframe'}, tag
        if tag == 'img':
            self.images += 1
            assert attrs.get('alt') and attrs.get('width') and attrs.get('height')
        if tag == 'a':
            self.links.append(attrs['href'])
        for key in ('src', 'srcset', 'href'):
            if key not in attrs:
                continue
            value = attrs[key]
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc:
                assert value.startswith('https://'), value
                continue
            assert not parsed.query and not parsed.fragment, value
            target = (ROOT / parsed.path).resolve()
            assert target.is_relative_to(ROOT) and target.is_file(), value
            self.local.add(target.relative_to(ROOT).as_posix())


def verify(documents):
    acknowledgements_count = len(json.loads((ROOT / 'folio/acknowledgements.json').read_text())['people']) + 1
    expected_counts = {'README.md': (23, 19), 'THEMES.md': (28, 29),
                       'ACKNOWLEDGEMENTS.md': (acknowledgements_count, acknowledgements_count)}
    references = set()
    for name, source in documents.items():
        parsed = References()
        parsed.feed(source)
        assert (parsed.images, len(parsed.links)) == expected_counts[name], name
        references.update(parsed.local)
        if name == 'README.md':
            assert './THEMES.md' in parsed.links and './ACKNOWLEDGEMENTS.md' in parsed.links
            assert 'https://github.com/omacom/omarchy-plugin-marketplace' in parsed.links
        elif name == 'THEMES.md':
            assert parsed.links.count('https://github.com/HANCORE-linux') == 2
            assert './README.md' not in parsed.links
        else:
            assert parsed.links.count('https://github.com/HANCORE-linux') == 1
            assert './README.md' not in parsed.links
            assert 'https://github.com/dhh' in parsed.links
    return references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true', help='Update the three root Markdown files')
    mode.add_argument('--check', action='store_true', help='Read-only export and local-link verification')
    args = parser.parse_args()
    documents = {name: publication_source(name) for name in PAGES}
    references = verify(documents)
    for name, source in documents.items():
        path = ROOT / name
        if args.write:
            path.write_text(source)
        else:
            assert path.read_text() == source, f'Stale publication export: {name}'
    print(f'OK three profile pages, {len(references)} local targets, approved folio content and rebased image paths')


if __name__ == '__main__':
    main()
