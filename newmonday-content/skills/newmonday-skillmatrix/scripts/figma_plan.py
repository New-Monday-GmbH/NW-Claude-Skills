#!/usr/bin/env python3
"""Baut aus skillmatrix.json den Bauplan fuer den Figma-Frame.

    python3 scripts/figma_plan.py skillmatrix.json arbeit/
    python3 scripts/figma_plan.py skillmatrix.json arbeit/ --pdf "ausgabe/… .pdf"

Schreibt arbeit/figma_plan.json: ein einziger Frame, darin vier Baender (Kopf,
Hero, Rumpf, Fuss) in Lesereihenfolge — alle Werte fertig ausgerechnet
(Schriftgroesse, Figma-Schnitt, Zeilenhoehe, Laufweite, Farbe, Breite, Padding,
Logomasse in pt). Das use_figma-Skript setzt nur noch, was hier steht;
Layoutwerte werden dort nicht mehr gerechnet.

Die Werte stammen aus assets/skillmatrix.css und references/layout.md — nichts
davon wird hier ein zweites Mal erfunden. Wer am CSS dreht, zieht dieses Skript
mit, sonst laeuft der Frame vom PDF weg.

Anders als beim CV-Skill gibt es hier keine Seitenaufteilung zu ermitteln: Die
Matrix ist eine einzige lange Seite und wird ein einziger Frame. Das PDF wird
deshalb nicht gebraucht — `--pdf` ist optional und traegt nur die gemessene
Hoehe als Sollwert in den Plan, damit sich der fertige Frame dagegen pruefen
laesst.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_skillmatrix import BESCHRIFTUNG  # noqa: E402  — nach sys.path.insert

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# --- Feste Masse, 1:1 aus assets/skillmatrix.css ----------------------------
# In Figma gilt 1px = 1pt, die Zahlen wandern also unveraendert in den Frame.
BREITE = 1440           # Seitenbreite, wie die Figma-Frames der Vorlage
RAND = 104              # Rand links und rechts
INHALT = 1232           # .container

FARBEN = {
    "brand": "#009193", "schwarz": "#111111", "grau": "#465469",
    "grau_2": "#64748a", "flaeche": "#f8f9fb", "linie": "#e2e8ef",
    "badge_bg": "#f0f4f9", "gruen": "#21c45d", "jahr_bg": "#e6f4f4",
    "weiss": "#ffffff", "fotokarte_bg": "#f6f7fa",
}

# Inter heisst in Figma "Semi Bold" und "Extra Bold" — mit Leerzeichen. Ohne
# Leerzeichen wirft loadFontAsync, und mit ihm faellt jeder Textknoten aus.
SCHNITT = {400: "Regular", 600: "Semi Bold", 700: "Bold", 800: "Extra Bold"}

# Muss der Vorgabe in render_skillmatrix.html_bauen() entsprechen — der
# Ansprechpartner steht als Vorgabe im Skill, nicht in der skillmatrix.json.
KONTAKT_VORGABE = {
    "name": "Manuel Klein", "rolle": "CCO",
    "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0) 155 1148 0130",
    "firma": "New Monday GmbH", "strasse": "Stresemannstraße 32",
    "ort": "10963 Berlin",
}

# Skillkarte: 397 breit, Padding 26 seitlich -> 345 Inhalt. Die Punktereihe
# misst 5 x 10 + 4 x 3,5 = 64, dazu 12 Abstand nach links; der Titel bekommt
# den Rest. Im CSS traegt jeder Punkt margin-left 3,5 (also 67,5); in Figma
# sitzt der Abstand zwischen den Punkten. Die 3,5pt Differenz sind die einzige
# bewusste Abweichung an dieser Karte.
KARTE = {"breite": 397, "radius": 14, "padding": [24, 26, 22, 26]}
KARTE_INHALT = KARTE["breite"] - KARTE["padding"][1] - KARTE["padding"][3]
PUNKTE = {"groesse": 10, "abstand": 3.5, "anzahl": 5, "oben": 4, "links": 12}
PUNKTE_BREITE = (PUNKTE["anzahl"] * PUNKTE["groesse"]
                 + (PUNKTE["anzahl"] - 1) * PUNKTE["abstand"])

# Zertifikatskarte: 1232 breit, 5pt Teal-Kante links, Padding 26/32/24/28.
ZERT = {"radius": 12, "kante": 5, "padding": [26, 32, 24, 28]}
ZERT_INHALT = INHALT - ZERT["kante"] - ZERT["padding"][1] - ZERT["padding"][3]

hinweise = []


def svg_masse(datei, breite):
    """Hoehe zur Zielbreite, aus dem Seitenverhaeltnis der SVG-Datei.

    Das CSS setzt bei allen Logos nur die Breite und laesst die Hoehe laufen.
    In Figma gibt es kein `height: auto` — die Hoehe muss im Plan stehen.
    """
    kopf = Path(datei).read_text(encoding="utf-8", errors="replace")[:800]
    treffer = re.search(
        r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', kopf)
    if not treffer:
        treffer = re.search(r'width="([\d.]+)[a-z]*"\s+height="([\d.]+)', kopf)
    if not treffer:
        hinweise.append(f"Seitenverhaeltnis von {Path(datei).name} nicht lesbar "
                        "— Hoehe geraten.")
        return round(breite / 9.869, 3)
    w, h = float(treffer.group(1)), float(treffer.group(2))
    return round(breite * h / w, 3)


def logo(datei, breite):
    """Absoluter Pfad, nicht relativ: Die Logos liegen im Skill-Ordner, Foto und
    Zertifikatsbilder im Arbeitsverzeichnis des Nutzers. Relativ liesse sich im
    Plan nicht mehr unterscheiden, worauf sich welcher Pfad bezieht."""
    pfad = ASSETS / datei
    return {"datei": str(pfad), "typ": "svg", "breite": breite,
            "hoehe": svg_masse(pfad, breite)}


def bild(wert, wofuer):
    """Rasterbild aus der JSON: absolut machen und auf Existenz pruefen."""
    if not wert:
        return None
    p = Path(str(wert)).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        hinweise.append(f"{wofuer} nicht gefunden: {wert}")
        return None
    return {"datei": str(p), "typ": "raster"}


def typo(groesse, gewicht, zeilenhoehe=None, laufweite=0, farbe="schwarz",
         versalien=False, deckkraft=1):
    """Ein fertiger Textstil. zeilenhoehe None heisst in Figma AUTO — das ist
    das Gegenstueck zu `line-height: normal` im CSS."""
    return {"groesse": groesse, "schnitt": SCHNITT[gewicht],
            "zeilenhoehe": zeilenhoehe, "laufweite": laufweite,
            "farbe": farbe, "versalien": versalien, "deckkraft": deckkraft}


def text(inhalt, stil, breite, **rest):
    return {"text": " ".join(str(inhalt or "").split()), "typo": stil,
            "breite": breite, **rest}


# --- Die vier Baender -------------------------------------------------------

def band_kopf():
    """Teal-Balken 88pt, Wortmarke bei 44/33 — nicht auf der Containerkante,
    so steht sie in der Vorlage."""
    return {"art": "kopf", "hoehe": 88, "hintergrund": "brand",
            "logo": {**logo("nm-logo-weiss.svg", 166), "links": 44, "oben": 33}}


def band_hero(person, labels):
    karte = {
        "breite": 433, "hoehe": 390, "radius": 16, "abstand_oben": 27,
        "hintergrund": "fotokarte_bg",
        "foto": bild(person.get("foto"), "Foto"),
        # Der Verlauf liegt ueber dem Foto und beginnt bei 63 % der Kartenhoehe.
        # Eine Farbe, fuenf Deckkraftstufen — genau die Stopps aus dem CSS.
        "verlauf": {"hoehe": 145, "farbe": "brand",
                    "stopps": [{"position": 0.0, "deckkraft": 0.0},
                               {"position": 0.025, "deckkraft": 0.16},
                               {"position": 0.4, "deckkraft": 0.62},
                               {"position": 0.75, "deckkraft": 0.96},
                               {"position": 1.0, "deckkraft": 1.0}]},
        "textlinks": 26, "textunten": 22, "zeilenabstand": 5,
        "name": text(person.get("name"), typo(24, 700, farbe="weiss"), 381),
        "erfahrung": text(person.get("erfahrung"), typo(15, 400, farbe="weiss"), 381),
    }
    if not karte["foto"]:
        hinweise.append("Kein Foto — die Fotokarte im Frame zeigt nur den Verlauf.")

    schwerpunkte = person.get("schwerpunkte") or []
    return {
        "art": "hero", "hintergrund": "weiss", "oben": 31, "unten": 60,
        "textspalte": 700,
        "badge": {
            "text": f"{labels['verfuegbar']} {person.get('verfuegbar_ab', '')}".strip(),
            "typo": typo(12, 600, laufweite=1.2, farbe="grau", versalien=True),
            "radius": 14, "padding": [6, 16, 6, 14], "abstand": 8,
            "hintergrund": "badge_bg", "rahmen": "linie", "rahmenstaerke": 1,
            "punkt": {"groesse": 8, "farbe": "gruen"},
        },
        "name": text(person.get("name"),
                     typo(60, 700, 1.1, -1.8), 700, abstand_oben=32),
        "rolle": text(person.get("rolle"),
                      typo(60, 700, 1.1, -1.8, "brand"), 700, abstand_oben=4),
        "beschreibung": text(person.get("beschreibung"),
                             typo(20, 400, 1.55, 0, "grau"), 640, abstand_oben=36),
        "schwerpunkte": {
            "abstand_oben": 40, "abstand": 20, "radius": 14,
            "rahmen": "brand", "rahmenstaerke": 2, "padding": [11, 14, 11, 14],
            "typo": typo(19, 600), "eintraege": [str(s) for s in schwerpunkte],
        },
        "fotokarte": karte,
    }


def sektion_zertifikate(daten, labels):
    karten = []
    for z in daten.get("zertifikate") or []:
        tags = [str(t) for t in (z.get("tags") or [])]
        karten.append({
            "abstand_oben": 40, "breite": INHALT, "inhaltsbreite": ZERT_INHALT,
            **ZERT, "kantenfarbe": "brand", "hintergrund": "weiss",
            "titel": text(z.get("titel"), typo(18, 700), ZERT_INHALT - 120),
            "jahr": (text(z.get("jahr"), typo(13, 600, farbe="brand"), None,
                          radius=6, padding=[4, 12, 4, 12],
                          hintergrund="jahr_bg", abstand_links=24)
                     if z.get("jahr") else None),
            "aussteller": (text(f"{labels['aussteller']} {z['aussteller']}",
                                typo(14, 600), ZERT_INHALT, abstand_oben=10)
                           if z.get("aussteller") else None),
            "beschreibung": (text(z.get("beschreibung"),
                                  typo(14, 400, 1.4, 0, "grau_2"),
                                  ZERT_INHALT, abstand_oben=12)
                             if z.get("beschreibung") else None),
            "tags": ({"abstand_oben": 16, "abstand_x": 10, "abstand_y": 8,
                      "radius": 8, "padding": [5, 12, 5, 12],
                      "rahmen": "linie", "rahmenstaerke": 1,
                      "hintergrund": "weiss",
                      "typo": typo(12, 400, farbe="grau_2"),
                      "eintraege": tags} if tags else None),
        })

    bilder = [bild(b, "Zertifikatsbild") for b in daten.get("zertifikat_bilder") or []]
    bilder = [b for b in bilder if b]
    # Drei Kacheln je Zeile, wie `| batch(3)` im Template. Die Zeile misst
    # 3 x 395 + 2 x 24 = 1233 und steht damit 1pt ueber dem Container — so ist
    # es im PDF auch. Die Zeile deshalb auf HUG, nicht auf 1232 festnageln.
    zeilen = [bilder[i:i + 3] for i in range(0, len(bilder), 3)]

    return {
        "art": "zertifikate",
        "titel": text(labels["zertifikate"], typo(24, 700), None),
        "icon": {**logo("icon-zertifikat.svg", 26), "abstand": 14, "versatz": -4},
        "karten": karten,
        "raster": ({"abstand_oben": 64, "abstand": 24,
                    "kachel": {"breite": 395, "hoehe": 284, "radius": 8},
                    "zeilen": zeilen} if zeilen else None),
    }


def sektion_kompetenzen(daten, labels):
    kategorien = []
    for k in daten.get("kompetenzen") or []:
        skills = k.get("skills") or []
        zeilen = []
        for i in range(0, len(skills), 3):
            zeile = []
            for s in skills[i:i + 3]:
                punkte = s.get("punkte")
                punkte = punkte if isinstance(punkte, int) else 0
                zeile.append({
                    **KARTE, "hintergrund": "weiss",
                    "name": text(s.get("name"), typo(17, 700),
                                 KARTE_INHALT - PUNKTE_BREITE - PUNKTE["links"]),
                    "punkte": {**PUNKTE, "voll": max(0, min(5, punkte)),
                               "breite": PUNKTE_BREITE,
                               "voll_farbe": "brand", "leer_farbe": "linie"},
                    "beschreibung": text(s.get("beschreibung"),
                                         typo(14, 400, 1.45, -0.1, "grau_2"),
                                         KARTE_INHALT, abstand_oben=10),
                })
            zeilen.append(zeile)
        kategorien.append({
            "abstand_oben": 40,
            "label": text(k.get("kategorie"),
                          typo(14, 600, laufweite=0.8, farbe="grau_2",
                               versalien=True), INHALT),
            "label_unten": 14,
            "hairline": {"breite": INHALT, "staerke": 1, "farbe": "linie"},
            "zeilenabstand": 20, "kartenabstand": 20.5,
            "zeilen": zeilen,
        })
    return {
        "art": "kompetenzen",
        "titel": text(labels["kernkompetenzen"], typo(24, 700), None),
        "icon": {**logo("icon-kernkompetenzen.svg", 26),
                 "abstand": 14, "versatz": -4},
        "kategorien": kategorien,
    }


def band_rumpf(daten, labels):
    sektionen = []
    zert = sektion_zertifikate(daten, labels)
    komp = sektion_kompetenzen(daten, labels)
    hat_zert = bool(zert["karten"] or zert["raster"])
    if hat_zert and daten.get("zertifikate_position") != "ende":
        sektionen.append(zert)
    if komp["kategorien"]:
        sektionen.append(komp)
    if hat_zert and daten.get("zertifikate_position") == "ende":
        sektionen.append(zert)
    return {"art": "rumpf", "hintergrund": "flaeche", "oben": 80, "unten": 56,
            "sektionsabstand": 64, "sektionen": sektionen}


def band_fuss(daten, labels):
    k = dict(KONTAKT_VORGABE)
    k.update(daten.get("kontakt") or {})
    spalten = [
        (labels["ansprechpartner"], f"{k['name']}\n{k['rolle']}"),
        (labels["kontakt"], f"{k['mail']}\n{k['telefon']}"),
        (labels["adresse"], f"{k['firma']}\n{k['strasse']}\n{k['ort']}"),
    ]
    return {
        "art": "fuss", "hintergrund": "brand", "oben": 64, "unten": 56,
        "frage": text(labels["footer_frage"], typo(28, 700, farbe="weiss"), INHALT),
        "linie": {"abstand_oben": 40, "staerke": 1, "farbe": "weiss",
                  "deckkraft": 0.25, "breite": INHALT},
        "zeile": {
            "abstand_oben": 40,
            "logo": {**logo("nm-logo-weiss.svg", 140), "abstand_rechts": 96},
            "spaltenbreite": 240, "spaltenabstand": 48,
            "spalten": [{
                "label": text(bez, typo(11, 600, laufweite=0.8, farbe="weiss",
                                        versalien=True, deckkraft=0.75), 240),
                # Mehrzeilig: die Zeilenumbrueche sind Teil des Textknotens,
                # deshalb hier nicht ueber " ".join() normalisieren.
                "wert": {"text": wert, "typo": typo(14, 400, 1.5, farbe="weiss"),
                         "breite": 240, "abstand_oben": 10},
            } for bez, wert in spalten],
        },
    }


def plan_bauen(daten, pdf=None):
    sprache = daten.get("sprache", "de")
    labels = dict(BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"]))
    if daten.get("zertifikate_titel"):
        labels["zertifikate"] = daten["zertifikate_titel"]
    person = daten.get("person") or {}

    name = " ".join(str(person.get("name") or "Skillmatrix").split())
    plan = {
        "rahmen": {"name": f"Skillmatrix — {name}", "breite": BREITE,
                   "rand": RAND, "inhalt": INHALT, "hintergrund": "weiss"},
        "sprache": sprache,
        "farben": FARBEN,
        "schnitte": sorted(set(SCHNITT.values())),
        "baender": [band_kopf(), band_hero(person, labels),
                    band_rumpf(daten, labels), band_fuss(daten, labels)],
    }
    if pdf:
        hoehe = pdf_hoehe(pdf)
        if hoehe:
            # Sollwert zum Gegenpruefen. Der Frame selbst laeuft auf HUG —
            # eine feste Hoehe waere beim ersten Textwechsel falsch.
            plan["rahmen"]["hoehe_pdf"] = hoehe
    return plan


def pdf_hoehe(pfad):
    try:
        from pypdf import PdfReader
    except ImportError:
        hinweise.append("pypdf fehlt — die PDF-Hoehe kommt nicht in den Plan.")
        return None
    try:
        kasten = PdfReader(str(pfad)).pages[0].mediabox
        return round(float(kasten.height), 1)
    except Exception as fehler:                       # noqa: BLE001
        hinweise.append(f"PDF-Hoehe nicht lesbar: {fehler}")
        return None


def main():
    args = sys.argv[1:]
    pdf = None
    if "--pdf" in args:
        i = args.index("--pdf")
        if i + 1 >= len(args):
            raise SystemExit("--pdf braucht einen Pfad")
        pdf = args[i + 1]
        args = args[:i] + args[i + 2:]
    if len(args) < 2:
        raise SystemExit(__doc__)

    daten = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    ziel = Path(args[1])
    if ziel.suffix.lower() != ".json":
        ziel = ziel / "figma_plan.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)

    plan = plan_bauen(daten, pdf)
    ziel.write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                    encoding="utf-8")

    baender = plan["baender"]
    sektionen = baender[2]["sektionen"]
    karten = sum(len(z) for s in sektionen if s["art"] == "kompetenzen"
                 for k in s["kategorien"] for z in k["zeilen"])
    print(f"{ziel} geschrieben — {len(baender)} Baender, "
          f"{len(sektionen)} Sektionen, {karten} Skillkarten")
    if plan["rahmen"].get("hoehe_pdf"):
        print(f"Sollhoehe aus dem PDF: {plan['rahmen']['hoehe_pdf']}pt")
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
