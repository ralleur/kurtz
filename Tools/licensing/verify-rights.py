#!/usr/bin/env python3
"""Offline dependency-change gate. Reports fingerprints; never approves them.

Only repository files are read; no package code, package manager or downloaded
code is executed. See docs/licensing/README.md for the human review boundary.
"""

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REGISTER = 'docs/licensing/dependencies.json'
APP_LOCK = 'Swiftfin.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved'
SOURCE_INDEX = 'docs/release/source-index.json'
NOTICES = 'Shared/Resources/KurtzThirdPartyNotices.txt'
MANIFESTS = {
    'Package.swift', 'Package.resolved', 'Package.pins', 'project.pbxproj',
    'package.json', 'package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock',
    'pnpm-lock.yaml', 'bun.lock', 'bun.lockb', 'deno.json', 'deno.jsonc', 'deno.lock',
    'Gemfile', 'Gemfile.lock', 'Brewfile', 'Brewfile.lock.json',
    'Podfile', 'Podfile.lock', 'Cartfile', 'Cartfile.resolved',
    'go.mod', 'go.sum', 'go.work', 'go.work.sum', 'Cargo.toml', 'Cargo.lock',
    'pyproject.toml', 'poetry.lock', 'uv.lock', 'Pipfile', 'Pipfile.lock',
    'setup.py', 'setup.cfg', 'environment.yml', 'environment.yaml',
    'composer.json', 'composer.lock', 'pom.xml', 'build.gradle', 'build.gradle.kts',
    'gradle.lockfile', 'packages.lock.json', 'Directory.Packages.props',
    '.gitmodules', '.npmrc', '.yarnrc.yml', 'Dockerfile', 'Containerfile',
    'CMakeLists.txt', 'Makefile', 'Justfile', 'MODULE.bazel', 'WORKSPACE',
}
NATIVE = {'.a', '.dylib', '.so', '.dll', '.lib', '.wasm', '.jar', '.aar', '.ttf', '.otf', '.woff', '.woff2'}
FETCH = re.compile(
    r'\b(?:curl|wget)\b|\bgit\s+(?:clone|fetch|submodule)\b|'
    r'\b(?:pip3?|npm|pnpm|yarn|brew|bundle)\s+(?:install|add|bundle)\b|'
    r'[\"\'](?:curl|wget|git|pip3?|npm|pnpm|yarn|brew)[\"\']\s*,|'
    r'urlopen\s*\(|requests\.(?:get|post)\s*\(|'
    r'https?://[^\s\"\']+\.(?:zip|tar|gz|xcframework)\b', re.I)


class Invalid(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=unique_object)


def safe_file(root, relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or str(p) != relative:
        raise Invalid(f'unsafe repository path: {relative}')
    path = root / relative
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise Invalid(f'missing, symbolic or external file: {relative}')
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_files(root):
    # Include untracked, non-ignored additions locally as well as staged files.
    output = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root)
    return sorted(set(p.decode() for p in output.split(b'\0') if p))


def dependency_input(relative, text=''):
    p = PurePosixPath(relative)
    name = p.name
    lower = name.lower()
    if relative.startswith('Tools/licensing/') or relative == REGISTER:
        return False
    if name in MANIFESTS or lower.startswith(('dockerfile.', 'containerfile.')):
        return True
    if fnmatch.fnmatch(lower, '*requirements*.txt') or lower.endswith(('.csproj', '.fsproj', '.vbproj', '.lock', '.lock.json', '.lock.yaml')):
        return True
    if re.search(r'(^|[._-])(license|licence|copying|notice|copyright|ofl)([._-]|$)', lower) or 'thirdpartynotices' in lower:
        return True
    if p.suffix.lower() in NATIVE or any(part.lower() in {'vendor', 'vendored', 'third_party', 'third-party'} or part.endswith(('.framework', '.xcframework')) for part in p.parts):
        return True
    if relative.startswith('.github/workflows/'):
        return True
    if relative in {SOURCE_INDEX, 'Tools/MuttiConnect/source.json', 'marketing/sources-and-licenses.md', 'marketing/brand/README.md'}:
        return True
    if relative.startswith('Tools/kurtz/') or relative.startswith('Tools/MuttiConnect/'):
        return p.suffix in {'.py', '.sh', '.json', '.txt'}
    if p.suffix in {'.py', '.sh', '.rb', '.js', '.mjs', '.cjs', '.swift', '.yml', '.yaml', '.toml', '.json'}:
        return bool(FETCH.search(text))
    return False


def snapshot(root, files=None):
    result = {}
    for relative in repository_files(root) if files is None else files:
        path = root / relative
        if path.is_symlink() and dependency_input(relative):
            safe_file(root, relative)
        if not path.exists():
            continue  # A tracked deletion is checked against the register below.
        if path.is_dir():
            # Gitlinks are directories, not ordinary files. Record the indexed pin.
            entry = subprocess.check_output(['git', 'ls-files', '--stage', '--', relative], cwd=root, text=True).strip()
            if entry.startswith('160000 '):
                result[relative] = hashlib.sha256(entry.split()[1].encode()).hexdigest()
            continue
        text = ''
        if path.suffix in {'.py', '.sh', '.rb', '.js', '.mjs', '.cjs', '.swift', '.yml', '.yaml', '.toml', '.json'} and not path.is_symlink():
            text = path.read_text(errors='replace')
        if dependency_input(relative, text):
            result[relative] = digest(safe_file(root, relative))
    return result


def validate_register(root, register, actual, release=False):
    errors = []
    if register.get('schema_version') != 1:
        return ['unsupported dependency register schema']
    reviews = register.get('reviews', {})
    inputs = register.get('inputs', {})
    if not isinstance(inputs, dict) or not isinstance(reviews, dict) or not reviews:
        return ['register needs input and review objects']
    for review_id, review in reviews.items():
        for field in ('date', 'reviewed_by', 'components', 'origin', 'license_evidence', 'use', 'obligations', 'transfer_effect', 'decision'):
            if not review.get(field):
                errors.append(f'{review_id}: missing {field}')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', review.get('date', '')):
            errors.append(f'{review_id}: invalid review date')
        if review.get('decision') not in {'open-source-use', 'development-only'}:
            errors.append(f'{review_id}: decision must be open-source-use or development-only')
        evidence = review.get('evidence_files', {})
        if not isinstance(evidence, dict) or not evidence:
            errors.append(f'{review_id}: missing immutable local evidence')
        else:
            for path, expected in evidence.items():
                try:
                    if digest(safe_file(root, path)) != expected:
                        errors.append(f'{review_id}: evidence changed: {path}')
                except Invalid as error:
                    errors.append(str(error))
        blockers = review.get('release_blockers')
        if not isinstance(blockers, list):
            errors.append(f'{review_id}: release_blockers must be an explicit list')
        elif review.get('decision') == 'development-only' and not blockers:
            errors.append(f'{review_id}: development-only review needs a reason')
        if release and blockers and any(isinstance(v, dict) and v.get('review') == review_id for v in inputs.values()):
            errors.extend(f'{review_id}: release blocked: {reason}' for reason in blockers)
    for path in sorted(actual.keys() - inputs.keys()):
        errors.append(f'unreviewed dependency input: {path}')
    for path in sorted(inputs.keys() - actual.keys()):
        errors.append(f'registered input removed or no longer detected; review removal: {path}')
    for path, record in inputs.items():
        if not isinstance(record, dict):
            errors.append(f'{path}: input must be an object')
            continue
        if record.get('review') not in reviews:
            errors.append(f'{path}: unknown review {record.get("review")}')
        if not re.fullmatch('[0-9a-f]{64}', record.get('sha256', '')):
            errors.append(f'{path}: invalid SHA-256')
        elif path in actual and record['sha256'] != actual[path]:
            errors.append(f'dependency input changed; review exact new state: {path}')
    return errors


def application_sources(root):
    errors = []
    pins = read_json(safe_file(root, APP_LOCK))['pins']
    sources = read_json(safe_file(root, SOURCE_INDEX))
    indexed = {}
    for item in sources:
        if item['id'] in indexed:
            errors.append(f'duplicate source index id: {item["id"]}')
        indexed[item['id']] = item
    for pin in pins:
        item = indexed.get(pin['identity'])
        location = pin['location'].rstrip('/').removesuffix('.git')
        if not item or item.get('commit') != pin['state']['revision'] or location != 'https://github.com/' + item.get('repo', ''):
            errors.append(f'application pin lacks matching release source: {pin["identity"]}')
    return errors


def application_notices(root, register):
    pins = read_json(safe_file(root, APP_LOCK))['pins']
    sections = safe_file(root, NOTICES).read_text().split('=' * 72)
    notices = {}
    for section in sections:
        lines = section.strip().splitlines()
        if len(lines) >= 5 and lines[1].startswith('https://'):
            try:
                state = json.loads(lines[2])
            except ValueError:
                continue
            notices.setdefault(lines[0].lower(), []).append((lines[1].rstrip('/').removesuffix('.git'), state.get('revision')))
    exceptions = register.get('notice_exceptions', {})
    errors = []
    for pin in pins:
        identity = pin['identity']
        revision = pin['state']['revision']
        expected = (pin['location'].rstrip('/').removesuffix('.git'), revision)
        if expected in notices.get(identity, []):
            continue
        exception = exceptions.get(identity, {})
        review = register['reviews'].get(exception.get('review'), {})
        if (exception.get('revision') != revision or not exception.get('reason') or
                review.get('decision') != 'development-only' or not review.get('release_blockers')):
            errors.append(f'no matching bundled license notice for application pin: {identity}@{revision}')
    for identity, exception in exceptions.items():
        if not any(p['identity'] == identity and p['state']['revision'] == exception.get('revision') for p in pins):
            errors.append(f'stale notice exception: {identity}')
    return errors


def check(root, release, files=None):
    actual = snapshot(root, files)
    register = read_json(safe_file(root, REGISTER))
    errors = validate_register(root, register, actual, release)
    errors += application_sources(root)
    errors += application_notices(root, register)
    for document in ('CLA.md', 'RIGHTS.md', 'TRADEMARKS.md', 'LICENSE.md', '.github/workflows/cla.yml', '.github/workflows/rights.yml'):
        safe_file(root, document)
    if errors:
        print('\n'.join('ERROR: ' + error for error in errors), file=sys.stderr)
        return 1
    print(f'Rights and dependencies: PASS ({len(actual)} exact inputs).')
    if not release:
        blockers = [b for review in register['reviews'].values() for b in review.get('release_blockers', [])]
        if blockers:
            print(f'Development check only; {len(blockers)} documented release blocker(s). Run --release before distribution.')
    return 0


def check_ref(root, ref, release):
    # Validate the packaged commit, not unrelated files in the working tree.
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], cwd=root, text=True).strip()
    with tempfile.TemporaryDirectory(prefix='kurtz-rights-') as tmp:
        folder = Path(tmp)
        archive = folder / 'application.tar'
        with archive.open('wb') as stream:
            subprocess.run(['git', 'archive', '--format=tar', commit], cwd=root, stdout=stream, check=True)
        tree = folder / 'tree'
        tree.mkdir()
        files = []
        with tarfile.open(archive) as tar:
            for entry in tar:
                p = PurePosixPath(entry.name)
                if p.is_absolute() or '..' in p.parts:
                    raise Invalid('unsafe path in committed archive')
                if entry.issym() or entry.islnk():
                    if dependency_input(entry.name):
                        raise Invalid(f'symbolic dependency in committed archive: {entry.name}')
                    continue
                if not entry.isfile():
                    continue
                target = tree / entry.name
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(entry) as source:
                    target.write_bytes(source.read())
                files.append(entry.name)
        gitlinks = subprocess.check_output(['git', 'ls-tree', '-r', commit], cwd=root, text=True)
        if any(line.startswith('160000 ') for line in gitlinks.splitlines()):
            raise Invalid('source delivery contains submodules; include and verify their sources before release')
        return check(tree, release, files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--snapshot', action='store_true', help='print input hashes for a review; does not approve or write anything')
    parser.add_argument('--release', action='store_true', help='also reject unresolved release obligations')
    parser.add_argument('--ref', help='verify an exact committed tree for source packaging')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.ref:
            if args.snapshot:
                raise Invalid('--ref and --snapshot cannot be combined')
            return check_ref(root, args.ref, args.release)
        if args.snapshot:
            print(json.dumps(snapshot(root), indent=2, sort_keys=True))
            return 0
        return check(root, args.release)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError) as error:
        print(f'ERROR: rights verification failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
