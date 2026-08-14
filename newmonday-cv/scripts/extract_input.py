#!/usr/bin/env python3
"""Liest einen eingehenden Lebenslauf oder ein Foto aus.

    python3 scripts/extract_input.py eingang.pdf arbeit/

Schreibt arbeit/text.txt (Layout erhalten) und arbeit/fotos/*.png. Fotos werden
nach Portraetformat gefiltert, auf 79x106pt Seitenverhaeltnis beschnitten und in
Graustufen gewandelt — so wie im New-Monday-Layout.

Die inhaltliche Zuordnung macht das Modell, nicht dieses Skript.
"""
import subprocess
import sys
from pathlib import Path

SEITENVERHAELTNIS = 79 / 106  # Breite zu Hoehe im Layout


def text_lesen(pdf, ziel):
    ausgabe = ziel / "text.txt"
    subprocess.run(["pdftotext", "-layout", str(pdf), str(ausgabe)], check=True)
    return ausgabe


def bilder_lesen(pdf, ziel):
    roh = ziel / "roh"
    roh.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdfimages", "-png", str(pdf), str(roh / "img")], check=True)
    return sorted(roh.glob("*.png"))


def entropie(bild):
    """Bits pro Pixel. Fotos liegen ueber 5, Logos und Masken unter 3."""
    import math
    hist = bild.histogram()
    n = sum(hist)
    return -sum((c / n) * math.log2(c / n) for c in hist if c)


def portraet_zuschneiden(pfad, ziel, pruefen=True):
    """Portraetkandidaten in Graustufen und aufs Zielformat bringen.

    pruefen=False bei einem bewusst geliefertem Foto — dann greifen die
    Heuristiken nicht, die aus einem PDF Logos aussortieren.
    """
    from PIL import Image
    bild = Image.open(pfad)
    b, h = bild.size
    if pruefen:
        if b < 80 or h < 80:
            return None                  # Logo oder Icon, kein Foto
        if b / h > 1.1:
            return None                  # querformatig, eher ein Logo

    bild = bild.convert("L")
    if pruefen and entropie(bild) < 4.5:
        return None                      # zweifarbig: Logo, Alphamaske, Strichzeichnung
    ist = b / h
    if ist > SEITENVERHAELTNIS:          # zu breit: seitlich beschneiden
        neu_b = int(h * SEITENVERHAELTNIS)
        links = (b - neu_b) // 2
        bild = bild.crop((links, 0, links + neu_b, h))
    else:                                # zu hoch: unten beschneiden
        neu_h = int(b / SEITENVERHAELTNIS)
        bild = bild.crop((0, 0, b, neu_h))

    ausgabe = ziel / f"foto-{pfad.stem}.png"
    bild.save(ausgabe)
    return ausgabe


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    quelle, ziel = Path(sys.argv[1]), Path(sys.argv[2])
    fotos = ziel / "fotos"
    fotos.mkdir(parents=True, exist_ok=True)

    # Foto separat geliefert (z.B. aus LinkedIn): direkt aufbereiten.
    if quelle.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        ergebnis = portraet_zuschneiden(quelle, fotos, pruefen=False)
        print(f"Foto: {ergebnis}" if ergebnis else "Bild nicht verwertbar.")
        return

    print(f"Text: {text_lesen(quelle, ziel)}")

    treffer = []
    for bild in bilder_lesen(quelle, ziel):
        ergebnis = portraet_zuschneiden(bild, fotos)
        if ergebnis:
            treffer.append(ergebnis)

    if treffer:
        print("Portraetkandidaten (groesster zuerst pruefen):")
        for t in sorted(treffer, key=lambda p: p.stat().st_size, reverse=True):
            print(f"  {t}")
    else:
        print("Kein Portraet gefunden — Foto beim Kandidaten oder aus LinkedIn nachreichen.")


if __name__ == "__main__":
    main()
