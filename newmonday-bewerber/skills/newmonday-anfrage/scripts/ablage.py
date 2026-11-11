#!/usr/bin/env python3
"""Ablage einer Anfrage unter Bewerberunterlagen/.

    ablage.py anlegen --anfrage "<ID> <Stelle>" --kandidat "Vorname Nachname" [--root <pfad>]
        legt <root>/<anfrage>/<kandidat>/_arbeit/ an und gibt den Laufordner (_arbeit) aus
    ablage.py einsammeln <kandidatenordner>
        kopiert die PDFs aus _arbeit/ausgabe/ in den Kandidatenordner, benannt als
        "New Monday - <Name> - CV.pdf", "New Monday - <V. N.> - CV.pdf" (anonym),
        "… - Skillmatrix.pdf", "… - Skillmatrix A4.pdf", "… - Portfolio.pdf"
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path.home() / "Desktop" / "Bewerberunterlagen"
# Reihenfolge zählt: „Skillmatrix A4“ vor „Skillmatrix“
ARTEN = [("skillmatrix a4", "Skillmatrix A4"), ("skillmatrix", "Skillmatrix"),
         ("portfolio", "Portfolio"), ("cv", "CV")]


def sauber(text: str) -> str:
    """Ordnername ohne Pfadtrenner und doppelte Leerzeichen."""
    return re.sub(r"\s+", " ", re.sub(r'[/\\:*?"<>|]', " ", text)).strip()


def initialen(name: str) -> str:
    return " ".join(f"{teil[0].upper()}." for teil in name.split() if teil)


def anlegen(root: Path, anfrage: str, kandidat: str) -> Path:
    lauf = root / sauber(anfrage) / sauber(kandidat) / "_arbeit"
    lauf.mkdir(parents=True, exist_ok=True)
    return lauf


def zielname(datei: str, kandidat: str) -> str | None:
    """Neuer Name für ein gebautes PDF, None wenn es keins der fünf ist."""
    klein = datei.lower().removesuffix(".pdf")
    art = next((neu for schluessel, neu in ARTEN if klein.endswith(schluessel)), None)
    if art is None:
        return None
    anonym = art == "CV" and initialen(kandidat) in datei and kandidat not in datei
    return f"New Monday - {initialen(kandidat) if anonym else kandidat} - {art}.pdf"


def einsammeln(kandidatenordner: Path) -> list[tuple[str, str]]:
    ausgabe = kandidatenordner / "_arbeit" / "ausgabe"
    kandidat = kandidatenordner.name
    kopiert = []
    for pdf in sorted(ausgabe.glob("*.pdf")):
        neu = zielname(pdf.name, kandidat)
        if neu:
            shutil.copy2(pdf, kandidatenordner / neu)
            kopiert.append((pdf.name, neu))
    return kopiert


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="befehl", required=True)
    a = sub.add_parser("anlegen")
    a.add_argument("--anfrage", required=True)
    a.add_argument("--kandidat", required=True)
    a.add_argument("--root", type=Path, default=ROOT)
    e = sub.add_parser("einsammeln")
    e.add_argument("kandidatenordner", type=Path)
    args = p.parse_args()
    if args.befehl == "anlegen":
        print(anlegen(args.root.expanduser(), args.anfrage, args.kandidat))
        return
    kopiert = einsammeln(args.kandidatenordner)
    for alt, neu in kopiert:
        print(f"{alt} → {neu}")
    if len(kopiert) < 5:
        sys.exit(f"Nur {len(kopiert)} von 5 PDFs gefunden – fehlt eins in _arbeit/ausgabe/?")


if __name__ == "__main__":
    main()
