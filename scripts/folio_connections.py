"""Independent clickable slices for two native README connection groups."""
from html import escape

PROJECTS = ('shibumi', 'omaq', 'marketplace')
WIDE_MIN = 1280
# GitHub's README column is the viewport minus 82 px below 768, minus 370 px to 1011 and minus
# 434 px to 1279, less a classic scrollbar of up to 17 px (live profile, 2026-10-26). At 496–743 px
# three 248 px cards wrap two plus one; a 496 px rumb line stacks its row instead. Lower bounds
# assume the widest scrollbar and upper bounds none, so the source is never narrowed or paired.
STACKED = ((595, 767), (883, 1177))
# Quiet routes; brighter signal segments and terminals.
ROUTE_INK = {'dark': '#48525b', 'light': '#a1a6ab'}
SIGNAL_INK = {'dark': '#e8e3d9', 'light': '#41474d'}


def specs(popular, details):
    result = [dict(slug=slug, kind='project', column=i, source=f'assets/{slug}',
                   width=624, height=820, x=0, y=120, body_height=700)
              for i, slug in enumerate(PROJECTS)]
    # rumb's compact mount on the centre route; Waybar and QS-Dots centred beside it.
    result.append(dict(slug='rumb', kind='feature', column=1, source='assets/rumb',
                       width=624, height=520, x=0, y=40, body_height=480))
    result += [dict(slug=f'info-{slug}', kind='flank', column=column, source=f'assets/info-{slug}',
                    width=624, height=520, x=0, y=164, body_height=192)
               for column, slug in ((0, 'waybar'), (2, 'qs-dots'))]
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
    line, bright = ROUTE_INK[mode], SIGNAL_INK[mode]
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
    elif kind == 'feature':
        top, bottom = spec['y'] + 16, spec['y'] + spec['body_height'] - 32
        route, segment = f'M312 0V{top}M312 {bottom}V{spec["height"]}', 'M312 8V28'
        terminals = f'M301 {top}H323M301 {bottom}H323'
    elif kind == 'flank':
        # Keep the outer rails quiet: only the centre route carries a bright segment.
        top, bottom = spec['y'] + 16, spec['y'] + 164
        route, segment = f'M312 0V{top}M312 {bottom}V{spec["height"]}', ''
        terminals = f'M301 {top}H323M301 {bottom}H323'
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
    extension = 'svg' if spec['kind'].startswith('theme-') else 'png'
    tooltip = f' title="{escape(title, quote=True)}"' if title else ''
    stacked = ''.join(f'<source media="{", ".join(f"(min-width: {low}px) and (max-width: {high}px) and (prefers-color-scheme: {mode})" for low, high in STACKED)}" '
                      f'srcset="./assets/stacked-{slug}-{mode}.png" width="496" height="{fallback_height}" />'
                      for mode in ('dark', 'light')) if spec['kind'] == 'feature' else ''
    return (f'<a href="{escape(url, quote=True)}"><picture>'
            f'<source media="(min-width: {WIDE_MIN}px) and (prefers-color-scheme: dark)" srcset="./assets/connected-{slug}-dark.{extension}" width="{width}" height="{height}" />'
            f'<source media="(min-width: {WIDE_MIN}px) and (prefers-color-scheme: light)" srcset="./assets/connected-{slug}-light.{extension}" width="{width}" height="{height}" />'
            f'{stacked}'
            f'<source media="(prefers-color-scheme: dark)" srcset="./{spec["source"]}-dark.{extension}" />'
            f'<img src="./{spec["source"]}-light.{extension}" alt="{escape(alt, quote=True)}" width="248" height="{fallback_height}" align="top"{tooltip} />'
            '</picture></a>')
