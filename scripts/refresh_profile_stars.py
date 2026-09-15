#!/usr/bin/env python3
"""Refresh all theme stars and project totals without changing original imagery.

Downloads are validated before any file is written. No commit or push here;
the scheduled workflow builds/checks the exports before publishing them.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from refresh_folio_badges import fetch as fetch_badge
from refresh_folio_totals import prepare as prepare_total

ROOT = Path(__file__).resolve().parents[1]
FOLIO = ROOT / 'folio'


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def ranked(stars):
    assert all(re.fullmatch(r'[a-z0-9-]+', slug) and type(count) is int and count >= 0
               for slug, count in stars.items())
    return sorted((slug for slug, count in stars.items() if count > 30),
                  key=lambda slug: (-stars[slug], f'omarchy-{slug}-theme'))[:6]


def theme_counts(total, themes):
    repos = {r['full_name'].casefold(): r for r in total['repositories']}
    counts = {}
    for theme in themes:
        slug = theme['slug']
        assert re.fullmatch(r'[a-z0-9-]+', slug)
        name = f'{total["account"]}/omarchy-{slug}-theme'.casefold()
        assert name in repos, f'Missing public theme: {name}; keep previous snapshot'
        repo = repos[name]
        assert repo['fork'] is False and repo['private'] is False
        assert type(repo['stars']) is int and repo['stars'] >= 0
        counts[slug] = repo['stars']
    return counts


def plan_updates(total, total_badge):
    """Return an in-memory write set; a failed download leaves all files intact."""
    assert sha256(total_badge) == total['badge']['sha256']
    themes = json.loads((ROOT / 'data/themes.json').read_text())
    counts = theme_counts(total, themes)
    popular = json.loads((FOLIO / 'popular-themes.json').read_text())
    badges = json.loads((FOLIO / 'badge-snapshot.json').read_text())
    collection = json.loads((FOLIO / 'collection/sources.json').read_text())
    selected = ranked(counts)
    writes = {FOLIO / 'total-stars.json': encoded(total),
              FOLIO / 'sources/badge-total-stars.svg': total_badge}
    records, badge_bytes, images = {}, {}, {}
    for slug in counts:
        if slug in badges['badges']:
            record = badges['badges'][slug]
            source = FOLIO / f'sources/badge-{slug}.svg'
        else:
            record = collection['themes'][slug]['badge']
            source = FOLIO / f'collection/sources/badge-{slug}.svg'
        data = source.read_bytes()
        assert sha256(data) == record['sha256'], f'Changed badge source: {slug}'
        records[slug], badge_bytes[slug] = record, data
        if slug in popular['previews']:
            data = (FOLIO / f'sources/popular-{slug}.png').read_bytes()
            assert git_blob(data) == popular['previews'][slug]['git_blob'], slug
        else:
            data = (FOLIO / f'collection/sources/{slug}.png').read_bytes()
            assert sha256(data) == collection['themes'][slug]['sha256'], slug
        assert data[:8] == b'\x89PNG\r\n\x1a\n', slug
        images[slug] = data
    changed = [slug for slug in counts if records[slug]['stars'] != counts[slug]
               or not records[slug].get('api_snapshot')]
    if not changed and popular['star_snapshot'] == counts and set(badges['badges']) == set(selected):
        return writes
    # Static Shields badges use the very same exact API counts as the total/rank.
    with ThreadPoolExecutor(max_workers=5) as pool:
        fetched = list(pool.map(lambda slug: fetch_badge({'theme_slug': slug}, counts[slug]), changed))
    for slug, data, record in fetched:
        assert record['stars'] == counts[slug] and sha256(data) == record['sha256']
        records[slug], badge_bytes[slug] = record, data
    stamp = datetime.now(timezone.utc).isoformat()
    popular = deepcopy(popular)
    popular.update({'verified_on': stamp[:10], 'source': total['sources'][0], 'star_snapshot': counts})
    collection = deepcopy(collection)
    collection['badges_fetched_at'] = stamp  # Preserve the original screenshot fetch date.
    for slug, data in images.items():
        if slug in selected:
            if slug not in popular['previews']:
                popular['previews'][slug] = {
                    'branch': 'HEAD', 'git_blob': git_blob(data),
                    'note': 'Reused hash-verified archive screenshot; no new image download.'}
            writes[FOLIO / f'sources/popular-{slug}.png'] = data
            writes[FOLIO / f'sources/badge-{slug}.svg'] = badge_bytes[slug]
        # Keep verified archive caches, including former popular themes.
        if slug not in selected and slug not in collection['themes']:
            preview = popular['previews'][slug]
            collection['themes'][slug] = {
                'url': f'https://raw.githubusercontent.com/{total["account"]}/omarchy-{slug}-theme/{preview["branch"]}/preview.png',
                'width': int.from_bytes(data[16:20], 'big'), 'height': int.from_bytes(data[20:24], 'big'),
                'sha256': sha256(data), 'git_blob': git_blob(data),
                'note': 'Reused preserved popular screenshot; no new image download.'}
            writes[FOLIO / f'collection/sources/{slug}.png'] = data
        if slug in collection['themes']:
            collection['themes'][slug]['badge'] = records[slug]
            writes[FOLIO / f'collection/sources/badge-{slug}.svg'] = badge_bytes[slug]
    writes[FOLIO / 'popular-themes.json'] = encoded(popular)
    writes[FOLIO / 'collection/sources.json'] = encoded(collection)
    writes[FOLIO / 'badge-snapshot.json'] = encoded({
        'fetched_at': stamp,
        'note': 'Exact public GitHub API counts, static Shields styling; refreshed daily by profile-stars.',
        'badges': {slug: records[slug] for slug in selected}})
    return writes


def apply_updates(writes):
    changed = 0
    for path, data in writes.items():
        assert path.resolve().is_relative_to(FOLIO.resolve()) and not path.is_symlink()
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
            changed += 1
    return changed


def main():
    total, total_badge = prepare_total()
    changed = apply_updates(plan_updates(total, total_badge))
    print(f'OK {total["owned_stars"]} own + {total["extra_stars"]} Marketplace = {total["total_stars"]} stars; '
          f'{changed} source files changed' if changed else 'OK star counts and scope unchanged; no files changed')


if __name__ == '__main__':
    main()
