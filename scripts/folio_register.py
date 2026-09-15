"""GitHub-native theme mounts matching the three featured project cards."""
from xml.sax.saxutils import escape

THEME_LABELS = {'banish': 'NEW'}


def luminance(color):
    values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(v * w for v, w in zip(values, (.2126, .7152, .0722)))


def contrast(a, b):
    a, b = sorted((luminance(a), luminance(b)))
    return (b + .05) / (a + .05)


def register_svg(mode, colors, badge, *, slug='solitude', name='Solitude', source=None, badge_source=None):
    dark = mode == 'dark'
    body = '#191c1e' if dark else '#e9e7e0'
    edge = '#353a3d' if dark else '#c6c5bf'
    ink = '#e8e3d9' if dark else '#262522'
    assert contrast(body, ink) >= 4.5, f'Unreadable theme label: {slug}'
    shadow = '0.48' if dark else '0.19'
    front = 'M24 16H600V450L578 472H24Z'
    swatches = ''.join(f'<rect x="{44 + i * 22}" y="420" width="22" height="30" fill="{color}" />'
                       for i, color in enumerate(colors))
    scale = 624 / 248
    badge_w = (badge['width'] + 24) * scale
    source = source or f'sources/popular-{slug}.png'
    badge_source = badge_source or f'assets/badge-{slug}-{mode}.png'
    status = ''
    if label := THEME_LABELS.get(slug):
        status_shadow = '0.55' if mode == 'dark' else '0.24'
        status = f'''  <g id="new-badge"><title>New theme</title>
    <defs><filter id="new-float" x="-30%" y="-70%" width="160%" height="260%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="1.2" /><feOffset dy="1.5" /></filter><clipPath id="new-caption"><rect x="24" y="339" width="576" height="81" /></clipPath></defs>
    <rect x="520" y="374" width="60" height="24" fill="#000000" opacity="{status_shadow}" filter="url(#new-float)" clip-path="url(#new-caption)" />
    <rect x="520" y="374" width="60" height="24" fill="#df6124" />
    <text x="550" y="392" text-anchor="middle" fill="#000000" font-family="IBM Plex Sans" font-size="18" font-weight="500" letter-spacing="1">{escape(label)}</text>
  </g>
'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1248" height="984" viewBox="0 0 624 492">
  <title>{escape(name)} — chamfered theme mount</title>
  <desc>Full original desktop, exact ANSI colors 0 through 7, and {badge['stars']} GitHub stars from the dated snapshot. Static linked image.</desc>
  <defs>
    <filter id="float" x="-15%" y="-15%" width="130%" height="140%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="8" /><feOffset dy="10" /></filter>
  </defs>
  <path d="{front}" fill="#000000" opacity="{shadow}" filter="url(#float)" />
  <path d="{front}" fill="{body}" stroke="{edge}" stroke-width="1.5" />
  <image x="32" y="24" width="560" height="315" xlink:href="{escape(source)}" />
  <text x="44" y="382" fill="{ink}" font-family="IBM Plex Sans" font-size="38" font-weight="500">{escape(name)}</text>
  <g id="ansi-palette"><title>ANSI color00–07, left to right</title>{swatches}<rect x="44" y="420" width="176" height="30" fill="none" stroke="{edge}" stroke-width="1" /></g>
  <image x="{580 - badge_w + 12 * scale}" y="400" width="{badge_w}" height="{36 * scale}" xlink:href="{escape(badge_source)}" />
{status}</svg>'''


def identity_svg(ink):
    """Original outline lettering; the register's chamfer recurs in C, O and R."""
    glyphs = [
        'M0 0V64M0 32H38M38 0V64',
        'M0 64V14L14 0H24L38 14V64M0 34H38',
        'M0 64V0M0 0L38 64M38 64V0',
        'M38 0H12L0 12V52L12 64H38',
        'M12 0H26L38 12V52L26 64H12L0 52V12Z',
        'M0 64V0H26L38 12V22L26 34H0M22 34L40 64',
        'M38 0H0V64H38M0 32H30',
    ]
    paths = ''.join(f'<path transform="translate({i*56} 0)" d="{glyph}" />' for i, glyph in enumerate(glyphs))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="318" viewBox="0 0 440 106">
<title>HANCORE — register wordmark study, original drawn lettering</title>
<g transform="translate(32 21)" fill="none" stroke="{ink}" stroke-width="6" stroke-linejoin="miter" stroke-linecap="square">{paths}</g>
</svg>'''
