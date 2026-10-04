// kurtz additions, licensed under the Mozilla Public License 2.0.
import SwiftUI

/// The video mark uses ivory in both appearances, matching the Mac player.
/// It never becomes a remote-control focus target or intercepts player gestures.
struct KurtzPlayerBrand: View {
    var body: some View {
        Image("KurtzPlayerMark")
            .resizable()
            .scaledToFit()
            .frame(width: UIDevice.isTV ? 56 : 40, height: UIDevice.isTV ? 46 : 33)
            .opacity(0.35)
            .allowsHitTesting(false)
            .accessibilityHidden(true)
    }
}
