"""Dated Shields source, clipped only at the lower-right corner of its mount."""
from xml.sax.saxutils import escape
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

from folio_vectors import FOLIO, inline_svg

BADGE_FONT = FOLIO / 'type/liberation-sans/LiberationSans-Regular.ttf'
BADGE_FONT_SHA256 = 'baccc64becc3eb7d104b7c84d99f5314a0a1f896e2b3ea6c2f22fc08d2003bee'


@contextmanager
def badge_environment():
    """Use the approved local badge face, independently of host fallback fonts."""
    assert hashlib.sha256(BADGE_FONT.read_bytes()).hexdigest() == BADGE_FONT_SHA256, 'Changed badge font'
    with tempfile.TemporaryDirectory(prefix='hancore-badge-fonts-') as temp:
        cfg = Path(temp) / 'fonts.conf'
        cfg.write_text(f'<?xml version="1.0"?><fontconfig><dir>{escape(str(BADGE_FONT.parent))}</dir><cachedir>{escape(temp)}/cache</cachedir></fontconfig>')
        env = dict(os.environ, FONTCONFIG_FILE=str(cfg))
        matched = subprocess.check_output(['fc-match', '-f', '%{file}', 'Liberation Sans'], env=env, text=True)
        assert Path(matched).resolve() == BADGE_FONT.resolve(), f'Badge font fallback: {matched}'
        yield env


def render_badge(svg, png):
    with badge_environment() as env:
        subprocess.run(['rsvg-convert', str(svg), '-o', str(png)], env=env, check=True)


def badge_svg(slug, record, mode, source):
    width = record['width']
    canvas = width + 24
    opacity = '0.55' if mode == 'dark' else '0.24'
    outline = f'M12 4H{12 + width}V20L{8 + width} 24H12Z'
    vector = inline_svg(source, x=12, y=4, width=width, height=20, font_family='Liberation Sans')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{canvas * 4}" height="144" viewBox="0 0 {canvas} 36">
  <title>GitHub stars — {escape(slug)}: {record['stars']}; dated snapshot</title>
  <defs><filter id="float" x="-25%" y="-50%" width="150%" height="220%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="2.2" /><feOffset dy="3" /></filter><clipPath id="badge-cut"><path d="{outline}" /></clipPath></defs>
  <path d="{outline}" fill="#000000" opacity="{opacity}" filter="url(#float)" />
  <g clip-path="url(#badge-cut)">{vector}</g>
</svg>'''
