"""Readable bio and a scoped, dated total-project-stars badge."""
import hashlib
from html import escape
import json
from pathlib import Path

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


def summary_html():
    config, data = settings(), snapshot()
    bio = '<br />'.join(escape(line) for line in config['bio'])
    stamp = data['fetched_at'][:10]
    alt = f"Total project stars: {data['total_stars']:,}; public non-fork repositories + Omarchy Plugin Marketplace; checked {stamp}"
    note = f"Public repositories + Omarchy Plugin Marketplace. Forks excluded. Snapshot: {stamp}. Stars per project, not unique people."
    return (f'<p align="center">{bio}</p>\n\n'
            f'<p align="center"><a href="https://github.com/{config["account"]}?tab=repositories" title="{escape(note, quote=True)}">'
            '<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/total-stars-dark.png" />'
            f'<img src="./assets/total-stars-light.png" width="{data["badge"]["width"] + 24}" height="36" '
            f'alt="{escape(alt, quote=True)}" /></picture></a></p>')
