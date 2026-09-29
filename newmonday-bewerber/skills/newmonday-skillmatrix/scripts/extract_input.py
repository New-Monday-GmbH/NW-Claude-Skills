#!/usr/bin/env python3
"""Liest einen eingehenden Lebenslauf, LinkedIn-Export oder ein Foto aus.

    python3 scripts/extract_input.py eingang.pdf arbeit/

Schreibt arbeit/text.txt (Layout erhalten) und arbeit/fotos/*.png. Fotos werden
nach Portraetformat gefiltert, auf das Format der Fotokarte (Bildbereich laut
assets/tokens.json, 435 x 433pt, fast quadratisch) beschnitten - mit dem Kopf in
der Mitte, siehe kopf_ausschnitt.py - und in Graustufen gewandelt, so wie im
New-Monday-Skillmatrix-Layout. Kontrollbilder liegen in arbeit/fotos/kontrolle/.

Die inhaltliche Zuordnung macht das Modell, nicht dieses Skript.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert

# Bildbereich der Fotokarte im Hero, aus assets/tokens.json. Anders als beim CV
# (79/106, hochkant) ist die Karte hier fast quadratisch.
_FOTO = design_system.laden()["komponenten"]["fotokarte"]
FOTO_BREITE, FOTO_HOEHE = _FOTO["bild-breite"], _FOTO["bild-hoehe"]
SEITENVERHAELTNIS = FOTO_BREITE / FOTO_HOEHE


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
    """Portraetkandidaten in Graustufen und aufs Kartenformat bringen.

    pruefen=False bei einem bewusst gelieferten Foto — dann greifen die
    Heuristiken nicht, die aus einem PDF Logos aussortieren.

    Den Ausschnitt setzt kopf_ausschnitt.py: Kopf waagerecht in der Mitte,
    Haaransatz bei 5 %, Kinn bei 70 % der Bildhoehe - so wie im Figma-Master,
    und frei vom Farbverlauf mit Name und Erfahrung unten auf der Karte. Das
    Kontrollbild dazu liegt in <ziel>/kontrolle/.
    """
    import kopf_ausschnitt
    pfad = Path(pfad)
    bild = kopf_ausschnitt.vorbereiten(pfad)   # nach EXIF gedreht, 8 Bit, ohne Transparenz
    b, h = bild.size
    if pruefen:
        if b < 80 or h < 80:
            return None                  # Logo oder Icon, kein Foto
        if b / h > 1.6:
            return None                  # stark querformatig: Banner oder Logo
        if entropie(bild.convert("L")) < 4.5:
            return None                  # zweifarbig: Logo, Alphamaske, Strichzeichnung

    ausgabe, bericht = kopf_ausschnitt.zuschneiden(pfad, ziel)
    print(kopf_ausschnitt.kurzbericht(ausgabe, bericht))
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
