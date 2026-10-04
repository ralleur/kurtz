# kurtz identity and upgrade compatibility

The public product name is **kurtz**. The repository and website move to
`ralleur/kurtz` and `https://ralleur.github.io/kurtz/`. New binaries, releases,
installer volumes and promotional exports use the lowercase name. The Apple
project/schemes retain Swiftfin's engineering names to ease upstream integration;
app product names, executables and displayed names are kurtz.

The following legacy identifiers are intentional compatibility contracts:

- `com.ralleur.vela` (iOS/tvOS) and `com.ralleur.vela.mac` (Mac): retain app
  container, keychain access, provisioning and the installation identity.
- Stored `vela.*`, `velaTrackMemory` and `velaMacShowPlayerLogo` preference keys:
  retain local bookmarks, recent files, positions, language, presets and shortcuts.
- `vela://` remains accepted alongside the primary `kurtz://` scheme.
- `com.ralleur.vela.snapshot` remains a development-only diagnostic notification.
- `SwiftfinAppIndex` and its indexed item's unique identifier retain the existing
  Spotlight entry; its visible title becomes kurtz.

Do not replace these identifiers mechanically. They are not visible branding.
Original historical releases, source records and footage remain labeled with the
version/product actually captured. New release and promo metadata identify the
new build and any intentionally reused historical footage.

The active workspace remains `/Users/ai/workspace/vela-swiftfin` so existing
Codex chats, signing tools and local dependencies keep working. Its Git remote
and public name change; this local compatibility path is not shipped branding.

No Apple Store release or new YouTube upload is implied by this rebranding.

## Public links

The renamed repository and historical asset URLs retain GitHub's automatic
redirect. GitHub Pages does not provide that redirect on repository rename.
The small [Ralleur Pages compatibility repository](https://github.com/ralleur/ralleur.github.io)
therefore serves only the old `/Vela/`, `/Vela/credits.html` and
`/Vela/privacy.html` routes and forwards them to their kurtz equivalents.
It does not occupy the old GitHub repository name or replace another project
site. The old product URL was followed in a browser to the live kurtz page.

## Installed upgrade

The exact notarized 0.9.7 DMG app was installed at `/Applications/kurtz.app` and
its About panel confirms 0.9.7 (9). Existing saved server sign-ins remained
available; the initial 0.9.6 upgrade had also verified local recent files and
settings. The previous kurtz app is backed up at
`build/rebrand-completion/previous-install/kurtz-0.9.6.app`. The original
`/Applications/Vela.app` remains preserved locally as
`build/rebrand-kurtz/previous-install/Vela-0.9.5.app`.

The paired Apple TV was still running Vela 0.9.4 (72). It now has the signed
kurtz 0.9.7 (75) build under the same bundle ID. Device metadata and the actual
device-generated icon confirm the new name, version and curl/yellow-ray icon.
The device must be awake for the final foreground-screen/playback inspection;
tvOS explicitly refused foreground launch while asleep.

No historical download, release tag or published video was replaced. Current
verification is recorded in [the product audit](product-audit.md) and the
[0.9.7 publication record](release/publication-kurtz-0.9.7.json).
