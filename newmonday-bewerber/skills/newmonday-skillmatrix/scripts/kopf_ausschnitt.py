#!/usr/bin/env python3
"""Schneidet ein Portraet so zu, dass der Kopf in der Fotokarte zentriert steht.

    python3 scripts/kopf_ausschnitt.py <original> <ziel-ordner> [--kopf x0,y0,x1,y1]

Die Regel (Masse aus assets/tokens.json, komponenten.fotokarte):

- **Waagerecht** steht die Kopfmitte in der Bildmitte.
- **Senkrecht** sitzt der Haaransatz bei kopf-oben-anteil (5 %) und das Kinn
  bei kinn-anteil (70 %) der Bildhoehe - so wie im Figma-Master. Der Kopf steht
  damit mittig in der freien Flaeche ueber dem Farbverlauf mit Name und
  Erfahrung.
- Gibt das Original links oder rechts nicht genug Rand her, wird enger
  geschnitten (der Kopf wird groesser), aber nur so weit, dass Haare und Kinn
  nicht angeschnitten werden und das Kinn nicht im Verlauf verschwindet.
  Reicht auch das nicht, steht der Kopf so mittig wie moeglich und das Skript
  meldet die Abweichung.

Den Kopf findet macOS Vision (scripts/gesicht.swift: Gesicht, Kinn,
Personenmaske fuer Haaransatz und Kopfumriss). Ohne macOS gibt man den Kopf
von Hand an: --kopf x0,y0,x1,y1 in Pixeln des Originals, von Haaransatz bis
Kinn und von Ohr zu Ohr.

Schreibt <ziel>/foto-<name>.png (Graustufen, Kartenformat) und
<ziel>/kontrolle/foto-<name>.png - das Bild so, wie es auf der Karte sitzt,
mit Mittellinie und Kopfrahmen. Das Kontrollbild wird angesehen, bevor das
Foto ins Dokument geht.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert

HIER = Path(__file__).resolve().parent
_DS = design_system.laden()
_FK = _DS["komponenten"]["fotokarte"]
BILD_B, BILD_H = _FK["bild-breite"], _FK["bild-hoehe"]
SEITENVERHAELTNIS = BILD_B / BILD_H
OBEN = _FK["kopf-oben-anteil"]            # Haaransatz, Anteil der Bildhoehe
KINN = _FK["kinn-anteil"]                 # Kinn, Anteil der Bildhoehe
MITTE_TOLERANZ = 0.02                     # 2 % der Breite gelten als mittig
OBEN_MIN = 0.02                           # Haare nie naeher als 2 % an die Kante


def _verlauf_oben():
    """Wo der Verlauf beginnt, als Anteil der Kartenhoehe (0,78): darunter
    liegen Name und Erfahrung, dort hat das Kinn nichts verloren."""
    pad = design_system.aufloesen(_DS, _FK["verlauf-padding"])
    zeilen = sum(_DS["textstile"][_DS["texte"][t]["stil"]]["zeilenhoehe_pt"]
                 for t in ("foto-name", "foto-erfahrung"))
    return 1 - (2 * pad + zeilen) / _FK["hoehe"]


KINN_MAX = _verlauf_oben()
AUSGABE_MAX = round(BILD_B / 72 * 300)    # mehr als 300 dpi braucht die Karte nicht
DPI_MIN = 100


# --- Kopf finden -------------------------------------------------------------

def swift_da():
    """/usr/bin/swiftc gibt es auf jedem Mac - ohne Command Line Tools ist es nur
    ein Stub. xcode-select -p sagt, ob wirklich ein Werkzeugsatz installiert ist."""
    if sys.platform != "darwin" or not shutil.which("swiftc"):
        return False
    try:
        return subprocess.run(["xcode-select", "-p"], capture_output=True).returncode == 0
    except OSError:
        return False


def _gesicht_programm():
    """gesicht.swift einmal uebersetzen und zwischenspeichern."""
    quelle = HIER / "gesicht.swift"
    if not swift_da():
        return None, ("Kopferkennung braucht macOS mit den Xcode Command Line Tools "
                      "(xcode-select --install).")
    kennung = hashlib.sha1(quelle.read_bytes()).hexdigest()[:10]
    ziel = Path(tempfile.gettempdir()) / "newmonday-skillmatrix" / f"gesicht-{kennung}"
    if not ziel.exists():
        ziel.parent.mkdir(parents=True, exist_ok=True)
        lauf = subprocess.run(["swiftc", "-O", str(quelle), "-o", str(ziel)],
                              capture_output=True, text=True)
        if lauf.returncode != 0:
            return None, f"gesicht.swift liess sich nicht uebersetzen: {lauf.stderr.strip()[:300]}"
    return ziel, None


def _lauf_um(zeile, x, grenze_l, grenze_r):
    """Zusammenhaengender Personenbereich in einer Maskenzeile um x."""
    if not zeile[x]:
        return None
    links = x
    while links > grenze_l and zeile[links - 1]:
        links -= 1
    rechts = x
    while rechts < grenze_r and zeile[rechts + 1]:
        rechts += 1
    if links <= grenze_l or rechts >= grenze_r:
        return None                       # laeuft in Schultern, Haende, Nachbarn
    return links, rechts


def kopf_finden(bild):
    """Kopf im (bereits gedrehten) PIL-Bild: dict mit links, rechts, oben,
    kinn, mitte (Pixel) oder None plus Hinweisen."""
    programm, grund = _gesicht_programm()
    if not programm:
        return None, [grund]
    with tempfile.TemporaryDirectory() as tmp:
        eingang, maske_pfad = Path(tmp) / "bild.png", Path(tmp) / "maske.png"
        bild.convert("RGB").save(eingang)
        lauf = subprocess.run([str(programm), str(eingang), str(maske_pfad)],
                              capture_output=True, text=True)
        if lauf.returncode != 0:
            return None, [f"Kopferkennung fehlgeschlagen: {lauf.stderr.strip()[-300:]}"]
        daten = json.loads(lauf.stdout)
        maske = None
        if daten.get("maske") and maske_pfad.exists():
            from PIL import Image
            maske = Image.open(maske_pfad).convert("L").point(lambda v: 255 if v > 127 else 0)
            maske.load()

    hinweise = []
    gesichter = daten.get("gesichter") or []
    if not gesichter:
        return None, ["Kein Gesicht erkannt."]
    g = max(gesichter, key=lambda f: (f["x1"] - f["x0"]) * (f["y1"] - f["y0"]))
    if len(gesichter) > 1:
        hinweise.append(f"{len(gesichter)} Gesichter erkannt - das groesste genommen. "
                        "Pruefen, ob es die richtige Person ist.")
    fx0, fx1, fy0, fy1 = g["x0"], g["x1"], g["y0"], g["y1"]
    fb, fh = fx1 - fx0, fy1 - fy0
    kinn = g.get("kinn", fy1)
    kopf = {"gesicht_mitte": (fx0 + fx1) / 2, "kinn": kinn,
            "links": fx0, "rechts": fx1, "quelle": "Vision"}

    if maske is not None:
        b, h = maske.size
        px = maske.load()
        # Vision liefert Gesichtsboxen, die ueber den Bildrand ragen; PIL liest
        # negative Indizes vom anderen Rand. Deshalb alles aufs Bild klemmen.
        # Haaransatz: je Spalte ueber dem Gesicht von der Stirn nach oben, bis
        # die Person aufhoert - so zaehlt nur, was mit dem Kopf verbunden ist.
        start = int(min(h - 1, max(0, fy0 + 0.3 * fh)))
        grenze = int(max(0, fy0 - 1.2 * fh))
        spitzen = []
        for x in range(max(0, int(fx0 + 0.15 * fb)), min(b, int(fx1 - 0.15 * fb))):
            if not px[x, start]:
                continue
            y = start
            while y > grenze and px[x, y - 1]:
                y -= 1
            spitzen.append(y)
        # Kopfumriss auf Stirn- und Augenhoehe
        grenze_l, grenze_r = int(max(0, fx0 - 0.6 * fb)), int(min(b - 1, fx1 + 0.6 * fb))
        mitten, raender = [], []
        mitte_px = int(kopf["gesicht_mitte"])
        for anteil in (0.1, 0.35):
            y = int(fy0 + anteil * fh)
            if not (0 <= y < h and grenze_l < mitte_px < grenze_r):
                continue
            zeile = [px[x, y] for x in range(b)]
            lauf_ = _lauf_um(zeile, mitte_px, grenze_l, grenze_r)
            if lauf_:
                mitten.append((lauf_[0] + lauf_[1]) / 2)
                raender.append(lauf_)
        if spitzen:
            kopf["oben"] = min(spitzen)
        if mitten:
            kopf["mitte"] = sum(mitten) / len(mitten)
            kopf["links"] = min(r[0] for r in raender)
            kopf["rechts"] = max(r[1] for r in raender)
    if "oben" not in kopf:
        kopf["oben"] = fy0 - 0.45 * fh
        hinweise.append("Haaransatz geschaetzt (keine Personenmaske) - die Haare koennen oben "
                        "angeschnitten sein. Kontrollbild ansehen.")
    kopf.setdefault("mitte", kopf["gesicht_mitte"])
    return kopf, hinweise


# --- Ausschnitt ------------------------------------------------------------

def ausschnitt_berechnen(breite, hoehe, kopf):
    """Kartenformat-Ausschnitt (links, oben, rechts, unten) um den Kopf."""
    r = SEITENVERHAELTNIS
    cx, oben, kinn = kopf["mitte"], kopf["oben"], kopf["kinn"]
    kopf_h = max(1.0, kinn - oben)
    s_ziel = kopf_h / (KINN - OBEN)                 # Kopf so gross wie im Master
    s_min = kopf_h / (KINN_MAX - OBEN_MIN)          # groesser geht nicht ohne Anschnitt
    s_bild = min(hoehe, breite / r)
    s_mitte = 2 * max(0.0, min(cx, breite - cx)) / r   # breitester Ausschnitt mit Kopf mittig
    s = min(s_ziel, s_bild, s_mitte)
    if s < s_min:
        s = min(s_min, s_bild)
    w = s * r
    links = min(max(cx - w / 2, 0), breite - w)
    # senkrecht: Kopfmitte dort, wo sie im Master steht; bei groesserem Kopf
    # Haare und Kinn im erlaubten Band halten. Passt der Kopf gar nicht in das
    # Band (Original zu klein), steht er mittig darin und wird oben wie unten
    # gleich angeschnitten - bewerten() meldet das.
    mitte_y = (oben + kinn) / 2
    if kopf_h / s <= KINN_MAX - OBEN_MIN:
        oben_px = mitte_y - (OBEN + KINN) / 2 * s
        oben_px = min(oben_px, oben - OBEN_MIN * s)
        oben_px = max(oben_px, kinn - KINN_MAX * s)
    else:
        oben_px = mitte_y - (OBEN_MIN + KINN_MAX) / 2 * s
    oben_px = min(max(oben_px, 0), hoehe - s)
    return (round(links), round(oben_px), round(links + w), round(oben_px + s))


def bewerten(box, kopf):
    """Wo der Kopf im Ausschnitt steht, und was davon zu melden ist."""
    l, o, r_, u = box
    w, h = r_ - l, u - o
    lage = {
        "mitte_x": (kopf["mitte"] - l) / w,
        "oben": (kopf["oben"] - o) / h,
        "kinn": (kopf["kinn"] - o) / h,
        "dpi": w / (BILD_B / 72),
        "breite_px": w,
    }
    hinweise = []
    abweichung = lage["mitte_x"] - 0.5
    if abs(abweichung) > MITTE_TOLERANZ:
        seite = "rechts" if abweichung > 0 else "links"
        hinweise.append(
            f"Kopf nicht mittig: steht bei {lage['mitte_x']:.0%} der Breite, "
            f"{abs(abweichung):.0%} nach {seite} - das Original hat auf der Gegenseite "
            "zu wenig Rand. Besseres Foto anfragen oder so lassen.")
    if lage["oben"] < OBEN_MIN - 0.005:
        hinweise.append(f"Haare oben angeschnitten (Haaransatz bei {lage['oben']:.0%}).")
    if lage["kinn"] > KINN_MAX + 0.005:
        hinweise.append(f"Kinn im Verlauf (bei {lage['kinn']:.0%}, Verlauf ab {KINN_MAX:.0%}).")
    if lage["dpi"] < DPI_MIN:
        hinweise.append(f"Nur {lage['dpi']:.0f} dpi auf der Karte ({w}px breit) - "
                        f"unter {DPI_MIN} dpi wird das Foto sichtbar weich.")
    return lage, hinweise


def _ohne_kopf(breite, hoehe):
    """Rueckfall ohne Kopf: waagerecht mittig, oben buendig."""
    r = SEITENVERHAELTNIS
    if breite / hoehe > r:
        w = round(hoehe * r)
        links = (breite - w) // 2
        return (links, 0, links + w, hoehe)
    return (0, 0, breite, round(breite / r))


# --- Ausgabe -----------------------------------------------------------------

def kontrollbild(foto, box, kopf, ziel):
    """Das Foto, wie es auf der Karte sitzt: 90 % Deckkraft auf dem
    Kartengrund, Verlauf unten, dazu Mittellinie und Kopfrahmen."""
    from PIL import Image, ImageDraw
    b = 600
    h = round(b / SEITENVERHAELTNIS)
    grund = design_system.rgb(design_system.farbe(_DS, _FK["hintergrund"]))
    karte = Image.new("RGB", (b, h), grund)
    karte = Image.blend(karte, foto.convert("RGB").resize((b, h)), _FK["bild-deckkraft"])
    farbe = design_system.rgb(design_system.farbe(_DS, _FK["verlauf"]["farbe"]))
    voll = _FK["verlauf"]["voll-anteil"]
    verlauf_h = round((1 - KINN_MAX) * h)
    schicht = Image.new("RGBA", (b, h), (0, 0, 0, 0))
    zeichnen = ImageDraw.Draw(schicht)
    for y in range(verlauf_h):
        a = min(1.0, y / (voll * verlauf_h))
        zeichnen.line([(0, h - verlauf_h + y), (b, h - verlauf_h + y)], fill=farbe + (round(255 * a),))
    karte = Image.alpha_composite(karte.convert("RGBA"), schicht)
    linien = ImageDraw.Draw(karte)
    for y in range(0, h, 12):                       # Mittellinie gestrichelt
        linien.line([(b / 2, y), (b / 2, y + 6)], fill=(230, 40, 40, 255), width=2)
    if kopf:
        l, o, r_, u = box
        sx, sy = b / (r_ - l), h / (u - o)
        linien.rectangle([((kopf["links"] - l) * sx, (kopf["oben"] - o) * sy),
                          ((kopf["rechts"] - l) * sx, (kopf["kinn"] - o) * sy)],
                         outline=(255, 170, 0, 255), width=2)
        mx = (kopf["mitte"] - l) * sx
        linien.line([(mx, (kopf["oben"] - o) * sy), (mx, (kopf["kinn"] - o) * sy)],
                    fill=(255, 170, 0, 255), width=2)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    karte.convert("RGB").save(ziel)


def vorbereiten(pfad):
    """Original laden, wie es gemeint ist: nach EXIF gedreht, 16 Bit auf 8 Bit
    skaliert (sonst wird es weiss), Transparenz auf Weiss gesetzt (sonst wird
    sie schwarz)."""
    from PIL import Image, ImageOps
    bild = ImageOps.exif_transpose(Image.open(pfad))
    if bild.mode.startswith("I;16"):
        bild = bild.convert("I").point(lambda i: i * (1 / 256)).convert("L")
    elif bild.mode in ("I", "F"):
        hoechst = bild.getextrema()[1] or 1
        faktor = 255 / hoechst if hoechst > 255 else 1
        bild = bild.point(lambda i: i * faktor).convert("L")
    if bild.mode in ("RGBA", "LA", "PA") or (bild.mode == "P" and "transparency" in bild.info):
        rgba = bild.convert("RGBA")
        grund = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        bild = Image.alpha_composite(grund, rgba).convert("RGB")
    elif bild.mode not in ("L", "RGB"):
        bild = bild.convert("RGB")
    return bild


def kopf_von_hand_pruefen(kopf, breite, hoehe):
    """--kopf in beliebiger Eckenreihenfolge; muss eine Flaeche im Bild haben."""
    x0, y0, x1, y1 = kopf
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    x0, x1 = max(0, x0), min(breite, x1)
    y0, y1 = max(0, y0), min(hoehe, y1)
    if x1 - x0 < 2 or y1 - y0 < 2:
        raise SystemExit(f"--kopf liegt nicht im Bild ({breite} x {hoehe} px) oder hat keine "
                         "Flaeche. Erwartet: x0,y0,x1,y1 in Pixeln des Originals, von "
                         "Haaransatz bis Kinn und von Ohr zu Ohr.")
    return x0, y0, x1, y1


def zuschneiden(pfad, ziel_ordner, kopf_von_hand=None, kontrolle=True):
    """Original -> foto-<name>.png im Kartenformat, Kopf zentriert.
    Gibt (ausgabe, bericht) zurueck; bericht["hinweise"] ist zu melden."""
    from PIL import Image
    pfad, ziel_ordner = Path(pfad), Path(ziel_ordner)
    bild = vorbereiten(pfad)
    breite, hoehe = bild.size

    hinweise = []
    if kopf_von_hand:
        x0, y0, x1, y1 = kopf_von_hand_pruefen(kopf_von_hand, breite, hoehe)
        kopf = {"links": x0, "rechts": x1, "oben": y0, "kinn": y1,
                "mitte": (x0 + x1) / 2, "quelle": "von Hand"}
    else:
        kopf, hinweise = kopf_finden(bild)

    if kopf:
        box = ausschnitt_berechnen(breite, hoehe, kopf)
        lage, weitere = bewerten(box, kopf)
        hinweise += weitere
    else:
        box, lage = _ohne_kopf(breite, hoehe), None
        hinweise.append("Kopf nicht gefunden - Rueckfall: waagerecht mittig, oben buendig. "
                        "Kontrollbild ansehen; sitzt der Kopf nicht mittig, mit "
                        "--kopf x0,y0,x1,y1 (Haaransatz bis Kinn, Ohr zu Ohr) neu schneiden.")

    foto = bild.convert("L").crop(box)
    if foto.width > AUSGABE_MAX:
        foto = foto.resize((AUSGABE_MAX, round(AUSGABE_MAX / SEITENVERHAELTNIS)), Image.LANCZOS)
        if lage:                          # gemeldet wird, was in der Datei steht
            lage["dpi"], lage["breite_px"] = foto.width / (BILD_B / 72), foto.width
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    ausgabe = ziel_ordner / f"foto-{pfad.stem}.png"
    foto.save(ausgabe)
    kontroll_pfad = None
    if kontrolle:
        kontroll_pfad = ziel_ordner / "kontrolle" / ausgabe.name
        kontrollbild(foto, box, kopf, kontroll_pfad)

    bericht = {"quelle": str(pfad), "original": [breite, hoehe], "ausschnitt": list(box),
               "kopf": {k: (round(v, 1) if isinstance(v, float) else v) for k, v in (kopf or {}).items()},
               "lage": {k: round(v, 3) for k, v in (lage or {}).items()},
               "kontrollbild": str(kontroll_pfad) if kontroll_pfad else None,
               "hinweise": hinweise}
    return ausgabe, bericht


def kurzbericht(ausgabe, bericht):
    lage = {k: round(v, 2) + 0.0 for k, v in bericht["lage"].items()}   # kein "-0%"
    if lage:
        zeile = (f"{ausgabe.name}: Kopf bei {lage['mitte_x']:.0%} der Breite, Haaransatz "
                 f"{lage['oben']:.0%}, Kinn {lage['kinn']:.0%}, {lage['dpi']:.0f} dpi "
                 f"({bericht['kopf'].get('quelle')})")
    else:
        zeile = f"{ausgabe.name}: ohne Kopferkennung zugeschnitten"
    return "\n".join([zeile] + [f"  ! {h}" for h in bericht["hinweise"]])


def main():
    argumente = sys.argv[1:]
    kopf = None
    if "--kopf" in argumente:
        i = argumente.index("--kopf")
        kopf = [float(v) for v in argumente[i + 1].split(",")]
        del argumente[i:i + 2]
        if len(kopf) != 4:
            raise SystemExit("--kopf erwartet x0,y0,x1,y1")
    if len(argumente) != 2:
        raise SystemExit(__doc__)
    ausgabe, bericht = zuschneiden(argumente[0], argumente[1], kopf)
    (ausgabe.parent / "kontrolle" / f"{ausgabe.stem}.json").write_text(
        json.dumps(bericht, ensure_ascii=False, indent=1), encoding="utf-8")
    print(kurzbericht(ausgabe, bericht))
    print(f"Kontrollbild: {bericht['kontrollbild']}")


if __name__ == "__main__":
    main()
