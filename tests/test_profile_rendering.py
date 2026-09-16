"""Catch low-resolution SVG embedding in the actual PNGs shipped by CI."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from folio_badges import badge_environment, badge_svg
from folio_details import social_svg
from folio_vectors import FOLIO, SVG

NS = {'s': SVG}
IM = shutil.which('magick') or shutil.which('convert')


def pixels(path, crop):
    return subprocess.check_output([IM, str(path), '-crop', crop, '+repage',
                                    '-background', '#808080', '-alpha', 'remove',
                                    '-depth', '8', 'rgb:-'])


class VectorExportTests(unittest.TestCase):
    def assert_pixels_match(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        # Permit tiny antialiasing rounding differences, not a blurred glyph.
        error = sum(abs(a - b) for a, b in zip(actual, expected)) / (255 * len(actual))
        self.assertLess(error, 0.003, f'Pixel error {error:.6f}: vector detail was lost')

    def test_generators_never_embed_svg_as_an_image(self):
        record = json.loads((FOLIO / 'total-stars.json').read_text())['badge']
        for mode in ('dark', 'light'):
            root = ET.fromstring(badge_svg('total', record, mode, 'sources/badge-total-stars.svg'))
            self.assertIsNone(root.find('.//s:image', NS))
            vector = root.find('s:g/s:svg', NS)
            self.assertIsNotNone(vector)
            self.assertEqual(vector.get('viewBox'), f'0 0 {record["width"]} 20')
            self.assertEqual(root.find('s:g', NS).get('clip-path'), 'url(#badge-cut)')
            self.assertTrue(all(node.get('font-family') == 'Liberation Sans'
                                for node in vector.iter() if 'font-family' in node.attrib))
            discord = ET.fromstring(social_svg('discord', mode))
            self.assertIsNone(discord.find('.//s:image', NS))
            source = ET.parse(FOLIO / f'sources/discord-symbol-{"white" if mode == "dark" else "black"}.svg').getroot()
            self.assertEqual([p.attrib for p in discord.findall('s:svg/s:path', NS)],
                             [p.attrib for p in source.findall('s:path', NS)])

    def test_shipped_badges_match_direct_vector_rendering(self):
        popular = set(json.loads((FOLIO / 'badge-snapshot.json').read_text())['badges'])
        cases = [(p, FOLIO / 'assets' / p.stem) for p in sorted((FOLIO / 'sources').glob('badge-*.svg'))
                 if p.stem.removeprefix('badge-') in popular | {'total-stars'}]
        cases += [(p, FOLIO / 'collection/assets' / p.stem)
                  for p in sorted((FOLIO / 'collection/sources').glob('badge-*.svg'))
                  if p.stem.removeprefix('badge-') not in popular]
        self.assertEqual(len(cases), 28)  # 27 themes and the total, individually.
        with tempfile.TemporaryDirectory() as temp, badge_environment() as env:
            direct, reference = Path(temp) / 'direct.svg', Path(temp) / 'direct.png'
            for source, target in cases:
                root = ET.parse(source).getroot()
                width = int(root.get('width'))
                root.set('viewBox', f'0 0 {width} 20')
                root.set('width', str(width * 4))
                root.set('height', '80')
                # No composition helper here: independently render the original
                # badge directly at export resolution with the approved font.
                for node in root.iter():
                    if 'font-family' in node.attrib:
                        node.set('font-family', 'Liberation Sans')
                direct.write_text(ET.tostring(root, encoding='unicode'))
                subprocess.run(['rsvg-convert', str(direct), '-o', str(reference)], env=env, check=True)
                crop_width = (width - 8) * 4  # Exclude only the intentional chamfer.
                expected = pixels(reference, f'{crop_width}x80+0+0')
                for mode in ('dark', 'light'):
                    with self.subTest(badge=source.name, mode=mode):
                        name = 'total-stars' if source.stem == 'badge-total-stars' else target.name
                        actual = target.parent / f'{name}-{mode}.png'
                        self.assert_pixels_match(pixels(actual, f'{crop_width}x80+48+16'), expected)

    def test_shipped_discord_matches_original_vector_at_export_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            reference = Path(temp) / 'discord.png'
            for mode, color in [('dark', 'white'), ('light', 'black')]:
                with self.subTest(mode=mode):
                    source = FOLIO / f'sources/discord-symbol-{color}.svg'
                    subprocess.run(['rsvg-convert', '-w', '128', '-h', '96', str(source), '-o', str(reference)], check=True)
                    self.assert_pixels_match(pixels(FOLIO / f'assets/social-discord-{mode}.png', '128x96+24+40'),
                                             pixels(reference, '128x96+0+0'))


if __name__ == '__main__':
    unittest.main()
