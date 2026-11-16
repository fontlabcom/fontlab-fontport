# this_file: tests_docs/test_site.py
"""Check the actual generated payload, routes and public source boundaries."""
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs'
PREFIX = '/fontlab-fontport/'
PAGES = ['index.html', 'installation/index.html', 'fonts-pens-and-interchange/index.html', 'development-and-limits/index.html', 'licence/index.html', 'guides/FONTPARTS-COVERAGE/index.html', 'guides/INTEGRATION/index.html', 'guides/LIVE-PEN-RECIPES/index.html', 'guides/NATIVE-BOUNDARIES/index.html', 'guides/NATIVE-FEATURES/index.html', 'guides/ROUND10-NATIVE/index.html', 'guides/ROUND12-NATIVE/index.html', 'guides/ROUND13-NATIVE/index.html', 'guides/ROUND14-NATIVE/index.html', 'guides/ROUND15-NATIVE/index.html', 'guides/UFO-INTERCHANGE/index.html']


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.ids = set()
        self.links = []
        self.text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ('href', 'src'):
            if name in attrs:
                self.links.append(attrs[name])

    def handle_data(self, data):
        self.text.append(data)


class SiteTests(unittest.TestCase):
    def test_all_generated_internal_links_and_fragments_resolve(self):
        for path in SITE.rglob('*.html'):
            for link in Page(path.read_text()).links:
                url = urlsplit(link)
                if url.scheme or url.netloc:
                    continue
                target = unquote(url.path)
                if target.startswith('/'):
                    self.assertTrue(target.startswith(PREFIX), (path, link))
                    dest = SITE / target.removeprefix(PREFIX)
                else:
                    dest = path.parent / target if target else path
                if dest.is_dir():
                    dest = dest / 'index.html'
                self.assertTrue(dest.is_file(), (path, link, dest))
                self.assertTrue(dest.resolve().is_relative_to(SITE.resolve()), link)
                if url.fragment and dest.suffix == '.html':
                    self.assertIn(unquote(url.fragment), Page(dest.read_text()).ids, (path, link))

    def test_pages_have_light_menu_footer_local_search_and_correct_canonical(self):
        for route in PAGES:
            page = Page((SITE / route).read_text())
            with self.subTest(route=route):
                self.assertEqual([attrs.get('mode') for tag, attrs in page.tags if tag == 'fontlab-menu'], ['light'])
                self.assertEqual([attrs.get('mode') for tag, attrs in page.tags if tag == 'fontlab-footer'], ['light'])
                self.assertEqual([attrs.get('data-md-color-scheme') for tag, attrs in page.tags if tag == 'body'], ['default'])
                search = [attrs for tag, attrs in page.tags if attrs.get('data-md-component') == 'search-query']
                self.assertEqual(len(search), 1)
                self.assertFalse(any(attrs.get('data-md-component') == 'palette' for _, attrs in page.tags))
                canonical = [attrs['href'] for tag, attrs in page.tags if attrs.get('rel') == 'canonical']
                self.assertEqual(canonical, ['https://fontlabcom.github.io/fontlab-fontport/' + route.removesuffix('index.html')])

    def test_search_indexes_every_authored_page(self):
        search = json.loads((SITE / 'search/search_index.json').read_text())
        locations = {row['location'].split('#')[0] for row in search['docs']}
        self.assertEqual(locations, {'', 'guides/ROUND14-NATIVE/', 'licence/', 'guides/NATIVE-BOUNDARIES/', 'fonts-pens-and-interchange/', 'installation/', 'guides/NATIVE-FEATURES/', 'guides/ROUND10-NATIVE/', 'guides/UFO-INTERCHANGE/', 'guides/INTEGRATION/', 'guides/ROUND12-NATIVE/', 'guides/ROUND13-NATIVE/', 'guides/LIVE-PEN-RECIPES/', 'guides/FONTPARTS-COVERAGE/', 'guides/ROUND15-NATIVE/', 'development-and-limits/'})
        text = ' '.join(row['text'] for row in search['docs'])
        for term in ('1,797', 'Native attached C4', 'UFOBackend'):
            self.assertTrue(term in text, f"Search must retain {term}")

    def test_attribution_downloads_are_exact_and_no_private_payload_is_published(self):
        for source, asset in (('LICENSE', 'assets/LICENSE'), ('NOTICE', 'assets/NOTICE')):
            self.assertEqual((ROOT / source).read_bytes(), (SITE / asset).read_bytes())
        self.assertTrue((SITE / '.nojekyll').is_file())
        private_markers = (b'/Users/', b'/Volumes/', b'/private/', b'ghp_', b'github_pat_', b'-----BEGIN PRIVATE KEY-----')
        sources = [path.read_bytes() for folder in ('src', 'Scripts', 'glyphs', 'examples') if (ROOT / folder).is_dir() for path in (ROOT / folder).rglob('*.py')]
        for path in SITE.rglob('*'):
            if path.is_file():
                self.assertNotIn('.DS_Store', path.parts)
                self.assertNotIn(path.suffix, ('.py', '.pyi', '.vfpy', '.whl', '.zip'))
                payload = path.read_bytes()
                for marker in private_markers:
                    self.assertFalse(marker in payload, (path, marker))
                for source in sources:
                    if len(source) > 80:
                        self.assertFalse(source in payload, path)

    def test_workflow_builds_every_main_push_and_requalifies_immutable_output(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/docs.yml').read_text())
        events = workflow.get('on', workflow.get(True))
        self.assertEqual(events['push'], {'branches': ['main']})
        self.assertNotIn('concurrency', workflow)
        build = workflow['jobs']['build']
        verify = workflow['jobs']['qualify-generated-output']
        self.assertNotIn('concurrency', build)
        self.assertEqual(verify['needs'], 'build')
        self.assertEqual(build['outputs']['epoch'], '${{ steps.epoch.outputs.value }}')
        for job, epoch in ((build, '${{ steps.epoch.outputs.value }}'), (verify, '${{ needs.build.outputs.epoch }}')):
            build_step = next(s for s in job['steps'] if s.get('run') == 'sh src_docs/build.sh')
            self.assertEqual(build_step['env']['SOURCE_DATE_EPOCH'], epoch)
        self.assertEqual(verify['steps'][0]['with']['ref'], '${{ needs.build.outputs.sha }}')
        self.assertEqual(verify['permissions'], {'contents': 'read'})
        for job in (build, verify):
            runs = '\n'.join(step.get('run', '') for step in job['steps'])
            self.assertIn('sh src_docs/build.sh', runs)
            self.assertIn('--require-hashes -r src_docs/requirements.txt', runs)
        self.assertIn('git diff --exit-code HEAD -- docs', '\n'.join(s.get('run', '') for s in verify['steps']))
        self.assertIn('git ls-files --others -- docs', '\n'.join(s.get('run', '') for s in verify['steps']))
        self.assertFalse(any('publish.sh' in s.get('run', '') for s in verify['steps']))

    def test_private_pages_hold_removes_automatic_request_and_permission(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/docs.yml').read_text())
        self.assertNotIn('pages', workflow['permissions'])
        for name, job in workflow['jobs'].items():
            with self.subTest(job=name):
                self.assertNotIn('pages', job['permissions'])
                commands = '\n'.join(step.get('run', '') for step in job['steps'])
                self.assertNotIn('request-pages.sh', commands)
                self.assertNotIn('/pages/builds', commands)

    def test_complete_catalogue_guides_and_readme_contract_survive(self):
        import hashlib
        def canonical(text):
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            return re.sub(r'\s+', ' ', text.replace('`', '')).strip()
        readme = (ROOT / 'README.md').read_text().split('# Fontport for FontLab\n', 1)[1]
        index = (ROOT / 'src_docs/md/index.md').read_text()
        self.assertIn(canonical(readme), canonical(index))
        expected = {'src_docs/md/guides/FONTPARTS-COVERAGE.md': '9aced07643cf342670435579a5ca06ea36cf3f1cbd777c513d58c01b1d26e270', 'src_docs/md/guides/INTEGRATION.md': '30e06b5e0404c78597ad1cf4aa5d728a0a88c8cfc789a813cd50da85d9f6e709', 'src_docs/md/guides/LIVE-PEN-RECIPES.md': '98402a015e11e5d943545bc6ae9104096286dc7b5c0bd347becc7c214a775e32', 'src_docs/md/guides/NATIVE-BOUNDARIES.md': '9974964ca59122be17c4950dea030bc12f91b299cddc7133c281d4811c082db4', 'src_docs/md/guides/NATIVE-FEATURES.md': 'be5617191d3a82b9f35e089b1ce8e24315141842b43729e6720ad4a3b23a740c', 'src_docs/md/guides/ROUND10-NATIVE.md': 'a95c135943bc3310b36ccf81deffb22f77d7f4c9512044d618e81daae706026e', 'src_docs/md/guides/ROUND12-NATIVE.md': '3b5e8ae4c4ce867b2335ebbd2ffa95b327baef15aca70fc751d36a2c844d0c1c', 'src_docs/md/guides/ROUND13-NATIVE.md': '1169f10544d05838d65bacccf889aa4f6fbca292b41ec644494437c32ab557df', 'src_docs/md/guides/ROUND14-NATIVE.md': '16500b076869e83c2970feef8d7c50b37c74f9c6636d4dd264fd398ff33fe6f5', 'src_docs/md/guides/ROUND15-NATIVE.md': 'ff5acf13dec3c6b8e1fb601723be5c567fb9bf6b3b5010fd75f9a4b2cacd55bf', 'src_docs/md/guides/UFO-INTERCHANGE.md': '222f2a4a7482ebc5805e7de8a29acfd57fa3d6398ff0fbe388879f17d6f8832d'}
        for name, digest in expected.items():
            body = (ROOT / name).read_text().split('---\n', 2)[-1]
            self.assertEqual(hashlib.sha256(canonical(body).encode()).hexdigest(), digest, name)
        self.assertEqual(len(expected), 11)
        from collections import Counter
        guide = ROOT / 'src_docs/md/guides/FONTPARTS-COVERAGE.md'
        rows = [line.split('|') for line in guide.read_text().splitlines() if line.startswith('| `fontParts.test.')]
        identifiers = [row[1].strip().strip('`') for row in rows]
        self.assertEqual(len(identifiers), 1797)
        self.assertEqual(len(set(identifiers)), 1797)
        for column, expected in [(5, {'pass': 432, 'capability': 1365}), (6, {'pass': 1087, 'capability': 638, 'harness exclusion': 72})]:
            self.assertEqual(Counter(row[column].strip().split(':', 1)[0] for row in rows), expected)
        published = Page((SITE / 'guides/FONTPARTS-COVERAGE/index.html').read_text()).text
        self.assertEqual([value for value in published if value in set(identifiers)], identifiers)
        self.assertEqual(hashlib.sha256((ROOT / 'verification/issue-105/NATIVE-MANIFEST.json').read_bytes()).hexdigest(), 'd939e9274b92940bfe3f335e06df21b450855ee5782bdb9f89a1fa5ae24d0933')
