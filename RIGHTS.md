# Rights, contributions and dependencies

kurtz remains open source. Its source license is [MPL-2.0](LICENSE.md).
The current combined application distribution uses GPL-3.0-or-later because
it includes the GPL-enabled mpv build; see [release records](docs/release/README.md).
This policy does not replace those licenses or revoke earlier grants.

Ralf Hauser maintains kurtz. He may transfer his own economic rights and the
rights validly granted to him, together with project assets he controls. This
does not make him the owner of Swiftfin, Jellyfin, third-party libraries, all
historical contributions, or purely AI-generated material. Existing recipients
retain their open-source permissions. Any successor inherits applicable license
obligations; this repository is not a promise of unrestricted proprietary use.

## What belongs to whom

| Material | Rights and evidence |
| --- | --- |
| Swiftfin foundation, including modified upstream files | Respective authors; MPL-2.0 and original notices. History records provenance. Changes do not erase upstream rights. |
| Original kurtz work created by Ralf | Ralf's rights, to the extent they exist; public distribution remains under the applicable source license. File location or a commit author alone is not proof of exclusive ownership. |
| New original contributions accepted under the kurtz CLA | Contributor retains authorship; Ralf receives the additional non-exclusive, transferable and sublicensable rights in [CLA.md](CLA.md). Retain acceptance evidence. |
| Earlier contributions and imported upstream changes | Their existing terms. No retrospective CLA grant is assumed. Importing, merging or signing on somebody else's behalf does not create additional rights. |
| Dependencies, copied code, fonts, media and bundled binaries | Their own licenses and notices, recorded in [the dependency register](docs/licensing/dependencies.json), [release records](docs/release/README.md), and [media credits](marketing/sources-and-licenses.md). |
| Product identity | [TRADEMARKS.md](TRADEMARKS.md). Brand policy does not supersede previously granted copyright permissions. |

Git history, license texts, source archives, documented authorship and actual
CLA acceptances together form the evidence. No blanket copyright replacement,
mass header rewrite or assertion that a directory is exclusively owned is
permitted. Record copied material even when its license is permissive. Disclose
AI-assisted work and known sources; do not invent human authorship or promise
exclusive rights in output that may not be protected.

## Every new or changed dependency

1. Identify the exact upstream, version/commit, direct and transitive inputs,
   license texts and copyright notices. Include native binaries, downloaded
   build artifacts, fonts, assets, snippets, submodules and build-only tools.
2. Record how it is used: modified or unmodified, linked or separate, shipped
   or development-only. Assess source delivery, attribution, copyleft, patent,
   trademark and redistribution obligations for the actual build.
3. Explain which rights remain with third parties and how a future project
   transfer would preserve those obligations. An SPDX label or CLA alone is
   not a compatibility decision. New restrictions require an explicit decision.
4. Add a review to [dependencies.json](docs/licensing/dependencies.json), with
   evidence and the exact input fingerprints. Follow [the maintenance guide](docs/licensing/README.md).
5. Update matching notices, source delivery and credits. Run the rights gate;
   unresolved distribution obligations block packaging and release.

Open-source dependencies are welcome. They are not automatically relicensable
by Ralf. Unknown or conflicting terms must be resolved, the component replaced,
or its use confined to an explicitly documented development scope.

## Contributions and enforcement

New original external contributions require [CLA v1](CLA.md) acceptance before
merge. Ralf does not need to grant rights to himself. Upstream imports retain
their authors and licenses and require provenance review; they must not be
labelled as CLA-covered original contributions. Do not evade the check by
squashing away authors or changing author metadata. Automated updates do not
grant rights in the packages they introduce.

The CI check `Rights and dependencies` detects changed registered inputs and
new dependency manifests, fetch scripts, license notices, vendored paths and
native binaries. It also checks pinned application sources against the release
source index. It cannot discover every copied snippet or establish authorship;
maintainer review remains necessary. There is no automatic approval command.

GitHub must require both `Rights and dependencies` and `license/cla` on the
default branch. The [activation guide](docs/licensing/README.md#github-activation)
distinguishes files present in a checkout from live server-side enforcement.

## Legal references

- [MPL-2.0, sections 2 and 3](https://www.mozilla.org/en-US/MPL/2.0/): grants, notices, modified source and combined works.
- [UrhG §29](https://www.gesetze-im-internet.de/urhg/__29.html) and [§31](https://www.gesetze-im-internet.de/urhg/__31.html): authorship and rights of use.
- [Hauser CLA v2](https://github.com/ralleur/hauser/blob/main/CLA.md): basis for the transfer provisions, adapted here to kurtz's third-party foundation.
