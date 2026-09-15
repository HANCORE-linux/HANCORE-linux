#!/usr/bin/env python3
"""Fetch a validated public project-star snapshot; never commit or push."""
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET
from folio_summary import FOLIO, settings


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl)[:2] != urlsplit(req.full_url)[:2]:
            raise ValueError('Refusing cross-origin download redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url, limit):
    headers = {'User-Agent': 'HANCORE-profile-stars'}
    assert urlsplit(url).scheme == 'https'
    if urlsplit(url).netloc == 'api.github.com':
        headers.update({'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        if token := os.environ.get('GH_TOKEN'):
            headers['Authorization'] = 'Bearer ' + token
    with build_opener(SameOriginRedirect()).open(Request(url, headers=headers), timeout=30) as response:
        data = response.read(limit + 1)
    assert len(data) <= limit, 'Unexpected response size'
    return data


def repository(raw):
    assert re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', raw['full_name'])
    assert type(raw['id']) is int and raw['id'] > 0
    assert type(raw['stargazers_count']) is int and raw['stargazers_count'] >= 0
    assert raw['private'] is False and type(raw['fork']) is bool
    assert raw['html_url'] == 'https://github.com/' + raw['full_name']
    return {'id': raw['id'], 'full_name': raw['full_name'], 'url': raw['html_url'],
            'stars': raw['stargazers_count'], 'fork': raw['fork'], 'private': raw['private']}


def collect(config):
    assert config['exclude_forks'] is True
    assert re.fullmatch(r'[A-Za-z0-9-]+', config['account'])
    records, excluded, sources = {}, {}, []
    for page in range(1, 21):
        url = f'https://api.github.com/users/{config["account"]}/repos?type=owner&sort=full_name&per_page=100&page={page}'
        rows = json.loads(download(url, 5_000_000))
        assert isinstance(rows, list)
        sources.append(url)
        for raw in rows:
            record = repository(raw)
            assert record['full_name'].split('/')[0].casefold() == config['account'].casefold()
            bucket = excluded if record['fork'] else records
            assert record['id'] not in records and record['id'] not in excluded, 'Unstable pagination: duplicate repository'
            bucket[record['id']] = record
        if len(rows) < 100:
            break
    else:
        raise ValueError('Repository pagination did not finish')
    for name in config['extra_repositories']:
        assert re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', name)
        url = 'https://api.github.com/repos/' + name
        record = repository(json.loads(download(url, 1_000_000)))
        assert record['full_name'] == name and record['fork'] is False
        records[record['id']] = record  # Count a transferred repository only once.
        sources.append(url)
    repos = sorted(records.values(), key=lambda r: r['full_name'].casefold())
    own = sum(r['stars'] for r in repos if r['full_name'] not in config['extra_repositories'])
    extra = sum(r['stars'] for r in repos if r['full_name'] in config['extra_repositories'])
    total = own + extra
    assert len({r['full_name'].casefold() for r in repos}) == len(repos)
    return {'account': config['account'], 'extra_repositories': config['extra_repositories'],
            'exclude_forks': True, 'sources': sources, 'repositories': repos,
            'excluded_forks': sorted(excluded.values(), key=lambda r: r['full_name'].casefold()),
            'owned_stars': own, 'extra_stars': extra, 'total_stars': total}


def prepare():
    config = settings()
    result = collect(config)
    total = result['total_stars']
    count = f'{total:,}'
    url = 'https://img.shields.io/badge/' + quote(config['label'].replace('-', '--'), safe='') + '-' + quote(count, safe='') + '-df6124?' + urlencode({'style': 'flat-square', 'labelColor': '000000'})
    previous_path = FOLIO / 'total-stars.json'
    if previous_path.exists():
        previous = json.loads(previous_path.read_text())
        keys = ('account', 'extra_repositories', 'exclude_forks', 'repositories')
        if all(previous[k] == result[k] for k in keys) and previous['badge']['url'] == url:
            badge = (FOLIO / 'sources/badge-total-stars.svg').read_bytes()
            assert hashlib.sha256(badge).hexdigest() == previous['badge']['sha256']
            return previous, badge
    badge = download(url, 100_000)
    svg = ET.fromstring(badge)
    assert svg.tag == '{http://www.w3.org/2000/svg}svg'
    width = int(svg.attrib['width'])
    assert 80 <= width <= 230 and svg.attrib['height'] == '20'
    texts = [''.join(n.itertext()) for n in svg.iter('{http://www.w3.org/2000/svg}text')]
    assert texts == [config['label'], count], texts
    assert b'#000000' in badge and b'#df6124' in badge
    for node in svg.iter():
        assert node.tag.rsplit('}', 1)[-1] in {'svg', 'g', 'rect', 'text', 'title', 'path', 'defs', 'clipPath'}
        assert not any(key.startswith('on') or 'href' in key for key in node.attrib)
    result.update({'fetched_at': datetime.now(timezone.utc).isoformat(),
              'note': 'Dated public project-star sum, not unique supporters.',
              'badge': {'url': url, 'width': width, 'height': 20, 'stars': total,
                        'sha256': hashlib.sha256(badge).hexdigest()}})
    return result, badge


def main():
    result, badge = prepare()
    # Validate every remote response before replacing either local snapshot.
    (FOLIO / 'sources/badge-total-stars.svg').write_bytes(badge)
    (FOLIO / 'total-stars.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'OK {result["owned_stars"]} own + {result["extra_stars"]} Marketplace = {result["total_stars"]} stars')


if __name__ == '__main__':
    main()
