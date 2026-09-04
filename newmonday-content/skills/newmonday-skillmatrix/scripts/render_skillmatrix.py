#!/usr/bin/env python3
"""Rendert skillmatrix.json ueber das New-Monday-Template zu einem PDF.

    python3 scripts/render_skillmatrix.py daten/skillmatrix.json ausgabe/

Den Dateinamen setzt das Skript selbst aus den Daten:
"New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf". Das zweite
Argument bestimmt nur den Ordner — ein dort angehaengter Dateiname wird
ersetzt (Ausnahme: --pfad-genau, siehe main()).

Die Skillmatrix ist eine einzige lange Seite: 1440pt breit, so hoch wie ihr
Inhalt — wie die Vorlage aus Figma, die eine Webseite abbildet und kein
A4-Dokument. Weil CSS keine Seite "so hoch wie der Inhalt" kennt, wird zweimal
gerendert: erst auf Vorrat hoch, dann wird die tatsaechliche Inhaltshoehe
gemessen und exakt gesetzt.

Sucht sich die Render-Engine selbst: WeasyPrint (bevorzugt), sonst headless
Chrome, sonst wkhtmltopdf. Prueft ausserdem die Daten auf Auffaelligkeiten und
schreibt sie nach stderr — korrigiert wird nichts.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SEITENBREITE = 1440          # pt, wie die Figma-Frames der Vorlage
VORRAT_HOEHE = 12000         # pt, erster Durchgang — reicht fuer jede Matrix

BESCHRIFTUNG = {
    "de": {
        "verfuegbar": "Verfügbar ab",
        "zertifikate": "Zertifikate",
        "kernkompetenzen": "Kernkompetenzen",
        "aussteller": "Ausgestellt von:",
        "footer_frage": "Bereit für das nächste Projekt?",
        "ansprechpartner": "Ansprechpartner", "kontakt": "Kontakt", "adresse": "Adresse",
    },
    "en": {
        "verfuegbar": "Available from",
        "zertifikate": "Certificates",
        "kernkompetenzen": "Core Skills",
        "aussteller": "Issued by:",
        "footer_frage": "Ready for the next project?",
        "ansprechpartner": "Contact person", "kontakt": "Contact", "adresse": "Address",
    },
}


# Sprachprobe fuer die Beschreibungen. Absichtlich grob und absichtlich
# schweigsam: gewarnt wird nur, wenn die Marker der FALSCHEN Sprache die der
# richtigen ueberwiegen. Ein Text ohne jeden Marker ("Photoshop, Illustrator,
# After Effects") bleibt unbeanstandet — lieber ein uebersehener Fall als eine
# Warnung, die man sich abgewoehnt zu lesen.
_DE_MARKER = re.compile(
    r"\b(der|die|das|und|für|von|mit|zur|zum|den|dem|eine|einen|einer|auf|aus"
    r"|durch|über|bei|nach|sowie|nicht|wird|werden|ohne|zwischen|zu|bis|um"
    r"|ihre|ihrer|echten)\b|[äöüßÄÖÜ]", re.I)
# Englisch zeigt sich hier an Funktionswoertern und am Gerundium AM ANFANG
# ("Designing …", "Using …"). Ein -ing mitten im Satz zaehlt nicht: deutsche
# Beschreibungen tragen Fachbegriffe wie "Prototyping" oder "Onboarding".
_EN_MARKER = re.compile(
    r"\b(the|and|for|with|of|to|into|across|within|from|by|their|its|real"
    r"|users|based|before|through)\b", re.I)
_EN_GERUND = re.compile(r"^\s*\w+ing\b", re.I)


def _sprachprobe(text):
    """(de_treffer, en_treffer) — je hoeher, desto sicherer die Sprache."""
    text = str(text or "")
    de = len(_DE_MARKER.findall(text))
    en = len(_EN_MARKER.findall(text)) + (1 if _EN_GERUND.match(text) else 0)
    return de, en


def _sprachhinweis(text, sprache, wo):
    de, en = _sprachprobe(text)
    if sprache == "de" and en > de and en:
        return (f"{wo}: sieht englisch aus, die Matrix ist deutsch — "
                f"„{text}“")
    if sprache == "en" and de > en and de:
        return (f"{wo}: looks German, the matrix is English — "
                f"“{text}”")
    return None


def pruefe(daten):
    """Sammelt Auffaelligkeiten. Aendert nichts."""
    hinweise = []
    sprache = daten.get("sprache", "de")
    person = daten.get("person") or {}
    for feld in ("name", "rolle", "beschreibung", "erfahrung", "verfuegbar_ab"):
        if not person.get(feld):
            hinweise.append(f"person.{feld} fehlt — die Zeile bleibt im Hero leer.")
    schwerpunkte = person.get("schwerpunkte") or []
    if len(schwerpunkte) > 3:
        hinweise.append(
            f"{len(schwerpunkte)} Schwerpunkte gesetzt — die Vorlage traegt drei. "
            "Mehr als drei brechen im Hero um.")
    if not person.get("foto"):
        hinweise.append("Kein Foto — die Fotokarte zeigt nur den Farbverlauf mit dem Namen.")

    # Die Hero-Beschreibung ist der einzige laengere neue Text im Dokument und
    # steht in der Ich-Perspektive — die Matrix ist kein Steckbrief ueber den
    # Kandidaten, sondern ein Dokument, in dem er selbst spricht.
    beschreibung = person.get("beschreibung")
    if beschreibung:
        hinweis = _sprachhinweis(beschreibung, sprache, "person.beschreibung")
        if hinweis:
            hinweise.append(hinweis)
        ich = (r"\b(ich|mein|meine|meinen|meiner|meinem|mich|mir)\b"
               if sprache == "de" else r"\b(I|my|me|mine)\b")
        if not re.search(ich, str(beschreibung), 0 if sprache == "en" else re.I):
            hinweise.append(
                "person.beschreibung steht nicht in der Ich-Perspektive — in der "
                "Skill Matrix spricht der Kandidat selbst („Ich gestalte …“, "
                "nicht „Gestaltet …“).")

    for z in daten.get("zertifikate") or []:
        if not z.get("titel"):
            hinweise.append("Ein Zertifikat ohne Titel.")
        if not z.get("jahr"):
            hinweise.append(f"Zertifikat ohne Jahr: {z.get('titel')}")

    for datei in daten.get("zertifikat_bilder") or []:
        pfad = Path(datei).expanduser()
        if not pfad.is_absolute():
            pfad = Path.cwd() / pfad
        if not pfad.exists():
            hinweise.append(f"Zertifikatsbild nicht gefunden: {datei}")

    for kategorie in daten.get("kompetenzen") or []:
        skills = kategorie.get("skills") or []
        if not skills:
            hinweise.append(f"Kategorie ohne Skills: {kategorie.get('kategorie')}")
        for s in skills:
            p = s.get("punkte")
            if not isinstance(p, int) or not 1 <= p <= 5:
                hinweise.append(
                    f"{s.get('name')}: punkte muss eine ganze Zahl 1–5 sein, ist {p!r}.")
            elif p < 3:
                hinweise.append(
                    f"{s.get('name')} steht mit {p} Punkten in der Matrix — in den "
                    "Vorlagen ist 3 die unterste Stufe, darunter wird weggelassen.")
            if not s.get("beschreibung"):
                hinweise.append(f"{s.get('name')}: beschreibung fehlt — die Karte wirkt leer.")
            elif len(str(s.get("beschreibung"))) > 110:
                hinweise.append(
                    f"{s.get('name')}: Beschreibung ist {len(str(s['beschreibung']))} Zeichen "
                    "lang — die Karten der Vorlage tragen ein bis zwei kurze Zeilen.")
            if s.get("beschreibung"):
                hinweis = _sprachhinweis(s["beschreibung"], sprache, s.get("name"))
                if hinweis:
                    hinweise.append(hinweis)
    if not daten.get("kompetenzen"):
        hinweise.append("Keine Kernkompetenzen — die Matrix besteht dann nur aus dem Hero.")
    return hinweise


def _pfad_zu_uri(wert):
    """Relative Pfade aus der JSON beziehen sich aufs Arbeitsverzeichnis,
    gerendert wird aber aus assets/ heraus — darum absolut machen."""
    if not wert or str(wert).startswith(("file:", "http:", "https:")):
        return wert
    p = Path(wert).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        print(f"Warnung: Datei nicht gefunden: {p}", file=sys.stderr)
    return p.as_uri()


def html_bauen(daten, hoehe):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(ASSETS)),
        autoescape=select_autoescape(["html"]),
    )
    sprache = daten.get("sprache", "de")
    labels = dict(BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"]))
    # Ueberschrift der Zertifikatssektion laesst sich ueberschreiben —
    # ein Beispiel der Vorlage traegt "Zertifizierungen UX/UI".
    if daten.get("zertifikate_titel"):
        labels["zertifikate"] = daten["zertifikate_titel"]

    daten = dict(daten)
    person = dict(daten.get("person") or {})
    person["foto"] = _pfad_zu_uri(person.get("foto"))
    daten["person"] = person
    daten["zertifikat_bilder"] = [
        _pfad_zu_uri(b) for b in daten.get("zertifikat_bilder") or []]

    daten.setdefault("kontakt", {
        "name": "Manuel Klein", "rolle": "CCO",
        "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0) 155 1148 0130",
        "firma": "New Monday GmbH", "strasse": "Stresemannstraße 32", "ort": "10963 Berlin",
    })
    return env.get_template("template.html").render(
        hoehe=hoehe, t=labels, **daten)


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

    Schreibt nichts in den Skill-Ordner: WeasyPrint bekommt die Basis-URL
    direkt, die anderen Engines eine Temporaerdatei mit <base>-Tag.
    """
    basis = ASSETS.as_uri() + "/"
    try:
        from weasyprint import HTML
        HTML(string=html, base_url=basis).write_pdf(str(ziel))
        return "WeasyPrint"
    except ImportError:
        pass

    with tempfile.TemporaryDirectory() as tmp:
        seite = Path(tmp) / "matrix.html"
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
                "--margin-top", "0", "--margin-bottom", "0",
                "--margin-left", "0", "--margin-right", "0",
                str(seite), str(ziel),
            ], check=True, capture_output=True, timeout=120)
            return "wkhtmltopdf (eingeschraenktes CSS)"

    raise SystemExit(
        "Keine Render-Engine gefunden. python3 scripts/pruefe_umgebung.py "
        "zeigt, was fehlt und wie es installiert wird."
    )


def inhaltshoehe_messen(pdf):
    """Unterkante des Inhalts auf Seite 1, in pt ab Oberkante. None = nicht messbar.

    Gemessen wird am Bild, nicht am Text: Das unterste Element ist der teal
    gefuellte Footer, unter ihm ist die Vorratsseite weiss. Die letzte nicht
    weisse Pixelzeile ist also die Unterkante des Inhalts — das funktioniert
    fuer jede Engine gleich. Aufgeloest wird mit 36 dpi (0,5 px je pt), der
    Messfehler liegt damit bei 2pt und verschwindet in der Rundungsreserve.
    """
    zeile = None
    try:
        import fitz                                   # PyMuPDF, falls vorhanden
        seite = fitz.open(str(pdf))[0]
        pix = seite.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
        px, breite, hoehe = pix.samples, pix.width, pix.height
        n = pix.n
        for y in range(hoehe - 1, -1, -1):
            reihe = px[y * breite * n:(y + 1) * breite * n]
            if any(kanal < 247 for kanal in reihe):
                zeile = y
                break
        if zeile is not None:
            return (zeile + 1) / 0.5
    except ImportError:
        pass

    if not shutil.which("pdftoppm"):
        return None
    try:
        from PIL import Image
    except ImportError:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "mess"
        subprocess.run(
            ["pdftoppm", "-png", "-r", "36", "-f", "1", "-l", "1", str(pdf), str(prefix)],
            check=True, capture_output=True,
        )
        treffer = sorted(Path(tmp).glob("mess*.png"))
        if not treffer:
            return None
        bild = Image.open(treffer[0]).convert("L")
        px = bild.load()
        for y in range(bild.height - 1, -1, -1):
            if any(px[x, y] < 247 for x in range(bild.width)):
                return (y + 1) * 72 / 36
    return None


def seitenzahl(pdf):
    try:
        from pypdf import PdfReader
    except ImportError:
        return 0
    return len(PdfReader(str(pdf)).pages)


def dateiname(daten):
    """New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf

    Der Name kommt aus den Daten, nicht aus dem Aufrufargument: so heisst jede
    Matrix beim Kunden gleich, egal wie der Zielpfad getippt war. Fehlt ein
    Feld, faellt nur sein Abschnitt weg — eine Datei entsteht trotzdem.
    """
    person = daten.get("person") or {}
    teile = ["New-Monday"]
    for feld in ("name", "rolle"):
        wert = re.sub(r'[/\\:*?"<>|]', "-", str(person.get(feld) or ""))
        wert = re.sub(r"\s+", " ", wert).strip(" .")
        if wert:
            teile.append(wert)
    teile.append("Skillmatrix")
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
    args = [a for a in sys.argv[1:] if a != "--pfad-genau"]
    if len(args) < 2:
        raise SystemExit(__doc__)
    quelle = Path(args[0])
    daten = json.loads(quelle.read_text(encoding="utf-8"))

    hinweise = pruefe(daten)
    ziel = Path(args[1]) if genau else zielpfad(Path(args[1]), daten)
    ziel.parent.mkdir(parents=True, exist_ok=True)

    # Durchgang 1: Vorratshoehe. Durchgang 2: exakt. Die 2pt Reserve decken
    # den Messfehler der Rasterung — lieber eine haarduenne weisse Kante als
    # ein abgeschnittener Footer.
    engine = rendern(html_bauen(daten, VORRAT_HOEHE), ziel)
    hoehe = inhaltshoehe_messen(ziel)
    if hoehe is None:
        hinweise.append(
            f"Inhaltshoehe nicht messbar (weder PyMuPDF noch pdftoppm+Pillow) — "
            f"die Seite bleibt auf Vorratshoehe {VORRAT_HOEHE}pt und traegt unten "
            "viel Weissraum. pruefe_umgebung.py zeigt, was fehlt.")
    else:
        hoehe = round(hoehe + 2)
        engine = rendern(html_bauen(daten, hoehe), ziel)
        print(f"Seitenformat: {SEITENBREITE} x {hoehe}pt")

    seiten = seitenzahl(ziel)
    if seiten > 1:
        hinweise.append(
            f"Das PDF hat {seiten} Seiten statt einer — der Inhalt ist hoeher als "
            "die gesetzte Seitenhoehe. Das darf nicht passieren, bitte melden.")

    print(f"{ziel} geschrieben (Engine: {engine})")
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
