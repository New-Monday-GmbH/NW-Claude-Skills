#!/usr/bin/env python3
"""Wo die Logobibliothek liegt.

Portfolio und Lebenslauf brauchen dieselben Firmenlogos. Liegt der Skill
`newmonday-cv` daneben, wird dessen Bestand genutzt und ergaenzt - dann gibt es
einen Pflegeort statt zwei, und ein Logo, das fuer einen Lebenslauf gesucht
wurde, steht beim naechsten Portfolio schon bereit.

Fehlt der CV-Skill, faellt alles auf den eigenen Ordner zurueck; der Skill
funktioniert dann fuer sich allein, nur ohne den vorhandenen Bestand.
"""
from __future__ import annotations

from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def bibliothek() -> Path:
    geteilt = SKILL.parent / "newmonday-cv" / "assets" / "logos"
    ordner = geteilt if geteilt.is_dir() else SKILL / "assets" / "logos"
    ordner.mkdir(parents=True, exist_ok=True)
    return ordner


def suche(name: str) -> Path | None:
    """Findet eine Logodatei im Bestand - mit oder ohne Endung im Namen."""
    if not name:
        return None
    ordner = bibliothek()
    direkt = ordner / name
    if direkt.exists():
        return direkt
    for endung in (".svg", ".png", ".jpg"):
        kandidat = ordner / (Path(name).stem + endung)
        if kandidat.exists():
            return kandidat
    return None


if __name__ == "__main__":
    ordner = bibliothek()
    dateien = sorted(p.name for p in ordner.iterdir()
                     if p.suffix in (".svg", ".png", ".jpg"))
    geteilt = "gemeinsam mit newmonday-cv" if "newmonday-cv" in str(ordner) else "eigen"
    print(f"{ordner}  ({geteilt})\n{len(dateien)} Logos")
