# First kurtz TestFlight beta

The first beta uses Apple's **TestFlight Internal Only** export option for iOS
(iPhone and iPad) and tvOS. It is intended to qualify real devices before an
external beta or App Store submission. No public invitation link or external
review is created by the local export tool.

This does not resolve the native-decoder licensing assessment, dependency
privacy audit, or other external-distribution gates in
[the Apple release plan](apple-release-plan.md). Keep those gates open; do not
check the GitHub workflow's `releaseGatesChecked` checkbox for this test pass.

## App record

Create one App Store Connect record named `kurtz`, primary locale `en-US`, SKU
`kurtz-apple`, bundle ID `com.ralleur.vela`, with iOS and tvOS. iPad belongs to
the iOS platform. Preserve the registered bundle ID for upgrade compatibility.
Apple's public API cannot create the first app record; use the authenticated
App Store Connect website. After creation, verify its bundle ID through the API.

## Local archive and export

Use an unused build number. The first candidates use version 0.9.6, build 75 on
both platforms. The override does not modify the published Mac release.

```sh
KURTZ_BUILD_NUMBER=75 Tools/kurtz/archive-apple.sh ios
KURTZ_BUILD_NUMBER=75 Tools/kurtz/archive-apple.sh tvos
python3 Tools/kurtz/export-testflight.py ios build/apple-release/kurtz-ios.xcarchive \
  --team YOUR_TEAM --output build/testflight/ios
python3 Tools/kurtz/export-testflight.py tvos build/apple-release/kurtz-tvos.xcarchive \
  --team YOUR_TEAM --output build/testflight/tvos
```

The exporter validates bundle identity, resources, device families and signature;
rejects the debug playback harness; and exports for internal testing only.
It preserves the archive's version/build numbers. Embedded frameworks must
contain the app's arm64 architecture. If a vendor framework contains additional
architectures, the exporter creates `prepared.xcarchive` in a fresh output
directory, removes only the extra slices, and re-signs the framework and app
using the supplied local certificate. It leaves the source archive unchanged
and records before/after binary hashes. For existing API-key signing,
provide `--key /private/path/AuthKey_ID.p8 --key-id ID --issuer-file /private/path/issuer.txt`.
If cloud signing is unavailable but an authorized local distribution identity
exists, provide `--profile /private/path/profile.mobileprovision` and
`--certificate-sha1 CERTIFICATE_FINGERPRINT`. Install that profile in Xcode's
provisioning-profile directory first. This uses the existing identity rather
than requesting cloud-signing permissions.

Keep keys, profiles and diagnostic logs out of Git. The diagnostic log is created
with user-only permissions and may contain account identifiers.

Export alone does not upload. Once the app record and local package have been
checked, repeat the export command with `--upload` and a separate output folder.
A successful Xcode command is only an upload result: verify Apple processing,
export-compliance status and availability to the intended internal test group
before reporting that the beta is ready to install. Do not automatically invite
additional users or enable a public link.

## Device qualification

On iPhone/iPad: local video selection through Files (including a file provider),
external subtitles, pause/seek, audio and subtitle selection, resume after a
restart, rotation, background interruptions, history deletion and engine retry.
Also test Jellyfin login and streaming with dedicated test media.

On Apple TV: Jellyfin login, Siri Remote focus, playback, track selection,
next-episode/intro prompts, stop/resume and a sustained playback session.
Simulator evidence is recorded separately and does not replace these tests.

## References

- [Apple: add an app record](https://developer.apple.com/help/app-store-connect/create-an-app-record/add-a-new-app)
- [Apple: internal TestFlight testers](https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers)

## Preparation evidence

On 4 October 2026, both Release archives and local distribution exports passed.
The exported IPAs retain 0.9.6 (75) and use valid TestFlight distribution profiles.
[The candidate record](testflight-0.9.6-75.json) includes source identity and IPA hashes.
On 5 October 2026, the app record was created (`6819176198`) for iOS and tvOS.
The `kurtz Internal` group contains the existing account holder only; builds are
assigned manually. Upload and Apple processing status are recorded in the
candidate record.

The initial tvOS upload was rejected because the vendor Libmpv framework also
contained arm64e. The corrected arm64-only export passed local architecture,
signature and provisioning checks and was uploaded successfully. Libmpv lacks
a matching vendor dSYM, limiting native-library crash symbolication.
