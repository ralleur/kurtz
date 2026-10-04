// SPDX-License-Identifier: MPL-2.0
import SwiftUI
#if os(iOS)
import VisionKit
#endif

struct MuttiPairingView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var invitation = ""
    @State private var status = ""
    @State private var pairing: Task<Void, Never>?
    @State private var isScanning = false
    let initialInvitation: String
    let connected: (URL) -> Void

    init(invitation: String = "", connected: @escaping (URL) -> Void) {
        initialInvitation = invitation
        self.connected = connected
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Mit Mutti koppeln").font(KurtzBrand.font(size: 24, weight: .semibold, relativeTo: .title2))
                    Text("Öffne in Mutti „Geräte“ und erstelle einen QR-Code. Scanne ihn hier oder füge den Kopplungslink ein. Bestätige anschließend dieses Gerät in Mutti.")
                        .foregroundStyle(.secondary)
                    #if os(iOS) && !targetEnvironment(macCatalyst)
                    if DataScannerViewController.isSupported && DataScannerViewController.isAvailable {
                        Button("QR-Code scannen", systemImage: "qrcode.viewfinder") { isScanning = true }
                            .disabled(pairing != nil)
                    }
                    #endif
                    TextField("Kopplungslink", text: $invitation, axis: .vertical)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        .disabled(pairing != nil)
                    if pairing == nil {
                        Button("Sicher verbinden", action: start).disabled(!MuttiConnection.isInvitation(invitation.trimmingCharacters(in: .whitespacesAndNewlines)))
                    } else {
                        ProgressView("Kopplung läuft …")
                        Button("Abbrechen", role: .cancel) { pairing?.cancel(); pairing = nil }
                    }
                }
                if !status.isEmpty {
                    Section { Text(status).font(.callout).accessibilityLabel(status) }
                }
                Section { Text("Die Verbindung ist direkt und verschlüsselt. In Netzen, die direkte Verbindungen blockieren, steht in dieser Version kein Relay zur Verfügung.").font(.footnote).foregroundStyle(.secondary) }
            }
            .navigationTitle("Mutti")
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Schließen") { pairing?.cancel(); dismiss() } } }
            .onAppear { invitation = initialInvitation }
            .onDisappear { pairing?.cancel() }
            #if os(iOS) && !targetEnvironment(macCatalyst)
            .sheet(isPresented: $isScanning) {
                MuttiQRScanner { code in invitation = code; isScanning = false }
                    .ignoresSafeArea()
            }
            #endif
        }
    }

    private func start() {
        status = "Direkte Verbindung zu Mutti wird aufgebaut …"
        pairing = Task { @MainActor in
            do {
                let stored = try await MuttiConnection.shared.pair(
                    invitation.trimmingCharacters(in: .whitespacesAndNewlines),
                    name: ProcessInfo.processInfo.isMacCatalystApp ? "kurtz auf Mac" : UIDevice.current.name
                ) { status = $0 }
                try Task.checkCancellation()
                pairing = nil
                connected(stored)
                dismiss()
            } catch is CancellationError { status = "Kopplung abgebrochen."; pairing = nil }
            catch { status = error.localizedDescription; pairing = nil }
        }
    }
}

#if os(iOS) && !targetEnvironment(macCatalyst)
private struct MuttiQRScanner: UIViewControllerRepresentable {
    let scanned: (String) -> Void
    func makeCoordinator() -> Coordinator { Coordinator(scanned: scanned) }
    func makeUIViewController(context: Context) -> DataScannerViewController {
        let scanner = DataScannerViewController(recognizedDataTypes: [.barcode(symbologies: [.qr])], qualityLevel: .balanced, recognizesMultipleItems: false, isHighlightingEnabled: true)
        scanner.delegate = context.coordinator
        do { try scanner.startScanning() } catch { /* Camera availability is also checked before presentation. */ }
        return scanner
    }
    func updateUIViewController(_ view: DataScannerViewController, context: Context) {}
    static func dismantleUIViewController(_ view: DataScannerViewController, coordinator: Coordinator) { view.stopScanning() }
    final class Coordinator: NSObject, DataScannerViewControllerDelegate {
        let scanned: (String) -> Void
        private var finished = false
        init(scanned: @escaping (String) -> Void) { self.scanned = scanned }
        func dataScanner(_ dataScanner: DataScannerViewController, didAdd addedItems: [RecognizedItem], allItems: [RecognizedItem]) {
            guard !finished else { return }
            for item in addedItems {
                if case let .barcode(code) = item, let payload = code.payloadStringValue, MuttiConnection.isInvitation(payload) {
                    finished = true; dataScanner.stopScanning(); scanned(payload); return
                }
            }
        }
    }
}
#endif
