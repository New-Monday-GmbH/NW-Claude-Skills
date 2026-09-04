#!/usr/bin/env python3
"""Bestimmt die Markenfarbe eines Kunden aus dessen Logo.

    python3 scripts/markenfarbe.py deutsche-bank.svg
    python3 scripts/markenfarbe.py portfolio.json --setzen

Die Loesungsseiten liegen auf der Farbe des Kunden - apoBank dunkelblau, Yareto
orange, Boeing blau. Diese Farbe steckt im Logo, muss dort aber gesucht werden:
Gefragt ist die kraeftigste Markenfarbe, nicht der haeufigste Pixel. Ein Logo
ist meistens ueberwiegend weiss oder schwarz, und genau diese beiden Werte
taugen nicht als Seitenfarbe.

Findet das Skript nichts Farbiges, gibt es nichts zurueck. Dann bleibt die
Flaeche neutral - das ist richtiger als ein geratener Ton, denn eine falsche
Markenfarbe faellt beim Kunden sofort auf.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logo_lib import suche  # noqa: E402

# Ein Ton muss satt und weder fast weiss noch fast schwarz sein, sonst ist er
# keine Marken-, sondern eine Zeichenfarbe.
# Nach oben wird nicht begrenzt: Gelb und Orange sind bei voller Helligkeit
# satt und trotzdem echte Markenfarben. Fast-Weiss faellt schon ueber die
# Saettigung heraus, dafuer braucht es keine zweite Schranke.
MIN_SAETTIGUNG = 0.25
HELLIGKEIT = (0.10, 1.0)


def rgb_hsv(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    hi, lo = max(r, g, b), min(r, g, b)
    s = 0 if hi == 0 else (hi - lo) / hi
    return s, hi


def taugt(rgb) -> bool:
    s, v = rgb_hsv(*rgb)
    return s >= MIN_SAETTIGUNG and HELLIGKEIT[0] <= v <= HELLIGKEIT[1]


def svg_rastern(pfad: Path):
    """SVG in Pixel wandeln, damit die Flaeche zaehlt und nicht die Zahl der
    Farbangaben im Quelltext. Ein Logo nennt Rot vielleicht zwanzigmal fuer
    zwanzig kleine Pfade und Gelb einmal fuer die grosse Flaeche dahinter -
    im Quelltext gewinnt dann das Falsche."""
    import tempfile

    from weasyprint import HTML
    import fitz
    from PIL import Image

    html = (f'<style>@page{{size:400px 400px;margin:0}}body{{margin:0}}'
            f'img{{width:400px}}</style><img src="{pfad.resolve().as_uri()}">')
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "l.pdf"
        HTML(string=html).write_pdf(str(pdf))
        seite = fitz.open(pdf)[0]
        pix = seite.get_pixmap(matrix=fitz.Matrix(1, 1))
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def aus_svg(pfad: Path):
    try:
        return farbzaehler(svg_rastern(pfad))
    except Exception:
        pass
    # Ausweichweg ohne Renderer: die Farbangaben im Quelltext auszaehlen.
    zaehler = Counter()
    for treffer in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})",
                              pfad.read_text(errors="ignore")):
        h = treffer if len(treffer) == 6 else "".join(x * 2 for x in treffer)
        rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        if taugt(rgb):
            zaehler[rgb] += 1
    return zaehler


def farbzaehler(im):
    """Zaehlt Markenfarben nach Flaeche. Gerundet wird in 24er-Stufen, damit
    Verlaeufe und Antialiasing nicht als eigene Farben zaehlen; gemerkt wird
    trotzdem der genaue Ton, damit am Ende die echte Marken-Hex herauskommt
    und nicht der Mittelpunkt eines Rasterfachs."""
    if im.width > 240:
        im = im.resize((240, max(1, int(240 * im.height / im.width))))
    zaehler, genau = Counter(), {}
    for rgb in im.convert("RGB").getdata():
        if not taugt(rgb):
            continue
        fach = tuple(v // 24 * 24 + 12 for v in rgb)
        zaehler[fach] += 1
        genau.setdefault(fach, Counter())[rgb] += 1
    zaehler.genau = genau
    return zaehler


def aus_bild(pfad: Path):
    from PIL import Image
    with Image.open(pfad) as im:
        return farbzaehler(im)


def farbe(datei: str | Path) -> str | None:
    pfad = Path(datei)
    if not pfad.exists():
        pfad = suche(str(datei)) or pfad
    if not pfad.exists():
        return None
    zaehler = aus_svg(pfad) if pfad.suffix.lower() == ".svg" else aus_bild(pfad)
    if not zaehler:
        return None
    # Unter den haeufigsten Kandidaten den saettigsten nehmen: der haeufigste
    # ist oft ein blasser Verlaufsschritt, die Marke ist der kraeftige Ton.
    top = zaehler.most_common(6)
    fach = max(top, key=lambda p: rgb_hsv(*p[0])[0] * (p[1] ** 0.3))[0]
    genau = getattr(zaehler, "genau", {}).get(fach)
    rgb = genau.most_common(1)[0][0] if genau else fach
    return "#%02x%02x%02x" % rgb


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    quelle = Path(sys.argv[1])

    if quelle.suffix == ".json":
        daten = json.loads(quelle.read_text(encoding="utf-8"))
        setzen = "--setzen" in sys.argv
        for pr in daten.get("projekte", []):
            # Bei mehreren Logos (Liste) zaehlt das erste - die Kopfseite
            # fuehrt es an, und eine Flaeche traegt nur eine Farbe.
            logo = pr.get("logo")
            if isinstance(logo, list):
                logo = next((l for l in logo if l), None)
            gefunden = farbe(logo) if logo else None
            stand = pr.get("markenfarbe")
            print(f"{pr.get('kunde', '?'):28} {gefunden or '– nichts Farbiges gefunden'}"
                  + (f"   (gesetzt: {stand})" if stand else ""))
            if setzen and gefunden and not stand:
                pr["markenfarbe"] = gefunden
        if setzen:
            quelle.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
            print("\nIn die portfolio.json eingetragen. Farben vor dem Rendern ansehen:")
            print("ein falscher Markenton fällt beim Kunden sofort auf.")
        return

    print(farbe(quelle) or "nichts Farbiges gefunden – Fläche bleibt neutral")


if __name__ == "__main__":
    main()
