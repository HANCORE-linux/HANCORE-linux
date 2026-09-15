#!/usr/bin/env python3
"""Fetch the six public Shields badges for a dated, shadow-ready local snapshot."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from build_folio import FOLIO, badge_url, popular_works, theme_url


def fetch(work, stars=None):
    slug = work['theme_slug']
    url = badge_url(slug, stars)
    with urlopen(Request(url, headers={'User-Agent': 'HANCORE-profile-preview'}), timeout=30) as response:
        data = response.read(100_001)
    return validate_badge(work, data, stars)


def validate_badge(work, data, stars=None):
    slug = work['theme_slug']
    url = badge_url(slug, stars)
    assert len(data) < 100_000, 'Unexpected badge size'
    svg = ET.fromstring(data)
    assert svg.tag == '{http://www.w3.org/2000/svg}svg'
    assert svg.attrib['height'] == '20'
    assert 40 <= int(svg.attrib['width']) <= 200
    labels = [''.join(node.itertext()) for node in svg.iter('{http://www.w3.org/2000/svg}text')]
    assert len(labels) == 2 and labels[0] == 'stars', f'Unexpected badge labels: {labels}'
    count = re.fullmatch(r'([0-9,]+)', labels[1])
    assert count, f'Shields returned no star count for {slug}'
    if stars is not None:
        assert int(count[1].replace(',', '')) == stars, 'Badge disagrees with GitHub API'
    allowed = {'svg', 'g', 'rect', 'text', 'title', 'path', 'defs', 'clipPath', 'a'}
    for node in svg.iter():
        assert node.tag.rsplit('}', 1)[-1] in allowed, 'Unexpected badge element'
        assert not any(key.startswith('on') for key in node.attrib)
        for key, value in node.attrib.items():
            if 'href' in key:
                assert node.tag.endswith('}a') and value in {theme_url(slug), theme_url(slug) + '/stargazers'}
    assert b'#000000' in data and b'#df6124' in data, 'Badge colors changed'
    return slug, data, {'url': url, 'stars': int(count[1].replace(',', '')),
                        'width': int(svg.attrib['width']), 'height': 20,
                        'sha256': hashlib.sha256(data).hexdigest(), **({'api_snapshot': True} if stars is not None else {})}


def main():
    # Fetch and validate everything before replacing any previous source.
    with ThreadPoolExecutor(max_workers=6) as pool:
        fetched = list(pool.map(fetch, popular_works()))
    records = {}
    for slug, data, record in fetched:
        (FOLIO / 'sources' / f'badge-{slug}.svg').write_bytes(data)
        records[slug] = record
    snapshot = {'fetched_at': datetime.now(timezone.utc).isoformat(),
                'note': 'Public Shields snapshot. Exported shadow PNGs are not a live feed.',
                'badges': records}
    (FOLIO / 'badge-snapshot.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    print(f'OK refreshed {len(records)} public star badges; rebuild and render to show them')


if __name__ == '__main__':
    main()
