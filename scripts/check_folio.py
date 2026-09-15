#!/usr/bin/env python3
"""Check independent README assets, provenance, links and preview freshness."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import struct
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from build_folio import WORKS, PROJECT_CROPS, popular_works, theme_url, identities, badge_url
from folio_details import detail_cards, SOCIALS, SHIPS_WITH_ADVANCE, ACCENT_INK
from folio_labels import labels, label_dimensions
from folio_connections import specs as connection_specs, connected_picture
from folio_register import contrast
from folio_summary import summary_html, snapshot as total_snapshot, settings as summary_settings

ROOT = Path(__file__).resolve().parents[1]


class Check(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = 0
        self.links = []
        self.tables = 0
        self.details = 0
        self.badges = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        assert tag not in {'script','style','iframe','video'}, tag
        assert not ({'style','class','id'} & attrs.keys()), attrs
        assert not any(key.startswith('on') for key in attrs), attrs
        if tag == 'table':
            self.tables += 1
        if tag == 'td':
            assert attrs.get('align') == 'left' and attrs.get('valign') == 'middle', attrs
        if tag == 'details':
            self.details += 1
            assert 'open' not in attrs, 'The complete theme index must start collapsed'
        if tag == 'img':
            self.images += 1
            assert attrs.get('alt') and attrs.get('height')
            if attrs['src'].startswith('./assets/badge-'):
                assert attrs['height'] == '36' and attrs.get('width')
                assert 'checked ' in attrs['alt'] and attrs['title'].startswith('Star snapshot')
                self.badges.append(attrs['src'])
            else:
                assert attrs.get('width')
        if tag == 'a':
            self.links.append(attrs['href'])
        for key in ['src','srcset','href']:
            if key not in attrs:
                continue
            value = attrs[key]
            if urlsplit(value).scheme:
                assert value.startswith('https://'), value
            else:
                target = (ROOT / 'folio' / value).resolve()
                assert target.is_relative_to(ROOT) and target.is_file(), value


def check_project_line():
    ns = {'s': 'http://www.w3.org/2000/svg'}
    for mode in ('dark', 'light'):
        wordmark = ET.parse(ROOT / f'folio/wordmark-cut-{mode}.svg').getroot()
        assert len(wordmark.findall('s:path', ns)) == 1, 'Only the H is custom geometry'
        assert wordmark.find('s:text', ns).text == 'ANCORE'
        for work in WORKS:
            if work['slug'] not in PROJECT_CROPS:
                continue
            slug = work['slug']
            card = ET.parse(ROOT / f'folio/{slug}-{mode}.svg').getroot()
            assert card.attrib['viewBox'] == '0 0 624 700'
            assert struct.unpack('>II', (ROOT / f'folio/assets/{slug}-{mode}.png').read_bytes()[16:24]) == (1248, 1400)
            caption = card.find('s:text', ns)
            assert caption.text == work['name']
            assert caption.attrib['x'] == '312' and caption.attrib['text-anchor'] == 'middle'
            assert caption.attrib['font-family'] == 'IBM Plex Sans'
            assert caption.attrib['font-size'] == '34' and caption.attrib['font-weight'] == '500'
            assert caption.get('fill') == ('#e8e3d9' if mode == 'dark' else '#262522')
            mount = card.findall('s:path', ns)[1]
            assert contrast(mount.get('fill'), caption.get('fill')) >= 4.5
            viewport = card.find('s:svg', ns)
            crop = list(map(float, viewport.attrib['viewBox'].split()))
            assert crop == PROJECT_CROPS[slug]
            assert abs(float(viewport.attrib['width']) / float(viewport.attrib['height']) - crop[2] / crop[3]) < 1e-6
            assert viewport.attrib['overflow'] == 'hidden'
            image = viewport.find('s:image', ns)
            assert image.attrib['{http://www.w3.org/1999/xlink}href'] == f'sources/{slug}.png'
            assert len(card.findall('.//s:image', ns)) == 1
            filtered = [node for node in card.iter() if 'filter' in node.attrib]
            assert len(filtered) == 1 and filtered[0].tag == '{http://www.w3.org/2000/svg}path', 'Shadow must never blur the screenshot'
    print('OK custom H, three 2× project mounts, centered Plex labels and unfiltered original source viewports')


def check_logo():
    ns = {'s': 'http://www.w3.org/2000/svg'}
    for mode in ('dark', 'light'):
        logo = ET.parse(ROOT / f'folio/wordmark-logo-{mode}.svg').getroot()
        mark = ET.parse(ROOT / f'folio/mark-logo-{mode}.svg').getroot()
        assert len(logo.findall('.//s:path', ns)) == 7
        assert len(mark.findall('.//s:path', ns)) == 1
        assert mark.find('.//s:path', ns).get('d') == logo.find('.//s:path', ns).get('d')
        for asset in (logo, mark):
            assert not asset.findall('.//s:text', ns) and not asset.findall('.//s:image', ns), 'Logo must be self-contained paths, not a font or raster'
            assert not asset.findall('.//s:filter', ns)
            assert asset.find('s:g', ns).get('fill-rule') == 'evenodd'
        assert struct.unpack('>II', (ROOT / f'folio/assets/wordmark-logo-{mode}.png').read_bytes()[16:24]) == (1056, 256)
        assert struct.unpack('>II', (ROOT / f'folio/assets/mark-logo-{mode}.png').read_bytes()[16:24]) == (512, 512)
    print('OK self-contained HANCORE vector logo and matching standalone H, dark/light PNG exports')
    for mode in ('dark', 'light'):
        mark = ET.parse(ROOT / f'folio/mark-core-{mode}.svg').getroot()
        lockup = ET.parse(ROOT / f'folio/wordmark-core-{mode}.svg').getroot()
        assert not mark.findall('.//s:text', ns), 'The signet must work without any wordmark'
        paths = mark.findall('.//s:path', ns)
        assert len(paths) == 2
        assert [p.get('d') for p in paths] == [p.get('d') for p in lockup.findall('.//s:path', ns)]
        assert lockup.find('s:text', ns).text == 'HANCORE'
        assert lockup.find('s:text', ns).get('fill') == mark.find('s:g', ns).get('fill') == '#df6124'
        assert struct.unpack('>II', (ROOT / f'folio/assets/wordmark-core-{mode}.png').read_bytes()[16:24]) == (880, 352)
    print('OK independent orange HC signet and matching orange HANCORE name')


def check_detail_line(themes, highlights):
    ns = {'s': 'http://www.w3.org/2000/svg'}
    cards = detail_cards(themes, highlights)
    assert len(cards) == 6
    for mode in ('dark', 'light'):
        project = ET.parse(ROOT / f'folio/shibumi-{mode}.svg').getroot().findall('s:path', ns)[1]
        for card in cards:
            svg = ET.parse(ROOT / f'folio/info-{card["slug"]}-{mode}.svg').getroot()
            mount = svg.findall('s:path', ns)[1]
            assert all(mount.get(key) == project.get(key) for key in ('fill', 'stroke', 'stroke-width'))
            texts = svg.findall('s:text', ns)
            assert texts[0].text == card['title'] and texts[1].text == card['caption']
            assert [t.get('font-size') for t in texts] == ['40', '34']
            assert [t.get('font-weight') for t in texts] == ['600', '500']
            assert all(t.get('text-anchor') == 'middle' and contrast(mount.get('fill'), t.get('fill')) >= 4.5 for t in texts)
            assert texts[0].get('x') == '312'
            expected_ink = ACCENT_INK[mode] if card['group'] == 'index' else ('#e8e3d9' if mode == 'dark' else '#262522')
            assert texts[0].get('fill') == expected_ink, 'Orange title accents belong to the archive only'
            if card.get('brand'):
                brand = svg.find('s:image', ns)
                assert brand.get('{http://www.w3.org/1999/xlink}href') == 'assets/omarchy-wordmark-orange.png'
                left = float(texts[1].get('x')) - SHIPS_WITH_ADVANCE / 2
                right = float(brand.get('x')) + float(brand.get('width'))
                assert abs((left + right) / 2 - 312) < 0.001, 'Combined caption is not centered'
            else:
                assert texts[1].get('x') == '312'
        for slug, label, _ in SOCIALS:
            svg = ET.parse(ROOT / f'folio/social-{slug}-{mode}.svg').getroot()
            assert svg.find('s:title', ns).text == label
            assert not svg.findall('.//s:filter', ns), 'Official social logos are not filtered'
    print('OK six compact info/archive cards, exact orange Omarchy wordmark, two official social icons and original acknowledgements icon')


def check_labels(theme_count):
    ns = {'s': 'http://www.w3.org/2000/svg'}
    for mode, ink, background in [('dark', '#e8e3d9', '#0d1117'), ('light', '#262522', '#ffffff')]:
        for slug, lines in labels(theme_count).items():
            svg = ET.parse(ROOT / f'folio/label-{slug}-{mode}.svg').getroot()
            texts = svg.findall('s:text', ns)
            assert tuple(t.text for t in texts) == lines
            if slug == 'archive':
                mount = svg.findall('s:path', ns)[1]
                assert mount.get('d') == 'M24 16H680V142L658 164H24Z'
                project = ET.parse(ROOT / f'folio/shibumi-{mode}.svg').getroot().findall('s:path', ns)[1]
                assert all(mount.get(key) == project.get(key) for key in ('fill', 'stroke', 'stroke-width'))
                assert svg.find('s:defs/s:filter', ns).get('id') == 'float'
                assert all(t.get('font-family') == 'IBM Plex Sans' and t.get('font-size') == '40' and t.get('font-weight') == '600' for t in texts)
                assert all(t.get('x') == '352' and t.get('text-anchor') == 'middle' for t in texts)
                assert texts[0].get('fill') == ACCENT_INK[mode]
                assert texts[1].get('fill') == ('#bfc4c9' if mode == 'dark' else '#50565b')
                assert all(contrast(mount.get('fill'), t.get('fill')) >= 4.5 for t in texts)
                assert label_dimensions(slug, theme_count) == (280, 76)
                assert struct.unpack('>II', (ROOT / f'folio/assets/label-{slug}-{mode}.png').read_bytes()[16:24]) == (1408, 384)
                continue
            assert all(t.get('font-family') == 'IBM Plex Sans' and t.get('font-size') == '16' and t.get('font-weight') == '600' for t in texts)
            assert all(t.get('fill') == ink for t in texts) and contrast(ink, background) >= 4.5
            assert struct.unpack('>II', (ROOT / f'folio/assets/label-{slug}-{mode}.png').read_bytes()[16:24]) == (992, len(lines) * 112)
    print('OK matching 16 px Plex section labels; centered, shadowed archive tile with orange title and neutral metadata')


def check_connections():
    ns = {'s': 'http://www.w3.org/2000/svg'}
    themes = json.loads((ROOT / 'data/themes.json').read_text())
    highlights = json.loads((ROOT / 'folio/highlights.json').read_text())
    connections = connection_specs(popular_works(), detail_cards(themes, highlights))
    assert len(connections) == 15
    for mode in ('dark', 'light'):
        for spec in connections:
            slug = spec['slug']
            svg = ET.parse(ROOT / f'folio/connected-{slug}-{mode}.svg').getroot()
            assert svg.get('viewBox') == f'0 0 {spec["width"]} {spec["height"]}'
            assert not svg.findall('.//s:filter', ns) and not svg.findall('.//s:text', ns)
            image = svg.find('s:image', ns)
            assert image.get('{http://www.w3.org/1999/xlink}href') == f'{spec["source"]}-{mode}.png'
            assert [image.get(k) for k in ('x', 'y', 'width', 'height')] == [str(spec['x']), str(spec['y']), '624', str(spec['body_height'])]
            assert len(svg.findall('s:path', ns)) == 3
            if spec['kind'] == 'bridge':
                assert svg.findall('s:path', ns)[1].get('d') == '', 'No staggered ticks above Banish and Solitude'
            assert struct.unpack('>II', (ROOT / f'folio/assets/connected-{slug}-{mode}.png').read_bytes()[16:24]) == (spec['width'] * 2, spec['height'] * 2)
    from build_folio import FEATURED
    readme = (ROOT / 'folio/README.md').read_text()
    by_slug = {s['slug']: s for s in connections}
    assert ''.join(connected_picture(by_slug[slug], url, alt) for slug, url, alt in FEATURED) in readme, 'Continuous routes need separate adjacent links without whitespace'
    assert readme.count('align="top"') == 15, 'Native row alignment is required at the joins'
    assert 'info-archive' in by_slug and by_slug['info-archive']['kind'] == 'archive'
    print('OK 15 independently linked slices: projects through highlights, 3×2 themes joined to archive CTA, unchanged card scale')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-only', action='store_true', help='Check publication without local browser/render caches')
    args = parser.parse_args()
    subprocess.run([sys.executable,str(ROOT / 'scripts/build_folio.py'),'--check'],check=True)
    check_project_line()
    check_logo()
    check_connections()
    parsed = Check()
    parsed.feed((ROOT / 'folio/README.md').read_text())
    popular = popular_works()
    assert len(popular) <= 6 and all(work['stars'] > 30 for work in popular)
    assert not parsed.badges, 'Badges belong to the wrapping popular-preview compositions'
    snapshot = json.loads((ROOT / 'folio/badge-snapshot.json').read_text())
    for work in popular:
        slug = work['theme_slug']
        record = snapshot['badges'][slug]
        assert record['url'] == badge_url(slug, record['stars'] if record.get('api_snapshot') else None)
        assert isinstance(snapshot['badges'][slug]['stars'], int)
    themes = json.loads((ROOT / 'data/themes.json').read_text())
    assert parsed.images == 16 + len(popular), parsed.images
    totals = total_snapshot()
    if all(record.get('api_snapshot') for record in snapshot['badges'].values()):
        archive_sources = json.loads((ROOT / 'folio/collection/sources.json').read_text())
        ranking = json.loads((ROOT / 'folio/popular-themes.json').read_text())['star_snapshot']
        repos = {repo['full_name']: repo['stars'] for repo in totals['repositories']}
        for theme in themes:
            slug = theme['slug']
            record = snapshot['badges'].get(slug) or archive_sources['themes'][slug]['badge']
            assert record['stars'] == ranking[slug] == repos[f'HANCORE-linux/omarchy-{slug}-theme'], f'Inconsistent star counts: {slug}'
    assert summary_html() in (ROOT / 'folio/README.md').read_text()
    assert len(summary_settings()['bio']) == 2
    ns = {'s': 'http://www.w3.org/2000/svg'}
    for mode in ('dark', 'light'):
        svg = ET.parse(ROOT / f'folio/total-stars-{mode}.svg').getroot()
        assert svg.find('s:image', ns).get('{http://www.w3.org/1999/xlink}href') == 'sources/badge-total-stars.svg'
        assert svg.find('s:image', ns).get('clip-path') == 'url(#badge-cut)'
        assert svg.find('s:defs/s:filter', ns).get('id') == 'float'
        assert struct.unpack('>II', (ROOT / f'folio/assets/total-stars-{mode}.png').read_bytes()[16:24]) == ((totals['badge']['width'] + 24) * 4, 144)
    check_labels(len(themes))
    highlights = json.loads((ROOT / 'folio/highlights.json').read_text())
    check_detail_line(themes, highlights)
    assert len(parsed.links) == len(popular) + 13, parsed.links
    assert 'https://github.com/HANCORE-linux/waybar-themes' in parsed.links
    assert 'https://github.com/omacom/omarchy-plugin-marketplace' in parsed.links
    assert parsed.tables == 0 and parsed.details == 0, 'The complete archive must be a separate page'
    assert './THEMES.md' in parsed.links
    assert './ACKNOWLEDGEMENTS.md' in parsed.links
    thanks_source = (ROOT / 'folio/ACKNOWLEDGEMENTS.md').read_text()
    thanks = Check()
    thanks.feed(thanks_source)
    assert thanks.images == 1 and len(thanks.links) == 8
    assert thanks_source.count('<li>') == 7
    for name, role in [('Amit', 'Content Creator'), ('OldJobobo', 'Minister of Taste'), ('Miqim', 'Visual Stylist'), ('Bypass', 'Theme-hook-script'), ('bjarneo', 'Aether'), ('Taha', 'Omarchist'), ('DHH', 'Omarchy')]:
        assert f'>{name}</a> / {role}</li>' in thanks_source
    assert 'Credits' not in thanks_source and 'Contributions' not in thanks_source
    archive = Check()
    archive.feed((ROOT / 'folio/THEMES.md').read_text())
    assert archive.images == 28 and len(archive.links) == 29
    assert archive.tables == 0 and archive.details == 0
    assert archive.links.count('https://github.com/HANCORE-linux') == 2
    assert './README.md' not in archive.links
    for theme in themes:
        assert archive.links.count(theme_url(theme['slug'])) == 1, theme['name']
    assert highlights['chat']['url'] in parsed.links
    for _, _, url in SOCIALS:
        assert url in parsed.links
    assert {item['slug'] for item in highlights['included_in_omarchy']} == {'lasthorizon', 'solitude'}
    expected_assets = {f'{slug}-{mode}.png' for slug in ['signature', 'mark-logo', 'mark-core', *[work['slug'] for work in WORKS + popular],
                       *[f'wordmark-{variant["id"]}' for variant in identities()['variants']]]
                       for mode in ['dark', 'light']}
    expected_assets.update(f'badge-{work["theme_slug"]}-{mode}.png' for work in popular for mode in ['dark','light'])
    expected_assets.add('omarchy-wordmark-orange.png')
    expected_assets.update(f'total-stars-{mode}.png' for mode in ('dark', 'light'))
    expected_assets.update(f'palette-{theme["slug"]}.png' for theme in themes)
    expected_assets.update(f'info-{card["slug"]}-{mode}.png' for card in detail_cards(themes, highlights) for mode in ('dark', 'light'))
    expected_assets.update(f'social-{slug}-{mode}.png' for slug, _, _ in SOCIALS for mode in ('dark', 'light'))
    expected_assets.update(f'label-{slug}-{mode}.png' for slug in labels(len(themes)) for mode in ('dark', 'light'))
    expected_assets.update(f'connected-{spec["slug"]}-{mode}.png' for spec in connection_specs(popular, detail_cards(themes, highlights)) for mode in ('dark', 'light'))
    original = (ROOT / 'folio/sources/omarchy-wordmark.svg').read_text()
    assert (ROOT / 'folio/omarchy-wordmark-orange.svg').read_text() == original.replace('fill="#9ece6a"', 'fill="#df6124"')
    assert {p.name for p in (ROOT / 'folio/assets').glob('*.png')} == expected_assets
    if args.assets_only:
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_theme_registers.py'), '--check'], check=True)
        print(f'OK {parsed.images} accessible images, {len(parsed.links)} links, {len(expected_assets)} assets; local rendering not required')
        return
    manifest = json.loads((ROOT / '.review/folio-manifest.json').read_text())
    assert manifest['renderer'].startswith('GitHub Markdown'), 'Preview is not GitHub-rendered'
    for section in ['inputs','outputs']:
        for name, digest in manifest[section].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    pages = json.loads((ROOT / '.review/register-pages-manifest.json').read_text())
    assert len(pages['renderers']) == 4 and all(r.startswith('GitHub Markdown') for r in pages['renderers'])
    for section in ('inputs', 'outputs'):
        for name, digest in pages[section].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_theme_registers.py'), '--check'], check=True)
    print(f'OK {parsed.images} accessible images, top {len(popular)} themes above 30 stars, {len(parsed.links)} links, {len(expected_assets)} assets and fresh GitHub rendering')


if __name__ == '__main__':
    main()
