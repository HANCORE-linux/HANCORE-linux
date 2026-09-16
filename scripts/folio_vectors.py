"""Keep small, verified SVG assets vector-native until the final rasterization."""
from pathlib import Path
import xml.etree.ElementTree as ET

FOLIO = Path(__file__).resolve().parents[1] / 'folio'
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)


def inline_svg(source, *, x, y, width, height, font_family=None):
    path = (FOLIO / source).resolve()
    if not path.is_relative_to(FOLIO) or path.suffix != '.svg':
        raise ValueError(f'Not a local folio SVG: {source}')
    root = ET.parse(path).getroot()
    if root.tag != f'{{{SVG}}}svg':
        raise ValueError(f'Not an SVG: {source}')
    # These sources are also hash-verified by the callers. Do not introduce an
    # external resource or executable content when embedding their geometry.
    allowed = {'svg', 'g', 'path', 'rect', 'text', 'title', 'defs', 'clipPath'}
    for node in root.iter():
        if node.tag not in {f'{{{SVG}}}{tag}' for tag in allowed}:
            raise ValueError(f'Unsupported vector element in {source}: {node.tag}')
        for key, value in node.attrib.items():
            if key.rsplit('}', 1)[-1].startswith('on') or 'href' in key or key == 'style' or 'url(' in value:
                raise ValueError(f'Unsupported vector attribute in {source}: {key}')
        if font_family and 'font-family' in node.attrib:
            node.set('font-family', font_family)
    root.set('viewBox', root.get('viewBox', f'0 0 {root.attrib["width"]} {root.attrib["height"]}'))
    root.attrib.update(x=str(x), y=str(y), width=str(width), height=str(height))
    root.set('data-source', source)
    return ET.tostring(root, encoding='unicode')
