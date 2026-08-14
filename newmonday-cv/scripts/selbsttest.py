#!/usr/bin/env python3
"""Prueft nach der Installation, ob die ganze Kette laeuft.

    python3 scripts/selbsttest.py

Rendert den mitgelieferten Beispiel-Lebenslauf in ein temporaeres Verzeichnis
und kontrolliert das Ergebnis: Seitenzahl, A4-Format, eingebettete Schriften,
Logos und Foto. Schreibt nichts in den Skill-Ordner.
"""
import json
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
    daten["skillset"]["links"] = [
        {"titel": f"Gruppe {i}", "eintraege": [f"Eintrag {i}.{j}" for j in range(8)]}
        for i in range(4)
    ]
    quelle = Path(tmp) / "gleicher-titel.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    ziel = Path(tmp) / "gleicher-titel.pdf"
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel)],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if "passen nicht" not in lauf.stderr:
        return ["Ueberlauf nicht erkannt, wenn Rolle und Stationstitel gleich sind"]
    return []


def pruefe_verweise(tmp):
    """Stehen LinkedIn und Portfolio oben in der Kopfzeile — und anklickbar?

    Sie standen frueher als Fusszeile unter Seite 1. Geprueft wird beides, was
    beim Umzug schiefgehen kann: die Hoehe auf der Seite (sie muessen neben dem
    Logo stehen, nicht darunter) und die Link-Annotation im PDF (ohne sie ist
    der Unterstrich eine Behauptung).
    """
    daten = json.loads((WURZEL / "beispiel" / "cv.json").read_text(encoding="utf-8"))
    daten["person"]["links"] = [
        {"titel": "LinkedIn", "url": "https://www.linkedin.com/in/timo-muster"},
        {"titel": "Portfolio", "url": "https://timo-muster.de"},
    ]
    quelle = Path(tmp) / "verweise.json"
    quelle.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    ziel = Path(tmp) / "verweise.pdf"
    subprocess.run(
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel)],
        capture_output=True, text=True, cwd=str(WURZEL),
    )
    if not ziel.exists():
        return ["Verweistest: PDF nicht gerendert"]

    from pypdf import PdfReader
    seite = PdfReader(str(ziel)).pages[0]
    fehler = []

    # Die Kopfzeile beginnt 60pt unter der Blattkante (842pt hoch), das Logo ist
    # 13.5pt hoch. Alles ueber 740pt steht sicher noch in dieser Zeile.
    hoehen = []

    def besucher(text, cm, tm, schrift, groesse):
        if "timo-muster" in text:
            hoehen.append(tm[5] * cm[3] + cm[5])

    seite.extract_text(visitor_text=besucher)
    if not hoehen:
        fehler.append("Verweise stehen nicht auf Seite 1")
    elif min(hoehen) < 740:
        fehler.append(f"Verweise stehen zu tief auf Seite 1 ({min(hoehen):.0f}pt "
                      "ueber der Unterkante) — sie gehoeren in die Kopfzeile")

    adressen = {a.get_object().get("/A", {}).get("/URI")
                for a in (seite.get("/Annots") or [])
                if a.get_object().get("/Subtype") == "/Link"}
    for erwartet in ("https://www.linkedin.com/in/timo-muster", "https://timo-muster.de"):
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
        [sys.executable, str(WURZEL / "scripts" / "render_cv.py"), str(quelle), str(ziel)],
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


def main():
    beispiel = WURZEL / "beispiel" / "cv.json"
    if not beispiel.exists():
        raise SystemExit(f"Beispieldaten fehlen: {beispiel}")

    with tempfile.TemporaryDirectory() as tmp:
        ziel = Path(tmp) / "selbsttest.pdf"
        lauf = subprocess.run(
            [sys.executable, str(WURZEL / "scripts" / "render_cv.py"),
             str(beispiel), str(ziel)],
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

    fehler += pruefe_linkedin_auswahl()
    fehler += pruefe_website_auswahl()

    print(f"\n  Seiten:    {seiten}")
    print(f"  Format:    {breite} x {hoehe} pt")
    print(f"  Schriften: {schriften} eingebettet")
    print(f"  Bilder:    {bilder} (Logos und Foto)")
    print(f"  LinkedIn:  Fotoauswahl geprueft (ohne Netz)")
    print(f"  Website:   Bilderfilter geprueft (ohne Netz)")
    print(f"  Ueberlauf: erkannt, auch wenn Rolle = Stationstitel")
    print(f"  Verweise:  in der Kopfzeile und anklickbar")
    print(f"  Umbruch:   keine Station mit einem einzelnen Stichpunkt am Seitenende")

    if fehler:
        print("\nProbleme:")
        for f in fehler:
            print(f"  - {f}")
        raise SystemExit(1)

    print("\nSelbsttest bestanden. Der Skill ist einsatzbereit.")


if __name__ == "__main__":
    main()
