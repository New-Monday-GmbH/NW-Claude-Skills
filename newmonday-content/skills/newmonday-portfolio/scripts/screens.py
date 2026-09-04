#!/usr/bin/env python3
"""Baut die Markenflaeche mit den praesentierten Screens: eine Kaskade.

    python3 scripts/screens.py --farbe "#0018a8" --aus panel.jpg s1.png s2.png
    python3 scripts/screens.py --farbe "#0018a8" --voll --aus ende.jpg material/*.png

WeasyPrint kennt keine Transformationen und keine Verlaeufe, die hier taugen.
Der Look muss deshalb im Bild entstehen und nicht im Stylesheet - hier wird
die fertige Flaeche gerechnet, der Renderer platziert sie danach nur noch.

Die Darstellung ist eine **diagonale Kaskade** (Stand 9), gemessen an den
Referenzportfolios (Gottscheck S. 14/15/18/19, Lenz S. 14-23, New-Monday-
Fassung Enrico Meermeier S. 15-24): wenige, grosse Screens auf satter,
dunkler Markenfarbe, diagonal versetzt und an den Kanten entschlossen
angeschnitten.

- **Satter, dunkler Grund.** Die Markenfarbe steht voll gesaettigt; ist sie
  zu hell, wird sie Richtung Schwarz gezogen (GRUND_HELL_MAX/GRUND_ZIEL).
  Ohne Markenfarbe ein dunkles Petrol (NEUTRAL). Nie aufgehellt: Stand 8
  mischte 88 % Richtung Weiss, und dunkle Screens schwebten auf fahlem
  Grau - genau das kam als "sieht random rumfliegend aus" zurueck.
- **Wenige, grosse Screens.** Ein Panel traegt 1-3 Desktop-Screens (bis 6
  Hochformate), die volle Folie 2-6 (bis 8 Hochformate). Jeder Screen liegt
  gross - auf der vollen Folie um die halbe Folienbreite, wie in den
  Referenzen. Eine Wand aus vielen kleinen Kacheln kommt in keiner Referenz
  vor und ist mit Stand 9 abgeschafft.
- **Diagonale mit Anschnitt.** Der obere Screen blutet ueber die obere
  (und linke) Kante hinaus, der untere ueber die rechte und untere - die
  Komposition haengt an den Kanten, nichts schwebt frei in der Mitte. Der
  Grund zeigt sich als Negativraum der Diagonale, nicht als Rand um jede
  Kachel.
- **Ein gemeinsamer Kippwinkel.** Die ganze Kaskade liegt um WINKEL Grad
  gegen den Uhrzeigersinn gekippt. Kein Screen ist einzeln gedreht:
  komponiert wird auf einer uebergrossen Leinwand bei null Grad, DIESE
  Leinwand wird genau einmal gedreht (BICUBIC) und dann aufs Folienmass
  beschnitten. Jeder Screen wird genau einmal skaliert (LANCZOS).
- **Keine Fassungen.** Kein Browserfenster, kein Geraeterahmen, keine
  Ampelpunkte - nur Karten mit leicht gerundeten Ecken und weichem, flachem
  Schatten. Screens, die als Mockup mit Rand ankommen, beschneidet der
  Freisteller auf den Inhalt.
- **Wortmarke, Seitenzahl und NDA-Hinweis liegen auf Screens.** Unter ihren
  Ecken liegt deshalb ein weicher, dunkler Verlaufsschleier in der
  abgedunkelten Markenfarbe - ohne harte Kante. Die Kontrastmessung des
  Renderers entscheidet weiter ueber helle oder dunkle Wortmarke.

Fuenf Vorgaenger sind bewusst verworfen: Zufallsstreuung mit Perspektive,
gedrehtes 15-Grad-Raster, flaches Editorial-/Showcase-Raster (alle "sieht
komisch aus"), die Buehne aus Stand 7 (Fassungen, Ueberlapp-Paar, kleine
Screens mittig auf leerer Flaeche) und die Kachelwand aus Stand 8: viele
kleine Kacheln auf hell aufgehelltem Grund - im fertigen Deck wirkten die
Flaechen "random rumfliegend", waehrend alle Referenzen wenige grosse
Screens auf dunklem Grund zeigen.

Komposite werden zerlegt: Ein Quellbild, das mehrere getrennte Screens auf
einheitlichem Grund zeigt (typisch: Showcase-Exporte), zerfaellt in einzelne
Karten - aber nur, wenn die Teile gross genug bleiben, um scharf zu liegen.
Ueberlappend montierte Screens lassen sich nicht trennen und bleiben ganz.

Zu weiche Screens schrumpfen zuerst in ihrem Platz (bis SCHRUMPF_MIN der
Zielbreite), dann fliegen sie raus und die Kaskade wird mit einem Screen
weniger neu gelegt. Bleibt gar nichts, wird die reine Grundflaeche
geschrieben; die Uebergabe bittet dann um Originalexporte.

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

# Stand des Anordnungs-Algorithmus. Gehoert in jeden Cache-Fingerabdruck, der
# fertige Flaechen wiederverwendet: ohne ihn liefert ein Zwischenspeicher von
# vor einer Layoutaenderung stumm die alte Anordnung weiter. Bei jeder
# Aenderung an Anordnung, Massen oder Meldungen hochzaehlen.
# Stand 9: diagonale Kaskade - wenige grosse Screens, satter dunkler Grund.
LAYOUT_STAND = 9

# Qualitaets-Gate: unter diesem Anteil der platzierten Breite schrumpft ein
# Screen (bis SCHRUMPF_MIN), statt hochgerechnet zu werden; zwischen
# WEICH_MIN und 0.98 bleibt er mit Warnung stehen.
WEICH_MIN = 0.75

# Zwei Pixel je Punkt: die Flaeche wird im PDF nur skaliert, nie vergroessert.
PX_JE_PUNKT = 2
GROESSEN = {"panel": (1020, 1080), "voll": (1920, 1080)}
# Ohne Markenfarbe: ein dunkles Petrol in der Familie von --brand. Die
# Referenzen greifen im Zweifel zu Schwarz und Dunkelblau, nie zu Hellgrau -
# Lenz legt selbst rote Marken (DB, MediaMarkt) auf schwarzen Grund.
NEUTRAL = "#103537"

# Der gemeinsame Kippwinkel der Kaskade, in Grad gegen den Uhrzeigersinn.
# In den Referenzen liegen Desktop-Screens bei 5-10, Phones bei 10-12 Grad.
WINKEL = 8.0

# Der Grund ist die satte Markenfarbe. Nur wenn sie zu hell ist (perzeptive
# Luminanz ueber GRUND_HELL_MAX), wird sie Richtung Schwarz gezogen, bis sie
# GRUND_ZIEL erreicht - helle Screens brauchen dunklen Grund, sonst schwimmt
# die Flaeche.
GRUND_HELL_MAX = 0.55
GRUND_ZIEL = 0.42

# Wie viele Screens eine Kaskade traegt, je Format und Variante. Die
# Referenzen zeigen auf Loesungsseiten 1-3 Desktop-Screens (Gottscheck:
# immer genau 2) bzw. bis 6 Phones (Lenz S. 15), auf vollen Flaechen bis
# etwa 6 Desktop-Screens bzw. 8 Phones.
MAX_KASKADE = {
    ("quer", "panel"): 3,
    ("quer", "voll"): 6,
    ("hoch", "panel"): 6,
    ("hoch", "voll"): 8,
}

# Eine zu weiche Lage schrumpft bis zu diesem Anteil ihrer Zielbreite in
# ihrem Platz, bevor sie rausfliegt. 0.5 ist bewusst grosszuegig: eine
# kleinere, aber scharfe Lage ist besser als eine blanke Flaeche
# (Beispiel-Portfolio: ein 834-px-Screen fiel mit 53 Prozent knapp durch
# eine engere Grenze, und die Loesungsseite blieb leer).
SCHRUMPF_MIN = 0.50

# Kaskaden-Vorlagen: je Eintrag (mx, my, groesse) - mx/my sind der Versatz
# des Kachelzentrums von der Mitte des spaeteren Zuschnitts, als Anteil von
# dessen Breite/Hoehe; `groesse` ist fuer Querformate die Kachelbreite als
# Anteil der Zuschnittbreite, fuer Hochformate die Kachelhoehe als Anteil
# der Zuschnitthoehe. Die Werte sind an den Referenzen gemessen: oberer
# Screen blutet ueber die obere (und linke) Kante, unterer ueber rechts und
# unten (Gottscheck), ein Hero traegt die Seite allein (Enrico S. 19),
# drei liegen als grosser Kopf mit zwei Anschluessen (Lenz S. 18/23).
# Desktop-Slots bleiben unter 1920 px (voll: 0.50 x 3840), damit ein
# gewoehnlicher 1920er-Export ohne Hochrechnen jede Lage traegt.
KASKADE_QUER = {
    "panel": {
        1: [(0.06, 0.12, 0.94)],
        2: [(-0.13, -0.32, 0.92), (0.13, 0.32, 0.92)],
        3: [(0.02, -0.34, 0.94), (-0.27, 0.31, 0.60), (0.30, 0.35, 0.60)],
    },
    "voll": {
        1: [(0.17, 0.13, 0.50)],
        2: [(-0.24, -0.28, 0.50), (0.24, 0.28, 0.50)],
        3: [(-0.07, -0.32, 0.50), (-0.34, 0.32, 0.40), (0.28, 0.31, 0.44)],
        4: [(-0.30, -0.31, 0.42), (0.16, -0.34, 0.44),
            (-0.16, 0.34, 0.44), (0.32, 0.30, 0.42)],
        5: [(-0.32, -0.32, 0.40), (0.07, -0.36, 0.42), (0.38, -0.22, 0.36),
            (-0.14, 0.34, 0.42), (0.29, 0.35, 0.40)],
        6: [(-0.34, -0.36, 0.38), (0.02, -0.30, 0.40), (0.37, -0.36, 0.38),
            (-0.34, 0.30, 0.38), (0.02, 0.38, 0.40), (0.37, 0.30, 0.38)],
    },
}
KASKADE_HOCH = {
    "panel": {
        1: [(0.02, 0.02, 0.88)],
        2: [(-0.15, -0.16, 0.76), (0.16, 0.18, 0.76)],
        3: [(-0.24, -0.26, 0.68), (0.00, 0.06, 0.68), (0.25, 0.34, 0.68)],
        4: [(-0.15, -0.30, 0.62), (0.17, -0.24, 0.62),
            (-0.17, 0.26, 0.62), (0.15, 0.32, 0.62)],
        5: [(-0.26, -0.28, 0.60), (0.00, -0.32, 0.60), (0.27, -0.24, 0.60),
            (-0.14, 0.30, 0.60), (0.16, 0.34, 0.60)],
        6: [(-0.26, -0.28, 0.58), (0.00, -0.34, 0.58), (0.27, -0.26, 0.58),
            (-0.27, 0.28, 0.58), (0.00, 0.34, 0.58), (0.26, 0.30, 0.58)],
    },
    "voll": {
        1: [(0.05, 0.05, 0.86)],
        2: [(-0.12, -0.14, 0.78), (0.13, 0.16, 0.78)],
    },
}
# Ab drei Hochformaten auf der vollen Flaeche steht der Kamm: eine Reihe
# grosser Phones, abwechselnd nach oben und unten versetzt (Lenz S. 14/15).
KAMM_HOEHE = {3: 0.72, 4: 0.70, 5: 0.68, 6: 0.66, 7: 0.62, 8: 0.60}
KAMM_VERSATZ = 0.22
KAMM_BREITE = 0.37

# Runde Ecken und Schatten der Karten. Der Schatten ist auf hellem Grund
# deutlich zurueckgenommen: weicher, geringe Deckkraft, kaum Versatz.
ECKE_ANTEIL = 0.03
ECKE_MIN, ECKE_MAX = 20, 56
SCHATTEN_DECKKRAFT = 34      # von 255
SCHATTEN_WEICHE = 0.05       # Anteil der kuerzeren Kante
SCHATTEN_VERSATZ = 0.007

# Der Verlaufsschleier unter Wortmarke (oben rechts) und Seitenzahl/NDA
# (unten rechts): abgedunkelte Markenfarbe, elliptisch aus der Ecke, ohne
# harte Kante. Masse in Pixeln des fertigen Bildes. Er ist ein Scrim, kein
# Vorhang: SCHLEIER_DECKKRAFT deckelt die Deckkraft, damit der Screen
# darunter lesbar bleibt - der volldeckende Schleier aus Stand 8 kam in der
# Referenz-Gegenprobe als "gedimmt, kaum noch lesbar" zurueck.
SCHLEIER_DUNKEL = 0.68       # Anteil Richtung Schwarz
SCHLEIER_DECKKRAFT = 0.60    # Obergrenze der Deckkraft (0-1)
SCHLEIER_BREITER = 1.85      # horizontale Streckung der Ellipse
# Die Radien decken gerade das Moebelfeld und laufen kurz aus - die
# Endpruefung des ersten Wand-Laufs kam mit "der Schleier verschluckt
# Kachelinhalt" zurueck, seitdem sind sie so knapp wie die Messfelder.
SCHLEIER_OBEN = (340, 640)   # voll deckend bis R1, aus bis R2
SCHLEIER_UNTEN = (480, 780)
SCHLEIER_WEICH = 70          # Gauss am Ende, gegen jede Restkante
# Die Felder, in denen die Moebel stehen (Breite, Hoehe in Punkten von der
# rechten Ecke aus) - nur wenn dort Kacheln liegen, kommt der Schleier.
MOEBEL_OBEN = (240, 100)
MOEBEL_UNTEN = (330, 150)

# Mockup-Beschnitt: nur wenn deutlich Rand faellt und der Fund glaubhaft ist.
FREISTELL_OBEN = 0.86
FREISTELL_UNTEN = 0.25

# Komposit-Zerleger: Mindestmasse eines herausgeloesten Screens im Original
# (kuerzere/laengere Kante) - kleinere Teile blieben in der Kaskade unscharf,
# dann bleibt das Komposit lieber ganz.
TEIL_KURZ, TEIL_LANG = 500, 900
TEIL_FLAECHE = 0.025         # Mindestanteil eines Teils an der Bildflaeche
TEIL_RECHTECK = 0.85         # Fuellgrad der Box: darunter ist es kein Screen
ZERLEG_SCHWELLE = 60         # Farbabstand zum Grund (Summe ueber 3 Kanaele)

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


def _mischen(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _luminanz(farbe: tuple) -> float:
    r, g, b = farbe
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def _grundton(marke: tuple) -> tuple[int, int, int]:
    """Der Grund ist die satte Markenfarbe; zu helle Toene werden Richtung
    Schwarz gezogen, bis sie tragen. Dunkle Marken (Navy, Schwarz) bleiben,
    wie sie sind - so halten es auch die Referenzen."""
    if _luminanz(marke) <= GRUND_HELL_MAX:
        return marke
    t = 0.0
    ton = marke
    while _luminanz(ton) > GRUND_ZIEL and t < 1.0:
        t += 0.05
        ton = _mischen(marke, (0, 0, 0), t)
    return ton


# --------------------------------------------------------------------------
# Material vorbereiten

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
    rand = 0.006 * min(b, h)
    x0 = max(0, int(x0 - rand))
    y0 = max(0, int(y0 - rand))
    x1 = min(b, int(x1 + rand))
    y1 = min(h, int(y1 + rand))
    return bild.crop((x0, y0, x1, y1)), ((x1 - x0) * (y1 - y0)) / (b * h)


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


def _zerlegen(bild: Image.Image, name: str) -> list[tuple[str, Image.Image]]:
    """Ein Komposit in einzelne Screens zerlegen, wenn es eines ist.

    Ein Quellbild mit mehreren getrennten, rechteckigen Inhalten auf
    einheitlichem Grund zerfaellt in seine Teile. Zerlegt wird nur, wenn die
    Teile gross genug bleiben (TEIL_KURZ/TEIL_LANG) - kleine Schnipsel waeren
    in der Kaskade unscharf, dann traegt das Komposit als Ganzes mehr. Echte
    Screenshots (Inhalt fuellt das Bild) passieren unveraendert; ueberlappend
    montierte Screens lassen sich nicht trennen und bleiben ganz."""
    if _np is None:
        return [(name, bild)]
    b, h = bild.size
    if min(b, h) < 700:
        return [(name, bild)]
    f = min(1.0, 640 / max(b, h))
    probe = bild.convert("RGB")
    if f < 1.0:
        probe = probe.resize((round(b * f), round(h * f)), Image.BILINEAR)
    arr = _np.asarray(probe, dtype=_np.int16)
    rand = max(2, round(0.02 * min(arr.shape[:2])))
    saum = _np.concatenate([
        arr[:rand].reshape(-1, 3), arr[-rand:].reshape(-1, 3),
        arr[:, :rand].reshape(-1, 3), arr[:, -rand:].reshape(-1, 3)])
    grund = _np.median(saum, axis=0)
    abstand = _np.abs(arr - grund).sum(axis=2)
    maske = abstand > ZERLEG_SCHWELLE

    # Punktmuster und Rauschen wegschleifen, Luecken in Screens schliessen.
    mbild = Image.fromarray((maske * 255).astype("uint8"))
    mbild = mbild.filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.MaxFilter(7)).filter(ImageFilter.MaxFilter(7))
    maske = _np.asarray(mbild) > 128

    # Ein echter Screenshot traegt Inhalt bis an die Kanten (Header, Menü,
    # Footer) - ein Komposit hat rundum Grund. Ohne freien Saum auf allen
    # vier Seiten wird gar nicht erst zerlegt; genau an dieser Stelle hat
    # der Zerleger sonst einen Website-Screenshot auf sein Aufmacherfoto
    # beschnitten.
    zeilen = _np.flatnonzero(maske.any(axis=1))
    spalten_idx = _np.flatnonzero(maske.any(axis=0))
    if not len(zeilen) or not len(spalten_idx):
        return [(name, bild)]
    hoehe_m, breite_m = maske.shape
    saum_frei = min(zeilen[0] / hoehe_m, (hoehe_m - 1 - zeilen[-1]) / hoehe_m,
                    spalten_idx[0] / breite_m,
                    (breite_m - 1 - spalten_idx[-1]) / breite_m)
    if saum_frei < 0.025:
        return [(name, bild)]

    teile = [t for t in _komponenten(maske)
             if t[4] >= TEIL_FLAECHE * maske.size]
    if not teile:
        return [(name, bild)]

    def original_box(t, luft_anteil=0.006):
        x0, y0, x1, y1, _ = t
        luft = round(luft_anteil * min(b, h))
        return (max(0, int(x0 / f) - luft), max(0, int(y0 / f) - luft),
                min(b, int((x1 + 1) / f) + luft), min(h, int((y1 + 1) / f) + luft))

    if len(teile) == 1:
        # Ein einzelner Inhalt auf viel Grund: auf ihn beschneiden. Das ist
        # der Fall, an dem der Kantendetektor des Freistellers scheitert -
        # Punktmuster im Grund erzeugen ueberall Kanten, der Farbabstand
        # zum Grund nicht.
        t = teile[0]
        box_anteil = ((t[2] - t[0] + 1) * (t[3] - t[1] + 1)) / maske.size
        fuellung = t[4] / ((t[2] - t[0] + 1) * (t[3] - t[1] + 1))
        if 0.10 < box_anteil < FREISTELL_OBEN and fuellung >= TEIL_RECHTECK:
            ox0, oy0, ox1, oy1 = original_box(t)
            if min(ox1 - ox0, oy1 - oy0) >= TEIL_KURZ:
                hinweise.append(
                    f"{name}: Screen lag auf großem Grund – auf den Inhalt "
                    f"beschnitten ({box_anteil * 100:.0f} % der Fläche behalten)")
                return [(name, bild.crop((ox0, oy0, ox1, oy1)))]
        return [(name, bild)]

    scheiben: list[tuple[str, Image.Image]] = []
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
            verworfen += 1               # zu klein, wuerde in der Kaskade weich
            continue
        scheiben.append((f"{name}·{len(scheiben) + 1}",
                         bild.crop((ox0, oy0, ox1, oy1))))

    if len(scheiben) < 2:
        # Kein sauberer Mehrfach-Schnitt. Wenn wenigstens der groesste Teil
        # ein sauberer Screen ist, auf ihn beschneiden - ein grosser echter
        # Screen traegt mehr als das ganze Komposit mit totem Grund.
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
            return [(name, bild.crop((ox0, oy0, ox1, oy1)))]
        return [(name, bild)]
    hinweise.append(
        f"{name}: Komposit mit {len(scheiben)} einzelnen Screens – zerlegt"
        + (f", {verworfen} zu kleine oder überlappte Teile bleiben draußen"
           if verworfen else ""))
    return scheiben


# --------------------------------------------------------------------------
# Kacheln

def _seitenverhaeltnis(bild: Image.Image) -> float:
    return bild.height / max(1, bild.width)


def _hoch(bild: Image.Image) -> bool:
    return _seitenverhaeltnis(bild) >= 1.2


def _kachel(bild: Image.Image, b: int, h: int) -> Image.Image:
    """Ein Screen als pure Karte: einmal LANCZOS skaliert, leicht gerundete
    Ecken - keine Fassung, kein Rahmen."""
    einheit = Image.new("RGBA", (b, h), (0, 0, 0, 0))
    screen = bild.convert("RGB").resize((b, h), Image.LANCZOS)
    einheit.paste(screen, (0, 0))
    radius = int(min(ECKE_MAX, max(ECKE_MIN, min(b, h) * ECKE_ANTEIL)))
    maske = Image.new("L", (b, h), 0)
    ImageDraw.Draw(maske).rounded_rectangle((0, 0, b - 1, h - 1), radius, fill=255)
    einheit.putalpha(maske)
    return einheit


def _aufbringen(leinwand: Image.Image, belegt: Image.Image, bild: Image.Image,
                x: float, y: float, b: float, h: float) -> None:
    """Eine Kachel mit weichem, flachem Schatten auf die Leinwand legen.
    `belegt` fuehrt mit, wo Kacheln liegen (fuer Deckungs- und Eckpruefung)."""
    zb, zh = max(2, round(b)), max(2, round(h))
    x, y = round(x), round(y)
    if x >= leinwand.width or y >= leinwand.height or x + zb <= 0 or y + zh <= 0:
        return
    einheit = _kachel(bild, zb, zh)
    alpha = einheit.getchannel("A")
    kante = min(zb, zh)
    weiche = max(6.0, kante * SCHATTEN_WEICHE)
    versatz = int(kante * SCHATTEN_VERSATZ)
    schatten = alpha.filter(ImageFilter.GaussianBlur(weiche))
    schatten = schatten.point(lambda w: w * SCHATTEN_DECKKRAFT // 255)
    leinwand.paste((0, 0, 0), (x + versatz, y + versatz), schatten)
    leinwand.paste(einheit, (x, y), alpha)
    belegt.paste(255, (x, y), alpha)


# --------------------------------------------------------------------------
# Geometrie: Drehung, Zuschnitt, Sichtbarkeit

def _uebermass(W: int, H: int) -> tuple[int, int]:
    """Masse der 0-Grad-Leinwand, damit nach der Drehung der volle Zuschnitt
    ohne Fuellrand darin liegt."""
    a = math.radians(WINKEL)
    W2 = int(math.ceil(W * math.cos(a) + H * math.sin(a))) + 8
    H2 = int(math.ceil(W * math.sin(a) + H * math.cos(a))) + 8
    return W2, H2


def _drehen_und_beschneiden(leinwand: Image.Image, W: int, H: int,
                            grund: tuple) -> Image.Image:
    """Die eine Drehung des ganzen Blattes, dann der Zuschnitt aufs Mass."""
    gedreht = leinwand.rotate(WINKEL, resample=Image.BICUBIC, expand=True,
                              fillcolor=grund)
    x0 = (gedreht.width - W) // 2
    y0 = (gedreht.height - H) // 2
    return gedreht.crop((x0, y0, x0 + W, y0 + H))


# --------------------------------------------------------------------------
# Der Verlaufsschleier unter den Moebeln

def _schleier(bild: Image.Image, belegt_final: Image.Image, marke: tuple) -> None:
    """Wortmarke, Seitenzahl und NDA-Hinweis liegen auf Screens: unter ihre
    Ecken kommt ein weicher, dunkler Verlaufsschleier in der abgedunkelten
    Markenfarbe. Nur dort, wo wirklich Kacheln liegen - auf blankem Grund
    traegt die Messung des Renderers auch ohne Schleier."""
    if _np is None:
        return
    W, H = bild.size
    tief = _mischen(marke, (0, 0, 0), SCHLEIER_DUNKEL)
    beleg = _np.asarray(belegt_final.resize((W // 8, H // 8), Image.BILINEAR))

    def ecke_belegt(feld: tuple, oben: bool) -> bool:
        fb, fh = feld[0] * PX_JE_PUNKT // 8, feld[1] * PX_JE_PUNKT // 8
        x0 = max(0, beleg.shape[1] - fb - 10)
        if oben:
            fenster = beleg[:fh + 10, x0:]
        else:
            fenster = beleg[-(fh + 10):, x0:]
        return fenster.mean() > 24

    ys, xs = _np.mgrid[0:H, 0:W].astype(_np.float32)
    maske = _np.zeros((H, W), dtype=_np.float32)
    for feld, (r1, r2), oben in ((MOEBEL_OBEN, SCHLEIER_OBEN, True),
                                 (MOEBEL_UNTEN, SCHLEIER_UNTEN, False)):
        if not ecke_belegt(feld, oben):
            continue
        cy = 0.0 if oben else float(H)
        d = _np.hypot((xs - W) / SCHLEIER_BREITER, ys - cy)
        stufe = _np.clip((r2 - d) / max(1.0, r2 - r1), 0.0, 1.0)
        maske = _np.maximum(maske, stufe)
    if not maske.any():
        return
    mbild = Image.fromarray((maske * 255 * SCHLEIER_DECKKRAFT).astype("uint8"))
    mbild = mbild.filter(ImageFilter.GaussianBlur(SCHLEIER_WEICH))
    bild.paste(tief, (0, 0), mbild)


# --------------------------------------------------------------------------
# Die Kaskade

def _kamm_vorlage(n: int) -> list[tuple[float, float, float]]:
    """Ab drei Hochformaten auf der vollen Flaeche: eine Reihe grosser
    Phones, abwechselnd nach oben und unten versetzt - der Kamm aus Lenz
    S. 14/15. Deterministisch, symmetrisch um die Mitte."""
    hh = KAMM_HOEHE.get(n, KAMM_HOEHE[max(KAMM_HOEHE)])
    breite = 2 * KAMM_BREITE
    xs = [-KAMM_BREITE + breite * i / (n - 1) for i in range(n)]
    return [(x, KAMM_VERSATZ if i % 2 else -KAMM_VERSATZ, hh)
            for i, x in enumerate(xs)]


def _vorlage(n: int, typ: str, variante: str) -> list[tuple[float, float, float]]:
    if typ == "hoch":
        vorlagen = KASKADE_HOCH[variante]
        if n in vorlagen:
            return vorlagen[n]
        if variante == "voll":
            return _kamm_vorlage(n)
        return vorlagen[max(vorlagen)]
    return KASKADE_QUER[variante][min(n, max(KASKADE_QUER[variante]))]


# Ueberhang einer geschrumpften Kachel ueber die Kante, die sie laut Vorlage
# anschneidet: Anteil ihrer neuen Breite/Hoehe. So bleibt der Anschnitt
# erhalten, statt dass die Kachel nach dem Schrumpfen frei in der Flaeche
# schwebt.
SCHRUMPF_UEBERHANG = 0.10


def _plan_kaskade(eintraege: list, W: int, H: int, variante: str,
                  name: str):
    """Den Kaskadenplan rechnen: Positionen in der 0-Grad-Leinwand.

    Die Vorlage haengt an der Zahl der Screens und am Mehrheitsformat.
    Screens behalten ihre Eingangsreihenfolge - das staerkste Material
    zuerst, es bekommt den Hero-Platz der Vorlage. Ein Hochformat in einem
    Querformat-Platz wird ueber die Hoehe bemessen (und umgekehrt), damit
    kein Phone meterhoch im Anschnitt liegt.

    Das Qualitaets-Gate laeuft hier mit, weil nur der Plan weiss, welche
    Kante eine Kachel anschneiden soll: Eine zu weiche Lage schrumpft in
    ihrem Platz und behaelt dabei einen Ueberhang ueber jede Kante, die sie
    laut Vorlage blutet - erst unter SCHRUMPF_MIN fliegt sie raus. Zurueck
    kommen (plan, geschrumpft, meldungen, zu_weich): `zu_weich` sind
    (name, bild)-Paare, mit denen der Aufrufer neu planen muss."""
    W2, H2 = _uebermass(W, H)
    cx, cy = W2 / 2, H2 / 2
    a = math.radians(WINKEL)
    ca, sa = math.cos(a), math.sin(a)

    bilder = [b for _, b in eintraege]
    hoch_zahl = sum(1 for b in bilder if _hoch(b))
    typ = "hoch" if hoch_zahl > len(bilder) / 2 else "quer"
    vorlage = _vorlage(len(bilder), typ, variante)

    plan = []
    geschrumpft: set[int] = set()
    meldungen: list[str] = []
    zu_weich: list[tuple[str, Image.Image]] = []
    for (bname, bild), (mx, my, groesse) in zip(eintraege, vorlage):
        ar = _seitenverhaeltnis(bild)
        if typ == "hoch":
            h = groesse * H
            w = h / ar
            if not _hoch(bild):
                # Querformat im Hochformat-Platz: ueber die Breite deckeln.
                w = min(h / ar, (0.95 if variante == "panel" else 0.50) * W)
                h = w * ar
        else:
            w = groesse * W
            h = w * ar
            if _hoch(bild):
                # Hochformat im Querformat-Platz: ueber die Hoehe bemessen.
                h = min(w * ar * 0.62, 0.80 * H)
                w = h / ar

        # Gate: schrumpfen im Zuschnittraum, Anschnitt erhalten.
        px, py = mx * W, my * H
        if bild.width < w * WEICH_MIN:
            w_neu = bild.width / WEICH_MIN
            if w_neu < SCHRUMPF_MIN * w:
                zu_weich.append((bname, bild))
                continue
            meldungen.append(
                f"{name}: {bname} ist {bild.width} px breit – die Lage wurde "
                f"von {w:.0f} auf {w_neu:.0f} px verkleinert, damit sie "
                "scharf bleibt. Originalexport in voller Auflösung ergäbe "
                "die volle Größe.")
            h_neu = w_neu * h / w
            ueber_x = SCHRUMPF_UEBERHANG * w_neu
            ueber_y = SCHRUMPF_UEBERHANG * h_neu
            if px + w / 2 > W / 2:              # blutet rechts
                px = W / 2 + ueber_x - w_neu / 2
            elif px - w / 2 < -W / 2:           # blutet links
                px = -W / 2 - ueber_x + w_neu / 2
            if py + h / 2 > H / 2:              # blutet unten
                py = H / 2 + ueber_y - h_neu / 2
            elif py - h / 2 < -H / 2:           # blutet oben
                py = -H / 2 - ueber_y + h_neu / 2
            w, h = w_neu, h_neu
            geschrumpft.add(id(bild))

        qx = cx + px * ca - py * sa
        qy = cy + px * sa + py * ca
        plan.append([bild, qx - w / 2, qy - h / 2, w, h])
    return plan, geschrumpft, meldungen, zu_weich


# --------------------------------------------------------------------------
# Doubletten

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


# --------------------------------------------------------------------------
# Komponieren und sichern

def _komponieren(plan: list, uebermass: tuple, groesse: tuple,
                 marke: tuple) -> tuple[Image.Image, Image.Image]:
    """Den Plan auf die uebergrosse Leinwand bringen, einmal drehen,
    beschneiden. Zurueck kommen das fertige Bild und die Belegt-Maske im
    Endmass (fuer Schleier- und Deckungspruefung)."""
    grund = _grundton(marke)
    W, H = groesse
    leinwand = Image.new("RGB", uebermass, grund)
    belegt = Image.new("L", uebermass, 0)
    for bild, x, y, b, h in plan:
        _aufbringen(leinwand, belegt, bild, x, y, b, h)
    fertig = _drehen_und_beschneiden(leinwand, W, H, grund)
    belegt_final = _drehen_und_beschneiden(
        belegt.convert("RGB"), W, H, (0, 0, 0)).convert("L")
    _schleier(fertig, belegt_final, marke)
    return fertig, belegt_final


def _speichern(leinwand: Image.Image, ziel: Path) -> Path:
    """Die fertige Flaeche als JPEG sichern - deterministisch, hohe Guete,
    ohne Chromaunterabtastung (auf den Screens steht Schrift)."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    leinwand.save(ziel, "JPEG", quality=88, subsampling=0, optimize=True)
    return ziel


def baue_screens(bilder: list[Path], farbe: str | None, ziel: Path,
                 variante: str = "panel", seed: int = 0) -> Path:
    """Erzeugt die Kaskade und gibt den geschriebenen Pfad zurueck.

    `variante` ist "panel" fuer die rechte Haelfte einer Loesungsseite oder
    "voll" fuer die randlose Abschlussseite. `farbe=None` haelt den Grund
    neutral. `seed` bleibt aus API-Gruenden stehen, entscheidet aber nichts:
    die Anordnung ist deterministisch und ohne Zufall.

    Der Pfad kann von `ziel` abweichen (gesichert wird als JPEG), deshalb ist
    der Rueckgabewert massgeblich. Meldungen holt der Aufrufer mit
    hole_hinweise() ab."""
    variante = variante if variante in GROESSEN else "panel"
    punkte = GROESSEN[variante]
    groesse = (punkte[0] * PX_JE_PUNKT, punkte[1] * PX_JE_PUNKT)
    W, H = groesse
    marke = _farbe(farbe)
    ziel = Path(ziel).with_suffix(".jpg")

    geladen: list[tuple[str, Image.Image]] = []
    for pfad in bilder or []:
        try:
            with Image.open(pfad) as im:
                im.load()
                geladen.append((Path(pfad).name, im.copy()))
        except Exception as fehler:
            hinweise.append(f"{ziel.name}: {Path(pfad).name} nicht lesbar ({fehler})")

    # Komposite zerlegen, dann Mockup-Raender beschneiden: sonst vergleicht
    # die Doublettenpruefung Karten statt Screens, und das Layout rechnet mit
    # den falschen Verhaeltnissen.
    zerlegt: list[tuple[str, Image.Image]] = []
    for name, bild in geladen:
        zerlegt.extend(_zerlegen(bild, name))
    geladen = zerlegt

    beschnitten: list[tuple[str, Image.Image]] = []
    for name, bild in geladen:
        frei, anteil = _freistellen(bild)
        if anteil < 1.0:
            hinweise.append(
                f"{ziel.name}: {name} kam als Mockup mit Rand an – auf den "
                f"Inhalt beschnitten ({anteil * 100:.0f} % der Fläche behalten). "
                "Ein Originalexport ohne Rahmen wäre besser.")
        beschnitten.append((name, frei))
    geladen = beschnitten

    behalten: list[tuple[str, Image.Image]] = []
    abdruecke: list[tuple[str, tuple]] = []
    for name, bild in geladen:
        abdruck = _fingerabdruck(bild)
        gleich = next((n for n, a in abdruecke if _doublette(a, abdruck)), None)
        if gleich:
            hinweise.append(f"{ziel.name}: {name} zeigt dieselbe Ansicht wie "
                            f"{gleich} – nur einmal aufgenommen")
            continue
        abdruecke.append((name, abdruck))
        behalten.append((name, bild))
    geladen = behalten

    if not geladen:
        hinweise.append(f"{ziel.name}: keine Screens – die Fläche bleibt leer")
        return _speichern(Image.new("RGB", groesse, _grundton(marke)), ziel)

    hoch_zahl = sum(1 for _, b in geladen if _hoch(b))
    typ = "hoch" if hoch_zahl > len(geladen) / 2 else "quer"
    grenze = MAX_KASKADE[(typ, variante)]
    if len(geladen) > grenze:
        hinweise.append(
            f"{ziel.name}: {len(geladen)} Screens übergeben, die Kaskade "
            f"„{variante}“ trägt {grenze} – die übrigen wurden weggelassen. "
            "Die Reihenfolge in der JSON entscheidet, welche stehen.")
        geladen = geladen[:grenze]

    namen = {id(bild): name for name, bild in geladen}

    # Das Gate laeuft bis zur Stabilitaet: Ein zu weicher Screen schrumpft
    # in seinem Platz (bis SCHRUMPF_MIN der Zielbreite) und behaelt seinen
    # Anschnitt; erst darunter fliegt er raus - dann wird die Kaskade mit
    # einem Screen weniger neu gelegt, weil jede Vorlage an der Zahl der
    # Screens haengt.
    uebermass = _uebermass(W, H)
    plan = None
    geschrumpft: set[int] = set()
    while geladen:
        plan, geschrumpft, meldungen, zu_weich = _plan_kaskade(
            geladen, W, H, variante, ziel.name)
        if not zu_weich:
            # Die Schrumpf-Meldungen gelten erst, wenn dieser Plan steht -
            # eine Neuplanung nach Drops legt sonst dieselbe Lage doppelt ab.
            hinweise.extend(meldungen)
            break
        for name, bild in zu_weich:
            hinweise.append(
                f"{ziel.name}: {name} ist {bild.width} px breit und damit für "
                "jede Lage der Kaskade zu weich – weggelassen. Originalexport "
                "in voller Auflösung nachliefern.")
        weich_ids = {id(bild) for _, bild in zu_weich}
        geladen = [(n, b) for n, b in geladen if id(b) not in weich_ids]
        plan = None

    if not geladen or plan is None:
        hinweise.append(
            f"{ziel.name}: alle Screens sind für die Fläche zu klein – sie "
            "bleibt reine Grundfläche. Originalexporte nachliefern, dann "
            "wird neu gerendert.")
        return _speichern(Image.new("RGB", groesse, _grundton(marke)), ziel)

    # Leicht hochgerechnete Lagen melden - geschrumpfte sind schon gemeldet.
    for bild, _, _, b, _ in plan:
        if bild.width < b * 0.98 and id(bild) not in geschrumpft:
            hinweise.append(
                f"{ziel.name}: {namen.get(id(bild), '?')} ist {bild.width} px "
                f"breit, liegt aber {b:.0f} px breit auf der Fläche – wird "
                "leicht hochgerechnet. Schärfere Originaldatei anfragen.")

    fertig, _ = _komponieren(plan, uebermass, groesse, marke)
    return _speichern(fertig, ziel)


def main() -> None:
    argumente = sys.argv[1:]
    if not argumente or "--hilfe" in argumente:
        raise SystemExit(__doc__)
    farbe = None
    ziel = Path("screens.png")
    variante = "panel"
    seed = 0
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
        elif a == "--panel":
            variante = "panel"
        else:
            dateien.append(Path(a))
        i += 1

    pfad = baue_screens(dateien, farbe, ziel, variante, seed)
    for zeile in hole_hinweise():
        print(zeile)
    print(pfad)


if __name__ == "__main__":
    main()
