#!/usr/bin/env python3
"""Prueft nach der Installation, ob die ganze Kette laeuft.

    python3 scripts/selbsttest.py

Rendert den mitgelieferten Beispiel-Lebenslauf in ein temporaeres Verzeichnis
und kontrolliert das Ergebnis: Seitenzahl, A4-Format, eingebettete Schriften,
Logos und Foto — und ob Schriften, Farben und Abstaende den Designwerten aus
assets/tokens.json entsprechen (pruefe_design). Danach dasselbe fuer die anonyme
Fassung — ob vom Namen im fertigen PDF wirklich nichts uebrig ist. Schreibt
nichts in den Skill-Ordner.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def pruefe(pdf):
    fehler = []
    from pypdf import PdfReader
    leser = PdfReader(str(pdf))

    seiten = len(leser.pages)
    if seiten < 2:
        fehler.append(f"nur {seiten} Seite(n) — erwartet werden mehrere")

    kasten = leser.pages[0].mediabox
    breite, hoehe = round(float(kasten.width)), round(float(kasten.height))
    if not (590 <= breite <= 600 and 838 <= hoehe <= 846):
        fehler.append(f"Seitenformat {breite}x{hoehe}pt statt A4 (595x842)")

    schriften = set()
    bilder = 0
    for seite in leser.pages:
        mittel = seite.get("/Resources", {})
        for f in (mittel.get("/Font", {}) or {}).values():
            schriften.add(str(f.get_object().get("/BaseFont", "")))
        bilder += len(mittel.get("/XObject", {}) or {})
    if not any("Inter" in f for f in schriften):
        fehler.append(f"Inter nicht eingebettet, gefunden: {sorted(schriften) or 'keine'}")
    if bilder == 0:
        fehler.append("keine Bilder im PDF — Logos und Foto fehlen")

    # Bildung und Skillset gehoeren auf Seite 1, unter den Profilkopf, und
    # muessen dort komplett Platz finden — die Stationen fangen erst danach an.
    erste = " ".join((leser.pages[0].extract_text() or "").split())
    for rubrik in ("Bildung", "Skillset"):
        if rubrik not in erste:
            fehler.append(f"{rubrik} steht nicht auf Seite 1")
    if "Union Investment" in erste:
        fehler.append("die Stationen beginnen schon auf Seite 1")
    # Das Kurzprofil gehoert auf Seite 2 — auf Seite 1 nimmt es den Platz weg,
    # den Bildung und Skillset brauchen.
    if "Als UX-Designer mit Schwerpunkt" in erste:
        fehler.append("das Kurzprofil steht auf Seite 1 statt auf Seite 2")

    return seiten, breite, hoehe, len(schriften), bilder, fehler


# Nachbau einer oeffentlichen Profilseite: oben das Foto der Person im
# og:image-Tag, darunter — wie im Original unter "Weitere aehnliche Profile" —
# fremde Gesichter in GROESSERER Variante. Wer nach Bildgroesse auswaehlt,
# laedt hier ein falsches Gesicht.
PROFILSEITE = '''
<meta property="og:image" content="https://media.licdn.com/dms/image/v2/PERSON/profile-displayphoto-shrink_200_200/0?e=1&amp;t=x" />
<img src="https://media.licdn.com/dms/image/v2/FREMD1/profile-displayphoto-shrink_400_400/0?e=1\\u0026t=y">
<img src="https://media.licdn.com/dms/image/v2/FREMD2/profile-displayphoto-scale_400_400/0?e=1\\u0026t=z">
'''


def pruefe_linkedin_auswahl():
    """Das Foto muss von der Person kommen, nicht aus der Seitenspalte."""
    sys.path.insert(0, str(WURZEL / "scripts"))
    from linkedin_foto import foto_urls, url_normalisieren

    treffer = foto_urls(PROFILSEITE)
    if not treffer:
        return ["LinkedIn: kein Foto in der Testseite erkannt"]
    fremd = [u for u in treffer if "/PERSON/" not in u]
    if fremd:
        return [f"LinkedIn: fremdes Gesicht ausgewaehlt — {fremd[0][:80]}"]

    # Die Eingabeformen, die Nutzer tatsaechlich schicken.
    for eingabe in ("https://www.linkedin.com/in/timo-muster/",
                    "https://de.linkedin.com/in/timo-muster?originalSubdomain=de",
                    "timo-muster"):
        if url_normalisieren(eingabe)[1] != "timo-muster":
            return [f"LinkedIn: {eingabe!r} falsch normalisiert"]
    return []


# Nachbau einer Portfolioseite: Logo und Inline-Grafik muessen wegfallen, das
# og:image zuerst kommen, aus dem srcset die groesste Variante, und der Link auf
# eine fremde Domain darf nicht mitgelesen werden.
PORTFOLIOSEITE = '''
<meta property="og:image" content="/img/portrait.jpg">
<a href="/ueber-mich">Ueber mich</a>
<a href="https://fremd.de/about">Gastbeitrag</a>
<img src="/img/logo-dark.png">
<img src="grafik.svg">
<img src="data:image/png;base64,xxx">
<img src="img/projekt.jpg" srcset="img/projekt-400.jpg 400w, img/projekt-900.jpg 900w">
'''


def pruefe_website_auswahl():
    """Die Bildersuche auf einer Website muss den offensichtlichen Ballast filtern."""
    sys.path.insert(0, str(WURZEL / "scripts"))
    from website_foto import bild_urls, unterseiten

    basis = "https://timo-muster.de/"
    bilder = bild_urls(PORTFOLIOSEITE, basis)
    fehler = []
    if not bilder or not bilder[0].endswith("/img/portrait.jpg"):
        fehler.append(f"Website: og:image steht nicht vorn — {bilder[:2]}")
    for muster in ("logo-dark", ".svg", "data:"):
        if any(muster in u for u in bilder):
            fehler.append(f"Website: {muster} nicht ausgefiltert")
    if not any(u.endswith("projekt-900.jpg") for u in bilder):
        fehler.append("Website: groesste srcset-Variante nicht genommen")

    seiten = unterseiten(PORTFOLIOSEITE, basis)
    if seiten != ["https://timo-muster.de/ueber-mich"]:
        fehler.append(f"Website: falsche Unterseiten verfolgt — {seiten}")
    return fehler


def pruefe_gleicher_titel(tmp):
    """Rolle und erster Stationstitel gleich — laeuft der Ueberlauf trotzdem auf?

    Bei "Softwareentwickler" als Rolle UND als Stationstitel hat die Messung den
    Titel schon im Profilkopf auf Seite 1 gefunden und "passt" gemeldet, waehrend
    das Skillset in Wirklichkeit auf Seite 2 lief. Gemessen wird deshalb am Ende
    des Blocks, nicht am Anfang der Stationen.
    """
    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    rolle = daten["stationen"][0]["titel"]
    daten["person"]["rolle"] = rolle
    # So viel Skillset, dass es sicher nicht auf Seite 1 passt.
    daten["skillset"]["faehigkeiten"] = [f"Eintrag {i}" for i in range(36)]
    quelle = Path(tmp) / "gleicher-titel.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    ziel = Path(tmp) / "gleicher-titel.pdf"
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel),
         "--pfad-genau"],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if "passen nicht" not in lauf.stderr:
        return ["Ueberlauf nicht erkannt, wenn Rolle und Stationstitel gleich sind"]
    return []


def pruefe_verweise(tmp):
    """Stehen die Verweise unter der Erfahrungszeile — benannt und anklickbar?

    Sie standen frueher rechts in der Kopfzeile und davor als Fusszeile unter
    Seite 1. Geprueft wird alles, was beim Umzug schiefgehen kann: der
    Anzeigetext (benannt, nicht als Adresse), die Lage im Profilkopf (direkt
    unter der Erfahrungszeile, alle in einer Zeile nebeneinander) und die
    Link-Annotation im PDF (ohne sie ist der Unterstrich eine Behauptung).
    """
    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    daten["person"]["links"] = [
        {"titel": "LinkedIn", "url": "https://www.linkedin.com/in/timo-muster"},
        {"titel": "Xing", "url": "https://www.xing.com/profile/Timo_Muster"},
        {"titel": "Portfolio", "url": "https://timo-muster.de"},
    ]
    quelle = Path(tmp) / "verweise.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    ziel = Path(tmp) / "verweise.pdf"
    subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel),
         "--pfad-genau"],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if not ziel.exists():
        return ["Verweistest: PDF nicht gerendert"]

    from pypdf import PdfReader
    seite = PdfReader(str(ziel)).pages[0]
    fehler = []

    # Gemessen wird relativ zur Erfahrungszeile, nicht gegen feste Hoehen: die
    # Lage des Profilkopfs haengt an der Laenge von Name und Rolle.
    hoehen = {}

    def besucher(text, cm, tm, schrift, groesse):
        y = tm[5] * cm[3] + cm[5]
        for marke in ("Jahre Erfahrung", "LinkedIn", "Xing", "Portfolio"):
            if marke in text:
                hoehen.setdefault(marke, y)

    seite.extract_text(visitor_text=besucher)

    fehlend = [m for m in ("LinkedIn", "Xing", "Portfolio") if m not in hoehen]
    if fehlend:
        fehler.append(f"Verweise stehen nicht auf Seite 1: {', '.join(fehlend)}")
    elif "Jahre Erfahrung" not in hoehen:
        fehler.append("Erfahrungszeile nicht gefunden — Lage der Verweise nicht pruefbar")
    else:
        # Von Schriftlinie zu Schriftlinie: Rest der Erfahrungszeile, der
        # Abstand aus tokens.json und die Oberlaenge der Verweiszeile.
        sys.path.insert(0, str(WURZEL / "scripts"))
        import tokens
        soll = (tokens.stil("rolle")["zeile"] - tokens.grundlinie("rolle")
                + tokens.laden()["abstand"]["erfahrung_verweise"] + tokens.grundlinie("verweis"))
        abstand = hoehen["Jahre Erfahrung"] - hoehen["LinkedIn"]
        if abs(abstand - soll) > 0.3:
            fehler.append(f"Verweise stehen {abstand:.1f}pt unter der Erfahrungszeile "
                          f"statt {soll:.1f}pt")
        if max(hoehen[m] for m in ("LinkedIn", "Xing", "Portfolio")) - \
           min(hoehen[m] for m in ("LinkedIn", "Xing", "Portfolio")) > 1:
            fehler.append("Verweise stehen untereinander statt in einer Zeile")

    # Benannt, nicht als Adresse: eine nackte URL im Text heisst, dass der
    # Anzeigetext aus VERWEISTEXT nicht gegriffen hat.
    text = seite.extract_text()
    if "linkedin.com" in text or "xing.com" in text:
        fehler.append("Verweise stehen als Adresse im Text statt benannt")
    for erwartet in ("zum LinkedIn Profil", "zum Xing Profil", "zum Portfolio"):
        if erwartet not in text:
            fehler.append(f"Verweistext fehlt: {erwartet}")

    adressen = {a.get_object().get("/A", {}).get("/URI")
                for a in (seite.get("/Annots") or [])
                if a.get_object().get("/Subtype") == "/Link"}
    for erwartet in ("https://www.linkedin.com/in/timo-muster",
                     "https://www.xing.com/profile/Timo_Muster",
                     "https://timo-muster.de"):
        if erwartet not in adressen:
            fehler.append(f"Verweis nicht anklickbar: {erwartet}")
    return fehler


def pruefe_stationsumbruch(tmp):
    """Faengt eine Station unten auf der Seite an, muessen zwei Bullets folgen.

    Sonst steht dort ein Jobtitel mit einem einzelnen Stichpunkt an der
    Blattkante und alles Weitere hinter dem Umbruch. Der Fuellstand ist so
    gewaehlt, dass die letzte Station des Beispiels genau an die Seitenkante
    rutscht — ohne die Umbruchregeln in cv.css blieb dort ein Bullet haengen.
    """
    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    daten["stationen"][0]["projekte"][0]["aufgaben"] += [
        f"Fuelltext Nummer {i} zum Verschieben der Seitenkante" for i in range(11)
    ]
    quelle = Path(tmp) / "umbruch.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    ziel = Path(tmp) / "umbruch.pdf"
    subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel),
         "--pfad-genau"],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if not ziel.exists():
        return ["Umbruchtest: PDF nicht gerendert"]

    from pypdf import PdfReader
    seiten = [" ".join((s.extract_text() or "").split()) for s in PdfReader(str(ziel)).pages]
    fehler = []
    for station in daten["stationen"]:
        aufgaben = station.get("aufgaben") or []
        if len(aufgaben) < 2:
            continue
        titel = " ".join(station["titel"].split())
        nummer = next((i for i, t in enumerate(seiten, 1) if titel in t), None)
        if nummer is None:
            continue
        drauf = sum(1 for a in aufgaben
                    if " ".join(a.split())[:40] in seiten[nummer - 1])
        if drauf < 2:
            fehler.append(
                f"Station '{titel[:40]}' faengt auf Seite {nummer} an, aber nur "
                f"{drauf} von {len(aufgaben)} Stichpunkten stehen dort — sie "
                "gehoert komplett auf die naechste Seite"
            )
    return fehler


def _bildlagen(pdf):
    """Jedes Rasterbild im PDF als Lage in pt: Seite, x, y, Breite, Hoehe.

    x von links, y die Oberkante von der Blattoberkante aus — dieselben
    Koordinaten wie im Figma-Frame. SVG-Logos zeichnet WeasyPrint als Pfade und
    nicht als Bildobjekt; sie tauchen hier nicht auf.
    """
    from pypdf import PdfReader
    from pypdf.generic import ContentStream
    leser = PdfReader(str(pdf))

    def mal(a, b):
        return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
                a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
                a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]

    lagen = []
    for nummer, seite in enumerate(leser.pages, start=1):
        hoehe = float(seite.mediabox.height)
        objekte = (seite.get("/Resources") or {}).get("/XObject") or {}
        matrix, stapel = [1, 0, 0, 1, 0, 0], []
        for operanden, op in ContentStream(seite.get_contents(), leser).operations:
            if op == b"q":
                stapel.append(matrix)
            elif op == b"Q" and stapel:
                matrix = stapel.pop()
            elif op == b"cm":
                matrix = mal([float(o) for o in operanden], matrix)
            elif op == b"Do" and operanden[0] in objekte:
                if objekte[operanden[0]].get_object().get("/Subtype") != "/Image":
                    continue
                lagen.append({"seite": nummer, "x": matrix[4],
                              "y": hoehe - matrix[5] - matrix[3],
                              "breite": matrix[0], "hoehe": matrix[3]})
    return lagen


def pruefe_projektlogos(tmp):
    """Stehen mehrere Projektlogos nebeneinander, gleich gross, auf der Mitte?

    Design-Feedback vom 28.09.2026: Projektlogos standen untereinander und
    schrumpften ab zwei Marken auf 19pt. Jetzt stehen sie in einer Reihe ueber
    dem Kundennamen, jedes in derselben Groesse wie ein einzelnes. Beim ersten
    Versuch lagen sie im PDF alle uebereinander an derselben Stelle — WeasyPrint
    gibt einem <img> als Flex-Element die Breite 0. Deshalb wird am fertigen PDF
    nachgemessen und nicht am CSS. Gemessen wird mit zwei PNGs: SVG-Logos
    zeichnet WeasyPrint als Pfade, deren Lage sich nicht auslesen laesst.
    """
    sys.path.insert(0, str(WURZEL / "scripts"))
    import tokens
    from render_cv import LOGO_PROJEKT_GROESSE, logo_masse
    t = tokens.laden()
    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    projekt = daten["stationen"][0]["projekte"][0]
    reihe = ["beq.png", "tollwerk.png"]
    projekt["logo"] = reihe
    quelle = Path(tmp) / "projektlogos.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    ziel = Path(tmp) / "projektlogos.pdf"
    subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel),
         "--pfad-genau"],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if not ziel.exists():
        return ["Projektlogos: PDF nicht gerendert"]

    lagen = _bildlagen(ziel)
    masse = [logo_masse(d, LOGO_PROJEKT_GROESSE) for d in reihe]
    kandidaten = [[l for l in lagen if abs(l["breite"] - b) < 0.1 and abs(l["hoehe"] - h) < 0.1]
                  for b, h in masse]
    if not all(kandidaten):
        return [f"Projektlogos: nicht in {LOGO_PROJEKT_GROESSE}pt gesetzt — gesucht "
                f"{masse}, im PDF {[(round(l['breite'], 1), round(l['hoehe'], 1)) for l in lagen]}"]
    # beq.png steht im Beispiel auch allein an einem Projekt, in derselben
    # Groesse. Das Paar ist das, dessen Mitten auf einer Hoehe liegen.
    mitte = lambda l: l["y"] + l["hoehe"] / 2
    paar = next(((a, b) for a in kandidaten[0] for b in kandidaten[1]
                 if a["seite"] == b["seite"] and abs(mitte(a) - mitte(b)) < 0.3), None)
    if paar is None:
        return ["Projektlogos: stehen nicht nebeneinander auf einer Hoehe — "
                "sie liegen untereinander oder an verschiedenen Stellen"]
    erstes, zweites = paar
    fehler = []
    links = t["seite"]["rand_links"] + t["abgeleitet"]["einzug"]
    if abs(erstes["x"] - links) > 0.3:
        fehler.append(f"Projektlogos: das erste steht bei x = {erstes['x']:.1f}pt statt "
                      f"{links:.1f}pt an der Textkante")
    soll_x = erstes["x"] + erstes["breite"] + t["raster"]["projektlogo_reihe"]
    if abs(zweites["x"] - soll_x) > 0.3:
        fehler.append(f"Projektlogos: das zweite steht bei x = {zweites['x']:.1f}pt statt "
                      f"{soll_x:.1f}pt — Abstand nicht projektlogo_reihe aus tokens.json")

    # Der Kundenname steht projektlogo_kunde unter der Unterkante der Reihe.
    unten = max(l["y"] + l["hoehe"] for l in paar)
    kunde = next((l for l in _laeufe(ziel) if l["seite"] == erstes["seite"]
                  and l["text"].startswith(projekt["kunde"]) and l["y"] > unten), None)
    if kunde is None:
        fehler.append("Projektlogos: Kundenname unter der Logoreihe nicht gefunden")
    else:
        soll_y = unten + t["abstand"]["projektlogo_kunde"] + tokens.grundlinie("kunde")
        if abs(kunde["y"] - soll_y) > 0.3:
            fehler.append(f"Projektlogos: Kundenname steht {kunde['y'] - unten:.1f}pt unter "
                          f"der Logoreihe statt {soll_y - unten:.1f}pt")
    return fehler


# Die Sollwerte stehen hier und nicht aus render_cv.py gelesen: die vier Gruppen
# in ihrer Anordnung (Vorgabe vom 29.09.2026) und die Sprachvorgabe.
SKILLSET_SOLL = {"de": [["Fähigkeiten", "Branchen"], ["Tools", "Sprachen"]],
                 "en": [["Skills", "Industries"], ["Tools", "Languages"]]}
SPRACHEN_SOLL = {"de": ["Deutsch – Muttersprache", "Englisch – Business Niveau"],
                 "en": ["German – Native speaker", "English – Business level"]}


def pruefe_skillset(tmp):
    """Hat das Skillset immer dieselben vier Gruppen, 2 x 2, mit der Sprachvorgabe?

    Vorgabe vom 29.09.2026: In jedem Lebenslauf stehen Faehigkeiten, Branchen,
    Tools und Sprachen — links Faehigkeiten und Branchen, rechts Tools und
    Sprachen. Deutsch – Muttersprache und Englisch – Business Niveau stehen
    immer drin, auch wenn das Material sie nicht nennt oder ein anderes Niveau
    angibt; weitere Sprachen bleiben mit ihrem Niveau. Vorher trug jeder
    Lebenslauf andere Gruppen. Geprueft wird am gerenderten PDF (Titel, Lage,
    Sprachzeilen) und an der Aufbereitung (alte cv.json, Englisch, Luecken).
    """
    sys.path.insert(0, str(WURZEL / "scripts"))
    import tokens
    from render_cv import skillset_gruppen, sprachen_mit_vorgabe
    t = tokens.laden()
    fehler = []

    # Das Material nennt Englisch mit anderem Niveau, Deutsch gar nicht, dazu
    # Franzoesisch — und Figma steht doppelt.
    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    daten["skillset"]["sprachen"] = ["Englisch (C1)", "Französisch – Grundkenntnisse"]
    daten["skillset"]["tools"] = list(daten["skillset"]["tools"]) + ["Figma"]
    quelle = Path(tmp) / "skillset.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    ziel = Path(tmp) / "skillset.pdf"
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel),
         "--pfad-genau"],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if not ziel.exists():
        return ["Skillset: PDF nicht gerendert"]

    seite1 = [l for l in _laeufe(ziel) if l["seite"] == 1]
    rubrik = next((l for l in seite1 if l["text"] == "Skillset"), None)
    if rubrik is None:
        return ["Skillset: Rubrik steht nicht auf Seite 1"]
    stil = tokens.stil("gruppe")
    titel = {l["text"]: l for l in seite1 if l["y"] > rubrik["y"]
             and _schriftname(l["schrift"]) == _schriftname(tokens.postscript("gruppe"))
             and round(l["groesse"], 1) == stil["groesse"]}
    soll = SKILLSET_SOLL["de"]
    erwartet = [n for spalte in soll for n in spalte]
    if sorted(titel) != sorted(erwartet):
        return [f"Skillset: Gruppen {sorted(titel)} statt {sorted(erwartet)}"]
    links = t["seite"]["rand_links"]
    rechts = links + t["abgeleitet"]["halbe_spalte"] + t["raster"]["spaltenabstand"]
    for x, spalte in ((links, soll[0]), (rechts, soll[1])):
        oben, unten = titel[spalte[0]], titel[spalte[1]]
        if abs(oben["x"] - x) > 0.3 or abs(unten["x"] - x) > 0.3:
            fehler.append(f"Skillset: {spalte[0]}/{spalte[1]} stehen nicht in der Spalte bei "
                          f"x = {x:.0f}pt")
        if not unten["y"] > oben["y"]:
            fehler.append(f"Skillset: {spalte[1]} steht nicht unter {spalte[0]}")
    if abs(titel[soll[0][0]]["y"] - titel[soll[1][0]]["y"]) > 0.3:
        fehler.append(f"Skillset: {soll[0][0]} und {soll[1][0]} stehen nicht auf einer Hoehe")

    sprachzeilen = [l["text"] for l in sorted(seite1, key=lambda l: l["y"])
                    if l["y"] > titel[soll[1][1]]["y"] and l["x"] > rechts
                    and l["text"] not in ("•", "")]
    erwartet = SPRACHEN_SOLL["de"] + ["Französisch – Grundkenntnisse"]
    if sprachzeilen[:3] != erwartet:
        fehler.append(f"Skillset: Sprachen {sprachzeilen[:3]} statt {erwartet}")
    tools = [l for l in seite1 if l["text"] == "Figma" and l["x"] > rechts]
    if len(tools) != 1:
        fehler.append(f"Skillset: 'Figma' steht {len(tools)}-mal unter Tools statt einmal")
    for meldung in ("Englisch steht als", "Deutsch – Muttersprache“ ergänzt", "stand doppelt"):
        if meldung not in lauf.stderr:
            fehler.append(f"Skillset: Hinweis fehlt in der Ausgabe — '{meldung} …'")

    # Aeltere cv.json mit freien Gruppen: Eindeutiges wird zugeordnet, der Rest
    # faellt raus und wird gemeldet — nichts verschwindet still.
    alt = {"sprache": "de", "skillset": {
        "links": [{"titel": "Fähigkeiten", "eintraege": ["A"]},
                  {"titel": "Zertifizierungen", "eintraege": ["Z"]},
                  {"titel": "Branchenerfahrung", "eintraege": ["B"]}],
        "rechts": [{"titel": "Tools", "eintraege": ["T"]},
                   {"titel": "Kunden und Partner", "eintraege": ["K"]}]}}
    spalten, hinweise = skillset_gruppen(alt)
    if [[g["titel"] for g in s] for s in (spalten["links"], spalten["rechts"])] != soll:
        fehler.append("Skillset: alte cv.json landet nicht in den vier festen Gruppen")
    for gruppe in ("Zertifizierungen", "Kunden und Partner"):
        if not any(gruppe in h for h in hinweise):
            fehler.append(f"Skillset: aus der alten cv.json fiel „{gruppe}“ still weg")

    # Englischer Lebenslauf: englische Titel, englische Sprachvorgabe.
    spalten, _ = skillset_gruppen({"sprache": "en", "skillset": {
        "faehigkeiten": ["UX"], "branchen": ["Energy"], "tools": ["Figma"]}})
    if [[g["titel"] for g in s] for s in (spalten["links"], spalten["rechts"])] != SKILLSET_SOLL["en"]:
        fehler.append("Skillset: englische Gruppentitel stimmen nicht")
    if spalten["rechts"][-1]["eintraege"] != SPRACHEN_SOLL["en"]:
        fehler.append(f"Skillset: englische Sprachvorgabe fehlt — {spalten['rechts'][-1]['eintraege']}")

    # Eine zusammengefasste Zeile traegt die Sprache schon und bleibt, wie sie ist.
    zeilen, _ = sprachen_mit_vorgabe(["Deutsch, Italienisch – Muttersprache", "Englisch"])
    if zeilen != ["Deutsch, Italienisch – Muttersprache", "Englisch – Business Niveau"]:
        fehler.append(f"Skillset: zusammengefasste Sprachzeile falsch behandelt — {zeilen}")

    # Eine leere Gruppe faellt weg und wird gemeldet.
    spalten, hinweise = skillset_gruppen({"skillset": {"faehigkeiten": ["X"], "tools": ["T"]}})
    if [g["titel"] for g in spalten["links"]] != ["Fähigkeiten"] or \
            not any("Branchen ist leer" in h for h in hinweise):
        fehler.append("Skillset: leere Gruppe Branchen nicht gemeldet")
    return fehler


def pruefe_silhouette(tmp):
    """Ist das Platzhalterbild der anonymen Fassung das aus dem Design?

    Das Bild kommt als Datei aus dem Design (assets/silhouette-vorlage.svg,
    Vorgabe vom 29.09.2026); scripts/silhouette.py setzt es in den Fotoplatz
    ein und schreibt silhouette.svg und .png. Geprueft wird, dass beide genau
    das sind, was das Skript heute aus Vorlage und tokens.json machen wuerde —
    eine neue Vorlage oder ein neues Fotomass ohne Skriptlauf faellt so auf,
    ebenso eine von Hand geaenderte Datei. Vorher stand hier eine selbst
    gezeichnete Silhouette mit Kreis-Kopf; genau die darf nicht zurueckkommen.
    """
    sys.path.insert(0, str(WURZEL / "scripts"))
    import silhouette
    import tokens
    r = tokens.laden()["raster"]
    svg = WURZEL / "assets" / "silhouette.svg"
    try:
        soll = silhouette.svg_bauen(r["foto_breite"], r["foto_hoehe"])
    except Exception as fehler:                       # fehlende oder kaputte Vorlage
        return [f"Silhouette: Vorlage nicht verwendbar — {fehler}"]
    if not svg.exists() or svg.read_text(encoding="utf-8") != soll:
        return ["Silhouette: silhouette.svg ist nicht das eingesetzte Bild aus "
                "silhouette-vorlage.svg — python3 scripts/silhouette.py schreibt es neu"]
    png = WURZEL / "assets" / "silhouette.png"
    if not png.exists():
        return ["Silhouette: silhouette.png fehlt — --foto-raster liefe ins Leere"]
    try:
        from PIL import Image, ImageChops, ImageStat
        frisch = Path(tmp) / "silhouette-frisch.png"
        silhouette.png_bauen(svg, r["foto_breite"], r["foto_hoehe"], frisch)
    except Exception:
        return []                    # ohne Pillow/pypdfium2/pdftoppm nicht pruefbar
    alt, neu = Image.open(png).convert("RGB"), Image.open(frisch).convert("RGB")
    if alt.size != neu.size or max(ImageStat.Stat(ImageChops.difference(alt, neu)).mean) > 1:
        return ["Silhouette: silhouette.png zeigt nicht dasselbe wie silhouette.svg — "
                "python3 scripts/silhouette.py schreibt beide neu"]
    return []


# So heissen die Schnitte in Figma. Die Schreibweise ist nicht einheitlich:
# Inter fuehrt "Semi Bold" mit Leerzeichen, Rethink Sans "SemiBold" ohne. Falsch
# geschrieben wirft loadFontAsync, und damit faellt jeder Textknoten des Frames
# aus. Der Massstab steht deshalb hier und wird nicht aus dem Bauplan gelesen:
# ein Test, der seine Sollwerte vom Pruefling bezieht, prueft nichts.
FIGMA_SCHNITTE = {("Inter", "Regular"), ("Inter", "Bold"), ("Rethink Sans", "SemiBold")}


# Der Figma-Frame wird nicht hier gebaut — das braucht eine angemeldete
# Anbindung und eine fremde Datei. Geprueft wird der Bauplan: Er ist das, was
# schiefgehen kann, ohne dass es jemandem auffaellt.
def pruefe_figma_plan(pdf, stufen, tmp):
    """Stimmt der Bauplan mit dem gerenderten PDF ueberein?"""
    from pypdf import PdfReader
    fehler = []
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "figma_plan.py"),
         str(WURZEL / "beispiel" / "cv.json"), str(pdf), str(tmp),
         "--stufen", str(stufen)],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if lauf.returncode != 0:
        return [f"figma_plan.py fehlgeschlagen: {(lauf.stderr or lauf.stdout).strip()}"]

    plan = json.loads((Path(tmp) / "figma_plan.json").read_text(encoding="utf-8"))
    norm = lambda t: " ".join((t or "").split())
    seiten = [norm(s.extract_text()) for s in PdfReader(str(pdf)).pages]

    if len(plan["frames"]) != len(seiten):
        fehler.append(f"{len(plan['frames'])} Frames, aber {len(seiten)} PDF-Seiten")

    im_plan = {(familie, schnitt) for familie, schnitte in plan["schrift"].items()
               if isinstance(schnitte, list) for schnitt in schnitte}
    if im_plan != FIGMA_SCHNITTE:
        fehler.append(f"Schnittliste im Plan: {sorted(im_plan)} statt {sorted(FIGMA_SCHNITTE)}")

    # Jeder Textstil im Plan muss einer aus tokens.json sein — Wert fuer Wert.
    # Sonst setzt der Frame eine Groesse, Zeilenhoehe oder Farbe, die das PDF
    # nicht hat, und die beiden Fassungen laufen auseinander, ohne dass es
    # jemand merkt.
    sys.path.insert(0, str(WURZEL / "scripts"))
    import tokens
    soll = {_stilwerte(tokens.stil(n)) for n in tokens.laden()["text"]}
    arten = []
    for frame in plan["frames"]:
        for b in frame["bloecke"]:
            arten.append((frame["nr"], b["art"]))
            # Jeder Block muss dort stehen, wo sein Text im PDF steht. Sonst
            # weicht der Frame genau da vom Dokument ab, wo es keiner nachprueft.
            marke = _marke(b)
            if marke and marke[:60] not in seiten[frame["nr"] - 1]:
                fehler.append(f'Frame {frame["nr"]}: "{marke[:40]}" steht dort nicht im PDF')
            for stil in _stile(b):
                if (stil.get("familie"), stil["schnitt"]) not in FIGMA_SCHNITTE:
                    fehler.append(f"Unbekannter Schriftschnitt: {stil.get('familie')} "
                                  f"{stil['schnitt']!r}")
                elif _stilwerte(stil) not in soll:
                    fehler.append(f"Frame {frame['nr']}, {b['art']}: Textstil nicht aus "
                                  f"tokens.json — {_stilwerte(stil)}")
            for logo in _logos(b):
                if not Path(logo["datei"]).exists():
                    fehler.append(f"Logodatei fehlt: {logo['datei']}")
            # Das Skillset im Plan hat dieselben vier Gruppen 2 x 2 wie das PDF.
            if b["art"] == "skillset":
                titel = [[g["titel"]["text"] for g in spalte] for spalte in b["spalten"]]
                if titel != SKILLSET_SOLL["de"]:
                    fehler.append(f"Frame {frame['nr']}: Skillset-Gruppen {titel} statt "
                                  f"{SKILLSET_SOLL['de']}")
            # Projektlogos stehen nebeneinander wie im PDF. Fehlt die Angabe,
            # baut der Frame sie untereinander, und er laeuft dem PDF davon.
            if b["art"] == "projekt" and (b.get("logos") or {}).get("richtung") != "nebeneinander":
                fehler.append(f"Frame {frame['nr']}: Projektlogos ohne richtung "
                              "'nebeneinander' im Plan")

    if arten[0] != (1, "kopfzeile"):
        fehler.append("Die Kopfzeile steht nicht als erster Block auf Frame 1")
    if arten[-1] != (len(seiten), "footer"):
        fehler.append("Der Footer steht nicht als letzter Block auf dem letzten Frame")
    return fehler


def _marke(b):
    """Der Text, an dem sich ein Block im PDF wiederfinden laesst."""
    for schluessel in ("titel", "kunde", "name"):
        if isinstance(b.get(schluessel), dict):
            return b[schluessel]["text"]
    if isinstance(b.get("text"), str):
        return b["text"]
    eintraege = b.get("eintraege")
    if isinstance(eintraege, list) and eintraege and isinstance(eintraege[0], str):
        return eintraege[0]
    return None


def _stile(wert):
    """Alle Textstile, die irgendwo in einem Block stecken."""
    if isinstance(wert, dict):
        if isinstance(wert.get("schnitt"), str):
            yield wert
        for v in wert.values():
            yield from _stile(v)
    elif isinstance(wert, list):
        for v in wert:
            yield from _stile(v)


def _stilwerte(s):
    """Ein Textstil als vergleichbares Tupel — aus tokens.json wie aus dem Plan."""
    return (s.get("familie") or s.get("schrift"), s.get("schnitt") or s.get("figma_schnitt"),
            float(s["groesse"]), float(s["zeile"]), float(s["laufweite"]),
            (s.get("farbe_hex") or s.get("farbe")).upper(), bool(s.get("versalien")))


# --- Design: Schriften, Farben, Abstaende --------------------------------------

def _schriftname(name):
    """Schriftname ohne Subset-Praefix und Schreibvarianten: WeasyPrint bettet
    Inter-Regular als "Inter" und Inter-SemiBold als "Inter-Semi-Bold" ein."""
    kern = str(name).split("+")[-1].lower()
    return re.sub(r"[^a-z]", "", kern).replace("regular", "")


def _laeufe(pdf):
    """Jede Textzeile im PDF mit Schrift, Groesse, Farbe und Lage in pt.

    y ist die Schriftlinie, gemessen von der Blattoberkante, x der
    Zeilenanfang von links — dieselben Koordinaten wie im Figma-Frame.
    """
    from pypdf import PdfReader
    laeufe = []
    for nummer, seite in enumerate(PdfReader(str(pdf)).pages, start=1):
        hoehe = float(seite.mediabox.height)
        farbe = ["#000000"]

        def vorher(op, args, cm, tm):
            if op == b"rg" and len(args) == 3:
                farbe[0] = "#" + "".join(f"{round(float(a) * 255):02X}" for a in args)
            elif op == b"g" and len(args) == 1:
                farbe[0] = "#" + f"{round(float(args[0]) * 255):02X}" * 3

        def text(inhalt, cm, tm, schrift, groesse):
            if not inhalt.strip() or not schrift:
                return
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            laeufe.append({
                "seite": nummer, "text": " ".join(inhalt.split()),
                "schrift": str(schrift.get("/BaseFont", "")),
                "groesse": round(abs(groesse * tm[3] * cm[3]), 2), "farbe": farbe[0],
                "y": round(hoehe - y, 2), "x": round(tm[4] * cm[0] + cm[4], 2)})

        seite.extract_text(visitor_operand_before=vorher, visitor_text=text)
    return laeufe


def _css_literale():
    """Zahlen mit Einheit und Farben, die als Literal in cv.css stehen.

    cv.css ist ein Jinja-Template; jeder Designwert kommt dort aus tokens.json.
    Steht einer als Literal da, laeuft er beim naechsten Design-Update nicht mit
    — genau so war der alte Stand entstanden. Erlaubt sind nur 0 und die
    Strukturwerte, die keine Gestaltung sind (flex: 1 0 0, 100%).
    """
    css = (WURZEL / "assets" / "cv.css").read_text(encoding="utf-8")
    css = re.sub(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", " ", css, flags=re.S)
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    css = re.sub(r":nth-child\([^)]*\)", "", css)      # Selektor, kein Designwert
    css = css.replace("flex: 1 0 0", "").replace("100%", "")
    funde = re.findall(r"#[0-9A-Fa-f]{3,8}\b|(?<![\w.-])\d*\.?\d+(?:pt|px|mm|cm|em|rem|%)?\b", css)
    return sorted({f for f in funde if f != "0"})


def _schatten_und_rundungen():
    """Weder Figma noch der Skill setzen Schatten, Rundungen oder Filter."""
    css = (WURZEL / "assets" / "cv.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    return sorted(set(re.findall(r"box-shadow|text-shadow|drop-shadow|border-radius|filter\s*:|opacity\s*:", css)))


def pruefe_design(pdf, stufen):
    """Setzt das PDF dieselben Schriften, Farben und Abstaende wie Figma?

    Die Sollwerte stehen in assets/tokens.json, abgelesen aus der Figma-Datei,
    die dort unter "quelle" steht — nicht hier und nicht im Pruefling. Geprueft
    wird dreierlei:
      - cv.css traegt keine eigenen Werte, nur solche aus tokens.json;
      - jede Textzeile im PDF hat Schrift, Groesse und Farbe eines Tokenstils;
      - die Abstaende stimmen, gemessen von Schriftlinie zu Schriftlinie.
    """
    sys.path.insert(0, str(WURZEL / "scripts"))
    import tokens
    t = tokens.laden()
    fehler = []

    literale = _css_literale()
    if literale:
        fehler.append("Design: Werte stehen als Literal in cv.css statt in tokens.json — "
                      + ", ".join(literale[:12]))
    verboten = _schatten_und_rundungen()
    if verboten:
        fehler.append("Design: cv.css setzt " + ", ".join(verboten)
                      + " — die Figma-Vorlage hat weder Schatten noch Rundungen")
    # Die Notstufen sollen enger setzen, nie weiter: Wird ein normal-Wert aus
    # Figma kleiner, muessen kompakt und eng mitziehen, sonst setzt die Stufe,
    # die Platz schaffen soll, mehr Abstand als der Normalsatz.
    for bereich, werte in t["verdichtung"].items():
        if not isinstance(werte, dict) or "normal" not in werte:
            continue
        for schluessel in werte["normal"]:
            n, k, e = (werte[s][schluessel] for s in ("normal", "kompakt", "eng"))
            if not n >= k >= e:
                fehler.append(f"tokens.json: verdichtung.{bereich}.{schluessel} wird nicht "
                              f"enger ({n} / {k} / {e}) — kompakt und eng muessen "
                              "hoechstens so gross sein wie die Stufe davor")

    laeufe = _laeufe(pdf)
    if not laeufe:
        return fehler + ["Design: kein Text im PDF gefunden"]

    # Schriften, Groessen, Farben: jede Zeile gegen die Stile aus tokens.json.
    erlaubt = {(_schriftname(tokens.postscript(n)), round(tokens.stil(n)["groesse"], 1),
                tokens.stil(n)["farbe_hex"].upper()) for n in t["text"]}
    fremd = {}
    for l in laeufe:
        schluessel = (_schriftname(l["schrift"]), round(l["groesse"], 1), l["farbe"])
        if schluessel not in erlaubt:
            fremd.setdefault(schluessel, l["text"][:30])
    for (schrift, groesse, farbe), beispiel in sorted(fremd.items())[:8]:
        fehler.append(f"Design: {schrift or '?'} {groesse}pt {farbe} ist kein Stil aus "
                      f"tokens.json (\"{beispiel}\")")
    eingebettet = {_schriftname(l["schrift"]) for l in laeufe}
    if _schriftname(tokens.postscript("name")) not in eingebettet:
        fehler.append(f"Design: {t['text']['name']['schrift']} ist nicht eingebettet — "
                      "der Name steht in einer Ersatzschrift")

    # Abstaende: von Schriftlinie zu Schriftlinie, so wie Figma sie setzt. Die
    # Stufen braucht es, weil render_cv.py Seite 1 enger setzen darf.
    stufe = json.loads(Path(stufen).read_text(encoding="utf-8"))
    d = t["verdichtung"]["deckblatt"][stufe.get("deckblatt", "normal")]
    s = t["verdichtung"]["stationen"][stufe.get("stationen", "normal")]
    a, r, ab = t["abstand"], t["raster"], t["abgeleitet"]
    gl = tokens.grundlinie

    def unter(stil):
        return tokens.stil(stil)["zeile"] - gl(stil)

    def zeile(marke, nach=None):
        """Erste Zeile, die mit marke beginnt — mit nach: die naechste darunter
        auf derselben Seite. Eintraege wie "UI-Design" stehen oft zweimal im
        Dokument, in der Bildung und im Skillset."""
        for l in laeufe:
            if not l["text"].startswith(marke):
                continue
            if nach is None or (l["seite"] == nach["seite"] and l["y"] > nach["y"]):
                return l
        return None

    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    # Die DATEV-Station: kurzer Titel, der sicher nicht umbricht — sonst misst
    # die Probe eine zweite Titelzeile mit.
    person, station = daten["person"], daten["stationen"][2]
    projekt = daten["stationen"][0]["projekte"][0]
    from render_cv import skillset_gruppen
    spalten = skillset_gruppen(daten)[0]
    gruppe = spalten["links"][0]
    kontakt_label = "ANSPRECHPARTNER"
    proben = [
        # (von, bis zur naechsten Zeile darunter, Soll von Schriftlinie zu Schriftlinie)
        (person["name"], person["rolle"], unter("name") + a["name_rolle"] + gl("rolle")),
        (person["rolle"], person["erfahrung"], tokens.stil("rolle")["zeile"] + a["rolle_erfahrung"]),
        ("Bildung", daten["bildung"][0]["abschluss"], unter("rubrik") + d["rubrik_inhalt"] + gl("abschluss")),
        (gruppe["titel"], gruppe["eintraege"][0], unter("gruppe") + d["gruppe_liste"] + gl("liste")),
        ("Kurzprofil", person["kurzprofil"][:20], unter("rubrik") + s["profil_rubrik"] + gl("profil")),
        (station["titel"], station["firma"], unter("titel") + a["titel_firma"] + gl("firma")),
        (station["firma"], station["zeitraum"], unter("firma") + a["firma_zeitraum"] + gl("zeitraum")),
        (station["zeitraum"], station["aufgaben"][0][:20], unter("zeitraum") + s["kopf_aufgaben"] + gl("aufgabe")),
        (projekt["kunde"], projekt["zeitraum"], unter("kunde") + a["kunde_zeitraum"] + gl("zeitraum")),
        (kontakt_label, "Manuel Klein", unter("fuss_label") + a["fuss_label_wert"] + gl("fuss_name")),
    ]
    # Der Listentakt im Skillset: Eintrag unter Eintrag, gemessen ab dem
    # Gruppentitel — nicht ab dem ersten Treffer, der kann in der Bildung stehen.
    titel_zeile = zeile(gruppe["titel"])
    erster = zeile(gruppe["eintraege"][0], nach=titel_zeile) if titel_zeile else None
    if erster:
        proben.append((erster, gruppe["eintraege"][1], tokens.stil("liste")["zeile"]))
    for von, nach, soll in proben:
        erste = von if isinstance(von, dict) else zeile(von)
        von = erste["text"] if isinstance(von, dict) else von
        zweite = zeile(nach, nach=erste) if erste else None
        if not (erste and zweite):
            fehler.append(f"Design: Abstand {von[:25]!r} -> {nach[:25]!r} nicht messbar")
            continue
        ist = zweite["y"] - erste["y"]
        if abs(ist - soll) > 0.3:
            fehler.append(f"Design: {von[:25]!r} -> {nach[:25]!r} steht {ist:.1f}pt "
                          f"statt {soll:.1f}pt")

    # Lagen, die an keiner anderen Zeile haengen: der Name unter dem Kopflogo,
    # das Kurzprofil oben auf seiner Seite, die rechte Skillset-Spalte und der
    # Footer an der rechten Kante des Satzspiegels.
    seite_t = t["seite"]
    kopf = seite_t["rand_oben"] + r["kopflogo_hoehe"] + a["kopf_intro"]
    rechts = spalten["rechts"][0]["titel"]
    lagen = [
        (person["name"], "y", kopf + gl("name")),
        ("Kurzprofil", "y", seite_t["rand_oben"] + gl("rubrik")),
        (rechts, "x", seite_t["rand_links"] + ab["halbe_spalte"] + r["spaltenabstand"]),
        (station["titel"], "x", seite_t["rand_links"] + ab["einzug"]),
        (kontakt_label, "x", seite_t["rand_links"] + r["fuss_breite"] - r["fuss_block"]),
    ]
    for marke, achse, soll in lagen:
        l = zeile(marke)
        if not l:
            fehler.append(f"Design: {marke!r} nicht gefunden")
        elif abs(l[achse] - soll) > 0.3:
            fehler.append(f"Design: {marke!r} steht bei {achse} = {l[achse]:.1f}pt "
                          f"statt {soll:.1f}pt")

    # Aufgaben laufen ohne Zwischenraum: jede Zeile genau eine Zeilenhoehe tiefer.
    erste = zeile(station["aufgaben"][0][:20])
    if erste:
        grau = sorted({l["y"] for l in laeufe
                       if l["seite"] == erste["seite"] and l["farbe"] == t["farben"]["grau"].upper()
                       and l["y"] >= erste["y"]})
        schritte = {round(b - a_, 1) for a_, b in zip(grau, grau[1:]) if b - a_ < 30}
        takt = float(tokens.stil("aufgabe")["zeile"])
        if schritte and min(schritte) and abs(min(schritte) - takt) > 0.3:
            fehler.append(f"Design: Aufgabenzeilen stehen {min(schritte)}pt auseinander "
                          f"statt {takt}pt")
    return fehler


def _logos(b):
    if isinstance(b.get("logo"), dict):
        yield b["logo"]
    for l in (b.get("rail") or {}).get("logos") or []:
        yield l
    for l in (b.get("logos") or {}).get("eintraege") or []:
        yield l


# Der Sollwert steht hier und wird nicht aus dem Ergebnis gelesen: aus "Florian
# Feiler" muss "F. F." werden. Traegt das Beispiel spaeter einen anderen Namen,
# faellt diese Pruefung auf und die beiden Werte werden nachgezogen — das ist
# der Sinn der Sache und keine Panne.
ANONYM_NAME = "Florian Feiler"
ANONYM_KUERZEL = "F. F."


def _fuellfarben(svg):
    """Die fill-Farben eines SVG als (r, g, b) im Bereich 0..1."""
    return {tuple(int(wert[i:i + 2], 16) / 255 for i in (0, 2, 4))
            for wert in re.findall(r'fill\s*[=:]\s*"?#([0-9A-Fa-f]{6})', svg)}


def _malfarben(seite):
    """Jede Fuellfarbe, die im Zeichenstrom einer PDF-Seite gesetzt wird."""
    inhalt = seite.get_contents()
    if inhalt is None:
        return set()
    strom = inhalt.get_data().decode("latin-1")
    return {tuple(float(w) for w in gruppe)
            for gruppe in re.findall(r"([\d.]+) ([\d.]+) ([\d.]+) rg", strom)}


def _fehlen(farben, gemalt):
    """Welche der Farben auf der Seite nicht vorkommen — auf 1/1000 genau."""
    return [f for f in farben
            if not any(max(abs(a - b) for a, b in zip(f, g)) < 0.001 for g in gemalt)]


def _anonymisiere(tmp, daten, name, *schalter):
    """anonymisieren.py ueber eine erfundene cv.json laufen lassen."""
    daten = json.loads(json.dumps(daten))
    daten["person"]["name"] = name
    marke = re.sub(r"\W+", "-", name).strip("-").lower()
    quelle = Path(tmp) / f"kante-{marke}.json"
    ziel = Path(tmp) / f"kante-{marke}-anonym.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "anonymisieren.py"),
         str(quelle), str(ziel), *schalter],
        capture_output=True, text=True, cwd=str(WURZEL))
    if not ziel.exists():
        return None, lauf
    return json.loads(ziel.read_text(encoding="utf-8")), lauf


def pruefe_anonym_kanten(tmp):
    """Die Faelle, in denen die Namensersetzung zu viel oder zu wenig tut.

    Sie zerschiesst Saetze, wenn sie einen einzelnen Namensteil blind ersetzt:
    Wer "Mai" heisst, hat sonst kein "Im Mai 2024" mehr im Lebenslauf, und wer
    bei der "Feiler GmbH" war, keine Firma. Und sie laesst den Klarnamen stehen,
    wenn sie nur den Fliesstext ansieht: Bei Selbstaendigen steht der Name in
    firma und in rolle — und render_cv.py baut den Dateinamen aus beidem.

    Beide Richtungen sind einmal danebengegangen, deshalb stehen sie hier.
    """
    basis = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    basis["person"]["kurzprofil"] = (
        "Im Mai 2024 uebernahm ich die Leitung. Bei der Feiler GmbH lag der "
        "Schwerpunkt auf Migration.")
    basis["stationen"] = basis["stationen"] + [{
        "titel": "Entwickler", "firma": "Feiler GmbH",
        "zeitraum": "Januar 2018 - Mai 2020", "aufgaben": ["Frontend"]}]
    fehler = []

    # Zu viel: ein Vorname, der auch ein Monat ist, und ein Nachname, der auch
    # im Arbeitgeber steht. Beide muessen im Satz stehen bleiben.
    for name, wort in (("Mai Nguyen", "Mai 2024"), ("Timo Feiler", "Feiler GmbH")):
        daten, lauf = _anonymisiere(tmp, basis, name)
        if daten is None:
            fehler.append(f"Anonym: {name} brach ab — {lauf.stderr.strip()[:120]}")
            continue
        if wort not in daten["person"]["kurzprofil"]:
            fehler.append(f'Anonym: "{wort}" wurde bei {name} aus dem Satz '
                          f'ersetzt: {daten["person"]["kurzprofil"]}')
        if "Pruefen" not in lauf.stderr:
            fehler.append(f"Anonym: {name} liess den mehrdeutigen Namensteil "
                          "unerwaehnt — der Nutzer muss davon erfahren.")

    # Zu wenig: der Name steht in firma und rolle. Beides geht sonst ins PDF,
    # der Rollenteil sogar in den Dateinamen.
    selbst = json.loads(json.dumps(basis))
    selbst["person"]["rolle"] = "UX Designer – Timo Muster"
    selbst["stationen"].append({"titel": "Inhaber", "firma": "Timo Muster Freelance",
                                "zeitraum": "2019 - 2021", "aufgaben": ["Beratung"]})
    daten, lauf = _anonymisiere(tmp, selbst, "Timo Muster")
    if daten is None:
        fehler.append(f"Anonym: Selbstaendigen-Fall brach ab — {lauf.stderr.strip()[:120]}")
    else:
        uebrig = [pfad for pfad, wert in (
            ("person.rolle", daten["person"]["rolle"]),
            ("firma", daten["stationen"][-1]["firma"]))
            if "Timo Muster" in wert]
        if uebrig:
            fehler.append("Anonym: der volle Name steht noch in "
                          + ", ".join(uebrig))

    # Ein Zeitraum ohne Monat ist eine Aussage und kein Datum: aus "Seit 2019"
    # darf --jahre kein "2019" machen.
    offen = json.loads(json.dumps(basis))
    offen["stationen"][-1]["zeitraum"] = "Seit 2019"
    daten, lauf = _anonymisiere(tmp, offen, "Timo Muster", "--jahre")
    if daten is None:
        fehler.append(f"Anonym: --jahre brach ab — {lauf.stderr.strip()[:120]}")
    elif daten["stationen"][-1]["zeitraum"] != "Seit 2019":
        fehler.append("Anonym: --jahre machte aus \"Seit 2019\" ein "
                      f"\"{daten['stationen'][-1]['zeitraum']}\"")
    return fehler


def pruefe_anonym(pdf, tmp):
    """Ist an der anonymen Fassung wirklich nichts mehr vom Namen abzulesen?

    Anonymisiert wird auf den Daten, nicht im Renderer. Geprueft wird trotzdem
    am fertigen PDF: Dateiname, Metadatentitel und Frame-Namen sind alle drei
    aus person.name abgeleitet, und ein Leck faellt genau dort auf, wo in der
    JSON nichts zu sehen ist.

    Das Beispiel bekommt vorher Verweise und zwei Namensnennungen im
    Fliesstext, weil es beides nicht mitbringt: ohne Link gaebe es keine
    Annotation zu entfernen, ohne Nennung im Satz bliebe die einzige Stelle
    ungeprueft, an der das Skript fremden Text umschreibt.

    pdf ist das normale Beispiel-PDF und dient als Gegenprobe zur Silhouette.
    """
    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    if daten["person"]["name"] != ANONYM_NAME:
        return [f"Anonym: das Beispiel heisst jetzt {daten['person']['name']!r} — "
                "ANONYM_NAME und ANONYM_KUERZEL im Selbsttest nachziehen"]
    vorname, nachname = ANONYM_NAME.split()

    daten["person"]["links"] = [
        {"titel": "LinkedIn", "url": "https://www.linkedin.com/in/florian-feiler"},
        {"titel": "Portfolio", "url": "https://florian-feiler.de"},
    ]
    daten["person"]["kurzprofil"] = (f"{ANONYM_NAME} leitet Workshops. "
                                     + daten["person"]["kurzprofil"])
    daten["stationen"][0]["projekte"][0]["aufgaben"].append(f"Abstimmung mit {nachname}")

    quelle = Path(tmp) / "anonym-quelle.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    anonym = Path(tmp) / "cv-anonym.json"
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "anonymisieren.py"),
         str(quelle), str(anonym)],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if lauf.returncode != 0 or not anonym.exists():
        return [f"anonymisieren.py fehlgeschlagen: {(lauf.stderr or lauf.stdout).strip()}"]

    # Ohne --pfad-genau gerendert, und in einen Ordner statt auf eine Datei:
    # der Dateiname ist selbst Teil der Pruefung, und den baut render_cv.py aus
    # person.name — vorgegeben waere er kein Befund mehr.
    ordner = Path(tmp) / "anonym"
    stufen = Path(tmp) / "anonym-stufen.json"
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"),
         str(anonym), str(ordner), "--stufen-json", str(stufen)],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    gerendert = sorted(ordner.glob("*.pdf")) if ordner.exists() else []
    if not gerendert:
        return [f"Anonymes PDF nicht gerendert: {(lauf.stderr or lauf.stdout).strip()}"]
    anonym_pdf = gerendert[0]

    from pypdf import PdfReader
    leser = PdfReader(str(anonym_pdf))
    fehler = []

    text = " ".join(" ".join((s.extract_text() or "").split()) for s in leser.pages)
    for verboten in (ANONYM_NAME, vorname, nachname):
        if verboten.lower() in text.lower():
            fehler.append(f"Anonym: {verboten!r} steht noch im auslesbaren Text")
    if ANONYM_KUERZEL not in text:
        fehler.append(f"Anonym: {ANONYM_KUERZEL!r} steht nirgends im PDF — der "
                      "Lebenslauf gehoert dann niemandem mehr")

    # Mit person.links faellt der sichtbare Verweis weg — die Adresse dahinter
    # aber steht im Klartext in der Annotation, und "in/florian-feiler" benennt
    # die Person so genau wie der Name selbst. pruefe_verweise liest dieselbe
    # Stelle am normalen PDF aus, dort muessen die Adressen stehen.
    adressen = [a.get_object().get("/A", {}).get("/URI")
                for s in leser.pages for a in (s.get("/Annots") or [])]
    offen = [a for a in adressen if a]
    if offen:
        fehler.append(f"Anonym: Verweis noch im PDF — {offen[0]}")

    titel = str((leser.metadata or {}).get("/Title") or "")
    if any(t.lower() in titel.lower() for t in (vorname, nachname)):
        fehler.append(f"Anonym: der PDF-Titel traegt den Namen — {titel!r}")
    elif ANONYM_KUERZEL not in titel:
        fehler.append(f"Anonym: der PDF-Titel traegt die Initialen nicht — {titel!r}")

    if any(t.lower() in anonym_pdf.name.lower() for t in (vorname, nachname)):
        fehler.append(f"Anonym: der Dateiname traegt den Namen — {anonym_pdf.name}")
    elif ANONYM_KUERZEL not in anonym_pdf.name:
        fehler.append(f"Anonym: der Dateiname traegt die Initialen nicht — {anonym_pdf.name}")

    # WeasyPrint bettet ein SVG als Vektorzeichnung ein und nicht als
    # Bildobjekt: unter /XObject stehen nur die Logos, ueber die Bildzahl ist
    # die Silhouette nicht nachzuweisen. Nachgewiesen wird sie an ihren
    # Fuellfarben. Das ist keine Spitzfindigkeit — ein SVG, das sich nicht
    # parsen laesst, laesst WeasyPrint kommentarlos weg, und die Fotospalte
    # bleibt leer, ohne dass irgendwo eine Meldung steht.
    silhouette = _fuellfarben(
        (WURZEL / "assets" / "silhouette.svg").read_text(encoding="utf-8"))
    if not silhouette:
        fehler.append("Anonym: silhouette.svg nennt keine fill-Farbe — so ist "
                      "nicht mehr nachzuweisen, dass sie im PDF ankommt")
    elif _fehlen(silhouette, _malfarben(leser.pages[0])):
        fehler.append("Anonym: die Silhouette steht nicht auf Seite 1 — die "
                      "Fotospalte ist leer geblieben")
    # Gegenprobe: Waeren ihre Farben auch ohne sie da, pruefte die Zeile darueber
    # nur noch, dass das Dokument bunt ist.
    elif not _fehlen(silhouette, _malfarben(PdfReader(str(pdf)).pages[0])):
        fehler.append("Anonym: die Silhouettenfarben stehen auch im normalen "
                      "PDF — der Nachweis unterscheidet nichts mehr")

    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "figma_plan.py"),
         str(anonym), str(anonym_pdf), str(Path(tmp) / "anonym-figma"),
         "--stufen", str(stufen)],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if lauf.returncode != 0:
        fehler.append("Anonym: figma_plan.py fehlgeschlagen: "
                      f"{(lauf.stderr or lauf.stdout).strip()}")
        return fehler

    plan = json.loads((Path(tmp) / "anonym-figma" / "figma_plan.json")
                      .read_text(encoding="utf-8"))
    for frame in plan["frames"]:
        if any(t.lower() in frame["name"].lower() for t in (vorname, nachname)):
            fehler.append(f"Anonym: Frame-Name traegt den Namen — {frame['name']}")
    if ANONYM_KUERZEL not in plan["person"]["name"]:
        fehler.append(f"Anonym: der Plan fuehrt {plan['person']['name']!r} "
                      f"statt {ANONYM_KUERZEL!r}")

    # In Figma fuehren SVG und Rasterbild zu verschiedenen Wegen — Markup im
    # Code gegen Upload aufs Rechteck. Steht hier der falsche Typ, baut der
    # Agent die Silhouette als Bild und bekommt ein leeres Rechteck.
    fotos = [b["foto"] for f in plan["frames"] for b in f["bloecke"] if b.get("foto")]
    if not fotos:
        fehler.append("Anonym: der Figma-Plan fuehrt kein Foto — im Frame bliebe "
                      "die Fotospalte leer")
    elif fotos[0].get("typ") != "svg":
        fehler.append(f"Anonym: foto.typ ist {fotos[0].get('typ')!r} statt 'svg'")
    elif not Path(fotos[0]["datei"]).exists():
        fehler.append(f"Anonym: Silhouettendatei fehlt: {fotos[0]['datei']}")
    return fehler


def main():
    beispiel = WURZEL / "beispiel" / "cv.json"
    if not beispiel.exists():
        raise SystemExit(f"Beispieldaten fehlen: {beispiel}")

    with tempfile.TemporaryDirectory() as tmp:
        ziel = Path(tmp) / "selbsttest.pdf"
        stufen = Path(tmp) / "stufen.json"
        lauf = subprocess.run(
            [sys.executable, str(WURZEL / "scripts" / "render_cv.py"),
             str(beispiel), str(ziel), "--pfad-genau",
             "--stufen-json", str(stufen)],
            capture_output=True, text=True, cwd=str(WURZEL),
        )
        if lauf.returncode != 0 or not ziel.exists():
            print("Rendern fehlgeschlagen:\n" + (lauf.stderr or lauf.stdout))
            print("\npython3 scripts/pruefe_umgebung.py zeigt, was fehlt.")
            raise SystemExit(1)

        print(lauf.stdout.strip())
        seiten, breite, hoehe, schriften, bilder, fehler = pruefe(ziel)
        fehler += pruefe_gleicher_titel(tmp)
        fehler += pruefe_verweise(tmp)
        fehler += pruefe_stationsumbruch(tmp)
        fehler += pruefe_projektlogos(tmp)
        fehler += pruefe_design(ziel, stufen)
        fehler += pruefe_figma_plan(ziel, stufen, tmp)
        fehler += pruefe_anonym(ziel, tmp)
        fehler += pruefe_anonym_kanten(tmp)
        fehler += pruefe_silhouette(tmp)
        fehler += pruefe_skillset(tmp)

    fehler += pruefe_linkedin_auswahl()
    fehler += pruefe_website_auswahl()

    print(f"\n  Seiten:    {seiten}")
    print(f"  Format:    {breite} x {hoehe} pt")
    print(f"  Schriften: {schriften} eingebettet")
    print(f"  Bilder:    {bilder} (Logos und Foto)")
    print(f"  LinkedIn:  Fotoauswahl geprueft (ohne Netz)")
    print(f"  Website:   Bilderfilter geprueft (ohne Netz)")
    print(f"  Ueberlauf: erkannt, auch wenn Rolle = Stationstitel")
    print(f"  Verweise:  benannt unter der Erfahrungszeile und anklickbar")
    print(f"  Umbruch:   keine Station mit einem einzelnen Stichpunkt am Seitenende")
    print(f"  Projekte:  mehrere Logos nebeneinander, gleich gross, auf der Mitte")
    print(f"  Design:    Schriften, Farben und Abstaende wie in tokens.json (Figma)")
    print(f"  Figma:     Bauplan deckt sich mit dem PDF (Seiten, Logos, Stile)")
    print(f"  Anonym:    kein Name in Text, Titel, Dateiname und Frames, Silhouette da")
    print(f"  Platzhalter: Bild aus dem Design, eingesetzt in den Fotoplatz, SVG und PNG")
    print(f"  Skillset:  immer Faehigkeiten, Branchen, Tools, Sprachen - 2 x 2, Sprachvorgabe")
    print(f"  Kanten:    Monatsnamen und Firmen bleiben heil, firma/rolle werden mitgezogen")

    if fehler:
        print("\nProbleme:")
        for f in fehler:
            print(f"  - {f}")
        raise SystemExit(1)

    print("\nSelbsttest bestanden. Der Skill ist einsatzbereit.")


if __name__ == "__main__":
    main()
