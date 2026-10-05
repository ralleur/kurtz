import base64
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('github_policy', Path(__file__).parents[1] / 'configure-github.py')
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


class GitHubPolicyTests(unittest.TestCase):
    def test_existing_signatures_are_never_overwritten(self):
        content = {'signedContributors': [{'name': 'fixture', 'id': 123}]}
        responses = [{'object': {'sha': 'a' * 40}}, {'content': base64.b64encode(json.dumps(content).encode()).decode()}]
        with patch.object(policy, 'api', side_effect=responses) as api:
            self.assertIn('preserved', policy.ensure_signatures('kurtz', True))
            self.assertTrue(all(len(call.args) == 1 for call in api.call_args_list))

    def test_dry_run_cannot_create_signature_storage(self):
        with patch.object(policy, 'api', return_value=None) as api:
            self.assertIn('initialization', policy.ensure_signatures('kurtz', False))
            self.assertEqual(api.call_count, 1)

    def test_initialization_creates_only_empty_acceptance_list(self):
        responses = [None, {'object': {'sha': 'a' * 40}}, {}, None, {}]
        with patch.object(policy, 'api', side_effect=responses) as api:
            policy.ensure_signatures('kurtz', True)
            payload = api.call_args_list[-1].args[2]
            self.assertEqual(json.loads(base64.b64decode(payload['content'])), {'signedContributors': []})

    def test_required_checks_are_bound_to_actual_actions_app(self):
        rules = policy.ruleset(42, 123)
        checks = next(r for r in rules['rules'] if r['type'] == 'required_status_checks')
        self.assertEqual({c['context'] for c in checks['parameters']['required_status_checks']}, {'license/cla', 'Rights and dependencies'})
        self.assertTrue(all(c['integration_id'] == 123 for c in checks['parameters']['required_status_checks']))
        self.assertEqual(rules['bypass_actors'][0]['bypass_mode'], 'pull_request')

    def test_manual_rule_changes_are_not_silently_erased(self):
        expected = policy.ruleset(42, 123)
        changed = policy.ruleset(42, 123)
        changed['rules'].append({'type': 'required_signatures'})
        self.assertFalse(policy.equivalent(changed, expected))
        self.assertTrue(policy.equivalent(expected, expected))


if __name__ == '__main__':
    unittest.main()
