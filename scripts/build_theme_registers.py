#!/usr/bin/env python3
"""Build the complete chamfered theme collection and retain the old identity study."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from build_folio import ROOT, FOLIO, INK, checksum, popular_works, theme_url
from folio_register import register_svg, identity_svg, THEME_LABELS, contrast
from folio_badges import badge_svg, render_badge, BADGE_FONT
from folio_archive_routes import kinds, height_px, slice_svg, head_svg, head_geometry
from folio_badge_delivery import publish_theme, publish_connected
from folio_connections import WIDE_MIN
from folio_labels import label_picture, labels
from refresh_folio_badges import fetch as fetch_badge

COLLECTION = FOLIO / 'collection'
MANIFEST = COLLECTION / 'provenance.json'


def themes():
    return sorted(json.loads((ROOT / 'data/themes.json').read_text()), key=lambda t: t['name'].casefold())


def fetch_sources():
    popular = {w['theme_slug'] for w in popular_works()}
    def fetch(theme):
        slug = theme['slug']
        url = f'https://raw.githubusercontent.com/HANCORE-linux/omarchy-{slug}-theme/HEAD/preview.png'
        with urlopen(Request(url, headers={'User-Agent': 'HANCORE-profile-preview'}), timeout=40) as response:
            data = response.read(25_000_001)
        assert len(data) <= 25_000_000 and data[:8] == b'\x89PNG\r\n\x1a\n', slug
        width, height = (int.from_bytes(data[i:i+4], 'big') for i in (16, 20))
        assert width >= 1000 and height >= 600 and abs(width/height-16/9) < .01, (slug, width, height)
        _, badge, record = fetch_badge({'theme_slug': slug})
        return slug, data, badge, {'url': url, 'width': width, 'height': height, 'badge': record}
    with ThreadPoolExecutor(max_workers=5) as pool:
        fetched = list(pool.map(fetch, [t for t in themes() if t['slug'] not in popular]))
    (COLLECTION / 'sources').mkdir(parents=True, exist_ok=True)
    records = {}
    for slug, data, badge, record in fetched:
        source = COLLECTION / 'sources' / f'{slug}.png'
        source.write_bytes(data)
        (COLLECTION / 'sources' / f'badge-{slug}.svg').write_bytes(badge)
        record['sha256'] = checksum(source)
        records[slug] = record
    (COLLECTION / 'sources.json').write_text(json.dumps({'fetched_at': datetime.now(timezone.utc).isoformat(), 'themes': records}, indent=2) + '\n')
    print(f'OK fetched {len(records)} public previews and matching black/orange star badges')


def picture(theme, width=396, prefix='./collection/assets/', connected=None):
    slug, name = theme['slug'], theme['name']
    snapshot = json.loads((FOLIO / 'badge-snapshot.json').read_text())
    if slug in snapshot['badges']:
        badge, stamp = snapshot['badges'][slug], snapshot['fetched_at'][:10]
    else:
        source = json.loads((COLLECTION / 'sources.json').read_text())
        badge, stamp = source['themes'][slug]['badge'], source.get('badges_fetched_at', source['fetched_at'])[:10]
    status = f'{THEME_LABELS[slug]}; ' if slug in THEME_LABELS else ''
    alt = escape(f'{name} — {status}full desktop preview; exact ANSI colors 00–07, left to right; {badge["stars"]} GitHub stars, checked {stamp}', {'"': '&quot;'})
    wide = align = ''
    plain, height = f'{prefix}{slug}', round(width * 492 / 624)
    if connected:
        # Wide views swap in the routed card; narrow views keep the same spacing
        # without routes. Top alignment joins the rows of the single paragraph.
        wide = ''.join(f'<source media="(min-width: {WIDE_MIN}px) and (prefers-color-scheme: {mode})" srcset="{prefix}connected-{slug}-{mode}.svg" width="{width}" height="{connected}" />' for mode in INK)
        plain, height, align = f'{prefix}spaced-{slug}', height_px('blank'), ' align="top"'
    return f'<a href="{theme_url(slug)}"><picture>{wide}<source media="(prefers-color-scheme: dark)" srcset="{plain}-dark.svg" /><img src="{plain}-light.svg" alt="{alt}" title="Star snapshot · {stamp}" width="{width}" height="{height}"{align} /></picture></a>'


def build():
    records = json.loads((COLLECTION / 'sources.json').read_text())
    snapshot = json.loads((FOLIO / 'badge-snapshot.json').read_text())
    palettes = json.loads((FOLIO / 'palettes.json').read_text())['themes']
    (COLLECTION / 'assets').mkdir(parents=True, exist_ok=True)
    outputs = []
    with tempfile.TemporaryDirectory(prefix='hancore-series-fonts-') as temp:
        cfg = Path(temp) / 'fonts.conf'
        cfg.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>{escape(str(FOLIO / "type"))}</dir><cachedir>{escape(temp)}/cache</cachedir></fontconfig>')
        env = dict(os.environ, FONTCONFIG_FILE=str(cfg))
        assert 'IBM Plex Sans' in subprocess.check_output(['fc-match', '-f', '%{family}', 'IBM Plex Sans'], env=env, text=True).split(',')
        for theme in themes():
            slug = theme['slug']
            popular = slug in snapshot['badges']
            badge = snapshot['badges'][slug] if popular else records['themes'][slug]['badge']
            source = f'sources/popular-{slug}.png' if popular else f'collection/sources/{slug}.png'
            if not popular:
                assert checksum(FOLIO / source) == records['themes'][slug]['sha256']
                assert checksum(COLLECTION / f'sources/badge-{slug}.svg') == badge['sha256']
            for mode in INK:
                badge_source = f'assets/badge-{slug}-{mode}.png'
                if not popular:
                    badge_source = f'collection/assets/badge-{slug}-{mode}.png'
                    content = badge_svg(slug, badge, mode, f'collection/sources/badge-{slug}.svg')
                    svg = FOLIO / f'series-badge-{slug}-{mode}.svg'
                    svg.write_text(content)
                    render_badge(svg, FOLIO / badge_source)
                    outputs.extend([svg, FOLIO / badge_source])
                svg = FOLIO / f'series-{slug}-{mode}.svg'
                png = COLLECTION / f'assets/{slug}-{mode}.png'
                svg.write_text(register_svg(mode, palettes[slug]['colors'], badge, slug=slug, name=theme['name'], source=source, badge_source=badge_source))
                subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], env=env, check=True)
                outputs.extend([svg, png])
                public_svg = png.with_suffix('.svg')
                badge_svg_path = FOLIO / f'{"badge" if popular else "series-badge"}-{slug}-{mode}.svg'
                publish_theme(svg, badge_svg_path, public_svg, env)
                outputs.append(public_svg)
        ordered = themes()
        title = ' — '.join(labels(len(ordered))['archive'])
        for row, kind in enumerate(kinds(len(ordered))):
            for column, theme in enumerate(ordered[2 * row:2 * row + 2]):
                for mode in INK:
                    svg = FOLIO / f'connected-archive-{theme["slug"]}-{mode}.svg'
                    public_svg = COLLECTION / f'assets/connected-{theme["slug"]}-{mode}.svg'
                    svg.write_text(slice_svg(theme['slug'], theme['name'], mode, kind, column))
                    publish_connected(svg, COLLECTION / f'assets/{theme["slug"]}-{mode}.svg', public_svg)
                    outputs.extend([svg, public_svg])
                    svg = FOLIO / f'spaced-archive-{theme["slug"]}-{mode}.svg'
                    public_svg = COLLECTION / f'assets/spaced-{theme["slug"]}-{mode}.svg'
                    svg.write_text(slice_svg(theme['slug'], theme['name'], mode, 'blank'))
                    publish_connected(svg, COLLECTION / f'assets/{theme["slug"]}-{mode}.svg', public_svg)
                    outputs.extend([svg, public_svg])
        for mode in INK:
            svg = FOLIO / f'connected-archive-head-{mode}.svg'
            png = FOLIO / f'assets/connected-archive-head-{mode}.png'
            svg.write_text(head_svg(mode, title))
            subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], check=True)
            outputs.extend([svg, png])
        for mode, ink in INK.items():
            svg = FOLIO / f'series-identity-{mode}.svg'
            png = COLLECTION / f'assets/identity-{mode}.png'
            svg.write_text(identity_svg(ink))
            subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], check=True)
            outputs.extend([svg, png])
    # One paragraph: explicit breaks join the heading and rows without gaps, so
    # wide-view routes meet at image edges; narrow views fall back to plain cards.
    head = label_picture('archive', len(ordered), connected=('./assets/connected-archive-head', 2 * 396, head_geometry()[-1]))
    rows = [''.join(picture(t, connected=height_px(kind)) for t in ordered[2 * row:2 * row + 2])
            for row, kind in enumerate(kinds(len(ordered)))]
    archive = FOLIO / 'THEMES.md'
    archive.write_text('<!-- Generated by scripts/build_theme_registers.py. Native GitHub Markdown. -->\n'
                       '<p><a href="https://github.com/HANCORE-linux">← Back to profile</a></p>\n\n'
                       + '<p align="center">' + head + '<br />\n' + '<br />\n'.join(rows) + '</p>'
                       + '\n\n<p><a href="https://github.com/HANCORE-linux">← Back to profile</a></p>\n')
    outputs.append(archive)
    sources = [Path(__file__).resolve(), ROOT / 'scripts/folio_register.py', ROOT / 'scripts/folio_badges.py', ROOT / 'scripts/folio_labels.py', ROOT / 'scripts/folio_archive_routes.py', ROOT / 'scripts/folio_connections.py', ROOT / 'data/themes.json',
               *sorted((FOLIO / 'assets').glob('label-archive-*.png')),
               ROOT / 'scripts/folio_vectors.py', ROOT / 'scripts/folio_badge_delivery.py', BADGE_FONT,
               FOLIO / 'badge-snapshot.json', FOLIO / 'palettes.json', COLLECTION / 'sources.json',
               *sorted((COLLECTION / 'sources').glob('*')), *sorted((FOLIO / 'assets').glob('badge-*.png')),
               *sorted((FOLIO / 'sources').glob('popular-*.png')), FOLIO / 'type/plex-sans/IBMPlexSans.ttf']
    MANIFEST.write_text(json.dumps({'inputs': {str(p.relative_to(ROOT)): checksum(p) for p in sources},
                                    'outputs': {str(p.relative_to(ROOT)): checksum(p) for p in outputs}}, indent=2) + '\n')
    print('OK 28 theme mounts in dark/light, separate two-column GitHub archive, historical identity study')


def check():
    manifest = json.loads(MANIFEST.read_text())
    for section in ('inputs', 'outputs'):
        for name, digest in manifest[section].items():
            assert checksum(ROOT / name) == digest, f'Stale collection {section}: {name}'
    palettes = json.loads((FOLIO / 'palettes.json').read_text())['themes']
    ns = {'s': 'http://www.w3.org/2000/svg'}
    for theme in themes():
        slug = theme['slug']
        for mode in INK:
            svg = ET.parse(FOLIO / f'series-{slug}-{mode}.svg').getroot()
            swatches = svg.findall('.//s:g[@id="ansi-palette"]/s:rect', ns)[:8]
            assert [r.get('fill') for r in swatches] == palettes[slug]['colors']
            assert all(r.get('width') == '22' and r.get('height') == '30' for r in swatches)
            shot = svg.find('s:image', ns)
            assert shot.get('width') == '560' and shot.get('height') == '315' and 'filter' not in shot.attrib
            assert shot.get('x') == '32' and shot.get('y') == '24'
            paths = svg.findall('s:path', ns)
            assert len(paths) == 2, 'Only one backing shadow and one neutral mount; no register tabs'
            assert paths[1].get('d') == 'M24 16H600V450L578 472H24Z'
            project = ET.parse(FOLIO / f'shibumi-{mode}.svg').getroot()
            project_mount = project.findall('s:path', ns)[1]
            assert all(paths[1].get(key) == project_mount.get(key) for key in ('fill', 'stroke', 'stroke-width')), 'Theme frame differs from the project cards'
            assert ET.tostring(svg.find('s:defs/s:filter', ns)).strip() == ET.tostring(project.find('s:defs/s:filter', ns)).strip(), 'Different shadow geometry'
            caption = svg.find('s:text', ns)
            assert caption.text == theme['name'] and caption.get('x') == '44' and caption.get('y') == '382'
            assert caption.get('text-anchor', 'start') == 'start'
            assert contrast(paths[1].get('fill'), caption.get('fill')) >= 4.5
            assert caption.get('font-family') == 'IBM Plex Sans'
            assert all(rect.get('x') == str(44 + i * 22) and rect.get('y') == '420' for i, rect in enumerate(swatches))
            status = svg.find('s:g[@id="new-badge"]', ns)
            assert (status is not None) == (slug in THEME_LABELS), f'Wrong NEW badge: {slug}'
            if status is not None:
                label = status.find('s:text', ns)
                rect = status.findall('s:rect', ns)[1]
                assert label.text == THEME_LABELS[slug] == 'NEW'
                assert rect.get('fill') == '#df6124' and contrast(rect.get('fill'), label.get('fill')) >= 4.5
                assert int(rect.get('y')) >= int(shot.get('y')) + int(shot.get('height')), 'NEW overlaps the desktop'
                assert int(rect.get('y')) + int(rect.get('height')) < 420, 'NEW overlaps the palette'
                assert [rect.get(key) for key in ('x', 'y', 'width', 'height')] == ['520', '374', '60', '24'], 'NEW must be right-aligned above the star badge'
                assert int(rect.get('x')) + int(rect.get('width')) == 580
                stars_image = svg.findall('s:image', ns)[1]
                assert abs(float(stars_image.get('x')) + float(stars_image.get('width')) - 12 * 624 / 248 - 580) < 1e-6
                assert float(stars_image.get('y')) + 4 * 624 / 248 - 398 >= 12, 'Leave a visible gap above stars'
            badge_path = FOLIO / f'badge-{slug}-{mode}.svg'
            if not badge_path.exists():
                badge_path = FOLIO / f'series-badge-{slug}-{mode}.svg'
            badge_svg_root = ET.parse(badge_path).getroot()
            badge_group = badge_svg_root.find('s:g', ns)
            assert badge_group.get('clip-path') == 'url(#badge-cut)'
            badge_image = badge_group.find('s:svg', ns)
            assert badge_svg_root.find('.//s:image', ns) is None, 'Badges must stay vector-native'
            width = int(badge_image.get('width'))
            cut = badge_svg_root.find('.//s:clipPath[@id="badge-cut"]/s:path', ns)
            assert cut.get('d') == f'M12 4H{12 + width}V20L{8 + width} 24H12Z', 'Badge corner must be a 45-degree cut'
            png = COLLECTION / f'assets/{slug}-{mode}.png'
            data = png.read_bytes()
            assert int.from_bytes(data[16:20], 'big') == 1248 and int.from_bytes(data[20:24], 'big') == 984
            assert len(data) < 2_500_000, (slug, len(data))
            for crop in ('1120x630+64+48', '290x90+864+826'):
                spread = subprocess.check_output([shutil.which('magick') or 'convert', str(png), '-crop', crop, '+repage', '-format', '%[standard-deviation]', 'info:'], text=True)
                assert float(spread) > 1000, f'Missing screenshot/badge: {slug}, {crop}'
    archive = (FOLIO / 'THEMES.md').read_text()
    assert archive.count('width="396" height="335" align="top"') == 28 and archive.count('/connected-') == 2 * 28 + 2 and archive.count('/spaced-') == 2 * 28
    for theme in themes():
        for mode in INK:
            routed = ET.parse(COLLECTION / f'assets/connected-{theme["slug"]}-{mode}.svg').getroot()
            assert routed.find('s:svg[@id="badge-glyphs"]', ns) is None and routed.find('s:svg//s:svg[@id="badge-glyphs"]', ns) is not None, 'Routed card must embed the vector-lettered card'
            assert routed.findall('s:path', ns)[0].get('d').startswith('M312 0V'), 'Route must enter at the upper edge'
    assert (FOLIO / 'THEMES.md').read_text().count('— NEW;') == 1
    print('OK all 56 theme mounts match project frames; exact palettes, unfiltered desktops, captions and visible badges')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.fetch:
        fetch_sources()
    elif args.check:
        check()
    else:
        build()
