"""Dated Shields source, clipped only at the lower-right corner of its mount."""
from xml.sax.saxutils import escape


def badge_svg(slug, record, mode, source):
    width = record['width']
    canvas = width + 24
    opacity = '0.55' if mode == 'dark' else '0.24'
    outline = f'M12 4H{12 + width}V20L{8 + width} 24H12Z'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{canvas * 4}" height="144" viewBox="0 0 {canvas} 36">
  <title>GitHub stars — {escape(slug)}: {record['stars']}; dated snapshot</title>
  <defs><filter id="float" x="-25%" y="-50%" width="150%" height="220%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="2.2" /><feOffset dy="3" /></filter><clipPath id="badge-cut"><path d="{outline}" /></clipPath></defs>
  <path d="{outline}" fill="#000000" opacity="{opacity}" filter="url(#float)" />
  <image x="12" y="4" width="{width}" height="20" xlink:href="{escape(source)}" clip-path="url(#badge-cut)" />
</svg>'''
