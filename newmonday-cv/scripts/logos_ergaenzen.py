#!/usr/bin/env python3
"""Ergaenzt alle fehlenden Logos einer cv.json in einem Durchgang.

    python3 scripts/logos_ergaenzen.py cv.json
    python3 scripts/logos_ergaenzen.py cv.json --domains domains.json

Geht jede Station und jedes Projekt durch, das noch kein `logo` hat, sucht das
Logo und traegt den Dateinamen direkt in die cv.json ein. Reihenfolge je Firma:

  1. Bibliothek in assets/logos/ (kostet nichts und ist schon geprueft)
  2. Quellenkette aus fetch_logo.py (Wikimedia, Brandfetch, logo.dev, Favicon)

domains.json ist optional und ordnet Firmennamen Domains zu — Brandfetch,
logo.dev und der Favicon-Dienst brauchen eine Domain, Wikimedia nicht:

    { "Hays": "hays.de", "TEAM GmbH, Paderborn": "team-pb.de" }

Am Ende steht ein Bericht: was aus der Bibliothek kam, was neu gefunden wurde
und welche Firmen offen sind. Offene Logos sind kein Fehler — die Station
rendert ohne, das Raster bleibt stehen.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_logo import ZIEL, als_bild, als_svg, bibliothek_bereit, slugify  # noqa: E402
import fetch_logo  # noqa: E402

RECHTSFORMEN = (
    "gmbh & co. kg", "gmbh", "ag", "eg", "se", "kg", "ohg", "plc", "inc",
    "ltd", "mbh", "e.v.", "ug",
)


def slugs(firma):
    """Kandidaten fuer den Dateinamen, vom Genauen zum Groben."""
    name = firma.split(",")[0].strip()          # Ortsangabe hinter dem Komma weg
    grund = re.sub(r"[^\w\s&-]", "", name.lower())
    ohne_form = grund
    for form in RECHTSFORMEN:
        ohne_form = re.sub(rf"\b{re.escape(form)}\b", "", ohne_form)
    kandidaten = [grund, ohne_form.strip(), ohne_form.split("&")[0].strip()]
    ergebnis = []
    for k in kandidaten:
        s = slugify(k)
        if s and s not in ergebnis:
            ergebnis.append(s)
    return ergebnis


def aus_bibliothek(firma):
    aliase = ZIEL / "aliase.json"
    if aliase.exists():
        karte = json.loads(aliase.read_text(encoding="utf-8"))
        for schluessel, datei in karte.items():
            if schluessel.lower() in firma.lower() and (ZIEL / datei).exists():
                return datei
    vorhanden = {p.stem: p.name for p in ZIEL.iterdir() if p.suffix in (".svg", ".png")}
    for s in slugs(firma):
        if s in vorhanden:
            return vorhanden[s]
        for stem, datei in vorhanden.items():        # "team" trifft "team-gmbh"
            if stem.startswith(s + "-") or s.startswith(stem + "-"):
                return datei
    return None


def suchen(firma, domain):
    name = slugs(firma)[-1] or slugs(firma)[0]
    tmp = ZIEL / f".suche-{name}"
    for quelle in fetch_logo.QUELLEN:
        try:
            ergebnis = quelle(firma, domain)
        except Exception:
            continue
        if not ergebnis:
            continue
        daten, endung, woher = ergebnis
        tmp.write_bytes(daten)
        try:
            ziel = als_svg(tmp, name) if endung == "svg" else als_bild(tmp, name)
            return ziel.name, woher
        except Exception:
            continue
        finally:
            tmp.unlink(missing_ok=True)
    tmp.unlink(missing_ok=True)
    return None, None


def eintraege(daten):
    """Alle Stellen, die ein Logo tragen koennen."""
    for s in daten.get("stationen", []):
        if s.get("firma"):
            yield s, "firma"
        for p in s.get("projekte", []):
            if p.get("kunde"):
                yield p, "kunde"


def mehrere_marken(firma):
    """Stehen im Feld mehrere Firmen statt Firma plus Ort?

    "TEAM GmbH, Paderborn" ist Firma plus Ort — ein Komma, kein Und.
    "Deutsche Bank, Postbank, FYRST & Norisbank" sind vier Marken.
    """
    return firma.count(",") >= 2 or " & " in firma


def alle_marken(firma):
    """Feld mit mehreren Marken in die einzelnen Namen zerlegen."""
    teile = [t.strip() for t in re.split(r",|\s&\s|\sund\s", firma)]
    return [t for t in teile if t]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pfad = Path(sys.argv[1])
    domains = {}
    if "--domains" in sys.argv:
        domains = json.loads(
            Path(sys.argv[sys.argv.index("--domains") + 1]).read_text(encoding="utf-8")
        )
    bibliothek_bereit()
    daten = json.loads(pfad.read_text(encoding="utf-8"))

    aus_lib, neu, offen, teilweise = [], [], [], []
    for knoten, feld in eintraege(daten):
        firma = knoten[feld]
        if knoten.get("logo"):
            continue

        marken = alle_marken(firma) if mehrere_marken(firma) else [firma]
        gefunden, fehlend = [], []
        for marke in marken:
            treffer = aus_bibliothek(marke)
            if treffer:
                gefunden.append(treffer)
                aus_lib.append(f"{marke} -> {treffer}")
                continue
            datei, woher = suchen(marke, domains.get(marke) or domains.get(firma))
            if datei:
                gefunden.append(datei)
                neu.append(f"{marke} -> {datei} ({woher})")
            else:
                fehlend.append(marke)

        if gefunden:
            knoten["logo"] = gefunden[0] if len(gefunden) == 1 else gefunden
        if fehlend and gefunden:
            teilweise.append(f"{firma} — es fehlen: {', '.join(fehlend)}")
        elif fehlend:
            offen.append(firma)

    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    if aus_lib:
        print("Aus der Bibliothek:")
        for z in aus_lib:
            print("  " + z)
    if neu:
        print("Neu gefunden (bitte ansehen — Suche trifft manchmal daneben):")
        for z in neu:
            print("  " + z)
    if offen:
        print("Offen — Datei hochladen und add_logo.py aufrufen, oder Domain in")
        print("domains.json nachtragen:")
        for z in offen:
            print("  " + z)
    if teilweise:
        print("Nur teilweise gefunden — die uebrigen Logos fehlen in der Reihe:")
        for z in dict.fromkeys(teilweise):
            print("  " + z)


if __name__ == "__main__":
    main()
