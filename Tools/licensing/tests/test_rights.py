"""Mutation tests for the actual failure boundaries, without network access."""

import contextlib
import io
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('rights', Path(__file__).parents[1] / 'verify-rights.py')
rights = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rights)


class RightsGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.write('LICENSE.md', 'Original upstream license\n')
        self.write('Package.resolved', '{"pins": []}\n')
        self.actual = rights.snapshot(self.root)
        self.register = {
            'schema_version': 1,
            'reviews': {'r1': {
                'date': '2026-10-05', 'reviewed_by': 'test reviewer',
                'components': ['fixture'], 'origin': 'fixture upstream',
                'license_evidence': 'local license', 'use': 'test',
                'obligations': 'keep notices', 'transfer_effect': 'upstream retains rights',
                'decision': 'open-source-use', 'release_blockers': [],
                'evidence_files': {'LICENSE.md': self.actual['LICENSE.md']},
            }},
            'inputs': {path: {'sha256': sha, 'review': 'r1'} for path, sha in self.actual.items()},
        }

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def errors(self, release=False):
        return rights.validate_register(self.root, self.register, rights.snapshot(self.root), release)

    def test_unchanged_review_passes(self):
        self.assertEqual(self.errors(), [])

    def test_transitive_lock_change_fails(self):
        self.write('Package.resolved', '{"pins": [{"identity": "new-transitive"}]}')
        self.assertTrue(any('changed' in e for e in self.errors()))

    def test_new_manifest_in_new_directory_fails(self):
        self.write('new/module/go.mod', 'module new\nrequire x v1.0.0\n')
        self.assertTrue(any('unreviewed' in e for e in self.errors()))

    def test_removal_requires_review(self):
        (self.root / 'Package.resolved').unlink()
        self.assertTrue(any('removed' in e for e in self.errors()))

    def test_new_fetch_script_fails(self):
        self.write('Tools/new-engine.sh', 'curl -L https://example.org/engine.zip\n')
        self.assertTrue(any('new-engine.sh' in e for e in self.errors()))

    def test_new_binary_and_font_fail(self):
        for path in ['Native/libunknown.a', 'assets/new.woff2']:
            self.write(path, 'binary fixture')
        errors = '\n'.join(self.errors())
        self.assertIn('libunknown.a', errors)
        self.assertIn('new.woff2', errors)

    def test_new_vendored_source_fails(self):
        self.write('vendor/new/code.c', 'int imported;')
        self.assertTrue(any('vendor/new/code.c' in e for e in self.errors()))

    def test_changed_evidence_cannot_be_approved_by_input_hash_only(self):
        self.write('LICENSE.md', 'Changed license')
        self.register['inputs']['LICENSE.md']['sha256'] = rights.digest(self.root / 'LICENSE.md')
        self.assertTrue(any('evidence changed' in e for e in self.errors()))

    def test_missing_review_and_fields_fail(self):
        self.register['inputs']['Package.resolved']['review'] = 'missing'
        del self.register['reviews']['r1']['transfer_effect']
        errors = '\n'.join(self.errors())
        self.assertIn('unknown review', errors)
        self.assertIn('transfer_effect', errors)

    def test_development_review_does_not_authorize_release(self):
        review = self.register['reviews']['r1']
        review['decision'] = 'development-only'
        review['release_blockers'] = ['No redistribution permission yet']
        self.assertEqual(self.errors(), [])
        self.assertTrue(any('release blocked' in e for e in self.errors(release=True)))

    def test_duplicate_json_keys_fail(self):
        self.write('record.json', '{"inputs": {}, "inputs": {}}')
        with self.assertRaises(rights.Invalid):
            rights.read_json(self.root / 'record.json')

    def test_symlink_and_path_escape_fail(self):
        (self.root / 'other').mkdir()
        (self.root / 'other/Package.swift').symlink_to(self.root / 'LICENSE.md')
        with self.assertRaises(rights.Invalid):
            rights.snapshot(self.root)
        with self.assertRaises(rights.Invalid):
            rights.safe_file(self.root, '../outside')

    def test_application_pin_revision_and_origin_must_match_source_record(self):
        pin = {'identity': 'example', 'location': 'https://github.com/org/example.git', 'state': {'revision': 'a' * 40}}
        item = {'id': 'example', 'repo': 'org/example', 'commit': 'a' * 40}
        self.write(rights.APP_LOCK, json.dumps({'pins': [pin]}))
        self.write(rights.SOURCE_INDEX, json.dumps([item]))
        self.assertEqual(rights.application_sources(self.root), [])
        for change in [{'commit': 'b' * 40}, {'repo': 'somebody-else/example'}]:
            self.write(rights.SOURCE_INDEX, json.dumps([dict(item, **change)]))
            self.assertTrue(rights.application_sources(self.root))

    def test_regular_source_edit_does_not_require_dependency_review(self):
        self.write('Shared/View.swift', 'struct View { let title = "test" }')
        self.assertEqual(self.errors(), [])

    def test_new_package_or_version_needs_bundled_notice(self):
        pin = {'identity': 'example', 'location': 'https://github.com/org/example', 'state': {'revision': 'a' * 40}}
        self.write(rights.APP_LOCK, json.dumps({'pins': [pin]}))
        self.write(rights.NOTICES, 'Unrelated notices\n')
        self.assertTrue(rights.application_notices(self.root, self.register))
        self.write(rights.NOTICES, 'example\nhttps://github.com/org/example\n' + json.dumps(pin['state']) + '\nLICENSE\n\nFull fixture license\n')
        self.assertEqual(rights.application_notices(self.root, self.register), [])
        pin['state']['revision'] = 'b' * 40
        self.write(rights.APP_LOCK, json.dumps({'pins': [pin]}))
        self.assertTrue(rights.application_notices(self.root, self.register))

    def test_notice_exception_must_be_explicit_and_block_distribution(self):
        pin = {'identity': 'example', 'location': 'https://github.com/org/example', 'state': {'revision': 'a' * 40}}
        self.write(rights.APP_LOCK, json.dumps({'pins': [pin]}))
        self.write(rights.NOTICES, 'No package notice\n')
        self.register['notice_exceptions'] = {'example': {'revision': 'a' * 40, 'review': 'r1', 'reason': 'Missing permission'}}
        self.assertTrue(rights.application_notices(self.root, self.register))
        self.register['reviews']['r1'].update(decision='development-only', release_blockers=['Resolve missing permission'])
        self.assertEqual(rights.application_notices(self.root, self.register), [])
        self.register['notice_exceptions']['example']['revision'] = 'b' * 40
        self.assertTrue(rights.application_notices(self.root, self.register))

    def test_scanner_covers_common_new_ecosystems(self):
        for name in ['Cargo.toml', 'uv.lock', 'package-lock.json', 'Podfile', 'go.work',
                     'Dockerfile.release', 'CMakeLists.txt', '.gitmodules', 'a.csproj']:
            with self.subTest(name=name):
                self.assertTrue(rights.dependency_input('new/' + name))

    def test_committed_source_check_uses_requested_tree(self):
        for doc in ['CLA.md', 'RIGHTS.md', 'TRADEMARKS.md', '.github/workflows/cla.yml', '.github/workflows/rights.yml']:
            self.write(doc, 'fixture\n')
        self.write(rights.APP_LOCK, '{"pins": []}')
        self.write(rights.SOURCE_INDEX, '[]')
        self.write(rights.NOTICES, 'fixture notices')
        self.register['inputs'] = {p: {'sha256': s, 'review': 'r1'} for p, s in rights.snapshot(self.root).items()}
        self.write(rights.REGISTER, json.dumps(self.register))
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], cwd=self.root, check=True)
        self.write('Package.resolved', '{"changed": true}')
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(rights.check_ref(self.root, 'HEAD', True), 0)
            self.assertNotEqual(rights.check(self.root, True), 0)


if __name__ == '__main__':
    unittest.main()
