#!/usr/bin/env python3
"""Inspect or activate GitHub enforcement after the policy is deployed.

Read-only by default. --apply is an explicit administrative mutation. Never
replaces other rulesets, fabricates a signature or publishes local source files.
"""

import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
REPO = 'ralleur/kurtz'
NAME = 'kurtz rights and contributions'
SIGNATURES = '.github/cla-signatures-v1.json'


class APIError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def api(endpoint, method='GET', data=None, optional=False):
    command = ['gh', 'api', f'repos/{REPO}' + ('/' + endpoint if endpoint else ''), '--method', method]
    if data is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                            text=True, capture_output=True)
    if result.returncode:
        try:
            error = json.loads(result.stdout)
        except ValueError:
            error = {}
        if optional and str(error.get('status')) == '404':
            return None
        raise APIError(f'GitHub request failed: {method} {endpoint}: {error.get("message", result.stderr.strip())}', error.get('status'))
    return json.loads(result.stdout) if result.stdout else None


def ruleset(owner_id, actions_id):
    return {
        'name': NAME, 'target': 'branch', 'enforcement': 'active',
        # The owner can merge his own PR explicitly; direct pushes remain blocked.
        'bypass_actors': [{'actor_id': owner_id, 'actor_type': 'User', 'bypass_mode': 'pull_request'}],
        'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}},
        'rules': [
            {'type': 'deletion'}, {'type': 'non_fast_forward'},
            {'type': 'pull_request', 'parameters': {
                'required_approving_review_count': 1,
                'dismiss_stale_reviews_on_push': True,
                'require_code_owner_review': True,
                'require_last_push_approval': False,
                'required_review_thread_resolution': True,
                'allowed_merge_methods': ['merge', 'squash', 'rebase'],
            }},
            {'type': 'required_status_checks', 'parameters': {
                'strict_required_status_checks_policy': True,
                'do_not_enforce_on_create': False,
                'required_status_checks': [
                    {'context': 'Rights and dependencies', 'integration_id': actions_id},
                    {'context': 'license/cla', 'integration_id': actions_id},
                ],
            }},
        ],
    }


def deployed_policy(branch):
    errors = []
    if branch != 'kurtz':
        return ['default branch changed; update the CLA document URL and review activation first']
    for name in ['CLA.md', 'RIGHTS.md', 'TRADEMARKS.md', '.github/CODEOWNERS',
                 '.github/workflows/cla.yml', '.github/workflows/rights.yml',
                 'Tools/licensing/verify-rights.py', 'docs/licensing/dependencies.json']:
        remote = api(f'contents/{quote(name, safe="/")}?ref={quote(branch, safe="")}', optional=True)
        if remote is None:
            errors.append(f'not deployed: {name}')
        elif remote.get('encoding') != 'base64' or base64.b64decode(remote['content']) != (ROOT / name).read_bytes():
            errors.append(f'deployed file differs from this checkout: {name}')
    return errors


def ensure_signatures(branch, apply):
    ref = api('git/ref/heads/cla-signatures', optional=True)
    if ref is None:
        if not apply:
            return 'signature branch needs initialization'
        base = api('git/ref/heads/' + quote(branch, safe=''))
        api('git/refs', 'POST', {'ref': 'refs/heads/cla-signatures', 'sha': base['object']['sha']})
    remote = api(f'contents/{SIGNATURES}?ref=cla-signatures', optional=True)
    if remote is not None:
        signatures = json.loads(base64.b64decode(remote['content']))
        if not isinstance(signatures.get('signedContributors'), list):
            raise APIError('Existing signature file has an unexpected shape; refusing to modify it')
        return 'signature storage present; existing acceptances preserved'
    if apply:
        api(f'contents/{SIGNATURES}', 'PUT', {
            'branch': 'cla-signatures', 'message': 'Initialize kurtz CLA v1 acceptance storage',
            'content': base64.b64encode(b'{"signedContributors": []}\n').decode(),
        })
        return 'empty signature storage initialized; no acceptances invented'
    return 'signature file needs initialization'


def equivalent(actual, expected):
    """GitHub may add default fields or return the rules in another order."""
    for field in ('name', 'target', 'enforcement', 'conditions', 'bypass_actors'):
        if actual.get(field) != expected[field]:
            return False
    rules = {r['type']: r for r in actual['rules']}
    if set(rules) != {r['type'] for r in expected['rules']}:
        return False
    for rule in expected['rules']:
        for name, value in rule.get('parameters', {}).items():
            if rules[rule['type']].get('parameters', {}).get(name) != value:
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        repo = api('')
        if repo['full_name'].lower() != REPO or not repo.get('permissions', {}).get('admin'):
            raise APIError('Repository administrator access is required')
        errors = deployed_policy(repo['default_branch'])
        if errors:
            print('\n'.join(errors))
            print('No GitHub configuration changed. Deploy the reviewed policy first.')
            return 1
        print(ensure_signatures(repo['default_branch'], args.apply))
        # Paginate explicitly; do not silently overlook an existing matching rule.
        existing = []
        page = 1
        while True:
            batch = api(f'rulesets?per_page=100&page={page}')
            existing += [item for item in batch if item['name'] == NAME and item.get('source') == REPO]
            if len(batch) < 100:
                break
            page += 1
        if len(existing) > 1:
            raise APIError('Multiple matching rulesets; refusing an ambiguous update')
        checks = api('commits/' + quote(repo['default_branch'], safe='') + '/check-runs?per_page=100')
        action_ids = {check['app']['id'] for check in checks['check_runs'] if check['app']['slug'] == 'github-actions'}
        if len(action_ids) != 1:
            raise APIError('Cannot identify the GitHub Actions app from actual checks; refusing an unbound required check')
        expected = ruleset(repo['owner']['id'], action_ids.pop())
        if not args.apply:
            print('Policy deployed. Run with --apply to activate or reconcile the dedicated ruleset.')
            print('Matching ruleset:', existing[0]['id'] if existing else 'absent')
            return 0
        if existing:
            endpoint = f'rulesets/{existing[0]["id"]}'
            current = api(endpoint)
            if not equivalent(current, expected):
                raise APIError('Existing dedicated ruleset differs; preserve it and review changes manually')
            result = current
        else:
            result = api('rulesets', 'POST', expected)
        actual = api(f'rulesets/{result["id"]}')
        if not equivalent(actual, expected):
            raise APIError(f'Post-write verification differs; inspect rule {result["id"]}')
        print(f'Active and verified: https://github.com/{REPO}/rules/{result["id"]}')
        return 0
    except (APIError, OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
