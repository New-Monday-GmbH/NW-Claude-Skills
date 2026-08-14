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

## Seitenaufbau

| Seite | Inhalt |
|---|---|
| 1 | Kopfzeile (Logo, Verweise), Profilkopf (Foto, Name, Rolle), Bildung, Skillset |
| 2 ff. | Kurzprofil als eigene Rubrik, danach die Stationen mit ihren Projekten |
| letzte | Footer, am unteren Seitenrand |

Bildung und Skillset stehen auf Seite 1 und nicht mehr am Dokumentende: Sie sind
das, was ein Kunde zuerst sehen soll. Die Stationen beginnen danach auf einer
neuen Seite (`.stationen--neue-seite`), der Umbruch entfällt nur, wenn der
Lebenslauf weder Bildung noch Skillset mitbringt.

Das Kurzprofil steht deshalb **nicht** im Profilkopf, sondern auf Seite 2 über
der ersten Station. Es ist der längste Fließtext im Dokument; auf Seite 1 hätte
es rund 100pt gekostet, die Bildung und Skillset fehlen würden.

Dort bekommt es eine **eigene Rubrik** (`.section--profil`): Überschrift wie
Bildung und Skillset, Text über die volle Inhaltsbreite, Trennlinie darunter.
Ohne diese Absetzung liest es sich wie der Text der ersten Station — die
Stationen rücken auf 120pt ein, das Kurzprofil beginnt an der Blattkante.

### Die Verweise stehen in der Kopfzeile

Die Verweise (LinkedIn, Portfolio) stehen **rechtsbündig in der Kopfzeile**, auf
derselben Zeile wie die Wortmarke. Sie standen früher als Fußzeile unter Seite 1
— dort hat sie niemand gesucht.

Angezeigt wird die Adresse ohne `https://` und `www.`, verlinkt bleibt die volle.
Dass sie anklickbar sind, zeigt allein der **Unterstrich in der Markenfarbe**:
Der Text bleibt schwarz wie das übrige Dokument, eine farbige Schrift wäre im
Ausdruck ein Fremdkörper, ein grauer Unterstrich als Link nicht erkennbar. Ein
Portfolio, das nur als PDF vorliegt, hat keine Adresse und steht deshalb ohne
Unterstrich da.

Die Kopfzeile ist mit **Float** gebaut, nicht mit Flexbox: WeasyPrint (66)
rechnet die Breite eines Flex-Elements mit Text zu knapp und bricht die Verweise
untereinander um, obwohl die Zeile Platz hätte. Neben dem gefloateten Logo
laufen sie zuverlässig in einer Zeile, und sind die Adressen doch einmal zu lang,
bricht die zweite Zeile rechtsbündig unter dem Logo weiter.

Der Profilkopf belegt damit rund 200pt, für Bildung und Skillset bleiben etwa
550pt statt einer ganzen Seite. `render_cv.py` setzt die Abstände in zwei Stufen
enger (`.deckblatt--kompakt`, `.deckblatt--eng`), bevor überhaupt jemand
Einträge streicht — angefasst werden nur Abstände, nie Schriftgrößen.

### Der Footer sitzt unten, gemessen statt geraten

Der Footer schließt die letzte Seite am unteren Rand ab. CSS kann das nicht von
sich aus: Ein Flex-Anker ließe sich nicht auftrennen und zwänge den Block auf
eine eigene Seite, ein `margin-top` würfe WeasyPrint am Seitenanfang weg.
Deshalb rendert `render_cv.py` mehrfach — `text_tiefe()` liest über die
Textmatrizen des PDF, wie hoch die unterste Zeile einer Seite steht, dann
bekommt das Luftelement davor (`.fussluft`) die Differenz als Höhe.

Das Luftelement ist immer da (Grundzustand 31pt), damit Messung und
Korrektur dieselbe Ausgangslage haben. Unter der letzten Schriftlinie sitzt noch
Zeilenrest, und der Umbruch braucht Reserve — wie viel, hängt am Dokument. Darum
werden vier Zielhöhen von knapp bis gelassen probiert; was die Seite sprengt,
fällt durch.

**Eine Seite, auf der nur der Footer steht, wird vermieden.** Erkennt
`footer_allein()` diesen Fall, setzt das Skript die Abstände zwischen Stationen,
Projekten und Bullets in zwei Notstufen enger (`.stationen--kompakt`,
`.stationen--eng`), bis der Footer auf die Seite davor passt. Gemessen wird
dabei mit minimaler Fußluft (`FUSS_MIN`), sonst zeigt sich gar nicht, ob er noch
hinpasst. Erst wenn die Seitenzahl feststeht, rückt der Footer so weit nach
unten, wie sie es zulässt — reicht es nur für den Mindestabstand, ist das immer
noch besser als eine fast leere Seite.

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
| `--brand` | `#009193` | Logo und der Unterstrich der Verweise in der Kopfzeile |

## Typografie (Inter)

| Element | Größe | Schnitt | Zeilenhöhe | Laufweite |
|---|---|---|---|---|
| Name | 24pt | 800 | 1.35 | −1.08pt |
| Rolle, Erfahrung | 10pt | 400 | normal | – |
| Kurzprofil (Seite 2) | 10pt | 400 | 1.35 | −0.05pt |
| Verweise (Kopfzeile) | 8pt | 400 | normal | –, Unterstrich in `--brand` |
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
| Intro und Bildung | 32pt |
| Kurzprofil und erster Station | 32pt |
| Stationen | 32pt |
| Station und ihren Projekten | 32pt |
| Projekten | 32pt |
| Logo und Kundenname | 8pt |
| Kundenname und Zeitraum | 4pt |
| Text und Bulletliste | 8pt |
| Aufgaben-Bullets untereinander | 10pt |
| Rubriken auf Seite 1 (Bildung, Skillset) | 31pt, eng gesetzt 20pt bzw. 14pt |
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

### Eine Station bricht nicht nach dem ersten Stichpunkt um

Fängt eine Station unten auf einer Seite an und bricht gleich wieder um, steht
dort ein Jobtitel, eine Firmenzeile und ein einzelner Bullet – alles Weitere
hinter dem Seitenwechsel. Das liest sich wie zwei angefangene Stationen.
Deshalb hängen Kopf und die ersten **beiden** Stichpunkte zusammen:

```css
.station__kopf { break-inside: avoid; }                          /* Logo + Kopf */
.station--bullets .station__kopf { break-after: avoid; }         /* Kopf + Bullet 1 */
ul.tasks li:first-child:not(:last-child) { break-after: avoid; } /* Bullet 1 + 2 */
```

Passt das nicht mehr auf die Seite, rückt die ganze Station auf die nächste.
`.station--bullets` setzt `template.html` nur an Stationen mit eigenen
Aufgaben – ohne die Bedingung würde der Kopf einer Station, die direkt mit
einem Projekt beginnt, den unteilbaren Projektblock mitziehen und eine halb
leere Seite hinterlassen.

Zwei Details hängen daran:

- **Das Logo steht im selben Block wie der Kopf.** `.station__kopf` umschließt
  Rail und Kopftext, sonst bleibt der Float auf der alten Seite stehen, während
  der Text weiterrückt: gemessen das DATEV-Logo unten auf Seite 3, die Station
  dazu auf Seite 4. Der Float darf den Kopf unten überragen (kein Clearfix) –
  er läuft in der 88pt-Spalte, der Text beginnt erst bei 120pt.
- **`:not(:last-child)`.** Hat eine Station genau einen Stichpunkt, darf hinter
  ihm umbrochen werden. Ohne die Einschränkung zöge dieser eine Bullet das
  erste Projekt mit – dasselbe Problem wie oben.

Für Projekte braucht es die Regel nicht: Sie sind als Ganzes unteilbar
(`.station__body > .project { break-inside: avoid }`), dort kann kein einzelner
Bullet hängen bleiben.

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
