"""Original HANCORE logo geometry. No font dependency or borrowed logo artwork."""
from xml.sax.saxutils import escape

BRAND_ORANGE = '#df6124'
# Two interlocking, original HC shapes. The shared crossbar is also a connection.
# These are symbol geometry, independent of the HANCORE name underneath.
CORE_SHAPES = [
    'M0 12L12 0H16V32H29L38 23V43L33 48H16V80H0Z',
    'M50 0H88V16H57L50 23V57L57 64H88L72 80H50L34 64V16Z',
]

H = 'M0 0H12V34H33L42 25V0H54V80H42V40L36 46H12V80H0Z'
GLYPHS = [
    (54, H),
    (58, 'M0 80L18 0H40L58 80H46L42 62H16L12 80Z M19 50H39L30 13H28Z'),
    (56, 'M0 80V0H12L44 57V0H56V80H44L12 23V80Z'),
    (54, 'M14 0H54V12H20L12 20V60L20 68H54V80H14L0 66V14Z'),
    (56, 'M0 0H56V66L42 80H0Z M12 12V68H37L44 61V12Z'),
    (59, 'M0 80V0H42L56 14V38L44 50H34L59 80H44L21 51H12V80Z M12 12V39H36L44 31V20L36 12Z'),
    (50, 'M0 0H50V12H12V33H43V45H12V68H50L38 80H0Z'),
]


def logo_svg(ink, *, mark=False):
    """Filled outlines with stepped H, clipped O and matching E terminal."""
    if mark:
        paths = f'<path transform="translate(37 24)" d="{H}" />'
        viewport, size = '0 0 128 128', 'width="512" height="512"'
        title = 'HANCORE — H monogram'
    else:
        x = (528 - sum(width for width, _ in GLYPHS) - 8 * 6) / 2
        paths = []
        for width, glyph in GLYPHS:
            paths.append(f'<path transform="translate({x:g} 24)" d="{glyph}" />')
            x += width + 8
        paths = ''.join(paths)
        viewport, size = '0 0 528 128', 'width="1056" height="256"'
        title = 'HANCORE — original drawn wordmark'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" {size} viewBox="{viewport}" role="img" aria-labelledby="logo-title">
  <title id="logo-title">{title}</title>
  <desc>Original filled vector outlines. Stepped H crossbar and a single cut corner, drawn for HANCORE.</desc>
  <g fill="{escape(ink)}" fill-rule="evenodd">{paths}</g>
</svg>'''


def signet_svg(*, mark=False):
    """Standalone HC signet, or the signet with a quiet orange name below."""
    paths = ''.join(f'<path d="{shape}" />' for shape in CORE_SHAPES)
    if mark:
        size, viewport, position = 'width="512" height="512"', '0 0 128 128', '20 24'
        name = ''
    else:
        size, viewport, position = 'width="880" height="352"', '0 0 440 176', '176 12'
        name = f'<text x="220" y="154" text-anchor="middle" fill="{BRAND_ORANGE}" font-family="IBM Plex Sans" font-weight="600" font-size="40" letter-spacing="2">HANCORE</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" {size} viewBox="{viewport}" role="img" aria-labelledby="core-title">
  <title id="core-title">HANCORE — HC signet{' with name' if not mark else ''}</title>
  <desc>An original interlocking HC symbol with a stepped connection and cut corner. HANCORE orange, #DF6124.</desc>
  <g id="core-symbol" transform="translate({position})" fill="{BRAND_ORANGE}">{paths}</g>
  {name}
</svg>'''
