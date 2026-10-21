// Decode retail barcodes in photos with Apple Vision. Usage: swift decode_barcode.swift photo.jpg [more.jpg ...]
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let image = NSImage(contentsOfFile: path),
          let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("\(path)\tunreadable"); continue
    }
    let request = VNDetectBarcodesRequest()
    request.symbologies = [.ean13, .ean8, .upce, .code128, .gs1DataBar, .gs1DataBarExpanded]
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do {
        try handler.perform([request])
        let results = request.results ?? []
        if results.isEmpty { print("\(path)\tnone") }
        for r in results {
            print("\(path)\t\(r.symbology.rawValue)\t\(r.payloadStringValue ?? "?")\t\(String(format: "%.2f", r.confidence))")
        }
    } catch { print("\(path)\terror\t\(error)") }
}
