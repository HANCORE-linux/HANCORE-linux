"""Self-contained image exports: frozen card pixels, vector-only badge lettering.

PNG exports remain as regression references. Public SVGs embed their background
pixels and only redraw the badge's original glyph outlines at browser resolution.
No browser font, remote resource, script, or new build dependency is needed.
"""
import base64
from copy import deepcopy
import re
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from folio_badges import BADGE_FONT, badge_environment
from folio_vectors import FOLIO, SVG

NS = {'s': SVG}
HREF = '{http://www.w3.org/1999/xlink}href'
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')


def render(root, env, output_format='png'):
    return subprocess.check_output(['rsvg-convert', '-f', output_format],
                                   input=ET.tostring(root), env=env)


def png_uri(data):
    assert data.startswith(b'\x89PNG\r\n\x1a\n')
    return 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')


def badge_layers(source, env):
    matched = subprocess.check_output(['fc-match', '-f', '%{file}', 'Liberation Sans'], env=env, text=True)
    assert Path(matched).resolve() == BADGE_FONT.resolve(), 'Badge outline font fallback'
    original = ET.parse(source).getroot()
    background, lettering = deepcopy(original), deepcopy(original)
    for parent in background.iter():
        for child in list(parent):
            if child.tag == f'{{{SVG}}}text':
                parent.remove(child)
    # Keep the exact text coordinates/transforms and clipping. Remove only the
    # badge face/shadow from the outline pass, never stroke or embolden glyphs.
    for parent in lettering.iter():
        for child in list(parent):
            if child.tag in (f'{{{SVG}}}path', f'{{{SVG}}}rect') and parent.tag != f'{{{SVG}}}clipPath':
                parent.remove(child)
    glyphs = ET.fromstring(render(lettering, env, 'svg'))
    assert glyphs.find('.//s:text', NS) is None
    assert glyphs.find('.//s:image', NS) is None
    assert glyphs.findall('.//s:path', NS), 'Missing badge outlines'
    glyphs.set('id', 'badge-glyphs')
    glyphs.set('data-source', str(source.relative_to(FOLIO)))
    return render(background, env), glyphs


def wrap(original, background, glyphs):
    root = ET.Element(f'{{{SVG}}}svg', {key: original.get(key) for key in ('width', 'height', 'viewBox')})
    # README dimensions are rounded (248×196 / 396×312). Match the previous
    # bitmap's axis scaling, rather than introducing SVG letterboxing.
    root.set('preserveAspectRatio', 'none')
    for tag in ('title', 'desc'):
        child = original.find(f's:{tag}', NS)
        if child is not None:
            root.append(deepcopy(child))
    _, _, width, height = original.get('viewBox').split()
    ET.SubElement(root, f'{{{SVG}}}image', {'id': 'card-pixels', HREF: png_uri(background),
                                         'width': width, 'height': height})
    root.append(glyphs)
    return root


def write_public(root, output):
    """Only inert, self-contained SVGs can enter public image directories."""
    validate_public(root)
    content = '\n'.join(line.rstrip() for line in ET.tostring(root, encoding='unicode').splitlines()) + '\n'
    assert len(content.encode()) < 3_500_000, f'Unexpectedly large SVG: {output}'
    output.write_text(content)


def validate_public(root):
    allowed = {'svg', 'title', 'desc', 'defs', 'g', 'path', 'rect', 'clipPath', 'symbol', 'use', 'image'}
    ids = {node.get('id') for node in root.iter() if node.get('id')}
    for node in root.iter():
        assert node.tag in {f'{{{SVG}}}{tag}' for tag in allowed}, node.tag
        for key, value in node.attrib.items():
            assert not key.rsplit('}', 1)[-1].startswith('on')
            assert 'font-' not in key and key != 'filter', 'Public lettering must be static outlines'
            if key in (HREF, 'href'):
                if node.tag == f'{{{SVG}}}image':
                    assert value.startswith('data:image/png;base64,'), 'External image dependency'
                else:
                    assert value.startswith('#') and value[1:] in ids, 'External or broken vector reference'
            if 'url(' in value:
                references = re.findall(r'url\(#([^)]+)\)', value)
                assert len(references) == value.count('url(') and all(ref in ids for ref in references), 'External vector resource'
    assert root.find('.//s:svg[@id="badge-glyphs"]', NS) is not None


def publish_theme(source, badge_source, output, env):
    original = ET.parse(source).getroot()
    background_card = deepcopy(original)
    screenshot, badge = background_card.findall('s:image', NS)
    background, glyphs = badge_layers(badge_source, env)
    path = (FOLIO / screenshot.get(HREF)).resolve()
    assert path.is_relative_to(FOLIO) and path.suffix == '.png'
    screenshot.set(HREF, png_uri(path.read_bytes()))
    badge.set(HREF, png_uri(background))
    for key in ('x', 'y', 'width', 'height'):
        glyphs.set(key, badge.get(key))
    write_public(wrap(original, render(background_card, env), glyphs), output)


def publish_total(source, output):
    original = ET.parse(source).getroot()
    with badge_environment() as env:
        background, glyphs = badge_layers(source, env)
    _, _, width, height = original.get('viewBox').split()
    glyphs.set('width', width)
    glyphs.set('height', height)
    write_public(wrap(original, background, glyphs), output)


def publish_connected(source, theme_source, output):
    root = ET.parse(source).getroot()
    root.set('preserveAspectRatio', 'none')
    image = root.find('s:image', NS)
    theme = ET.parse(theme_source).getroot()
    for key in ('x', 'y', 'width', 'height'):
        theme.set(key, image.get(key))
    root.insert(list(root).index(image), theme)
    root.remove(image)
    write_public(root, output)
