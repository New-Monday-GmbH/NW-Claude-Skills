#!/usr/bin/env python3
"""Das Design System der Skillmatrix — eine Quelle fuer PDF und Figma.

    python3 scripts/design_system.py pruefe "ausgabe/New-Monday - … - Skillmatrix.pdf"
    python3 scripts/design_system.py pruefe "ausgabe/New-Monday - … - Skillmatrix A4.pdf" a4
    python3 scripts/design_system.py css [a4]     # erzeugtes CSS ansehen

Alle Farben, Abstaende, Radien, Schatten, Schriften und Masse stehen einmal, in
assets/tokens.json — gespiegelt aus der Figma-Library der Masterdatei. Dieses
Modul liest sie und gibt sie in der Form weiter, die der jeweilige Abnehmer
braucht. Es gibt zwei Fassungen: die lange (oberste Ebene von tokens.json) und
die A4-Fassung (Block "a4" mit eigenen textstilen, texten und komponenten);
fassung(ds, "a4") legt den Block ueber die gemeinsamen Farben, Abstaende und
Schriften, und alle Funktionen hier nehmen das Ergebnis wie ds selbst:

  - css()          @font-face, :root-Variablen je Komponente, .t-*-Textklassen
                   fuer template.html und skillmatrix.css
  - textstil(),
    aufloesen()    fertige Werte fuer figma_plan.py
  - schatten_bild() die Schatten als Bild — WeasyPrint kennt kein box-shadow
  - pruefe_pdf()   das fertige PDF gegen die Tokens: Seitenbreite, Schriften,
                   Textstile, Farben

Wer einen Wert aendern will, aendert ihn in tokens.json. CSS, Template und
figma_plan.py tragen keine eigenen Zahlen.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
TOKENS = ASSETS / "tokens.json"
FONTS = ASSETS / "fonts"


def _meta(schluessel):
    return str(schluessel).startswith("_")


FASSUNGEN = ("lang", "a4")
GEMEINSAM = ("farben", "abstaende", "radien", "schatten", "schriften", "figma_schnitte")


def laden(pfad=TOKENS):
    ds = json.loads(Path(pfad).read_text(encoding="utf-8"))
    seite = ds["komponenten"]["seite"]
    rand = aufloesen(ds, ds["komponenten"]["hero"]["padding-x"])
    if abs(seite["breite"] - 2 * rand - seite["inhalt"]) > 0.01:
        raise SystemExit(
            f"tokens.json ist in sich unstimmig: seite.breite {seite['breite']} "
            f"- 2 x {rand} ist nicht seite.inhalt {seite['inhalt']}.")
    a4 = ds["a4"]["komponenten"]["seite"]
    if abs(a4["breite"] - a4["rand-links"] - a4["rand-rechts"] - a4["inhalt"]) > 0.01:
        raise SystemExit(
            f"tokens.json ist in sich unstimmig: a4.seite.breite {a4['breite']} - Raender "
            f"{a4['rand-links']} + {a4['rand-rechts']} ist nicht a4.seite.inhalt {a4['inhalt']}.")
    return ds


def fassung(ds, name="lang"):
    """Die Tokens einer Fassung in der Form von ds: fuer "lang" ds selbst, fuer
    "a4" die gemeinsamen Farben, Abstaende, Radien, Schatten und Schriften mit
    den textstilen, texten und komponenten aus dem Block "a4". Die Textstile der
    langen Fassung bleiben sichtbar (Namen mit "a4/" stossen nicht an)."""
    if name in (None, "lang"):
        return ds
    if name not in ds:
        raise KeyError(f"Keine Fassung {name!r} in tokens.json (bekannt: {', '.join(FASSUNGEN)}).")
    block = ds[name]
    sicht = {k: ds[k] for k in GEMEINSAM}
    sicht["textstile"] = {**ds["textstile"], **block["textstile"]}
    sicht["texte"] = block["texte"]
    sicht["komponenten"] = block["komponenten"]
    sicht["_fassung"] = name
    return sicht


# --- Aufloesen --------------------------------------------------------------

def aufloesen(ds, ref):
    """Tokenname -> Wert. Zahlen und rohe Hexwerte kommen unveraendert zurueck."""
    if isinstance(ref, (int, float)) or ref is None:
        return ref
    if isinstance(ref, str):
        if ref.startswith("#"):
            return ref.lower()
        for gruppe in ("farben", "abstaende", "radien", "schatten"):
            if ref in ds[gruppe]:
                wert = ds[gruppe][ref]
                return wert.lower() if isinstance(wert, str) else wert
    raise KeyError(f"Unbekannter Token in tokens.json: {ref!r}")


def farbe(ds, ref):
    wert = aufloesen(ds, ref)
    if not (isinstance(wert, str) and re.fullmatch(r"#[0-9a-f]{6}", wert)):
        raise ValueError(f"{ref!r} ist keine Farbe")
    return wert


def rgb(hexwert):
    return tuple(int(hexwert[i:i + 2], 16) for i in (1, 3, 5))


def k(ds, komponente, eigenschaft):
    """Aufgeloester Wert einer Komponenten-Eigenschaft (Rahmen bleiben Dicts)."""
    wert = ds["komponenten"][komponente][eigenschaft]
    if isinstance(wert, dict):
        return {s: (aufloesen(ds, v) if s != "voll-anteil" else v)
                for s, v in wert.items() if not _meta(s)}
    return aufloesen(ds, wert)


def textstil(ds, verwendung):
    """Alles, was ein Textknoten braucht — fuer CSS wie fuer Figma."""
    t = ds["texte"][verwendung]
    stil = dict(ds["textstile"][t["stil"]])
    stil["stilname"] = t["stil"]
    stil["farbe"] = farbe(ds, t["farbe"])
    stil["versalien"] = bool(t.get("versalien") or stil.get("versalien"))
    stil["figma_schnitt"] = ds["figma_schnitte"][stil["familie"]][str(stil["gewicht"])]
    return stil


def zeilenhoehe(ds, verwendung):
    """Hoehe einer Textzeile in pt (Zeilenhoehe aus dem Textstil)."""
    s = textstil(ds, verwendung)
    return s.get("zeilenhoehe_pt") or s["zeilenhoehe"] * s["groesse"]


def schatten_ebenen(ds, ref):
    ebenen = aufloesen(ds, ref)
    if not isinstance(ebenen, list):
        raise ValueError(f"{ref!r} ist kein Schatten")
    return ebenen


# --- CSS --------------------------------------------------------------------

def _zahl(n):
    return f"{n:.3f}".rstrip("0").rstrip(".") if isinstance(n, float) else str(n)


def _schatten_css(ebenen):
    teile = []
    for e in ebenen:
        r, g, b = rgb(e["farbe"])
        teile.append(f"{_zahl(e['x'])}pt {_zahl(e['y'])}pt {_zahl(e['blur'])}pt "
                     f"{_zahl(e['spread'])}pt rgba({r}, {g}, {b}, {_zahl(e['deckkraft'])})")
    return ", ".join(teile)


def _css_wert(ds, eigenschaft, wert):
    if isinstance(wert, dict):
        if "voll-anteil" in wert:                       # Verlauf
            f = farbe(ds, wert["farbe"])
            r, g, b = rgb(f)
            return (f"linear-gradient(180deg, rgba({r}, {g}, {b}, 0) 0%, "
                    f"{f} {_zahl(wert['voll-anteil'] * 100)}%)")
        return f"{_zahl(wert['breite'])}pt solid {farbe(ds, wert['farbe'])}"   # Rahmen
    if isinstance(wert, str) and wert in ds["schatten"]:
        return _schatten_css(ds["schatten"][wert])
    aufgeloest = aufloesen(ds, wert)
    if isinstance(aufgeloest, str):
        return aufgeloest                                 # Farbe
    # Zaehler und Verhaeltnisse sind keine Masse — ohne pt.
    if (eigenschaft.endswith(("deckkraft", "anteil", "format", "zeilen", "spalten", "anzahl"))
            or eigenschaft == "eintraege"):
        return _zahl(aufgeloest)
    return f"{_zahl(aufgeloest)}pt"


def _typo_css(stil):
    if stil.get("zeilenhoehe_pt"):
        zeile = f"{_zahl(stil['zeilenhoehe_pt'])}pt"
    else:
        zeile = _zahl(stil.get("zeilenhoehe", 1.2))
    if stil.get("laufweite_prozent"):
        lauf = f"{_zahl(stil['laufweite_prozent'] / 100)}em"
    else:
        lauf = f"{_zahl(stil.get('laufweite', 0))}pt"
    return (f"font-family: \"{stil['familie']}\"; font-weight: {stil['gewicht']}; "
            f"font-size: {_zahl(stil['groesse'])}pt; line-height: {zeile}; "
            f"letter-spacing: {lauf}; "
            f"text-transform: {'uppercase' if stil['versalien'] else 'none'}; "
            f"color: {stil['farbe']};")


def css(ds):
    """Das CSS, das vor skillmatrix.css in den Kopf des Templates kommt."""
    zeilen = ["/* Erzeugt aus assets/tokens.json — hier nichts von Hand aendern. */"]
    for familie, schnitte in ds["schriften"].items():
        for gewicht, datei in schnitte.items():
            zeilen.append(f"@font-face {{ font-family: \"{familie}\"; "
                          f"src: url(fonts/{datei}); font-weight: {gewicht}; }}")
    variablen = []
    for name, eigenschaften in ds["komponenten"].items():
        for eigenschaft, wert in eigenschaften.items():
            if _meta(eigenschaft):
                continue
            variablen.append(f"  --{name}-{eigenschaft}: {_css_wert(ds, eigenschaft, wert)};")
            if isinstance(wert, dict) and "breite" in wert:     # Rahmen auch einzeln
                variablen.append(f"  --{name}-{eigenschaft}-breite: {_zahl(wert['breite'])}pt;")
                variablen.append(f"  --{name}-{eigenschaft}-farbe: {farbe(ds, wert['farbe'])};")
    zeilen.append(":root {\n" + "\n".join(variablen) + "\n}")
    for verwendung in ds["texte"]:
        zeilen.append(f".t-{verwendung} {{ {_typo_css(textstil(ds, verwendung))} }}")
    return "\n".join(zeilen)


def schriften_fehlen(ds):
    """Schriftdateien, die tokens.json nennt, die aber nicht in assets/fonts liegen."""
    return [FONTS / datei for schnitte in ds["schriften"].values()
            for datei in schnitte.values() if not (FONTS / datei).exists()]


# --- Schatten als Bild ------------------------------------------------------

def schatten_bild(ds, ref, breite, hoehe, radius, ordner, cache, aufloesung=3):
    """Zeichnet den Schatten einer Karte als PNG.

    breite/hoehe/radius sind die Masse des Rahmenkastens der Karte in pt. Das
    Bild ist um `rand` pt nach allen Seiten groesser und wird mit genau diesem
    Versatz hinter die Karte gelegt. Jede Ebene ist ein abgerundetes Rechteck,
    um spread vergroessert, um x/y verschoben und mit einem Gauss weichgezeichnet
    (CSS-Blur b entspricht sigma = b/2) — dieselbe Rechnung wie box-shadow.
    """
    schluessel = (ref, round(breite, 2), round(hoehe, 2), radius)
    if schluessel in cache:
        return cache[schluessel]
    from PIL import Image, ImageDraw, ImageFilter
    ebenen = schatten_ebenen(ds, ref)
    reichweite = max(max(abs(e["x"]), abs(e["y"])) + e["blur"] + max(e["spread"], 0)
                     for e in ebenen)
    rand = math.ceil(reichweite) + 1
    groesse = (round((breite + 2 * rand) * aufloesung),
               round((hoehe + 2 * rand) * aufloesung))
    bild = Image.new("RGBA", groesse, (0, 0, 0, 0))
    for e in ebenen:
        maske = Image.new("L", groesse, 0)
        s = e["spread"]
        kasten = [(rand - s + e["x"]) * aufloesung,
                  (rand - s + e["y"]) * aufloesung,
                  (rand + breite + s + e["x"]) * aufloesung - 1,
                  (rand + hoehe + s + e["y"]) * aufloesung - 1]
        ImageDraw.Draw(maske).rounded_rectangle(
            kasten, radius=max(radius + s, 0) * aufloesung, fill=255)
        if e["blur"] > 0:
            maske = maske.filter(ImageFilter.GaussianBlur(e["blur"] / 2 * aufloesung))
        alpha = maske.point(lambda v, d=e["deckkraft"]: round(v * d))
        ebene = Image.new("RGBA", groesse, rgb(e["farbe"]) + (0,))
        ebene.putalpha(alpha)
        bild = Image.alpha_composite(bild, ebene)
    pfad = Path(ordner) / f"schatten-{len(cache) + 1:02d}.png"
    bild.save(pfad, optimize=True)
    cache[schluessel] = (pfad, rand)
    return cache[schluessel]


# --- Pruefung des fertigen PDFs ---------------------------------------------

def _schriftschluessel(name):
    """'ABCDEF+Inter-Semi-Bold' und 'Inter-SemiBold.ttf' -> 'intersemibold'."""
    name = name.split("+", 1)[-1]
    name = re.sub(r"\.(ttf|otf)$", "", name, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", name.lower()).replace("regular", "")


def _erlaubte_farben(ds):
    farben = {v.lower() for s, v in ds["farben"].items() if not _meta(s)}
    # Schattenfarben: Chrome zeichnet box-shadow selbst, als Flaeche in dieser Farbe.
    farben |= {e["farbe"].lower() for ebenen in ds["schatten"].values() for e in ebenen}

    def sammeln(wert):
        if isinstance(wert, dict):
            for s, v in wert.items():
                if not _meta(s):
                    sammeln(v)
        elif isinstance(wert, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", wert):
            farben.add(wert.lower())
    sammeln(ds["komponenten"])
    return farben


def _nah(a, b, toleranz=1):
    """Gleiche Farbe bis auf Rundung. Mehr Toleranz darf es nicht sein: Die
    hellen Toene liegen nur 2–7 Stufen auseinander (#f8fafc, #ebf2f5, #ffffff)."""
    return all(abs(x - y) <= toleranz for x, y in zip(rgb(a), rgb(b)))


def pruefe_pdf(pdf, ds):
    """(fehler, hinweise). Ein Fehler heisst: Das PDF weicht vom Design System ab.
    ds ist die Fassung (fassung()); geprueft wird jede Seite, bei fester
    Seitenhoehe (A4) auch die Hoehe."""
    fehler, hinweise = [], []
    try:
        import fitz                                   # PyMuPDF
    except ImportError:
        return [], ["PyMuPDF fehlt — Designpruefung uebersprungen "
                    "(pip3 install pymupdf)."]
    dokument = fitz.open(str(pdf))
    seite_soll = ds["komponenten"]["seite"]
    soll, soll_h = seite_soll["breite"], seite_soll.get("hoehe")
    for nr, seite in enumerate(dokument, start=1):
        if abs(seite.rect.width - soll) > 0.5:
            fehler.append(f"Seite {nr}: Breite {seite.rect.width:g}pt statt {soll}pt.")
        if soll_h and abs(seite.rect.height - soll_h) > 0.5:
            fehler.append(f"Seite {nr}: Hoehe {seite.rect.height:g}pt statt {soll_h}pt.")
    _pruefe_seiten(dokument, ds, fehler)
    return fehler, hinweise


def _pruefe_seiten(dokument, ds, fehler):
    """Schriften, Textstile und Farben auf allen Seiten."""
    # Schriften: jede eingebettete Schrift muss eine aus tokens.json sein.
    schnitte = {}
    for familie, dateien in ds["schriften"].items():
        for gewicht, datei in dateien.items():
            schnitte[_schriftschluessel(datei)] = (familie, int(gewicht))
    fremde = sorted({e[3].split("+", 1)[-1] for seite in dokument for e in seite.get_fonts()
                     if _schriftschluessel(e[3]) not in schnitte})
    for name in fremde:
        fehler.append(f"Fremde Schrift im PDF: {name} — Ersatzschrift? "
                      "Schriftdatei fehlt oder font-family ist falsch geschrieben.")

    # Textstile: Schrift, Schnitt, Groesse und Farbe jeder Zeile muessen einer
    # Verwendung aus tokens.json (der Fassung) entsprechen.
    erlaubt = set()
    for verwendung in ds["texte"]:
        s = textstil(ds, verwendung)
        erlaubt.add((s["familie"], s["gewicht"], float(s["groesse"]), s["farbe"]))
    gemeldet = set()
    for seite in dokument:
        for block in seite.get_text("dict")["blocks"]:
            for zeile in block.get("lines", []):
                for span in zeile["spans"]:
                    if not span["text"].strip():
                        continue
                    familie, gewicht = schnitte.get(_schriftschluessel(span["font"]),
                                                    (span["font"], None))
                    hexwert = f"#{span['color']:06x}"
                    treffer = any(f == familie and g == gewicht and abs(gr - span["size"]) < 0.05
                                  and _nah(fa, hexwert) for f, g, gr, fa in erlaubt)
                    schluessel = (familie, gewicht, round(span["size"], 1), hexwert)
                    if not treffer and schluessel not in gemeldet:
                        gemeldet.add(schluessel)
                        schrift = f"{familie} {gewicht}" if gewicht else familie
                        fehler.append(f"Textstil ohne Token: {schrift} {span['size']:.4g}pt "
                                      f"{hexwert} — „{span['text'][:40]}“")

    # Flaechen und Linien: nur Farben aus tokens.json.
    palette = _erlaubte_farben(ds)
    fremd = set()
    for seite in dokument:
        for zeichnung in seite.get_drawings():
            for schluessel in ("fill", "color"):
                wert = zeichnung.get(schluessel)
                if wert is None:
                    continue
                hexwert = "#" + "".join(f"{round(c * 255):02x}" for c in wert[:3])
                if not any(_nah(hexwert, p) for p in palette):
                    fremd.add(hexwert)
    if fremd:
        fehler.append("Farben ohne Token in Flaechen oder Linien: " + ", ".join(sorted(fremd)))


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "css":
        print(css(fassung(laden(), sys.argv[2] if len(sys.argv) > 2 else "lang")))
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "pruefe":
        name = sys.argv[3] if len(sys.argv) > 3 else "lang"
        fehler, hinweise = pruefe_pdf(sys.argv[2], fassung(laden(), name))
        for h in hinweise:
            print(f"Hinweis: {h}")
        for f in fehler:
            print(f"FEHLER: {f}")
        if not fehler:
            print("Design System eingehalten: Seitenbreite, Schriften, Textstile, Farben.")
        sys.exit(1 if fehler else 0)
    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
