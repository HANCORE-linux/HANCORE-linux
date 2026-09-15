"""Keep the footer badge compact across automatic star-count refreshes."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import folio_summary


class Images(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.images = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))


class TotalBadgeTests(unittest.TestCase):
    def test_compact_dimensions_preserve_ratio_as_the_count_grows(self):
        for source_width, stars, expected_width in [(150, 1995, 213), (162, 12345, 227)]:
            with self.subTest(stars=stars):
                data = dict(badge=dict(width=source_width), total_stars=stars,
                            fetched_at='2026-09-15T12:00:00Z')
                with patch.object(folio_summary, 'settings', return_value=dict(account='HANCORE-linux')), \
                     patch.object(folio_summary, 'snapshot', return_value=data):
                    html = folio_summary.total_badge_html()
                image, = Images(html).images
                self.assertEqual(image['width'], str(expected_width))
                self.assertEqual(image['height'], '44')
                self.assertEqual(image['alt'], f'Total project stars: {stars:,}; public non-fork repositories + Omarchy Plugin Marketplace; checked 2026-09-15')
                self.assertIn('href="https://github.com/HANCORE-linux?tab=repositories"', html)
                self.assertIn('srcset="./assets/total-stars-dark.png"', html)
                self.assertEqual(image['src'], './assets/total-stars-light.png')


if __name__ == '__main__':
    unittest.main()
