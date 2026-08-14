#!/usr/bin/env python3
"""Prueft nach der Installation, ob die ganze Kette laeuft.

    python3 scripts/selbsttest.py

Rendert den mitgelieferten Beispiel-Lebenslauf in ein temporaeres Verzeichnis
und kontrolliert das Ergebnis: Seitenzahl, A4-Format, eingebettete Schriften,
Logos und Foto. Schreibt nichts in den Skill-Ordner.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def pruefe(pdf):
    fehler = []
    from pypdf import PdfReader
    leser = PdfReader(str(pdf))

    seiten = len(leser.pages)
    if seiten < 2:
        fehler.append(f"nur {seiten} Seite(n) — erwartet werden mehrere")

    kasten = leser.pages[0].mediabox
    breite, hoehe = round(float(kasten.width)), round(float(kasten.height))
    if not (590 <= breite <= 600 and 838 <= hoehe <= 846):
        fehler.append(f"Seitenformat {breite}x{hoehe}pt statt A4 (595x842)")

    schriften = set()
    bilder = 0
    for seite in leser.pages:
        mittel = seite.get("/Resources", {})
        for f in (mittel.get("/Font", {}) or {}).values():
            schriften.add(str(f.get_object().get("/BaseFont", "")))
        bilder += len(mittel.get("/XObject", {}) or {})
    if not any("Inter" in f for f in schriften):
        fehler.append(f"Inter nicht eingebettet, gefunden: {sorted(schriften) or 'keine'}")
    if bilder == 0:
        fehler.append("keine Bilder im PDF — Logos und Foto fehlen")

    return seiten, breite, hoehe, len(schriften), bilder, fehler


# Nachbau einer oeffentlichen Profilseite: oben das Foto der Person im
# og:image-Tag, darunter — wie im Original unter "Weitere aehnliche Profile" —
# fremde Gesichter in GROESSERER Variante. Wer nach Bildgroesse auswaehlt,
# laedt hier ein falsches Gesicht.
PROFILSEITE = '''
<meta property="og:image" content="https://media.licdn.com/dms/image/v2/PERSON/profile-displayphoto-shrink_200_200/0?e=1&amp;t=x" />
<img src="https://media.licdn.com/dms/image/v2/FREMD1/profile-displayphoto-shrink_400_400/0?e=1\\u0026t=y">
<img src="https://media.licdn.com/dms/image/v2/FREMD2/profile-displayphoto-scale_400_400/0?e=1\\u0026t=z">
'''


def pruefe_linkedin_auswahl():
    """Das Foto muss von der Person kommen, nicht aus der Seitenspalte."""
    sys.path.insert(0, str(WURZEL / "scripts"))
    from linkedin_foto import foto_urls, url_normalisieren

    treffer = foto_urls(PROFILSEITE)
    if not treffer:
        return ["LinkedIn: kein Foto in der Testseite erkannt"]
    fremd = [u for u in treffer if "/PERSON/" not in u]
    if fremd:
        return [f"LinkedIn: fremdes Gesicht ausgewaehlt — {fremd[0][:80]}"]

    # Die Eingabeformen, die Nutzer tatsaechlich schicken.
    for eingabe in ("https://www.linkedin.com/in/timo-muster/",
                    "https://de.linkedin.com/in/timo-muster?originalSubdomain=de",
                    "timo-muster"):
        if url_normalisieren(eingabe)[1] != "timo-muster":
            return [f"LinkedIn: {eingabe!r} falsch normalisiert"]
    return []


def main():
    beispiel = WURZEL / "beispiel" / "cv.json"
    if not beispiel.exists():
        raise SystemExit(f"Beispieldaten fehlen: {beispiel}")

    with tempfile.TemporaryDirectory() as tmp:
        ziel = Path(tmp) / "selbsttest.pdf"
        lauf = subprocess.run(
            [sys.executable, str(WURZEL / "scripts" / "render_cv.py"),
             str(beispiel), str(ziel)],
            capture_output=True, text=True, cwd=str(WURZEL),
        )
        if lauf.returncode != 0 or not ziel.exists():
            print("Rendern fehlgeschlagen:\n" + (lauf.stderr or lauf.stdout))
            print("\npython3 scripts/pruefe_umgebung.py zeigt, was fehlt.")
            raise SystemExit(1)

        print(lauf.stdout.strip())
        seiten, breite, hoehe, schriften, bilder, fehler = pruefe(ziel)

    fehler += pruefe_linkedin_auswahl()

    print(f"\n  Seiten:    {seiten}")
    print(f"  Format:    {breite} x {hoehe} pt")
    print(f"  Schriften: {schriften} eingebettet")
    print(f"  Bilder:    {bilder} (Logos und Foto)")
    print(f"  LinkedIn:  Fotoauswahl geprueft (ohne Netz)")

    if fehler:
        print("\nProbleme:")
        for f in fehler:
            print(f"  - {f}")
        raise SystemExit(1)

    print("\nSelbsttest bestanden. Der Skill ist einsatzbereit.")


if __name__ == "__main__":
    main()
