# Maintaining kurtz's rights and dependency records

This implements **MK-007**: open-source kurtz with documented, transferable
rights in original contributions, while preserving third-party obligations.
Read [RIGHTS.md](../../RIGHTS.md), [CLA v1](../../CLA.md) and
[the brand policy](../../TRADEMARKS.md) together. The source license remains MPL-2.0.

## What the checks establish

`Rights and dependencies` compares the actual repository to the exact reviewed
SHA-256 inputs in [dependencies.json](dependencies.json). It discovers manifests
and lockfiles across the tree, including new directories and package ecosystems,
Xcode projects, workflows, native binaries, fonts, vendored trees, license files
and dependency-fetch scripts. Locally it includes non-ignored untracked files.
Known packaging and transport scripts are always monitored. Changed/deleted
inputs and changed license evidence fail closed.

The app's SwiftPM pins must also match the repository URL and commit in the
release source index. This catches a stale source bundle even if a manifest's
fingerprint was updated. A source package is checked against its `--ref` commit,
not against the current checkout. A new submodule needs a source-delivery path;
the source-package check deliberately rejects submodules until that exists.

This is a change gate, not a legal opinion or automatic discovery of authorship.
Copied snippets in ordinary source files, obfuscated downloads and new package
managers require maintainer review and, where necessary, scanner extensions.
The initial register records the existing state with explicit unresolved items;
it is not a retrospective certificate of ownership or release clearance.

## Adding or updating a component

1. Read the exact version's terms, including transitive and native components.
   Record immutable upstream URLs, full license/notice evidence, actual use,
   modifications and whether anything is shipped. For generated assets record
   the provenance and the limits of any claimed rights.
2. Add a distinct review under `reviews` in `dependencies.json`. Required fields:
   `date`, `reviewed_by` (the actual reviewer, never a fictitious owner approval),
   `components`, `origin`, `license_evidence`, `use`, `obligations`,
   `transfer_effect`, `decision`, `evidence_files`, `release_blockers`.
3. Use `open-source-use` only when the stated use is supported by evidence.
   Use `development-only` with concrete `release_blockers` for unresolved
   distribution questions. Neither decision means that Ralf owns the dependency.
   `evidence_files` maps repository-relative evidence paths to SHA-256 digests.
4. Print the actual inputs with
   `python3 Tools/licensing/verify-rights.py --snapshot`. Update only the reviewed
   input entries, each with `sha256` and its `review` ID. Removing a dependency
   also requires documenting and updating the register. There is deliberately
   no `approve-all` or `refresh` option.
5. Update bundled notices and matching source archives/recipes, asset credits
   and, where needed, the scanner. Run the tests and both relevant checks below.
   A green development gate does not resolve a listed release blocker.

```sh
python3 -m unittest discover -s Tools/licensing/tests -v
python3 Tools/licensing/verify-rights.py
python3 Tools/licensing/verify-rights.py --release
# For the committed tree that will be included in a source bundle:
python3 Tools/licensing/verify-rights.py --ref HEAD --release
```

DMG packaging, Apple archive preparation, committed source packaging and
TestFlight all invoke the release gate before distribution actions. TestFlight
does not sign or upload while the gate fails. Existing downloadable releases
are not withdrawn or relicensed by this policy.

## Contributions and evidence

The CLA action is pinned to its reviewed commit. The privileged workflow never
checks out or runs PR code. Only `ralleur` is exempt from signing rights to
himself. No blanket bot exemption is used: a bot cannot grant rights in other
people's work. Imported upstream history may require a deliberately scoped,
documented exception in the contribution process; do not forge signatures or
strip authors to satisfy the check.

Store acceptances on `cla-signatures` in `.github/cla-signatures-v1.json` and
retain the associated PR/comment evidence. Never create a contributor entry
on someone's behalf. Preserve previous agreement versions and acceptance data;
material changes require a new version, a new signing sentence and a new file.
A copied CLA document or successful maintainer-only PR is not evidence that
external contributors have accepted it.

Before a project transfer, preserve Git history, original license texts,
source records, actual CLA acceptances and separately documented brand/asset
rights. Disclose unresolved issues and distinguish original rights from
non-exclusive grants and upstream licenses. Selling kurtz does not silently
include the broader ralleur brand.

## GitHub activation

Repository files alone do not enforce merges. Deploy the policy and workflows
on the default `kurtz` branch, then establish the `cla-signatures` branch with
`{"signedContributors": []}` if it does not exist. Never overwrite signatures.
The action must be allowed to write that branch and PR comments.

Require these exact checks on the default branch:

- `Rights and dependencies` from the read-only `Rights` workflow.
- `license/cla` from the CLA workflow (the explicit job name, not an assumed
  commit status supplied by the third-party action).

Require up-to-date branches, PRs and code-owner review by `@ralleur`; block
force pushes and branch deletion. The sole maintainer may need an explicit
administrator exception for his own PRs because GitHub forbids self-approval.
Such an exception is not third-party license clearance, and local/release
checks must still pass. Protect the rules, workflow, CLA and register through
the same review process. Do not require CLA approval on the signature-storage
branch itself, which the action must be able to update.

Use `python3 Tools/licensing/configure-github.py` to inspect readiness and
`python3 Tools/licensing/configure-github.py --apply` to add a dedicated ruleset
after deployment. The script refuses incomplete deployments, preserves other
rulesets, seeds only an absent signature file and verifies the resulting rule.
It requires an authenticated `gh` account with repository administration rights.
An explicit admin bypass remains possible; automation cannot constrain a repo
owner who deliberately disables protection.

## Evidence for the initial state

See [baseline-2026-10-05.md](baseline-2026-10-05.md). The known gaps are recorded
as release blockers, not inferred owner approval. Resolve each with evidence
and update only its affected review before the next distribution.
