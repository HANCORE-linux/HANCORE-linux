"""Shared, GitHub-safe Plex Sans labels at a native 16 px display size."""
from html import escape
from folio_details import detail_svg

LABEL_WIDTH = 248
LABEL_SIZE = 16


def labels(theme_count):
    return {
        'subtitle': ('Linux themes & interfaces.',),
        'popular': ('Most starred themes',),
        'archive': ('Theme archive', f'{theme_count} themes · color00–07 · A–Z'),
        'acknowledgements': ('Inspired by',),
    }


def label_dimensions(slug, theme_count):
    # Extra width keeps the archive's full metadata readable at the same 16 px
    # size, inside the shared chamfered frame rather than against its edges.
    return (280, 76) if slug == 'archive' else (LABEL_WIDTH, len(labels(theme_count)[slug]) * 28)


def label_svg(lines, ink, slug=None):
    if slug == 'archive':
        return detail_svg({'title': lines[0], 'caption': lines[1], 'group': 'index'},
                          'dark' if ink == '#e8e3d9' else 'light',
                          width=704, caption_size=40, caption_weight=600)
    height = len(lines) * 28
    text = '\n'.join(
        f'  <text x="124" y="{20 + index * 28}" text-anchor="middle" '
        f'fill="{ink}" font-family="IBM Plex Sans" font-size="{LABEL_SIZE}" '
        f'font-weight="600">{escape(line)}</text>'
        for index, line in enumerate(lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{LABEL_WIDTH * 4}" height="{height * 4}" viewBox="0 0 {LABEL_WIDTH} {height}">
  <title>{escape(' — '.join(lines))}</title>
{text}
</svg>'''


def label_picture(slug, theme_count, connected=None):
    lines = labels(theme_count)[slug]
    alt = escape(' — '.join(lines), quote=True)
    width, height = label_dimensions(slug, theme_count)
    wide = align = ''
    if connected:
        # Wide views swap in the routed heading; the top-aligned tile joins what follows.
        from folio_connections import WIDE_MIN
        path, wide_width, wide_height = connected
        wide = ''.join(f'<source media="(min-width: {WIDE_MIN}px) and (prefers-color-scheme: {mode})" srcset="{path}-{mode}.png" '
                       f'width="{wide_width}" height="{wide_height}" />' for mode in ('dark', 'light'))
        align = ' align="top"'
    return (f'<picture>{wide}<source media="(prefers-color-scheme: dark)" srcset="./assets/label-{slug}-dark.png" />'
            f'<img src="./assets/label-{slug}-light.png" alt="{alt}" '
            f'width="{width}" height="{height}"{align} /></picture>')
