#!/usr/bin/env python3
"""Rendert cv.json ueber das New-Monday-Template zu einem PDF.

    python3 scripts/render_cv.py daten/cv.json ausgabe/

Den Dateinamen setzt das Skript selbst aus den Daten:
"New-Monday - Vorname Nachname - Jobtitel - CV.pdf". Das zweite Argument
bestimmt nur den Ordner — ein dort angehaengter Dateiname wird ersetzt
(Ausnahme: --pfad-genau, siehe main()).

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
        "bildung": "Bildung", "skillset": "Skillset", "links": "Weiterführende Links",
        "kurzprofil": "Kurzprofil",
        "ansprechpartner": "Ansprechpartner", "kontakt": "Kontakt", "adresse": "Adresse",
    },
    "en": {
        "bildung": "Education", "skillset": "Skillset", "links": "Further links",
        "kurzprofil": "Profile",
        "ansprechpartner": "Contact person", "kontakt": "Contact", "adresse": "Address",
    },
}

# Die Verweise im Profilkopf werden benannt, nicht als Adresse gesetzt: "zum
# LinkedIn Profil" statt "linkedin.com/in/timo-muster". In einem Dokument, das
# auch gedruckt wird, liest sich der Satz besser als eine nackte URL — und
# ausserhalb des Browsers ist eine URL ohnehin nur Zeichensalat.
# Was hier nicht steht, faellt auf den Titel aus der cv.json zurueck; ein
# eigenes "text" in der cv.json schlaegt beides.
VERWEISTEXT = {
    "de": {
        "linkedin": "zum LinkedIn Profil",
        "xing": "zum Xing Profil",
        "portfolio": "zum Portfolio",
        "website": "zur Website",
    },
    "en": {
        "linkedin": "to the LinkedIn profile",
        "xing": "to the Xing profile",
        "portfolio": "to the portfolio",
        "website": "to the website",
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


def html_bauen(daten, stufe="normal", fuss_abstand=0, stationen_kompakt=False):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(ASSETS)),
        autoescape=select_autoescape(["html"]),
    )
    sprache = daten.get("sprache", "de")
    labels = BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"])
    # Angezeigt wird der benannte Verweis, nicht die Adresse — verlinkt bleibt
    # die volle URL. Das Template setzt nur noch, was hier steht.
    verweise = VERWEISTEXT.get(sprache, VERWEISTEXT["de"])
    for l in daten.get("person", {}).get("links") or []:
        titel = str(l.get("titel") or "").strip()
        l["anzeige"] = l.get("text") or verweise.get(titel.lower()) or titel
    daten.setdefault("kontakt", {
        "name": "Manuel Klein", "rolle": "CCO",
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
        stufe=stufe, fuss_abstand=fuss_abstand,
        stationen_kompakt=stationen_kompakt, t=labels, **daten
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


def spalten_pruefen(daten):
    """Steht das Skillset schief in den Spalten? Dann laesst sich Hoehe gewinnen.

    Der Block ist so hoch wie seine laengere Spalte. Eine halb leere zweite
    Spalte kostet also Platz auf Seite 1 — und Umverteilen kostet im Gegensatz
    zum Kuerzen keinen einzigen Eintrag.
    """
    skillset = daten.get("skillset") or {}
    def zeilen(spalte):                       # Ueberschrift plus Eintraege
        return sum(1 + len(g.get("eintraege") or []) for g in spalte or [])
    links, rechts = zeilen(skillset.get("links")), zeilen(skillset.get("rechts"))
    lang, kurz = max(links, rechts), min(links, rechts)
    if kurz and lang > kurz * 1.5:
        seite = "linke" if links > rechts else "rechte"
        return [
            f"Das Skillset steht schief: die {seite} Spalte traegt {lang} Zeilen, "
            f"die andere {kurz}. Eine Gruppe hinueberschieben macht den Block "
            "flacher, ohne dass ein Eintrag wegfaellt — das zuerst versuchen."
        ]
    return []


# Wo die unterste Zeile des Footers stehen soll, in pt ueber der Blattunterkante.
# Der Seitenrand liegt bei 32pt; gemessen wird die Schriftlinie, die ein Stueck
# darueber sitzt. Der Rest ist Sicherheitsabstand: gemessen kippt der Footer auf
# eine neue Seite, sobald die Fussluft die Restseite auf den Punkt ausfuellt, und
# 12pt sind vier Millimeter — von buendig nicht zu unterscheiden.
FUSS_ZIEL = 44
# Mindestabstand, wenn die Seite nicht mehr hergibt. Lieber eng als eine
# zusaetzliche Seite, auf der nichts ausser dem Footer steht.
FUSS_MIN = 12


def seitenzahl(ziel):
    """Seiten im fertigen PDF. 0, wenn pypdf fehlt — dann wird nicht gemessen."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return 0
    return len(PdfReader(str(ziel)).pages)


def footer_allein(ziel, daten):
    """Steht auf der letzten Seite nur noch der Footer?

    Dann ist die Seite reine Verschwendung — es lohnt der Versuch, die Stationen
    enger zu setzen, damit er auf die Seite davor rutscht. Gemessen wird, was
    nach Abzug der Footer-Texte an Text uebrig bleibt: ueber die Stationen ginge
    es nicht, "New Monday GmbH" steht als Firma und als Adresse im Dokument.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return False
    letzte = " ".join((PdfReader(str(ziel)).pages[-1].extract_text() or "").split()).lower()
    labels = BESCHRIFTUNG.get(daten.get("sprache", "de"), BESCHRIFTUNG["de"])
    teile = [labels[k] for k in ("ansprechpartner", "kontakt", "adresse")]
    teile += [str(w) for w in (daten.get("kontakt") or {}).values()]
    for stueck in teile:
        letzte = letzte.replace(" ".join(str(stueck).split()).lower(), " ", 1)
    return len(letzte.split()) < 4


def text_tiefe(ziel, seite=-1):
    """Wie weit ueber der Blattunterkante endet der Text einer Seite?

    In pt, gemessen an der untersten Schriftlinie. None, wenn nicht messbar.
    Die Textmatrix allein reicht dafuer nicht: WeasyPrint setzt eine gedrehte
    und skalierte Grundmatrix, erst beide zusammen ergeben die Seitenkoordinate.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    hoehen = []

    def besucher(text, cm, tm, schrift, groesse):
        if text.strip():
            hoehen.append(tm[4] * cm[1] + tm[5] * cm[3] + cm[5])

    PdfReader(str(ziel)).pages[seite].extract_text(visitor_text=besucher)
    return min(hoehen) if hoehen else None


def _schlussmarken(daten):
    """Texte, die ganz am Ende des Deckblatts stehen — je Skillset-Spalte einer.

    Nicht am Anfang der Stationen messen: deren erster Titel ist oft derselbe
    Text wie die Rolle im Profilkopf ("Softwareentwickler") und wird dann schon
    auf Seite 1 gefunden, obwohl das Skillset laengst ueberlaeuft.

    Die Verweise taugen dafuer nicht: sie stehen im Profilkopf, also immer weit
    oben auf Seite 1, egal wie weit das Skillset darunter ueberlaeuft.
    """
    marken = []
    skillset = daten.get("skillset") or {}
    for spalte in (skillset.get("links"), skillset.get("rechts")):
        if spalte:
            letzte = spalte[-1]
            eintraege = letzte.get("eintraege") or []
            marken.append(eintraege[-1] if eintraege else letzte.get("titel"))
    if not marken:
        for b in (daten.get("bildung") or [])[-1:]:
            themen = b.get("themen") or []
            marken.append(themen[-1] if themen else b.get("institution") or b.get("abschluss"))
    return [" ".join(str(m).split()) for m in marken if m]


def deckblatt_seiten(ziel, daten):
    """Wie viele Seiten belegen Profilkopf, Bildung und Skillset zusammen?

    Gemessen am jeweils ersten Vorkommen der Schlussmarken — der Block steht vor
    den Stationen, ein spaeterer Treffer im Stationstext zaehlt also nicht.
    0 heisst: gibt hier nichts zu pruefen (kein pypdf, kein Bildung/Skillset).
    -1 heisst: geprueft, aber keine Marke wiedergefunden.
    """
    if not (daten.get("bildung") or daten.get("skillset")):
        return 0
    try:
        from pypdf import PdfReader
    except ImportError:
        return 0

    marken = _schlussmarken(daten)
    if not marken:
        return 0
    # Normalisiert, weil ein umgebrochener Eintrag im PDF-Text ein \n traegt.
    seiten = [" ".join((s.extract_text() or "").split())
              for s in PdfReader(str(ziel)).pages]
    letzte = 0
    for marke in marken:
        for nummer, text in enumerate(seiten, start=1):
            if marke in text:
                letzte = max(letzte, nummer)
                break
    return letzte or -1


def dateiname(daten):
    """New-Monday - Vorname Nachname - Jobtitel - CV.pdf

    Der Name kommt aus den Daten, nicht aus dem Aufrufargument: so heisst jeder
    Lebenslauf beim Kunden gleich, egal wie der Zielpfad getippt war. Fehlt ein
    Feld, faellt nur sein Abschnitt weg — eine Datei entsteht trotzdem.
    """
    person = daten.get("person") or {}
    teile = ["New-Monday"]
    for feld in ("name", "rolle"):
        wert = re.sub(r'[/\\:*?"<>|]', "-", str(person.get(feld) or ""))
        wert = re.sub(r"\s+", " ", wert).strip(" .")
        if wert:
            teile.append(wert)
    teile.append("CV")
    return " - ".join(teile) + ".pdf"


def zielpfad(argument, daten):
    """Ordner aus dem Argument, Dateiname aus den Daten."""
    name = dateiname(daten)
    pdf_gemeint = argument.suffix.lower() == ".pdf"
    ordner = argument.parent if pdf_gemeint else argument
    if pdf_gemeint and argument.name != name:
        print(f"Dateiname gesetzt: {argument.name} -> {name}")
    return ordner / name


def main():
    # --pfad-genau nimmt den Zielpfad wie angegeben — nur fuer Tests, die eine
    # bekannte Datei wieder aufmachen. Im normalen Lauf gilt der Namensaufbau.
    genau = "--pfad-genau" in sys.argv[1:]
    # --stufen-json schreibt nebenbei mit, welche Verdichtungsstufen gegriffen
    # haben. Das braucht figma_plan.py: der Figma-Frame muss dieselben Abstaende
    # setzen wie das PDF, sonst laeuft er ueber. Aus der Ausgabe unten laesst es
    # sich nicht ablesen — die Deckblattstufe wird nur gemeldet, wenn sie am Ende
    # auch gereicht hat. Ohne die Option aendert sich nichts.
    stufen_datei = None
    args = []
    rest = list(sys.argv[1:])
    while rest:
        a = rest.pop(0)
        if a == "--pfad-genau":
            continue
        if a == "--stufen-json":
            if not rest:
                raise SystemExit("--stufen-json braucht einen Dateinamen")
            stufen_datei = Path(rest.pop(0))
            continue
        args.append(a)
    if len(args) < 2:
        raise SystemExit(__doc__)
    quelle = Path(args[0])
    daten = json.loads(quelle.read_text(encoding="utf-8"))

    hinweise = pruefe(daten)
    person = daten.get("person") or {}
    for feld in ("name", "rolle"):
        if not person.get(feld):
            hinweise.append(f"person.{feld} fehlt — der Dateiname bleibt ohne diesen Teil.")
    ziel = Path(args[1]) if genau else zielpfad(Path(args[1]), daten)
    ziel.parent.mkdir(parents=True, exist_ok=True)

    # Deckblatt = Profilkopf, Bildung und Skillset auf Seite 1. Passt es nicht,
    # werden die Abstaende gestaffelt enger gesetzt, bevor irgendwer Eintraege
    # streicht. Erst wenn auch die engste Stufe nicht reicht, kommt der Hinweis.
    stufe = "normal"
    engine = rendern(html_bauen(daten), ziel)
    for naechste in ("kompakt", "eng"):
        if deckblatt_seiten(ziel, daten) <= 1:
            break
        stufe = naechste
        engine = rendern(html_bauen(daten, stufe=stufe), ziel)

    kompakt = False

    def setzen(**abstaende):
        return rendern(html_bauen(daten, stufe=stufe, stationen_kompakt=kompakt,
                                  **abstaende), ziel)

    # Der Footer schliesst die letzte Seite unten ab. Sein Abstand wird nicht
    # geraten, sondern gemessen: erst die Ist-Hoehe der untersten Zeile, dann
    # bekommt die Luft davor genau die Differenz. Unter der Schriftlinie sitzt
    # aber noch Zeilenrest, und der Umbruch braucht Reserve — wie viel, haengt
    # am Dokument, deshalb mehrere Zielhoehen von knapp bis gelassen. Was die
    # Seite sprengt, faellt durch.
    ZIELE = (FUSS_ZIEL, FUSS_ZIEL + 20, FUSS_ZIEL + 45, FUSS_ZIEL + 75)

    # Eine letzte Seite, auf der nur der Footer steht, ist verschenktes Papier.
    # Dann werden die Abstaende zwischen Stationen, Projekten und Bullets enger
    # gesetzt — bringt das die Seite zurueck, bleibt es dabei. Gemessen wird mit
    # minimaler Fussluft: nur so zeigt sich, ob der Footer ueberhaupt noch auf
    # die Seite davor passt.
    engine = setzen(fuss_abstand=FUSS_MIN)
    if footer_allein(ziel, daten):
        vorher = seitenzahl(ziel)
        for enger in ("kompakt", "eng"):
            kompakt = enger
            engine = setzen(fuss_abstand=FUSS_MIN)
            if seitenzahl(ziel) < vorher:
                break
        else:
            kompakt = False
            engine = setzen(fuss_abstand=FUSS_MIN)

    # Jetzt steht fest, mit wie wenig Seiten das Dokument auskommt. Der Footer
    # rueckt so weit nach unten, wie es diese Seitenzahl zulaesst — reicht es
    # nur fuer den Mindestabstand, ist das immer noch besser als eine Seite,
    # auf der nichts als der Footer steht.
    minimal = seitenzahl(ziel)
    tiefe = text_tiefe(ziel)
    for ziel_hoehe in ZIELE if tiefe else ():
        abstand = round(tiefe - ziel_hoehe + FUSS_MIN, 1)
        if abstand <= FUSS_MIN:
            break
        engine = setzen(fuss_abstand=abstand)
        if seitenzahl(ziel) <= minimal:
            break
        engine = setzen(fuss_abstand=FUSS_MIN)

    seiten = deckblatt_seiten(ziel, daten)
    if seiten > 1:
        hinweise.append(
            f"Bildung/Skillset passen nicht neben den Profilkopf auf Seite 1, sie "
            f"laufen ueber {seiten} Seiten. Zusammenfassen: Gruppen zusammenlegen, "
            "je Gruppe die aussagekraeftigsten Eintraege behalten."
        )
        hinweise += spalten_pruefen(daten)
    elif seiten < 0:
        hinweise.append(
            "Die Seitenaufteilung liess sich nicht pruefen: die erste Station "
            "steht nicht im auslesbaren Text des PDF. Bitte im PDF nachsehen, ob "
            "Bildung und Skillset zusammen auf Seite 1 stehen."
        )
    elif stufe != "normal":
        print(f"Bildung/Skillset {stufe} gesetzt, damit sie auf Seite 1 passen.")
    if kompakt:
        print(f"Stationen {kompakt} gesetzt, damit der Footer nicht allein auf "
              "einer Seite steht.")

    if stufen_datei:
        stufen_datei.parent.mkdir(parents=True, exist_ok=True)
        stufen_datei.write_text(json.dumps({
            "deckblatt": stufe,
            "stationen": kompakt or "normal",
            "seiten": seitenzahl(ziel),
            "engine": engine,
            "pdf": str(ziel),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{stufen_datei} geschrieben")

    print(f"{ziel} geschrieben (Engine: {engine})")
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
