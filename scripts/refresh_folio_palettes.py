#!/usr/bin/env python3
"""Snapshot public ANSI colors 0–7; never infer colors from screenshot pixels."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
import tomllib
from urllib.request import Request, urlopen
from build_folio import FOLIO, ROOT


def fetch(theme):
    slug = theme['slug']
    url = f'https://raw.githubusercontent.com/HANCORE-linux/omarchy-{slug}-theme/HEAD/colors.toml'
    with urlopen(Request(url, headers={'User-Agent':'HANCORE-profile-preview'}), timeout=30) as response:
        data = response.read(100_001)
    assert len(data) < 100_000, f'Oversized color config: {slug}'
    config = tomllib.loads(data.decode())
    colors = [config[f'color{i}'] for i in range(8)]
    assert all(isinstance(c,str) and re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in colors), slug
    return slug, data, {'url':url, 'colors':colors, 'sha256':hashlib.sha256(data).hexdigest()}


def main():
    themes = json.loads((ROOT / 'data/themes.json').read_text())
    with ThreadPoolExecutor(max_workers=6) as pool:
        fetched = list(pool.map(fetch, themes))
    directory = FOLIO / 'sources/palettes'
    directory.mkdir(exist_ok=True)
    records = {}
    for slug, data, record in fetched:
        (directory / f'{slug}.toml').write_bytes(data)
        records[slug] = record
    snapshot = {'fetched_at':datetime.now(timezone.utc).isoformat(), 'order':'ANSI color0 through color7, left to right', 'themes':records}
    (FOLIO / 'palettes.json').write_text(json.dumps(snapshot,indent=2) + '\n')
    print(f'OK verified {len(records)} public ANSI palettes, eight source colors each')


if __name__ == '__main__':
    main()
