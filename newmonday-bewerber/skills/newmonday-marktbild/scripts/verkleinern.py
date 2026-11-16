#!/usr/bin/env python3
"""PDF für Plattformen mit Größengrenze verkleinern (GULP: 5 MB je Datei).

    verkleinern.py <ein.pdf> <aus.pdf> [--qualitaet 92]

Nur Bildströme werden neu als JPEG gespeichert – Text, Tags, Schriften,
Lesereihenfolge bleiben unangetastet (PDF/UA bleibt erhalten; danach trotzdem
verapdf --flavour ua1 laufen lassen). Übersprungen: Masken (SMask/ImageMask),
andere Farbräume als RGB/Graustufen und Flate-Bilder unter 150 KB (Logos,
Icons – dort wäre JPEG schlechter). Ein Bild wird nur ersetzt, wenn es kleiner wird.

Braucht pikepdf und Pillow, einmalig:
    python3 -m venv ~/.newmonday/venv && ~/.newmonday/venv/bin/pip install pikepdf pillow
und dann mit ~/.newmonday/venv/bin/python aufrufen.
"""
from __future__ import annotations

import argparse
import io

import pikepdf
from pikepdf import Name, PdfImage

MIN_FLATE = 150_000


def farbraum_ok(cs) -> bool:
    if cs in (Name.DeviceRGB, Name.DeviceGray):
        return True
    return (isinstance(cs, pikepdf.Array) and len(cs) == 2 and cs[0] == Name.ICCBased
            and int(cs[1].get("/N", 0)) in (1, 3))


def verkleinern(ein: str, aus: str, qualitaet: int) -> tuple[int, int]:
    pdf = pikepdf.open(ein)
    masken = {o.get("/SMask").objgen for o in pdf.objects
              if isinstance(o, pikepdf.Stream) and o.get("/SMask") is not None}
    ersetzt = gespart = 0
    for o in pdf.objects:
        if not isinstance(o, pikepdf.Stream) or o.get("/Subtype") != Name.Image:
            continue
        if o.objgen in masken or o.get("/ImageMask", False) or not farbraum_ok(o.get("/ColorSpace")):
            continue
        alt = len(o.read_raw_bytes())
        if o.get("/Filter") == Name.FlateDecode and alt < MIN_FLATE:
            continue
        try:
            bild = PdfImage(o).as_pil_image()
        except Exception:                      # exotische Kodierung: lieber unverändert lassen
            continue
        if bild.mode not in ("RGB", "L"):
            continue
        puffer = io.BytesIO()
        bild.save(puffer, "JPEG", quality=qualitaet, optimize=True)
        neu = puffer.getvalue()
        if len(neu) >= alt:
            continue
        o.write(neu, filter=Name.DCTDecode)
        o.BitsPerComponent = 8
        if "/DecodeParms" in o:
            del o["/DecodeParms"]
        ersetzt += 1
        gespart += alt - len(neu)
    pdf.save(aus, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    return ersetzt, gespart


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ein")
    ap.add_argument("aus")
    ap.add_argument("--qualitaet", type=int, default=92)
    a = ap.parse_args()
    n, kb = verkleinern(a.ein, a.aus, a.qualitaet)
    print(f"{n} Bilder neu gespeichert, {kb // 1024} KB gespart")
