#!/usr/bin/env python3
"""Regression fuer die Deck-Vorlagen. Nach JEDER Aenderung an templates/ oder
references/site-styles.css laufen lassen:

    scripts/.venv/bin/python tests/check_deck.py

Prueft zwei Dinge:

1. Je Folientyp: Vorlage + Referenz-Inhalt == die freigegebene Original-Folie.
2. Gesamt: das aus audits/worksdone.de-2026-07-16/deck.json gebaute Deck ist
   identisch mit der freigegebenen index.html.

Wenn du eine Vorlage BEWUSST aenderst, schlaegt das hier fehl -- das ist der Sinn.
Dann die Referenz bewusst nachziehen: tests/reference/slides/ + die freigegebene
index.html aktualisieren und im Commit begruenden.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from deck_render import render, TemplateError  # noqa: E402
from deck_content import enrich, ContentError  # noqa: E402

REF = ROOT / "tests" / "reference"
PY = str(ROOT / "scripts" / ".venv" / "bin" / "python")
DECK_JSON = ROOT / "audits/worksdone.de-2026-07-16/deck.json"
FREIGEGEBEN = ROOT / "audits/worksdone.de-2026-07-16/site/index.html"

# Typ -> Original-Folien (aus der deck.json abgeleitet, Reihenfolge = JSON-Listenreihenfolge)
ZUORDNUNG = {
    "cover": [
        "slide01"
    ],
    "ueber-nm": [
        "slide02"
    ],
    "credibility": [
        "slide03"
    ],
    "ueber-projekt": [
        "slide04"
    ],
    "redesign-fokus": [
        "slide05"
    ],
    "vorgehen": [
        "slide06"
    ],
    "summary": [
        "slide07"
    ],
    "scope": [
        "slide08"
    ],
    "divider": [
        "slide09",
        "slide12",
        "slide18",
        "slide24",
        "slide27"
    ],
    "persona": [
        "slide10"
    ],
    "positionierung": [
        "slide11"
    ],
    "erkenntnis": [
        "slide13",
        "slide14",
        "slide15",
        "slide16"
    ],
    "gut": [
        "slide17"
    ],
    "wettbewerber": [
        "slide19",
        "slide20",
        "slide21"
    ],
    "inspiration": [
        "slide22",
        "slide23"
    ],
    "findings": [
        "slide25"
    ],
    "roadmap": [
        "slide26"
    ],
    "wireframe": [
        "slide28",
        "slide29"
    ],
    "nextsteps": [
        "slide30"
    ],
    "projektablauf": [
        "slide31"
    ],
    "closing": [
        "slide32"
    ]
}


def normalize(html):
    h = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    h = re.sub(r">\s+<", "><", h)
    h = re.sub(r"\s*\n\s*", " ", h)
    h = re.sub(r"[ \t]{2,}", " ", h)
    return h.strip()


def erste_abweichung(a, b):
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    lo = max(0, i - 80)
    return f"    ab Zeichen {i}\n    SOLL: ...{a[lo:i+80]}\n    IST : ...{b[lo:i+80]}"


def teil1():
    print("1) Folientypen gegen die freigegebenen Original-Folien")
    fehler = 0
    for typ, slides in sorted(ZUORDNUNG.items()):
        tpl_p = ROOT / "templates" / "slides" / f"{typ}.html"
        json_p = REF / "content" / f"{typ}.json"
        if not tpl_p.exists():
            print(f"   FAIL {typ}: Vorlage fehlt"); fehler += 1; continue
        if not json_p.exists():
            print(f"   FAIL {typ}: Referenz-Inhalt fehlt"); fehler += 1; continue

        data = json.loads(json_p.read_text())
        items = data if isinstance(data, list) else [data]
        if len(items) != len(slides):
            print(f"   FAIL {typ}: {len(items)} Inhalte, {len(slides)} Folien"); fehler += 1; continue

        schlecht = []
        for item, name in zip(items, slides):
            try:
                got = render(tpl_p.read_text(), enrich({"type": typ, **item}))
            except (TemplateError, ContentError) as e:
                schlecht.append((name, f"    {e}")); continue
            want = (REF / "slides" / f"{name}.html").read_text()
            if normalize(got) != normalize(want):
                schlecht.append((name, erste_abweichung(normalize(want), normalize(got))))
        if schlecht:
            fehler += len(schlecht)
            for name, detail in schlecht:
                print(f"   FAIL {typ} / {name}\n{detail}")
        else:
            print(f"   OK   {typ:16s} ({len(slides)}x)")
    return fehler


def teil2():
    print("\n2) Gesamtes Referenz-Deck")
    # Das Referenz-Audit liegt unter audits/ und wird NICHT mitverteilt (2 GB).
    # Ohne es ist nur Teil 1 (Folientypen gegen Goldens) sinnvoll pruefbar.
    if not DECK_JSON.exists() or not FREIGEGEBEN.exists():
        print("   uebersprungen - Referenz-Audit nicht vorhanden (nur im Maintainer-Checkout)")
        return 0
    out = Path("/tmp/_deckcheck.html")
    r = subprocess.run([PY, str(ROOT / "scripts/build_deck.py"), str(DECK_JSON), "--out", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("   FAIL Build:", (r.stderr or r.stdout).strip())
        return 1

    a, b = normalize(FREIGEGEBEN.read_text()), normalize(out.read_text())
    if a == b:
        print(f"   OK   identisch mit der freigegebenen index.html ({len(a)} Zeichen)")
        return 0
    print("   FAIL gebautes Deck weicht ab")
    print(erste_abweichung(a, b))
    return 1


if __name__ == "__main__":
    f = teil1() + teil2()
    print()
    if f:
        print(f"FEHLGESCHLAGEN: {f} Abweichung(en)")
        sys.exit(1)
    print("Alles gruen — die Vorlagen reproduzieren das freigegebene Deck exakt.")
