"""Plex bio mount and a larger, scoped total-project-stars footer badge."""
import hashlib
from html import escape
import json
from pathlib import Path
from textwrap import wrap
from folio_details import detail_svg

FOLIO = Path(__file__).resolve().parents[1] / 'folio'


def settings():
    return json.loads((FOLIO / 'profile-summary.json').read_text())


def snapshot():
    data = json.loads((FOLIO / 'total-stars.json').read_text())
    config = settings()
    assert data['account'] == config['account']
    assert data['extra_repositories'] == config['extra_repositories']
    assert data['exclude_forks'] == config['exclude_forks'] is True
    repos = data['repositories']
    assert len({r['id'] for r in repos}) == len(repos), 'Duplicate repository in total'
    assert len({r['full_name'].casefold() for r in repos}) == len(repos)
    extras = set(config['extra_repositories'])
    assert extras <= {r['full_name'] for r in repos}
    for repo in repos:
        assert repo['fork'] is False and repo['private'] is False
        assert type(repo['stars']) is int and repo['stars'] >= 0
        assert repo['full_name'].split('/')[0].casefold() == config['account'].casefold() or repo['full_name'] in extras
    own = sum(r['stars'] for r in repos if r['full_name'] not in extras)
    external = sum(r['stars'] for r in repos if r['full_name'] in extras)
    assert data['owned_stars'] == own and data['extra_stars'] == external
    assert data['total_stars'] == own + external == data['badge']['stars']
    source = FOLIO / 'sources/badge-total-stars.svg'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == data['badge']['sha256']
    return data


def bio_svg(mode, wide=True):
    lines = settings()['bio']
    if wide:
        return detail_svg({'title': lines[0], 'caption': lines[1]}, mode,
                          width=1872, title_size=46, caption_size=46, caption_weight=500)
    # Reflow the same words, not a scaled-down desktop paragraph.
    first = wrap(lines[0], width=27, break_long_words=False, break_on_hyphens=False)
    lines = first + wrap(lines[1], width=27, break_long_words=False, break_on_hyphens=False)
    dark = mode == 'dark'
    paper, edge, ink = ('#191c1e', '#353a3d', '#e8e3d9') if dark else ('#e9e7e0', '#c6c5bf', '#262522')
    height = 82 + 54 * len(lines)
    outline = f'M24 16H680V{height - 50}L658 {height - 28}H24Z'
    text = '\n'.join(f'  <text x="352" y="{72 + i * 54}" text-anchor="middle" fill="{ink}" '
                     f'font-family="IBM Plex Sans" font-size="46" font-weight="{600 if i < len(first) else 500}">{escape(line)}</text>'
                     for i, line in enumerate(lines))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1408" height="{height * 2}" viewBox="0 0 704 {height}">
  <title>{escape(' '.join(settings()['bio']))}</title>
  <defs><filter id="float" x="-15%" y="-50%" width="130%" height="210%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="8" /><feOffset dy="10" /></filter></defs>
  <path d="{outline}" fill="#000000" opacity="{'0.48' if dark else '0.19'}" filter="url(#float)" />
  <path d="{outline}" fill="{paper}" stroke="{edge}" stroke-width="1.5" />
{text}
</svg>'''


def summary_html():
    alt = escape(' '.join(settings()['bio']), quote=True)
    lines = sum(len(wrap(line, width=27, break_long_words=False, break_on_hyphens=False)) for line in settings()['bio'])
    height = round((82 + 54 * lines) * 280 / 704)
    return ('<p align="center"><picture>'
            '<source media="(min-width: 1280px) and (prefers-color-scheme: dark)" srcset="./assets/bio-wide-dark.png" width="744" height="76" />'
            '<source media="(min-width: 1280px) and (prefers-color-scheme: light)" srcset="./assets/bio-wide-light.png" width="744" height="76" />'
            '<source media="(prefers-color-scheme: dark)" srcset="./assets/bio-narrow-dark.png" />'
            f'<img src="./assets/bio-narrow-light.png" width="280" height="{height}" alt="{alt}" />'
            '</picture></p>')


def total_badge_html():
    config, data = settings(), snapshot()
    stamp = data['fetched_at'][:10]
    alt = f"Total project stars: {data['total_stars']:,}; public non-fork repositories + Omarchy Plugin Marketplace; checked {stamp}"
    note = f"Public repositories + Omarchy Plugin Marketplace. Forks excluded. Snapshot: {stamp}. Stars per project, not unique people."
    return (f'<p align="center"><a href="https://github.com/{config["account"]}?tab=repositories" title="{escape(note, quote=True)}">'
            '<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/total-stars-dark.png" />'
            f'<img src="./assets/total-stars-light.png" width="{round((data["badge"]["width"] + 24) * 44 / 36)}" height="44" '
            f'alt="{escape(alt, quote=True)}" /></picture></a></p>')
