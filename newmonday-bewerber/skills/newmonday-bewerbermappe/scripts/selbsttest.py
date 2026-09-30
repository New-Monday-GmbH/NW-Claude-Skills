#!/usr/bin/env python3
"""Prüft pruefe_lauf.py und den Beispiel-Lauf in beispiel/lauf/.

    python3 scripts/selbsttest.py

Schreibt nichts in den Skill-Ordner. Rückgabe 1, wenn etwas abweicht.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import pruefe_lauf as pl  # noqa: E402

BEISPIEL = HIER.parent / "beispiel" / "lauf"
SKRIPT = HIER / "pruefe_lauf.py"

FRAGEN = {
    "skill": "newmonday-cv",
    "kandidat": "Timo Muster",
    "texte": [],
    "luecken": [{"was": "Profilfoto", "folge": "Fotospalte bleibt leer",
                 "form": "Bilddatei, Porträt"}],
    "abweichungen": [{"feld": "Zeitraum Cocomore AG",
                      "werte": {"lebenslauf": "11/2021 – 04/2022", "portfolio": "2020 – 2021"},
                      "neuer": "lebenslauf"}],
    "fragen": [
        {"id": "nm_rolle", "question": "Wie heißt die Rolle bei New Monday?",
         "header": "NM-Rolle", "multiSelect": False,
         "options": [{"label": "User Experience Design Specialist (Empfohlen)",
                      "description": "UX-Profil"},
                     {"label": "Software Development Specialist",
                      "description": "Entwicklerprofil"}]},
    ],
}

AUFTRAG = {
    "version": 1,
    "laufordner": "/tmp/Timo Muster",
    "kandidat": "Timo Muster",
    "sprache": "de",
    "reihenfolge": list(pl.SKILLS),
    "figma": {"aktiv": True,
              "link": "https://www.figma.com/design/AbC123/Test?node-id=12-34",
              "file_key": "AbC123", "seite_id": "12:34", "neues_file": False},
    "material": {"lebenslauf": "eingang/lebenslauf.pdf"},
    "ohne": ["linkedin_export"],
    "vorrang": "portfolio",
    "entscheidungen": {},
    "status": {s: {"vorbereiten": "offen", "bauen": "offen", "fehler": None}
               for s in pl.SKILLS},
}

UEBERGABE = "# Übergabe newmonday-cv\n\n" + "\n\n".join(
    h + "\n–" for h in pl.UEBERGABE) + "\n"


def geaendert(basis: dict, aenderung) -> dict:
    d = copy.deepcopy(basis)
    aenderung(d)
    return d


def zweite_frage(d):
    q = copy.deepcopy(d["fragen"][0])
    d["fragen"].append(q)


def status(skill: str, **werte):
    """Änderung für geaendert(): status.<skill> bekommt diese Werte."""
    return lambda d: d["status"][skill].update(werte)


def antworten(skill: str, **werte):
    """Änderung für geaendert(): entscheidungen.<skill> sind genau diese Antworten."""
    return lambda d: d["entscheidungen"].update({skill: werte})


def abweichung(**felder):
    """Änderung für geaendert(): abweichungen[0] bekommt diese Felder."""
    return lambda d: d["abweichungen"][0].update(felder)


def vorrang(wert):
    """Änderung für geaendert(): vorrang bekommt diesen Wert."""
    return lambda d: d.update(vorrang=wert)


# (Name, Prüffunktion, Daten, erwarteter Fehlertext oder None, erwartete Warnung oder None)
FAELLE = [
    ("fragen gültig", pl.pruefe_fragen, FRAGEN, None, None),
    ("fünf Fragen", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(fragen=[
         dict(d["fragen"][0], id=f"f{i}", question=f"Frage {i}?") for i in range(5)])),
     "statt höchstens 4", None),
    ("id nicht snake_case", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0].update(id="NM-Rolle")),
     "kein snake_case", None),
    ("id doppelt", pl.pruefe_fragen, geaendert(FRAGEN, zweite_frage), "doppelt", None),
    ("ohne Fragezeichen", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0].update(question="Rolle bei NM")),
     "muss mit '?' enden", None),
    ("eine Option", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0]["options"].pop()),
     "statt 2–4", None),
    ("Empfohlen an zweiter Stelle", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0]["options"].reverse()),
     "muss die erste Option sein", None),
    ("text_noetig kein bool", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0]["options"][1].update(text_noetig="ja")),
     "text_noetig", None),
    ("unbekannter Skill", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(skill="newmonday-foo")),
     "ist keiner von", None),
    ("Lücke ohne Folge", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["luecken"][0].pop("folge")),
     "luecken[0].folge", None),
    ("Header 13 Zeichen", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0].update(header="Weiterbildung")),
     None, "13 Zeichen"),
    ("auftrag gültig", pl.pruefe_auftrag, AUFTRAG, None, None),
    ("Sprache fr", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(sprache="fr")), "sprache", None),
    ("Reihenfolge vertauscht", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["reihenfolge"].reverse()), "reihenfolge", None),
    ("Figma-Link ohne node-id", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["figma"].update(
         link="https://www.figma.com/design/AbC123/Test")), "figma.link", None),
    ("Seite passt nicht zum Link", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["figma"].update(seite_id="1:2")),
     "passt nicht zur node-id", None),
    ("Figma aus, kein Link", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(figma={"aktiv": False, "link": None})),
     None, None),
    ("weder Lebenslauf noch LinkedIn", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(material={"portfolio_pdf": "eingang/p.pdf"})),
     "weder lebenslauf", None),
    ("gebaut, nicht vorbereitet", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["status"]["newmonday-cv"].update(bauen="fertig")),
     "gebaut, aber nicht vorbereitet", None),
    ("unbekanntes Material", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["material"].update(website="x")),
     "material.website: unbekannt", None),
    ("fragen mit [] statt dict", pl.pruefe_fragen, [], "oberste Ebene", None),
    ("fragen[0] ist String statt dict", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(fragen=["oops"])),
     "fragen[0]: muss ein Objekt sein", None),
    ("question ist Liste statt String", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0].update(question=["a", "b"])),
     "muss mit '?' enden", None),
    ("options[0] ist String statt dict", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0].update(options=["x", {"label": "y", "description": "z"}])),
     "options[0]: muss ein Objekt sein", None),
    ("auftrag ist String statt dict", pl.pruefe_auftrag, "x", "oberste Ebene", None),
    ("ohne ist int statt Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(ohne=5)), "ohne: muss eine Liste sein", None),
    ("entscheidungen ist Liste statt dict", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(entscheidungen=[])), "entscheidungen: muss ein Objekt sein", None),
    # Nicht-Strings vor Mengen- und Dict-Tests, jeder Typ geprüft
    ("skill ist Liste", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(skill=["newmonday-cv"])),
     "skill: muss ein String sein", None),
    ("skill ist Objekt", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(skill={})),
     "skill: muss ein String sein", None),
    ("ohne-Eintrag ist Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(ohne=[["x"]])),
     "ohne[0]: muss ein String sein", None),
    ("ohne-Eintrag ist Objekt", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(ohne=["linkedin_export", {}])),
     "ohne[1]: muss ein String sein", None),
    ("Status ist Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, status("newmonday-cv", vorbereiten=[])),
     "status.newmonday-cv.vorbereiten: [] ist keiner von", None),
    ("Status ist Objekt", pl.pruefe_auftrag,
     geaendert(AUFTRAG, status("newmonday-portfolio", bauen={})),
     "status.newmonday-portfolio.bauen: {} ist keiner von", None),
    ("status ist Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(status=[])),
     "status: muss ein Objekt sein", None),
    ("Fehlergrund ist Zahl", pl.pruefe_auftrag,
     geaendert(AUFTRAG, status("newmonday-cv", vorbereiten="fehler", fehler=3)),
     "status.newmonday-cv.fehler: muss ein String oder null sein", None),
    ("Materialpfad ist Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["material"].update(lebenslauf=["eingang/lebenslauf.pdf"])),
     "material.lebenslauf: muss ein String oder null sein", None),
    ("figma.neues_file kein bool", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["figma"].update(neues_file="nein")),
     "figma.neues_file: muss true oder false sein", None),
    ("Antworten eines Skills sind Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(entscheidungen={"newmonday-cv": []})),
     "entscheidungen.newmonday-cv: muss ein Objekt sein", None),
    ("Antwort ist Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, antworten("newmonday-cv", fachfremd=["Verkäufer", "Zivildienst"])),
     "entscheidungen.newmonday-cv.fachfremd: muss ein String sein", None),
    ("leere Mehrfachauswahl", pl.pruefe_auftrag,
     geaendert(AUFTRAG, antworten("newmonday-cv", fachfremd="")), None, None),
    # weitere Einzelprüfungen
    ("Fragetext doppelt", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"].append(
         dict(copy.deepcopy(d["fragen"][0]), id="nm_rolle_neu"))),
     "question: doppelt", None),
    ("zweimal Empfohlen", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0]["options"][1].update(
         label="Software Development Specialist (Empfohlen)")),
     "mehr als eine Option (Empfohlen)", None),
    ("Labels doppelt", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0]["options"][0].update(
         label="Software Development Specialist")),
     "Labels doppelt", None),
    ("multiSelect kein bool", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["fragen"][0].update(multiSelect="nein")),
     "multiSelect: muss true oder false sein", None),
    ("ohne mit Lücke ohne Materialschlüssel", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(ohne=["Weitere Projekte"])),
     None, "kein Materialschlüssel"),
    ("ohne und material zugleich", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.update(ohne=["lebenslauf"])),
     None, "steht auch unter material"),
    ("ungültiger Statuswert", pl.pruefe_auftrag,
     geaendert(AUFTRAG, status("newmonday-skillmatrix", bauen="erledigt")),
     "status.newmonday-skillmatrix.bauen: 'erledigt' ist keiner von", None),
    ("file_key passt nicht zum Link", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d["figma"].update(file_key="XyZ789")),
     None, "figma.file_key"),
    # Eine Quelle für alle: abweichungen in fragen.json
    ("abweichungen fehlen", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.pop("abweichungen")), None, None),
    ("abweichungen leer", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(abweichungen=[])), None, None),
    ("abweichungen ist Objekt", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(abweichungen={})),
     "abweichungen: muss eine Liste sein", None),
    ("Abweichung ist String", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d.update(abweichungen=["Zeitraum Cocomore AG"])),
     "abweichungen[0]: muss ein Objekt sein", None),
    ("Abweichung mit leerem feld", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(feld=" ")), "abweichungen[0].feld: fehlt", None),
    ("Abweichung ohne feld", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["abweichungen"][0].pop("feld")),
     "abweichungen[0].feld: fehlt", None),
    ("werte ist Liste", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte=["11/2021 – 04/2022", "2020 – 2021"])),
     "abweichungen[0].werte: muss ein Objekt sein", None),
    ("werte mit einer Quelle", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "11/2021 – 04/2022"})),
     "abweichungen[0].werte: 1 Quelle(n) statt mindestens 2", None),
    ("werte mit drei Quellen", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "UX Designer",
                                         "linkedin_export": "Senior UX Designer",
                                         "portfolio": "Lead UX Designer"},
                                  neuer="linkedin_export")), None, None),
    ("werte mit unbekannter Quelle", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "2021", "xing": "2020"}, neuer="lebenslauf")),
     "abweichungen[0].werte.xing: unbekannte Quelle", None),
    ("Wert ist Zahl", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "2021", "portfolio": 2020})),
     "abweichungen[0].werte.portfolio: muss ein String sein", None),
    ("werte alle gleich", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "2021", "portfolio": "2021 "})),
     "abweichungen[0].werte: alle gleich – keine Abweichung", None),
    ("werte gleich bis auf Großschreibung", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "UX Designer",
                                         "portfolio": "ux  designer"}, neuer="portfolio")),
     "alle gleich – keine Abweichung", None),
    ("werte gleich bis auf Strichart", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "2017 - 2024",
                                         "linkedin_export": "2017 – 2024"}, neuer="lebenslauf")),
     "alle gleich – keine Abweichung", None),
    ("werte verschieden in der Reihenfolge", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "UI/UX Designer",
                                         "portfolio": "UX/UI Designer"}, neuer="portfolio")),
     None, None),
    ("Wert leer", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "2021", "portfolio": " "})),
     "abweichungen[0].werte.portfolio: leer", None),
    ("Wert Gedankenstrich", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "2021", "linkedin_export": "2020",
                                         "portfolio": "–"})),
     "abweichungen[0].werte.portfolio: leer", None),
    ("zwei Werte, einer leer, der dritte gleich", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte={"lebenslauf": "2021", "linkedin_export": "2021",
                                         "portfolio": "-"})),
     "alle gleich – keine Abweichung", None),
    ("neuer fehlt", pl.pruefe_fragen,
     geaendert(FRAGEN, lambda d: d["abweichungen"][0].pop("neuer")), None, None),
    ("neuer nicht in werte", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(neuer="linkedin_export")),
     "abweichungen[0].neuer: 'linkedin_export' ist keine Quelle aus werte", None),
    ("neuer ist Label statt Schlüssel", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(neuer="Lebenslauf")),
     "abweichungen[0].neuer: 'Lebenslauf' ist keine Quelle", None),
    ("neuer ist Liste", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(neuer=["lebenslauf"])),
     "abweichungen[0].neuer: muss ein String sein", None),
    ("neuer ist null", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(neuer=None)),
     "abweichungen[0].neuer: muss ein String sein", None),
    ("neuer bei kaputten werte", pl.pruefe_fragen,
     geaendert(FRAGEN, abweichung(werte=[], neuer="xing")),
     "abweichungen[0].neuer: 'xing' ist keine Quelle", None),
    # Eine Quelle für alle: vorrang in auftrag.json
    ("vorrang fehlt", pl.pruefe_auftrag,
     geaendert(AUFTRAG, lambda d: d.pop("vorrang")), None, None),
    ("vorrang null", pl.pruefe_auftrag, geaendert(AUFTRAG, vorrang(None)), None, None),
    ("vorrang lebenslauf", pl.pruefe_auftrag,
     geaendert(AUFTRAG, vorrang("lebenslauf")), None, None),
    ("vorrang linkedin_export", pl.pruefe_auftrag,
     geaendert(AUFTRAG, vorrang("linkedin_export")), None, None),
    ("vorrang Anweisung", pl.pruefe_auftrag,
     geaendert(AUFTRAG, vorrang("Anweisung: Zeiträume aus LinkedIn, Titel aus dem Portfolio")),
     None, None),
    ("vorrang ist Label statt Schlüssel", pl.pruefe_auftrag,
     geaendert(AUFTRAG, vorrang("LinkedIn-Export")),
     "vorrang: 'LinkedIn-Export' ist keiner von", None),
    ("vorrang Anweisung ohne Text", pl.pruefe_auftrag,
     geaendert(AUFTRAG, vorrang("Anweisung:  ")), "vorrang: Anweisung ohne Text", None),
    ("vorrang ist Zahl", pl.pruefe_auftrag,
     geaendert(AUFTRAG, vorrang(1)), "vorrang: 1 ist keiner von", None),
    ("vorrang ist Liste", pl.pruefe_auftrag,
     geaendert(AUFTRAG, vorrang(["portfolio"])), "vorrang: ['portfolio'] ist keiner von", None),
]


def pruefe_fall(name, funktion, daten, fehler_text, warn_text) -> str | None:
    try:
        fehler, warnungen = funktion(daten)
    except Exception as e:  # jede Ausnahme ist ein Befund, kein Abbruch des Tests
        return f"{name}: Ausnahme {type(e).__name__}: {e}"
    if fehler_text is None and fehler:
        return f"{name}: unerwartete Fehler {fehler}"
    if fehler_text is not None and not any(fehler_text in x for x in fehler):
        return f"{name}: erwartet Fehler mit {fehler_text!r}, bekommen {fehler}"
    if warn_text is not None and not any(warn_text in x for x in warnungen):
        return f"{name}: erwartet Warnung mit {warn_text!r}, bekommen {warnungen}"
    return None


def pruefe_uebergaben() -> list[str]:
    probleme = []
    if pl.pruefe_uebergabe(UEBERGABE):
        probleme.append(f"uebergabe gültig: {pl.pruefe_uebergabe(UEBERGABE)}")
    ohne = UEBERGABE.replace("## Fehlt noch\n", "")
    if not any("Fehlt noch" in x for x in pl.pruefe_uebergabe(ohne)):
        probleme.append("uebergabe ohne 'Fehlt noch' wird nicht bemängelt")
    vertauscht = (UEBERGABE.replace("## Hinweise\n", "## X\n")
                  .replace("## Zur Freigabe\n", "## Hinweise\n")
                  .replace("## X\n", "## Zur Freigabe\n"))
    if not any("nicht in der Reihenfolge" in x for x in pl.pruefe_uebergabe(vertauscht)):
        probleme.append("uebergabe mit vertauschten Abschnitten wird nicht bemängelt")
    return probleme


def pruefe_ordner_faelle() -> list[str]:
    probleme = []
    with tempfile.TemporaryDirectory() as tmp:
        lauf = Path(tmp)
        (lauf / "auftrag.json").write_text(json.dumps(AUFTRAG), encoding="utf-8")
        f, _ = pl.pruefe_ordner(lauf)
        if not any("gibt es im Laufordner nicht" in x for x in f):
            probleme.append(f"fehlender Lebenslauf nicht bemerkt: {f}")
        (lauf / "eingang").mkdir()
        (lauf / "eingang" / "lebenslauf.pdf").write_bytes(b"%PDF-1.4\n")
        (lauf / "skillmatrix").mkdir()
        (lauf / "skillmatrix" / "fragen.json").write_text(json.dumps(FRAGEN), encoding="utf-8")
        f, _ = pl.pruefe_ordner(lauf)
        if not any("erwartet 'newmonday-skillmatrix'" in x for x in f):
            probleme.append(f"fragen.json im falschen Ordner nicht bemerkt: {f}")
        # Test: auftrag.json with non-dict material
        (lauf / "auftrag.json").write_text(json.dumps({**AUFTRAG, "material": []}), encoding="utf-8")
        f, _ = pl.pruefe_ordner(lauf)
        if not any("material: muss ein Objekt sein" in x for x in f):
            probleme.append(f"material als Liste nicht bemerkt: {f}")
        # Test: skillmatrix/fragen.json as JSON list instead of dict
        (lauf / "auftrag.json").write_text(json.dumps(AUFTRAG), encoding="utf-8")
        (lauf / "skillmatrix" / "fragen.json").write_text(json.dumps([]), encoding="utf-8")
        f, _ = pl.pruefe_ordner(lauf)
        if not any("skillmatrix/fragen.json: oberste Ebene" in x for x in f):
            probleme.append(f"fragen.json als Liste nicht bemerkt: {f}")
        # Test: cv/uebergabe.md with invalid UTF-8
        (lauf / "cv").mkdir()
        (lauf / "cv" / "uebergabe.md").write_bytes(b"\xff\xfe")
        f, _ = pl.pruefe_ordner(lauf)
        if not any("cv/uebergabe.md: nicht lesbar" in x for x in f):
            probleme.append(f"UTF-8 Fehler nicht bemerkt: {f}")
    return probleme


def schreibe(lauf: Path, pfad: str, inhalt) -> None:
    """Legt eine Datei im Laufordner an – str als Rohtext, alles andere als JSON."""
    datei = lauf / pfad
    datei.parent.mkdir(parents=True, exist_ok=True)
    text = inhalt if isinstance(inhalt, str) else json.dumps(inhalt)
    datei.write_text(text, encoding="utf-8")


# (Name, Dateien im Laufordner, erwarteter Fehlertext oder None, erwartete Warnung oder None);
# geprüft mit pruefe_ordner(..., dateien=False). Fehlertext None heißt: kein Fehler.
ORDNER = [
    ("auftrag.json fehlt", {"cv/fragen.json": FRAGEN}, "auftrag.json: fehlt", None),
    ("auftrag.json ist null", {"auftrag.json": "null"},
     "auftrag.json: oberste Ebene muss ein JSON-Objekt sein", None),
    ("auftrag.json mit Syntaxfehler", {"auftrag.json": '{"version": 1,'},
     "auftrag.json: nicht lesbar", None),
    ("fragen.json ist null", {"auftrag.json": AUFTRAG, "cv/fragen.json": "null"},
     "cv/fragen.json: oberste Ebene muss ein JSON-Objekt sein", None),
    ("fragen.json mit Syntaxfehler",
     {"auftrag.json": AUFTRAG, "cv/fragen.json": '{"skill": "newmonday-cv",'},
     "cv/fragen.json: nicht lesbar", None),
    ("skill in fragen.json ist Liste",
     {"auftrag.json": AUFTRAG,
      "cv/fragen.json": geaendert(FRAGEN, lambda d: d.update(skill=["newmonday-cv"]))},
     "cv/fragen.json: skill: muss ein String sein", None),
    ("Antwort-id ohne Frage",
     {"auftrag.json": geaendert(AUFTRAG, antworten(
         "newmonday-cv", nm_rolle="Software Development Specialist", nm_start="Oktober 2026")),
      "cv/fragen.json": FRAGEN},
     "entscheidungen.newmonday-cv.nm_start", None),
    ("Antwort-ids passen",
     {"auftrag.json": geaendert(AUFTRAG, antworten(
         "newmonday-cv", nm_rolle="Software Development Specialist")),
      "cv/fragen.json": FRAGEN},
     None, None),
    ("vorbereiten fehler: fragen.json übersprungen",
     {"auftrag.json": geaendert(AUFTRAG, status(
         "newmonday-skillmatrix", vorbereiten="fehler", fehler="Subagent abgebrochen")),
      "skillmatrix/fragen.json": "{kaputt"},
     None, "skillmatrix/fragen.json: nicht geprüft"),
    ("ausgelassen: uebergabe.md übersprungen",
     {"auftrag.json": geaendert(AUFTRAG, status(
         "newmonday-portfolio", vorbereiten="ausgelassen", bauen="ausgelassen")),
      "portfolio/uebergabe.md": "# Übergabe newmonday-portfolio\n"},
     None, "portfolio/uebergabe.md: nicht geprüft"),
    ("bauen offen: uebergabe.md geprüft",
     {"auftrag.json": AUFTRAG, "portfolio/uebergabe.md": "# Übergabe newmonday-portfolio\n"},
     "portfolio/uebergabe.md: Abschnitt fehlt", None),
    ("Abweichung mit falschem neuer im Laufordner",
     {"auftrag.json": AUFTRAG, "cv/fragen.json": geaendert(FRAGEN, abweichung(neuer="xing"))},
     "cv/fragen.json: abweichungen[0].neuer", None),
    ("vorrang falsch im Laufordner",
     {"auftrag.json": geaendert(AUFTRAG, vorrang("Portfolio")), "cv/fragen.json": FRAGEN},
     "auftrag.json: vorrang", None),
]


def ordner_fall(name, dateien, fehler_text, warn_text) -> str | None:
    with tempfile.TemporaryDirectory() as tmp:
        lauf = Path(tmp)
        for pfad, inhalt in dateien.items():
            schreibe(lauf, pfad, inhalt)
        try:
            fehler, warnungen = pl.pruefe_ordner(lauf, dateien=False)
        except Exception as e:
            return f"{name}: Ausnahme {type(e).__name__}: {e}"
    return pruefe_fall(name, lambda _: (fehler, warnungen), None, fehler_text, warn_text)


def pruefe_laufordner() -> list[str]:
    """laufordner in auftrag.json gegen den geprüften Ordner: nur eine Warnung."""
    probleme = []
    with tempfile.TemporaryDirectory() as tmp:
        lauf = Path(tmp)
        for pfad, erwartet in ((str(lauf), False), (str(lauf / "anderer Ordner"), True)):
            schreibe(lauf, "auftrag.json", geaendert(AUFTRAG, lambda d: d.update(laufordner=pfad)))
            fehler, warnungen = pl.pruefe_ordner(lauf, dateien=False)
            if any("laufordner" in x for x in fehler + warnungen) != erwartet:
                probleme.append(f"laufordner {pfad!r}: erwartet Warnung {erwartet}, "
                                f"bekommen {fehler + warnungen}")
    return probleme


# Werte, die an jeder Stelle einer JSON-Datei stehen könnten
SONDERWERTE = [None, True, 0, 2.5, "", "x", "\ud800", "a\x00b",
               [], {}, [None], [[]], [{}], {"x": []}]


def schluesselpfade(wert, pfad: tuple = ()):
    """Jeder Pfad zu einem Wert im JSON-Baum, die Wurzel eingeschlossen."""
    yield pfad
    if isinstance(wert, dict):
        for k, v in wert.items():
            yield from schluesselpfade(v, pfad + (k,))
    elif isinstance(wert, list):
        for i, v in enumerate(wert):
            yield from schluesselpfade(v, pfad + (i,))


def ersetzt(basis, pfad: tuple, wert):
    if not pfad:
        return copy.deepcopy(wert)
    d = copy.deepcopy(basis)
    ziel = d
    for k in pfad[:-1]:
        ziel = ziel[k]
    ziel[pfad[-1]] = copy.deepcopy(wert)
    return d


def pruefe_robustheit() -> list[str]:
    """Kein JSON-Wert an keiner Stelle darf pruefe_ordner eine Ausnahme entlocken."""
    auftrag = geaendert(AUFTRAG, antworten("newmonday-cv", nm_rolle="Software Development Specialist"))
    befunde: dict = {}
    with tempfile.TemporaryDirectory() as tmp:
        lauf = Path(tmp)
        schreibe(lauf, "cv/uebergabe.md", UEBERGABE)
        for datei, basis in (("auftrag.json", auftrag), ("cv/fragen.json", FRAGEN)):
            schreibe(lauf, "auftrag.json", auftrag)
            schreibe(lauf, "cv/fragen.json", FRAGEN)
            for pfad in schluesselpfade(basis):
                for wert in SONDERWERTE:
                    schreibe(lauf, datei, json.dumps(ersetzt(basis, pfad, wert)))
                    try:
                        pl.pruefe_ordner(lauf)
                    except Exception as e:
                        stelle = f"{datei} {'.'.join(map(str, pfad)) or '(ganze Datei)'}"
                        befunde.setdefault(stelle, [f"{type(e).__name__}: {e}"]).append(wert)
    return [f"Robustheit {stelle}: {werte[0]} bei {werte[1:]!r}"
            for stelle, werte in befunde.items()]


def cli(*args: str, seed: str = "0") -> subprocess.CompletedProcess:
    umgebung = dict(os.environ, PYTHONHASHSEED=seed)
    return subprocess.run([sys.executable, str(SKRIPT), *args],
                          capture_output=True, text=True, env=umgebung)


def pruefe_cli() -> list[str]:
    """pruefe_lauf.py als Befehl: Rückgabewerte, feste Reihenfolge, kein Traceback."""
    probleme = []
    r = cli(str(BEISPIEL), "--ohne-dateien")
    if r.returncode != 0 or not r.stdout.rstrip().endswith("Lauf in Ordnung"):
        probleme.append(f"CLI Beispiel: Rückgabe {r.returncode} statt 0: {r.stdout}{r.stderr}")
    r = cli()
    if r.returncode != 2:
        probleme.append(f"CLI ohne Laufordner: Rückgabe {r.returncode} statt 2")
    with tempfile.TemporaryDirectory() as tmp:
        lauf = Path(tmp)
        schreibe(lauf, "auftrag.json", geaendert(AUFTRAG, lambda d: d["material"].update(
            foto="eingang/foto.jpg", logos="eingang/logos/", screens="eingang/screens/",
            zertifikate="eingang/zertifikate/")))
        r = cli(str(lauf))
        if r.returncode != 1 or "FEHLER —" not in r.stdout or "Traceback" in r.stderr:
            probleme.append(f"CLI mit Fehlern: Rückgabe {r.returncode} statt 1: {r.stdout}{r.stderr}")
        ausgaben = {cli(str(lauf), seed=str(s)).stdout for s in range(8)}
        if len(ausgaben) != 1:
            probleme.append(f"CLI: Ausgabe hängt vom Hash-Seed ab – {len(ausgaben)} Fassungen "
                            "bei 8 Läufen, Reihenfolge nicht fest")
        schreibe(lauf, "auftrag.json", '{"version": 1, "material": {"\\ud800": "x"}}')
        r = cli(str(lauf))
        if r.returncode != 1 or "Traceback" in r.stderr:
            letzte = (r.stderr.strip().splitlines() or [""])[-1]
            probleme.append(f"CLI mit einzelnem Surrogat im Schlüssel: Rückgabe {r.returncode}, {letzte}")
    return probleme


def main() -> int:
    probleme = [p for p in (pruefe_fall(*fall) for fall in FAELLE) if p]
    probleme += pruefe_uebergaben()
    probleme += pruefe_ordner_faelle()
    probleme += [p for p in (ordner_fall(*fall) for fall in ORDNER) if p]
    probleme += pruefe_laufordner()
    probleme += pruefe_robustheit()
    probleme += pruefe_cli()
    if BEISPIEL.exists():
        f, _ = pl.pruefe_ordner(BEISPIEL, dateien=False)
        probleme += [f"beispiel/lauf: {x}" for x in f]
    else:
        probleme.append(f"{BEISPIEL} fehlt")
    for p in probleme:
        print(f"FEHLER: {p}")
    if probleme:
        return 1
    print(f"Selbsttest bestanden ({len(FAELLE)} Fälle, {len(ORDNER)} Laufordner-Fälle, "
          "Übergabe, Robustheit, Befehl, Beispiel)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
