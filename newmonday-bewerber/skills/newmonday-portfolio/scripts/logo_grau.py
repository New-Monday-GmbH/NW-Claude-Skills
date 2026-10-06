#!/usr/bin/env python3
"""Kundenlogos in Graustufen - wie in Florians ueberarbeitetem Deck (Oktober 2026,
Figma-Datei KoR4rzVSoMrvQot8z33gkv, Seite »Portfolio«, Folie 3).

    python3 scripts/logo_grau.py datev.svg [union-investment.svg …]   # Werte zeigen
    python3 scripts/logo_grau.py datev.svg --aus ordner/               # umgerechnet ablegen

Seit Oktober 2026 stehen die Kundenlogos schwarz-weiss: auf der Kundenwand
(Folie 3) und auf allen Projektseiten. Das ersetzt die Entscheidung
„Originalfarben" vom September 2026. Die Werkzeuglogos der KI-Folie bleiben
farbig - sie laufen nicht hier durch.

Die Regel ist an Folie 3 abgelesen, nicht erfunden:

- **Grau nach Luminanz.** Jede Farbe wird das Grau mit derselben relativen
  Helligkeit (Rec. 709, linear gerechnet) - genau das, was Figma mit
  „Saettigung -1" aus einem Bild macht (Tollwerk #00285b -> #2a2a2a).
- **Der Hauptton wird base/black.** Je Logo wird gespreizt: die dunkelste
  Farbe, die nennenswert Flaeche hat (3 % der Tinte), wird #111111, Weiss
  bleibt Weiss, dazwischen laeuft eine Kurve (Exponent 0,78). So stehen
  Union Investment, Green Planet Energy und die DATEV-Schrift fast schwarz,
  und das DATEV-Gruen wird ein mittleres Grau: #90d033 -> #8b8b8b, in Figma
  #8c8c8c. Nur nach Luminanz waere Union ein mattes #3c3c3c und das Gruen
  ein blasses #bebebe; alles auf Schwarz waere die DATEV-Flaeche ein Klotz.
- **Nie verzerrt.** Vektorlogos bleiben Vektor: nur die Farbwerte im SVG
  werden ersetzt, viewBox und Pfade bleiben unberuehrt. Rasterlogos behalten
  Pixelmass und Alphakanal.

Das PDF bekommt die umgerechneten Dateien (WeasyPrint kennt kein CSS-filter),
und figma_plan.py liest das Layout - also dieselben Dateien: Vektorlogos
tragen die Grauwerte als Fuellung, Rasterlogos gehen als Graustufen-PNG hoch.
PDF und Figma sehen damit gleich aus. Die gemeinsame Logobibliothek bleibt in
Originalfarben - entfaerbt wird nur beim Rendern, im Zwischenspeicher.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import design_tokens as _ds                     # noqa: E402
    SCHWARZ = _ds.laden()["farben"]["base/black"]
except Exception:                                   # pragma: no cover
    SCHWARZ = "#111111"

# Stand der Umrechnung. Gehoert in den Dateinamen im Zwischenspeicher: eine
# geaenderte Regel darf keine alten Grauwerte weiterliefern.
STAND = 1

TIEF = int(SCHWARZ.lstrip("#")[:2], 16)   # 17 - der Hauptton, base/black
WEISS_AB = 250        # heller ist Grund, keine Tinte
TINTE_ANTEIL = 0.03   # so viel Tintenflaeche muss der dunkelste Ton haben
TOLERANZ = 3          # Glaettung und Raster verschieben den Hauptton um 1-2 Stufen
KURVE = 0.78          # an Folie 3 abgelesen: DATEV-Gruen -> #8c8c8c
BLASS = 150           # Hauptton heller als das: das Logo verschwindet fast
RASTER_BREITE = 1400  # SVG mit eingebettetem Bild: so breit wird gerastert

_LIN = [((i / 255) / 12.92 if i / 255 <= 0.04045 else ((i / 255 + 0.055) / 1.055) ** 2.4)
        for i in range(256)]

hinweise: list[str] = []
_tinte_cache: dict[str, float | None] = {}


def hole_hinweise() -> list[str]:
    global hinweise
    raus, hinweise = hinweise, []
    return raus


def luminanzgrau(r: int, g: int, b: int) -> float:
    """Das Grau mit derselben relativen Helligkeit, 0 bis 255."""
    y = 0.2126 * _LIN[r] + 0.7152 * _LIN[g] + 0.0722 * _LIN[b]
    s = 12.92 * y if y <= 0.0031308 else 1.055 * y ** (1 / 2.4) - 0.055
    return max(0.0, min(255.0, s * 255))


def abbildung(dunkel: float):
    """Grauwert (Luminanz) -> Grauwert im Deck. `dunkel` ist der Hauptton des
    Logos; er und alles Dunklere wird base/black, Weiss bleibt Weiss."""
    spanne = max(1.0, 255.0 - dunkel)

    def grau(g0: float) -> int:
        t = max(0.0, min(1.0, (g0 - dunkel) / spanne))
        return round(TIEF + (255 - TIEF) * t ** KURVE)
    return grau


def _tinte(werte, anteile=None) -> float | None:
    """Der Hauptton: der Grauwert, unter dem TINTE_ANTEIL der Tintenflaeche
    liegt. Ein kleines (R) oder eine Haarlinie entscheidet so nicht ueber
    das ganze Logo."""
    tinte = sorted(w for w in werte if w < WEISS_AB)
    if not tinte:
        return None
    return tinte[min(len(tinte) - 1, int(len(tinte) * TINTE_ANTEIL))]


def _pixelgrau(bild):
    """Luminanzgrau und Alpha je Pixel - mit numpy, sonst ueber eine Tabelle."""
    rgba = bild.convert("RGBA")
    try:
        import numpy as np
        arr = np.asarray(rgba, dtype=np.uint8)
        lin = np.asarray(_LIN)
        y = (0.2126 * lin[arr[..., 0]] + 0.7152 * lin[arr[..., 1]]
             + 0.0722 * lin[arr[..., 2]])
        s = np.where(y <= 0.0031308, 12.92 * y, 1.055 * np.power(y, 1 / 2.4) - 0.055)
        return np.clip(s * 255, 0, 255), arr[..., 3]
    except ImportError:                             # pragma: no cover
        grau = [luminanzgrau(*px[:3]) for px in rgba.getdata()]
        alpha = list(rgba.getchannel("A").getdata())
        return grau, alpha


def _raster_tinte(bild) -> float | None:
    grau, alpha = _pixelgrau(bild)
    try:
        import numpy as np
        werte = grau[(alpha >= 128)]
        werte = werte[werte < WEISS_AB]
        if not werte.size:
            return None
        return float(np.quantile(werte, TINTE_ANTEIL))
    except ImportError:                             # pragma: no cover
        return _tinte([g for g, a in zip(grau, alpha) if a >= 128])


def _svg_rastern(pfad: Path, b: int = 400, h: int = 400, passung: str = "contain"):
    """SVG mit WeasyPrint rastern - derselbe Renderer wie im PDF -, mit
    Alphakanal, damit der Grund nicht als Tinte zaehlt. b x h in Pixeln."""
    import io

    import fitz
    from PIL import Image
    from weasyprint import HTML
    html = (f'<style>@page{{size:{b}px {h}px;margin:0}}body{{margin:0}}'
            f'img{{width:{b}px;height:{h}px;object-fit:{passung};display:block}}</style>'
            f'<img src="{pfad.resolve().as_uri()}">')
    pdf = HTML(string=html).write_pdf()
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        # WeasyPrint rechnet in CSS-px (0,75 pt), fitz in pt: 4/3 ergibt b x h Pixel.
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(4 / 3, 4 / 3), alpha=True)
        return Image.open(io.BytesIO(pix.tobytes("png"))).copy()


def _svg_rastern_genau(pfad: Path, verhaeltnis: float):
    """Ganzes SVG als Rasterbild im Seitenverhaeltnis der viewBox."""
    return _svg_rastern(pfad, RASTER_BREITE, max(1, round(RASTER_BREITE / verhaeltnis)), "fill")


def hauptton(pfad: Path) -> float | None:
    """Grauwert des Haupttons eines Logos (SVG gerastert), gecacht je Datei."""
    schluessel = f"{pfad}:{pfad.stat().st_mtime_ns}"
    if schluessel not in _tinte_cache:
        from PIL import Image
        if pfad.suffix.lower() == ".svg":
            bild = _svg_rastern(pfad)
        else:
            with Image.open(pfad) as im:
                im.load()
                bild = im.copy()
        ton = _raster_tinte(bild)
        # Der Hauptton selbst soll genau base/black werden, nicht #161616:
        # gerastert liegt er durch Kantenglaettung ein, zwei Stufen dunkler
        # als seine Farbangabe.
        _tinte_cache[schluessel] = None if ton is None else min(254.0, ton + TOLERANZ)
    return _tinte_cache[schluessel]


# Farbangaben im SVG: als Attribut (fill="#90d033") und als CSS-Deklaration
# (style="fill:#90d033", <style>.cls-1{fill:#90d033}). fill-opacity und
# stroke-width beginnen mit demselben Wort, gehen aber mit "-" weiter und
# fallen deshalb heraus.
_EIG = r"(?P<eig>(?<![\w-])(?:fill|stroke|stop-color|flood-color|lighting-color|color))"
_ATTR = re.compile(_EIG + r"(?P<zw>\s*=\s*)(?P<q>[\"'])(?P<wert>[^\"']*)(?P=q)")
_CSS = re.compile(_EIG + r"(?P<zw>\s*:\s*)(?P<wert>[^;\"'}<>]+)")
_KEINE_FARBE = ("none", "transparent", "currentcolor", "inherit", "initial", "unset", "")


def _grau_wert(wert: str, grau, unbekannt: set) -> str:
    roh = wert.strip()
    wichtig = ""
    if "!important" in roh:
        roh, wichtig = roh.replace("!important", "").strip(), " !important"
    if roh.lower() in _KEINE_FARBE or roh.lower().startswith(("url(", "var(")):
        return wert
    try:
        from PIL import ImageColor
        farbe = ImageColor.getrgb(roh)
    except (ValueError, AttributeError):
        unbekannt.add(roh)
        return wert
    g = grau(luminanzgrau(*farbe[:3]))
    if len(farbe) == 4 and farbe[3] < 255:
        return f"rgba({g},{g},{g},{farbe[3] / 255:.3f}){wichtig}"
    return f"#{g:02x}{g:02x}{g:02x}{wichtig}"


def svg_grau(text: str, grau) -> tuple[str, set]:
    """Jede Farbangabe im SVG durch ihr Grau ersetzen. Elemente ohne Fuellung
    sind schwarz - sie erben ein fill am Wurzelelement, das deshalb gesetzt
    wird, wenn es fehlt. Zurueck kommen der Text und unlesbare Angaben."""
    unbekannt: set = set()
    text = _ATTR.sub(lambda m: f'{m["eig"]}{m["zw"]}{m["q"]}'
                               f'{_grau_wert(m["wert"], grau, unbekannt)}{m["q"]}', text)
    text = _CSS.sub(lambda m: f'{m["eig"]}{m["zw"]}{_grau_wert(m["wert"], grau, unbekannt)}',
                    text)
    m = re.search(r"<svg\b[^>]*>", text)
    if m and not re.search(r"(?<![\w-])fill\s*=", m.group(0)):
        g = grau(0)
        kopf = re.sub(r"(/?>)$", f' fill="#{g:02x}{g:02x}{g:02x}"\\1', m.group(0))
        text = text[:m.start()] + kopf + text[m.end():]
    return text, unbekannt


def raster_grau(bild, grau):
    """Ein Rasterlogo Pixel fuer Pixel ins Grau - Groesse und Alpha bleiben."""
    from PIL import Image
    werte, alpha = _pixelgrau(bild)
    tabelle = [grau(float(i)) for i in range(256)]
    try:
        import numpy as np
        g = np.asarray(tabelle, dtype=np.uint8)[np.clip(np.rint(werte), 0, 255).astype(np.uint8)]
        l_kanal = Image.fromarray(g)
        a_kanal = Image.fromarray(np.asarray(alpha, dtype=np.uint8))
    except ImportError:                             # pragma: no cover
        l_kanal = Image.new("L", bild.size)
        l_kanal.putdata([tabelle[int(round(v))] for v in werte])
        a_kanal = Image.new("L", bild.size)
        a_kanal.putdata(list(alpha))
    return Image.merge("LA", (l_kanal, a_kanal))


def umrechnen(pfad: Path, ordner: Path) -> Path:
    """Liefert die Graustufen-Fassung eines Logos im Zwischenspeicher. Der
    Dateiname traegt Quelle, Aenderungszeit und STAND - ein zweiter Lauf
    greift die fertige Datei ab. Geht etwas schief, kommt das Original
    zurueck und eine Meldung."""
    pfad = Path(pfad).resolve()
    marke = hashlib.sha1(f"{STAND}:{pfad}:{pfad.stat().st_mtime_ns}"
                         .encode()).hexdigest()[:12]
    svg = pfad.suffix.lower() == ".svg"
    ziel = ordner / f"logo-grau-{pfad.stem}-{marke}{'.svg' if svg else '.png'}"
    ersatz = ziel.with_suffix(".png")
    for fertig in (ziel, ersatz):
        if fertig.exists():
            return fertig
    try:
        dunkel = hauptton(pfad)
        if dunkel is None:
            hinweise.append(f"Logo {pfad.name}: keine Tinte gefunden (weiß oder leer) – "
                            "steht wie geliefert. Auf weißer Folie unsichtbar: dunkle "
                            "Fassung der Marke nachlegen.")
            return pfad
        grau = abbildung(dunkel)
        if dunkel > BLASS:
            hinweise.append(f"Logo {pfad.name}: der Hauptton ist sehr hell – als "
                            "Graustufe trotzdem base/black gesetzt. Ansehen, ob die "
                            "Marke so lesbar bleibt.")
        ordner.mkdir(parents=True, exist_ok=True)
        if svg:
            text = pfad.read_text(encoding="utf-8", errors="replace")
            if re.search(r"<image\b", text, re.I):
                # Ein eingebettetes Bild traegt seine Farben im Pixel, nicht im
                # Quelltext - dann geht das ganze Logo als Raster, im
                # Seitenverhaeltnis der viewBox.
                import render_portfolio as _rp   # noqa: E402 - erst hier, kein Kreis beim Import
                v = _rp.seitenverhaeltnis(pfad.as_uri())
                raster_grau(_svg_rastern_genau(pfad, v), grau).save(ersatz)
                hinweise.append(f"Logo {pfad.name}: SVG mit eingebettetem Bild – als "
                                "Graustufen-PNG gesetzt.")
                return ersatz
            neu, unbekannt = svg_grau(text, grau)
            if unbekannt:
                hinweise.append(f"Logo {pfad.name}: Farbangaben nicht gelesen "
                                f"({', '.join(sorted(unbekannt))[:80]}) – stehen farbig. "
                                "Logo ansehen.")
            ziel.write_text(neu, encoding="utf-8")
            return ziel
        from PIL import Image
        with Image.open(pfad) as im:
            im.load()
            raster_grau(im, grau).save(ziel)
        return ziel
    except Exception as fehler:
        hinweise.append(f"Logo {pfad.name} nicht entfärbt ({fehler}) – steht farbig im "
                        "Dokument.")
        return pfad


def main() -> None:
    argumente = sys.argv[1:]
    if not argumente:
        raise SystemExit(__doc__)
    aus = None
    if "--aus" in argumente:
        i = argumente.index("--aus")
        aus = Path(argumente[i + 1])
        argumente = argumente[:i] + argumente[i + 2:]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from logo_lib import suche
    for name in argumente:
        pfad = Path(name)
        if not pfad.exists():
            pfad = suche(name) or pfad
        if not pfad.exists():
            print(f"{name}: nicht gefunden")
            continue
        dunkel = hauptton(pfad)
        if dunkel is None:
            print(f"{pfad.name}: keine Tinte")
            continue
        grau = abbildung(dunkel)
        zeile = f"{pfad.name}: Hauptton {dunkel:.0f} -> #{grau(dunkel):02x}{grau(dunkel):02x}{grau(dunkel):02x}"
        if pfad.suffix.lower() == ".svg":
            farben = sorted({m["wert"].strip() for m in list(_ATTR.finditer(pfad.read_text(errors="ignore")))
                             + list(_CSS.finditer(pfad.read_text(errors="ignore")))
                             if m["wert"].strip().lower() not in _KEINE_FARBE})
            umgerechnet = [f"{f} -> {_grau_wert(f, grau, set()).strip()}" for f in farben[:8]]
            zeile += ("  ·  " + ", ".join(umgerechnet)) if umgerechnet else ""
        print(zeile)
        if aus:
            print(f"  -> {umrechnen(pfad, aus)}")
    for h in hole_hinweise():
        print(f"  - {h}")


if __name__ == "__main__":
    main()
