"""Check the image delivered to README, not only intermediate high-DPI PNGs."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from folio_badge_delivery import FOLIO, NS, SVG, HREF, validate_public
from folio_badges import badge_environment

IM = shutil.which('magick') or shutil.which('convert')


def rgb(data, crop=None):
    command = [IM, 'png:-']
    if crop:
        command += ['-crop', crop, '+repage']
    return subprocess.check_output(command + ['-background', '#808080', '-alpha', 'remove', '-depth', '8', 'rgb:-'], input=data)


class BadgeDeliveryTests(unittest.TestCase):
    def test_every_public_badge_is_self_contained_vector_lettering(self):
        paths = [*sorted((FOLIO / 'collection/assets').glob('*.svg')), *sorted((FOLIO / 'assets').glob('*.svg'))]
        self.assertEqual(len(paths), 68)  # 54 archive cards, 12 connectors, 2 totals.
        for path in paths:
            with self.subTest(asset=path.name):
                root = ET.parse(path).getroot()
                validate_public(root)
                glyphs = root.find('.//s:svg[@id="badge-glyphs"]', NS)
                self.assertTrue(glyphs.findall('.//s:path', NS))
                self.assertIsNone(glyphs.find('.//s:image', NS))
                self.assertIsNone(root.find('.//s:text', NS))
                self.assertLess(path.stat().st_size, 3_500_000)

    def test_theme_background_pixels_and_caption_stay_unchanged(self):
        themes = json.loads((FOLIO.parent / 'data/themes.json').read_text())
        for theme in themes:
            for mode in ('dark', 'light'):
                slug = theme['slug']
                with self.subTest(theme=slug, mode=mode):
                    root = ET.parse(FOLIO / f'collection/assets/{slug}-{mode}.svg').getroot()
                    background = base64.b64decode(root.find('s:image[@id="card-pixels"]', NS).get(HREF).split(',', 1)[1])
                    original = (FOLIO / f'collection/assets/{slug}-{mode}.png').read_bytes()
                    # Everything above/left of the badge: screenshot, title,
                    # palette, NEW label, mount and its shadow retain their pixels.
                    for crop in ('1248x800+0+0', '780x984+0+0'):
                        self.assertEqual(rgb(background, crop), rgb(original, crop))
                    badge_pixels = rgb(background, '450x160+780+800')
                    self.assertFalse(any(min(badge_pixels[i:i+3]) > 245 for i in range(0, len(badge_pixels), 3)),
                                     'Badge text must not be baked into the background bitmap')

    def test_glyphs_derive_from_the_original_badge_at_display_resolution(self):
        paths = sorted((FOLIO / 'collection/assets').glob('*.svg')) + sorted((FOLIO / 'assets').glob('total-stars-*.svg'))
        with badge_environment() as env:
            for path in paths:
                with self.subTest(asset=path.name):
                    glyphs = deepcopy(ET.parse(path).getroot().find('.//s:svg[@id="badge-glyphs"]', NS))
                    mount = ET.parse(FOLIO / glyphs.get('data-source')).getroot()
                    shield = mount.find('s:g/s:svg', NS)
                    original_source = ET.parse(FOLIO / shield.get('data-source')).getroot()
                    width, height = map(int, mount.get('viewBox').split()[2:])
                    expected = ET.Element(f'{{{SVG}}}svg', dict(width=str(width), height=str(height), viewBox=mount.get('viewBox')))
                    # Independent reference: original source lettering, without
                    # the export helper, outlines, background, shadow or filter.
                    group = deepcopy(original_source.findall('s:g', NS)[-1])
                    group.set('font-family', 'Liberation Sans')
                    shifted = ET.SubElement(expected, f'{{{SVG}}}g', {'transform': 'translate(12 4)'})
                    shifted.append(group)
                    for density in (1, 2):
                        args = ['rsvg-convert', '-w', str(width * density), '-h', str(height * density)]
                        reference = rgb(subprocess.check_output(args, input=ET.tostring(expected), env=env))
                        actual = rgb(subprocess.check_output(args, input=ET.tostring(glyphs), env=env))
                        self.assertEqual(len(actual), len(reference))
                        error = sum(abs(a - b) for a, b in zip(actual, reference)) / (255 * len(actual))
                        self.assertLess(error, .003, f'Badge glyph detail differs from its source: {error:.6f}')

    def test_readme_delivers_vectors_at_unchanged_sizes(self):
        markdown = (FOLIO / 'README.md').read_text()
        total = json.loads((FOLIO / 'total-stars.json').read_text())
        width = round((total['badge']['width'] + 24) * 44 / 36)
        self.assertIn('total-stars-dark.svg', markdown)
        self.assertIn(f'src="./assets/total-stars-light.svg" width="{width}" height="44"', markdown)
        self.assertNotIn('total-stars-dark.png', markdown)
        snapshot = json.loads((FOLIO / 'badge-snapshot.json').read_text())['badges']
        for slug in snapshot:
            self.assertIn(f'connected-theme-{slug}-dark.svg', markdown)
            self.assertIn(f'collection/assets/{slug}-light.svg', markdown)
        self.assertEqual((FOLIO / 'THEMES.md').read_text().count('width="396" height="312"'), 27)


if __name__ == '__main__':
    unittest.main()
