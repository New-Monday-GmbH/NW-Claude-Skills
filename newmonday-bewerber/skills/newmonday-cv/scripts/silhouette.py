#!/usr/bin/env python3
"""Schreibt das Platzhalterbild der anonymen Fassung — SVG und PNG — aus der Vorlage.

    python3 scripts/silhouette.py

Das Bild selbst kommt aus dem Design: assets/silhouette-vorlage.svg ist die
Datei "user-pict-placeholder.svg", unveraendert so, wie New Monday sie geliefert
hat (Vorgabe vom 29.09.2026). Sie ist 80 x 110 gross, der Fotoplatz im Layout
aber raster.foto_breite x foto_hoehe (79 x 106pt, derselbe wie fuer das echte
Foto). Dieses Skript setzt die Vorlage deshalb so ein wie ein Foto mit
object-fit: cover — gleichmaessig skaliert, bis der Platz gefuellt ist, der
Ueberstand mittig beschnitten. Gezeichnet wird dabei nichts neu; nur die viewBox
aendert sich.

Es schreibt zwei Dateien, beide nicht von Hand aendern:

  assets/silhouette.svg   fuer PDF (WeasyPrint) und Figma (createNodeFromSvg)
  assets/silhouette.png   fuer --foto-raster, fuenffach (395 x 530px) gerastert

Eine neue Vorlage aus dem Design: als assets/silhouette-vorlage.svg ablegen,
dieses Skript laufen lassen, dann den Selbsttest.
"""
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokens  # noqa: E402  — erst nach sys.path.insert moeglich

ASSETS = Path(__file__).resolve().parent.parent / "assets"
VORLAGE = ASSETS / "silhouette-vorlage.svg"
PNG_MASSSTAB = 5

KOMMENTAR = """<!-- Platzhalter fuer die anonymisierte Fassung. Das Bild ist
     assets/silhouette-vorlage.svg ({vb} x {vh}), unveraendert; nur die viewBox
     setzt es in den Fotoplatz von {b} x {h}pt ein, gleichmaessig skaliert und
     mittig beschnitten wie ein Foto. Diese Datei schreibt scripts/silhouette.py
     aus der Vorlage, nicht von Hand aendern. Doppelte Bindestriche stehen in
     diesem Kommentar bewusst nicht: XML verbietet sie darin, und WeasyPrint
     laesst ein SVG, das es nicht parsen kann, still weg. -->"""


def zahl(wert):
    """Vier Nachkommastellen, ohne Nullen am Ende: 107.3418, 79, 1.3291."""
    return f"{wert:.4f}".rstrip("0").rstrip(".")


def zuschnitt(vx, vy, vw, vh, ziel):
    """Ausschnitt der viewBox, der das Seitenverhaeltnis ziel fuellt (cover, mittig)."""
    if vw / vh > ziel:
        nw = vh * ziel
        return vx + (vw - nw) / 2, vy, nw, vh
    nh = vw / ziel
    return vx, vy + (vh - nh) / 2, vw, nh


def svg_bauen(breite, hoehe):
    quelle = VORLAGE.read_text(encoding="utf-8")
    ET.fromstring(quelle)                               # kaputte Vorlage: hier laut
    kopf = re.search(r"<svg\b[^>]*>", quelle)
    if not kopf:
        raise SystemExit(f"{VORLAGE.name}: kein <svg>-Element gefunden")
    tag = kopf.group(0)
    box = re.search(r'viewBox\s*=\s*"([^"]+)"', tag)
    if box:
        vx, vy, vw, vh = (float(z) for z in re.split(r"[\s,]+", box.group(1).strip()))
    else:
        vx = vy = 0.0
        vw = float(re.search(r'\bwidth\s*=\s*"([\d.]+)', tag).group(1))
        vh = float(re.search(r'\bheight\s*=\s*"([\d.]+)', tag).group(1))
    nx, ny, nw, nh = zuschnitt(vx, vy, vw, vh, breite / hoehe)
    # Alle Attribute der Vorlage bleiben (xmlns, fill ...), nur Groesse und
    # Ausschnitt werden ersetzt.
    rest = re.sub(r'\s(?:width|height|viewBox)\s*=\s*"[^"]*"', "", tag[len("<svg"):-1])
    neu = (f'<svg width="{zahl(breite)}" height="{zahl(hoehe)}" '
           f'viewBox="{zahl(nx)} {zahl(ny)} {zahl(nw)} {zahl(nh)}"{rest}>')
    kommentar = KOMMENTAR.format(vb=zahl(vw), vh=zahl(vh), b=zahl(breite), h=zahl(hoehe))
    ergebnis = quelle[:kopf.start()] + neu + "\n" + kommentar + quelle[kopf.end():]
    ET.fromstring(ergebnis)
    return ergebnis


def png_bauen(svg_datei, breite, hoehe, ziel):
    """Das SVG so rastern, wie WeasyPrint es im PDF zeichnet — ueber ein PDF."""
    from weasyprint import HTML
    html = (f"<style>@page{{size:{breite}pt {hoehe}pt;margin:0}}body{{margin:0}}"
            f"img{{display:block;width:{breite}pt;height:{hoehe}pt}}</style>"
            f'<img src="{svg_datei.name}">')
    pdf = HTML(string=html, base_url=str(svg_datei.parent) + "/").write_pdf()
    try:
        import pypdfium2
    except ImportError:
        pypdfium2 = None
    if pypdfium2:
        dokument = pypdfium2.PdfDocument(pdf)
        try:
            bild = dokument[0].render(scale=PNG_MASSSTAB).to_pil().convert("RGB")
            bild.save(ziel, optimize=True)
        finally:
            dokument.close()
        return
    with tempfile.TemporaryDirectory() as tmp:
        quelle = Path(tmp) / "s.pdf"
        quelle.write_bytes(pdf)
        subprocess.run(["pdftoppm", "-r", str(72 * PNG_MASSSTAB), "-png", "-singlefile",
                        str(quelle), str(Path(ziel).with_suffix(""))], check=True)


def main():
    r = tokens.laden()["raster"]
    breite, hoehe = r["foto_breite"], r["foto_hoehe"]
    ziel_svg = ASSETS / "silhouette.svg"
    ziel_svg.write_text(svg_bauen(breite, hoehe), encoding="utf-8")
    print(f"assets/silhouette.svg geschrieben ({zahl(breite)} x {zahl(hoehe)}pt)")
    try:
        png_bauen(ziel_svg, breite, hoehe, ASSETS / "silhouette.png")
        print("assets/silhouette.png geschrieben")
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as fehler:
        print(f"silhouette.png NICHT neu geschrieben ({fehler}). Gebraucht wird "
              "WeasyPrint und pypdfium2 (pip install pypdfium2) oder pdftoppm.",
              file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
