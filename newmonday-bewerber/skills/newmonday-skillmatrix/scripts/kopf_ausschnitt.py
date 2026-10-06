#!/usr/bin/env python3
"""Schneidet ein Portraet je Fotoflaeche so zu, dass der Kopf ganz im Bild steht.

    python3 scripts/kopf_ausschnitt.py <original> <ziel-ordner> [--kopf x0,y0,x1,y1]

Die Skillmatrix hat zwei Fassungen und damit zwei Fotoflaechen mit eigenem
Seitenverhaeltnis (assets/tokens.json):

- lang: die Fotokarte im Hero, 435,33 x 433,34 (komponenten.fotokarte)
  -> <ziel>/foto-<name>.png
- a4:   die Fotokarte der A4-Fassung, 108 x 99 (a4.komponenten.fotokarte)
  -> <ziel>/foto-<name>-a4.png

Fuer jede Flaeche wird der Ausschnitt eigens gerechnet, nach denselben Regeln
mit den Werten der Flaeche:

- **Waagerecht** steht die Kopfmitte in der Bildmitte.
- **Senkrecht** sitzt der Haaransatz bei kopf-oben-anteil und das Kinn bei
  kinn-anteil der Bildhoehe.
- **Nie angeschnitten:** Ueber dem Scheitel bleibt mindestens kopf-luft-anteil
  Luft, das Kinn steht hoechstens bei der Kinngrenze (lang: Beginn des
  Verlaufs, a4: kinn-max-anteil). Die Luft geht vor.
- Passt der Kopf mit dieser Luft nicht in den Ausschnitt, wird der Ausschnitt
  groesser (der Kopf kleiner, mehr Schultern) - notfalls auf Kosten der
  waagerechten Mitte. Hat das Original oben zu wenig Rand, wird oben Flaeche in
  der Hintergrundfarbe ergaenzt, aber nur, wenn der obere Bildrand einfarbig
  ist (sonst saehe man die Naht). Reicht beides nicht, meldet das Skript es.

Den Kopf findet macOS Vision (scripts/gesicht.swift: Gesicht, Kinn,
Personenmaske fuer Scheitel und Kopfumriss). Ohne macOS gibt man den Kopf von
Hand an: --kopf x0,y0,x1,y1 in Pixeln des Originals, vom Scheitel bis zum Kinn
und von Ohr zu Ohr.

Je Flaeche entsteht ein Kontrollbild in <ziel>/kontrolle/ - das Foto, wie es
auf der Karte sitzt, mit Mittellinie, Kopfrahmen und der Mindestluft als
blauer Linie. Es wird angesehen, bevor das Foto ins Dokument geht.
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
MITTE_TOLERANZ = 0.02                     # 2 % der Breite gelten als mittig
DPI_MIN = 100
FLAECHEN = ("lang", "a4")
ENDUNG = {"lang": "", "a4": "-a4"}        # foto-<name>.png, foto-<name>-a4.png
GRUND_STREUUNG = 3.0                      # Grauwert-Streuung, bis zu der der obere Rand als einfarbig gilt


def _verlauf_oben():
    """Wo der Verlauf beginnt, als Anteil der Kartenhoehe (0,78): darunter
    liegen Name und Erfahrung, dort hat das Kinn nichts verloren."""
    pad = design_system.aufloesen(_DS, _FK["verlauf-padding"])
    zeilen = sum(_DS["textstile"][_DS["texte"][t]["stil"]]["zeilenhoehe_pt"]
                 for t in ("foto-name", "foto-erfahrung"))
    return 1 - (2 * pad + zeilen) / _FK["hoehe"]


def flaeche(name="lang"):
    """Mass und Kopfregeln einer Fotoflaeche aus tokens.json."""
    if name == "lang":
        fk, kinn_max = _FK, _verlauf_oben()
    else:
        fk = _DS[name]["komponenten"]["fotokarte"]
        kinn_max = fk["kinn-max-anteil"]
    b, h = fk["bild-breite"], fk["bild-hoehe"]
    return {"name": name, "breite_pt": b, "hoehe_pt": h, "r": b / h,
            "oben": fk["kopf-oben-anteil"], "kinn": fk["kinn-anteil"],
            "luft": fk["kopf-luft-anteil"], "kinn_max": kinn_max,
            "verlauf": name == "lang",
            "ausgabe_max": round(b / 72 * 300)}       # mehr als 300 dpi braucht keine Karte


# Fuer Aufrufer, die nur die lange Fotokarte kennen (extract_input, Foto-Skripte).
BILD_B, BILD_H = _FK["bild-breite"], _FK["bild-hoehe"]
SEITENVERHAELTNIS = BILD_B / BILD_H
KINN_MAX = _verlauf_oben()


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

def ausschnitt_berechnen(breite, hoehe, kopf, fl=None, polster=0.0):
    """Ausschnitt (links, oben, rechts, unten) im Format der Flaeche fl um den
    Kopf. polster: so viele Zeilen darf oben Hintergrund ergaenzt werden; die
    Box steht dann in Koordinaten des gepolsterten Bilds (Original um polster
    nach unten verschoben)."""
    fl = fl or flaeche("lang")
    r = fl["r"]
    cx = kopf["mitte"]
    oben, kinn = kopf["oben"] + polster, kopf["kinn"] + polster
    hoehe = hoehe + polster
    kopf_h = max(1.0, kinn - oben)
    band = fl["kinn_max"] - fl["luft"]                 # Platz fuer den Kopf mit Luft
    s_ziel = kopf_h / (fl["kinn"] - fl["oben"])         # Kopf so gross wie vorgesehen
    s_band = kopf_h / band                              # kleiner geht nicht ohne Anschnitt
    s_bild = min(hoehe, breite / r)
    s_mitte = 2 * max(0.0, min(cx, breite - cx)) / r    # breitester Ausschnitt mit Kopf mittig
    s = min(s_ziel, s_bild, s_mitte)
    if s < s_band:
        # Mit Luft passt der Kopf nicht: groesser schneiden (mehr Schultern),
        # die waagerechte Mitte gibt nach.
        s = min(s_band, s_bild)
    w = s * r
    links = min(max(cx - w / 2, 0), breite - w)
    # Senkrecht: Kopfmitte dort, wo die Regel sie will; Luft ueber dem Scheitel
    # und Kinngrenze halten. Passt der Kopf nicht ins Band (Original zu klein),
    # geht die Luft vor - lieber steht das Kinn tief als der Scheitel am Rand.
    ideal = (oben + kinn) / 2 - (fl["oben"] + fl["kinn"]) / 2 * s
    hoechstens = oben - fl["luft"] * s
    if kopf_h / s <= band + 1e-9:
        oben_px = min(max(ideal, kinn - fl["kinn_max"] * s), hoechstens)
    else:
        oben_px = hoechstens
    oben_px = min(max(oben_px, 0), hoehe - s)
    return (round(links), round(oben_px), round(links + w), round(oben_px + s))


def grund_oben(bild):
    """Grauwert des oberen Bildrands, wenn er einfarbig ist - sonst None. Nur
    dann laesst sich oben Flaeche ergaenzen, ohne dass man die Naht sieht."""
    from PIL import ImageStat
    grau = bild.convert("L")
    b, h = grau.size
    streifen = grau.crop((0, 0, b, max(4, round(0.03 * h))))
    stat = ImageStat.Stat(streifen)
    haelften = [ImageStat.Stat(streifen.crop(k)).mean[0]
                for k in ((0, 0, b // 2, streifen.height), (b // 2, 0, b, streifen.height))]
    if stat.stddev[0] > GRUND_STREUUNG or abs(haelften[0] - haelften[1]) > GRUND_STREUUNG:
        return None
    return round(stat.mean[0])


def bewerten(box, kopf, fl=None, polster=0):
    """Wo der Kopf im Ausschnitt steht, und was davon zu melden ist."""
    fl = fl or flaeche("lang")
    l, o, r_, u = box
    w, h = r_ - l, u - o
    lage = {
        "mitte_x": (kopf["mitte"] - l) / w,
        "oben": (kopf["oben"] + polster - o) / h,
        "kinn": (kopf["kinn"] + polster - o) / h,
        "dpi": w / (fl["breite_pt"] / 72),
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
    if lage["oben"] < 0.005:
        hinweise.append(f"Haare oben angeschnitten (Scheitel bei {lage['oben']:.0%}).")
    elif lage["oben"] < fl["luft"] - 0.005:
        hinweise.append(f"Zu wenig Luft ueber dem Scheitel ({lage['oben']:.0%}, Soll mindestens "
                        f"{fl['luft']:.0%}) - das Original hat oben zu wenig Rand und keinen "
                        "einfarbigen Hintergrund zum Ergaenzen. Besseres Foto anfragen.")
    if lage["kinn"] > 1.0:
        hinweise.append(f"Kinn unten angeschnitten (bei {lage['kinn']:.0%}).")
    elif lage["kinn"] > fl["kinn_max"] + 0.005:
        wo = "im Verlauf" if fl["verlauf"] else "nah an der Unterkante"
        hinweise.append(f"Kinn {wo} (bei {lage['kinn']:.0%}, Grenze {fl['kinn_max']:.0%}).")
    if lage["dpi"] < DPI_MIN:
        hinweise.append(f"Nur {lage['dpi']:.0f} dpi auf der Karte ({w}px breit) - "
                        f"unter {DPI_MIN} dpi wird das Foto sichtbar weich.")
    return lage, hinweise


def ausschnitt_mit_luft(bild, kopf, fl):
    """(box, polster, grund): erst ohne Ergaenzung; fehlt dann Luft ueber dem
    Scheitel, weil das Original oben zu knapp ist, mit Hintergrund oben - nur
    bei einfarbigem oberen Rand."""
    breite, hoehe = bild.size
    box = ausschnitt_berechnen(breite, hoehe, kopf, fl)
    luft = (kopf["oben"] - box[1]) / (box[3] - box[1])
    if luft >= fl["luft"] - 0.005:
        return box, 0, None
    grund = grund_oben(bild)
    if grund is None:
        return box, 0, None
    # So viel Rand oben, wie die Luft verlangt - gerechnet mit grosszuegigem
    # Polster, dann auf das gekuerzt, was der Ausschnitt wirklich nutzt.
    vorrat = hoehe
    probe = ausschnitt_berechnen(breite, hoehe, kopf, fl, polster=vorrat)
    polster = max(0, vorrat - probe[1])
    if polster <= 0:
        return box, 0, None
    box = ausschnitt_berechnen(breite, hoehe, kopf, fl, polster=polster)
    return box, polster, grund


def _ohne_kopf(breite, hoehe, fl=None):
    """Rueckfall ohne Kopf: waagerecht mittig, oben buendig."""
    r = (fl or flaeche("lang"))["r"]
    if breite / hoehe > r:
        w = round(hoehe * r)
        links = (breite - w) // 2
        return (links, 0, links + w, hoehe)
    return (0, 0, breite, round(breite / r))


# --- Ausgabe -----------------------------------------------------------------

def kontrollbild(foto, box, kopf, ziel, fl=None, polster=0):
    """Das Foto, wie es auf der Karte sitzt: 90 % Deckkraft auf dem
    Kartengrund, bei der langen Karte der Verlauf unten, dazu Mittellinie,
    Kopfrahmen und die Mindestluft ueber dem Scheitel (blau)."""
    from PIL import Image, ImageDraw
    fl = fl or flaeche("lang")
    fk = _FK if fl["name"] == "lang" else _DS[fl["name"]]["komponenten"]["fotokarte"]
    b = 600
    h = round(b / fl["r"])
    grund = design_system.rgb(design_system.farbe(_DS, fk["hintergrund"]))
    karte = Image.new("RGB", (b, h), grund)
    karte = Image.blend(karte, foto.convert("RGB").resize((b, h)), fk["bild-deckkraft"])
    schicht = Image.new("RGBA", (b, h), (0, 0, 0, 0))
    zeichnen = ImageDraw.Draw(schicht)
    if fl["verlauf"]:
        farbe = design_system.rgb(design_system.farbe(_DS, _FK["verlauf"]["farbe"]))
        voll = _FK["verlauf"]["voll-anteil"]
        verlauf_h = round((1 - fl["kinn_max"]) * h)
        for y in range(verlauf_h):
            a = min(1.0, y / (voll * verlauf_h))
            zeichnen.line([(0, h - verlauf_h + y), (b, h - verlauf_h + y)],
                          fill=farbe + (round(255 * a),))
    karte = Image.alpha_composite(karte.convert("RGBA"), schicht)
    linien = ImageDraw.Draw(karte)
    for y in range(0, h, 12):                       # Mittellinie gestrichelt
        linien.line([(b / 2, y), (b / 2, y + 6)], fill=(230, 40, 40, 255), width=2)
    luft_y = fl["luft"] * h                         # Mindestluft: Haare nicht darueber
    for x in range(0, b, 12):
        linien.line([(x, luft_y), (x + 6, luft_y)], fill=(40, 110, 230, 255), width=2)
    if kopf:
        l, o, r_, u = box
        sx, sy = b / (r_ - l), h / (u - o)
        oben, kinn = kopf["oben"] + polster, kopf["kinn"] + polster
        linien.rectangle([((kopf["links"] - l) * sx, (oben - o) * sy),
                          ((kopf["rechts"] - l) * sx, (kinn - o) * sy)],
                         outline=(255, 170, 0, 255), width=2)
        mx = (kopf["mitte"] - l) * sx
        linien.line([(mx, (oben - o) * sy), (mx, (kinn - o) * sy)],
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


def zuschneiden(pfad, ziel_ordner, kopf_von_hand=None, kontrolle=True, flaechen=FLAECHEN):
    """Original -> je Fotoflaeche ein Zuschnitt in Graustufen, Kopf ganz im Bild:
    foto-<name>.png (lang) und foto-<name>-a4.png (a4). Gibt (ausgabe der
    ersten Flaeche, bericht) zurueck; bericht["hinweise"] ist zu melden,
    bericht["flaechen"] traegt je Flaeche Datei, Ausschnitt und Lage."""
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
    if not kopf:
        hinweise.append("Kopf nicht gefunden - Rueckfall: waagerecht mittig, oben buendig. "
                        "Kontrollbilder ansehen; sitzt der Kopf nicht mittig, mit "
                        "--kopf x0,y0,x1,y1 (Scheitel bis Kinn, Ohr zu Ohr) neu schneiden.")

    grau = bild.convert("L")
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    bericht = {"quelle": str(pfad), "original": [breite, hoehe],
               "kopf": {k: (round(v, 1) if isinstance(v, float) else v)
                        for k, v in (kopf or {}).items()},
               "hinweise": list(hinweise), "flaechen": {}}
    erste = None
    for name in flaechen:
        fl = flaeche(name)
        polster, grund = 0, None
        if kopf:
            box, polster, grund = ausschnitt_mit_luft(bild, kopf, fl)
            lage, weitere = bewerten(box, kopf, fl, polster)
        else:
            box, lage, weitere = _ohne_kopf(breite, hoehe, fl), None, []
        quelle = grau
        if polster:
            quelle = Image.new("L", (breite, hoehe + polster), grund)
            quelle.paste(grau, (0, polster))
            weitere.insert(0, f"Oben {polster}px Hintergrund ergaenzt (Grauwert {grund}) - das "
                              "Original hat ueber dem Scheitel zu wenig Rand. Kontrollbild ansehen.")
        foto = quelle.crop(box)
        if foto.width > fl["ausgabe_max"]:
            foto = foto.resize((fl["ausgabe_max"], round(fl["ausgabe_max"] / fl["r"])), Image.LANCZOS)
            if lage:                      # gemeldet wird, was in der Datei steht
                lage["dpi"], lage["breite_px"] = foto.width / (fl["breite_pt"] / 72), foto.width
        ausgabe = ziel_ordner / f"foto-{pfad.stem}{ENDUNG[name]}.png"
        foto.save(ausgabe)
        kontroll_pfad = None
        if kontrolle:
            kontroll_pfad = ziel_ordner / "kontrolle" / ausgabe.name
            kontrollbild(foto, box, kopf, kontroll_pfad, fl, polster)
        bericht["flaechen"][name] = {
            "datei": str(ausgabe), "ausschnitt": list(box), "polster_oben": polster,
            "lage": {k: round(v, 3) for k, v in (lage or {}).items()},
            "kontrollbild": str(kontroll_pfad) if kontroll_pfad else None,
            "hinweise": weitere}
        bericht["hinweise"] += [f"{name}: {h}" for h in weitere]
        erste = erste or ausgabe
    # Die lange Flaeche wie bisher auch oben im Bericht.
    vorne = bericht["flaechen"].get("lang") or next(iter(bericht["flaechen"].values()))
    bericht.update(ausschnitt=vorne["ausschnitt"], lage=vorne["lage"],
                   kontrollbild=vorne["kontrollbild"])
    return erste, bericht


def kurzbericht(ausgabe, bericht):
    zeilen = []
    for name, f in bericht["flaechen"].items():
        lage = {k: round(v, 2) + 0.0 for k, v in f["lage"].items()}   # kein "-0%"
        datei = Path(f["datei"]).name
        if lage:
            zeilen.append(f"{datei}: Kopf bei {lage['mitte_x']:.0%} der Breite, Scheitel "
                          f"{lage['oben']:.0%}, Kinn {lage['kinn']:.0%}, {lage['dpi']:.0f} dpi "
                          f"({bericht['kopf'].get('quelle')})")
        else:
            zeilen.append(f"{datei}: ohne Kopferkennung zugeschnitten")
        zeilen += [f"  ! {h}" for h in f["hinweise"]]
    allgemein = [h for h in bericht["hinweise"]
                 if not any(h.startswith(f"{n}: ") for n in bericht["flaechen"])]
    return "\n".join(zeilen + [f"  ! {h}" for h in allgemein])


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
    for f in bericht["flaechen"].values():
        print(f"Kontrollbild: {f['kontrollbild']}")


if __name__ == "__main__":
    main()
