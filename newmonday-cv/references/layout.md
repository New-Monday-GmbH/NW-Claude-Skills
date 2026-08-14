# Layout-Referenz

Quelle: Figma `KoR4rzVSoMrvQot8z33gkv`, Seite "CV" (Node `1:32`), Frames `1:420`,
`1:277`, `1:207`. Alle Werte hier sind aus dieser Datei gezogen, nicht geschätzt.

## Einheiten

Die Figma-Frames sind 595 × 842 groß – das ist A4 **in Punkt**. Damit gilt
`1 Figma-px = 1pt`. Im CSS deshalb durchgehend `pt` verwenden.

Wer die Figma-Werte als CSS-`px` übernimmt, baut das Dokument um ein Viertel zu
klein: 24px sind in CSS 18pt.

## Seite

| Wert | |
|---|---|
| Format | A4 |
| Rand oben | 60pt |
| Rand links | 60pt |
| Rand rechts | 107pt |
| Rand unten | 32pt |
| Inhaltsbreite | 428pt |

Die Figma-Datei ist an dieser Stelle nicht sauber: Seite 1 und 2 arbeiten mit
428pt Inhaltsbreite, Seite 3 mit 483pt, der Footer mit 475pt. Im Template ist
alles auf 428pt vereinheitlicht.

## Raster

```
|<-- 88pt -->|<-- 32pt -->|<------ 308pt ------>|
   Logospalte    Abstand        Inhaltsspalte
```

Im Intro abweichend: Fotospalte 78pt, Abstand 40pt, Infospalte 308pt.
Foto 79 × 106pt, Graustufen, oben 7pt eingerückt.

## Farben

| Token | Wert | Einsatz |
|---|---|---|
| `--black` | `#111111` | Text, Trennlinien |
| `--muted` | `#485758` | Aufgaben-Bullets |
| `--brand` | `#009193` | nur im Logo |

## Typografie (Inter)

| Element | Größe | Schnitt | Zeilenhöhe | Laufweite |
|---|---|---|---|---|
| Name | 24pt | 800 | 1.35 | −1.08pt |
| Rolle, Erfahrung | 10pt | 400 | normal | – |
| Kurzprofil | 10pt | 400 | 1.35 | −0.05pt |
| Jobtitel | 12pt | 700 | normal | – |
| Zeitraum, Firma | 8pt | 400 | normal | – |
| Kundenname | 10pt | 700 | 1.35 | – |
| Kundenzeitraum | 8pt | 400 | 1.35 | – |
| Fließtext | 10pt | 400 | 1.35 | – |
| Aufgaben-Bullets | 10pt | 400 | 1.35 | −0.05pt |
| Rubrik (Bildung, Skillset) | 14pt | 600 | normal | – |
| Untertitel (Fähigkeiten, Tools) | 10pt | 600 | normal | – |
| Footer-Label | 7pt | 600 | normal | 0.4pt, Versalien |
| Footer-Wert | 8pt | 400 | 1.4 | – |

Zwischen Zeitraum und Firma steht ein senkrechter Strich, 1px breit, 10pt hoch.

## Abstände

| Zwischen | |
|---|---|
| Kopfzeile und Intro | 35.5pt |
| Intro und erster Station | 32pt |
| Stationen | 32pt |
| Station und ihren Projekten | 32pt |
| Projekten | 32pt |
| Logo und Kundenname | 8pt |
| Kundenname und Zeitraum | 4pt |
| Text und Bulletliste | 8pt |
| Aufgaben-Bullets untereinander | 10pt |
| Rubriken auf der letzten Seite | 31pt |
| Untertitel und Liste | 17pt |

Bulletlisten in Bildung und Skillset stehen eng (2pt), Aufgabenlisten in den
Stationen locker (10pt). Das ist so gewollt.

## Float statt Flexbox – nicht ändern

Die Stationen sind mit `float` gebaut, nicht mit Flexbox:

```css
.station__rail { float: left; width: 88pt; }
.station__body { margin-left: 120pt; }
```

Grund: Flex-Container lassen sich im Seitenumbruch nicht auftrennen. Mit
`display: flex` springt eine lange Station als Ganzes auf die nächste Seite und
hinterlässt eine halbleere Seite davor. Mit Float bleibt das Logo am Anfang der
Station stehen und der Text läuft über den Seitenwechsel weiter.

Flexbox ist nur dort im Einsatz, wo der Block ohnehin nicht umbrechen soll:
Intro, Bildungsspalten, Skillsetspalten, Footer.

## Logos

| Ort | Maß |
|---|---|
| Station (Arbeitgeber) | gleiche Fläche, rechtsbündig, max. 88pt breit |
| Projekt (Kunde) | gleiche Fläche, linksbündig zur Textkante, max. 88pt breit |
| Kopfzeile New Monday | 133.231 × 13.5pt |
| Footer New Monday | 79pt breit |

SVG bevorzugt. PNG vorher am Alphakanal zuschneiden, sonst wird das Logo durch
den mitgelieferten Weißraum zu klein dargestellt.

### Gleiche Fläche, nicht gleiche Höhe

Logos werden **nicht** über eine gemeinsame Höhe skaliert, sondern über eine
gemeinsame Fläche. Über die Höhe gesetzt wirkt eine kompakte Bildmarke doppelt
so schwer wie ein breiter Schriftzug: 3pc (Verhältnis 1,8:1) deckte auf 58pt
Höhe 88 × 48pt, Cocomore (5,9:1) in derselben Staffel nur 88 × 15pt — dreimal
so viel Fläche für dieselbe Staffelstufe.

`render_cv.py` (`logo_masse`) liest das Seitenverhältnis aus der Datei selbst
(SVG: `viewBox`, sonst `width`/`height`; PNG/GIF/JPEG: Dateikopf) und rechnet
daraus:

```
Breite = Größe × √Verhältnis      Höhe = Größe / √Verhältnis
```

Ein Quadrat bekommt damit genau `Größe × Größe`, ein 4:1-Schriftzug dieselbe
Fläche in flacher Form. Die Maße stehen als `width`/`height` direkt am `<img>`;
im CSS steht dazu nichts mehr.

Zwei Grenzen brechen die Regel bewusst:

- **88pt Spaltenbreite.** Ein Schriftzug breiter als 4,4:1 erreicht seine
  Sollfläche nicht und wird stattdessen auf volle Spaltenbreite gesetzt. Das
  betrifft nur sehr flache Wortmarken (Cocomore, Norisbank, Pixelpark) — die
  wirken als dünne Schriftzüge ohnehin leichter als ihre Rahmenfläche.
- **Hochformat.** Höher als `Größe × 1,4` wird kein Logo, sonst schiebt sich
  die Logospalte über den Stationskopf hinaus.

### Warum die Größe dokumentweit gilt

Mehrere Marken in einer Station stehen untereinander, und je mehr es sind, desto
kleiner müssen sie gesetzt werden, damit die Logoreihe nicht länger wird als der
Text daneben. Diese Staffelung darf aber nicht pro Station gelten: Sonst steht
dieselbe Marke — Deutsche Bank etwa, einmal allein und einmal neben Postbank,
FYRST und Norisbank — an der einen Stelle doppelt so groß wie an der anderen.

Deshalb entscheidet die größte Markenzahl im ganzen Dokument über die Größe
**aller** Stationslogos. `render_cv.py` (`logo_groessen`) rechnet sie aus und
hängt die fertigen Maße an jede Station und jedes Projekt.

| Marken je Station (Maximum) | Größe | | Logos je Projekt (Maximum) | Größe |
|---|---|---|---|---|
| 1 | 42pt | | 1 | 26pt |
| 2 | 37pt | | ab 2 | 19pt |
| 3 | 33pt | | | |
| ab 4 | 29pt | | | |

Die Zahl ist die Kantenlänge eines quadratischen Logos, nicht dessen Höhe im
Layout — ein flacher Schriftzug wird bei derselben Zahl breiter und niedriger.

Die beiden Ebenen bleiben getrennt: Projektlogos sind bewusst die kleinere
Stufe. Steht dieselbe Datei in beiden Ebenen, meldet `render_cv.py` das als
Prüfhinweis, statt eine der beiden Größen anzugleichen.

### Rechtsbündig in der Logospalte

Stationslogos stehen rechtsbündig in ihrer 88pt-Spalte (`margin-left: auto`),
also an der Kante zum Text. Sie sind verschieden breit; linksbündig franst die
Spalte an der Innenkante aus und der Abstand zum Stationstext springt von
Station zu Station. Rechtsbündig steht überall derselbe Abstand (`--gap`).

Projektlogos sind davon ausgenommen: Sie stehen nicht in der Logospalte,
sondern über dem Kundennamen, und richten sich an dessen linker Textkante aus.

`nm-logo.svg` ist aus zwei Figma-Exporten zusammengesetzt (Bildmarke `#009193`,
Wortmarke `#111111`) und liegt im Verhältnis 133.231 × 13.5 vor.
