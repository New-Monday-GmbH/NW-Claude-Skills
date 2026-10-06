#!/usr/bin/env python3
"""Baut die Screenflaeche mit den praesentierten Screens: ein gekipptes Raster.

    python3 scripts/screens.py --farbe "#0018a8" --aus panel.jpg s1.png s2.png
    python3 scripts/screens.py --farbe "#0018a8" --voll --aus ende.jpg material/*.png

WeasyPrint kennt keine Transformationen und keine Verlaeufe, die hier taugen.
Der Look muss deshalb im Bild entstehen und nicht im Stylesheet - hier wird
die fertige Flaeche gerechnet, der Renderer platziert sie danach nur noch.

Stand 11: **das Raster aus den Figma-Referenzen** (September 2026, sieben
Folien aus den Portfolios Wissem Kordi S. 14/19, Carolin Reis S. 13/14/21,
Daniel Fallack S. 13/14 - vom Nutzer als "so sieht es gut aus" vorgegeben,
nachdem die Kaskade aus Stand 9/10 bei Paul und Enrico "schlecht aussah").
Vermessen in Figma:

- **Der Grund ist neutral, nichts darueber.** Seit Oktober 2026 liegt das
  Raster auf neutral/15 (#ebf2f5) - so stehen die Loesungsflaechen in
  Florians ueberarbeitetem Deck. Eine Farbe kommt nur, wenn sie aus Produkt
  oder Screens stammt (`markenfarbe` mit Quelle, z. B. DATEV-Petrol
  #247488); sie steht dann, wie sie ist. Nur praktisch Weiss wird zur
  neutralen Flaeche - darauf verschwaenden weisse Screens. Auf hellem Grund
  tragen die Karten eine Kontur in neutral/20 statt in Weiss. Kein
  Verlaufsschleier, kein Schatten: in keiner Referenz traegt ein Screen einen
  Effekt.
- **Ein Raster gleich breiter Screens in versetzten Spalten**, gemeinsam
  gekippt, das die ganze Flaeche fuellt und an allen Kanten angeschnitten
  wird. Desktop-Screens: 560 pt breit, 36 pt Abstand, 15 Grad (Wissem S. 19,
  Carolin S. 14). Phones: 276 pt breit, 30 pt Abstand, 10 Grad (Wissem
  S. 14). Die Spalten sind gegeneinander versetzt, so entsteht die Diagonale.
  Sind es weniger Screens als Plaetze, wiederholen sie sich - wie in der
  Referenz, in der ein Screen dreimal vorkommt.
- **Karten und Geraete.** Desktop-Screens sind Karten mit 2,8 % Eckradius und
  feiner weisser Kontur (1,45 pt). Phones stecken in einer schwarzen Fassung
  mit Dynamic Island (Rand 3,25 %, Radius 14,7 % der Breite, wie der
  Container in Wissem S. 14). Browserfenster, Ampelpunkte, Tablets: nein.
- **Die volle Abschlussseite** traegt Desktop-Screens gerade, in drei
  Spalten von 502 pt mit 40 pt Abstand ab x 67 (Carolin S. 21) - rechts
  bleibt ein Streifen Grund fuer Wortmarke und Seitenzahl. Phones
  liegen auch dort als gekipptes Raster.
- **Ein einzelner Screen** liegt gross und gekippt allein auf der Flaeche.
- **Szenen.** Ein Bild, das schon eine fertig gestaltete Showcase-Szene ist
  (mehrere Fenster ueberlappend auf eigenem Grund) und sich nicht in saubere
  Screens zerlegen laesst, fuellt die Flaeche als Ganzes, auf seinen Inhalt
  ausgerichtet - so wie das Laptop-Foto in Daniel S. 14.
- **Wortmarke und Seitenzahl** liegen wie in den Referenzen auf dem Grund:
  Kacheln, die in ihre Felder (und in das des NDA-Hinweises) ragen,
  entfallen - die Spalte beginnt dort spaeter, wie die rechte Spalte in
  Wissem S. 14. Unter 48 Verschiebungen des Rasters gewinnt die, bei der am
  wenigsten Screen entfaellt. Die Kontrastmessung des Renderers waehlt
  danach die Schriftfarbe.

Material wird vorher aufbereitet: Geraete-Mockups (helle Clay-Phones auf
hellem Grund) geben ihre Screens her, Komposite zerfallen in einzelne
Screens, Mockup-Raender werden abgeschnitten, Doubletten fliegen raus.

Verworfen sind die Vorgaenger: Zufallsstreuung mit Perspektive, das flache
Editorial-Raster, die Buehne mit Fassungen (Stand 7), die Kachelwand auf
hellem Grund (Stand 8) und die Kaskade weniger grosser Screens auf
abgedunkelter Markenfarbe mit Schatten und Eckschleier (Stand 9/10).

Geschrieben wird ein JPEG - auch dann, wenn der Zielpfad anders endet.
`baue_screens` gibt den geschriebenen Pfad zurueck, `hole_hinweise` die
Meldungen dazu."""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

try:
    import numpy as _np
except Exception:                                   # pragma: no cover
    _np = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import design_tokens as _ds                     # noqa: E402
except Exception:                                   # pragma: no cover
    _ds = None

# Stand des Anordnungs-Algorithmus. Gehoert in jeden Cache-Fingerabdruck, der
# fertige Flaechen wiederverwendet: ohne ihn liefert ein Zwischenspeicher von
# vor einer Layoutaenderung stumm die alte Anordnung weiter. Bei jeder
# Aenderung an Anordnung, Massen oder Meldungen hochzaehlen.
# Stand 11: Raster aus den Figma-Referenzen - Markenfarbe, Karten, Phones.
# Stand 12/13: Szene nur auf dunklem/farbigem Grund; Hochformate zwischen
# Desktop-Screens liegen als Karte. Stand 14: der Freisteller schneidet nur
# einfarbige Unterlage weg, nie eine Kopfleiste am Bildrand. Stand 15: Grund
# neutral/15 statt Petrol, Karten-Kontur auf hellem Grund in neutral/20.
LAYOUT_STAND = 15

# Zwei Pixel je Punkt: die Flaeche wird im PDF nur skaliert, nie vergroessert.
PX_JE_PUNKT = 2
GROESSEN = {"panel": (988, 1080), "voll": (1920, 1080)}  # panel = Bildflaeche ab x 932 (Figma)
PANEL_LINKS = 932            # wo die Panelflaeche auf der Folie beginnt

# Qualitaet: unter diesem Anteil der platzierten Breite gilt ein Screen als
# weich. Das Raster wird dann als Ganzes bis RASTER_MIN kleiner, bevor es
# hochrechnet; unter HOCH_MIN fliegt ein Screen raus.
WEICH_MIN = 0.75
RASTER_MIN = 0.80
HOCH_MIN = 0.40
# Szenen fuellen die Flaeche als Foto: dort genuegt ein Pixel je Punkt.
SZENE_MIN = 0.5

# Ohne Flaechenfarbe: die neutrale Flaeche neutral/15 aus den Tokens - so
# stehen die Loesungsseiten in Florians Deck (Oktober 2026); die Karten
# bekommen dort eine Kontur in neutral/20.
NEUTRAL, KONTUR_HELL = "#ebf2f5", "#c9cfd1"
if _ds is not None:
    try:
        NEUTRAL = _ds.laden()["farben"]["neutral/15"]
        KONTUR_HELL = _ds.laden()["farben"]["neutral/20"]
    except Exception:                               # pragma: no cover
        pass
# Praktisch Weiss traegt keine weissen Screens - dann steht die neutrale
# Flaeche. Alles andere steht, wie es ist: neutral/15 (0,94), eine helle
# Produktflaeche, Petrol, #111111.
GRUND_WEISS_AB = 0.97
# Ab dieser Helligkeit des Grundes ist die weisse Kontur der Karten unsichtbar
# - dann zieht neutral/20 die Kante.
KONTUR_WECHSEL = 0.80

# Die Raster je Screenart und Flaeche, in Punkt. `versatz` ist die
# Verschiebung jeder Spalte gegen die vorige, als Anteil des Spaltentakts.
RASTER = {
    ("desktop", "panel"): {"spalte": 560, "luecke": 36, "winkel": 15.0, "versatz": 0.70},
    ("phone", "panel"): {"spalte": 276, "luecke": 30, "winkel": 10.0, "versatz": 0.30},
    ("desktop", "voll"): {"spalte": 502, "luecke": 40, "winkel": 0.0, "x0": 67,
                          "spalten": 3, "start": (-0.15, -0.55, -0.35)},
    ("phone", "voll"): {"spalte": 300, "luecke": 32, "winkel": 10.0, "versatz": 0.30},
}
# Hoechstes Seitenverhaeltnis (Hoehe/Breite) einer Karte - lange Seiten
# werden von oben gezeigt. Phones: das Displayformat, auf das die Fassung
# den Screen einpasst.
KARTE_AR_MAX = 1.25
PHONE_AR = (1.75, 2.30)
# Ein Screen allein: Kartenbreite bzw. Phonehoehe als Anteil der Flaeche.
HERO = {("desktop", "panel"): 0.92, ("desktop", "voll"): 0.62,
        ("phone", "panel"): 0.86, ("phone", "voll"): 0.82}
# Hoechstzahl verschiedener Screens in einem Raster.
MAX_SCREENS = 12

# Karte: Eckradius und weisse Kontur (Carolin S. 14: 15,5 / 1,45 pt bei 560 pt).
KARTE_RADIUS = 0.028
KARTE_KONTUR = 1.45          # pt
# Phone-Fassung (Wissem S. 14: Container 276 x 598, Rand 9, Radius 40,6,
# Screen-Radius 32,5, Insel 97,5 x 24,4).
PHONE_RAND = 0.0325          # Anteil der Gehaeusebreite
PHONE_RADIUS = 0.147
PHONE_SCREEN_RADIUS = 0.126  # Anteil der Screenbreite
INSEL_BREITE, INSEL_HOEHE, INSEL_OBEN = 0.353, 0.088, 0.03
GEHAEUSE = (0, 0, 0)

# Die Felder von Wortmarke und Seitenzahl auf der Folie, in Punkt, mit Luft.
# Sie bleiben frei wie in den Referenzen: Kacheln, die hineinragen, entfallen
# - die Spalte beginnt dort spaeter, die Ecke zeigt den Grund. Unter den
# Verschiebungen des Rasters gewinnt die, bei der am wenigsten entfaellt.
# Steht ein NDA-Hinweis auf der Seite, kommt sein Feld dazu (NDA_FELD).
FELD_LOGO = (1690, 44, 1880, 92)
FELD_SEITE = (1822, 998, 1908, 1052)
NDA_FELD = (1392, 936, 1872, 996)

# Mockup-Beschnitt: nur wenn deutlich Rand faellt, der Fund glaubhaft ist und
# der wegfallende Rand einfarbig ist (FREISTELL_RUHE: groesste Abweichung
# vom Randmedian, Summe ueber drei Kanaele, die 95 % der Randpixel einhalten).
FREISTELL_OBEN = 0.86
FREISTELL_UNTEN = 0.25
FREISTELL_RUHE = 45

# Komposit-Zerleger: Mindestmasse eines herausgeloesten Screens im Original
# (kuerzere/laengere Kante) - kleinere Teile blieben im Raster unscharf,
# dann bleibt das Komposit lieber ganz.
TEIL_KURZ, TEIL_LANG = 500, 900
TEIL_FLAECHE = 0.025         # Mindestanteil eines Teils an der Bildflaeche
TEIL_RECHTECK = 0.85         # Fuellgrad der Box: darunter ist es kein Screen
ZERLEG_SCHWELLE = 60         # Farbabstand zum Grund (Summe ueber 3 Kanaele)

# Szene oder Screen: Liegt das Bild auf dunklem oder farbigem Grund und
# bleibt nach dem Freistellen mehr als dieser Anteil Grund im Bild, ist es
# eine gestaltete Szene mit Fenstern auf eigenem Grund. Heller, unbunter
# Grund ist die Unterlage eines Screen-Exports - dort ist es immer ein Screen.
SZENE_GRUND = 0.10

# Geraete-Mockups: helle Phone-Gehaeuse auf hellem, ruhigem Grund.
GERAET_HELLER = 8            # so viel heller als der Grund ist das Gehaeuse
GERAET_AR = (1.85, 2.35)
GERAET_MIN_BREITE = 150
GERAET_RAND = 0.034          # Gehaeuserand des Mockups, Anteil der Breite

# Doubletten: gleiche Masse (3 %) und gleiche 8x8-Mittelwerte.
MASS_TOLERANZ = 0.03
RASTER_TOLERANZ = 3.0

hinweise: list[str] = []


def hole_hinweise() -> list[str]:
    """Gibt die gesammelten Meldungen zurueck und leert die Liste."""
    global hinweise
    raus, hinweise = hinweise, []
    return raus


# --------------------------------------------------------------------------
# Farben und Grund

def _farbe(wert: str | None) -> tuple[int, int, int]:
    h = (wert or NEUTRAL).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(z * 2 for z in h)
    if len(h) != 6:
        h = NEUTRAL.lstrip("#")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return tuple(int(NEUTRAL.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


def _luminanz(farbe: tuple) -> float:
    r, g, b = farbe
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def _grundton(marke: tuple) -> tuple[int, int, int]:
    """Der Grund ist die Flaechenfarbe, wie sie ist. Nur praktisch Weiss wird
    zur neutralen Flaeche - auf ihm verschwaenden helle Screens."""
    if _luminanz(marke) <= GRUND_WEISS_AB:
        return marke
    return _farbe(NEUTRAL)


def _konturfarbe(grund: tuple) -> tuple[int, int, int]:
    """Weisse Kontur auf dunklem und farbigem Grund wie in den Referenzen, auf
    hellem Grund neutral/20 - sonst verschwimmt ein weisser Screen mit ihm."""
    return (255, 255, 255) if _luminanz(grund) <= KONTUR_WECHSEL else _farbe(KONTUR_HELL)


# --------------------------------------------------------------------------
# Material vorbereiten

class Stueck:
    """Ein aufbereiteter Screen: Name, Bild und Art (desktop, phone, szene)."""
    def __init__(self, name: str, bild: Image.Image, art: str):
        self.name, self.bild, self.art = name, bild, art


def _freistellen(bild: Image.Image) -> tuple[Image.Image, float]:
    """Mockup-Rand abschneiden, wenn deutlich einer da ist.

    Ein Kantendetektor findet den Inhalt: Verlaeufe und weiche Schatten
    erzeugen keine Kanten, die Screenkante selbst schon. Beschnitten wird
    nur, wenn dabei wirklich Rand faellt (< FREISTELL_OBEN) und der Fund
    glaubhaft ist (> FREISTELL_UNTEN). Zurueck kommt das Bild und der
    behaltene Anteil."""
    b, h = bild.size
    if min(b, h) < 500:
        return bild, 1.0
    f = min(1.0, 640 / max(b, h))
    probe = bild.convert("L")
    if f < 1.0:
        probe = probe.resize((max(8, round(b * f)), max(8, round(h * f))),
                             Image.BILINEAR)
    kanten = probe.filter(ImageFilter.FIND_EDGES).point(
        lambda w: 255 if w > 26 else 0)
    kanten = kanten.crop((2, 2, kanten.width - 2, kanten.height - 2))
    kasten = kanten.getbbox()
    if not kasten:
        return bild, 1.0
    x0 = (kasten[0] + 2) / f
    y0 = (kasten[1] + 2) / f
    x1 = (kasten[2] + 2) / f
    y1 = (kasten[3] + 2) / f
    anteil = ((x1 - x0) * (y1 - y0)) / (b * h)
    if anteil > FREISTELL_OBEN or anteil < FREISTELL_UNTEN:
        return bild, 1.0
    if not _rand_ruhig(bild, (x0, y0, x1, y1)):
        return bild, 1.0              # am Rand liegt Inhalt, keine Unterlage
    rand = 0.006 * min(b, h)
    x0 = max(0, int(x0 - rand))
    y0 = max(0, int(y0 - rand))
    x1 = min(b, int(x1 + rand))
    y1 = min(h, int(y1 + rand))
    return bild.crop((x0, y0, x1, y1)), ((x1 - x0) * (y1 - y0)) / (b * h)


def _rand_ruhig(bild: Image.Image, kasten: tuple) -> bool:
    """Ist alles ausserhalb des Kastens einfarbige Unterlage? Eine farbige
    Kopfleiste oder ein Menue am Bildrand ist Inhalt - dann wird nicht
    beschnitten, auch wenn der Kantendetektor dort keine Kante sieht."""
    if _np is None:
        return True
    f = min(1.0, 400 / max(bild.size))
    probe = bild.convert("RGB").resize((max(8, round(bild.width * f)),
                                        max(8, round(bild.height * f))), Image.BILINEAR)
    arr = _np.asarray(probe, dtype=_np.int16)
    x0, y0, x1, y1 = (int(v * f) for v in kasten)
    maske = _np.ones(arr.shape[:2], dtype=bool)
    maske[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = False
    aussen = arr[maske]
    if aussen.size == 0:
        return True
    median = _np.median(aussen, axis=0)
    abweichung = _np.abs(aussen - median).sum(axis=1)
    return float(_np.percentile(abweichung, 95)) <= FREISTELL_RUHE


def _komponenten(maske) -> list[tuple[int, int, int, int, int]]:
    """Zusammenhaengende Bereiche einer bool-Maske (numpy), als Liste von
    (x0, y0, x1, y1, flaeche). Zweipass mit Union-Find auf Zeilenlaeufen -
    schnell genug ohne scipy."""
    hoehe, breite = maske.shape
    eltern: list[int] = []

    def finde(i: int) -> int:
        while eltern[i] != i:
            eltern[i] = eltern[eltern[i]]
            i = eltern[i]
        return i

    def vereine(a: int, b: int) -> None:
        ra, rb = finde(a), finde(b)
        if ra != rb:
            eltern[max(ra, rb)] = min(ra, rb)

    laeufe: list[list[tuple[int, int, int]]] = []   # je Zeile (x0, x1, id)
    for y in range(hoehe):
        zeile = maske[y]
        laeufe.append([])
        if not zeile.any():
            continue
        idx = _np.flatnonzero(zeile)
        starts = [int(idx[0])]
        enden = []
        spruenge = _np.flatnonzero(_np.diff(idx) > 1)
        for s in spruenge:
            enden.append(int(idx[s]))
            starts.append(int(idx[s + 1]))
        enden.append(int(idx[-1]))
        for x0, x1 in zip(starts, enden):
            kennung = len(eltern)
            eltern.append(kennung)
            laeufe[y].append((x0, x1, kennung))
            if y:
                for vx0, vx1, vid in laeufe[y - 1]:
                    if vx0 <= x1 and vx1 >= x0:
                        vereine(vid, kennung)

    kaesten: dict[int, list[int]] = {}
    for y, zeile in enumerate(laeufe):
        for x0, x1, kennung in zeile:
            wurzel = finde(kennung)
            k = kaesten.get(wurzel)
            if k is None:
                kaesten[wurzel] = [x0, y, x1, y, x1 - x0 + 1]
            else:
                k[0] = min(k[0], x0)
                k[2] = max(k[2], x1)
                k[3] = y
                k[4] += x1 - x0 + 1
    return [tuple(k) for k in kaesten.values()]


def _saum(arr):
    rand = max(2, round(0.02 * min(arr.shape[:2])))
    return _np.concatenate([
        arr[:rand].reshape(-1, 3), arr[-rand:].reshape(-1, 3),
        arr[:, :rand].reshape(-1, 3), arr[:, -rand:].reshape(-1, 3)])


def _geraete_finden(bild: Image.Image, name: str) -> list[Stueck]:
    """Phone-Mockups (helle Clay-Gehaeuse auf hellem, ruhigem Grund) geben
    ihre Screens her: Das Gehaeuse ist heller als der Grund, sein Umriss ein
    Hochformat-Rechteck. Innen, um den Gehaeuserand eingerueckt, liegt der
    Screen - er kommt spaeter in die eigene Fassung. Nichts gefunden: leere
    Liste, das Bild geht den ueblichen Weg."""
    if _np is None:
        return []
    b, h = bild.size
    if min(b, h) < 400:
        return []
    rgb = bild.convert("RGB")
    arr = _np.asarray(rgb, dtype=_np.int16)
    saum = _saum(arr)
    grund = _np.median(saum, axis=0)
    # Nur auf hellem, ruhigem Grund: dort ist ein Clay-Gehaeuse eindeutig.
    if grund.min() < 190 or _np.abs(saum - grund).sum(axis=1).mean() > 30:
        return []
    schwelle = min(250, int(grund.min()) + GERAET_HELLER)
    hell = arr.min(axis=2) >= schwelle
    mbild = Image.fromarray((hell * 255).astype("uint8"))
    mbild = mbild.filter(ImageFilter.MinFilter(5)).filter(
        ImageFilter.MaxFilter(9)).filter(ImageFilter.MaxFilter(9))
    maske = _np.asarray(mbild) > 128
    funde = []
    for x0, y0, x1, y1, flaeche in _komponenten(maske):
        w, hh = x1 - x0 + 1, y1 - y0 + 1
        if w < GERAET_MIN_BREITE or flaeche < 0.01 * maske.size:
            continue
        if not (GERAET_AR[0] <= hh / w <= GERAET_AR[1]):
            continue
        if flaeche / (w * hh) < TEIL_RECHTECK:
            continue
        if x0 <= 2 or y0 <= 2 or x1 >= b - 3 or y1 >= h - 3:
            continue                                  # angeschnitten
        # Der genaue Umriss aus der unverbreiterten Maske.
        roh = hell[y0:y1 + 1, x0:x1 + 1]
        zeilen = _np.flatnonzero(roh.any(axis=1))
        spalten = _np.flatnonzero(roh.any(axis=0))
        if not len(zeilen) or not len(spalten):
            continue
        gx0, gx1 = x0 + int(spalten[0]), x0 + int(spalten[-1]) + 1
        gy0, gy1 = y0 + int(zeilen[0]), y0 + int(zeilen[-1]) + 1
        rand = round(GERAET_RAND * (gx1 - gx0))
        funde.append((gx0 + rand, gy0 + rand, gx1 - rand, gy1 - rand))
    if not funde:
        return []
    funde.sort(key=lambda k: (k[0], k[1]))
    hinweise.append(f"{name}: Geräte-Mockup – {len(funde)} Screen(s) aus den "
                    "Gehäusen gelöst und in die eigene Fassung gesetzt")
    return [Stueck(f"{name}·{i + 1}", rgb.crop(k), "phone") for i, k in enumerate(funde)]


def _zerlegen(bild: Image.Image, name: str) -> list[tuple[str, Image.Image, bool]]:
    """Ein Komposit in einzelne Screens zerlegen, wenn es eines ist.

    Ein Quellbild mit mehreren getrennten, rechteckigen Inhalten auf
    einheitlichem Grund zerfaellt in seine Teile. Zerlegt wird nur, wenn die
    Teile gross genug bleiben (TEIL_KURZ/TEIL_LANG) - kleine Schnipsel waeren
    im Raster unscharf. Echte Screenshots (Inhalt fuellt das Bild) passieren
    unveraendert. Zurueck kommen (name, bild, szene): `szene` heisst, das
    Bild hat rundum eigenen Grund, laesst sich aber nicht in saubere Screens
    zerlegen - eine fertig gestaltete Showcase-Szene mit ueberlappenden
    Fenstern. Sie wird spaeter als Ganzes gezeigt, nicht als Karte."""
    if _np is None:
        return [(name, bild, False)]
    b, h = bild.size
    if min(b, h) < 700:
        return [(name, bild, False)]
    f = min(1.0, 640 / max(b, h))
    probe = bild.convert("RGB")
    if f < 1.0:
        probe = probe.resize((round(b * f), round(h * f)), Image.BILINEAR)
    arr = _np.asarray(probe, dtype=_np.int16)
    grund = _np.median(_saum(arr), axis=0)
    abstand = _np.abs(arr - grund).sum(axis=2)
    maske = abstand > ZERLEG_SCHWELLE

    # Punktmuster und Rauschen wegschleifen, Luecken in Screens schliessen.
    mbild = Image.fromarray((maske * 255).astype("uint8"))
    mbild = mbild.filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.MaxFilter(7)).filter(ImageFilter.MaxFilter(7))
    maske = _np.asarray(mbild) > 128

    # Ein echter Screenshot traegt Inhalt bis an die Kanten (Header, Menü,
    # Footer) - ein Komposit hat rundum Grund. Ohne freien Saum auf allen
    # vier Seiten wird gar nicht erst zerlegt.
    zeilen = _np.flatnonzero(maske.any(axis=1))
    spalten_idx = _np.flatnonzero(maske.any(axis=0))
    if not len(zeilen) or not len(spalten_idx):
        return [(name, bild, False)]
    hoehe_m, breite_m = maske.shape
    saum_frei = min(zeilen[0] / hoehe_m, (hoehe_m - 1 - zeilen[-1]) / hoehe_m,
                    spalten_idx[0] / breite_m,
                    (breite_m - 1 - spalten_idx[-1]) / breite_m)
    if saum_frei < 0.025:
        return [(name, bild, False)]

    teile = [t for t in _komponenten(maske)
             if t[4] >= TEIL_FLAECHE * maske.size]
    if not teile:
        return [(name, bild, True)]

    def original_box(t, luft_anteil=0.006):
        x0, y0, x1, y1, _ = t
        luft = round(luft_anteil * min(b, h))
        return (max(0, int(x0 / f) - luft), max(0, int(y0 / f) - luft),
                min(b, int((x1 + 1) / f) + luft), min(h, int((y1 + 1) / f) + luft))

    if len(teile) == 1:
        # Ein einzelner Inhalt auf viel Grund: auf ihn beschneiden, wenn er
        # ein sauberes Rechteck ist. Sonst ist es eine Szene.
        t = teile[0]
        box_anteil = ((t[2] - t[0] + 1) * (t[3] - t[1] + 1)) / maske.size
        fuellung = t[4] / ((t[2] - t[0] + 1) * (t[3] - t[1] + 1))
        if 0.10 < box_anteil < FREISTELL_OBEN and fuellung >= TEIL_RECHTECK:
            ox0, oy0, ox1, oy1 = original_box(t)
            if min(ox1 - ox0, oy1 - oy0) >= TEIL_KURZ:
                hinweise.append(
                    f"{name}: Screen lag auf großem Grund – auf den Inhalt "
                    f"beschnitten ({box_anteil * 100:.0f} % der Fläche behalten)")
                return [(name, bild.crop((ox0, oy0, ox1, oy1)), False)]
        return [(name, bild, fuellung < TEIL_RECHTECK)]

    scheiben: list[tuple[str, Image.Image, bool]] = []
    verworfen = 0
    for t in sorted(teile, key=lambda t: (t[1], t[0])):
        x0, y0, x1, y1, flaeche = t
        box_flaeche = (x1 - x0 + 1) * (y1 - y0 + 1)
        ox0, oy0, ox1, oy1 = original_box(t, 0.004)
        kurz = min(ox1 - ox0, oy1 - oy0)
        lang = max(ox1 - ox0, oy1 - oy0)
        if flaeche / box_flaeche < TEIL_RECHTECK:
            verworfen += 1               # ueberlappt montiert oder kein Screen
            continue
        if kurz < TEIL_KURZ or lang < TEIL_LANG:
            verworfen += 1               # zu klein, wuerde im Raster weich
            continue
        scheiben.append((f"{name}·{len(scheiben) + 1}",
                         bild.crop((ox0, oy0, ox1, oy1)), False))

    if len(scheiben) < 2:
        # Kein sauberer Mehrfach-Schnitt. Ist wenigstens der groesste Teil
        # ein sauberer Screen, auf ihn beschneiden; sonst ist es eine Szene.
        gross = max(teile, key=lambda t: t[4])
        box_anteil = ((gross[2] - gross[0] + 1) * (gross[3] - gross[1] + 1)) \
            / maske.size
        fuellung = gross[4] / ((gross[2] - gross[0] + 1) * (gross[3] - gross[1] + 1))
        ox0, oy0, ox1, oy1 = original_box(gross)
        if (0.10 < box_anteil < FREISTELL_OBEN and fuellung >= TEIL_RECHTECK
                and min(ox1 - ox0, oy1 - oy0) >= TEIL_KURZ):
            hinweise.append(
                f"{name}: nur der größte Screen des Komposits ist brauchbar – "
                f"auf ihn beschnitten ({box_anteil * 100:.0f} % der Fläche)")
            return [(name, bild.crop((ox0, oy0, ox1, oy1)), False)]
        return [(name, bild, True)]
    hinweise.append(
        f"{name}: Komposit mit {len(scheiben)} einzelnen Screens – zerlegt"
        + (f", {verworfen} zu kleine oder überlappte Teile bleiben draußen"
           if verworfen else ""))
    return scheiben


def _randfarbe(bild: Image.Image) -> tuple:
    """Die Farbe des Bildrands (Median des Saums)."""
    if _np is None:
        return (255, 255, 255)
    f = min(1.0, 320 / max(bild.size))
    probe = bild.convert("RGB").resize((max(8, round(bild.width * f)),
                                        max(8, round(bild.height * f))), Image.BILINEAR)
    return tuple(int(v) for v in _np.median(_saum(_np.asarray(probe, dtype=_np.int16)), axis=0))


def _hell_neutral(farbe: tuple) -> bool:
    """Heller, unbunter Grund - die Unterlage eines Screen-Exports, keine
    gestaltete Szene. Szenen stehen in den Portfolios auf dunklem oder
    farbigem Grund (Navy, Schwarz, Markenfarbe)."""
    return _luminanz(farbe) > 0.70 and max(farbe) - min(farbe) < 40


def _grundanteil(bild: Image.Image, original: Image.Image) -> float:
    """Wie viel eines (freigestellten) Bildes die Farbe des Original-Bildrands
    traegt: bei einer Szene viel (Grund zwischen den Fenstern), bei einem
    freigestellten Screen wenig."""
    if _np is None:
        return 0.0
    f = min(1.0, 320 / max(bild.size))
    probe = bild.convert("RGB").resize((max(8, round(bild.width * f)),
                                        max(8, round(bild.height * f))), Image.BILINEAR)
    of = min(1.0, 320 / max(original.size))
    oprobe = original.convert("RGB").resize((max(8, round(original.width * of)),
                                             max(8, round(original.height * of))),
                                            Image.BILINEAR)
    grund = _np.median(_saum(_np.asarray(oprobe, dtype=_np.int16)), axis=0)
    arr = _np.asarray(probe, dtype=_np.int16)
    return float((_np.abs(arr - grund).sum(axis=2) <= ZERLEG_SCHWELLE).mean())


def _art(bild: Image.Image) -> str:
    """Phone oder Desktop: ein Hochformat im Displayformat eines Phones und in
    Phone-Breite. Eine lange Webseite im Hochformat bleibt eine Karte."""
    ar = bild.height / max(1, bild.width)
    if PHONE_AR[0] - 0.05 <= ar <= 2.45 and bild.width <= 1400:
        return "phone"
    return "desktop"


def _fingerabdruck(bild: Image.Image) -> tuple:
    grob = bild.convert("L").resize((8, 8), Image.BOX)
    return bild.size, tuple(grob.getdata())


def _doublette(a: tuple, b: tuple) -> bool:
    (ab, ah), araster = a
    (bb, bh), braster = b
    if max(abs(ab - bb) / max(ab, bb), abs(ah - bh) / max(ah, bh)) > MASS_TOLERANZ:
        return False
    abstand = sum(abs(x - y) for x, y in zip(araster, braster)) / len(araster)
    return abstand <= RASTER_TOLERANZ


def aufbereiten(geladen: list[tuple[str, Image.Image]], ziel_name: str) -> list[Stueck]:
    """Aus den Rohbildern die Stuecke fuer die Flaeche: Geraete-Mockups
    loesen, Komposite zerlegen, Mockup-Raender beschneiden, Doubletten weg."""
    stuecke: list[Stueck] = []
    for name, bild in geladen:
        geraete = _geraete_finden(bild, name)
        if geraete:
            stuecke.extend(geraete)
            continue
        for teil_name, teil, szene in _zerlegen(bild, name):
            frei, anteil = _freistellen(teil)
            if (szene and not _hell_neutral(_randfarbe(teil))
                    and _grundanteil(frei, teil) > SZENE_GRUND):
                stuecke.append(Stueck(teil_name, teil.convert("RGB"), "szene"))
                continue
            if anteil < 1.0:
                hinweise.append(
                    f"{ziel_name}: {teil_name} kam als Mockup mit Rand an – auf den "
                    f"Inhalt beschnitten ({anteil * 100:.0f} % der Fläche behalten). "
                    "Ein Originalexport ohne Rahmen wäre besser.")
            frei = frei.convert("RGB")
            stuecke.append(Stueck(teil_name, frei, _art(frei)))

    behalten: list[Stueck] = []
    abdruecke: list[tuple[str, tuple]] = []
    for s in stuecke:
        abdruck = _fingerabdruck(s.bild)
        gleich = next((n for n, a in abdruecke if _doublette(a, abdruck)), None)
        if gleich:
            hinweise.append(f"{ziel_name}: {s.name} zeigt dieselbe Ansicht wie "
                            f"{gleich} – nur einmal aufgenommen")
            continue
        abdruecke.append((s.name, abdruck))
        behalten.append(s)
    return behalten


# --------------------------------------------------------------------------
# Kacheln: Karte und Phone

def _karte(bild: Image.Image, b: int, h: int,
           kontur_farbe: tuple = (255, 255, 255)) -> Image.Image:
    """Ein Desktop-Screen als Karte: einmal LANCZOS auf die Spaltenbreite,
    zu lange Seiten von oben gezeigt, 2,8 % Eckradius, feine Kontur - weiss,
    auf hellem Grund neutral/20."""
    skala = b / bild.width
    voll_h = max(1, round(bild.height * skala))
    screen = bild.resize((b, voll_h), Image.LANCZOS)
    if voll_h > h:
        screen = screen.crop((0, 0, b, h))
    elif voll_h < h:
        unten = Image.new("RGB", (b, h), screen.getpixel((b // 2, voll_h - 1)))
        unten.paste(screen, (0, 0))
        screen = unten
    einheit = screen.convert("RGBA")
    radius = max(6, round(b * KARTE_RADIUS))
    maske = Image.new("L", (b, h), 0)
    ImageDraw.Draw(maske).rounded_rectangle((0, 0, b - 1, h - 1), radius, fill=255)
    kontur = max(1, round(KARTE_KONTUR * PX_JE_PUNKT))
    ImageDraw.Draw(einheit).rounded_rectangle(
        (0, 0, b - 1, h - 1), radius, outline=tuple(kontur_farbe) + (255,), width=kontur)
    einheit.putalpha(maske)
    return einheit


def _phone_masse(b: int, ar: float) -> tuple[int, int, int, int]:
    """Gehaeusebreite b und Screen-Seitenverhaeltnis -> (rand, screen_b,
    screen_h, gehaeuse_h)."""
    rand = max(2, round(b * PHONE_RAND))
    sb = b - 2 * rand
    sh = round(sb * min(max(ar, PHONE_AR[0]), PHONE_AR[1]))
    return rand, sb, sh, sh + 2 * rand


def _phone(bild: Image.Image, b: int) -> Image.Image:
    """Ein Phone-Screen in der schwarzen Fassung mit Dynamic Island."""
    ar = bild.height / max(1, bild.width)
    rand, sb, sh, h = _phone_masse(b, ar)
    skala = sb / bild.width
    voll_h = max(1, round(bild.height * skala))
    screen = bild.resize((sb, voll_h), Image.LANCZOS)
    if voll_h > sh:
        screen = screen.crop((0, 0, sb, sh))
    elif voll_h < sh:
        unten = Image.new("RGB", (sb, sh), screen.getpixel((sb // 2, voll_h - 1)))
        unten.paste(screen, (0, 0))
        screen = unten
    einheit = Image.new("RGBA", (b, h), (0, 0, 0, 0))
    ImageDraw.Draw(einheit).rounded_rectangle(
        (0, 0, b - 1, h - 1), round(b * PHONE_RADIUS), fill=GEHAEUSE + (255,))
    smaske = Image.new("L", (sb, sh), 0)
    ImageDraw.Draw(smaske).rounded_rectangle(
        (0, 0, sb - 1, sh - 1), round(sb * PHONE_SCREEN_RADIUS), fill=255)
    einheit.paste(screen, (rand, rand), smaske)
    ib, ih = round(b * INSEL_BREITE), max(2, round(b * INSEL_HOEHE))
    ix = (b - ib) // 2
    iy = rand + round(sb * INSEL_OBEN)
    ImageDraw.Draw(einheit).rounded_rectangle(
        (ix, iy, ix + ib, iy + ih), ih // 2, fill=GEHAEUSE + (255,))
    return einheit


def _kachel_hoehe(s: Stueck, b: int) -> int:
    ar = s.bild.height / max(1, s.bild.width)
    if s.art == "phone":
        return _phone_masse(b, ar)[3]
    return max(1, round(b * min(ar, KARTE_AR_MAX)))


def _kachel(s: Stueck, b: int, kontur: tuple = (255, 255, 255)) -> Image.Image:
    if s.art == "phone":
        return _phone(s.bild, b)
    return _karte(s.bild, b, _kachel_hoehe(s, b), kontur)


# --------------------------------------------------------------------------
# Geometrie

def _uebermass(W: int, H: int, winkel: float) -> tuple[int, int]:
    """Masse der 0-Grad-Leinwand, damit nach der Drehung der volle Zuschnitt
    ohne Fuellrand darin liegt."""
    a = math.radians(abs(winkel))
    W2 = int(math.ceil(W * math.cos(a) + H * math.sin(a))) + 8
    H2 = int(math.ceil(W * math.sin(a) + H * math.cos(a))) + 8
    return W2, H2


def _nach_endmass(x: float, y: float, W2: int, H2: int, W: int, H: int,
                  winkel: float) -> tuple[float, float]:
    """Ein Punkt der 0-Grad-Leinwand im fertigen, gedrehten und beschnittenen
    Bild. PIL dreht gegen den Uhrzeigersinn: rechts liegende Punkte wandern
    nach oben."""
    a = math.radians(winkel)
    dx, dy = x - W2 / 2, y - H2 / 2
    return (W / 2 + dx * math.cos(a) + dy * math.sin(a),
            H / 2 - dx * math.sin(a) + dy * math.cos(a))


def _felder(variante: str, extra: list | None = None) -> list[tuple[float, ...]]:
    """Die freizuhaltenden Felder im Pixelmass der Flaeche."""
    links = PANEL_LINKS if variante == "panel" else 0
    return [tuple(((v - links) if i % 2 == 0 else v) * PX_JE_PUNKT
                  for i, v in enumerate(feld))
            for feld in [FELD_LOGO, FELD_SEITE] + list(extra or [])]


def _schneidet(ecken: list[tuple[float, float]], feld: tuple) -> bool:
    """Ob ein konvexes Viereck ein achsenparalleles Feld schneidet
    (Trennachsen-Satz: Feldachsen und die Kantennormalen des Vierecks)."""
    x0, y0, x1, y1 = feld
    feld_ecken = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    achsen = [(1.0, 0.0), (0.0, 1.0)]
    for i in range(len(ecken)):
        (ax, ay), (bx, by) = ecken[i], ecken[(i + 1) % len(ecken)]
        achsen.append((ay - by, bx - ax))
    for nx, ny in achsen:
        a = [px * nx + py * ny for px, py in ecken]
        b = [px * nx + py * ny for px, py in feld_ecken]
        if max(a) < min(b) or max(b) < min(a):
            return False
    return True


# --------------------------------------------------------------------------
# Planen

def _plan_raster(stuecke: list[Stueck], W: int, H: int, art: str, variante: str,
                 skala: float, phase: tuple[float, float], start: int) -> dict:
    """Das Raster auf der 0-Grad-Leinwand: Spalten gleicher Breite, jede um
    `versatz` gegen die vorige verschoben, jede von oben bis unten mit
    Kacheln gefuellt, die Screens reihum. `phase` verschiebt das ganze Raster
    (Anteil des Spaltentakts quer, Anteil des mittleren Kacheltakts laengs).
    Die gerade Variante (`x0`) steht ab x0 in fester Spaltenzahl."""
    p = RASTER[(art, variante)]
    b = round(p["spalte"] * PX_JE_PUNKT * skala)
    g = round(p["luecke"] * PX_JE_PUNKT * skala)
    winkel = p["winkel"]
    W2, H2 = _uebermass(W, H, winkel) if winkel else (W, H)
    hoehen = [_kachel_hoehe(s, b) for s in stuecke]
    takt_y = sum(hoehen) / len(hoehen) + g
    takt_x = b + g
    n = len(stuecke)
    kacheln = []
    if "x0" in p:
        for j in range(p["spalten"]):
            x = p["x0"] * PX_JE_PUNKT + j * takt_x
            y = (p["start"][j % len(p["start"])] + phase[1]) * takt_y
            i = 0
            while y < H2:
                k = (start + i + j) % n
                kacheln.append((k, x, y, b, hoehen[k]))
                y += hoehen[k] + g
                i += 1
    else:
        spalten = int(math.ceil(W2 / takt_x)) + 3
        x_start = (W2 - spalten * takt_x) / 2 + phase[0] * takt_x
        for j in range(spalten):
            x = x_start + j * takt_x
            versatz = ((j * p["versatz"] + phase[1]) % 1.0) * takt_y
            y = -takt_y - versatz
            i = 0
            while y < H2 + takt_y:
                k = (start + i + j * max(1, n // 2)) % n
                kacheln.append((k, x, y, b, hoehen[k]))
                y += hoehen[k] + g
                i += 1
    return {"art": art, "winkel": winkel, "uebermass": (W2, H2), "breite": b,
            "kacheln": kacheln}


def _plan_hero(s: Stueck, W: int, H: int, variante: str, skala: float) -> dict:
    """Ein Screen allein: gross, gekippt wie sein Raster, leicht nach rechts
    unten versetzt, damit er an zwei Kanten anschneidet."""
    art = s.art
    winkel = RASTER[(art, "panel")]["winkel"]
    W2, H2 = _uebermass(W, H, winkel)
    ar = s.bild.height / max(1, s.bild.width)
    if art == "phone":
        ziel_h = HERO[(art, variante)] * H * skala
        b = 100
        while _phone_masse(b, ar)[3] < ziel_h:
            b += 4
    else:
        b = round(HERO[(art, variante)] * W * skala)
    h = _kachel_hoehe(s, b)
    x = W2 / 2 - b / 2 + 0.04 * W
    y = H2 / 2 - h / 2 + 0.05 * H
    return {"art": art, "winkel": winkel, "uebermass": (W2, H2), "breite": b,
            "kacheln": [(0, x, y, b, h)]}


def umrisse(plan: dict, W: int, H: int) -> list[list[tuple[float, float]]]:
    """Die Kachelumrisse im fertigen Bild (Pixel) - fuer die Bewertung und
    fuer den Selbsttest."""
    W2, H2 = plan["uebermass"]
    raus = []
    for _, x, y, b, h in plan["kacheln"]:
        if plan["winkel"]:
            raus.append([_nach_endmass(px, py, W2, H2, W, H, plan["winkel"])
                         for px, py in ((x, y), (x + b, y), (x + b, y + h), (x, y + h))])
        else:
            raus.append([(x, y), (x + b, y), (x + b, y + h), (x, y + h)])
    return raus


def _freihalten(plan: dict, W: int, H: int, felder: list) -> tuple[dict, float]:
    """Kacheln, die in ein freizuhaltendes Feld ragen, fallen aus dem Plan.
    Zurueck kommt der Plan ohne sie und die sichtbare Flaeche, die dabei
    verloren geht (gemessen in einem Achtel des Masses)."""
    f = 8
    verlust = Image.new("L", (W // f, H // f), 0)
    zeichne = ImageDraw.Draw(verlust)
    bleiben = []
    for kachel, ecken in zip(plan["kacheln"], umrisse(plan, W, H)):
        if any(_schneidet(ecken, feld) for feld in felder):
            zeichne.polygon([(px / f, py / f) for px, py in ecken], fill=255)
        else:
            bleiben.append(kachel)
    daten = verlust.getdata()
    return dict(plan, kacheln=bleiben), sum(daten) / 255


def _raster_waehlen(stuecke, W, H, art, variante, skala, start,
                    frei: list | None = None) -> dict:
    """Unter den Verschiebungen des Rasters die, bei der fuer die freien
    Felder (Wortmarke, Seitenzahl, NDA-Hinweis) am wenigsten Screen entfaellt.
    Deterministisch: bei Gleichstand gewinnt die erste Verschiebung."""
    felder = _felder(variante, frei)
    if "x0" in RASTER[(art, variante)]:
        plan = _plan_raster(stuecke, W, H, art, variante, skala, (0.0, 0.0), start)
        return _freihalten(plan, W, H, felder)[0]
    beste = None
    for px in (0.0, 1 / 6, 1 / 3, 1 / 2, 2 / 3, 5 / 6):
        for py in (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875):
            plan = _plan_raster(stuecke, W, H, art, variante, skala, (px, py), start)
            frei_plan, verlust = _freihalten(plan, W, H, felder)
            if beste is None or verlust < beste[0] - 1e-9:
                beste = (verlust, frei_plan)
    return beste[1]


# --------------------------------------------------------------------------
# Komponieren und sichern

def _komponieren(plan: dict, stuecke: list[Stueck], groesse: tuple,
                 grund: tuple) -> Image.Image:
    """Die Kacheln auf die 0-Grad-Leinwand, einmal drehen, beschneiden. Jede
    Kachel wird einmal skaliert (LANCZOS), das Blatt einmal gedreht (BICUBIC)."""
    W, H = groesse
    W2, H2 = plan["uebermass"]
    leinwand = Image.new("RGB", (W2, H2), grund)
    fertig_kacheln: dict[tuple[int, int], Image.Image] = {}
    kontur = _konturfarbe(grund)
    for k, x, y, b, h in plan["kacheln"]:
        if x >= W2 or y >= H2 or x + b <= 0 or y + h <= 0:
            continue
        schluessel = (k, b)
        if schluessel not in fertig_kacheln:
            fertig_kacheln[schluessel] = _kachel(stuecke[k], b, kontur)
        einheit = fertig_kacheln[schluessel]
        leinwand.paste(einheit, (round(x), round(y)), einheit.getchannel("A"))
    if not plan["winkel"]:
        return leinwand.crop((0, 0, W, H))
    gedreht = leinwand.rotate(plan["winkel"], resample=Image.BICUBIC,
                              expand=True, fillcolor=grund)
    x0 = (gedreht.width - W) // 2
    y0 = (gedreht.height - H) // 2
    return gedreht.crop((x0, y0, x0 + W, y0 + H))


def _szene(s: Stueck, groesse: tuple, ziel_name: str) -> Image.Image:
    """Eine fertig gestaltete Szene fuellt die Flaeche (cover). Quer wird der
    Ausschnitt auf den Inhalt gelegt: dorthin, wo sich am meisten vom Grund
    der Szene abhebt."""
    W, H = groesse
    bild = s.bild
    skala = max(W / bild.width, H / bild.height)
    sb, sh = round(bild.width * skala), round(bild.height * skala)
    x0 = (sb - W) // 2
    if _np is not None and sb > W:
        klein = bild.convert("RGB").resize((max(8, sb // 8), max(8, sh // 8)), Image.BILINEAR)
        arr = _np.asarray(klein, dtype=_np.int16)
        grund = _np.median(_saum(arr), axis=0)
        profil = (_np.abs(arr - grund).sum(axis=2) > ZERLEG_SCHWELLE).sum(axis=0)
        fenster = max(1, W // 8)
        summen = _np.convolve(profil, _np.ones(fenster), mode="valid")
        if len(summen):
            x0 = max(0, min(sb - W, int(_np.argmax(summen)) * 8))
    y0 = (sh - H) // 2
    if bild.height < H * SZENE_MIN or bild.width < W * SZENE_MIN:
        hinweise.append(f"{ziel_name}: {s.name} ist für eine ganze Fläche klein "
                        f"({bild.width} × {bild.height} px) – wird hochgerechnet. "
                        "Größeren Export anfragen.")
    return bild.resize((sb, sh), Image.LANCZOS).crop((x0, y0, x0 + W, y0 + H))


def _speichern(leinwand: Image.Image, ziel: Path) -> Path:
    """Die fertige Flaeche als JPEG sichern - deterministisch, hohe Guete,
    ohne Chromaunterabtastung (auf den Screens steht Schrift)."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    leinwand.save(ziel, "JPEG", quality=88, subsampling=0, optimize=True)
    return ziel


def _skala_waehlen(stuecke: list[Stueck], breite_px: int,
                   ziel_name: str) -> tuple[float, list[Stueck]]:
    """Das Raster wird als Ganzes kleiner, bis der schwaechste Screen scharf
    liegt (bis RASTER_MIN). Wer auch dann unter HOCH_MIN bleibt, fliegt raus;
    alles dazwischen wird leicht hochgerechnet und gemeldet."""
    def bedarf(s: Stueck) -> float:
        screen_b = breite_px * (1 - 2 * PHONE_RAND) if s.art == "phone" else breite_px
        return s.bild.width / screen_b

    behalten = []
    for s in stuecke:
        if bedarf(s) / RASTER_MIN < HOCH_MIN:
            hinweise.append(f"{ziel_name}: {s.name} ist {s.bild.width} px breit und "
                            "damit für das Raster zu klein – weggelassen. "
                            "Originalexport in voller Auflösung nachliefern.")
            continue
        behalten.append(s)
    if not behalten:
        return 1.0, []
    schwach = min(bedarf(s) for s in behalten)
    skala = 1.0 if schwach >= WEICH_MIN else max(RASTER_MIN, schwach / WEICH_MIN)
    for s in behalten:
        if bedarf(s) / skala < WEICH_MIN:
            hinweise.append(f"{ziel_name}: {s.name} ist {s.bild.width} px breit, liegt "
                            f"aber {breite_px * skala:.0f} px breit im Raster – wird "
                            "hochgerechnet. Schärfere Originaldatei anfragen.")
    return skala, behalten


def baue_screens(bilder: list[Path], farbe: str | None, ziel: Path,
                 variante: str = "panel", seed: int = 0,
                 nda: bool = False) -> Path:
    """Erzeugt die Flaeche und gibt den geschriebenen Pfad zurueck.

    `variante` ist "panel" fuer die rechte Haelfte einer Loesungsseite oder
    "voll" fuer die randlose Abschlussseite. `farbe=None` nimmt die neutrale
    Flaeche neutral/15. `seed` verschiebt nur, mit welchem Screen die Reihe
    beginnt - so liegen Loesungs- und Abschlussseite nicht gleich. `nda`
    haelt zusaetzlich das Feld des Vertraulichkeitshinweises frei.

    Der Pfad kann von `ziel` abweichen (gesichert wird als JPEG), deshalb ist
    der Rueckgabewert massgeblich. Meldungen holt der Aufrufer mit
    hole_hinweise() ab."""
    variante = variante if variante in GROESSEN else "panel"
    punkte = GROESSEN[variante]
    groesse = (punkte[0] * PX_JE_PUNKT, punkte[1] * PX_JE_PUNKT)
    W, H = groesse
    grund = _grundton(_farbe(farbe))
    ziel = Path(ziel).with_suffix(".jpg")

    geladen: list[tuple[str, Image.Image]] = []
    for pfad in bilder or []:
        try:
            with Image.open(pfad) as im:
                im.load()
                geladen.append((Path(pfad).name, im.copy()))
        except Exception as fehler:
            hinweise.append(f"{ziel.name}: {Path(pfad).name} nicht lesbar ({fehler})")

    plan, stuecke, bild = planen(geladen, variante, seed, ziel.name,
                                 [NDA_FELD] if nda else None)
    if bild is not None:
        return _speichern(bild, ziel)
    if plan is None:
        return _speichern(Image.new("RGB", groesse, grund), ziel)
    return _speichern(_komponieren(plan, stuecke, groesse, grund), ziel)


def planen(geladen: list[tuple[str, Image.Image]], variante: str, seed: int,
           ziel_name: str, frei: list | None = None):
    """Material aufbereiten und die Flaeche planen. Zurueck kommen (plan,
    stuecke, bild): ein Raster- oder Einzelplan, oder - bei reinen Szenen -
    gleich das fertige Bild; (None, [], None) heisst: nichts zu zeigen."""
    punkte = GROESSEN[variante]
    W, H = punkte[0] * PX_JE_PUNKT, punkte[1] * PX_JE_PUNKT
    stuecke = aufbereiten(geladen, ziel_name)
    screens_ = [s for s in stuecke if s.art != "szene"]
    szenen = [s for s in stuecke if s.art == "szene"]

    if not screens_ and not szenen:
        hinweise.append(f"{ziel_name}: keine Screens – die Fläche bleibt leer")
        return None, [], None
    if not screens_:
        if len(szenen) > 1:
            hinweise.append(f"{ziel_name}: {len(szenen)} Showcase-Szenen – die "
                            f"Fläche zeigt {szenen[0].name}, die übrigen nicht. "
                            "Die Reihenfolge in der JSON entscheidet.")
        return None, szenen, _szene(szenen[0], (W, H), ziel_name)
    if szenen:
        hinweise.append(f"{ziel_name}: {', '.join(s.name for s in szenen)} – fertige "
                        "Showcase-Szene, passt nicht ins Raster und bleibt draußen.")

    phones = [s for s in screens_ if s.art == "phone"]
    art = "phone" if len(phones) > len(screens_) / 2 else "desktop"
    if art == "desktop":
        # Hochformate zwischen Desktop-Screens liegen als Karte im Raster -
        # von oben gezeigt, ohne Fassung. Weglassen hiesse Material verlieren.
        passend = [s if s.art == "desktop" else Stueck(s.name, s.bild, "desktop")
                   for s in screens_]
    else:
        passend = [s for s in screens_ if s.art == "phone"]
        if len(passend) < len(screens_):
            anders = [s.name for s in screens_ if s.art != "phone"]
            hinweise.append(f"{ziel_name}: {', '.join(anders)} – Desktop-Screen "
                            "zwischen Phones, passt nicht ins Phone-Raster und "
                            "bleibt draußen.")
    if len(passend) > MAX_SCREENS:
        hinweise.append(f"{ziel_name}: {len(passend)} Screens, das Raster zeigt "
                        f"{MAX_SCREENS} – die Reihenfolge in der JSON entscheidet.")
        passend = passend[:MAX_SCREENS]

    if len(passend) == 1:
        s = passend[0]
        hero_b = (HERO[(art, variante)] * W if art == "desktop"
                  else HERO[(art, variante)] * H / 2.2)
        skala, passend = _skala_waehlen(passend, round(hero_b), ziel_name)
        if not passend:
            return None, [], None
        return _plan_hero(passend[0], W, H, variante, skala), passend, None

    breite_px = round(RASTER[(art, variante)]["spalte"] * PX_JE_PUNKT)
    skala, passend = _skala_waehlen(passend, breite_px, ziel_name)
    if not passend:
        hinweise.append(f"{ziel_name}: alle Screens sind für die Fläche zu klein "
                        "– sie bleibt reine Grundfläche. Originalexporte nachliefern.")
        return None, [], None
    if len(passend) == 1:
        return _plan_hero(passend[0], W, H, variante, skala), passend, None
    return (_raster_waehlen(passend, W, H, art, variante, skala, seed % len(passend),
                            frei), passend, None)


def main() -> None:
    argumente = sys.argv[1:]
    if not argumente or "--hilfe" in argumente:
        raise SystemExit(__doc__)
    farbe = None
    ziel = Path("screens.png")
    variante = "panel"
    seed = 0
    nda = False
    dateien: list[Path] = []
    i = 0
    while i < len(argumente):
        a = argumente[i]
        if a == "--farbe" and i + 1 < len(argumente):
            farbe, i = argumente[i + 1], i + 1
        elif a == "--aus" and i + 1 < len(argumente):
            ziel, i = Path(argumente[i + 1]), i + 1
        elif a == "--seed" and i + 1 < len(argumente):
            seed, i = int(argumente[i + 1]), i + 1
        elif a == "--voll":
            variante = "voll"
        elif a == "--nda":
            nda = True
        elif a == "--panel":
            variante = "panel"
        else:
            dateien.append(Path(a))
        i += 1

    pfad = baue_screens(dateien, farbe, ziel, variante, seed, nda)
    for zeile in hole_hinweise():
        print(zeile)
    print(pfad)


if __name__ == "__main__":
    main()
