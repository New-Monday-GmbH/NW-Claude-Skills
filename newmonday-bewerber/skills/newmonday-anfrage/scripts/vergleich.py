#!/usr/bin/env python3
"""Prüft, dass eine angepasste JSON nichts aus dem Bestand verloren hat.

    vergleich.py <bestand.json> <neu.json> [--ausnahmen <datei>]

Jeder Textwert des Bestands muss in der neuen Fassung noch stehen: seine
Wörter in derselben Reihenfolge innerhalb eines neuen Werts – Einschübe und
angehängte Sätze sind erlaubt, Streichungen nicht. Umsortieren ist erlaubt,
Pfade spielen keine Rolle, Bild- und Dateipfade zählen nicht. Für die Felder,
die newmonday-anfrage austauschen darf (SKILL.md, „Nichts entfernen“), gilt:
  FREI      – dürfen ganz neu sein
  WOANDERS  – ein herausgefallener Eintrag muss irgendwo sonst im Dokument stehen
--ausnahmen: Datei mit je einem alten Text pro Zeile, dessen Änderung der
Nutzer freigegeben hat (z. B. Kürzungen fürs Layout); er wird nicht gemeldet.
Exit 1, wenn etwas fehlt.
"""
import argparse
import json
import re
import sys

FREI = {"person.kurzprofil", "person.schwerpunkte", "person.beschreibung", "anfrage"}
WOANDERS = {"person.top_kenntnisse", "person.kenntnisse"}
DATEIENDUNGEN = (".png", ".jpg", ".jpeg", ".svg", ".pdf", ".webp")


def blaetter(knoten, pfad=""):
    """(Pfad ohne Listenindex, Text) für jeden Textwert."""
    if isinstance(knoten, dict):
        for k, v in knoten.items():
            yield from blaetter(v, f"{pfad}.{k}" if pfad else k)
    elif isinstance(knoten, list):
        for v in knoten:
            yield from blaetter(v, pfad)
    elif isinstance(knoten, str) and knoten.strip():
        yield pfad, knoten.strip()


def woerter(text: str) -> list[str]:
    return re.findall(r"\w[\w&+./-]*\w|\w", text.lower())


def enthalten(alt: list[str], neu: list[str]) -> bool:
    """Stehen alle Wörter von alt in derselben Reihenfolge in neu?"""
    rest = iter(neu)
    return all(w in rest for w in alt)


def fehlend(bestand, neu, ausnahmen=frozenset()) -> list[tuple[str, str]]:
    neue = [woerter(t) for _, t in blaetter(neu)]
    alle = " " + " ".join(" ".join(ws) for ws in neue) + " "
    weg = []
    for pfad, text in blaetter(bestand):
        if (pfad in FREI or text in ausnahmen or text.startswith("/")
                or text.lower().endswith(DATEIENDUNGEN)):
            continue
        alt = woerter(text)
        if pfad in WOANDERS:  # als Begriff irgendwo im Dokument
            da = f" {' '.join(alt)} " in alle
        else:
            da = any(enthalten(alt, ws) for ws in neue)
        if not da:
            weg.append((pfad, text))
    return weg


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("bestand")
    p.add_argument("neu")
    p.add_argument("--ausnahmen")
    a = p.parse_args()
    bestand, neu = (json.load(open(x, encoding="utf-8")) for x in (a.bestand, a.neu))
    ausnahmen = frozenset(l.strip() for l in open(a.ausnahmen, encoding="utf-8")) if a.ausnahmen else frozenset()
    weg = fehlend(bestand, neu, ausnahmen)
    for pfad, text in weg:
        print(f"FEHLT  {pfad}: {text[:160]}")
    print(f"{len(weg)} Werte des Bestands fehlen." if weg else "Nichts entfernt.")
    sys.exit(1 if weg else 0)


if __name__ == "__main__":
    main()
