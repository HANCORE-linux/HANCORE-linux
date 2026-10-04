"""Decorative connection routes for the two-column theme archive.

Archive cards span 624 units but display at 396 px, so strokes are rescaled to
the profile's displayed weights. Each card keeps its own link; adjacent
top-aligned images and explicit line breaks join the routes on wide views.
"""
from math import ceil
from xml.sax.saxutils import escape

from folio_connections import ROUTE_INK, SIGNAL_INK

DISPLAY = 396
UNIT = 624 / DISPLAY  # archive units per displayed px
SCALE = (248 / 624) * UNIT  # profile unit -> archive unit at equal displayed weight
ROUTE, SIGNAL, TERMINAL = 2.5 * SCALE, 3.5 * SCALE, 3 * SCALE
TICK, HUB = 11 * SCALE, 8 * SCALE
# Whole displayed pixels keep every joined edge on the pixel grid. 335 px restores the
# archive's former row gap (paragraph margin plus the inline baseline gap).
TRACK_PX, CLOSE_PX = 335, 357
LEAD = TRACK_PX * UNIT - 492  # route zone above every card
CARD_TOP, CARD_BOTTOM = LEAD + 16, LEAD + 472
# The 704 x 192 archive tile (mount ends at 164) is shown 280 px wide.
TILE_WIDTH, TILE_VIEW, TILE_MOUNT = 280, (704, 192), 164
HEAD_WIDTH = 2 * 624


def kinds(count):
    """Route kind per archive row: tracks, then one closing row or a merge into a single card."""
    assert count >= 2
    rows = (count + 1) // 2
    if count % 2 == 0:
        return ['track'] * (rows - 1) + ['close']
    return ['track'] * (rows - 2) + ['merge', 'single']


def height_px(kind):
    return TRACK_PX if kind in ('track', 'blank') else CLOSE_PX


def slice_svg(slug, name, mode, kind, column=0):
    height = height_px(kind) * UNIT
    tick = lambda y: f'M{312 - TICK:.3f} {y:.3f}H{312 + TICK:.3f}'
    route = [f'M312 0V{CARD_TOP:.3f}']
    signal = ['M312 8V28']
    ticks = [tick(CARD_TOP), tick(CARD_BOTTOM)]
    hubs = []
    seam = 624 if column == 0 else 0
    if kind == 'track':
        route.append(f'M312 {CARD_BOTTOM:.3f}V{height:.3f}')
    elif kind == 'close':
        # Both columns meet below the last row; the end point straddles the seam.
        rail = (CARD_BOTTOM + 20 + height) / 2
        route.append(f'M312 {CARD_BOTTOM:.3f}V{rail:.3f}H{seam}')
        hubs.append((seam - HUB / 2, rail - HUB / 2))
    elif kind == 'merge':
        # Rail flush with the lower edge; the centered single card continues it.
        rail = height - ROUTE / 2
        route.append(f'M312 {CARD_BOTTOM:.3f}V{rail:.3f}H{seam}')
    else:
        end = (CARD_BOTTOM + 20 + height) / 2
        route.append(f'M312 {CARD_BOTTOM:.3f}V{end:.3f}')
        hubs += [(312 - HUB / 2, 0), (312 - HUB / 2, end - HUB / 2)]
    if kind == 'blank':
        # Narrow fallback: the same spacing zone, without routes.
        route = signal = ticks = hubs = []
    paths = '' if kind == 'blank' else (
        f'\n  <path d="{''.join(route)}" fill="none" stroke="{ROUTE_INK[mode]}" stroke-width="{ROUTE:.3f}" />'
        f'\n  <path d="{''.join(signal)}" fill="none" stroke="{SIGNAL_INK[mode]}" stroke-width="{SIGNAL:.3f}" />'
        f'\n  <path d="{''.join(ticks)}" fill="none" stroke="{SIGNAL_INK[mode]}" stroke-width="{TERMINAL:.3f}" />')
    rects = ''.join(f'\n  <rect x="{x:.3f}" y="{y:.3f}" width="{HUB:.3f}" height="{HUB:.3f}" fill="#df6124" />' for x, y in hubs)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1248" height="{2 * height:.0f}" viewBox="0 0 624 {height:.3f}">
  <title>{escape(name)} — archive card with decorative connection route</title>
  <image x="0" y="{LEAD:.3f}" width="624" height="492" xlink:href="collection/assets/{slug}-{mode}.png" />{paths}{rects}
</svg>'''


def head_geometry():
    tile_width = TILE_WIDTH * UNIT
    tile_height = tile_width * TILE_VIEW[1] / TILE_VIEW[0]
    bottom = tile_height * TILE_MOUNT / TILE_VIEW[1]
    rail = bottom + 40
    display = ceil((rail + 8) / UNIT)
    return tile_width, tile_height, bottom, rail, display


def head_svg(mode, title):
    tile_width, tile_height, bottom, rail, display = head_geometry()
    height = display * UNIT
    left, right, mid = 312, HEAD_WIDTH - 312, HEAD_WIDTH / 2
    route = (f'M{mid:g} {bottom:.3f}V{rail:.3f}M{left} {rail:.3f}H{right}'
             f'M{left} {rail:.3f}V{height:.3f}M{right} {rail:.3f}V{height:.3f}')
    signal = f'M{left + 60} {rail:.3f}H{left + 84}M{right - 84} {rail:.3f}H{right - 60}'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{2 * 2 * DISPLAY}" height="{2 * display}" viewBox="0 0 {HEAD_WIDTH} {height:.3f}">
  <title>{escape(title)} — archive heading with decorative connection route</title>
  <image x="{mid - tile_width / 2:.3f}" y="0" width="{tile_width:.3f}" height="{tile_height:.3f}" xlink:href="assets/label-archive-{mode}.png" />
  <path d="{route}" fill="none" stroke="{ROUTE_INK[mode]}" stroke-width="{ROUTE:.3f}" />
  <path d="{signal}" fill="none" stroke="{SIGNAL_INK[mode]}" stroke-width="{SIGNAL:.3f}" />
  <path d="M{mid - TICK:.3f} {bottom:.3f}H{mid + TICK:.3f}" fill="none" stroke="{SIGNAL_INK[mode]}" stroke-width="{TERMINAL:.3f}" />
  <rect x="{mid - HUB / 2:.3f}" y="{rail - HUB / 2:.3f}" width="{HUB:.3f}" height="{HUB:.3f}" fill="#df6124" />
</svg>'''
