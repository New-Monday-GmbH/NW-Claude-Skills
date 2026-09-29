#!/usr/bin/env python3
"""Rendert skillmatrix.json ueber das New-Monday-Template zu einem PDF.

    python3 scripts/render_skillmatrix.py daten/skillmatrix.json ausgabe/

Den Dateinamen setzt das Skript selbst aus den Daten:
"New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf". Das zweite
Argument bestimmt nur den Ordner — ein dort angehaengter Dateiname wird
ersetzt (Ausnahme: --pfad-genau, siehe main()).

Die Skillmatrix ist eine einzige lange Seite: so breit wie der Figma-Frame der
Vorlage (1444pt, aus assets/tokens.json), so hoch wie ihr Inhalt — sie bildet
eine Webseite ab, kein A4-Dokument. Weil CSS keine Seite "so hoch wie der
Inhalt" kennt, wird zweimal gerendert: erst auf Vorrat hoch, dann mit der
gemessenen Inhaltshoehe.

Alle Farben, Abstaende, Radien, Schatten und Schriften kommen aus
assets/tokens.json (design_system.py erzeugt daraus das CSS). WeasyPrint kennt
kein box-shadow; im ersten Durchgang werden deshalb die Karten vermessen und
ihre Schatten als Bild gezeichnet, im zweiten liegen sie hinter den Karten.
Zum Schluss wird das fertige PDF gegen die Tokens geprueft — Seitenbreite,
Schriften, Textstile, Farben. Weicht es ab, endet das Skript mit Code 2.

Sucht sich die Render-Engine selbst: WeasyPrint (bevorzugt), sonst headless
Chrome, sonst wkhtmltopdf. Prueft ausserdem die Daten auf Auffaelligkeiten und
schreibt sie nach stderr — korrigiert wird nichts.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

VORRAT_HOEHE = 12000         # pt, erster Durchgang — reicht fuer jede Matrix
PT_JE_PX = 0.75              # WeasyPrint rechnet intern in CSS-px (96 dpi)

BESCHRIFTUNG = {
    "de": {
        "verfuegbar": "Verfügbar ab",
        "zertifikate": "Zertifikate",
        "kernkompetenzen": "Kernkompetenzen",
        "tools": "Tools",
        "aussteller": "Ausgestellt von:",
        "footer_frage": "Bereit für das nächste Projekt?",
        "ansprechpartner": "Ansprechpartner", "kontakt": "Kontakt", "adresse": "Adresse",
    },
    "en": {
        "verfuegbar": "Available from",
        "zertifikate": "Certificates",
        "kernkompetenzen": "Core Skills",
        "tools": "Tools",
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
            "Die Buttons stehen in einer Zeile; mehr als drei laufen ueber die "
            "Textspalte hinaus.")
    if not person.get("foto"):
        hinweise.append("Kein Foto — die Fotokarte zeigt nur den Farbverlauf mit dem Namen.")
    elif not str(person["foto"]).startswith(("http:", "https:", "file:")):
        foto = Path(person["foto"]).expanduser()
        if not foto.is_absolute():
            foto = Path.cwd() / foto
        if not foto.exists():
            hinweise.append(f"Foto nicht gefunden: {foto} — die Fotokarte bliebe leer. "
                            "Relative Pfade gelten ab dem Arbeitsverzeichnis.")

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

    tools = daten.get("tools") or []
    hoechstens = design_system.laden()["komponenten"]["tools"]["anzahl"]
    if len(tools) > hoechstens:
        hinweise.append(
            f"{len(tools)} Tools gesetzt — die Sektion traegt hoechstens {hoechstens} "
            "(zwei Reihen). Die schwaechsten weglassen.")
    gruppen = [(k.get("kategorie"), k.get("skills") or []) for k in daten.get("kompetenzen") or []]
    for kategorie, _ in gruppen:
        if re.match(r"\s*tools\b", str(kategorie or ""), re.I):
            hinweise.append(
                f"Kategorie „{kategorie}“ unter den Kernkompetenzen — Tools haben eine "
                "eigene Sektion (JSON-Feld tools); Werkzeuge gehoeren dorthin.")
    if tools:
        gruppen.append((TOOLS_SEKTION, tools))
    for kategorie, skills in gruppen:
        if not skills:
            hinweise.append(f"Kategorie ohne Skills: {kategorie}")
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
    hinweise += _doppelte(gruppen)
    if not daten.get("kompetenzen"):
        hinweise.append("Keine Kernkompetenzen — die Matrix besteht dann nur aus dem Hero.")
    return hinweise


TOOLS_SEKTION = object()      # Kennung der Tools-Sektion - eine Kategorie darf auch "Tools" heissen


def _namensteile(name):
    """'Figma / FigJam' -> {'figma', 'figjam', 'figmafigjam'}: Sammelnamen
    zaehlen auch mit jedem ihrer Teile."""
    norm = lambda s: re.sub(r"[^0-9a-z+#]", "", s.lower())      # C++ und C# bleiben verschieden
    teile = {norm(t) for t in re.split(r"\s*/\s*", str(name or ""))}
    teile.add(norm(str(name or "")))
    return {t for t in teile if t}


def _doppelte(gruppen):
    """Jeder Name steht einmal im Dokument; ein Tool nur in der Tools-Sektion."""
    hinweise, gesehen = [], []                 # (teile, name, kategorie)
    for kategorie, skills in gruppen:
        for s in skills:
            teile = _namensteile(s.get("name"))
            for teile_alt, name_alt, kat_alt in gesehen:
                if not teile & teile_alt:
                    continue
                if TOOLS_SEKTION in (kategorie, kat_alt) and kategorie != kat_alt:
                    if kategorie is TOOLS_SEKTION:
                        tool, skill, skill_kat = s.get("name"), name_alt, kat_alt
                    else:
                        tool, skill, skill_kat = name_alt, s.get("name"), kategorie
                    hinweise.append(
                        f"„{skill}“ unter „{skill_kat}“ doppelt das Tool „{tool}“ — ein Tool "
                        "steht nur in der Tools-Sektion; unter den Kernkompetenzen streichen.")
                else:
                    orte = [("Tools-Sektion" if k is TOOLS_SEKTION else k) for k in (kat_alt, kategorie)]
                    hinweise.append(
                        f"„{s.get('name')}“ steht doppelt ({orte[0]} und {orte[1]}) — "
                        "jeder Name kommt nur einmal vor.")
                break
            gesehen.append((teile, s.get("name"), kategorie))
    return hinweise


def _pfad_zu_uri(wert):
    """Relative Pfade aus der JSON beziehen sich aufs Arbeitsverzeichnis,
    gerendert wird aber aus assets/ heraus — darum absolut machen."""
    if not wert or str(wert).startswith(("file:", "http:", "https:")):
        return wert
    p = Path(wert).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists() and p not in _GEMELDET:
        _GEMELDET.add(p)
        print(f"Warnung: Datei nicht gefunden: {p}", file=sys.stderr)
    return p.as_uri()


_GEMELDET = set()


def html_bauen(daten, hoehe, design, schatten=None):
    """schatten: Karten-ID -> Schattenbild samt Lage, nur im zweiten
    WeasyPrint-Durchgang. Ohne sie zeichnet Chrome box-shadow selbst."""
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
        "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0)155 1148 0130",
        "firma": "New Monday GmbH", "strasse": "Stresemannstraße 32", "ort": "10963 Berlin",
    })
    komponenten = design["komponenten"]
    return env.get_template("template.html").render(
        hoehe=hoehe, t=labels,
        design_css=design_system.css(design),
        seitenbreite=komponenten["seite"]["breite"],
        raster_spalten=komponenten["raster"]["spalten"],
        skill_spalten=komponenten["skillraster"]["spalten"],
        punkte_anzahl=komponenten["punkte"]["anzahl"],
        schatten=schatten or {},
        **daten)


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


def _kaesten(box):
    yield box
    for kind in getattr(box, "children", None) or []:
        yield from _kaesten(kind)


def _kasten(box):
    """Rahmenkasten eines Layout-Kastens in pt."""
    return {
        "x": box.border_box_x() * PT_JE_PX, "y": box.border_box_y() * PT_JE_PX,
        "breite": box.border_width() * PT_JE_PX, "hoehe": box.border_height() * PT_JE_PX,
        "rahmen_links": box.border_left_width * PT_JE_PX,
        "rahmen_oben": box.border_top_width * PT_JE_PX,
    }


def _elemente(wurzel):
    """Je HTML-Element sein erster (Haupt-)Kasten, in Dokumentreihenfolge."""
    gesehen = set()
    for box in _kaesten(wurzel):
        element = getattr(box, "element", None)
        if element is None or id(element) in gesehen or not hasattr(box, "border_width"):
            continue
        gesehen.add(id(element))
        yield element, box


def layout_pruefen(wurzel, design):
    """Hinweise, die erst das fertige Layout zeigt."""
    hinweise = []
    spalte = design["komponenten"]["hero"]["textspalte"]
    for element, box in _elemente(wurzel):
        if "hero__schwerpunkte" in (element.get("class") or ""):
            buttons = [_kasten(k) for k in box.children if hasattr(k, "border_width")]
            if buttons:
                breite = buttons[-1]["x"] + buttons[-1]["breite"] - buttons[0]["x"]
                if breite > spalte + 0.5:
                    hinweise.append(
                        f"Die Schwerpunkt-Buttons sind zusammen {breite:.0f}pt breit, "
                        f"die Textspalte {spalte}pt — kuerzere Begriffe waehlen.")
    return hinweise


def rendern_weasyprint(daten, design, ziel):
    """Zwei Durchgaenge. Der erste liefert Inhaltshoehe und Kartengroessen, der
    zweite rendert mit exakter Hoehe und den Schattenbildern hinter den Karten.
    Gibt (engine, hoehe_pt, anzahl_schatten, hinweise) zurueck; ImportError,
    wenn WeasyPrint fehlt."""
    from weasyprint import HTML
    basis = ASSETS.as_uri() + "/"
    doc = HTML(string=html_bauen(daten, VORRAT_HOEHE, design), base_url=basis).render()
    wurzel = doc.pages[0]._page_box
    html_kasten = wurzel.children[0]
    hoehe = math.ceil((html_kasten.position_y + html_kasten.margin_height()) * PT_JE_PX)
    hinweise = layout_pruefen(wurzel, design)

    with tempfile.TemporaryDirectory() as tmp:
        cache, schatten = {}, {}
        for element, box in _elemente(wurzel):
            komponente = element.get("data-schatten")
            if not komponente:
                continue
            k = _kasten(box)
            eigenschaften = design["komponenten"][komponente]
            radius = design_system.aufloesen(design, eigenschaften["radius"])
            bild, rand = design_system.schatten_bild(
                design, eigenschaften["schatten"], k["breite"], k["hoehe"],
                min(radius, k["breite"] / 2, k["hoehe"] / 2), tmp, cache)
            schatten[element.get("id")] = {
                "src": bild.as_uri(),
                "links": round(-rand - k["rahmen_links"], 3),
                "oben": round(-rand - k["rahmen_oben"], 3),
                "breite": round(k["breite"] + 2 * rand, 3),
                "hoehe": round(k["hoehe"] + 2 * rand, 3),
            }
        HTML(string=html_bauen(daten, hoehe, design, schatten),
             base_url=basis).write_pdf(str(ziel))
    return "WeasyPrint", hoehe, len(schatten), hinweise


def rendern_ausweich(html, ziel):
    """Ohne WeasyPrint: headless Chrome, sonst wkhtmltopdf. Gibt den Namen der
    Engine zurueck. Schreibt nichts in den Skill-Ordner — die Engines bekommen
    eine Temporaerdatei mit <base>-Tag."""
    basis = ASSETS.as_uri() + "/"
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

    design = design_system.laden()
    fehlend = design_system.schriften_fehlen(design)
    if fehlend:
        # Ohne die Datei setzt jede Engine still eine Ersatzschrift — lieber
        # gar kein PDF als eines in der falschen Schrift.
        raise SystemExit(
            "Schriftdateien fehlen — ohne sie entstuende das PDF in einer "
            "Ersatzschrift:\n" + "\n".join(f"  {p}" for p in fehlend) +
            "\nDie Schnitte nennt assets/tokens.json unter \"schriften\" "
            "(Google Fonts, OFL).")

    hinweise = pruefe(daten)
    ziel = Path(args[1]) if genau else zielpfad(Path(args[1]), daten)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    breite = design["komponenten"]["seite"]["breite"]

    try:
        engine, hoehe, schatten, layout_hinweise = rendern_weasyprint(daten, design, ziel)
        hinweise += layout_hinweise
        print(f"Seitenformat: {breite} x {hoehe}pt, {schatten} Kartenschatten")
    except ImportError:
        # Ausweichweg: Hoehe am Bild messen (letzte nicht weisse Pixelzeile).
        # Die 2pt Reserve decken den Messfehler der Rasterung — lieber eine
        # haarduenne weisse Kante als ein abgeschnittener Footer.
        engine = rendern_ausweich(html_bauen(daten, VORRAT_HOEHE, design), ziel)
        hoehe = inhaltshoehe_messen(ziel)
        if hoehe is None:
            hinweise.append(
                f"Inhaltshoehe nicht messbar (weder PyMuPDF noch pdftoppm+Pillow) — "
                f"die Seite bleibt auf Vorratshoehe {VORRAT_HOEHE}pt und traegt unten "
                "viel Weissraum. pruefe_umgebung.py zeigt, was fehlt.")
        else:
            hoehe = round(hoehe + 2)
            engine = rendern_ausweich(html_bauen(daten, hoehe, design), ziel)
            print(f"Seitenformat: {breite} x {hoehe}pt")

    seiten = seitenzahl(ziel)
    if seiten > 1:
        hinweise.append(
            f"Das PDF hat {seiten} Seiten statt einer — der Inhalt ist hoeher als "
            "die gesetzte Seitenhoehe. Das darf nicht passieren, bitte melden.")

    print(f"{ziel} geschrieben (Engine: {engine})")

    fehler, design_hinweise = design_system.pruefe_pdf(ziel, design)
    hinweise += design_hinweise
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)
    if fehler:
        print("\nFEHLER — das PDF weicht vom Design System ab (assets/tokens.json). "
              "So nicht ausliefern:", file=sys.stderr)
        for f in fehler:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(2)
    print("Design System eingehalten: Seitenbreite, Schriften, Textstile, Farben.")


if __name__ == "__main__":
    main()
