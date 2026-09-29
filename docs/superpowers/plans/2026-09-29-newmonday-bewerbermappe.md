# newmonday-bewerbermappe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein Orchestrator-Skill `newmonday-bewerbermappe`, der `newmonday-cv`, `newmonday-skillmatrix` und `newmonday-portfolio` in einem Lauf nacheinander ausführt – gemeinsame Fragen einmal, Lückencheck vorab, alle Entscheidungen gebündelt, danach Bau ohne Rückfrage.

**Architecture:** Der Orchestrator läuft im Hauptgespräch und stellt als Einziger Fragen (`AskUserQuestion`). Je Skill und Phase (*vorbereiten*, *bauen*) arbeitet ein `general-purpose`-Subagent mit frischem Kontext; Orchestrator und Subagenten reden über Dateien in einem Laufordner (`auftrag.json`, `fragen.json`, `notizen.md`, `uebergabe.md`). Die drei Skills bekommen je einen Abschnitt `## Im Gesamtlauf`, sonst ändert sich an ihnen nichts.

**Tech Stack:** Claude-Code-Skills (Markdown, deutsch), Python 3 nur Standardbibliothek, Bash, Figma-MCP (`use_figma`, `whoami`, `get_metadata`, `create_new_file`).

**Spec:** `docs/superpowers/specs/2026-09-29-newmonday-bewerbermappe-design.md` – die „Nachträge aus der Planung“ (Task 1, Schritt 7) gehen der Spec vor.

## Global Constraints

- Branch: `newmonday-bewerbermappe` (existiert, Spec ist committet).
- Skill-Name `newmonday-bewerbermappe`, Ordner `newmonday-bewerber/skills/newmonday-bewerbermappe/`; Frontmatter-`description` ≤ 1 024 Zeichen.
- Bau-Reihenfolge immer `newmonday-cv` → `newmonday-skillmatrix` → `newmonday-portfolio`, nie parallel.
- Unterordner im Laufordner: `cv`, `skillmatrix`, `portfolio`.
- Die drei Skills bekommen **nur** je einen neuen Abschnitt `## Im Gesamtlauf`, eingefügt direkt vor der Zeile `## Gefragt wird mit Klickboxen, nicht im Fließtext`. Keine Änderung an `description`, Templates, Skripten, Referenzen der drei Skills.
- Python: nur Standardbibliothek, `from __future__ import annotations`, läuft mit dem System-`python3`.
- Texte in Skills und Referenzen: Deutsch mit Umlauten und typografischen Anführungszeichen („…“), im Ton der Nachbar-Skills.
- Keine Kandidatendaten ins Repo. Testläufe liegen unter `/Users/florian/Desktop/bewerbermappe-test/`.
- Plugin-Version `1.3.0` in `newmonday-bewerber/.claude-plugin/plugin.json` und `.claude-plugin/marketplace.json`.
- Commit-Nachrichten im Repo-Stil (`newmonday-bewerbermappe: …`, `newmonday-cv: …`), letzte Zeile `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Die Shell merkt sich nichts zwischen zwei Aufrufen.** Jeder Befehlsblock braucht die Zeilen aus „Kurzpfade“ (unten) vorneweg, in Task 3–5 zusätzlich die `L=`-Zeile des Tasks. In den Blöcken unten stehen sie der Kürze halber nicht jedes Mal.
- Schritte mit **[Hauptgespräch]** führt der Controller aus, nicht ein Implementierungs-Subagent: Sie starten selbst Subagenten (`Agent`) oder brauchen den Nutzer.

## Dateien

| Datei | Verantwortung |
|---|---|
| `newmonday-bewerber/skills/newmonday-bewerbermappe/SKILL.md` | Orchestrator: Phasen 1–6, Subagenten-Auftrag, Wiederaufnahme |
| `…/newmonday-bewerbermappe/references/formate.md` | Felder und Regeln von `auftrag.json`, `fragen.json`, `notizen.md`, `uebergabe.md` |
| `…/newmonday-bewerbermappe/scripts/pruefe_lauf.py` | prüft einen Laufordner (auch zur Laufzeit, vor jedem `AskUserQuestion`) |
| `…/newmonday-bewerbermappe/scripts/selbsttest.py` | Tests für `pruefe_lauf.py` und das Beispiel |
| `…/newmonday-bewerbermappe/scripts/testmaterial.sh` | rendert den Beispiel-Lebenslauf aus `newmonday-cv` als Test-Eingang |
| `…/newmonday-bewerbermappe/beispiel/lauf/…` | erfundener Beispiel-Lauf „Timo Muster“ – Referenz für die Formate |
| `…/newmonday-cv/SKILL.md` | + Abschnitt `## Im Gesamtlauf` |
| `…/newmonday-skillmatrix/SKILL.md` | + Abschnitt `## Im Gesamtlauf` |
| `…/newmonday-portfolio/SKILL.md` | + Abschnitt `## Im Gesamtlauf` |
| `README.md`, `newmonday-bewerber/README.md`, `plugin.json`, `marketplace.json` | Eintrag, Installation, Version |
| `docs/superpowers/specs/2026-09-29-newmonday-bewerbermappe-design.md` | + „Nachträge aus der Planung“ |

Kurzpfade in den Befehlen unten:

```bash
R=/Users/florian/NW-Claude-Skills
S=$R/newmonday-bewerber/skills
BM=$S/newmonday-bewerbermappe
T=/Users/florian/Desktop/bewerbermappe-test
```

---

### Task 1: Formate und Laufprüfung

**Files:**
- Create: `newmonday-bewerber/skills/newmonday-bewerbermappe/scripts/selbsttest.py`
- Create: `newmonday-bewerber/skills/newmonday-bewerbermappe/scripts/pruefe_lauf.py`
- Create: `newmonday-bewerber/skills/newmonday-bewerbermappe/beispiel/lauf/auftrag.json`
- Create: `…/beispiel/lauf/cv/fragen.json`, `…/beispiel/lauf/cv/uebergabe.md`
- Create: `…/beispiel/lauf/skillmatrix/fragen.json`
- Create: `…/beispiel/lauf/portfolio/fragen.json`
- Create: `newmonday-bewerber/skills/newmonday-bewerbermappe/references/formate.md`
- Modify: `docs/superpowers/specs/2026-09-29-newmonday-bewerbermappe-design.md` (Abschnitt am Ende anhängen)

**Interfaces:**
- Produces: `pruefe_lauf.py` mit `SKILLS: dict[str, str]` (Skill → Unterordner, Bau-Reihenfolge), `UEBERGABE: list[str]` (sechs Überschriften), `pruefe_fragen(d: dict) -> tuple[list[str], list[str]]`, `pruefe_auftrag(d: dict) -> tuple[list[str], list[str]]`, `pruefe_uebergabe(text: str) -> list[str]`, `pruefe_ordner(lauf: Path, dateien: bool = True) -> tuple[list[str], list[str]]` (jeweils Fehler, Warnungen). CLI: `python3 pruefe_lauf.py <laufordner> [--ohne-dateien]` → letzte Zeile `Lauf in Ordnung` (Exit 0) oder `FEHLER — n Stelle(n)` (Exit 1).
- Produces: `references/formate.md` – von SKILL.md und dem Subagenten-Auftrag referenziert.

- [ ] **Step 1: Selbsttest schreiben**

`newmonday-bewerber/skills/newmonday-bewerbermappe/scripts/selbsttest.py`:

```python
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
```

- [ ] **Step 2: Selbsttest laufen lassen – muss scheitern**

Run: `python3 $BM/scripts/selbsttest.py`
Expected: FAIL mit `ModuleNotFoundError: No module named 'pruefe_lauf'`

- [ ] **Step 3: `pruefe_lauf.py` schreiben**

`newmonday-bewerber/skills/newmonday-bewerbermappe/scripts/pruefe_lauf.py`:

```python
#!/usr/bin/env python3
"""Prüft die Dateien eines Gesamtlaufs von newmonday-bewerbermappe.

    python3 pruefe_lauf.py <laufordner>
    python3 pruefe_lauf.py <laufordner> --ohne-dateien   # Materialpfade nicht prüfen

Geprüft werden auftrag.json, jede <skill>/fragen.json und jede
<skill>/uebergabe.md, die es gibt. Rückgabe 1, wenn etwas nicht stimmt – die
Ausgabe nennt jede Stelle. Warnungen halten nichts auf. Nur Standardbibliothek.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Skill -> Unterordner im Laufordner, in Bau-Reihenfolge
SKILLS = {
    "newmonday-cv": "cv",
    "newmonday-skillmatrix": "skillmatrix",
    "newmonday-portfolio": "portfolio",
}
MATERIAL = {"lebenslauf", "linkedin_export", "linkedin_url", "xing_url",
            "portfolio_url", "portfolio_pdf", "foto", "logos", "screens",
            "zertifikate", "kundentexte"}
PFADE = {"lebenslauf", "linkedin_export", "portfolio_pdf", "foto", "logos",
         "screens", "zertifikate"}
STATUS = {"offen", "fertig", "fehler", "ausgelassen"}
UEBERGABE = ["## Dateien", "## Zur Freigabe", "## Quellen weichen ab",
             "## Hinweise", "## Ohne Rückfrage entschieden", "## Fehlt noch"]
EMPFOHLEN = "(Empfohlen)"
ID = re.compile(r"^[a-z][a-z0-9_]*$")
FIGMA_LINK = re.compile(
    r"^https://www\.figma\.com/design/[A-Za-z0-9]+/[^?]*\?(?:.*&)?node-id=(\d+)-(\d+)")
SEITE = re.compile(r"^\d+:\d+$")


def _text(wert) -> bool:
    return isinstance(wert, str) and bool(wert.strip())


def pruefe_fragen(d: dict) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für den Inhalt einer fragen.json."""
    f: list[str] = []
    w: list[str] = []
    if d.get("skill") not in SKILLS:
        f.append(f"skill: {d.get('skill')!r} ist keiner von {sorted(SKILLS)}")
    if not _text(d.get("kandidat")):
        f.append("kandidat: fehlt")
    texte = d.get("texte", [])
    if not isinstance(texte, list) or not all(isinstance(t, str) for t in texte):
        f.append("texte: muss eine Liste von Strings sein")
    luecken = d.get("luecken", [])
    if not isinstance(luecken, list):
        f.append("luecken: muss eine Liste sein")
        luecken = []
    for i, l in enumerate(luecken):
        for k in ("was", "folge", "form"):
            if not _text(l.get(k) if isinstance(l, dict) else None):
                f.append(f"luecken[{i}].{k}: fehlt")
    fragen = d.get("fragen", [])
    if not isinstance(fragen, list):
        return f + ["fragen: muss eine Liste sein"], w
    if len(fragen) > 4:
        f.append(f"fragen: {len(fragen)} statt höchstens 4")
    ids: set = set()
    fragetexte: set = set()
    for i, q in enumerate(fragen):
        o = f"fragen[{i}]"
        qid = str(q.get("id", ""))
        if not ID.match(qid):
            f.append(f"{o}.id: {qid!r} ist kein snake_case")
        elif qid in ids:
            f.append(f"{o}.id: {qid!r} doppelt")
        ids.add(qid)
        text = q.get("question")
        if not _text(text) or not text.strip().endswith("?"):
            f.append(f"{o}.question: muss mit '?' enden")
        elif text in fragetexte:
            f.append(f"{o}.question: doppelt – Antworten kommen nach Fragetext zurück")
        fragetexte.add(text)
        header = q.get("header")
        if not _text(header):
            f.append(f"{o}.header: fehlt")
        elif len(header) > 12:
            w.append(f"{o}.header: {header!r} hat {len(header)} Zeichen, "
                     "AskUserQuestion zeigt 12")
        if not isinstance(q.get("multiSelect"), bool):
            f.append(f"{o}.multiSelect: muss true oder false sein")
        opts = q.get("options")
        if not isinstance(opts, list) or not 2 <= len(opts) <= 4:
            anzahl = len(opts) if isinstance(opts, list) else "keine"
            f.append(f"{o}.options: {anzahl} statt 2–4")
            continue
        labels = []
        for j, p in enumerate(opts):
            if not _text(p.get("label")):
                f.append(f"{o}.options[{j}].label: fehlt")
            if not isinstance(p.get("description"), str):
                f.append(f"{o}.options[{j}].description: fehlt")
            if "text_noetig" in p and not isinstance(p["text_noetig"], bool):
                f.append(f"{o}.options[{j}].text_noetig: muss true oder false sein")
            labels.append(str(p.get("label", "")))
        if len(set(labels)) != len(labels):
            f.append(f"{o}.options: Labels doppelt")
        empf = [j for j, l in enumerate(labels) if EMPFOHLEN in l]
        if len(empf) > 1:
            f.append(f"{o}.options: mehr als eine Option {EMPFOHLEN}")
        elif empf and empf[0] != 0:
            f.append(f"{o}.options: {EMPFOHLEN} muss die erste Option sein")
    return f, w


def pruefe_auftrag(d: dict) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für den Inhalt einer auftrag.json."""
    f: list[str] = []
    w: list[str] = []
    if d.get("version") != 1:
        f.append(f"version: {d.get('version')!r} statt 1")
    if not str(d.get("laufordner", "")).startswith("/"):
        f.append("laufordner: muss ein absoluter Pfad sein")
    if not _text(d.get("kandidat")):
        f.append("kandidat: fehlt")
    if d.get("sprache") not in ("de", "en"):
        f.append(f"sprache: {d.get('sprache')!r} statt 'de' oder 'en'")
    reihe = d.get("reihenfolge")
    if not isinstance(reihe, list) or not reihe or reihe != [s for s in SKILLS if s in reihe]:
        f.append(f"reihenfolge: {reihe!r} – erlaubt sind {list(SKILLS)} in dieser Reihenfolge")
        reihe = []
    fig = d.get("figma", {})
    if not isinstance(fig, dict) or not isinstance(fig.get("aktiv"), bool):
        f.append("figma.aktiv: muss true oder false sein")
    elif fig["aktiv"]:
        m = FIGMA_LINK.match(str(fig.get("link") or ""))
        if not m:
            f.append("figma.link: kein figma.com/design-Link mit node-id der Zielseite")
        seite = str(fig.get("seite_id") or "")
        if not SEITE.match(seite):
            f.append("figma.seite_id: fehlt (Form 12:34)")
        elif m and seite != f"{m.group(1)}:{m.group(2)}":
            f.append("figma.seite_id: passt nicht zur node-id im Link")
    mat = d.get("material", {})
    if not isinstance(mat, dict):
        f.append("material: muss ein Objekt sein")
        mat = {}
    for k in mat:
        if k not in MATERIAL:
            f.append(f"material.{k}: unbekannt")
    if not (mat.get("lebenslauf") or mat.get("linkedin_export")):
        f.append("material: weder lebenslauf noch linkedin_export – ohne eins von beiden kein Lauf")
    for k in d.get("ohne", []):
        if k not in MATERIAL:
            f.append(f"ohne: {k!r} ist kein Materialposten")
        elif mat.get(k):
            w.append(f"ohne: {k!r} steht auch unter material")
    for s in d.get("entscheidungen", {}):
        if s not in SKILLS:
            f.append(f"entscheidungen.{s}: unbekannter Skill")
    status = d.get("status", {})
    for s in reihe:
        st = status.get(s) if isinstance(status, dict) else None
        if not isinstance(st, dict):
            f.append(f"status.{s}: fehlt")
            continue
        for phase in ("vorbereiten", "bauen"):
            if st.get(phase) not in STATUS:
                f.append(f"status.{s}.{phase}: {st.get(phase)!r} ist keiner von {sorted(STATUS)}")
        if st.get("bauen") == "fertig" and st.get("vorbereiten") != "fertig":
            f.append(f"status.{s}: gebaut, aber nicht vorbereitet")
    return f, w


def pruefe_uebergabe(text: str) -> list[str]:
    """Fehler für eine uebergabe.md: alle Abschnitte da, in dieser Reihenfolge."""
    stellen = [text.find("\n" + h + "\n") for h in UEBERGABE]
    fehlen = [h for h, s in zip(UEBERGABE, stellen) if s < 0]
    if fehlen:
        return [f"Abschnitt fehlt: {h}" for h in fehlen]
    if stellen != sorted(stellen):
        return ["Abschnitte nicht in der Reihenfolge " + " · ".join(UEBERGABE)]
    return []


def _lade(datei: Path, f: list[str]):
    try:
        return json.loads(datei.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        f.append(f"{datei.name}: nicht lesbar – {e}")
        return None


def pruefe_ordner(lauf: Path, dateien: bool = True) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für einen ganzen Laufordner."""
    f: list[str] = []
    w: list[str] = []
    datei = lauf / "auftrag.json"
    if not datei.exists():
        return [f"{datei}: fehlt"], w
    auftrag = _lade(datei, f)
    if auftrag is not None:
        fa, wa = pruefe_auftrag(auftrag)
        f += [f"auftrag.json: {x}" for x in fa]
        w += [f"auftrag.json: {x}" for x in wa]
        if dateien:
            for k in PFADE:
                v = auftrag.get("material", {}).get(k)
                if _text(v) and not (lauf / v).exists():
                    f.append(f"auftrag.json: material.{k}: {v} gibt es im Laufordner nicht")
    for skill, kurz in SKILLS.items():
        fr = lauf / kurz / "fragen.json"
        if fr.exists():
            d = _lade(fr, f)
            if d is not None:
                ff, ww = pruefe_fragen(d)
                if d.get("skill") in SKILLS and d.get("skill") != skill:
                    ff.append(f"skill: {d.get('skill')!r}, erwartet {skill!r}")
                f += [f"{kurz}/fragen.json: {x}" for x in ff]
                w += [f"{kurz}/fragen.json: {x}" for x in ww]
        ue = lauf / kurz / "uebergabe.md"
        if ue.exists():
            f += [f"{kurz}/uebergabe.md: {x}"
                  for x in pruefe_uebergabe("\n" + ue.read_text(encoding="utf-8") + "\n")]
    return f, w


def main(args: list[str]) -> int:
    pfade = [a for a in args if not a.startswith("--")]
    if len(pfade) != 1:
        print(__doc__)
        return 2
    fehler, warnungen = pruefe_ordner(Path(pfade[0]), dateien="--ohne-dateien" not in args)
    for x in warnungen:
        print(f"Warnung: {x}")
    for x in fehler:
        print(f"FEHLER: {x}")
    if fehler:
        print(f"FEHLER — {len(fehler)} Stelle(n)")
        return 1
    print("Lauf in Ordnung")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Selbsttest – nur noch das Beispiel fehlt**

Run: `python3 $BM/scripts/selbsttest.py`
Expected: genau eine Zeile `FEHLER: …/beispiel/lauf fehlt`, Exit 1. Jede andere `FEHLER`-Zeile ist ein Fehler in `pruefe_lauf.py` – beheben, bevor es weitergeht.

- [ ] **Step 5: Beispiel-Lauf anlegen**

`…/beispiel/lauf/auftrag.json`:

```json
{
  "version": 1,
  "laufordner": "/Users/beispiel/Desktop/Timo Muster",
  "kandidat": "Timo Muster",
  "sprache": "de",
  "reihenfolge": ["newmonday-cv", "newmonday-skillmatrix", "newmonday-portfolio"],
  "figma": {
    "aktiv": true,
    "link": "https://www.figma.com/design/AbCdEf123456/Bewerbermappen?node-id=12-34",
    "file_key": "AbCdEf123456",
    "seite_id": "12:34",
    "neues_file": false
  },
  "material": {
    "lebenslauf": "eingang/lebenslauf.pdf",
    "linkedin_url": "https://www.linkedin.com/in/timo-muster",
    "portfolio_url": "https://timo-muster.de",
    "logos": "eingang/logos/",
    "screens": "eingang/screens/"
  },
  "ohne": ["linkedin_export"],
  "entscheidungen": {
    "newmonday-cv": {
      "nm_rolle": "User Experience Design Specialist",
      "nm_start": "Oktober 2026",
      "fachfremd": "Zivildienst, DRK Braunschweig (2013 – 2014)"
    },
    "newmonday-skillmatrix": {
      "verfuegbar_ab": "sofort",
      "freigabe": "Ich möchte etwas ändern: Figma / FigJam auf 5 Punkte, Service Design raus"
    },
    "newmonday-portfolio": {
      "projekte": "Samsung Circle, Prectavi, NMVS Core",
      "statement": "Fläche leer lassen"
    }
  },
  "status": {
    "newmonday-cv": {"vorbereiten": "fertig", "bauen": "fertig", "fehler": null},
    "newmonday-skillmatrix": {"vorbereiten": "fertig", "bauen": "offen", "fehler": null},
    "newmonday-portfolio": {"vorbereiten": "fertig", "bauen": "offen", "fehler": null}
  }
}
```

`…/beispiel/lauf/cv/fragen.json`:

```json
{
  "skill": "newmonday-cv",
  "kandidat": "Timo Muster",
  "texte": [],
  "luecken": [],
  "fragen": [
    {
      "id": "nm_rolle",
      "question": "Wie heißt die Rolle bei New Monday?",
      "header": "NM-Rolle",
      "multiSelect": false,
      "options": [
        {"label": "User Experience Design Specialist (Empfohlen)", "description": "UX-Lebenslauf: Konzeption, Research, Prototyping in allen Stationen"},
        {"label": "Software Development Specialist", "description": "Entwicklerrolle"}
      ]
    },
    {
      "id": "nm_start",
      "question": "Ab wann ist Timo bei New Monday?",
      "header": "NM-Start",
      "multiSelect": false,
      "options": [
        {"label": "September 2026 (Empfohlen)", "description": "der laufende Monat"},
        {"label": "Oktober 2026", "description": "der folgende Monat"}
      ]
    },
    {
      "id": "fachfremd",
      "question": "Welche fachfremden Stationen sollen mit rein?",
      "header": "Fachfremd",
      "multiSelect": true,
      "options": [
        {"label": "Verkäufer, Media Markt (2014 – 2016)", "description": "Nebenjob im Studium; ohne ihn keine Lücke"},
        {"label": "Zivildienst, DRK Braunschweig (2013 – 2014)", "description": "ohne ihn 12 Monate Lücke vor dem Studium"}
      ]
    }
  ]
}
```

`…/beispiel/lauf/skillmatrix/fragen.json`:

```json
{
  "skill": "newmonday-skillmatrix",
  "kandidat": "Timo Muster",
  "texte": [
    "**Hero-Beschreibung** (generiert, bitte freigeben): „Ich gestalte digitale Produkte von der Research-Phase bis zur Umsetzung, zuletzt für Versicherer und Energieversorger.“\n\n**Schwerpunkte:** UX Research · Design Systems · Prototyping",
    "| Kategorie | Attribut | Punkte | Beleg |\n|---|---|---|---|\n| Strategie & Research | User Interviews | 5 | 6 Jahre, 3 Stationen |\n| Strategie & Research | Service Design | 3 | ein Portfolio-Case |\n| Design Systems | Design Tokens | 4 | Design-System bei X |",
    "| Tool | Punkte | Beleg |\n|---|---|---|\n| Figma / FigJam | 4 | alle Stationen seit 2019 |"
  ],
  "luecken": [
    {"was": "Profilfoto", "folge": "Das beste Foto (LinkedIn) hat nach dem Kopfzuschnitt 48 dpi – die Fotokarte wirkt sichtbar weich.", "form": "Bilddatei, Porträt, mindestens 1 000 px breit"}
  ],
  "fragen": [
    {
      "id": "verfuegbar_ab",
      "question": "Ab wann ist Timo verfügbar?",
      "header": "Verfügbar",
      "multiSelect": false,
      "options": [
        {"label": "ab sofort (Empfohlen)", "description": "Badge: VERFÜGBAR AB SOFORT"},
        {"label": "Oktober 2026", "description": "Badge: VERFÜGBAR AB OKTOBER 2026"},
        {"label": "November 2026", "description": "Badge: VERFÜGBAR AB NOVEMBER 2026"}
      ]
    },
    {
      "id": "freigabe",
      "question": "Passen Auswahl und Bewertung der Skill Matrix so?",
      "header": "Freigabe",
      "multiSelect": false,
      "options": [
        {"label": "Ja, so bauen (Empfohlen)", "description": "Tabelle und Hero-Beschreibung wie oben"},
        {"label": "Ich möchte etwas ändern", "description": "Ich frage danach, was anders sein soll", "text_noetig": true}
      ]
    }
  ]
}
```

`…/beispiel/lauf/portfolio/fragen.json`:

```json
{
  "skill": "newmonday-portfolio",
  "kandidat": "Timo Muster",
  "texte": [],
  "luecken": [
    {"was": "Screens NMVS Core", "folge": "Lösungs- und Abschlussseite von NMVS Core zeigen nur die Markenfläche – die Screens im Portfolio sind 640 px breit.", "form": "Einzelne Exporte, ein Screen je Datei, Desktop ab 1 120 px Breite"}
  ],
  "fragen": [
    {
      "id": "projekte",
      "question": "Welche Projekte sollen ins Portfolio, in dieser Reihenfolge?",
      "header": "Projekte",
      "multiSelect": true,
      "options": [
        {"label": "Samsung Circle (Empfohlen)", "description": "stärkste Beleglage: Case-Text und 7 Screens"},
        {"label": "Prectavi", "description": "Case-Text und 5 Screens"},
        {"label": "NMVS Core", "description": "Case-Text, Screens nur 640 px breit"},
        {"label": "Relaunch Stadtwerke", "description": "nur zwei Sätze, keine Screens"}
      ]
    },
    {
      "id": "statement",
      "question": "Im Material steht kein Statement für Seite 4 – wie soll es aussehen?",
      "header": "Statement",
      "multiSelect": false,
      "options": [
        {"label": "Ich gebe es ein", "description": "Ich frage danach nach dem Wortlaut", "text_noetig": true},
        {"label": "Fläche leer lassen", "description": "Das Layout trägt eine leere Statement-Seite"}
      ]
    }
  ]
}
```

`…/beispiel/lauf/cv/uebergabe.md`:

```markdown
# Übergabe newmonday-cv

## Dateien
- ausgabe/New-Monday - Timo Muster - UX Designer - CV.pdf
- ausgabe/New-Monday - T. M. - UX Designer - CV.pdf
- Figma: https://www.figma.com/design/AbCdEf123456/Bewerbermappen?node-id=12-40

## Zur Freigabe
Kurzprofil (generiert): „Ich arbeite seit 2019 als UX Designer …“

## Quellen weichen ab
- Zeitraum Cocomore AG: Lebenslauf „11/2021 – 04/2022“ / Portfolio „2021“ → im Dokument: Lebenslauf

## Hinweise
- Letzte eigene Station endet jetzt im August 2026 (Monat vor dem NM-Start) – bitte bestätigen.
- Weggefallen: Realschulabschluss (nur der neueste Schulabschluss steht drin).

## Ohne Rückfrage entschieden
–

## Fehlt noch
Folgende Firmenlogos fehlen: TEAM GmbH – einfügen, um Lebenslauf zu vervollständigen
```

- [ ] **Step 6: Selbsttest – grün**

Run: `python3 $BM/scripts/selbsttest.py && python3 $BM/scripts/pruefe_lauf.py $BM/beispiel/lauf --ohne-dateien`
Expected:
```
Selbsttest bestanden (20 Fälle, Übergabe, Laufordner, Beispiel)
Lauf in Ordnung
```

- [ ] **Step 7: `references/formate.md` schreiben**

`newmonday-bewerber/skills/newmonday-bewerbermappe/references/formate.md`:

````markdown
# Formate im Gesamtlauf

Über diese vier Dateien reden Orchestrator und Subagenten miteinander. Ein
vollständiger Beispiel-Lauf (Kandidat „Timo Muster“, erfunden) liegt in
`beispiel/lauf/`. `scripts/pruefe_lauf.py <laufordner>` prüft jede dieser
Dateien, die es im Laufordner gibt; `scripts/selbsttest.py` prüft das Beispiel.

```
<Vorname Nachname>/
  eingang/          gelieferte Dateien, unverändert (logos/, screens/, zertifikate/)
  auftrag.json      schreibt nur der Orchestrator
  cv/               arbeit/, cv.json, fragen.json, notizen.md, uebergabe.md
  skillmatrix/      arbeit/, skillmatrix.json, fragen.json, notizen.md, uebergabe.md
  portfolio/        arbeit/, portfolio.json, fragen.json, notizen.md, uebergabe.md
  ausgabe/          alle PDFs
```

Die Unterordner heißen `cv`, `skillmatrix` und `portfolio` – je Skill einer, weil
alle drei Skills nach `arbeit/fotos/`, `arbeit/text.txt` und
`arbeit/figma_plan.json` schreiben.

## `auftrag.json` — schreibt nur der Orchestrator

Beispiel: `beispiel/lauf/auftrag.json`.

| Feld | Inhalt |
|---|---|
| `version` | `1` |
| `laufordner` | absoluter Pfad |
| `kandidat` | „Vorname Nachname“ |
| `sprache` | `de` oder `en`, für alle drei Dokumente |
| `reihenfolge` | `["newmonday-cv", "newmonday-skillmatrix", "newmonday-portfolio"]` |
| `figma.aktiv` | `false` = keine Frames |
| `figma.link` | Link auf die Kandidatenseite mit `node-id` (`…?node-id=12-34`) – den geben die Skills als ihren Figma-Link aus Schritt 0 |
| `figma.file_key`, `figma.seite_id` | Teil nach `/design/`; Seiten-ID `12:34` (passt zur `node-id`) |
| `figma.neues_file` | `true`, wenn der Orchestrator das File angelegt hat |
| `material.*` | `lebenslauf`, `linkedin_export`, `portfolio_pdf`, `foto`: Dateien; `logos`, `screens`, `zertifikate`: Ordner; `linkedin_url`, `xing_url`, `portfolio_url`: Adressen; `kundentexte`: Datei oder Text. Pfade relativ zum Laufordner. Nicht Vorhandenes fehlt oder ist `null`. |
| `ohne` | Materialposten, die der Nutzer bewusst nicht liefert – werden nicht mehr erbeten |
| `entscheidungen.<skill>.<id>` | Antwort auf die Frage mit dieser `id` aus `<skill>/fragen.json`, wörtlich (siehe unten) |
| `status.<skill>` | `vorbereiten` und `bauen`: `offen`, `fertig`, `fehler` oder `ausgelassen`; `fehler`: Grund oder `null` |

**Antworten** stehen so, wie `AskUserQuestion` sie zurückgibt: das Label ohne
„ (Empfohlen)“; bei mehreren Haken alle gewählten Labels, wie das Werkzeug sie
liefert; bei „Other“ der eingegebene Text. Hat die gewählte Option
`"text_noetig": true`, steht dort `<Label>: <Text>`. Fehlt eine `id`, wurde die
Frage nicht gestellt.

## `fragen.json` — schreibt der Subagent beim Vorbereiten

Beispiele: `beispiel/lauf/cv/fragen.json`, `…/skillmatrix/fragen.json`,
`…/portfolio/fragen.json`.

```json
{
  "skill": "newmonday-cv",
  "kandidat": "Timo Muster",
  "texte": ["Markdown, das vor den Fragen gezeigt wird"],
  "luecken": [{ "was": "Profilfoto", "folge": "…", "form": "…" }],
  "fragen": [{ "id": "nm_rolle", "question": "…?", "header": "NM-Rolle",
               "multiSelect": false,
               "options": [{ "label": "… (Empfohlen)", "description": "…" },
                           { "label": "…", "description": "…", "text_noetig": true }] }]
}
```

- **`fragen`**: höchstens vier – so viele nimmt ein `AskUserQuestion`-Aufruf.
  Felder wie bei `AskUserQuestion`, dazu `id` (snake_case, eindeutig). Jede
  `question` endet mit „?“ und kommt nur einmal vor – die Antworten kommen nach
  Fragetext zurück. `header` höchstens 12 Zeichen (länger ist eine Warnung, das
  Werkzeug kürzt). 2–4 Optionen, Labels eindeutig; „(Empfohlen)“ höchstens
  einmal und dann an erster Stelle. Wortlaut und Optionen so, wie der Skill die
  Frage im Einzellauf stellt.
- **`text_noetig`** (optional, an einer Option): Wer sie wählt, wird im
  Fließtext nach dem Text gefragt – für „Ich möchte etwas ändern“ oder „Ich gebe
  es ein“.
- **`texte`**: Markdown-Blöcke, die der Nutzer vor den Fragen sehen muss, um sie
  zu beantworten – etwa die Matrix-Tabelle. Sonst leer.
- **`luecken`**: Material, nach dem der Skill im Einzellauf fragen würde. `was`
  ist der Posten; gleiche Posten heißen in allen Skills gleich, damit der
  Orchestrator sie zusammenlegen kann: „Profilfoto“, „Lebenslauf“,
  „LinkedIn-Export“, „Zertifikate“, „Screens <Projekt>“, „Logo <Firma>“.
  `folge` sagt, was im Dokument passiert, wenn es nicht kommt; `form`, in
  welcher Form es kommen soll. Nichts, was unter `ohne` steht.

## `notizen.md` — schreibt der Subagent beim Vorbereiten

Freies Markdown. Alles, was der Bauen-Subagent aus dem Vorbereiten braucht und
was nicht in `fragen.json` steht; welche Punkte das je Skill sind, steht in
dessen Abschnitt „Im Gesamtlauf“. Pfade relativ zum Skill-Ordner. Der
Bauen-Subagent leitet nichts neu her, was hier steht.

## `uebergabe.md` — schreibt der Subagent beim Bauen

Sechs Abschnitte, genau diese Überschriften, in dieser Reihenfolge – der
Orchestrator setzt die Gesamtübergabe Abschnitt für Abschnitt daraus zusammen.
Ist ein Abschnitt leer, steht darunter „–“. Beispiel:
`beispiel/lauf/cv/uebergabe.md`.

```
# Übergabe <skill>

## Dateien
PDF-Dateien in ausgabe/ und der Figma-Link auf den ersten Frame (…?node-id=…)

## Zur Freigabe
Alles, was der Skill selbst formuliert hat, im Wortlaut

## Quellen weichen ab
- <Feld>: <Quelle> „…“ / <Quelle> „…“ → im Dokument: <Quelle>

## Hinweise
Der Rest der Übergabe des Skills

## Ohne Rückfrage entschieden
- <Stelle>: was genommen wurde und warum

## Fehlt noch
Die Schlusszeilen des Skills, wörtlich
```
````

- [ ] **Step 8: Nachträge an die Spec hängen**

Ans Ende von `docs/superpowers/specs/2026-09-29-newmonday-bewerbermappe-design.md`:

```markdown

## Nachträge aus der Planung (29.09.2026)

Sie gehen den Abschnitten oben vor.

- **Zwei kleine Skripte statt keinem.** `scripts/pruefe_lauf.py` prüft
  `auftrag.json`, jede `fragen.json` und jede `uebergabe.md` – der Orchestrator
  braucht das zur Laufzeit, weil eine fehlerhafte `fragen.json` den
  `AskUserQuestion`-Aufruf scheitern ließe. `scripts/testmaterial.sh` rendert
  den Beispiel-Lebenslauf aus `newmonday-cv` als Test-Eingang ohne echte
  Kandidatendaten. Dazu `scripts/selbsttest.py` und ein erfundener Beispiel-Lauf
  in `beispiel/lauf/`.
- **Figma-Ziel als Link.** Der Orchestrator schreibt nach `figma.link` einen Link
  mit der `node-id` der Kandidatenseite. Alle drei Skills legen ihre Frames schon
  heute auf die Seite, auf die ein Link mit `node-id` zeigt, rechts neben das
  Vorhandene – an ihrer Figma-Logik ändert sich dadurch nichts. `figma.seite_id`
  bleibt als Kontrollwert und muss zur `node-id` passen.
- **`uebergabe.md` hat sechs feste Abschnitte**: Dateien, Zur Freigabe, Quellen
  weichen ab, Hinweise, Ohne Rückfrage entschieden, Fehlt noch. Der Orchestrator
  setzt die Gesamtübergabe Abschnitt für Abschnitt daraus zusammen.
- **Antworten wörtlich.** `entscheidungen.<skill>.<id>` hält die Antwort so, wie
  `AskUserQuestion` sie liefert (bei mehreren Haken keine Liste). Eine Option mit
  `"text_noetig": true` lässt den Orchestrator im Fließtext nach dem Text fragen;
  gespeichert wird `<Label>: <Text>`.
- **Einfügestelle** der Abschnitte „Im Gesamtlauf“: direkt vor
  `## Gefragt wird mit Klickboxen, nicht im Fließtext` – das ist in allen drei
  Skills der Abschnitt nach „Umgebung“.
```

- [ ] **Step 9: Commit**

```bash
cd $R && git add newmonday-bewerber/skills/newmonday-bewerbermappe docs/superpowers/specs/2026-09-29-newmonday-bewerbermappe-design.md && git commit -q -F - <<'EOF'
newmonday-bewerbermappe: Formate, Laufpruefung, Beispiel-Lauf

pruefe_lauf.py prueft auftrag.json, fragen.json und uebergabe.md eines
Gesamtlaufs; selbsttest.py und beispiel/lauf/ halten die Formate fest.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 2: Orchestrator-Skill

**Files:**
- Create: `newmonday-bewerber/skills/newmonday-bewerbermappe/SKILL.md`
- Create: `newmonday-bewerber/skills/newmonday-bewerbermappe/scripts/testmaterial.sh`
- Außerhalb des Repos: Symlink `~/.claude/skills/newmonday-bewerbermappe`

**Interfaces:**
- Consumes: `scripts/pruefe_lauf.py` (CLI), `references/formate.md` aus Task 1.
- Produces: Abschnitt „Der Auftrag an die Subagenten“ in SKILL.md – die Vorlage, mit der Task 3–5 ihre Subagenten starten. Platzhalter darin: `<skill>`, `<vorbereiten|bauen>`, `<laufordner>`, `<cv|skillmatrix|portfolio>`, `<skills>`.
- Produces: `bash scripts/testmaterial.sh <zielordner>` → `<zielordner>/lebenslauf.pdf` (Florian Feiler, UX Designer, mit Foto).

- [ ] **Step 1: Prüfung schreiben, die noch scheitert**

Run:
```bash
python3 - "$BM" <<'EOF'
import re, sys, pathlib
bm = pathlib.Path(sys.argv[1])
t = (bm / "SKILL.md").read_text(encoding="utf-8")
m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", t)
assert m and m.group(1) == "newmonday-bewerbermappe", "Frontmatter/Name"
assert len(m.group(2)) <= 1024, f"description {len(m.group(2))} Zeichen"
for pfad in ("references/formate.md", "scripts/pruefe_lauf.py"):
    assert pfad.split("/")[-1] in t, f"SKILL.md nennt {pfad} nicht"
for pfad in ("references/formate.md", "scripts/pruefe_lauf.py", "scripts/testmaterial.sh"):
    assert (bm / pfad).exists(), f"{pfad} fehlt"
for kopf in ("### Phase 1", "### Phase 2", "### Phase 3", "### Phase 4", "### Phase 5",
             "### Phase 6", "## Der Auftrag an die Subagenten", "## Wiederaufnahme"):
    assert kopf in t, f"Abschnitt fehlt: {kopf}"
print("SKILL.md in Ordnung,", len(m.group(2)), "Zeichen Beschreibung")
EOF
```
Expected: FAIL mit `FileNotFoundError` (SKILL.md gibt es noch nicht).

- [ ] **Step 2: `testmaterial.sh` schreiben**

`newmonday-bewerber/skills/newmonday-bewerbermappe/scripts/testmaterial.sh`:

```bash
#!/usr/bin/env bash
# Legt Testmaterial ohne echte Kandidatendaten an: den Beispiel-Lebenslauf
# aus newmonday-cv (beispiel/cv.json) als gerendertes PDF.
#
#   bash scripts/testmaterial.sh <zielordner>
#
# Ergebnis: <zielordner>/lebenslauf.pdf. Schreibt nichts in die Skill-Ordner.
set -euo pipefail
ZIEL="${1:?Zielordner fehlt}"
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CV="$(cd "$HIER/../../newmonday-cv" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
( cd "$CV" && python3 scripts/render_cv.py beispiel/cv.json "$TMP/" >/dev/null 2>&1 )
mkdir -p "$ZIEL"
mv "$TMP"/*.pdf "$ZIEL/lebenslauf.pdf"
echo "$ZIEL/lebenslauf.pdf"
```

Run: `bash $BM/scripts/testmaterial.sh $T/material && pdftotext -l 1 $T/material/lebenslauf.pdf - | head -2 && cd $R && git status --short`
Expected: `…/bewerbermappe-test/material/lebenslauf.pdf`, dann `Florian Feiler` und `UX Designer`; `git status` zeigt nur den neuen Ordner `newmonday-bewerbermappe/` (nichts in `newmonday-cv/`).

- [ ] **Step 3: `SKILL.md` schreiben**

`newmonday-bewerber/skills/newmonday-bewerbermappe/SKILL.md`:

````markdown
---
name: newmonday-bewerbermappe
description: Baut in einem Lauf alle drei New-Monday-Dokumente eines Kandidaten – Lebenslauf (vollständig und anonym), Skill Matrix und Portfolio –, jeweils als PDF und als Frames auf einer gemeinsamen Figma-Seite. Führt newmonday-cv, newmonday-skillmatrix und newmonday-portfolio nacheinander aus, stellt jede gemeinsame Frage nur einmal (Sprache, Figma, Material), prüft vorab, was an Unterlagen fehlt, und bündelt alle Entscheidungen in einer Sitzung, bevor gebaut wird. Nutze diesen Skill immer, wenn alle drei Dokumente für denselben Kandidaten entstehen sollen – "die ganze Mappe", "das komplette Set", "alle Unterlagen für <Name>", "CV, Portfolio und Skillmatrix", "Bewerbermappe", "mach alles fertig für <Name>" –, und wenn ein laufender Gesamtlauf fortgesetzt oder um nachgelieferte Logos, Screens oder Fotos ergänzt werden soll. Für genau ein Dokument sind newmonday-cv, newmonday-skillmatrix und newmonday-portfolio zuständig.
---

# New Monday Bewerbermappe

Aus den Unterlagen eines Kandidaten entstehen in einem Lauf alle drei
New-Monday-Dokumente: der Lebenslauf (vollständig und anonym), die Skill Matrix
und das Portfolio – jeweils als PDF und als Frames auf einer gemeinsamen
Figma-Seite. Dieser Skill baut selbst nichts. Er sammelt ein, prüft, fragt und
verteilt; gebaut wird von `newmonday-cv`, `newmonday-skillmatrix` und
`newmonday-portfolio`, jeder in einem eigenen Subagenten.

## Die eine Regel, die alles andere schlägt

**Gefragt wird nur hier, gebaut wird nur dort.** Subagenten können dem Nutzer
keine Fragen stellen – `AskUserQuestion` fehlt ihnen. Deshalb holt dieser Skill
jede Antwort ein, bevor ein Subagent sie braucht, und die Subagenten arbeiten nur
mit dem, was in `auftrag.json` steht. Umgekehrt schreibt dieser Skill keinen
Dokumentinhalt: keine `cv.json`, keine Matrix, keinen Kundentext, keine
Übersetzung. Was in einem Dokument steht, entscheidet der zuständige Skill nach
seinen eigenen Regeln.

Daraus folgt:

- **Jede Frage, die mehrere Skills stellen würden, kommt genau einmal** –
  Sprache, Figma-Ziel, Material, Foto, Logos.
- **Nach Phase 4 wird nicht mehr gefragt.** Wer den Entscheidungsblock
  beantwortet hat, darf weggehen.
- **Was ein Subagent ohne Rückfrage entscheiden musste, steht in der
  Übergabe** – nie still.

## Voraussetzungen

- Die drei Skills liegen neben diesem Skill. Bei der Installation per Symlink
  aus dem Repo ist das so. Im Folgenden steht `<skills>` für den absoluten Pfad
  von `${CLAUDE_SKILL_DIR}/..` – einmal mit `cd "${CLAUDE_SKILL_DIR}/.." && pwd`
  ermitteln und so in jeden Subagenten-Auftrag schreiben.
- Das `Agent`-Werkzeug, Subagent-Typ `general-purpose`.
- Für Figma: ein verbundener Figma-MCP-Server und Bearbeitungsrecht auf der
  Zieldatei. Fehlt beides, entstehen nur die PDFs.

## Gefragt wird mit Klickboxen

Wie in den drei Skills: Jede Frage mit überschaubarer Antwortmenge läuft über
`AskUserQuestion` – bis zu vier Fragen je Aufruf, die wahrscheinlichste Option
zuerst, mit „(Empfohlen)“ im Label. Material, das der Nutzer schicken muss,
steht als Text in derselben Nachricht. Gefragt wird nur in Phase 1, 2 und 4.

## Ablauf

### Phase 1 — Eingang

Eine Nachricht. Zwei Klickboxen in einem `AskUserQuestion`-Aufruf:

```
Frage:    Sollen Lebenslauf, Skill Matrix und Portfolio auf Deutsch oder Englisch sein?
Header:   Sprache
Optionen: Deutsch | Englisch
```

```
Frage:    In welches Figma-File sollen die drei Dokumente?
Header:   Figma
Optionen: In ein bestehendes File – ich schicke den Link (Empfohlen)
        | Leg ein neues File an
```

Die Sprachfrage wird gestellt, auch wenn der Eingang eindeutig einsprachig
aussieht – ein englischer Lebenslauf kann für einen deutschen Kunden gedacht
sein. Sie gilt für alle drei Dokumente.

Daneben als Text, wörtlich so:

> Schick mir bitte:
>
> - den **Lebenslauf** als PDF,
> - den **LinkedIn-Export** als PDF (auf dem Profil: *Mehr* → *Als PDF
>   speichern*) und den **Link zum Profil** (linkedin.com/in/…) – daraus hole
>   ich auch das Foto,
> - das **Portfolio** als Link zur Website oder als PDF,
> - den **Link zum Figma-File** (figma.com/design/…), falls es ein bestehendes
>   sein soll. Ich lege darin eine Seite mit dem Namen des Kandidaten an und
>   brauche Bearbeitungsrechte.
>
> Wenn es sie gibt, spart das Zeit: Firmen- und Kundenlogos als SVG, Screenshots
> je Projekt (einzelne Exporte, ein Screen je Datei), Zertifikate als Bild oder
> PDF, ein Foto in guter Auflösung, ein paar Sätze zu jedem Kunden, ein
> Xing-Profil.

**Was mit dem Aufruf schon kam, wird nicht noch einmal erbeten.** Dateien und
Links, die schon im Chat liegen, fallen aus der Liste; eine genannte Sprache
(„auf Englisch“) ersetzt die Sprachfrage, ein mitgeschickter Figma-Link die
Figma-Frage. Ist dann nichts mehr offen, entfällt die Nachricht ganz.

### Phase 2 — Lückencheck vor dem Lesen

Alles in dieser Phase erledigt dieser Skill selbst, ohne Subagenten.

1. **Material zuordnen.** Jede Datei nach ihrem Inhalt, nicht nach dem Namen:
   `pdftotext -l 1 <datei> - | head -40`. Ein LinkedIn-Export trägt auf Seite 1
   „Kontakt“ bzw. „Contact“, „Top-Kenntnisse“ bzw. „Top Skills“ und eine
   `linkedin.com/in/`-Adresse. Bleibt eine Zuordnung unklar, im Fließtext der
   Lücken-Nachricht nachfragen.
2. **Kandidatenname** aus der ersten Seite von Lebenslauf oder LinkedIn-Export.
   Bleibt der Text leer (als Bild gesetztes PDF), die erste Seite als Bild lesen.
   Das ist die einzige Inhaltsarbeit dieses Skills; der Name gibt Laufordner und
   Figma-Seite ihren Namen.
3. **Ablageort.** Der Laufordner heißt wie der Kandidat und liegt im
   Arbeitsverzeichnis – außer das Arbeitsverzeichnis gehört zum Skill-Repo:

   ```bash
   top=$(git rev-parse --show-toplevel 2>/dev/null) && [ -d "$top/newmonday-bewerber/skills" ] && echo "Skill-Repo"
   ```

   Dann kommen Kandidatendaten nicht dorthin, und die Lücken-Nachricht trägt
   eine Klickbox mehr – allein gestellt, wenn sonst nichts fehlt:

   ```
   Frage:    Wohin soll der Laufordner für <Vorname Nachname>?
   Header:   Ablage
   Optionen: Schreibtisch (Empfohlen) | Downloads
   ```

   Über „Other“ nennt der Nutzer einen eigenen Ort. Existiert der Laufordner
   schon mit einer `auftrag.json`, ist das eine Wiederaufnahme – siehe unten.
4. **Umgebung.** Einmal je Skill:

   ```bash
   python3 <skills>/newmonday-cv/scripts/pruefe_umgebung.py
   python3 <skills>/newmonday-skillmatrix/scripts/pruefe_umgebung.py
   python3 <skills>/newmonday-portfolio/scripts/pruefe_umgebung.py
   ```

   Meldet eins eine Lücke, gehört der Installationsbefehl aus der Ausgabe in die
   Lücken-Nachricht.
5. **Figma lesen.** Per ToolSearch `whoami figma` suchen und `whoami` aufrufen.
   Antworten zwei Figma-Server, zählt der, dessen `whoami` durchläuft; ein nicht
   angemeldeter zweiter Server wird ignoriert. Dann:
   - Link ist eine Design-Datei: `figma.com/design/…`. `/board/`, `/slides/`,
     `/make/`, `/proto/` gehen nicht – das ist eine Lücke.
   - Datei lesbar: `get_metadata` mit dem `fileKey` (der Teil nach `/design/`).
   - Bei „neues File“: den Plan aus `whoami` nehmen, dessen Seat nicht „View“ ist.
     Gibt es mehrere, kommt eine Klickbox mit den Plannamen in die
     Lücken-Nachricht.
6. **Die Lücken-Nachricht** – nur, wenn etwas fehlt. Jeder fehlende Posten mit
   seiner Folge, in diesem Wortlaut:

   | Fehlt | Folge |
   |---|---|
   | Lebenslauf | Der Lebenslauf entsteht allein aus dem LinkedIn-Export, und die erste Fotoquelle fehlt. |
   | LinkedIn-Export | Firmennamen, Zeiträume und Rollen kommen nur aus dem Lebenslauf – vollständige Firmierungen und feiner aufgeteilte Stationen fehlen oft. |
   | LinkedIn-Link | Kein automatisches Profilfoto von LinkedIn und kein LinkedIn-Verweis im Lebenslauf. |
   | Portfolio | Das Portfolio entsteht nur aus Lebenslauf und LinkedIn, mit Platzhaltern statt Screens; Lebenslauf und Skill Matrix fehlt die dritte Quelle. |
   | Figma-Link (bei „bestehendes File“) | Ich lege ein neues Figma-File an. |
   | Figma nicht verbunden oder falscher Dateityp | Es entstehen nur die PDFs, keine Frames. |
   | Umgebung | <Skill> kann nicht rendern: <was fehlt>. Einrichten mit: `<Befehl>` |

   Dazu eine Klickbox:

   ```
   Frage:    Kannst du das nachliefern?
   Header:   Nachliefern
   Optionen: Ich liefere nach (Empfohlen) | Ohne weitermachen
   ```

   Weder Lebenslauf noch LinkedIn-Export: Dann gibt es keine Klickbox, sondern
   nur die Bitte darum. Ohne eins von beiden beginnt kein Lauf.

   „Ich liefere nach“: auf das Material warten und die Punkte 1–6 für das
   Nachgelieferte wiederholen. „Ohne weitermachen“: Die Posten kommen in
   `auftrag.json` unter `ohne` und werden in diesem Lauf nicht mehr
   angesprochen – auch von den Skills nicht. Das optionale Material aus Phase 1
   ist nie eine Lücke.
7. **Figma-Zielseite anlegen – zugleich der Schreibtest.** Nur wenn Figma
   bleibt. Erst den Skill `figma:figma-use` laden, dann per `use_figma`:
   - Link mit `node-id` → die Seite dieses Knotens:

     ```js
     let n = await figma.getNodeByIdAsync("<node-id mit Doppelpunkt, z. B. 12:34>");
     while (n && n.type !== "PAGE") n = n.parent;
     return { seite: n ? n.id : null };
     ```

   - sonst die Seite „Vorname Nachname“ – vorhanden (früherer Lauf) oder neu:

     ```js
     const NAME = "<Vorname Nachname>";
     let seite = figma.root.children.find(p => p.name === NAME);
     const neu = !seite;
     if (neu) { seite = figma.createPage(); seite.name = NAME; }
     return { seite: seite.id, neu };
     ```

   - „neues File“: zuerst den Skill `figma:figma-create-new-file` laden, das File
     `Bewerbermappe — Vorname Nachname` mit `create_new_file` im Plan aus Punkt 5
     anlegen und dessen erste, leere Seite in „Vorname Nachname“ umbenennen,
     statt eine zweite anzulegen.

   Aus der Seiten-ID `12:34` wird der Link, den alle drei Skills bekommen:
   `https://www.figma.com/design/<fileKey>/<Name aus dem Link oder "Bewerbermappe">?node-id=12-34`.
   Alle drei legen ihre Frames auf die Seite, auf die ein Link mit `node-id`
   zeigt, jeweils rechts neben das Vorhandene – an ihnen ändert sich dafür
   nichts.

   Scheitert das Schreiben (nur Leserecht, Datei gesperrt), eine Klickbox:
   *Ich richte es ein (Empfohlen)* | *Ohne Figma weiter*. Das ist die einzige
   Frage nach der Lücken-Nachricht, und sie kommt nur in diesem Fall. Bricht der
   Nutzer den Lauf später ab, bleibt die leere Seite stehen – das ist in Kauf
   genommen.
8. **Laufordner anlegen und `auftrag.json` schreiben.** Aufbau und Felder:
   `references/formate.md`. Die Dateien werden nach `eingang/` kopiert, nicht
   verschoben (Logos nach `eingang/logos/`, Screens nach `eingang/screens/`, je
   Projekt ein Unterordner, wenn der Nutzer sie so geliefert hat, Zertifikate
   nach `eingang/zertifikate/`). Alle Status auf `offen`. Dann:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/pruefe_lauf.py "<laufordner>"
   ```

   Weiter erst bei „Lauf in Ordnung“.

### Phase 3 — Vorbereiten

Je Skill in der Reihenfolge aus `auftrag.json` (`newmonday-cv`,
`newmonday-skillmatrix`, `newmonday-portfolio`) ein Subagent mit Phase
*vorbereiten* – Auftrag siehe unten, im Vordergrund, einer nach dem anderen.
Nach jedem:

1. `pruefe_lauf.py` laufen lassen. Meldet es Fehler in der `fragen.json` dieses
   Skills, einmal nachfassen – derselbe Auftrag mit der Zeile
   `Nur fragen.json korrigieren. Fehler: <Zeilen aus pruefe_lauf>`. Bleibt es
   falsch, gilt die Vorbereitung als gescheitert.
2. Status in `auftrag.json` setzen: `fertig` oder `fehler` (Grund nach `fehler`).
3. Eine Statuszeile an den Nutzer: „Lebenslauf gelesen – 3 Fragen, 1 Lücke.“

Ein gescheiterter Skill hält die anderen nicht auf.

### Phase 4 — Entscheidungen

Eine Sitzung, in dieser Reihenfolge:

1. **Lücken.** Die `luecken` aller drei `fragen.json`, zusammengeführt:
   Gleiches `was` erscheint einmal, mit der Folge je Dokument („Profilfoto –
   Lebenslauf: die Fotospalte bleibt leer; Skill Matrix: die Karte zeigt nur den
   Verlauf“). Dazu gescheiterte Vorbereitungen mit Grund. Ein
   `AskUserQuestion`-Aufruf:
   - bei Lücken: *Ich liefere nach (Empfohlen)* | *Ohne weitermachen*
   - je gescheitertem Skill: *Ohne <Dokument> weiter (Empfohlen)* | *Abbrechen*

   Wird nachgeliefert: Dateien nach `eingang/`, `material` ergänzen, bei den
   Skills, die die Lücke gemeldet haben, `vorbereiten` auf `offen` und Phase 3
   für sie wiederholen – neues Material kann ihre Fragen ändern. Dann zurück an
   den Anfang dieser Phase; Lücken, die schon beantwortet sind, kommen nicht
   wieder. „Ohne weitermachen“: die Posten unter `ohne`. „Ohne <Dokument>“:
   dessen Status auf `ausgelassen`.
2. **Texte.** Alle `texte` in Bau-Reihenfolge, je Skill unter einer
   Zwischenzeile („**Skill Matrix**“). Vor allem Hero-Beschreibung, Matrix- und
   Tools-Tabelle – der Nutzer braucht sie, um die Freigabe-Frage zu beantworten.
3. **Fragen.** Je Skill ein `AskUserQuestion`-Aufruf mit seinen `fragen`, in
   Bau-Reihenfolge. Übergeben werden `question`, `header`, `multiSelect` und
   `options` mit `label` und `description`; `id` und `text_noetig` bleiben
   draußen. Skills ohne Fragen werden übersprungen.
4. **Antworten ablegen** in `auftrag.json` unter
   `entscheidungen.<skill>.<id>`. Die Antworten kommen nach Fragetext zurück;
   die `id` ist die der Frage mit diesem Text. Gespeichert wird wörtlich, was
   zurückkommt – ohne „ (Empfohlen)“, bei mehreren Haken so, wie das Werkzeug
   sie liefert, bei „Other“ der eingegebene Text. Hat die gewählte Option
   `"text_noetig": true`, im Fließtext nach dem Text fragen und
   `<Label>: <Text>` speichern. Danach `pruefe_lauf.py`.
5. **Ansage:** „Ab hier läuft alles ohne Rückfrage – erst der Lebenslauf, dann
   die Skill Matrix, dann das Portfolio. Das dauert eine Weile; am Ende kommt
   eine Übergabe.“

### Phase 5 — Bauen

Je Skill, dessen `vorbereiten` auf `fertig` und `bauen` auf `offen` steht, in
Bau-Reihenfolge ein Subagent mit Phase *bauen*. Nie zwei gleichzeitig: Alle drei
schreiben in dieselbe Figma-Seite und dieselbe Logobibliothek. Nach jedem:
`pruefe_lauf.py`, Status setzen, die gemeldeten PDFs in `ausgabe/` nachsehen,
eine Statuszeile („Lebenslauf fertig – 2 PDFs, 4 Frames“). Scheitert einer, geht
es mit dem nächsten weiter; nachgefragt wird nicht.

### Phase 6 — Gesamtübergabe

Die drei `uebergabe.md` ganz lesen. Sie haben dieselben sechs Abschnitte
(`references/formate.md`), und die Übergabe setzt sich Abschnitt für Abschnitt
daraus zusammen, in einer Nachricht:

1. **Fertig: Vorname Nachname** – die Dateien aus `ausgabe/` und der Link auf die
   Figma-Seite.
2. **Zur Freigabe** – je Dokument, was dort steht, im Wortlaut: Kurzprofil,
   Hero-Beschreibung und die endgültige Matrix, Cover-Titel, KI- und
   Prozesstexte, Kundentexte mit Quellen, KI-generierte Gebäude.
3. **Quellen weichen ab** – jede Abweichung einmal. Nennen zwei Skills dasselbe
   Feld mit denselben Werten, wird daraus eine Zeile mit der Fassung je
   Dokument. Die Regeln unterscheiden sich: Im Lebenslauf und in der Skill Matrix
   gewinnt der Lebenslauf, im Portfolio das Portfolio.
4. **Hinweise** – je Dokument der Rest, knapp.
5. **Ohne Rückfrage entschieden** – aus allen drei, mit Dokument und Stelle.
   Leer: Abschnitt weglassen.
6. **Nicht gebaut** – Dokumente mit `fehler` oder `ausgelassen`, mit Grund.
   Leer: weglassen.
7. **Ganz zum Schluss** die Zeilen aus „Fehlt noch“ aller drei, **wörtlich** und
   in Bau-Reihenfolge. Nichts dazuschreiben, nicht zusammenfassen – jeder Skill
   hat seinen Satz. Fehlt nirgends etwas, steht hier nichts.

Wurden Frames neben ältere eines früheren Laufs gelegt, steht das in den
Hinweisen: Die alten bleiben stehen, bis jemand sie löscht.

## Der Auftrag an die Subagenten

`Agent` mit `subagent_type: general-purpose`, im Vordergrund. Die spitzen
Klammern füllt dieser Skill, alles andere steht wörtlich so im Auftrag:

```
Gesamtlauf newmonday-bewerbermappe · Skill: <skill> · Phase: <vorbereiten|bauen>
Laufordner: <laufordner>
Skill-Ordner: <laufordner>/<cv|skillmatrix|portfolio>/

1. Lade den Skill <skill> mit dem Skill-Werkzeug – genau diesen Namen, ohne
   Präfix (nicht anthropic-skills:<skill>, das ist eine andere Fassung). Steht
   das Werkzeug nicht zur Verfügung: lies <skills>/<skill>/SKILL.md und setze
   ${CLAUDE_SKILL_DIR} = <skills>/<skill>.
2. Lies dort den Abschnitt „Im Gesamtlauf“. Er sagt, welche Schritte zu dieser
   Phase gehören, und geht jeder anderen Anweisung des Skills vor.
3. Allgemeine Regeln:
   - Schritt 0 des Skills entfällt. Sprache, Figma-Ziel und Material stehen in
     <laufordner>/auftrag.json; Pfade darin sind relativ zum Laufordner.
   - Kein AskUserQuestion und keine Frage an den Nutzer in deiner Antwort.
     Vorbereiten: jede Frage nach fragen.json, jede Materialbitte nach
     „luecken“. Bauen: bei Unerwartetem die Option nehmen, die der Skill
     empfiehlt, und sie in uebergabe.md unter „Ohne Rückfrage entschieden“
     notieren.
   - Formate von fragen.json, notizen.md und uebergabe.md:
     <skills>/newmonday-bewerbermappe/references/formate.md
   - Arbeitsordner ist der Skill-Ordner: arbeit/, die JSON des Skills,
     fragen.json, notizen.md und uebergabe.md liegen dort. PDFs nach
     <laufordner>/ausgabe/.
   - Figma nur, wenn figma.aktiv true ist. figma.link zeigt mit node-id auf die
     Seite, auf die alles kommt. Keine eigene Seite anlegen, nichts Vorhandenes
     anfassen.
   - Was in auftrag.json unter „ohne“ steht, nicht noch einmal erbitten.
   - Antworten: auftrag.json → entscheidungen.<skill>.<id>, wörtlich, wie der
     Nutzer sie gegeben hat; die Optionen dazu stehen in fragen.json.
   - Beim Bauen zuerst notizen.md lesen; was dort steht, nicht neu herleiten.
   - Zum Schluss: python3 <skills>/newmonday-bewerbermappe/scripts/pruefe_lauf.py
     "<laufordner>" – Fehler in deinen Dateien beheben.
4. Rückgabe, eine Zeile:
   vorbereiten → „fertig: <n> Fragen, <m> Lücken“ oder „fehler: <Grund>“
   bauen → „fertig: <PDF-Dateien>; Figma: <node-id oder –>“ oder „fehler: <Grund>“
```

Bei einem Änderungswunsch nach der Übergabe (siehe unten) kommt als letzte Zeile
dazu: `Änderung des Nutzers: <Text, wörtlich>`.

## Wiederaufnahme, Nachlieferung, Änderungen

**Wiederaufnahme.** Liegt ein Laufordner mit `auftrag.json` vor und soll es
weitergehen („mach den Lauf Timo Muster weiter“, auch in einer neuen Sitzung):
`pruefe_lauf.py`, dann `status` lesen und an der ersten offenen Stelle ansetzen –
`vorbereiten` offen → Phase 3 für diese Skills; vorbereitet, aber Antworten zu
Fragen aus `fragen.json` fehlen → Phase 4, nur für die fehlenden; `bauen` offen →
Phase 5; alles fertig → Phase 6 noch einmal. Beantwortetes wird nicht erneut
gefragt.

**Nachlieferung nach der Übergabe.** Dateien nach `eingang/`, `material`
ergänzen, den Posten aus `ohne` streichen. Dann je nach Material:

| Nachgeliefert | neu vorbereiten | neu bauen |
|---|---|---|
| Lebenslauf, LinkedIn-Export, Portfolio | alle drei (dann Phase 4 für neue Fragen) | alle drei |
| Zertifikate | Skill Matrix (dann Phase 4) | Skill Matrix |
| Foto | – | alle drei |
| Logos | – | Lebenslauf, Portfolio |
| Screens | – | Portfolio |

„Neu bauen“ heißt `bauen` auf `offen` und Phase 5 – ohne Rückfragen. Die
Frames kommen neben die alten, die Übergabe sagt das.

**Änderungswünsche nach der Übergabe** („Kurzprofil kürzer“, „Projekt X raus“):
Für das betroffene Dokument `bauen` auf `offen` und den Bauen-Auftrag mit der
Zeile `Änderung des Nutzers: …` schicken. Den Inhalt ändert der Skill, nicht
dieser.

## Was fest steht

- **Reihenfolge**: Lebenslauf → Skill Matrix → Portfolio, nacheinander, nie
  parallel.
- **Eine Sprache** für alle drei Dokumente.
- **Eine Figma-Seite je Kandidat**, alle Frames darauf. Figma hält kein PDF auf.
- **Kandidatendaten nie ins Skill-Repo** – nicht in den Skill-Ordnern, nicht im
  Repo-Arbeitsverzeichnis.
- **Kein Dokumentinhalt von diesem Skill.** Er ruft keine Render-, Logo- oder
  Figma-Skripte der drei Skills auf; einzig `pruefe_umgebung.py` in Phase 2.
- **Die Übergabe-Schlusszeilen der Skills bleiben wörtlich.**
````

- [ ] **Step 4: Prüfung aus Step 1 noch einmal – grün**

Run: denselben Befehl wie in Step 1.
Expected: `SKILL.md in Ordnung, 924 Zeichen Beschreibung` (die Zahl darf abweichen, solange ≤ 1024).

- [ ] **Step 5: Lokal installieren**

```bash
ln -s $BM ~/.claude/skills/newmonday-bewerbermappe && readlink ~/.claude/skills/newmonday-bewerbermappe
```
Expected: der Pfad von `$BM`. (Gibt es den Link schon, `ls -la ~/.claude/skills/newmonday-bewerbermappe` – er muss auf `$BM` zeigen.)

- [ ] **Step 6: [Hauptgespräch] Gegenlesen gegen die Spec**

`Agent`, `subagent_type: general-purpose`, Vordergrund, Auftrag:

```
Lies vollständig:
- /Users/florian/NW-Claude-Skills/docs/superpowers/specs/2026-09-29-newmonday-bewerbermappe-design.md
  (die „Nachträge aus der Planung“ am Ende gehen dem Rest vor)
- /Users/florian/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-bewerbermappe/SKILL.md
- /Users/florian/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-bewerbermappe/references/formate.md

Nenne jede Stelle, an der SKILL.md oder formate.md der Spec widerspricht, eine
Anforderung der Spec fehlt oder eine Anweisung zwei Lesarten zulässt. Je Fund:
Datei, Zitat (höchstens eine Zeile), was die Spec verlangt. Keine Stilkritik,
keine Verbesserungsvorschläge jenseits der Spec. Nichts ändern. Findest du
nichts, antworte „keine Abweichung“.
```

Expected: „keine Abweichung“ oder eine Liste. Jeden echten Fund in SKILL.md bzw. formate.md beheben, dann Step 4 wiederholen.

- [ ] **Step 7: Commit**

```bash
cd $R && git add newmonday-bewerber/skills/newmonday-bewerbermappe && git commit -q -F - <<'EOF'
newmonday-bewerbermappe: Orchestrator-Skill und Testmaterial

Phasen Eingang, Lueckencheck, Vorbereiten, Entscheidungen, Bauen und
Gesamtuebergabe; Subagenten-Auftrag; Wiederaufnahme und Nachlieferung.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 3: `newmonday-cv` im Gesamtlauf

**Files:**
- Modify: `newmonday-bewerber/skills/newmonday-cv/SKILL.md` – neuer Abschnitt vor `## Gefragt wird mit Klickboxen, nicht im Fließtext` (derzeit Zeile 179)

**Interfaces:**
- Consumes: Subagenten-Vorlage aus `newmonday-bewerbermappe/SKILL.md` („Der Auftrag an die Subagenten“), `pruefe_lauf.py`, `testmaterial.sh`.
- Produces: Frage-IDs `nm_rolle`, `nm_start` (immer), `fachfremd`, `weiterbildung` (bei Bedarf); `luecken`-Posten „Profilfoto“.

- [ ] **Step 1: Ausgangslage – Selbsttest grün**

Run: `cd $S/newmonday-cv && python3 scripts/selbsttest.py | tail -1`
Expected: `Selbsttest bestanden. Der Skill ist einsatzbereit.`

- [ ] **Step 2: Test-Laufordner anlegen**

```bash
bash $BM/scripts/testmaterial.sh $T/material
L=$T/lauf-cv; rm -rf "$L"; mkdir -p "$L/eingang" "$L/ausgabe"
cp $T/material/lebenslauf.pdf "$L/eingang/lebenslauf.pdf"
cat > "$L/auftrag.json" <<EOF
{
  "version": 1,
  "laufordner": "$L",
  "kandidat": "Florian Feiler",
  "sprache": "de",
  "reihenfolge": ["newmonday-cv", "newmonday-skillmatrix", "newmonday-portfolio"],
  "figma": {"aktiv": false, "link": null, "file_key": null, "seite_id": null, "neues_file": false},
  "material": {"lebenslauf": "eingang/lebenslauf.pdf"},
  "ohne": ["linkedin_export", "linkedin_url", "portfolio_url"],
  "entscheidungen": {},
  "status": {
    "newmonday-cv": {"vorbereiten": "offen", "bauen": "offen", "fehler": null},
    "newmonday-skillmatrix": {"vorbereiten": "offen", "bauen": "offen", "fehler": null},
    "newmonday-portfolio": {"vorbereiten": "offen", "bauen": "offen", "fehler": null}
  }
}
EOF
python3 $BM/scripts/pruefe_lauf.py "$L"
```
Expected: `Lauf in Ordnung`

- [ ] **Step 3: [Hauptgespräch] Baseline – Vorbereiten ohne den neuen Abschnitt**

`Agent`, `subagent_type: general-purpose`, Vordergrund. Auftrag = die Vorlage aus `$BM/SKILL.md`, Abschnitt „Der Auftrag an die Subagenten“, ausgefüllt mit: `<skill>` = `newmonday-cv`, Phase `vorbereiten`, `<laufordner>` = `/Users/florian/Desktop/bewerbermappe-test/lauf-cv`, Unterordner `cv`, `<skills>` = `/Users/florian/NW-Claude-Skills/newmonday-bewerber/skills`.

- [ ] **Step 4: Baseline auswerten**

Run:
```bash
python3 $BM/scripts/pruefe_lauf.py "$L"; python3 - "$L" cv nm_rolle nm_start <<'EOF'
import json, sys, pathlib
l, kurz, *pflicht = sys.argv[1:]
l = pathlib.Path(l)
f = l / kurz / "fragen.json"
if not f.exists():
    sys.exit("fragen.json fehlt")
ids = {q.get("id") for q in json.loads(f.read_text(encoding="utf-8")).get("fragen", [])}
print("IDs:", sorted(map(str, ids)))
print("fehlende Pflicht-IDs:", sorted(set(pflicht) - ids) or "keine")
print("PDFs in ausgabe:", sorted(p.name for p in (l / "ausgabe").glob("*.pdf")) or "keine")
print("notizen.md:", (l / kurz / "notizen.md").exists())
print("Skill-JSON schon gebaut:", (l / kurz / "cv.json").exists())
EOF
```
Expected: mindestens eins davon – `fragen.json fehlt`, fehlende Pflicht-IDs, PDFs in `ausgabe`, `Skill-JSON schon gebaut: True`, oder `FEHLER` von `pruefe_lauf`. Das Ergebnis in den Task-Bericht übernehmen. Besteht die Baseline wider Erwarten, das festhalten – der Abschnitt legt die IDs trotzdem fest.

- [ ] **Step 5: Abschnitt einfügen**

In `newmonday-bewerber/skills/newmonday-cv/SKILL.md` direkt vor der Zeile `## Gefragt wird mit Klickboxen, nicht im Fließtext` einfügen (mit einer Leerzeile danach):

```markdown
## Im Gesamtlauf

Dieser Abschnitt gilt nur, wenn der Auftrag mit „Gesamtlauf
newmonday-bewerbermappe“ beginnt. Dann läuft dieser Skill als Subagent in einer
von zwei Phasen, und der Auftrag bringt die allgemeinen Regeln mit: keine
Rückfragen, Laufordner, `auftrag.json`, die Formate in
`newmonday-bewerbermappe/references/formate.md`. Hier steht nur, was für den
Lebenslauf dazukommt. Wo dieser Abschnitt etwas regelt, geht er dem Rest des
Skills vor; im Einzellauf gilt er nicht.

**Schritt 0 entfällt.** Was er einholt, steht in `auftrag.json`:

| Schritt 0 | aus `auftrag.json` |
|---|---|
| Sprache | `sprache` |
| Figma-Ziel | `figma.link` – er trägt die `node-id` der Kandidatenseite, also gilt in `references/figma.md` „Zielseite“ mit `node-id`. Ist `figma.aktiv` false, entfällt Schritt 4a. |
| Lebenslauf, LinkedIn-Export und -Link, Xing, Portfolio, Foto, Logos | `material` |

**Phase vorbereiten: Schritte 1 bis 1c.** Statt der Frage-Nachricht aus Schritt
1d entsteht `fragen.json`:

- `fragen`: `nm_rolle` und `nm_start` immer, `fachfremd` und `weiterbildung`
  nur, wenn es etwas zu entscheiden gibt – Wortlaut, Optionen, `multiSelect` und
  „(Empfohlen)“ genau wie in Schritt 1d. Entstünde durch das Streichen einer
  Station eine Lücke, steht sie in der `description` dieser Option.
- `luecken`: „Profilfoto“, wenn Schritt 1a bei „beim Kandidaten anfragen“ endet
  oder das beste Foto unter 200 dpi liegt – die Folge nennt die dpi-Zahl bzw.
  „die Fotospalte bleibt leer“, die Form „Bilddatei, Porträt, gut aufgelöst“.
- `texte`: leer.

In `notizen.md`:

- die gewählte Fotoquelle mit Datei, dpi und – bei Website-Fotos – Bildadresse;
- jede Abweichung zwischen Lebenslauf, LinkedIn und Portfolio mit beiden Werten
  (Schritte 1b und 1c) und welche Fassung ins Dokument kommt;
- Kunden, die der Lebenslauf anonymisiert und das Portfolio beim Namen nennt;
- was aus dem Portfolio ergänzt werden soll, Feld für Feld;
- die Pfade der Auszüge (`arbeit/…/text.txt`).

Keine `cv.json`, keine Logos, nichts rendern.

**Phase bauen: Schritte 2 bis 5**, beide Fassungen. Die Antworten stehen in
`entscheidungen.newmonday-cv`:

- `nm_rolle`, `nm_start` → Titel und Zeitraum von `stationen[0]` und die
  Textbausteine dazu (Schritt 2). Ein eigener Titel über „Other“ wird genommen,
  wie er dasteht.
- `fachfremd`, `weiterbildung` → die angehakten Einträge bleiben drin, alle
  anderen aus der Frage fallen weg. Fehlt die `id`, gab es nichts zu entscheiden
  – dann bleibt alles drin.

Stationen mit mehreren Marken (Schritt 3): ohne Rückfrage in einer Station, alle
Logos als Liste in `logo`, und das unter „Ohne Rückfrage entschieden“. Die
Übergabe aus Schritt 5 geht nach `uebergabe.md`: Kurzprofil unter „Zur
Freigabe“, die Abweichungen aus `notizen.md` unter „Quellen weichen ab“, der
Hinweis auf den vollen Namen im Figma-File und alles Übrige unter „Hinweise“, die
beiden Schlusszeilen wörtlich unter „Fehlt noch“.
```

- [ ] **Step 6: [Hauptgespräch] Vorbereiten mit Abschnitt**

Erst Step 2 wiederholen (frischer Laufordner). Dann derselbe Subagenten-Auftrag wie in Step 3.

- [ ] **Step 7: Vorbereiten auswerten – grün**

Run: derselbe Befehl wie in Step 4.
Expected:
```
Lauf in Ordnung
IDs: [… 'nm_rolle', 'nm_start' …]
fehlende Pflicht-IDs: keine
PDFs in ausgabe: keine
notizen.md: True
Skill-JSON schon gebaut: False
```
Dazu `cat "$L/cv/notizen.md"` – Fotoquelle mit dpi muss drinstehen.

- [ ] **Step 8: Entscheidungen wie der Orchestrator eintragen (Empfohlen-Optionen)**

```bash
python3 - "$L" newmonday-cv cv <<'EOF'
import json, sys, pathlib
l, skill, kurz = sys.argv[1:]
l = pathlib.Path(l)
a = json.loads((l / "auftrag.json").read_text(encoding="utf-8"))
fr = json.loads((l / kurz / "fragen.json").read_text(encoding="utf-8"))
ent = {}
for q in fr["fragen"]:
    wahl = next(o for o in q["options"] if not o.get("text_noetig"))
    ent[q["id"]] = wahl["label"].replace(" (Empfohlen)", "")
a["entscheidungen"][skill] = ent
a["status"][skill]["vorbereiten"] = "fertig"
(l / "auftrag.json").write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding="utf-8")
print(ent)
EOF
python3 $BM/scripts/pruefe_lauf.py "$L"
```
Expected: die Antworten als Dictionary, dann `Lauf in Ordnung`.

- [ ] **Step 9: [Hauptgespräch] Bauen**

Derselbe Subagenten-Auftrag wie in Step 3, aber Phase `bauen`.

- [ ] **Step 10: Bauen auswerten**

Run:
```bash
python3 $BM/scripts/pruefe_lauf.py "$L"; ls "$L/ausgabe"; sed -n '/^## Ohne Rückfrage entschieden/,$p' "$L/cv/uebergabe.md"
```
Expected: `Lauf in Ordnung`; zwei PDFs – eins mit `Florian Feiler`, eins mit `F. F.` im Namen; die beiden letzten Abschnitte der Übergabe. Ein PDF ansehen: `pdftoppm -png -r 40 -f 1 -l 1 "$L/ausgabe/"*"Florian Feiler"*.pdf $T/blick-cv` und `$T/blick-cv-1.png` lesen – erste Station New Monday, Titel „User Experience Design Specialist“.

- [ ] **Step 11: Einzellauf unverändert**

Run: `cd $S/newmonday-cv && python3 scripts/selbsttest.py | tail -1 && cd $R && git diff --stat`
Expected: `Selbsttest bestanden. Der Skill ist einsatzbereit.`; im Diff nur `newmonday-cv/SKILL.md`.

- [ ] **Step 12: Commit**

```bash
cd $R && git add newmonday-bewerber/skills/newmonday-cv/SKILL.md && git commit -q -F - <<'EOF'
newmonday-cv: Abschnitt "Im Gesamtlauf" fuer newmonday-bewerbermappe

Vorbereiten (Schritte 1-1c, Fragen aus 1d nach fragen.json) und Bauen
(Schritte 2-5) als Subagent; der Einzellauf bleibt unveraendert.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 4: `newmonday-skillmatrix` im Gesamtlauf

**Files:**
- Modify: `newmonday-bewerber/skills/newmonday-skillmatrix/SKILL.md` – neuer Abschnitt vor `## Gefragt wird mit Klickboxen, nicht im Fließtext` (derzeit Zeile 65)

**Interfaces:**
- Consumes: Subagenten-Vorlage aus `newmonday-bewerbermappe/SKILL.md`, `pruefe_lauf.py`, `testmaterial.sh`.
- Produces: Frage-IDs `verfuegbar_ab`, `freigabe` (immer), `tools` (bei Bedarf); `texte` mit Hero-Beschreibung, Matrix- und Tools-Tabelle; `luecken`-Posten „Profilfoto“, „Zertifikate“.

- [ ] **Step 1: Ausgangslage – Beispiel rendert sauber**

Run: `cd $S/newmonday-skillmatrix && python3 scripts/render_skillmatrix.py beispiel/skillmatrix.json $T/regress-sm/ 2>&1 | tail -1`
Expected: `Design System eingehalten: Seitenbreite, Schriften, Textstile, Farben.`

- [ ] **Step 2: Test-Laufordner anlegen**

```bash
bash $BM/scripts/testmaterial.sh $T/material
L=$T/lauf-sm; rm -rf "$L"; mkdir -p "$L/eingang" "$L/ausgabe"
cp $T/material/lebenslauf.pdf "$L/eingang/lebenslauf.pdf"
cat > "$L/auftrag.json" <<EOF
{
  "version": 1,
  "laufordner": "$L",
  "kandidat": "Florian Feiler",
  "sprache": "de",
  "reihenfolge": ["newmonday-cv", "newmonday-skillmatrix", "newmonday-portfolio"],
  "figma": {"aktiv": false, "link": null, "file_key": null, "seite_id": null, "neues_file": false},
  "material": {"lebenslauf": "eingang/lebenslauf.pdf"},
  "ohne": ["linkedin_export", "linkedin_url", "portfolio_url"],
  "entscheidungen": {},
  "status": {
    "newmonday-cv": {"vorbereiten": "offen", "bauen": "offen", "fehler": null},
    "newmonday-skillmatrix": {"vorbereiten": "offen", "bauen": "offen", "fehler": null},
    "newmonday-portfolio": {"vorbereiten": "offen", "bauen": "offen", "fehler": null}
  }
}
EOF
python3 $BM/scripts/pruefe_lauf.py "$L"
```
Expected: `Lauf in Ordnung`

- [ ] **Step 3: [Hauptgespräch] Baseline – Vorbereiten ohne den neuen Abschnitt**

`Agent`, `subagent_type: general-purpose`, Vordergrund. Auftrag = die Vorlage aus `$BM/SKILL.md`, Abschnitt „Der Auftrag an die Subagenten“, ausgefüllt mit: `<skill>` = `newmonday-skillmatrix`, Phase `vorbereiten`, `<laufordner>` = `/Users/florian/Desktop/bewerbermappe-test/lauf-sm`, Unterordner `skillmatrix`, `<skills>` = `/Users/florian/NW-Claude-Skills/newmonday-bewerber/skills`.

- [ ] **Step 4: Baseline auswerten**

Run:
```bash
python3 $BM/scripts/pruefe_lauf.py "$L"; python3 - "$L" skillmatrix verfuegbar_ab freigabe <<'EOF'
import json, sys, pathlib
l, kurz, *pflicht = sys.argv[1:]
l = pathlib.Path(l)
f = l / kurz / "fragen.json"
if not f.exists():
    sys.exit("fragen.json fehlt")
d = json.loads(f.read_text(encoding="utf-8"))
ids = {q.get("id") for q in d.get("fragen", [])}
print("IDs:", sorted(map(str, ids)))
print("fehlende Pflicht-IDs:", sorted(set(pflicht) - ids) or "keine")
print("texte-Blöcke:", len(d.get("texte", [])), "| Tabelle drin:", any("|Punkte|" in t.replace(" ", "") for t in d.get("texte", [])))
print("PDFs in ausgabe:", sorted(p.name for p in (l / "ausgabe").glob("*.pdf")) or "keine")
print("notizen.md:", (l / kurz / "notizen.md").exists())
print("Skill-JSON schon gebaut:", (l / kurz / "skillmatrix.json").exists())
EOF
```
Expected: mindestens eins davon – `fragen.json fehlt`, fehlende Pflicht-IDs (vor allem `verfuegbar_ab`, das bisher in Schritt 0 steht), keine Tabelle in `texte`, PDFs in `ausgabe`, `Skill-JSON schon gebaut: True`. Ergebnis in den Task-Bericht.

- [ ] **Step 5: Abschnitt einfügen**

In `newmonday-bewerber/skills/newmonday-skillmatrix/SKILL.md` direkt vor der Zeile `## Gefragt wird mit Klickboxen, nicht im Fließtext` einfügen (mit einer Leerzeile danach):

```markdown
## Im Gesamtlauf

Dieser Abschnitt gilt nur, wenn der Auftrag mit „Gesamtlauf
newmonday-bewerbermappe“ beginnt. Dann läuft dieser Skill als Subagent in einer
von zwei Phasen, und der Auftrag bringt die allgemeinen Regeln mit: keine
Rückfragen, Laufordner, `auftrag.json`, die Formate in
`newmonday-bewerbermappe/references/formate.md`. Hier steht nur, was für die
Skill Matrix dazukommt. Wo dieser Abschnitt etwas regelt, geht er dem Rest des
Skills vor; im Einzellauf gilt er nicht.

**Schritt 0 entfällt.** Was er einholt, steht in `auftrag.json`:

| Schritt 0 | aus `auftrag.json` |
|---|---|
| Sprache | `sprache` |
| Figma | Der Frame entsteht, wenn `figma.aktiv` true ist – eine eigene Frage danach gibt es nicht. `figma.link` trägt die `node-id` der Kandidatenseite, also gilt „Zielseite“ mit `node-id` (`references/figma.md` bzw. `figma-vorlage.md`). |
| Material | `material` – Zertifikate aus dem Ordner `material.zertifikate`, in der Reihenfolge der Dateinamen |
| Verfügbarkeit | wandert in die Fragen der Phase *vorbereiten* |

**Phase vorbereiten: Schritte 1 bis 2d.** Statt der Freigabe-Nachricht aus 2e
entsteht `fragen.json`:

- `texte`: was 2e dem Nutzer zeigt, ein Markdown-Block je Punkt – die
  Hero-Beschreibung im Wortlaut (als generiert gekennzeichnet) mit den drei
  Schwerpunkten, die Matrix-Tabelle (Kategorie, Attribut, Punkte, Beleg), die
  Tools-Tabelle (Tool, Punkte, Beleg bzw. „Vorschlag, nicht belegt“). Sollen
  Zertifikate zu einer Karte gebündelt werden, steht der Vorschlag dabei.
- `fragen`:
  - `verfuegbar_ab` – Wortlaut und Optionen wie in Schritt 0, Punkt 2.
  - `freigabe` – wie in 2e; die Option „Ich möchte etwas ändern“ trägt
    `"text_noetig": true`.
  - `tools` – nur, wenn der Eingang keine Tools nennt, wie in 2e.
- `luecken`: „Profilfoto“, wenn Schritt 1a bei „beim Kandidaten anfragen“ endet
  oder das beste Foto unter 100 dpi liegt (Folge mit dpi-Zahl); „Zertifikate“,
  wenn Lebenslauf, LinkedIn oder Portfolio Zertifikate nennen, aber keine
  Dateien dazu im Eingang liegen (Folge: die Zertifikatssektion zeigt kein
  Bilderraster).

In `notizen.md`:

- der vollständige Entwurf als JSON-Block im Aufbau der `skillmatrix.json`
  (Schritt 3), mit dem Beleg je Skill und Tool als zusätzlichem Feld `beleg`;
- die Fotoquelle mit Datei, dpi und Kontrollbild, und ob der Kopf mittig steht;
- jede Abweichung zwischen den Quellen mit beiden Werten.

Keine `skillmatrix.json`, nichts rendern.

**Phase bauen: Schritte 3 bis 5**, aus dem Entwurf in `notizen.md` (das Feld
`beleg` fällt dabei weg). Die Antworten stehen in
`entscheidungen.newmonday-skillmatrix`:

- `verfuegbar_ab` → `person.verfuegbar_ab`: `"sofort"` bei „ab sofort“, sonst
  der Monat, wie er dasteht.
- `freigabe`: „Ja, so bauen“ → der Entwurf unverändert. Alles andere ist
  „Ich möchte etwas ändern: <Text>“ – den Text umsetzen, nach denselben Regeln
  wie Änderungen in 2e.
- `tools`: wie in 2e.

Schritt 4a läuft, wenn `figma.aktiv` true ist. Die Übergabe aus Schritt 5 geht
nach `uebergabe.md`: Hero-Beschreibung und die **endgültige** Matrix-Tabelle
unter „Zur Freigabe“ – nach einer Änderung ist das die einzige Stelle, an der der
Nutzer sie sieht –, Abweichungen unter „Quellen weichen ab“, der Rest unter
„Hinweise“, die Schlusszeilen wörtlich unter „Fehlt noch“.
```

- [ ] **Step 6: [Hauptgespräch] Vorbereiten mit Abschnitt**

Erst Step 2 wiederholen (frischer Laufordner). Dann derselbe Subagenten-Auftrag wie in Step 3.

- [ ] **Step 7: Vorbereiten auswerten – grün**

Run: derselbe Befehl wie in Step 4.
Expected:
```
Lauf in Ordnung
IDs: [… 'freigabe', 'verfuegbar_ab' …]
fehlende Pflicht-IDs: keine
texte-Blöcke: 3 | Tabelle drin: True
PDFs in ausgabe: keine
notizen.md: True
Skill-JSON schon gebaut: False
```
(`texte-Blöcke` darf 2–4 sein.) Dazu `grep -c '"beleg"' "$L/skillmatrix/notizen.md"` – größer als 0.

- [ ] **Step 8: Entscheidungen wie der Orchestrator eintragen (Empfohlen-Optionen)**

```bash
python3 - "$L" newmonday-skillmatrix skillmatrix <<'EOF'
import json, sys, pathlib
l, skill, kurz = sys.argv[1:]
l = pathlib.Path(l)
a = json.loads((l / "auftrag.json").read_text(encoding="utf-8"))
fr = json.loads((l / kurz / "fragen.json").read_text(encoding="utf-8"))
ent = {}
for q in fr["fragen"]:
    wahl = next(o for o in q["options"] if not o.get("text_noetig"))
    ent[q["id"]] = wahl["label"].replace(" (Empfohlen)", "")
a["entscheidungen"][skill] = ent
a["status"][skill]["vorbereiten"] = "fertig"
(l / "auftrag.json").write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding="utf-8")
print(ent)
EOF
python3 $BM/scripts/pruefe_lauf.py "$L"
```
Expected: `{'verfuegbar_ab': 'ab sofort', 'freigabe': 'Ja, so bauen', …}`, dann `Lauf in Ordnung`.

- [ ] **Step 9: [Hauptgespräch] Bauen**

Derselbe Subagenten-Auftrag wie in Step 3, aber Phase `bauen`.

- [ ] **Step 10: Bauen auswerten**

Run:
```bash
python3 $BM/scripts/pruefe_lauf.py "$L"; ls "$L/ausgabe"; sed -n '/^## Zur Freigabe/,/^## Quellen/p' "$L/skillmatrix/uebergabe.md"
```
Expected: `Lauf in Ordnung`; ein PDF `New-Monday - Florian Feiler - … - Skillmatrix.pdf`; unter „Zur Freigabe“ Hero-Beschreibung und Matrix-Tabelle. PDF ansehen: `pdftoppm -png -r 30 "$L/ausgabe/"*Skillmatrix.pdf $T/blick-sm` und `$T/blick-sm-1.png` lesen – Badge „VERFÜGBAR AB SOFORT“.

- [ ] **Step 11: Einzellauf unverändert**

Run: Step 1 noch einmal, dann `cd $R && git diff --stat`
Expected: `Design System eingehalten: …`; im Diff nur `newmonday-skillmatrix/SKILL.md`.

- [ ] **Step 12: Commit**

```bash
cd $R && git add newmonday-bewerber/skills/newmonday-skillmatrix/SKILL.md && git commit -q -F - <<'EOF'
newmonday-skillmatrix: Abschnitt "Im Gesamtlauf" fuer newmonday-bewerbermappe

Vorbereiten (Schritte 1-2d, Freigabe aus 2e und Verfuegbarkeit nach
fragen.json) und Bauen (Schritte 3-5) als Subagent; Einzellauf unveraendert.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 5: `newmonday-portfolio` im Gesamtlauf

**Files:**
- Modify: `newmonday-bewerber/skills/newmonday-portfolio/SKILL.md` – neuer Abschnitt vor `## Gefragt wird mit Klickboxen, nicht im Fließtext` (derzeit Zeile 93)

**Interfaces:**
- Consumes: Subagenten-Vorlage aus `newmonday-bewerbermappe/SKILL.md`, `pruefe_lauf.py`, `testmaterial.sh`.
- Produces: Frage-IDs `projekte` (immer), `nda`, `statement`, `ki_tools` (bei Bedarf); `luecken`-Posten „Screens <Projekt>“, „Lebenslauf“, „Projektname <Kunde>“, „Weitere Projekte“.

Das Test-Set hat kein Portfolio – geprüft wird hier der Weg „Kein Portfolio, nur Lebenslauf“ (Sonderfälle im Skill). Der Weg mit Portfolio läuft in Task 7 und 8.

- [ ] **Step 1: Ausgangslage – Selbsttest grün**

Run: `cd $S/newmonday-portfolio && python3 scripts/selbsttest.py | tail -1`
Expected: `Selbsttest bestanden: Tokens, Beispiel-PDF, Figma-Abgleich (1 Vorlage(n)), Sprachen und Screen-Stil ohne Abweichung.`

- [ ] **Step 2: Test-Laufordner anlegen**

```bash
bash $BM/scripts/testmaterial.sh $T/material
L=$T/lauf-pf; rm -rf "$L"; mkdir -p "$L/eingang" "$L/ausgabe"
cp $T/material/lebenslauf.pdf "$L/eingang/lebenslauf.pdf"
cat > "$L/auftrag.json" <<EOF
{
  "version": 1,
  "laufordner": "$L",
  "kandidat": "Florian Feiler",
  "sprache": "de",
  "reihenfolge": ["newmonday-cv", "newmonday-skillmatrix", "newmonday-portfolio"],
  "figma": {"aktiv": false, "link": null, "file_key": null, "seite_id": null, "neues_file": false},
  "material": {"lebenslauf": "eingang/lebenslauf.pdf"},
  "ohne": ["linkedin_export", "linkedin_url"],
  "entscheidungen": {},
  "status": {
    "newmonday-cv": {"vorbereiten": "offen", "bauen": "offen", "fehler": null},
    "newmonday-skillmatrix": {"vorbereiten": "offen", "bauen": "offen", "fehler": null},
    "newmonday-portfolio": {"vorbereiten": "offen", "bauen": "offen", "fehler": null}
  }
}
EOF
python3 $BM/scripts/pruefe_lauf.py "$L"
```
Expected: `Lauf in Ordnung`. (`portfolio_url` steht hier bewusst nicht unter `ohne` – das Fehlen des Portfolios soll als Lücke „Screens …“ auftauchen.)

- [ ] **Step 3: [Hauptgespräch] Baseline – Vorbereiten ohne den neuen Abschnitt**

`Agent`, `subagent_type: general-purpose`, Vordergrund. Auftrag = die Vorlage aus `$BM/SKILL.md`, Abschnitt „Der Auftrag an die Subagenten“, ausgefüllt mit: `<skill>` = `newmonday-portfolio`, Phase `vorbereiten`, `<laufordner>` = `/Users/florian/Desktop/bewerbermappe-test/lauf-pf`, Unterordner `portfolio`, `<skills>` = `/Users/florian/NW-Claude-Skills/newmonday-bewerber/skills`.

- [ ] **Step 4: Baseline auswerten**

Run:
```bash
python3 $BM/scripts/pruefe_lauf.py "$L"; python3 - "$L" portfolio projekte <<'EOF'
import json, sys, pathlib
l, kurz, *pflicht = sys.argv[1:]
l = pathlib.Path(l)
f = l / kurz / "fragen.json"
if not f.exists():
    sys.exit("fragen.json fehlt")
d = json.loads(f.read_text(encoding="utf-8"))
ids = {q.get("id") for q in d.get("fragen", [])}
print("IDs:", sorted(map(str, ids)))
print("fehlende Pflicht-IDs:", sorted(set(pflicht) - ids) or "keine")
print("Lücken:", [x.get("was") for x in d.get("luecken", [])])
print("PDFs in ausgabe:", sorted(p.name for p in (l / "ausgabe").glob("*.pdf")) or "keine")
print("notizen.md:", (l / kurz / "notizen.md").exists())
print("Skill-JSON schon gebaut:", (l / kurz / "portfolio.json").exists())
EOF
```
Expected: mindestens eins davon – `fragen.json fehlt`, `projekte` fehlt, keine Lücke mit „Screens“, PDFs in `ausgabe`, `Skill-JSON schon gebaut: True`. Ergebnis in den Task-Bericht.

- [ ] **Step 5: Abschnitt einfügen**

In `newmonday-bewerber/skills/newmonday-portfolio/SKILL.md` direkt vor der Zeile `## Gefragt wird mit Klickboxen, nicht im Fließtext` einfügen (mit einer Leerzeile danach):

```markdown
## Im Gesamtlauf

Dieser Abschnitt gilt nur, wenn der Auftrag mit „Gesamtlauf
newmonday-bewerbermappe“ beginnt. Dann läuft dieser Skill als Subagent in einer
von zwei Phasen, und der Auftrag bringt die allgemeinen Regeln mit: keine
Rückfragen, Laufordner, `auftrag.json`, die Formate in
`newmonday-bewerbermappe/references/formate.md`. Hier steht nur, was für das
Portfolio dazukommt. Wo dieser Abschnitt etwas regelt, geht er dem Rest des
Skills vor; im Einzellauf gilt er nicht.

**Schritt 0 entfällt.** Was er einholt, steht in `auftrag.json`:

| Schritt 0 | aus `auftrag.json` |
|---|---|
| Sprache | `sprache` |
| Figma-Ziel | `figma.link` – er trägt die `node-id` der Kandidatenseite: `figma_plan.py … --knoten <node-id>` (`references/figma.md`, „Die Zieldatei“). Ist `figma.aktiv` false, entfällt Schritt 7a. |
| Portfolio, Lebenslauf, LinkedIn-Export | `material.portfolio_url` oder `material.portfolio_pdf`, `material.lebenslauf`, `material.linkedin_export` |
| Logos, Screens, Kundentexte | `material.logos`, `material.screens` (je Projekt ein Unterordner, wenn so geliefert), `material.kundentexte` |

**Phase vorbereiten: Schritte 1 und 2.** Statt der Frage-Nachricht aus Schritt 3
entsteht `fragen.json`:

- `fragen`: `projekte` immer, `nda`, `statement` und `ki_tools` unter denselben
  Bedingungen wie in Schritt 3, mit demselben Wortlaut. `projekte` führt die
  Vorschläge nach Stärke, das stärkste zuerst mit „(Empfohlen)“; die
  `description` nennt die Beleglage (Text, Zahl und Schärfe der Screens). Mehr
  als vier Projekte: die vier stärksten als Optionen, die übrigen in der
  `description` der vierten („weitere über Other: …“). `statement` hat die
  Optionen „Ich gebe es ein“ mit `"text_noetig": true` und „Fläche leer lassen“.
- `luecken`:
  - je vorgeschlagenem Projekt ohne scharfe Screens ein Posten „Screens
    <Projekt>“ – gemessen an `bilder.txt` und den Grenzen aus Schritt 0,
    Punkt 4 (Desktop ab 1 120 px, Phone ab 520 px Displaybreite); Folge: „Lösungs-
    und Abschlussseite zeigen nur die Markenfläche“ bzw. „… werden hochgerechnet“;
  - „Lebenslauf“, wenn er fehlt (Schritt 0, Punkt 2);
  - „Projektname <Kunde>“, wenn zwei Projekte beim selben Kunden keinen
    Projektnamen im Material haben (Schritt 4, `projektname`);
  - bei genau einem Projekt im Material: „Weitere Projekte“ (Sonderfälle, „Sehr
    wenige Projekte“).
- `texte`: leer.

In `notizen.md`:

- je Projekt: Quelle der Texte, zugeordnete Bilder aus `arbeit/bilder/` mit
  Seitenzahl, Beleglage, Markenfarbe falls schon erkennbar;
- die Profilfoto-Quelle;
- jede Abweichung zwischen den Quellen mit beiden Werten (Portfolio vor
  Lebenslauf vor LinkedIn, Schritt 2) und anonymisierte Kunden;
- bei einer Figma-Datei als Quelle: die Knoten-IDs der Screens.

Keine `portfolio.json`, keine Logos, keine Recherche, nichts rendern.

**Phase bauen: Schritte 4 bis 8.** Die Antworten stehen in
`entscheidungen.newmonday-portfolio`:

- `projekte` → die gewählten Projekte in der Reihenfolge der Optionen; nennt der
  Text über „Other“ eine andere Reihenfolge, gilt die.
- `nda` → `"nda": true` bei den gewählten Projekten.
- `statement` → „Ich gebe es ein: <Text>“: der Text als `statement.text`,
  wörtlich; „Fläche leer lassen“: kein Statement.
- `ki_tools` → `person.ki.tools`.

Gerendert wird nach `<laufordner>/ausgabe/<nachname>-<vorname>-portfolio.pdf`.
Die Übergabe aus Schritt 8 geht nach `uebergabe.md`: Cover-Titel, KI- und
Prozesstexte, Kundentexte mit Quellen und KI-generierte Gebäude unter „Zur
Freigabe“, Abweichungen unter „Quellen weichen ab“, Bildnachweis und alles
Übrige unter „Hinweise“, die Schlusszeilen wörtlich unter „Fehlt noch“.
```

- [ ] **Step 6: [Hauptgespräch] Vorbereiten mit Abschnitt**

Erst Step 2 wiederholen (frischer Laufordner). Dann derselbe Subagenten-Auftrag wie in Step 3.

- [ ] **Step 7: Vorbereiten auswerten – grün**

Run: derselbe Befehl wie in Step 4.
Expected:
```
Lauf in Ordnung
IDs: [… 'projekte' …]
fehlende Pflicht-IDs: keine
Lücken: [… mindestens ein Eintrag, der mit 'Screens' beginnt …]
PDFs in ausgabe: keine
notizen.md: True
Skill-JSON schon gebaut: False
```

- [ ] **Step 8: Entscheidungen wie der Orchestrator eintragen (Empfohlen-Optionen, „ohne“ für die Lücken)**

```bash
python3 - "$L" newmonday-portfolio portfolio <<'EOF'
import json, sys, pathlib
l, skill, kurz = sys.argv[1:]
l = pathlib.Path(l)
a = json.loads((l / "auftrag.json").read_text(encoding="utf-8"))
fr = json.loads((l / kurz / "fragen.json").read_text(encoding="utf-8"))
ent = {}
for q in fr["fragen"]:
    wahl = next(o for o in q["options"] if not o.get("text_noetig"))
    ent[q["id"]] = wahl["label"].replace(" (Empfohlen)", "")
a["entscheidungen"][skill] = ent
a["status"][skill]["vorbereiten"] = "fertig"
a["ohne"] = sorted(set(a["ohne"]) | {"portfolio_url", "screens"})
(l / "auftrag.json").write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding="utf-8")
print(ent)
EOF
python3 $BM/scripts/pruefe_lauf.py "$L"
```
Expected: die Antworten, dann `Lauf in Ordnung`.

- [ ] **Step 9: [Hauptgespräch] Bauen**

Derselbe Subagenten-Auftrag wie in Step 3, aber Phase `bauen`.

- [ ] **Step 10: Bauen auswerten**

Run:
```bash
python3 $BM/scripts/pruefe_lauf.py "$L"; ls "$L/ausgabe"; sed -n '/^## Fehlt noch/,$p' "$L/portfolio/uebergabe.md"
```
Expected: `Lauf in Ordnung`; ein PDF `feiler-florian-portfolio.pdf`; unter „Fehlt noch“ die Zeile „Folgende Bilder fehlen: … – schick sie mir hier in den Chat, dann baue ich das PDF neu“. Ein Blick: `pdftoppm -png -r 20 -f 1 -l 4 "$L/ausgabe/"*portfolio.pdf $T/blick-pf` und die Bilder lesen – Cover mit Name, Profilseite befüllt.

- [ ] **Step 11: Einzellauf unverändert**

Run: Step 1 noch einmal, dann `cd $R && git diff --stat`
Expected: `Selbsttest bestanden: …`; im Diff nur `newmonday-portfolio/SKILL.md`.

- [ ] **Step 12: Commit**

```bash
cd $R && git add newmonday-bewerber/skills/newmonday-portfolio/SKILL.md && git commit -q -F - <<'EOF'
newmonday-portfolio: Abschnitt "Im Gesamtlauf" fuer newmonday-bewerbermappe

Vorbereiten (Schritte 1-2, Fragen aus 3 und fehlende Screens nach
fragen.json) und Bauen (Schritte 4-8) als Subagent; Einzellauf unveraendert.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 6: README, Installation, Version

**Files:**
- Modify: `README.md` (Tabelle, Symlink-Block)
- Modify: `newmonday-bewerber/README.md` (Liste, Symlink-Block)
- Modify: `newmonday-bewerber/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Prüfung, die noch scheitert**

Run:
```bash
cd $R && grep -c "newmonday-bewerbermappe" README.md newmonday-bewerber/README.md; grep '"version"' newmonday-bewerber/.claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Expected: `README.md:0`, `newmonday-bewerber/README.md:0`, zweimal `"version": "1.2.0"`.

- [ ] **Step 2: `README.md`**

In der Tabelle nach der Zeile, die mit `` | [`newmonday-portfolio`] `` beginnt, eine Zeile einfügen:

```markdown
| [`newmonday-bewerbermappe`](newmonday-bewerber/skills/newmonday-bewerbermappe/) | Baut alle drei Dokumente eines Kandidaten in einem Lauf: fragt Sprache, Figma und Material einmal, prüft vorab, was fehlt, bündelt alle Entscheidungen und lässt dann `newmonday-cv`, `newmonday-skillmatrix` und `newmonday-portfolio` nacheinander bauen – PDFs plus Frames auf einer Figma-Seite je Kandidat. |
```

Den Satz `Die drei Dokument-Skills liegen zusammen im Ordner` ersetzen durch `Die drei Dokument-Skills und der Gesamtlauf liegen zusammen im Ordner`.

Im Symlink-Block nach der Zeile mit `newmonday-portfolio` einfügen:

```bash
ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-bewerbermappe ~/.claude/skills/newmonday-bewerbermappe
```

- [ ] **Step 3: `newmonday-bewerber/README.md`**

`Drei Claude-Code-Skills der New Monday GmbH rund um Bewerber-Unterlagen:` ersetzen durch `Vier Claude-Code-Skills der New Monday GmbH rund um Bewerber-Unterlagen:`. Nach der Zeile `` - `skills/newmonday-portfolio` — … `` einfügen:

```markdown
- `skills/newmonday-bewerbermappe` — alle drei in einem Lauf: gemeinsame Fragen einmal, Lückencheck vorab, Entscheidungen gebündelt (braucht die drei anderen daneben)
```

`2. Die drei Skills per Symlink verlinken:` ersetzen durch `2. Die vier Skills per Symlink verlinken:` und im Block darunter nach der Zeile mit `newmonday-portfolio` einfügen:

```bash
   ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-bewerbermappe ~/.claude/skills/newmonday-bewerbermappe
```

- [ ] **Step 4: Version und Beschreibung**

`newmonday-bewerber/.claude-plugin/plugin.json`: `"version": "1.2.0"` → `"version": "1.3.0"`; `"description"` → `"New-Monday-Dokumente aus Kandidatenunterlagen: Lebenslauf, Skill Matrix und Portfolio im New-Monday-Layout – einzeln oder als ganze Bewerbermappe in einem Lauf."`

`.claude-plugin/marketplace.json`: `"version": "1.2.0"` → `"version": "1.3.0"`; `"description"` → `"Lebenslauf, Skill Matrix und Portfolio im New-Monday-Layout – einzeln oder als Bewerbermappe in einem Lauf. Ein Paket, eine Versionsnummer."`

- [ ] **Step 5: Prüfung – grün**

Run:
```bash
cd $R && grep -c "newmonday-bewerbermappe" README.md newmonday-bewerber/README.md; grep '"version"' newmonday-bewerber/.claude-plugin/plugin.json .claude-plugin/marketplace.json; python3 -m json.tool newmonday-bewerber/.claude-plugin/plugin.json >/dev/null && python3 -m json.tool .claude-plugin/marketplace.json >/dev/null && echo JSON ok
```
Expected: `README.md:2`, `newmonday-bewerber/README.md:2`, zweimal `"version": "1.3.0"`, `JSON ok`.

- [ ] **Step 6: Commit**

```bash
cd $R && git add README.md newmonday-bewerber/README.md newmonday-bewerber/.claude-plugin/plugin.json .claude-plugin/marketplace.json && git commit -q -F - <<'EOF'
newmonday-bewerber: Plugin-Version 1.3.0 (newmonday-bewerbermappe)

README-Eintraege und Symlink-Zeilen fuer den Gesamtlauf.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 7: [Hauptgespräch] Gesamtlauf mit Test-Set und Test-Figma-Datei

Braucht den Nutzer: Er beantwortet die Klickfragen und stellt eine Figma-Design-Datei zum Testen bereit, in die geschrieben werden darf. Läuft in einer **neuen Sitzung** (damit der Skill geladen ist), Arbeitsverzeichnis `/Users/florian/Desktop`.

- [ ] **Step 1: Nutzer nach der Test-Figma-Datei fragen**

Link der Form `https://www.figma.com/design/<fileKey>/…`, Bearbeitungsrecht.

- [ ] **Step 2: Lauf starten**

In der neuen Sitzung: `/newmonday-bewerbermappe` mit `/Users/florian/Desktop/bewerbermappe-test/material/lebenslauf.pdf` und dem Figma-Link aus Step 1 – ohne LinkedIn, ohne Portfolio.

- [ ] **Step 3: Checkliste während des Laufs**

- Phase 1: Nur die Sprachfrage (der Figma-Link kam mit) – keine Figma-Frage, keine Bitte um den Lebenslauf.
- Phase 2: Eine Lücken-Nachricht mit LinkedIn-Export, LinkedIn-Link und Portfolio, je mit der Folge aus der Tabelle in SKILL.md; eine Klickbox. Antwort: *Ohne weitermachen*.
- Figma: Seite „Florian Feiler“ entsteht in der Test-Datei.
- Phase 3: drei Statuszeilen, keine Frage.
- Phase 4: Lücken (falls welche) → Texte der Skill Matrix mit Tabelle → drei Frage-Runden (Lebenslauf, Skill Matrix, Portfolio). Bei der Matrix-Freigabe „Ich möchte etwas ändern“ wählen und eine Änderung nennen (etwa einen Skill streichen) – es muss eine Nachfrage im Fließtext kommen.
- Phase 5: keine einzige Frage.
- Phase 6: Abschnitte wie in SKILL.md; die Matrix-Tabelle zeigt die Änderung; „Fehlt noch“-Zeilen wörtlich.

- [ ] **Step 4: Ergebnis prüfen**

```bash
L="/Users/florian/Desktop/Florian Feiler"
python3 $BM/scripts/pruefe_lauf.py "$L"; ls "$L/ausgabe"
```
Expected: `Lauf in Ordnung`; vier PDFs (CV vollständig, CV `F. F.`, Skillmatrix, Portfolio).

Überlappung auf der Figma-Seite – `use_figma` (read-only, vorher Skill `figma:figma-use` laden) mit der `seite_id` aus `$L/auftrag.json`:

```js
const seite = await figma.getNodeByIdAsync("<seite_id>");
const k = seite.children.map(n => ({ name: n.name, x: n.x, y: n.y, w: n.width, h: n.height }));
const ueberlapp = [];
for (let i = 0; i < k.length; i++) for (let j = i + 1; j < k.length; j++) {
  const a = k[i], b = k[j];
  if (a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h) ueberlapp.push([a.name, b.name]);
}
return { anzahl: k.length, namen: k.map(n => n.name), ueberlapp };
```
Expected: `ueberlapp: []`; unter den Namen die CV-Frames beider Fassungen, der Skillmatrix-Frame und der Portfolio-Sammelrahmen.

- [ ] **Step 5: Wiederaufnahme**

```bash
cp -R "/Users/florian/Desktop/Florian Feiler" /Users/florian/Desktop/bewerbermappe-test/wiederaufnahme
python3 - /Users/florian/Desktop/bewerbermappe-test/wiederaufnahme <<'EOF'
import json, sys, pathlib
l = pathlib.Path(sys.argv[1])
a = json.loads((l / "auftrag.json").read_text(encoding="utf-8"))
a["laufordner"] = str(l)
a["entscheidungen"].pop("newmonday-portfolio", None)
a["figma"] = {"aktiv": False, "link": None, "file_key": None, "seite_id": None, "neues_file": False}
for s in a["status"].values():
    s["bauen"] = "offen"
(l / "auftrag.json").write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding="utf-8")
for p in (l / "ausgabe").glob("*.pdf"):
    p.unlink()
print("vorbereitet, Portfolio-Antworten fehlen, nichts gebaut, Figma aus")
EOF
```
Neue Sitzung: „Mach den Lauf in /Users/florian/Desktop/bewerbermappe-test/wiederaufnahme weiter“.
Expected: kein Vorbereiten-Subagent; nur die Portfolio-Fragen aus Phase 4; dann Phase 5 für alle drei; `pruefe_lauf.py` → `Lauf in Ordnung`.

- [ ] **Step 6: Funde beheben**

Jede Abweichung von der Checkliste: Ursache in SKILL.md, formate.md oder einem Abschnitt „Im Gesamtlauf“ suchen, beheben, den betroffenen Schritt wiederholen, committen (`newmonday-bewerbermappe: <was>`).

---

### Task 8: [Hauptgespräch] Gesamtlauf mit echtem Kandidaten-Set

Braucht den Nutzer: echtes Set (Lebenslauf, LinkedIn-Export und -Link, Portfolio als Link oder PDF) und die Test-Figma-Datei aus Task 7. Neue Sitzung, Arbeitsverzeichnis `/Users/florian/Desktop`.

- [ ] **Step 1: Lauf mit vollständigem Material**

`/newmonday-bewerbermappe` mit allen vier Unterlagen und dem Figma-Link.
Expected: keine Lücken-Nachricht in Phase 2 (außer Umgebung/Figma meldet etwas); Phase 4 mit echten Projektvorschlägen im Portfolio.

- [ ] **Step 2: Übergabe prüfen**

- Jede Quellenabweichung steht einmal, mit der Fassung je Dokument.
- Kurzprofil, Hero-Beschreibung, Cover-Titel, KI- und Prozesstexte stehen unter „Zur Freigabe“.
- `pruefe_lauf.py` → `Lauf in Ordnung`; Figma-Überlappungsprüfung aus Task 7, Step 4 → `ueberlapp: []`.
- Die vier PDFs mit dem Nutzer ansehen.

- [ ] **Step 3: Nachlieferung**

Ein Logo oder einen Screen nachliefern („hier ist noch das Logo von X“).
Expected: nur die betroffenen Dokumente werden neu gebaut (Logos: Lebenslauf und Portfolio), keine Frage; neue Frames neben den alten, die Übergabe sagt das.

- [ ] **Step 4: Funde beheben**

Wie Task 7, Step 6.

---

### Task 9: Branch abschließen

- [ ] **Step 1: Alle Prüfungen**

```bash
python3 $BM/scripts/selbsttest.py
cd $S/newmonday-cv && python3 scripts/selbsttest.py | tail -1
cd $S/newmonday-portfolio && python3 scripts/selbsttest.py | tail -1
cd $S/newmonday-skillmatrix && python3 scripts/render_skillmatrix.py beispiel/skillmatrix.json $T/regress-sm/ 2>&1 | tail -1
cd $R && git status --short
```
Expected: alle vier grün, `git status` leer.

- [ ] **Step 2: Testordner aufräumen**

```bash
rm -rf /Users/florian/Desktop/bewerbermappe-test
```
Den Laufordner `/Users/florian/Desktop/Florian Feiler` und den des echten Kandidaten nur nach Rückfrage beim Nutzer löschen – dort liegen die Ergebnisse.

- [ ] **Step 3: Abschluss**

Skill `superpowers:finishing-a-development-branch` – er fragt den Nutzer nach Merge, PR oder Beibehalten.
