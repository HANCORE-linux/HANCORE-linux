"""Small linked information mounts and accessible footer-icon compositions."""
from xml.sax.saxutils import escape

SOCIALS = [
    ('discord', 'Discord', 'https://discord.com/users/816417588610334741'),
    ('kofi', 'Ko-fi', 'https://ko-fi.com/hancore'),
    ('acknowledgements', 'Acknowledgements', './ACKNOWLEDGEMENTS.md'),
]

# Pango advance of the bundled IBM Plex Sans Medium at 34 px, unhinted.
# This centers the text + gap + official wordmark as one combined caption.
SHIPS_WITH_ADVANCE = 166246 / 1024
OMARCHY_WIDTH = 164
BRAND_GAP = 20
# Text accent: the existing brand orange on dark mounts, a darker counterpart
# on light mounts to retain at least 4.5:1 contrast at the compact label size.
ACCENT_INK = {'dark': '#df6124', 'light': '#ac450f'}


def detail_cards(themes, highlights):
    by_slug = {theme['slug']: theme['name'] for theme in themes}
    cards = [
        {'slug': 'waybar', 'title': 'Waybar themes', 'caption': 'For the bar.', 'url': 'https://github.com/HANCORE-linux/waybar-themes', 'group': 'projects'},
        {'slug': 'qs-dots', 'title': 'QS-Dots / Rise', 'caption': 'For the shell.', 'url': 'https://github.com/HANCORE-linux/quickshell-dots', 'group': 'projects'},
    ]
    latest = highlights['latest_theme']['slug']
    cards.append({'slug': latest, 'title': by_slug[latest], 'caption': 'Newest theme.', 'url': f'https://github.com/HANCORE-linux/omarchy-{latest}-theme', 'group': 'highlights'})
    for item in highlights['included_in_omarchy']:
        slug = item['slug']
        cards.append({'slug': slug, 'title': by_slug[slug], 'caption': 'Ships with', 'brand': True, 'url': f'https://github.com/HANCORE-linux/omarchy-{slug}-theme', 'group': 'highlights'})
    cards.append({'slug': 'archive', 'title': f'All {len(themes)} themes', 'caption': 'Open collection →', 'url': './THEMES.md', 'group': 'index'})
    return cards


def detail_svg(card, mode, *, width=624, caption_size=34, caption_weight=500):
    dark = mode == 'dark'
    paper, edge, ink, secondary = ('#191c1e', '#353a3d', '#e8e3d9', '#bfc4c9') if dark else ('#e9e7e0', '#c6c5bf', '#262522', '#50565b')
    opacity = '0.48' if dark else '0.19'
    title_ink = ACCENT_INK[mode] if card.get('group') == 'index' else ink
    center = width // 2
    outline = f'M24 16H{width - 24}V142L{width - 46} 164H24Z'
    caption_x = center - (BRAND_GAP + OMARCHY_WIDTH) / 2 if card.get('brand') else center
    brand_x = center + (SHIPS_WITH_ADVANCE + BRAND_GAP - OMARCHY_WIDTH) / 2
    brand = f'<image x="{brand_x}" y="99" width="{OMARCHY_WIDTH}" height="38" xlink:href="assets/omarchy-wordmark-orange.png" />' if card.get('brand') else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width * 2}" height="384" viewBox="0 0 {width} 192">
  <title>{escape(card['title'])} — {escape(card['caption'])}{' Omarchy.' if card.get('brand') else ''}</title>
  <defs><filter id="float" x="-15%" y="-50%" width="130%" height="210%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="8" /><feOffset dy="10" /></filter></defs>
  <path d="{outline}" fill="#000000" opacity="{opacity}" filter="url(#float)" />
  <path d="{outline}" fill="{paper}" stroke="{edge}" stroke-width="1.5" />
  <text x="{center}" y="72" text-anchor="middle" fill="{title_ink}" font-family="IBM Plex Sans" font-size="40" font-weight="600">{escape(card['title'])}</text>
  <text x="{caption_x}" y="126" text-anchor="middle" fill="{secondary}" font-family="IBM Plex Sans" font-size="{caption_size}" font-weight="{caption_weight}">{escape(card['caption'])}</text>
  {brand}
</svg>'''


def social_svg(slug, mode):
    if slug == 'acknowledgements':
        ink = '#e8e3d9' if mode == 'dark' else '#262522'
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="176" height="176" viewBox="0 0 44 44">
  <title>Acknowledgements</title>
  <g fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M22 12C18 9 12 9 6 10V33C12 32 18 32 22 35C26 32 32 32 38 33V10C32 9 26 9 22 12Z" />
    <path d="M22 12V35M11 18H17M11 23H17" />
  </g>
  <path d="M30 26L25.6 21.6C22.8 18.5 27.4 15.8 30 18.5C32.6 15.8 37.2 18.5 34.4 21.6Z" fill="#df6124" />
</svg>'''
    assert slug in ('discord', 'kofi'), f'Unknown footer icon: {slug}'
    source = f'sources/discord-symbol-{"white" if mode == "dark" else "black"}.svg' if slug == 'discord' else 'sources/kofi-icon.png'
    y, height = (10, 24) if slug == 'discord' else (6, 32)
    label = dict((slug, label) for slug, label, _ in SOCIALS)[slug]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="176" height="176" viewBox="0 0 44 44">
  <title>{escape(label)}</title>
  <image x="6" y="{y}" width="32" height="{height}" xlink:href="{source}" />
</svg>'''
