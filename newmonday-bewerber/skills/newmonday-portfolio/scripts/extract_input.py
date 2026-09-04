#!/usr/bin/env python3
"""Liest ein Kandidaten-PDF aus: Text, Projektbilder, Portraetkandidaten.

    python3 scripts/extract_input.py portfolio.pdf arbeit/
    python3 scripts/extract_input.py lebenslauf.pdf arbeit/cv/
    python3 scripts/extract_input.py foto.jpg arbeit/          # einzelnes Bild

Schreibt nach <ziel>/:
    text.txt          der gesamte Text, seitenweise getrennt
    bilder/           alle brauchbaren Bilder in Originalaufloesung
    fotos/            Portraetkandidaten, in Graustufen und aufs Layoutformat
                      (363 x 445pt) beschnitten
    bilder.txt        je Bild Groesse und wofuer die Aufloesung reicht

Warum getrennte Ordner: Ein Portfolio-PDF enthaelt Logos, Screenshots, Fotos und
Alphamasken durcheinander. Was ein Portraet sein kann, wird ueber Seitenformat
und Farbverteilung vorsortiert - sicher ist das nicht, deshalb sind die
Kandidaten anzusehen, bevor einer ins Dokument geht.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

# Zielflaechen des Layouts in Punkt. Ein Bild sollte mindestens so viele Pixel
# haben wie die Flaeche Punkte breit ist, sonst wirkt es auf der Folie weich.
FLAECHEN = {"Arbeitsweise/Vollbild": 960, "Projektkopf": 760, "Lösung/Summary": 1020}
FOTO_B, FOTO_H = 363, 445


def bewertung(breite: int, hoehe: int) -> str:
    faktor = breite / max(FLAECHEN.values())
    if faktor >= 2:
        return "sehr gut (auch für Druck)"
    if faktor >= 1:
        return "gut"
    if faktor >= 0.7:
        return "grenzwertig – auf der Folie sichtbar weich"
    return "zu klein – bessere Fassung anfragen"


def portraet_moeglich(im) -> bool:
    """Hochformat oder quadratisch, gross genug, und farblich nicht flach.
    Logos und Alphamasken fallen dadurch heraus, Screenshots meist auch."""
    if im.width < 200 or im.height < 260:
        return False
    if im.width / im.height > 1.15:
        return False
    grau = im.convert("L")
    stufen = [n for n in grau.histogram() if n]
    return len(stufen) > 40


def foto_zuschnitt(im):
    """Auf das Layoutformat beschneiden und entfaerben - so, wie es auf der
    Profilseite steht. Der Ausschnitt sitzt oben, weil dort der Kopf ist."""
    ziel = FOTO_B / FOTO_H
    b, h = im.size
    if b / h > ziel:
        neu_b = int(h * ziel)
        kasten = ((b - neu_b) // 2, 0, (b - neu_b) // 2 + neu_b, h)
    else:
        neu_h = int(b / ziel)
        oben = int((h - neu_h) * 0.15)
        kasten = (0, oben, b, oben + neu_h)
    return im.crop(kasten).convert("L").convert("RGB")


def aus_pdf(quelle: Path, ziel: Path) -> None:
    import fitz
    from PIL import Image

    doc = fitz.open(quelle)
    text = []
    zeilen = []
    n = 0
    for nr, page in enumerate(doc, 1):
        text.append(f"───────── Seite {nr} ─────────\n{page.get_text()}")
        gesehen = set()
        for info in page.get_image_info(xrefs=True):
            xref = info.get("xref")
            if not xref or xref in gesehen:
                continue
            gesehen.add(xref)
            try:
                roh = doc.extract_image(xref)
                im = Image.open(io.BytesIO(roh["image"])).convert("RGB")
            except Exception:
                continue
            if im.width < 120 or im.height < 120:
                continue                      # Icons, Trennlinien, Masken
            n += 1
            name = f"s{nr:02d}-{n:02d}.jpg"
            im.save(ziel / "bilder" / name, quality=90, optimize=True)
            zeilen.append(f"{name:16} {im.width}x{im.height}px   {bewertung(im.width, im.height)}")
            if portraet_moeglich(im):
                foto_zuschnitt(im).save(ziel / "fotos" / name, quality=92)

    (ziel / "text.txt").write_text("\n".join(text), encoding="utf-8")
    (ziel / "bilder.txt").write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    fotos = sorted((ziel / "fotos").iterdir())
    print(f"{len(zeilen)} Bilder, {len(fotos)} Porträtkandidaten, "
          f"{sum(len(t) for t in text)} Zeichen Text")
    if fotos:
        print("Porträtkandidaten (ansehen, bevor einer ins Dokument geht):")
        for f in fotos:
            print("  " + str(f))


def aus_bild(quelle: Path, ziel: Path) -> None:
    from PIL import Image
    with Image.open(quelle) as im:
        im = im.convert("RGB")
        foto_zuschnitt(im).save(ziel / "fotos" / (quelle.stem + ".jpg"), quality=92)
        im.save(ziel / "bilder" / (quelle.stem + ".jpg"), quality=92)
    print(f"{quelle.name}: {im.width}x{im.height}px – {bewertung(im.width, im.height)}")
    print(f"Zugeschnitten: {ziel / 'fotos' / (quelle.stem + '.jpg')}")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    quelle, ziel = Path(sys.argv[1]), Path(sys.argv[2])
    for unter in ("bilder", "fotos"):
        (ziel / unter).mkdir(parents=True, exist_ok=True)
    if quelle.suffix.lower() == ".pdf":
        aus_pdf(quelle, ziel)
    else:
        aus_bild(quelle, ziel)


if __name__ == "__main__":
    main()
