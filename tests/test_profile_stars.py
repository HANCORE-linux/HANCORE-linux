"""Offline coverage for star scope, no-op runs and changing top-six membership."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import refresh_profile_stars as refresh
import refresh_folio_totals as totals
from refresh_folio_badges import validate_badge


def repo(number, name, stars, fork=False):
    return dict(id=number, full_name=name, html_url='https://github.com/' + name,
                stargazers_count=stars, private=False, fork=fork)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(account='owner', extra_repositories=['org/marketplace'], exclude_forks=True)

    def collect(self, pages):
        with patch.object(totals, 'download', side_effect=[json.dumps(p).encode() for p in pages]):
            return totals.collect(self.config)

    def test_owned_plus_transferred_excludes_forks(self):
        result = self.collect([[repo(1, 'owner/project', 12), repo(2, 'owner/fork', 900, True)],
                               repo(3, 'org/marketplace', 8)])
        self.assertEqual((result['owned_stars'], result['extra_stars'], result['total_stars']), (12, 8, 20))
        self.assertEqual(len(result['excluded_forks']), 1)

    def test_extra_already_owned_counted_once(self):
        self.config['extra_repositories'] = ['owner/project']
        result = self.collect([[repo(1, 'owner/project', 12)], repo(1, 'owner/project', 12)])
        self.assertEqual(result['total_stars'], 12)
        self.assertEqual(len(result['repositories']), 1)

    def test_all_pages_are_included(self):
        result = self.collect([[repo(i, f'owner/p{i}', 1) for i in range(1, 101)],
                               [repo(101, 'owner/last', 3)], repo(102, 'org/marketplace', 7)])
        self.assertEqual(result['total_stars'], 110)

    def test_incomplete_or_invalid_data_is_rejected(self):
        for bad in [dict(message='rate limit'), [repo(1, 'someone/foreign', 1)],
                    [repo(1, 'owner/p', -1)], [repo(1, 'owner/p', True)],
                    [dict(repo(1, 'owner/p', 1), private=True)],
                    [repo(1, 'owner/p', 1), repo(1, 'owner/p', 1)]]:
            with self.subTest(bad=bad), self.assertRaises((AssertionError, KeyError)):
                self.collect([bad])

    def test_missing_extra_fails_instead_of_zero(self):
        with self.assertRaises(KeyError):
            self.collect([[repo(1, 'owner/p', 1)], dict(message='Not Found')])

    def test_cross_origin_redirect_is_rejected(self):
        from urllib.request import Request
        with self.assertRaises(ValueError):
            totals.SameOriginRedirect().redirect_request(Request('https://api.github.com/repos/x/y'),
                                                        None, 302, '', {}, 'https://example.com/')


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='profile-stars-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folio = self.root / 'folio'
        for directory in ['data', 'folio/sources', 'folio/collection/sources']:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for attr, value in [('ROOT', self.root), ('FOLIO', self.folio)]:
            p = patch.object(refresh, attr, value)
            p.start()
            self.addCleanup(p.stop)
        self.counts = dict(a=80, b=70, c=60, d=50, e=40, f=35, g=34)
        self.image = b'\x89PNG\r\n\x1a\n' + b'\0' * 8 + (2560).to_bytes(4, 'big') + (1440).to_bytes(4, 'big')
        self.total_badge = b'total-fixture'
        self.total = dict(account='owner', repositories=[dict(id=i, full_name=f'owner/omarchy-{s}-theme',
                         stars=n, private=False, fork=False) for i, (s, n) in enumerate(self.counts.items(), 1)],
                         badge=dict(sha256=refresh.sha256(self.total_badge)), sources=['https://api.github.com/test'])
        selected = refresh.ranked(self.counts)
        badges, previews, archive = {}, {}, {}
        for slug, stars in self.counts.items():
            _, data, record = self.badge(dict(theme_slug=slug), stars)
            if slug in selected:
                self.write(f'folio/sources/badge-{slug}.svg', data)
                self.write(f'folio/sources/popular-{slug}.png', self.image)
                badges[slug] = record
                previews[slug] = dict(branch='main', git_blob=refresh.git_blob(self.image))
            else:
                self.write(f'folio/collection/sources/badge-{slug}.svg', data)
                self.write(f'folio/collection/sources/{slug}.png', self.image)
                archive[slug] = dict(badge=record, sha256=refresh.sha256(self.image))
        self.write('data/themes.json', [dict(slug=s) for s in self.counts])
        self.write('folio/popular-themes.json', dict(star_snapshot=self.counts, previews=previews))
        self.write('folio/badge-snapshot.json', dict(fetched_at='original', badges=badges))
        self.write('folio/collection/sources.json', dict(fetched_at='original image date', themes=archive))
        self.write('folio/total-stars.json', self.total)
        self.write('folio/sources/badge-total-stars.svg', self.total_badge)

    def write(self, name, value):
        (self.root / name).write_bytes(value if isinstance(value, bytes) else refresh.encoded(value))

    @staticmethod
    def badge(work, count):
        slug = work['theme_slug']
        data = f'fixture {slug}: {count}'.encode()
        return slug, data, dict(stars=count, sha256=refresh.sha256(data), api_snapshot=True)

    def test_unchanged_counts_write_nothing(self):
        with patch.object(refresh, 'fetch_badge', side_effect=AssertionError('No badge download expected')):
            self.assertEqual(refresh.apply_updates(refresh.plan_updates(self.total, self.total_badge)), 0)

    def test_promotion_demotion_and_second_run_noop(self):
        self.total['repositories'][-1]['stars'] = 90
        with patch.object(refresh, 'fetch_badge', side_effect=self.badge):
            writes = refresh.plan_updates(self.total, self.total_badge)
            self.assertEqual(writes[self.folio / 'sources/popular-g.png'], self.image)
            self.assertEqual(writes[self.folio / 'collection/sources/f.png'], self.image)
            refresh.apply_updates(writes)
        snapshot = json.loads((self.folio / 'badge-snapshot.json').read_text())
        self.assertEqual(list(snapshot['badges']), ['g', 'a', 'b', 'c', 'd', 'e'])
        archive = json.loads((self.folio / 'collection/sources.json').read_text())
        self.assertEqual(archive['fetched_at'], 'original image date')
        with patch.object(refresh, 'fetch_badge', side_effect=AssertionError('No second download')):
            self.assertEqual(refresh.apply_updates(refresh.plan_updates(self.total, self.total_badge)), 0)

    def test_star_decrease_to_zero(self):
        self.total['repositories'][-1]['stars'] = 0
        with patch.object(refresh, 'fetch_badge', side_effect=self.badge):
            writes = refresh.plan_updates(self.total, self.total_badge)
        archive = json.loads(writes[self.folio / 'collection/sources.json'])
        self.assertEqual(archive['themes']['g']['badge']['stars'], 0)

    def test_failed_badge_fetch_leaves_files_intact(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.total['repositories'][0]['stars'] += 1
        with patch.object(refresh, 'fetch_badge', side_effect=ValueError('Invalid remote SVG')):
            with self.assertRaises(ValueError):
                refresh.plan_updates(self.total, self.total_badge)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_missing_theme_is_not_silently_zeroed(self):
        self.total['repositories'].pop()
        with self.assertRaisesRegex(AssertionError, 'Missing public theme'):
            refresh.plan_updates(self.total, self.total_badge)

    def test_threshold_limit_and_tie_break(self):
        self.assertEqual(refresh.ranked(dict(b=31, a=31, c=30)), ['a', 'b'])
        self.assertEqual(len(refresh.ranked({str(i): 100 for i in range(10)})), 6)


class BadgeTests(unittest.TestCase):
    source = b'<svg xmlns="http://www.w3.org/2000/svg" width="60" height="20"><rect fill="#000000"/><rect fill="#df6124"/><text>stars</text><text>42</text></svg>'

    def test_exact_api_count(self):
        _, _, record = validate_badge(dict(theme_slug='solitude'), self.source, 42)
        self.assertEqual(record['stars'], 42)
        self.assertTrue(record['api_snapshot'])

    def test_wrong_count_rejected(self):
        with self.assertRaises(AssertionError):
            validate_badge(dict(theme_slug='solitude'), self.source, 41)

    def test_external_content_rejected(self):
        for injection in [b'<script/>', b'<image href="https://example.com/x.png"/>',
                          b'<a href="https://example.com/"/>', b'<rect onload="bad()"/>']:
            with self.subTest(injection=injection), self.assertRaises(AssertionError):
                validate_badge(dict(theme_slug='solitude'), self.source.replace(b'</svg>', injection + b'</svg>'), 42)

    def test_error_response_rejected(self):
        with self.assertRaises(AssertionError):
            validate_badge(dict(theme_slug='solitude'), self.source.replace(b'>42<', b'>inaccessible<'), 42)


if __name__ == '__main__':
    unittest.main()
