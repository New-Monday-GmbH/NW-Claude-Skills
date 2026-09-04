#!/usr/bin/env python3
"""Bereitet Zertifikate fuer das Bilderraster der Skillmatrix auf.

    python3 scripts/zert_bilder.py zert1.pdf zert2.png zert3.jpg arbeit/zertifikate/

Nimmt beliebig viele Zertifikate als PDF oder Bild, das letzte Argument ist der
Zielordner. Aus PDFs wird die erste Seite gerendert (150 dpi), Bilder werden
nach RGB gewandelt und auf maximal 1600px Breite gebracht. Die Reihenfolge der
Argumente ist die Reihenfolge im Raster — die Dateinamen tragen deshalb eine
laufende Nummer, damit sie sortiert bleiben.

Die Kacheln im Layout sind 395 x 284pt und werden mittig gefuellt (cover):
stark abweichende Formate verlieren an den Raendern etwas Bild. Das Skript
meldet je Datei das Seitenverhaeltnis, damit Ausreisser auffallen, bevor sie
beschnitten im Dokument stehen.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Seitenverhaeltnis der Kachel im Raster (Breite / Hoehe), siehe skillmatrix.css.
KACHEL = 395 / 284
MAX_BREITE = 1600


def pdf_rendern(pdf, ziel_png):
    """Erste Seite als PNG. pdftoppm schreibt <prefix>-1.png o.ae., daher umbenennen."""
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "seite"
        subprocess.run(
            ["pdftoppm", "-png", "-r", "150", "-f", "1", "-l", "1",
             str(pdf), str(prefix)],
            check=True,
        )
        treffer = sorted(Path(tmp).glob("seite*.png"))
        if not treffer:
            return False
        shutil.move(str(treffer[0]), str(ziel_png))
    return True


def bild_aufbereiten(pfad, ziel_png):
    from PIL import Image
    bild = Image.open(pfad).convert("RGB")
    if bild.width > MAX_BREITE:
        bild = bild.resize(
            (MAX_BREITE, round(bild.height * MAX_BREITE / bild.width)))
    bild.save(ziel_png)
    return True


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    quellen, ziel = sys.argv[1:-1], Path(sys.argv[-1])
    ziel.mkdir(parents=True, exist_ok=True)

    from PIL import Image
    ergebnisse = []
    for nr, quelle in enumerate(map(Path, quellen), start=1):
        ausgabe = ziel / f"zert-{nr:02d}-{quelle.stem}.png".replace(" ", "-")
        if quelle.suffix.lower() == ".pdf":
            ok = pdf_rendern(quelle, ausgabe)
        elif quelle.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            ok = bild_aufbereiten(quelle, ausgabe)
        else:
            print(f"Uebersprungen (kein PDF/Bild): {quelle}")
            continue
        if not ok:
            print(f"Nicht lesbar: {quelle}")
            continue
        b, h = Image.open(ausgabe).size
        abweichung = (b / h) / KACHEL
        hinweis = ""
        if abweichung > 1.25 or abweichung < 0.8:
            hinweis = ("  — weicht deutlich vom Kachelformat ab, wird im "
                       "Raster mittig beschnitten")
        ergebnisse.append(ausgabe)
        print(f"{ausgabe}  ({b}x{h}px, Verhaeltnis {b / h:.2f}){hinweis}")

    if ergebnisse:
        print("\nFuer die skillmatrix.json, in dieser Reihenfolge:")
        print("  \"zertifikat_bilder\": [")
        for e in ergebnisse:
            print(f"    \"{e}\",")
        print("  ]")
    else:
        print("Nichts aufbereitet.")


if __name__ == "__main__":
    main()
