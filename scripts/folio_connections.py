"""Independent clickable slices for two native README connection groups."""
from html import escape

PROJECTS = ('shibumi', 'omaq', 'marketplace')
WIDE_MIN = 1280


def specs(popular, details):
    result = [dict(slug=slug, kind='project', column=i, source=f'assets/{slug}',
                   width=624, height=900, x=0, y=120, body_height=700)
              for i, slug in enumerate(PROJECTS)]
    result += [dict(slug=f'info-{slug}', kind='bridge', column=i, source=f'assets/info-{slug}',
                    width=936, height=272, x=312 if i == 0 else 0, y=40, body_height=192)
               for i, slug in enumerate(('waybar', 'qs-dots'))]
    result += [dict(slug=f'info-{card["slug"]}', kind='highlight', column=i, source=f'assets/info-{card["slug"]}',
                    width=624, height=232, x=0, y=40, body_height=192)
               for i, card in enumerate(c for c in details if c['group'] == 'highlights')]
    result += [dict(slug=f'theme-{work["theme_slug"]}', kind='theme-top' if i < 3 else 'theme-bottom',
                    column=i % 3, source=f'collection/assets/{work["theme_slug"]}', width=624,
                    height=680 if i < 3 else 612, x=0, y=120 if i < 3 else 40, body_height=492)
               for i, work in enumerate(popular)]
    result.append(dict(slug='info-archive', kind='archive', column=1, source='assets/info-archive',
                       width=624, height=232, x=0, y=40, body_height=192))
    return result


def connected_svg(spec, mode):
    line = '#48525b' if mode == 'dark' else '#a1a6ab'
    bright = '#e8e3d9' if mode == 'dark' else '#41474d'
    kind, column = spec['kind'], spec['column']
    hub = ''
    if kind in ('project', 'theme-top'):
        route = ['M624 48H312V136', 'M0 48H624M312 8V136', 'M0 48H312V136'][column]
        segment = ['M468 48H524', 'M312 76V112', 'M100 48H156'][column]
        end = spec['y'] + (668 if kind == 'project' else 472)
        route += f'M312 {end}V{spec["height"]}'
        terminals = f'M301 136H323M301 {end}H323'
        if column == 1:
            hub = '<rect x="308" y="4" width="8" height="8" fill="#df6124" />'
    elif kind == 'bridge':
        # The three rails run in the transparent margins beside the two cards.
        route = 'M312 0V272M936 0V272M312 120H336' if column == 0 else 'M0 0V272M624 0V272M624 120H600'
        # Keep the outer rails quiet: their former bright segments were staggered.
        segment = ''
        terminals = 'M336 113V127' if column == 0 else 'M600 113V127'
    elif kind == 'theme-bottom':
        route = 'M312 0V56' + ['M312 512V584H624', 'M312 512V612M0 584H624', 'M312 512V584H0'][column]
        segment = 'M312 12V32' + ['M468 584H524', 'M312 590V608', 'M100 584H156'][column]
        terminals = 'M301 56H323M301 512H323'
    else:
        route, segment, terminals = 'M312 0V56', 'M312 12V32', 'M301 56H323'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{spec['width'] * 2}" height="{spec['height'] * 2}" viewBox="0 0 {spec['width']} {spec['height']}">
  <title>{escape(spec['slug'])} — independent card with decorative connection route</title>
  <image x="{spec['x']}" y="{spec['y']}" width="624" height="{spec['body_height']}" xlink:href="{spec['source']}-{mode}.png" />
  <path d="{route}" fill="none" stroke="{line}" stroke-width="2.5" />
  <path d="{segment}" fill="none" stroke="{bright}" stroke-width="3.5" />
  <path d="{terminals}" fill="none" stroke="{bright}" stroke-width="3" />
  {hub}
</svg>'''


def connected_picture(spec, url, alt, title=None):
    # Adjacent top-aligned images and explicit line breaks join in both axes.
    # No image map, merged click target, CSS positioning or README script.
    width = round(spec['width'] * 248 / 624)
    height = round(spec['height'] * 248 / 624)
    fallback_height = round(spec['body_height'] * 248 / 624)
    slug = spec['slug']
    tooltip = f' title="{escape(title, quote=True)}"' if title else ''
    return (f'<a href="{escape(url, quote=True)}"><picture>'
            f'<source media="(min-width: {WIDE_MIN}px) and (prefers-color-scheme: dark)" srcset="./assets/connected-{slug}-dark.png" width="{width}" height="{height}" />'
            f'<source media="(min-width: {WIDE_MIN}px) and (prefers-color-scheme: light)" srcset="./assets/connected-{slug}-light.png" width="{width}" height="{height}" />'
            f'<source media="(prefers-color-scheme: dark)" srcset="./{spec["source"]}-dark.png" />'
            f'<img src="./{spec["source"]}-light.png" alt="{escape(alt, quote=True)}" width="248" height="{fallback_height}" align="top"{tooltip} />'
            '</picture></a>')
