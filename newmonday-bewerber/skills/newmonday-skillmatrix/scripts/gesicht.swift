// Gesichtserkennung fuer den Fotozuschnitt — macOS Vision, ohne Zusatzpakete.
//
//     gesicht <bild.png> <maske.png>
//
// Gibt JSON auf stdout aus: Bildgroesse, je Gesicht Rechteck und Kinn (Pixel,
// Ursprung oben links), dazu schreibt es die Personenmaske (Graustufen, weiss =
// Person) nach <maske.png>. kopf_ausschnitt.py uebersetzt und startet das; von
// Hand braucht es niemand.
import CoreImage
import Foundation
import Vision

func fehler(_ text: String) -> Never {
    FileHandle.standardError.write((text + "\n").data(using: .utf8)!)
    exit(1)
}

let argumente = CommandLine.arguments
if argumente.count < 3 { fehler("Aufruf: gesicht <bild> <maske.png>") }
let bildURL = URL(fileURLWithPath: argumente[1])
let maskeURL = URL(fileURLWithPath: argumente[2])

guard let bild = CIImage(contentsOf: bildURL) else { fehler("Bild nicht lesbar: \(argumente[1])") }
let breite = Double(bild.extent.width), hoehe = Double(bild.extent.height)

let gesichter = VNDetectFaceLandmarksRequest()
let person = VNGeneratePersonSegmentationRequest()
person.qualityLevel = .accurate
person.outputPixelFormat = kCVPixelFormatType_OneComponent8

let handler = VNImageRequestHandler(ciImage: bild, options: [:])
do { try handler.perform([gesichter, person]) } catch { fehler("Vision: \(error)") }

// Vision rechnet mit Ursprung unten links und normierten Koordinaten.
var liste: [[String: Double]] = []
for g in gesichter.results ?? [] {
    let r = g.boundingBox
    var eintrag: [String: Double] = [
        "x0": r.minX * breite, "x1": r.maxX * breite,
        "y0": (1 - r.maxY) * hoehe, "y1": (1 - r.minY) * hoehe,
        "sicherheit": Double(g.confidence),
    ]
    if let kontur = g.landmarks?.faceContour {
        let punkte = kontur.pointsInImage(imageSize: CGSize(width: breite, height: hoehe))
        if let tiefster = punkte.min(by: { $0.y < $1.y }) {
            eintrag["kinn"] = hoehe - Double(tiefster.y)
        }
    }
    liste.append(eintrag)
}

var maskeGeschrieben = false
if let puffer = person.results?.first?.pixelBuffer {
    let maske = CIImage(cvPixelBuffer: puffer)
    let skaliert = maske.transformed(by: CGAffineTransform(
        scaleX: CGFloat(breite) / maske.extent.width, y: CGFloat(hoehe) / maske.extent.height))
    let kontext = CIContext()
    do {
        try kontext.writePNGRepresentation(of: skaliert, to: maskeURL, format: .L8,
                                           colorSpace: CGColorSpaceCreateDeviceGray())
        maskeGeschrieben = true
    } catch {
        FileHandle.standardError.write("Maske nicht geschrieben: \(error)\n".data(using: .utf8)!)
    }
}

let ausgabe: [String: Any] = ["breite": breite, "hoehe": hoehe, "gesichter": liste,
                              "maske": maskeGeschrieben]
let daten = try! JSONSerialization.data(withJSONObject: ausgabe, options: [.sortedKeys])
print(String(data: daten, encoding: .utf8)!)
