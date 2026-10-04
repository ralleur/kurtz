# Current product verification

The remaining kurtz branding gaps were corrected on 4 October 2026 in 0.9.7.
The app-source commit is `e471199657b56c1fdbda721c1a2cb390e2fed29a`.
Historical Vela findings remain in [the original audit](history/product-audit-vela.md).

| Area | Evidence | Limit |
| --- | --- | --- |
| Mac | Universal Release 0.9.7 (9), signed, notarized and stapled; installed app, About and Sora settings UI inspected | Apple silicon runtime; no Intel/minimum-OS hardware qualification |
| iPhone/iPad | Simulator 0.9.7 (9); home and playback inspected; 23 decoder/playback/subtitle/resume checks passed on each simulator | No physical iPhone/iPad or Store/TestFlight release |
| Apple TV | Signed Release 0.9.7 (75) installed over Vela 0.9.4 (72) on the paired physical Apple TV; device query confirms kurtz and version | Foreground launch refused because the device is asleep; hardware screen/playback inspection awaits wake |
| tvOS simulator | Build and home screen checked; new native launch storyboard compiled and present in built app | Hardware focus/playback qualification remains separate |
| Product names | 32 translation files corrected; 33,597 localized values checked in source and each built app | Actual Swiftfin license/upstream attributions are intentionally preserved |
| Typography | App-owned semantic text styles and player labels use local Sora with platform sizes and Dynamic Type | System-owned menus and monospaced diagnostics keep native styling |
| Player mark | Shared ivory curl/yellow rays added to iOS/tvOS, hidden while controls or supplements are visible; Mac mark retained | Small, noninteractive, excluded from accessibility focus |
| Logic and style | 46 existing logic tests pass; SwiftLint and formatting pass | CI archive check below is separate |
| Upgrade | Existing Mac account/library remains available; stable app IDs, preferences and URL compatibility retained | No destructive account migration |
| DMG | Notarized universal app inside verified compressed image; Finder artwork, volume, kurtz.app and Applications link inspected | Historical installers unchanged |
| Media | Existing six kurtz Shorts and 0.9.6 Mac screenshot captures retained with accurate provenance | Existing listening limitation retained; no social uploads |

The [0.9.7 publication record](release/publication-kurtz-0.9.7.json) contains
asset digests, app versions and installation evidence. The supplementary
[CI run](https://github.com/ralleur/kurtz/actions/runs/37186138174) is in progress;
its archive results are not yet claimed here. CI now inspects localized product
names and packaged branding resources as well as compiling the apps.

The [0.9.6 record](release/publication-kurtz-0.9.6.json) remains unchanged. Its
successful compilation/archive checks did not catch the ten legacy text keys
or establish an installation on the physical Apple TV; those omissions prompted
this follow-up. See the [Apple release plan](release/apple-release-plan.md) for
separate Store release gates.
