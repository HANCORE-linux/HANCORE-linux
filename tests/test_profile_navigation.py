"""Regression checks for every public return link and requested personal links."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'https://github.com/HANCORE-linux'


class Links(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links, self.active = [], None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.active = dict(href=attrs['href'], text='', alt='')
        elif tag == 'img' and self.active is not None:
            self.active['alt'] = attrs.get('alt', '')

    def handle_data(self, data):
        if self.active is not None:
            self.active['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            self.links.append(self.active)
            self.active = None


class ProfileNavigationTests(unittest.TestCase):
    def test_inspired_by_keeps_three_rows_and_the_existing_page_link(self):
        for prefix in ('', 'folio/'):
            with self.subTest(prefix=prefix):
                page = (ROOT / (prefix + 'ACKNOWLEDGEMENTS.md')).read_text()
                rows = [Links(part).links for part in page.split('</p>')]
                rows = [row for row in rows if any(link['alt'] for link in row)]
                self.assertEqual([len(row) for row in rows], [3, 3, 2])
                self.assertIn('alt="Inspired by"', page)
                self.assertNotIn('alt="Acknowledgements"', page)
                self.assertEqual(page.count('width="248" height="89"'), 8)
                profile = (ROOT / (prefix + 'README.md')).read_text()
                link, = [link for link in Links(profile).links if link['alt'] == 'Inspired by']
                self.assertEqual(link['href'], './ACKNOWLEDGEMENTS.md')
                self.assertIn('title="Inspired by"', profile)

    def test_every_return_link_opens_the_account_profile(self):
        for prefix in ('', 'folio/'):
            for name, count in [('README.md', 0), ('THEMES.md', 2), ('ACKNOWLEDGEMENTS.md', 1)]:
                with self.subTest(page=prefix + name):
                    links = Links((ROOT / (prefix + name)).read_text()).links
                    returns = [link for link in links if 'Back to profile' in link['text']]
                    self.assertEqual(len(returns), count)
                    for link in returns:
                        self.assertEqual(link['href'], PROFILE)

    def test_dhh_and_ryan_link_to_their_personal_profiles(self):
        for prefix in ('', 'folio/'):
            with self.subTest(prefix=prefix):
                links = Links((ROOT / (prefix + 'ACKNOWLEDGEMENTS.md')).read_text()).links
                by_alt = {link['alt']: link['href'] for link in links}
                self.assertEqual(by_alt['DHH / Omarchy'], 'https://github.com/dhh')
                self.assertEqual(by_alt['Ryan Hughes / Omarchy-dev'], 'https://github.com/ryanrhughes')


if __name__ == '__main__':
    unittest.main()
