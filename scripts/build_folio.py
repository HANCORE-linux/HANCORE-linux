#!/usr/bin/env python3
"""Export native SVG compositions of original screenshots, without retouching."""
import argparse
from datetime import datetime
import hashlib
from html import escape as html_escape
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
from xml.sax.saxutils import escape
from urllib.parse import urlencode
from folio_identity import logo_svg, signet_svg
from folio_badges import badge_svg
from folio_details import detail_cards, detail_svg, social_svg, SOCIALS
from folio_labels import labels, label_svg, label_picture
from folio_connections import connected_svg, connected_picture, specs as connection_specs

ROOT = Path(__file__).resolve().parents[1]
FOLIO = ROOT / 'folio'
INK = {'dark': '#e8e3d9', 'light': '#262522'}
WORKS = [
    {'slug': 'shibumi', 'name': 'Shibumi-Shell', 'size': [920, 760], 'crop': [210, 164, 585, 585],
     'origin': 'assets/sources/shibumi-bars.png',
     'url': 'https://raw.githubusercontent.com/HANCORE-linux/Shibumi-Shell/3cb7f6d26df47b0e2d697575e4b42ba48e405c1d/docs/screenshots/shibumi-bars.png'},
    {'slug': 'solitude', 'name': 'Solitude', 'size': [2560, 1440], 'crop': [1420, 80, 1120, 1120],
     'origin': '/home/hancore/Projects/custom-themes/solitude/preview.png',
     'url': 'https://github.com/HANCORE-linux/omarchy-solitude-theme'},
    {'slug': 'omaq', 'name': 'OmaQ · Chat', 'size': [420, 520], 'crop': [-50, 0, 520, 520],
     'origin': 'Public documentation demo screenshot; full frame, centered without retouching.',
     'url': 'https://raw.githubusercontent.com/HANCORE-linux/OmaQ/c011103f962397fd342d3d57705f2f31b87cac84/docs/images/guide/15-direct-chat-overview.png'},
    {'slug': 'banish', 'name': 'Banish', 'size': [2560, 1440], 'crop': [710, 70, 1180, 1180],
     'origin': '/home/hancore/Projects/custom-themes/banish/preview.png',
     'url': 'https://github.com/HANCORE-linux/omarchy-banish-theme'},
    {'slug': 'marketplace', 'name': 'Omarchy-Plugin-Marketplace', 'size': [1153, 699], 'crop': [0, 0, 699, 699],
     'origin': 'Official public repository preview; square detail of the real interface.',
     'url': 'https://raw.githubusercontent.com/omacom/omarchy-plugin-marketplace/main/preview.png'},
    {'slug': 'waybar', 'name': 'Waybar', 'size': [2560, 1440], 'crop': [0, 0, 780, 102], 'layout':'bars',
     'origin': 'Three unchanged published V2.9c/d/e bar crops, using existing verified profile sources.',
     'url': 'https://github.com/HANCORE-linux/waybar-themes'},
    {'slug': 'qs-dots', 'name': 'QS-Dots · Rise', 'size': [2560, 1440], 'crop': [750, 305, 1050, 1050],
     'image': '../assets/sources/rise-carousel.webp',
     'origin': 'Preserved real Rise V1 carousel capture; timestamp unavailable. Not a new V2 screenshot.',
     'url': 'https://github.com/HANCORE-linux/quickshell-dots'},
]
FEATURED = [
    ('shibumi', 'https://github.com/HANCORE-linux/Shibumi-Shell', 'Shibumi-Shell — real bar configuration detail'),
    ('omaq', 'https://github.com/HANCORE-linux/OmaQ', 'OmaQ — chat for Omarchy, public documentation demo'),
    ('marketplace', 'https://github.com/omacom/omarchy-plugin-marketplace', 'Omarchy Plugin Marketplace — official public interface preview detail'),
]
# Original screenshot viewports; no retouching or reconstructed interface content.
PROJECT_CROPS = {
    'shibumi': [205, 165, 595, 480],
    'omaq': [0, 0, 420, 520],
    'marketplace': [12, 0, 750, 690],
}


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    return [ROOT / 'scripts/build_folio.py', ROOT / 'scripts/folio_identity.py', ROOT / 'scripts/folio_badges.py', ROOT / 'scripts/folio_details.py', ROOT / 'scripts/folio_labels.py', ROOT / 'scripts/folio_connections.py', ROOT / 'data/themes.json', FOLIO / 'highlights.json',
            FOLIO / 'social-sources.json', FOLIO / 'sources/kofi-icon.avif', FOLIO / 'ACKNOWLEDGEMENTS.md',
            FOLIO / 'popular-themes.json', FOLIO / 'identity.json',
            FOLIO / 'badge-snapshot.json', *sorted((FOLIO / 'sources').glob('*.svg')),
            FOLIO / 'palettes.json', *sorted((FOLIO / 'sources/palettes').glob('*.toml')),
            ROOT / 'assets/sources/rise-carousel.webp',
            *[ROOT / f'assets/sources/waybar-v29{version}.png' for version in ['c','d','e']],
            *sorted((FOLIO / 'sources').glob('*.png')),
            *sorted((FOLIO / 'type').rglob('*.ttf')), *sorted((FOLIO / 'type').rglob('OFL.txt'))]


def theme_url(slug):
    return f'https://github.com/HANCORE-linux/omarchy-{slug}-theme'


def link(url, name):
    return f'<a href="{html_escape(url, quote=True)}">{html_escape(name)}</a>'


def identities():
    return json.loads((FOLIO / 'identity.json').read_text())


def badge_url(slug):
    identity = identities()
    query = urlencode({'style': identity['badge_style'], 'label': 'stars',
                       'labelColor': identity['badge_label_color'], 'color': identity['badge_color']})
    return f'https://img.shields.io/github/stars/HANCORE-linux/omarchy-{slug}-theme?{query}'


def popular_works():
    config = json.loads((FOLIO / 'popular-themes.json').read_text())
    themes = {theme['slug']: theme for theme in json.loads((ROOT / 'data/themes.json').read_text())}
    stars = config['star_snapshot']
    assert set(stars) == set(themes), 'Every theme must have a verified star count'
    assert config['limit'] == 6 and config['minimum_stars_exclusive'] == 30
    selected = sorted((slug for slug, count in stars.items() if count > 30),
                      key=lambda slug: (-stars[slug], f'omarchy-{slug}-theme'))[:6]
    works = []
    for slug in selected:
        preview = config['previews'][slug]
        source = FOLIO / 'sources' / f'popular-{slug}.png'
        data = source.read_bytes()
        assert hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == preview['git_blob'], f'Changed public source: {slug}'
        works.append({'slug': f'popular-{slug}', 'theme_slug': slug, 'name': themes[slug]['name'],
                      'stars': stars[slug], 'size': [2560, 1440], 'crop': [0, 0, 2560, 1440],
                      'layout': 'landscape', 'origin': f'Public preview.png, git blob {preview["git_blob"]}',
                      'url': f'https://raw.githubusercontent.com/HANCORE-linux/omarchy-{slug}-theme/{preview["branch"]}/preview.png'})
    return works


def readme_content(markdown):
    themes = json.loads((ROOT / 'data/themes.json').read_text())
    by_slug = {theme['slug']: theme for theme in themes}
    highlights = json.loads((FOLIO / 'highlights.json').read_text())
    selected = identities()['selected']
    assert selected in {item['id'] for item in identities()['variants']}
    display_height = next(item for item in identities()['variants'] if item['id'] == selected).get('display_height', 53)
    heading = f'''<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/wordmark-{selected}-dark.png" />
    <img src="./assets/wordmark-{selected}-light.png" alt="HANCORE" width="220" height="{display_height}" />
  </picture>
  <br />
  {label_picture('subtitle', len(themes))}
</p>'''
    details = detail_cards(themes, highlights)
    connections = {s['slug']: s for s in connection_specs(popular_works(), details)}
    project_rows = [''.join(connected_picture(connections[slug], url, alt) for slug, url, alt in FEATURED)]
    for group in ('projects', 'highlights'):
        project_rows.append(''.join(connected_picture(connections[f'info-{card["slug"]}'], card['url'],
            f'{card["title"]} — {card["caption"]}' + (' Omarchy.' if card.get('brand') else ''))
            for card in details if card['group'] == group))
    projects = '<p align="center">' + '<br />'.join(project_rows) + '</p>'
    table = '<!-- Highlight cards are the final row of the connected project group above. -->'
    cells = []
    badge_snapshot = json.loads((FOLIO / 'badge-snapshot.json').read_text())
    for work in popular_works():
        alt = f'{work["name"]} — full desktop preview; exact ANSI colors 00–07, left to right'
        url = theme_url(work['theme_slug'])
        slug = work['theme_slug']
        badge = badge_snapshot['badges'][slug]
        badge_date = badge_snapshot['fetched_at'][:10]
        cells.append(connected_picture(connections[f'theme-{slug}'], url,
            f'{alt}; {badge["stars"]} GitHub stars, checked {badge_date}', f'Star snapshot · {badge_date}'))
    archive = next(card for card in details if card['group'] == 'index')
    archive_picture = connected_picture(connections['info-archive'], archive['url'], f'{archive["title"]} — {archive["caption"]}')
    gallery = '<p align="center">' + label_picture('popular', len(themes)) + '</p>\n\n<p align="center">' + ''.join(cells[:3]) + '<br />' + ''.join(cells[3:]) + '<br />' + archive_picture + '</p>'
    index = '<!-- The archive link is the final node of the connected theme group above. -->'
    footer = '<p align="center">\n' + '\n'.join(f'  <a href="{url}" title="{label}"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/social-{slug}-dark.png" /><img src="./assets/social-{slug}-light.png" alt="{label}" width="44" height="44" /></picture></a>' for slug, label, url in SOCIALS) + '\n</p>'
    for name, body in [('identity', heading), ('projects', projects), ('highlights', table), ('popular-themes', gallery), ('theme-index', index), ('social', footer)]:
        pattern = rf'(<!-- BEGIN GENERATED: {name} -->).*?(<!-- END GENERATED: {name} -->)'
        markdown, count = re.subn(pattern, lambda m: f'{m[1]}\n{body}\n{m[2]}', markdown, flags=re.S)
        assert count == 1, f'Expected one {name} region'
    return markdown


def project_tile(work, ink):
    """A quiet, chamfered mount shared with the register design language."""
    dark = ink == INK['dark']
    paper = '#191c1e' if dark else '#e9e7e0'
    edge = '#353a3d' if dark else '#c6c5bf'
    opacity = '0.48' if dark else '0.19'
    x, y, w, h = PROJECT_CROPS[work['slug']]
    sw, sh = work['size']
    scale = min(560 / w, 560 / h)
    image_w, image_h = w * scale, h * scale
    image_x, image_y = 32 + (560 - image_w) / 2, 24 + (560 - image_h) / 2
    outline = 'M24 16H600V646L578 668H24Z'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1248" height="1400" viewBox="0 0 624 700">
  <title>{escape(work['name'])} — original interface, chamfered project mount</title>
  <defs><filter id="float" x="-15%" y="-15%" width="130%" height="140%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="8" /><feOffset dy="10" /></filter></defs>
  <path d="{outline}" fill="#000000" opacity="{opacity}" filter="url(#float)" />
  <path d="{outline}" fill="{paper}" stroke="{edge}" stroke-width="1.5" />
  <rect x="32" y="24" width="560" height="560" fill="#101213" />
  <svg x="{image_x:.6f}" y="{image_y:.6f}" width="{image_w:.6f}" height="{image_h:.6f}" viewBox="{x} {y} {w} {h}" preserveAspectRatio="xMidYMid meet" overflow="hidden">
    <image xlink:href="sources/{work['slug']}.png" width="{sw}" height="{sh}" />
  </svg>
  <text x="312" y="636" text-anchor="middle" fill="{ink}" font-family="IBM Plex Sans" font-size="34" font-weight="500">{escape(work['name'])}</text>
</svg>'''


def tile(work, ink):
    if work['slug'] in PROJECT_CROPS:
        return project_tile(work, ink)
    x, y, w, h = work['crop']
    sw, sh = work['size']
    caption = identities()['caption']
    caption_style = f'font-family="{escape(caption["family"])}" font-size="{caption["size"]}" font-weight="{caption["weight"]}"'
    # Only the separate backing rectangle is blurred. Screenshot pixels stay sharp.
    opacity = '0.50' if ink == INK['dark'] else '0.20'
    shadow = f'''<defs><filter id="float" x="-15%" y="-15%" width="130%" height="140%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="8" /><feOffset dy="10" /></filter></defs>'''
    if work.get('layout') == 'bars':
        bars = ''.join(f'<svg x="44" y="{145 + i*120}" width="536" height="70" viewBox="{40 if version == "e" else 0} 0 780 102" overflow="hidden"><image xlink:href="../assets/sources/waybar-v29{version}.png" width="{1920 if version == "c" else 2560}" height="{1080 if version == "c" else 1440}" /></svg>' for i,version in enumerate(['c','d','e']))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="624" height="700" viewBox="0 0 624 700"><title>Waybar — three actual bar layout crops</title>{shadow}<rect x="24" y="16" width="576" height="576" fill="#000000" opacity="{opacity}" filter="url(#float)" /><rect x="24" y="16" width="576" height="576" fill="#101213" />{bars}<text x="312" y="659" text-anchor="middle" fill="{ink}" {caption_style}>Waybar</text></svg>'''
    if work.get('layout') == 'landscape':
        mode = 'dark' if ink == INK['dark'] else 'light'
        record = json.loads((FOLIO / 'badge-snapshot.json').read_text())['badges'][work['theme_slug']]
        badge_w = (record['width'] + 24) * 624 / 248
        badge_h = 36 * 624 / 248
        return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="624" height="492" viewBox="0 0 624 492">
  <title>{escape(work['name'])} — full desktop preview</title>
  {shadow}
  <rect x="24" y="16" width="576" height="324" fill="#000000" opacity="{opacity}" filter="url(#float)" />
  <image x="24" y="16" xlink:href="sources/{work['slug']}.png" width="576" height="324" />
  <text x="312" y="391" text-anchor="middle" fill="{ink}" {caption_style}>{escape(work['name'])}</text>
  <image x="{(624-badge_w)/2}" y="402" width="{badge_w}" height="{badge_h}" xlink:href="assets/badge-{work['theme_slug']}-{mode}.png" />
</svg>'''
    shadow_x = 24 + max(0, -x) * 576 / w
    shadow_y = 16 + max(0, -y) * 576 / h
    shadow_w = (min(sw, x+w) - max(0, x)) * 576 / w
    shadow_h = (min(sh, y+h) - max(0, y)) * 576 / h
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="624" height="700" viewBox="0 0 624 700">
  <title>{work['name']} — screenshot detail</title>
  {shadow}
  <rect x="{shadow_x}" y="{shadow_y}" width="{shadow_w}" height="{shadow_h}" fill="#000000" opacity="{opacity}" filter="url(#float)" />
  <svg x="24" y="16" width="576" height="576" viewBox="{x} {y} {w} {h}" overflow="hidden">
    <image xlink:href="{work.get('image', 'sources/' + work['slug'] + '.png')}" width="{sw}" height="{sh}" />
  </svg>
  <text x="312" y="659" text-anchor="middle" fill="{ink}" {caption_style}>{escape(work['name'])}</text>
</svg>'''


def signature(ink):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="528" height="208" viewBox="0 0 264 104">
  <title>hancore</title>
  <text x="132" y="74" text-anchor="middle" fill="{ink}" font-family="Instrument Serif" font-style="italic" font-size="78">hancore</text>
</svg>'''


def shadow_badge(slug, record, mode):
    source = FOLIO / 'sources' / f'badge-{slug}.svg'
    assert checksum(source) == record['sha256'], f'Badge source changed: {slug}'
    assert record['url'] == badge_url(slug), 'Badge source does not match the selected palette'
    return badge_svg(slug, record, mode, f'sources/badge-{slug}.svg')


def wordmark(variant, ink):
    if variant.get('geometry') == 'hc-signet':
        return signet_svg()
    if variant.get('geometry') == 'drawn-logo':
        return logo_svg(ink)
    if variant.get('geometry') == 'custom-h':
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1056" height="256" viewBox="0 0 528 128">
  <title>HANCORE — custom chamfered H with IBM Plex Sans</title>
  <path transform="translate(59 32)" d="M0 0H11V29H34L43 20V0H54V62H43V33L36 40H11V62H0Z" fill="{ink}" />
  <text x="121" y="94" fill="{ink}" font-family="IBM Plex Sans" font-weight="500" font-size="88">ANCORE</text>
</svg>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1056" height="256" viewBox="0 0 528 128">
  <title>HANCORE — {escape(variant['family'])} wordmark study</title>
  <text x="264" y="{variant['baseline']}" text-anchor="middle" fill="{ink}" font-family="{escape(variant['family'])}" font-weight="{variant['weight']}" font-size="{variant['size']}" letter-spacing="{variant['spacing']}">{escape(variant['text'])}</text>
</svg>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest_path = FOLIO / 'provenance.json'
    if args.check:
        manifest = json.loads(manifest_path.read_text())
        for section in ['inputs', 'outputs']:
            for name, digest in manifest[section].items():
                assert checksum(ROOT / name) == digest, f'Stale {section}: {name}'
        markdown = (FOLIO / 'README.md').read_text()
        assert readme_content(markdown) == markdown, 'Stale highlights or theme index'
        print('OK folio source and export hashes')
        return
    outputs = []
    social_sources = json.loads((FOLIO / 'social-sources.json').read_text())
    for source in social_sources['files']:
        assert checksum(FOLIO / source['path']) == source['sha256'], f'Changed social source: {source["path"]}'
    # Official geometry unchanged; paint-only variant in the user's existing accent.
    original = (FOLIO / 'sources/omarchy-wordmark.svg').read_text()
    assert original.count('fill="#9ece6a"') == 1, 'Unexpected official wordmark paint'
    brand_svg = FOLIO / 'omarchy-wordmark-orange.svg'
    brand_svg.write_text(original.replace('fill="#9ece6a"', 'fill="#df6124"'))
    brand_png = FOLIO / 'assets/omarchy-wordmark-orange.png'
    subprocess.run(['rsvg-convert', '--width', '624', str(brand_svg), '-o', str(brand_png)], check=True)
    outputs.extend([brand_svg, brand_png])
    palettes = json.loads((FOLIO / 'palettes.json').read_text())['themes']
    themes = json.loads((ROOT / 'data/themes.json').read_text())
    assert set(palettes) == {theme['slug'] for theme in themes}
    for slug, record in palettes.items():
        source = FOLIO / 'sources/palettes' / f'{slug}.toml'
        assert checksum(source) == record['sha256'], f'Changed palette source: {slug}'
        config = tomllib.loads(source.read_text())
        assert record['colors'] == [config[f'color{i}'] for i in range(8)]
        assert all(re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in record['colors'])
        rects = ''.join(f'<rect x="{i*8}" y="0" width="8" height="12" fill="{color}" />' for i,color in enumerate(record['colors']))
        svg = FOLIO / f'palette-{slug}.svg'
        png = FOLIO / 'assets' / f'palette-{slug}.png'
        svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="48" viewBox="0 0 64 12"><title>{slug}: ANSI colors 0–7</title>{rects}</svg>')
        subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], check=True)
        outputs.extend([svg, png])
    snapshot = json.loads((FOLIO / 'badge-snapshot.json').read_text())
    # Use the system's standard badge font fallback, not the isolated display fonts.
    for work in popular_works():
        slug = work['theme_slug']
        for mode in INK:
            svg = FOLIO / f'badge-{slug}-{mode}.svg'
            png = FOLIO / 'assets' / f'badge-{slug}-{mode}.png'
            svg.write_text(shadow_badge(slug, snapshot['badges'][slug], mode))
            subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], check=True)
            outputs.extend([svg, png])
    works = WORKS + popular_works()
    with tempfile.TemporaryDirectory(prefix='hancore-folio-fonts-') as temp:
        cfg = Path(temp) / 'fonts.conf'
        cfg.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>{escape(str(FOLIO / "type"))}</dir><cachedir>{escape(temp)}/cache</cachedir></fontconfig>')
        env = dict(os.environ, FONTCONFIG_FILE=str(cfg))
        match = subprocess.check_output(['fc-match', '-f', '%{family}', 'Instrument Serif'], env=env, text=True)
        assert match == 'Instrument Serif', f'Font fallback: {match}'
        for style in [*identities()['variants'], identities()['caption']]:
            matched = subprocess.check_output(['fc-match', '-f', '%{family}', style['family']], env=env, text=True)
            assert style['family'] in matched.split(','), f'Font fallback for {style["family"]}: {matched}'
        for mode, ink in INK.items():
            compositions = [('signature', signature(ink)), ('mark-logo', logo_svg(ink, mark=True)), ('mark-core', signet_svg(mark=True)), *[(w['slug'], tile(w, ink)) for w in works],
                            *[(f'label-{slug}', label_svg(lines, ink, slug)) for slug, lines in labels(len(themes)).items()],
                            *[(f'info-{card["slug"]}', detail_svg(card, mode)) for card in detail_cards(themes, json.loads((FOLIO / 'highlights.json').read_text()))],
                            *[(f'social-{slug}', social_svg(slug, mode)) for slug, _, _ in SOCIALS],
                            *[(f'wordmark-{v["id"]}', wordmark(v, ink)) for v in identities()['variants']]]
            for slug, content in compositions:
                svg = FOLIO / f'{slug}-{mode}.svg'
                png = FOLIO / 'assets' / f'{slug}-{mode}.png'
                svg.write_text(content)
                subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], env=env, check=True)
                outputs.extend([svg, png])
    # Theme wrappers must be composed after the current collection exports.
    from build_theme_registers import build
    build()
    for mode in INK:
        for spec in connection_specs(popular_works(), detail_cards(themes, json.loads((FOLIO / 'highlights.json').read_text()))):
            svg = FOLIO / f'connected-{spec["slug"]}-{mode}.svg'
            png = FOLIO / 'assets' / f'connected-{spec["slug"]}-{mode}.png'
            svg.write_text(connected_svg(spec, mode))
            subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], check=True)
            outputs.extend([svg, png])
    manifest = {
        'description': 'Native SVG viewport crops of unchanged screenshot sources; no generative imagery.',
        'works': works,
        'project_crops': PROJECT_CROPS,
        'typeface': 'Original HC signet: independent filled vector shapes, #DF6124. Quiet IBM Plex Sans Semibold HANCORE name below, also #DF6124. Prior drawn-wordmark and H studies preserved as comparisons. IBM Plex Sans project/theme labels. Unmodified upstream fonts, SIL OFL 1.1; licenses in folio/type.',
        'omarchy_wordmark': {'source': 'https://omarchy.org/brand/omarchy-wordmark.svg',
                            'reference': 'https://omarchy.org/brand/', 'change': 'Paint only: #9ece6a to #df6124; geometry unchanged.',
                            'rights': 'Omarchy trademark; all rights reserved by its owner. Not covered by this repository license.'},
        'inputs': {str(p.relative_to(ROOT)): checksum(p) for p in inputs()},
        'outputs': {str(p.relative_to(ROOT)): checksum(p) for p in outputs},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    readme = FOLIO / 'README.md'
    readme.write_text(readme_content(readme.read_text()))
    print(f'OK exported {len(outputs) // 2} base PNGs, highlights and archive link')


if __name__ == '__main__':
    main()
