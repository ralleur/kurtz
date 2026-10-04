// kurtz additions, licensed under the Mozilla Public License 2.0.
import SwiftUI
import UIKit

enum KurtzBrand {
    static let yellow = Color(red: 1, green: 230 / 255, blue: 0)
    static let graphite = Color(red: 31 / 255, green: 31 / 255, blue: 31 / 255)
    static let ivory = Color(red: 250 / 255, green: 248 / 255, blue: 241 / 255)

    static var body: Font {
        font(.body)
    }

    /// Keep the platform's text hierarchy and Dynamic Type while using Sora.
    static func font(_ style: Font.TextStyle) -> Font {
        let uiStyle: UIFont.TextStyle = switch style {
        #if os(tvOS)
        case .largeTitle: .title1
        #else
        case .largeTitle: .largeTitle
        #endif
        case .title: .title1
        case .title2: .title2
        case .title3: .title3
        case .headline: .headline
        case .subheadline: .subheadline
        case .callout: .callout
        case .footnote: .footnote
        case .caption: .caption1
        case .caption2: .caption2
        default: .body
        }
        let traits = UITraitCollection(preferredContentSizeCategory: .large)
        let size = UIFont.preferredFont(forTextStyle: uiStyle, compatibleWith: traits).pointSize
        return font(size: size, weight: style == .headline ? .semibold : .regular, relativeTo: style)
    }

    static func font(size: CGFloat, weight: Font.Weight = .regular, relativeTo style: Font.TextStyle = .body) -> Font {
        let name: String = switch weight {
        case .bold, .heavy, .black: "Sora-Bold"
        case .medium, .semibold: "Sora-SemiBold"
        default: "Sora-Regular"
        }
        return .custom(name, size: size, relativeTo: style)
    }

    static func heading(_ size: CGFloat, relativeTo style: Font.TextStyle = .title) -> Font {
        .custom("Sora-Bold", size: size, relativeTo: style)
    }
}

extension Color {
    static let kurtzAccent = KurtzBrand.yellow
}
