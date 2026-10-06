#!/usr/bin/env python3
"""Schlaegt die Flaechenfarbe eines Projekts aus seinen Screens vor - nie aus dem Logo.

    python3 scripts/markenfarbe.py portfolio.json
    python3 scripts/markenfarbe.py screen-1.png screen-2.png

Loesungs- und Abschlussseite liegen seit Oktober 2026 auf der neutralen
Flaeche (neutral/15). Eine Farbe gibt es nur noch, wenn das Produkt sie
mitbringt: die Flaeche der Produktoberflaeche (DATEV-Petrol #247488 aus Kopf-
und Seitenleiste der Anwendung) oder der Grund, auf dem das Material selbst
steht. Dann steht sie in der portfolio.json als `markenfarbe`, mit Quelle in
`markenfarbe_quelle` - ohne Quelle setzt das Renderskript sie nicht.

Bis September 2026 las dieses Skript die Farbe aus dem Kundenlogo und trug sie
mit --setzen ein. Der Logo-Weg ist entfernt, nicht nur abgeschaltet: Eine
Logofarbe ist keine Produktfarbe, und ein Werkzeug, das sie auf Knopfdruck
liefert, bringt sie ueber kurz oder lang wieder auf die Folie. Umgestellt ist
es auf die Screens, weil die Produktfarbe genau dort steht - und der Hex-Wert
aus der Datei genauer ist als ein Blick.

Das Skript setzt nichts. Ob ein Ton die Flaeche der Oberflaeche ist oder nur
ein Foto, ein Button, eine Grafik im Screen, entscheidet der Mensch; er traegt
Farbe und Quelle von Hand ein. Gezaehlt wird nach Flaeche, nicht nach Zahl der
Farben, und nur satte Toene - Weiss, Grau und Schwarz sind Grund, keine Farbe.
Ein dunkler Grund (#111111) fuer farbige Motive wie Kampagnen ist deshalb nie
ein Vorschlag dieses Skripts, sondern eine Entscheidung, die in der Quelle
begruendet wird.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# Ein Ton muss satt und weder fast weiss noch fast schwarz sein, sonst ist er
# Grund oder Schrift der Oberflaeche, keine Flaechenfarbe.
MIN_SAETTIGUNG = 0.25
HELLIGKEIT = (0.10, 1.0)
# Ab diesem mittleren Flaechenanteil, und wenn der Ton in mindestens der
# Haelfte der Screens vorkommt (je mindestens STREU), gilt er als flaechig -
# darunter ist er ein Akzent (Button, Icon, Foto).
FLAECHIG, STREU = 0.08, 0.02


def rgb_hsv(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    hi, lo = max(r, g, b), min(r, g, b)
    s = 0 if hi == 0 else (hi - lo) / hi
    return s, hi


def taugt(rgb) -> bool:
    s, v = rgb_hsv(*rgb)
    return s >= MIN_SAETTIGUNG and HELLIGKEIT[0] <= v <= HELLIGKEIT[1]


def anteile(pfad: Path) -> tuple[Counter, dict]:
    """Flaechenanteil je Farbfach (24er-Stufen, damit Kantenglaettung und
    Kompression nicht als eigene Farben zaehlen) und je Fach der genaue
    haeufigste Ton - am Ende soll die echte Hex herauskommen, nicht die Mitte
    eines Fachs."""
    from PIL import Image
    with Image.open(pfad) as im:
        im = im.convert("RGB")
        if im.width > 240:
            im = im.resize((240, max(1, int(240 * im.height / im.width))))
        pixel = list(im.getdata())
    zaehler, genau = Counter(), {}
    for rgb in pixel:
        if not taugt(rgb):
            continue
        fach = tuple(v // 24 * 24 + 12 for v in rgb)
        zaehler[fach] += 1
        genau.setdefault(fach, Counter())[rgb] += 1
    gesamt = max(1, len(pixel))
    return Counter({f: n / gesamt for f, n in zaehler.items()}), genau


def vorschlaege(dateien: list[Path], anzahl: int = 3) -> list[dict]:
    """Die flaechigsten satten Toene ueber alle Screens eines Projekts."""
    summe, vorkommen, genau = Counter(), Counter(), {}
    n = 0
    for pfad in dateien:
        try:
            teil, g = anteile(pfad)
        except Exception:
            continue
        n += 1
        for fach, a in teil.items():
            summe[fach] += a
            if a >= STREU:
                vorkommen[fach] += 1
            genau.setdefault(fach, Counter()).update(g.get(fach, {}))
    if not n:
        return []
    raus = []
    for fach, a in summe.most_common(anzahl):
        ton = genau[fach].most_common(1)[0][0] if genau.get(fach) else fach
        mittel = a / n
        raus.append({"farbe": "#%02x%02x%02x" % ton, "anteil": mittel,
                     "screens": vorkommen[fach], "von": n,
                     "flaechig": mittel >= FLAECHIG and vorkommen[fach] * 2 >= n})
    return raus


def zeile(v: dict) -> str:
    art = "flächig – Kandidat, prüfen" if v["flaechig"] else "Akzent – keine Fläche"
    return (f"{v['farbe']}  {v['anteil']:5.1%} der Screenfläche, in {v['screens']} von "
            f"{v['von']} Screens  ({art})")


def main() -> None:
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--setzen" in sys.argv:
        print("--setzen gibt es nicht mehr: Eine Flächenfarbe trägst du von Hand ein, "
              "mit Quelle in „markenfarbe_quelle“ (SKILL.md, Schritt 6).\n")
    if not argumente:
        raise SystemExit(__doc__)
    quelle = Path(argumente[0])
    if quelle.suffix.lower() != ".json":
        for v in vorschlaege([Path(a) for a in argumente]) or []:
            print(zeile(v))
        return

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from render_portfolio import datei_suchen  # noqa: E402
    daten = json.loads(quelle.read_text(encoding="utf-8"))
    basis = quelle.resolve().parent
    for pr in daten.get("projekte", []):
        namen = list(pr.get("screens") or [])
        for lo in pr.get("loesungen") or []:
            namen += [s for s in lo.get("screens") or [] if s not in namen]
        dateien = [p for p in (datei_suchen(s, basis) for s in namen) if p]
        stand = pr.get("markenfarbe")
        kopf = f"{pr.get('kunde', '?')}"
        if stand:
            kopf += (f"   (gesetzt: {stand} – Quelle: "
                     f"{pr.get('markenfarbe_quelle') or 'FEHLT, wird nicht gesetzt'})")
        print(kopf)
        liste = vorschlaege(dateien)
        if not liste:
            print("  keine satten Töne in den Screens – Fläche bleibt neutral")
        for v in liste:
            print("  " + zeile(v))
    print("\nNichts eingetragen. Eine Farbe nur, wenn sie die Fläche der Oberfläche "
          "ist – dann „markenfarbe“ und „markenfarbe_quelle“ von Hand setzen.")


if __name__ == "__main__":
    main()
