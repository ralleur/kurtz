# Mutti Connect Apple integration

Shared transport: the reviewed tree pinned by `source.json` in
[ralleur/mutti](https://github.com/ralleur/mutti). Place that repository beside
kurtz, or set `MUTTI_CONNECT_SOURCE` to its `mutti/connect` directory.

Build an arm64 slice using `bash Tools/MuttiConnect/build.sh catalyst` (Mac),
`ios`, `tvos`, `ios-simulator` or `tvos-simulator`. Optional second argument:
`x86_64` for an Intel Mac/simulator. Go 1.27.1 and Xcode 27.0 were used.

The generated, ignored `XcodeConfig/MuttiConnect.local.xcconfig` supplies the
module search path and static linker flags. `canImport(MuttiConnectCore)` enables
the implementation; inherited Swift compilation-condition overrides cannot
silently disable it. Mac builds use `kurtz.xcworkspace` and the existing Catalyst
package preparation. Build only architectures for which you generated a slice.
The Mac sandbox allows incoming network sockets because the common player/API
gateway binds to **127.0.0.1 only**, and ICE receives direct UDP packets.

Remove the local xcconfig to build ordinary kurtz without the experimental
transport. The Mutti UI then reports that the required test build is missing.
Existing ordinary Jellyfin connections continue using their normal URL.

Keys are persisted only in the app Keychain, not ServerState or UserDefaults.
The latter retains a `mutti://<public-server-fingerprint>` identity and resolves
it to a fresh capability-protected local origin on each launch. `MCFree` owns all
C result strings; cancellation closes the pending enrollment and its listener.

Test flow and deployable server/broker:
[Mutti Connect guide](https://github.com/ralleur/mutti/blob/codex/mutti-foundation/docs/mutti/connect.md).
Local checks cover QR invite expiry/replay, pinned identity, owner approval,
profile restriction, Range, HLS, WebSockets, live revocation and reconnection.
Real WAN networks and Apple devices remain part of the user test, not a claimed
success here. No relay, public deployment or release upload is enabled.
