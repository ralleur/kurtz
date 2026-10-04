// SPDX-License-Identifier: MPL-2.0
import Foundation
import Security
#if canImport(MuttiConnectCore)
import MuttiConnectCore
#endif

/// Only a public server fingerprint is persisted in ServerState. Private device
/// keys stay in this app's Keychain, and loopback capabilities change each launch.
final class MuttiConnection: @unchecked Sendable {
    static let shared = MuttiConnection()
    private let lock = NSLock()
    private var sessions: [String: (handle: UInt64, url: URL)] = [:]
    private let service = (Bundle.main.bundleIdentifier ?? "kurtz") + ".mutti.devices.v1"

    struct Failure: LocalizedError {
        let message: String
        var errorDescription: String? { message }
    }

    static func isInvitation(_ text: String) -> Bool { text.hasPrefix("kurtz://pair#") }

    func url(for stored: URL) -> URL {
        guard stored.scheme == "mutti", let pin = stored.host else { return stored }
        lock.lock()
        defer { lock.unlock() }
        if let session = sessions[pin] { return session.url }
        #if canImport(MuttiConnectCore)
        do {
            let data = try read(pin: pin)
            guard let input = String(data: data, encoding: .utf8) else { throw Failure(message: "Geräteschlüssel fehlt.") }
            let result = try decode(MCStart(input, 0, "kurtz"))
            guard let handle = result["handle"] as? UInt64,
                  let address = result["url"] as? String,
                  let url = URL(string: address), url.host == "127.0.0.1"
            else { throw Failure(message: "Mutti-Verbindung konnte nicht gestartet werden.") }
            sessions[pin] = (handle, url)
            return url
        } catch { /* Fail closed; never turn a saved identity into a public HTTP URL. */ }
        #endif
        return URL(string: "mutti-unavailable://missing-device-key")!
    }

    func pair(_ invitation: String, name: String, progress: @escaping @MainActor @Sendable (String) -> Void) async throws -> URL {
        #if canImport(MuttiConnectCore)
        let result = try decode(MCStart(invitation, 1, name))
        guard let handle = result["handle"] as? UInt64,
              let pin = result["pin"] as? String,
              let address = result["url"] as? String,
              let url = URL(string: address),
              let storedURL = URL(string: "mutti://" + pin)
        else { throw Failure(message: "Die Kopplung konnte nicht gestartet werden.") }
        var retained = false
        defer { if !retained { MCStop(handle) } }
        while true {
            try Task.checkCancellation()
            let status = try decode(MCStatus(handle))
            switch status["state"] as? String {
            case "ready":
                guard let credentials = status["credentials"] else { throw Failure(message: "Geräteschlüssel fehlt.") }
                let data = try JSONSerialization.data(withJSONObject: credentials)
                try write(data, pin: pin)
                retain(handle: handle, url: url, pin: pin)
                retained = true
                return storedURL
            case "error":
                throw Failure(message: status["message"] as? String ?? "Die Kopplung ist fehlgeschlagen.")
            case "approval":
                await progress(status["message"] as? String ?? "Bitte das Gerät in Mutti freigeben.")
            default:
                await progress("Direkte Verbindung zu Mutti wird aufgebaut …")
            }
            try await Task.sleep(for: .milliseconds(500))
        }
        #else
        throw Failure(message: "Dieser Build enthält Mutti Connect noch nicht. Bitte den Mutti-Testbuild verwenden.")
        #endif
    }

    func forget(_ stored: URL) {
        guard stored.scheme == "mutti", let pin = stored.host else { return }
        lock.lock()
        let old = sessions.removeValue(forKey: pin)
        lock.unlock()
        #if canImport(MuttiConnectCore)
        if let old { MCStop(old.handle) }
        #endif
        SecItemDelete(query(pin: pin) as CFDictionary)
    }

    private func retain(handle: UInt64, url: URL, pin: String) {
        lock.lock()
        let old = sessions.updateValue((handle, url), forKey: pin)
        lock.unlock()
        #if canImport(MuttiConnectCore)
        if let old { MCStop(old.handle) }
        #endif
    }

    #if canImport(MuttiConnectCore)
    private func decode(_ value: UnsafeMutablePointer<CChar>?) throws -> [String: Any] {
        guard let value else { throw Failure(message: "Mutti Connect antwortet nicht.") }
        defer { MCFree(value) }
        let data = Data(String(cString: value).utf8)
        guard let result = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw Failure(message: "Ungültige Antwort von Mutti Connect.")
        }
        if let error = result["error"] as? String { throw Failure(message: error) }
        return result
    }
    #endif

    private func query(pin: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: service,
         kSecAttrAccount as String: pin,
         kSecAttrSynchronizable as String: false]
    }

    private func read(pin: String) throws -> Data {
        var q = query(pin: pin)
        q[kSecReturnData as String] = true
        q[kSecMatchLimit as String] = kSecMatchLimitOne
        var result: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &result) == errSecSuccess, let data = result as? Data else {
            throw Failure(message: "Bitte dieses Gerät erneut mit Mutti koppeln.")
        }
        return data
    }

    private func write(_ data: Data, pin: String) throws {
        let q = query(pin: pin)
        let attributes: [String: Any] = [kSecValueData as String: data,
                                       kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly]
        let update = SecItemUpdate(q as CFDictionary, attributes as CFDictionary)
        if update == errSecSuccess { return }
        guard update == errSecItemNotFound else { throw Failure(message: "Geräteschlüssel konnte nicht sicher gespeichert werden.") }
        var insert = q
        attributes.forEach { insert[$0.key] = $0.value }
        guard SecItemAdd(insert as CFDictionary, nil) == errSecSuccess else {
            throw Failure(message: "Geräteschlüssel konnte nicht sicher gespeichert werden.")
        }
    }
}
