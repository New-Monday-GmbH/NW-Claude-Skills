#!/usr/bin/env python3
"""Rendert cv.json ueber das New-Monday-Template zu einem PDF.

    python3 scripts/render_cv.py daten/cv.json ausgabe/lebenslauf.pdf

Sucht sich die Render-Engine selbst: WeasyPrint (bevorzugt, ueberall per pip),
sonst headless Chrome, sonst wkhtmltopdf. Prueft ausserdem die Zeitraeume auf
Unstimmigkeiten und schreibt sie nach stderr — korrigiert wird nichts.
"""
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

BESCHRIFTUNG = {
    "de": {
        "bildung": "Bildung", "skillset": "Skillset",
        "ansprechpartner": "Ansprechpartner", "kontakt": "Kontakt", "adresse": "Adresse",
        "hinweis": "Für weitere Informationen fordern Sie bitte das Portfolio an.",
    },
    "en": {
        "bildung": "Education", "skillset": "Skillset",
        "ansprechpartner": "Contact person", "kontakt": "Contact", "adresse": "Address",
        "hinweis": "Please request the portfolio for further information.",
    },
}

# Optische Groesse in pt: die Kantenlaenge, die ein quadratisches Logo bekommt.
# Jedes Logo wird auf dieselbe Flaeche gebracht (Breite x Hoehe = Groesse^2),
# nicht auf dieselbe Hoehe. Ueber die Hoehe gesetzt wirkt eine kompakte
# Bildmarke doppelt so schwer wie ein breiter Schriftzug: 3pc auf 58pt Hoehe
# deckt 88 x 48pt, Cocomore in derselben Zeile nur 88 x 15pt.
# Gestaffelt nach Anzahl der Marken — je mehr untereinander, desto kleiner,
# damit die Logoreihe nicht laenger wird als der Text daneben. Entschieden wird
# einmal fuers ganze Dokument, nicht je Station: sonst steht dieselbe Marke —
# Deutsche Bank etwa, einmal allein und einmal neben Postbank, FYRST und
# Norisbank — an der einen Stelle doppelt so gross wie an der anderen.
LOGO_GROESSE = {1: 42, 2: 37, 3: 33}
LOGO_GROESSE_AB_4 = 29
LOGO_PROJEKT_GROESSE = {1: 26}
LOGO_PROJEKT_GROESSE_AB_2 = 19

# Muss --rail in cv.css entsprechen. Die Spaltenbreite ist die harte Grenze:
# ein Schriftzug, der breiter waere als 88pt, erreicht seine Sollflaeche nicht
# und wird stattdessen auf volle Spaltenbreite gesetzt.
RAIL_BREITE = 88
# Hochformatige Marken duerfen nicht beliebig hoch werden, sonst schiebt sich
# die Logospalte ueber den Stationskopf hinaus.
LOGO_HOCH_FAKTOR = 1.4

MONATE = {
    "januar": 1, "februar": 2, "maerz": 3, "märz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}
LAUFEND = ("heute", "aktuell", "jetzt", "laufend")


def parse_monat(text):
    """'Juni 2025' -> (2025, 6). None, wenn nicht lesbar oder laufend."""
    t = text.strip().lower()
    if any(w in t for w in LAUFEND):
        return "laufend"
    m = re.search(r"([a-zäöü]+)\s+(\d{4})", t)
    if not m:
        j = re.search(r"\b(\d{4})\b", t)
        return (int(j.group(1)), 1) if j else None
    monat = MONATE.get(m.group(1))
    return (int(m.group(2)), monat) if monat else None


def spanne(zeitraum):
    teile = re.split(r"\s*[-–—]\s*", zeitraum or "", maxsplit=1)
    if len(teile) != 2:
        return None, None
    return parse_monat(teile[0]), parse_monat(teile[1])


def logoliste(wert):
    """logo nimmt einen Dateinamen oder eine Liste davon — hier immer Liste."""
    if not wert:
        return []
    return [wert] if isinstance(wert, str) else list(wert)


def _svg_verhaeltnis(rohdaten):
    kopf = re.search(rb"<svg\b[^>]*>", rohdaten, re.S)
    if not kopf:
        return None
    tag = kopf.group(0).decode("utf-8", "replace")

    box = re.search(r'viewBox\s*=\s*["\']([^"\']+)["\']', tag)
    if box:
        zahlen = re.findall(r"[-+]?[\d.]+(?:[eE][-+]?\d+)?", box.group(1))
        if len(zahlen) == 4 and float(zahlen[3]):
            return float(zahlen[2]) / float(zahlen[3])

    # Ohne viewBox bleiben width/height — Einheiten (pt, px, mm) abschneiden.
    masse = []
    for attribut in ("width", "height"):
        wert = re.search(rf'\b{attribut}\s*=\s*["\']\s*([-+]?[\d.]+)', tag)
        masse.append(float(wert.group(1)) if wert else 0.0)
    if masse[0] and masse[1]:
        return masse[0] / masse[1]
    return None


def _bitmap_verhaeltnis(rohdaten):
    if rohdaten[:8] == b"\x89PNG\r\n\x1a\n":
        breite, hoehe = struct.unpack(">II", rohdaten[16:24])
        return breite / hoehe if hoehe else None
    if rohdaten[:6] in (b"GIF87a", b"GIF89a"):
        breite, hoehe = struct.unpack("<HH", rohdaten[6:10])
        return breite / hoehe if hoehe else None
    if rohdaten[:2] == b"\xff\xd8":                     # JPEG: SOF-Marker suchen
        i = 2
        while i + 9 < len(rohdaten):
            if rohdaten[i] != 0xFF:
                i += 1
                continue
            marker, laenge = rohdaten[i + 1], struct.unpack(">H", rohdaten[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                hoehe, breite = struct.unpack(">HH", rohdaten[i + 5:i + 9])
                return breite / hoehe if hoehe else None
            i += 2 + laenge
    return None


def seitenverhaeltnis(datei):
    """Breite/Hoehe einer Logodatei. 1.0, wenn sie sich nicht lesen laesst.

    Quelle ist die Datei selbst, nicht die Angabe in der cv.json: nur so laesst
    sich die Flaeche jedes Logos gleich setzen. SVG bringt das Verhaeltnis in
    der viewBox mit, PNG/GIF/JPEG im Dateikopf.
    """
    pfad = ASSETS / "logos" / datei
    try:
        rohdaten = pfad.read_bytes()
    except OSError:
        return 1.0
    try:
        verhaeltnis = (_svg_verhaeltnis(rohdaten) if pfad.suffix.lower() == ".svg"
                       else _bitmap_verhaeltnis(rohdaten))
    except (ValueError, struct.error):
        verhaeltnis = None
    if not verhaeltnis:
        print(f"Warnung: Seitenverhaeltnis von {datei} nicht lesbar, nehme 1:1",
              file=sys.stderr)
        return 1.0
    return verhaeltnis


def logo_masse(datei, groesse):
    """(Breite, Hoehe) in pt fuer ein Logo bei gegebener optischer Groesse.

    Gleiche Flaeche fuer alle: Breite = Groesse * sqrt(Verhaeltnis), Hoehe =
    Groesse / sqrt(Verhaeltnis). Ein Quadrat bekommt damit genau Groesse x
    Groesse, ein 4:1-Schriftzug dieselbe Flaeche in flacher Form.
    """
    verhaeltnis = seitenverhaeltnis(datei)
    wurzel = math.sqrt(verhaeltnis)
    breite, hoehe = groesse * wurzel, groesse / wurzel
    if breite > RAIL_BREITE:                  # breiter als die Spalte: kappen
        breite, hoehe = RAIL_BREITE, RAIL_BREITE / verhaeltnis
    hoch = groesse * LOGO_HOCH_FAKTOR
    if hoehe > hoch:                          # hochformatig: Hoehe deckeln
        breite, hoehe = hoch * verhaeltnis, hoch
    return round(breite, 2), round(hoehe, 2)


def logo_groessen(daten):
    """(Stationsgroesse, Projektgroesse) in pt — einmal fuer das ganze Dokument.

    Massgeblich ist die groesste Markenzahl, die irgendwo auftritt. Damit ist
    jedes Logo an jeder Stelle gleich gross, auch wenn es einmal allein und
    einmal in einer Markenreihe steht.
    """
    stationen = daten.get("stationen", [])
    st = max([len(logoliste(s.get("logo"))) for s in stationen] or [0])
    pr = max([len(logoliste(p.get("logo")))
              for s in stationen for p in s.get("projekte", [])] or [0])
    return (
        LOGO_GROESSE.get(max(st, 1), LOGO_GROESSE_AB_4),
        LOGO_PROJEKT_GROESSE.get(max(pr, 1), LOGO_PROJEKT_GROESSE_AB_2),
    )


def pruefe(daten):
    """Sammelt Auffaelligkeiten in den Zeitraeumen. Aendert nichts."""
    hinweise = []
    for s in daten.get("stationen", []):
        start, ende = spanne(s.get("zeitraum", ""))
        if start and ende and ende != "laufend" and start != "laufend" and ende < start:
            hinweise.append(f"{s.get('firma') or s.get('titel')}: Ende liegt vor dem Anfang ({s['zeitraum']})")
        for p in s.get("projekte", []):
            ps, pe = spanne(p.get("zeitraum", ""))
            if ps and pe and pe != "laufend" and ps != "laufend" and pe < ps:
                hinweise.append(f"{p.get('kunde')}: Ende liegt vor dem Anfang ({p['zeitraum']})")
            if ps and start and ps != "laufend" and start != "laufend" and ps < start:
                hinweise.append(
                    f"{p.get('kunde')}: startet vor der Anstellung bei {s.get('firma')} "
                    f"({p.get('zeitraum')} vs. {s.get('zeitraum')})"
                )
    def fehlende(wert, wer):
        return [f"Logo fehlt in assets/logos/: {d} ({wer})"
                for d in logoliste(wert) if not (ASSETS / "logos" / d).exists()]

    im_rail, im_projekt = set(), set()
    for s in daten.get("stationen", []):
        hinweise += fehlende(s.get("logo"), s.get("firma"))
        im_rail.update(logoliste(s.get("logo")))
        for p in s.get("projekte", []):
            hinweise += fehlende(p.get("logo"), p.get("kunde"))
            im_projekt.update(logoliste(p.get("logo")))

    # Innerhalb einer Ebene ist jedes Logo gleich gross. Ueber beide Ebenen
    # hinweg nicht: das Projektlogo ist bewusst die kleinere Stufe.
    for d in sorted(im_rail & im_projekt):
        hinweise.append(
            f"{d} steht als Stationslogo und als Projektlogo im Dokument — "
            "Projektlogos sind die kleinere Stufe, die beiden Groessen weichen "
            "deshalb ab."
        )
    return hinweise


def html_bauen(daten, kompakt=False, anker=False):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(ASSETS)),
        autoescape=select_autoescape(["html"]),
    )
    labels = BESCHRIFTUNG.get(daten.get("sprache", "de"), BESCHRIFTUNG["de"])
    daten.setdefault("hinweis", labels["hinweis"])
    daten.setdefault("kontakt", {
        "name": "Manuel Klein", "rolle": "COO",
        "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0) 155 1148 0130",
        "firma": "New Monday GmbH", "strasse": "Stresemannstraße 32", "ort": "10963 Berlin",
    })
    # Jedes Logo bekommt sein eigenes Mass, ausgerechnet aus dem
    # Seitenverhaeltnis der Datei. Das Template setzt nur noch, was hier steht.
    groesse, projekt_groesse = logo_groessen(daten)
    for s in daten.get("stationen", []):
        s.setdefault("projekte", [])
        s["logos"] = [dict(zip(("datei", "breite", "hoehe"),
                               (d, *logo_masse(d, groesse))))
                      for d in logoliste(s.get("logo"))]
        for p in s["projekte"]:
            p["logos"] = [dict(zip(("datei", "breite", "hoehe"),
                                   (d, *logo_masse(d, projekt_groesse))))
                          for d in logoliste(p.get("logo"))]

    # Das Template wird aus assets/ heraus gerendert; ein Fotopfad aus der JSON
    # bezieht sich aber auf das Arbeitsverzeichnis. Darum hier absolut machen.
    foto = daten.get("person", {}).get("foto")
    if foto and not str(foto).startswith("file:"):   # zweiter Lauf: schon umgewandelt
        p = Path(foto).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            print(f"Warnung: Foto nicht gefunden: {p}", file=sys.stderr)
        daten["person"]["foto"] = p.as_uri()

    return env.get_template("template.html").render(
        kompakt=kompakt, anker=anker, t=labels, **daten
    )


def chrome_pfad():
    kandidaten = [
        "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for k in kandidaten:
        p = shutil.which(k) or (k if os.path.exists(k) else None)
        if p:
            return p
    return None


def rendern(html, ziel):
    """Erste verfuegbare Engine gewinnt. Gibt ihren Namen zurueck.

    Schreibt nichts in den Skill-Ordner: WeasyPrint bekommt die Basis-URL direkt,
    die anderen Engines eine Temporaerdatei mit <base>-Tag. In Claude Code liegt
    der Skill unter ~/.claude/skills/ und darf nicht vollgeschrieben werden.
    """
    basis = ASSETS.as_uri() + "/"
    try:
        from weasyprint import HTML
        HTML(string=html, base_url=basis).write_pdf(str(ziel))
        return "WeasyPrint"
    except ImportError:
        pass

    with tempfile.TemporaryDirectory() as tmp:
        seite = Path(tmp) / "cv.html"
        seite.write_text(
            html.replace("<head>", f'<head><base href="{basis}">', 1), encoding="utf-8"
        )
        chrome = chrome_pfad()
        if chrome:
            with tempfile.TemporaryDirectory() as profil:
                subprocess.run([
                    chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    f"--user-data-dir={profil}", "--no-pdf-header-footer",
                    f"--print-to-pdf={ziel}", seite.as_uri(),
                ], check=True, capture_output=True, timeout=120)
            return "Chrome (headless) — Layout ist auf WeasyPrint abgestimmt, bitte pruefen"

        if shutil.which("wkhtmltopdf"):
            subprocess.run([
                "wkhtmltopdf", "--enable-local-file-access",
                "--page-size", "A4", "--margin-top", "0", "--margin-bottom", "0",
                str(seite), str(ziel),
            ], check=True, capture_output=True, timeout=120)
            return "wkhtmltopdf (eingeschraenktes CSS)"

    raise SystemExit(
        "Keine Render-Engine gefunden. python3 scripts/pruefe_umgebung.py "
        "zeigt, was fehlt und wie es installiert wird."
    )


def seiten_pruefen(ziel, daten):
    """Belegen Bildung und Skillset mehr als eine Seite?"""
    if not (daten.get("bildung") or daten.get("skillset")):
        return []
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    seiten = len(PdfReader(str(ziel)).pages)
    marken = ("Bildung", "Skillset")
    erste = None
    for nummer, seite in enumerate(PdfReader(str(ziel)).pages, start=1):
        text = seite.extract_text() or ""
        if any(m in text for m in marken):
            erste = nummer
            break
    if erste and seiten - erste > 0:
        return [
            f"Bildung/Skillset laufen ueber {seiten - erste + 1} Seiten. "
            "Skillset zusammenfassen: Gruppen zusammenlegen, je Gruppe die "
            "aussagekraeftigsten Eintraege behalten."
        ]
    return []


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    quelle, ziel = Path(sys.argv[1]), Path(sys.argv[2])
    daten = json.loads(quelle.read_text(encoding="utf-8"))

    hinweise = pruefe(daten)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    # Erst pruefen, ob der Abschluss auf eine Seite passt — notfalls enger setzen.
    engine = rendern(html_bauen(daten), ziel)
    kompakt = False
    ueberlauf = seiten_pruefen(ziel, daten)
    if ueberlauf:
        kompakt = True
        engine = rendern(html_bauen(daten, kompakt=True), ziel)
        ueberlauf = seiten_pruefen(ziel, daten)

    if ueberlauf:
        # Passt selbst eng nicht: ohne Anker laufen lassen, sonst wird geschnitten.
        hinweise += ueberlauf
    elif daten.get("bildung") or daten.get("skillset"):
        # Passt: Footer an den unteren Seitenrand ankern.
        engine = rendern(html_bauen(daten, kompakt=kompakt, anker=True), ziel)
        if seiten_pruefen(ziel, daten):          # Anker haette eine Seite gekostet
            engine = rendern(html_bauen(daten, kompakt=kompakt), ziel)
        elif kompakt:
            print("Bildung/Skillset eng gesetzt, damit sie auf eine Seite passen.")

    print(f"{ziel} geschrieben (Engine: {engine})")
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
