#!/usr/bin/env python3
"""Bereitet Zertifikate fuer die Zertifikatssektion der Skillmatrix auf.

    python3 scripts/zert_bilder.py zert1.pdf zert2.png zert3.jpg arbeit/zertifikate/

Nimmt beliebig viele Zertifikate als PDF oder Bild, das letzte Argument ist der
Zielordner. Aus PDFs wird die erste Seite gerendert (150 dpi), Bilder werden
nach RGB gewandelt und auf maximal 1600px Breite gebracht. Die Dateinamen
tragen eine laufende Nummer in der Reihenfolge der Argumente — am besten
neueste zuerst, so wie die Eintraege in der JSON stehen.

Jedes Bild gehoert danach in das Feld "bild" seines Zertifikats (SKILL.md,
Schritt 3). Im Layout wird es in seine Flaeche eingepasst: Seitenverhaeltnis
der Datei, nie beschnitten, nie verzerrt (scripts/zertifikate.py). Ein Format,
das stark vom Kachelformat 41 : 30 abweicht (assets/tokens.json,
zertbild.platz-format), wirkt deshalb klein — das Skript meldet solche
Ausreisser, damit vorher ein besserer Ausschnitt gesucht werden kann.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert

# Kachelformat (Breite / Hoehe) der Vorlage, aus assets/tokens.json.
KACHEL = design_system.laden()["komponenten"]["zertbild"]["platz-format"]
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
            hinweis = ("  — weicht deutlich vom Kachelformat ab, wirkt eingepasst "
                       "klein (beschnitten wird nichts)")
        ergebnisse.append(ausgabe)
        print(f"{ausgabe}  ({b}x{h}px, Verhaeltnis {b / h:.2f}){hinweis}")

    if ergebnisse:
        # Titel, Aussteller und Datum stehen auf dem Zertifikat - ablesen und
        # eintragen; erraten wird hier nichts.
        print("\nFuer die skillmatrix.json — je Zertifikat titel, aussteller und datum "
              "eintragen, neueste zuerst:")
        print("  \"zertifikate\": [")
        for e in ergebnisse:
            print(f"    {{\"titel\": \"\", \"aussteller\": \"\", \"datum\": \"\", "
                  f"\"bild\": \"{e}\"}},")
        print("  ]")
    else:
        print("Nichts aufbereitet.")


if __name__ == "__main__":
    main()
