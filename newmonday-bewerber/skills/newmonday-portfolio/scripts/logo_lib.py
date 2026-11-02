#!/usr/bin/env python3
"""Wo die Logobibliothek liegt: zwei Ordner, ein Bestand.

Portfolio und Lebenslauf brauchen dieselben Firmenlogos. Grundstock ist
assets/logos/ des Skills `newmonday-cv`, wenn er daneben liegt (im Plugin
immer), sonst der eigene assets/logos/. Der Grundstock kommt mit dem Repo bzw.
dem Plugin und wird bei der Plugin-Installation mit jedem Update ersetzt -
deshalb schreibt kein Skript dort hinein.

Neue Funde landen in ~/.newmonday/logos/ (anders: Umgebungsvariable
NEWMONDAY_HOME), gemeinsam fuer beide Skills. Der Ordner liegt ausserhalb des
Plugin-Caches und ueberlebt jedes Update; ein Logo, das fuer einen Lebenslauf
gesucht wurde, steht beim naechsten Portfolio schon bereit. Ein Pfleger
uebernimmt die Funde ins Repo (newmonday-cv/scripts/logos_uebernehmen.py).

Gesucht wird zuerst in den eigenen Funden, dann im Grundstock: eine bessere
Fassung eines Logos ersetzt so die alte, ohne den Grundstock anzufassen.

    python3 scripts/logo_lib.py        # beide Ordner und was darin liegt
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
_GETEILT = SKILL.parent / "newmonday-cv" / "assets" / "logos"
GRUNDSTOCK = _GETEILT if _GETEILT.is_dir() else SKILL / "assets" / "logos"
ENDUNGEN = (".svg", ".png", ".jpg")


def daten() -> Path:
    """Dauerhafter Ordner fuer alles, was die Skills unterwegs sammeln."""
    return Path(os.environ.get("NEWMONDAY_HOME") or Path.home() / ".newmonday").expanduser()


def bibliothek() -> Path:
    """Hier landen neue Logos. Angelegt wird er erst beim Schreiben."""
    return daten() / "logos"


def ordner() -> list[Path]:
    """Alle Ordner mit Logos, in Suchreihenfolge."""
    ergebnis = []
    for o in (bibliothek(), GRUNDSTOCK):
        if o.is_dir() and o.resolve() not in [e.resolve() for e in ergebnis]:
            ergebnis.append(o)
    return ergebnis


def suche(name: str) -> Path | None:
    """Findet eine Logodatei im Bestand - mit oder ohne Endung im Namen."""
    if not name:
        return None
    for o in ordner():
        if (o / name).is_file():
            return o / name
    for o in ordner():
        for endung in ENDUNGEN:
            kandidat = o / (Path(name).stem + endung)
            if kandidat.is_file():
                return kandidat
    return None


def bestand() -> dict[str, str]:
    """Dateiname ohne Endung -> Dateiname, ueber beide Ordner."""
    vorhanden: dict[str, str] = {}
    for o in reversed(ordner()):            # eigene Funde ueberschreiben
        vorhanden.update({p.stem: p.name for p in o.iterdir()
                          if p.suffix in (".svg", ".png")})
    return vorhanden


def aliase() -> dict[str, str]:
    """aliase.json aus beiden Ordnern; eigene Eintraege gewinnen."""
    karte: dict[str, str] = {}
    for o in reversed(ordner()):
        datei = o / "aliase.json"
        if datei.is_file():
            karte.update(json.loads(datei.read_text(encoding="utf-8")))
    return karte


def neue() -> list[Path]:
    """Eigene Funde, die im Grundstock fehlen oder dort anders aussehen."""
    eigen = bibliothek()
    if not eigen.is_dir() or eigen.resolve() == GRUNDSTOCK.resolve():
        return []
    ergebnis = []
    for p in sorted(eigen.iterdir()):
        if p.suffix not in ENDUNGEN + (".json",) or p.name.startswith("."):
            continue
        alt = GRUNDSTOCK / p.name
        if not alt.is_file() or alt.read_bytes() != p.read_bytes():
            ergebnis.append(p)
    return ergebnis


if __name__ == "__main__":
    for o in (bibliothek(), GRUNDSTOCK):
        anzahl = len([p for p in o.iterdir() if p.suffix in ENDUNGEN]) if o.is_dir() else 0
        art = "neue Funde" if o == bibliothek() else "Grundstock"
        print(f"{o}  ({art}): {anzahl} Logos")
    offen = neue()
    if offen:
        print(f"\nNoch nicht im Repo: {', '.join(p.name for p in offen)}")
        print("Pfleger: python3 ../newmonday-cv/scripts/logos_uebernehmen.py <repo-checkout>")
