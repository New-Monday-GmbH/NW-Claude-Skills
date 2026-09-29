#!/usr/bin/env python3
"""Prüft pruefe_lauf.py und den Beispiel-Lauf in beispiel/lauf/.

    python3 scripts/selbsttest.py

Schreibt nichts in den Skill-Ordner. Rückgabe 1, wenn etwas abweicht.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import pruefe_lauf as pl  # noqa: E402

BEISPIEL = HIER.parent / "beispiel" / "lauf"

FRAGEN = {
    "skill": "newmonday-cv",
    "kandidat": "Timo Muster",
    "texte": [],
    "luecken": [{"was": "Profilfoto", "folge": "Fotospalte bleibt leer",
                 "form": "Bilddatei, Porträt"}],
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
]


def pruefe_fall(name, funktion, daten, fehler_text, warn_text) -> str | None:
    fehler, warnungen = funktion(daten)
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


def main() -> int:
    probleme = [p for p in (pruefe_fall(*fall) for fall in FAELLE) if p]
    probleme += pruefe_uebergaben()
    probleme += pruefe_ordner_faelle()
    if BEISPIEL.exists():
        f, _ = pl.pruefe_ordner(BEISPIEL, dateien=False)
        probleme += [f"beispiel/lauf: {x}" for x in f]
    else:
        probleme.append(f"{BEISPIEL} fehlt")
    for p in probleme:
        print(f"FEHLER: {p}")
    if probleme:
        return 1
    print(f"Selbsttest bestanden ({len(FAELLE)} Fälle, Übergabe, Laufordner, Beispiel)")
    return 0


if __name__ == "__main__":
    sys.exit(main())