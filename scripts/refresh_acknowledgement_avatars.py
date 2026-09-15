#!/usr/bin/env python3
"""Fetch requested public GitHub avatars, unchanged and hash-recorded."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from refresh_folio_totals import download

FOLIO = Path(__file__).resolve().parents[1] / 'folio'


def fetch(person):
    assert re.fullmatch(r'[A-Za-z0-9-]+', person['github'])
    user = json.loads(subprocess.check_output(['gh', 'api', 'users/' + person['github']], text=True))
    assert user['login'].casefold() == person['github'].casefold()
    assert user['avatar_url'] == f'https://avatars.githubusercontent.com/u/{user["id"]}?v=4'
    url = user['avatar_url'] + '&s=256'
    data = download(url, 2_000_000)
    extension = 'png' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'jpg' if data.startswith(b'\xff\xd8\xff') else None
    assert extension, 'Only raster PNG/JPEG avatars are accepted'
    with tempfile.TemporaryDirectory(prefix='profile-avatar-') as tmp:
        path = Path(tmp) / f'avatar.{extension}'
        path.write_bytes(data)
        cmd = [shutil.which('magick'), 'identify'] if shutil.which('magick') else ['identify']
        size = subprocess.check_output([*cmd, '-ping', '-format', '%w %h', str(path)], text=True).split()
    width, height = map(int, size)
    assert 128 <= width <= 1024 and width == height, 'Expected a square public avatar'
    return person['slug'], data, {'github': user['login'], 'github_id': user['id'], 'url': url,
                                'path': f'sources/avatar-{person["slug"]}.{extension}',
                                'width': width, 'height': height,
                                'sha256': hashlib.sha256(data).hexdigest()}


def main():
    people = json.loads((FOLIO / 'acknowledgements.json').read_text())['people']
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', action='append', choices=[person['slug'] for person in people],
                        help='Refresh only this person, preserving other avatar sources')
    args = parser.parse_args()
    manifest_path = FOLIO / 'avatar-sources.json'
    stamp = datetime.now(timezone.utc).isoformat()
    if args.only:
        manifest = json.loads(manifest_path.read_text())
        people = [person for person in people if person['slug'] in args.only]
        manifest['last_updated'] = stamp
    else:
        manifest = {'fetched_at': stamp,
                    'note': 'Public GitHub profile avatars; unchanged raster sources, rights remain with their owners.',
                    'avatars': {}}
    with ThreadPoolExecutor(max_workers=4) as pool:
        fetched = list(pool.map(fetch, people))
    # Validate every response before writing; downloaded bytes are not altered.
    for slug, data, record in fetched:
        record['fetched_at'] = stamp
        (FOLIO / record['path']).write_bytes(data)
        manifest['avatars'][slug] = record
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'OK {len(fetched)} unchanged public GitHub avatars, square and hash-verified')


if __name__ == '__main__':
    main()
