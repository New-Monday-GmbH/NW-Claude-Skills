# Layout-Referenz

Quelle: Figma `oezbaw261xDwxthPuX3ZpS` ("Portfolio - CV Master"), Seite "CV"
(Node `4158:3773`), Frames `4158:5572`, `4158:5505`, `4158:5386`, `4158:5092`
— Stand 2026-09-28. Die Werte stehen **nur** in `assets/tokens.json`; hier steht,
woher sie kommen und warum einige anders aussehen als in Figma eingetragen.

## Eine Quelle für alle Werte

```
assets/tokens.json  ──►  cv.css (Jinja)        ──►  PDF
                    ──►  figma_plan.py          ──►  Figma-Frames
                    ──►  selbsttest.py (Sollwerte)
```

- `cv.css` ist ein Template ohne eigene Zahlen: `css("rubrik")` setzt einen ganzen
  Textstil, `pt(a.name_rolle)` einen Abstand. Der Selbsttest schlägt an, sobald
  dort eine Zahl mit Einheit oder eine Farbe als Literal steht.
- `figma_plan.py` liest dieselben Tokens. PDF und Figma-Frame können deshalb nicht
  auseinanderlaufen.
- `selbsttest.py` misst am fertigen PDF nach: Schrift, Größe und Farbe jeder
  Textzeile und die Abstände von Schriftlinie zu Schriftlinie.

Ändert sich das Design-System in Figma: `references/figma-abgleich.md`.

## Einheiten

Die Figma-Frames sind 595 × 842 groß – das ist A4 **in Punkt**. Damit gilt
`1 Figma-px = 1pt`. Wer Figma-Werte als CSS-`px` übernimmt, baut das Dokument um
ein Viertel zu klein: 24px sind in CSS 18pt, und eine 1px-Linie ist nur 0,75pt.

## Wo Figma anders rechnet als CSS

Drei Stellen, an denen der Figma-Wert nicht 1:1 in `tokens.json` steht. Alle drei
sind nachgemessen: Seite 1 und 2 des Figma-Musters stehen im PDF auf 0,00pt genau
an derselben Stelle.

**Zeilenhöhen rundet Figma auf ganze Punkt.** 10pt × 135 % sind 13,5pt, gesetzt
werden 14pt — drei Zeilen Bildung sind in Figma 42pt hoch, nicht 40,5. Ebenso
14pt × 135 % → 19, 32pt × 112 % → 36, und „Auto" bei Inter: 10pt → 12, 8pt → 10,
7pt → 8. `tokens.json` führt deshalb die gerundeten Werte als `zeile` in pt. Als
fester Wert setzen WeasyPrint und Chrome sie gleich; ein Faktor wie 1.35 hinge an
der Engine.

**Die Skillset-Listen laufen im 13pt-Takt.** In Figma stehen sie auf 25 %
Zeilenhöhe (gerundet 3pt) plus 10pt Listenabstand. Nachgebaut liefen umbrochene
Einträge ineinander, weil deren Zeilen nur 3pt auseinander stünden. Im Skill hat
jede Zeile 13pt und die Punkte keinen Abstand — für einzeilige Einträge ist das
dasselbe Bild. Weil die Figma-Zeile aber nur 3pt hoch ist und die Glyphen 4,5pt
darüber hinausragen, verschieben sich die Kästen: Aus 16pt Titel→Liste werden
**11pt** (`gruppe_liste`), aus 20pt zwischen den Gruppen **15pt** (`gruppen`). Die
Schriftlinien stehen damit exakt wie in Figma.

**Der Footer ist breiter als der Satzspiegel.** Figma setzt ihn auf 475pt, also
von der linken bis zur gespiegelten rechten Randlinie; der Inhalt darüber hat
428pt. Ragte der Footer über den Druckbereich, verkleinerte Chrome die ganze
Seite auf rund 90 %. Deshalb ist der Druckbereich 475pt breit (rechter Rand
60pt), und Kopf, Profilkopf, Deckblatt und Stationen tragen die 428pt als Breite.

## Seitenaufbau

| Seite | Inhalt |
|---|---|
| 1 | Kopfzeile (Logo), Profilkopf (Foto, Name, Rolle, Erfahrung, Verweise), Bildung (Abschlüsse, darunter Zertifikate), Skillset |
| 2 ff. | Kurzprofil als eigene Rubrik, danach die Stationen mit ihren Projekten |
| letzte | Footer, am unteren Seitenrand |

Bildung und Skillset stehen auf Seite 1 und nicht am Dokumentende: Sie sind das,
was ein Kunde zuerst sehen soll. Die Stationen beginnen danach auf einer neuen
Seite (`.stationen--neue-seite`). Ein Skillset gibt es immer – mindestens die
Sprachen stehen darin –, der Umbruch entfällt also nie.

Das Skillset hat in jedem Lebenslauf **dieselben vier Gruppen, 2 × 2**: links
Fähigkeiten und Branchen, rechts Tools und Sprachen (Vorgabe vom 2026-09-29;
`SKILLSET_SPALTEN` in `render_cv.py`, von dort lesen auch Figma-Plan und
Selbsttest). Die Titel kommen aus dem Skript, nicht aus der `cv.json`. Die
Figma-Vorlage zeigt noch zwei weitere Gruppen („Gestaltung", „AI-gestütztes
Arbeiten") und Sprachen ohne Niveau – beides bewusst nicht übernommen, siehe
„Bewusste Abweichungen".

Das Kurzprofil steht deshalb **nicht** im Profilkopf, sondern oben auf Seite 2, als
eigene Rubrik (`.section--profil`): Überschrift wie Bildung und Skillset, Text
über die volle Inhaltsbreite, Trennlinie darunter. Ohne diese Absetzung liest es
sich wie der Text der ersten Station.

### Die Verweise stehen unter der Erfahrungszeile

LinkedIn, Xing und Portfolio stehen im Profilkopf, direkt unter der Zeile mit den
Jahren Berufserfahrung (`.intro__links`), nebeneinander, **benannt statt als
Adresse** („zum LinkedIn Profil"). Die Texte stehen als `VERWEISTEXT` in
`render_cv.py`, deutsch und englisch; verlinkt bleibt die volle Adresse.

Dass sie anklickbar sind, zeigt allein die **Linie in der Markenfarbe** unter dem
schwarzen Text. In Figma ist das keine Unterstreichung, sondern die Unterkante
des Rahmens um den Text — im CSS deshalb `border-bottom`, direkt unter der Zeile.
Ein Portfolio, das nur als PDF vorliegt, hat keine Adresse und steht ohne Linie da.

Der Abstand zwischen zwei Verweisen ist in Figma gemessen, nicht eingetragen: Der
Rahmen dort ist fest 179pt breit und verteilt die beiden Verweise mit „Space
Between" — sichtbar sind 27pt (`verweise`).

Der Profilkopf belegt rund 200pt, für Bildung und Skillset bleiben etwa 550pt.
Die Verweise kosten keinen Platz: Die Infospalte ist mit ihnen 107pt hoch, die
Fotospalte 113pt. `render_cv.py` setzt Bildung und Skillset in zwei Stufen enger
(`.deckblatt--kompakt`, `.deckblatt--eng`), bevor jemand Einträge streicht —
angefasst werden nur Abstände, nie Schriftgrößen.

### Bildung: Abschlüsse und Zertifikate

Unter „Bildung“ stehen die Abschlüsse im Zweispaltenraster (202pt, 24pt
Abstand), je Eintrag Abschluss (fett), Einrichtung, Zeitraum – **ohne
Studieninhalte** (Vorgabe vom 2026-10-03; die Liste darunter und mit ihr
`bildung_liste` sind entfallen). Darunter, `zert_abstand` tiefer, der Block
„Zertifikate“: Titel im Stil einer Skillset-Gruppe (`gruppe`, `gruppe_liste`
bis zur ersten Reihe), dann **je Zertifikat ein Tag mit dem Titel**,
nebeneinander über die volle Inhaltsbreite (428pt), umbrechend, in der
Reihenfolge der `cv.json`. Aussteller und Datum stehen nur in den Daten
(Entscheidung des Nutzers vom 2026-10-03; die drei Darstellungen davor –
`zeilen`, `spalten`, `aussteller` – sind entfallen).

Die Figma-Vorlage des Lebenslaufs kennt den Block nicht. Abgeleitet ist das Tag
aus den Themen-Tags der Skill Matrix (Innenabstand 4 × 8, Radius 6, Abstand 8,
Rand 2px `neutral/80`, Grund `neutral/10`, Schrift 14px) im Maßstab der
Schriftgrößen, 10 : 14, auf ganze Punkt gerundet – und für Papier
zurückgenommen:

| Token | Wert | abgeleitet aus |
|---|---|---|
| `text.zert_tag` | Inter Regular 10/13, Laufweite 0, `text` | Größe und 13pt-Takt von `liste`; Laufweite 0 statt −0,05, siehe unten |
| `raster.zert_tag_innen_y`, `.zert_tag_innen_x` | 3pt, 6pt | 4 × 8 der Skill Matrix |
| `raster.zert_tag_radius` | 4pt | 6 der Skill Matrix – die einzige Rundung im Lebenslauf |
| `raster.zert_tag_linie`, `farben.rahmen` | 1pt, `#9EA8AA` (`neutral/40`) | Strichstärke von `linie`; heller und dünner als der 2px-Rand in `neutral/80`, der auf Papier jedes Tag zum Kasten macht |
| `raster.zert_tag_abstand`, `.zert_tag_reihen` | 6pt, 6pt | Abstand 8 der Skill Matrix, nebeneinander wie untereinander |
| `verdichtung.deckblatt.*.zert_abstand` | 20 / 16 / 12 | `bildung_reihen` |

Einen Grund hat das Tag nicht: `neutral/10` ist auf Papier nicht vom Weiß zu
unterscheiden und gäbe dem Drucker nur eine Fläche zu rastern. Ein Tag ist
13 + 2 × 3 + 2 × 1 = 21pt hoch, eine Reihe mit Abstand 27pt. Die Abstände
zwischen den Tags verdichten nicht mit: Bei vier Reihen brächte das 3–6pt,
und dicht gedrängte Tags verlieren genau das, was sie lesbar macht.

**Kein Tag bricht in sich um.** `.zert__tags` ist eine Flex-Reihe mit
`flex-wrap` und `gap`, wie die Verweise im Profilkopf: Ein Tag, das nicht mehr
in die Reihe passt, rückt als Ganzes in die nächste. Nur ein Titel, der breiter
ist als die ganze Reihe, wird über `max-width: 100%` auf die Satzbreite begrenzt
und bricht dann in sich um – er nimmt die Reihe allein. Dafür muss WeasyPrint
die Breite des Titels richtig messen, und das tut es **nur ohne Laufweite**:
Mit −0,05pt (dem Wert von `liste`) misst WeasyPrint 66 die Breite eines Titels
zu knapp, und jedes Tag bricht sein letztes Wort in eine zweite Zeile um
(„Claude Code in / Action“) – dieselbe Schwäche, wegen der die Abschlüsse als
Floats stehen. `zert_tag` trägt deshalb Laufweite 0, wie `fliesstext` und
`aufgabe`; der Unterschied ist bei 10pt nicht zu sehen.

Was der Block auf Seite 1 kostet, steht als Richtwert in SKILL.md (Schritt 2).
Gemessen am Lebenslauf Florian Feiler (zwei Abschlüsse, acht Zertifikate in vier
Reihen): der Block vom Titel bis zur Unterkante der letzten Reihe 127pt, mit
dem Abstand zu den Abschlüssen 147pt – in der normalen Stufe, die vorher
gebrauchte kompakte ist nicht mehr nötig. Die Darstellung `zeilen` brauchte
dafür 175pt in der kompakten Stufe.

### Der Stationskopf

Wie in Figma: Titel (10pt fett), darunter die Firma (8pt), darunter der Zeitraum
als eigene Zeile (10pt). Der senkrechte Strich zwischen Zeitraum und Firma ist
entfallen. Die Aufgaben beginnen 24pt unter dem Kopf und laufen ohne
Zwischenraum, jeder Punkt eine Zeilenhöhe unter dem vorigen.

### Der Footer sitzt unten, gemessen statt geraten

Der Footer schließt die letzte Seite am unteren Rand ab — in Figma sitzt seine
letzte Zeile auf dem unteren Seitenrand. CSS kann das nicht von sich aus: Ein
Flex-Anker ließe sich nicht auftrennen und zwänge den Block auf eine eigene Seite,
ein `margin-top` würfe WeasyPrint am Seitenanfang weg. Deshalb rendert
`render_cv.py` mehrfach — `text_tiefe()` liest über die Textmatrizen des PDF, wie
hoch die unterste Zeile einer Seite steht, dann bekommt das Luftelement davor
(`.fussluft`) die Differenz als Höhe. Ziel ist die Figma-Lage (`FUSS_ZIEL`, aus den
Tokens gerechnet); weil ein Footer, der die Restseite auf den Punkt ausfüllt, auf
eine neue Seite kippt, probiert das Skript erst 0,5pt Reserve, dann mehr.

**Eine Seite, auf der nur der Footer steht, wird vermieden.** Erkennt
`footer_allein()` diesen Fall, setzt das Skript die Abstände zwischen Stationen,
Projekten und Kurzprofil in zwei Notstufen enger (`.stationen--kompakt`,
`.stationen--eng`), bis der Footer auf die Seite davor passt.

Im Footer: Logo links, die drei Spalten (je 86,67pt, 48pt Abstand) bündig an der
rechten Kante. Name des Ansprechpartners fett, Mail und Telefon als zwei Blöcke
mit 4pt Abstand — so ist es in Figma gebaut. Die Adresse lautet „New Monday
GmbH, Stresemannstr. 23, 10963 Berlin“, genau so geschrieben (Vorgabe vom
2026-10-03, `KONTAKT_VORGABE` in `render_cv.py`; der Selbsttest prüft sie).

## Bewusste Abweichungen von der Figma-Vorlage

Entschieden am 2026-09-28. Wer abgleicht, zieht diese Punkte **nicht** nach.

| Figma | Skill | Warum |
|---|---|---|
| Firmenlogos entfärbt (Sättigung −1, dunkel überlagert) | Originalfarben der Marke | Entscheidung New Monday; Regel in SKILL.md, Schritt 3 |
| Keine Schlagwortzeile im Stationskopf | `zusammenfassung` unter dem Zeitraum (10pt) | bleibt im Skill |
| Footer mit „Für weitere Informationen fordern Sie bitte das Portfolio an." | ohne diesen Hinweis | der Portfolio-Verweis steht im Profilkopf |
| Rolle „Business Developer" unter Manuel Klein | „CCO" | Vorgabe in `render_cv.py` (`KONTAKT_VORGABE`) |
| Logos von Hand platziert (links, teils breiter als 88pt, Stapelabstand 6 oder 16pt) | gleiche Fläche, rechtsbündig, max. 88pt, Stapelabstand 10pt | siehe „Logos" unten |
| Aufgaben rücken unter hohe Logos (Row-Auto-Layout) | Aufgaben 24pt unter dem Kopftext, das Logo darf daneben weiterlaufen | Figma ist hier uneinheitlich (Bayer mit 13pt statt 24pt ausgeglichen) |
| Skillset mit sechs Gruppen (u. a. „Gestaltung", „AI-gestütztes Arbeiten", „Branchenerfahrung"), Sprachen ohne Niveau | immer genau vier: Fähigkeiten, Branchen, Tools, Sprachen, 2 × 2; Deutsch – Muttersprache, Englisch – Business Niveau | Vorgabe vom 2026-09-29: jeder Lebenslauf gleich aufgebaut |
| Porträt-Platzhalter in der Vorlage nicht vorgesehen | Platzhalterbild „user-pict-placeholder" (80 × 110) in den 79 × 106pt-Fotoplatz eingesetzt | Vorgabe vom 2026-09-29; siehe „Raster" |
| Education mit Studieninhalten als Liste („sub-p“) unter jedem Abschluss | keine Studieninhalte; Abschluss, Einrichtung, Zeitraum | Vorgabe vom 2026-10-03 |
| Keine Zertifikate | eigener Block „Zertifikate“ unter den Abschlüssen, je Zertifikat ein Tag mit dem Titel – mit 4pt Radius, der einzigen Rundung im Dokument | Vorgabe vom 2026-10-03; siehe „Bildung: Abschlüsse und Zertifikate“ |

Projekte (Kunden unter einer Station) kommen im Figma-Muster nicht vor. Sie tragen
die Stile des Stationskopfs: Kunde wie ein Titel, Zeitraum wie ein Zeitraum.

## Raster

```
|<-- 88pt -->|<-- 32pt -->|<------ 308pt ------>|
   Logospalte    Abstand        Inhaltsspalte
```

Im Intro abweichend: Fotospalte 78pt, Abstand 40pt, Infospalte 308pt. Foto
79 × 106pt, Graustufen, oben 7pt eingerückt. Bildung und Skillset zweispaltig,
je 202pt mit 24pt Abstand. Zertifikats-Tags über die volle Inhaltsbreite
(428pt), 6pt auseinander, Reihen 6pt auseinander.

Die anonyme Fassung setzt an dieselbe Stelle das **Platzhalterbild aus dem
Design** (`assets/silhouette-vorlage.svg`, „user-pict-placeholder", Vorgabe vom
2026-09-29; es ersetzt die früher selbst gezeichnete Silhouette). Die Vorlage ist
80 × 110, der Fotoplatz 79 × 106pt: `scripts/silhouette.py` setzt sie ein wie ein
Foto mit `object-fit: cover` — gleichmäßig auf 79pt Breite skaliert, oben und
unten je rund 1,3pt beschnitten —, und zwar nur über die viewBox; gezeichnet wird
nichts neu. Das Ergebnis sind `silhouette.svg` (PDF und Figma) und
`silhouette.png` (für `--foto-raster`, aus demselben WeasyPrint-Rendering
gerastert). `selbsttest.py` prüft, dass beide genau das sind, was das Skript aus
Vorlage und Fotomaß heute machen würde.

## Farben, Schriften, Abstände

Alle Werte: `assets/tokens.json`. Die Farben kommen aus der Figma-Bibliothek
(`base/black`, `neutral/80`, `brand/primary`, für den Rand der
Zertifikats-Tags `neutral/40`), die Schriften sind Inter
(Regular, Bold) und **Rethink Sans SemiBold** für den Namen (Text-Style
`Headings/H6`). Inter SemiBold und ExtraBold kommen im neuen Design nicht mehr vor.

**Schatten, Rundungen und Transparenzen gibt es nicht** — weder in der Figma-Vorlage
noch im Skill. Einzige Ausnahme ist der 4pt-Radius der Zertifikats-Tags
(`.zert__tag`, Vorgabe vom 2026-10-03). Der Selbsttest schlägt an, wenn `cv.css`
eines davon an einer anderen Regel setzt.

Rethink Sans liegt als statischer SemiBold-Schnitt in `assets/fonts/`, erzeugt
aus der variablen Google-Fonts-Datei (`RethinkSans[wght].ttf`, wght 600) mit
fontTools; Lizenz in `OFL-RethinkSans.txt`.

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
Intro, Verweise, Footer und die Logoreihe eines Projekts (mit Hülle je Logo,
siehe „Projektlogos nebeneinander"). **Die Bildungsspalten stehen ebenfalls auf Floats**:
Mit negativer Laufweite rechnet WeasyPrint (66) einen Flex-Eintrag eine Zeile zu
hoch — die Trennlinie darunter stand 14pt zu tief.

Zwei Fallen, die beim Umbau aufgefallen sind:

- **Das Foto muss `display: block` sein.** Als Inline-Bild sitzt es auf einer
  Textzeile und bringt deren Unterlänge mit — alles darunter rutscht gut 3pt.
- **Gleiche Spezifität, spätere Regel gewinnt.** `.section` und `.section h2`
  (Seite 1) stehen im CSS hinter dem Kurzprofil; deshalb heißen dessen Regeln
  `.section.section--profil …`. Mit `.section--profil` allein stand das
  Kurzprofil oben auf Seite 2 zu tief.

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
| Station (Arbeitgeber) | gleiche Fläche, rechtsbündig, max. 88pt breit; mehrere **untereinander**, 10pt Abstand |
| Projekt (Kunde) | gleiche Fläche, immer 26pt, linksbündig zur Textkante, max. 88pt breit; mehrere **nebeneinander**, auf der Mitte, 16pt Abstand |
| Kopfzeile New Monday | 133.231 × 13.5pt |
| Footer New Monday | 78.95 × 8pt |

SVG bevorzugt. PNG vorher am Alphakanal zuschneiden, sonst wird das Logo durch
den mitgelieferten Weißraum zu klein dargestellt.

### Nie verzerrt

Ein Logo steht in genau dem Seitenverhältnis seiner Datei, im PDF wie im
Figma-Frame. Breite und Höhe kommen beide aus diesem einen Verhältnis
(`logo_masse()` → `masse_aus_verhaeltnis()`); auch die beiden Kappen unten
(Spaltenbreite, Hochformat) rechnen die andere Seite aus dem Verhältnis nach.

Gelesen wird es in `render_cv.py` (`svg_masse()`, `verhaeltnis_der_datei()`):
bei SVG zuerst die `viewBox`, ohne sie `width`/`height` – in jeder Reihenfolge,
mit Zahlen wie `1e3` oder `.5`, ohne Einheit oder in px/pt; `stroke-width` zählt
nicht als `width`, Prozentangaben sind kein Maß. adidas.svg (`viewBox="0 0 1e3
593.2"`) und nestle.svg (nur `height` vor `width`) sind die Prüfsteine im
Selbsttest. Rasterbilder: Pixelmaße aus dem Dateikopf.

Die Rechnung schützt nicht vor einer Datei, die selbst gestaucht ist. Dafür die
Sichtprüfung beim Aufnehmen (`add_logo.py`, Kontrollbild, SKILL.md Schritt 3) und
in Figma die Verhältnisprüfung jedes Logoknotens (`references/figma.md`).

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

| Marken je Station (Maximum) | Größe |
|---|---|
| 1 | 42pt |
| 2 | 37pt |
| 3 | 33pt |
| ab 4 | 29pt |

**Projektlogos sind immer 26pt** (`LOGO_PROJEKT_GROESSE`), egal wie viele an
einem Projekt stehen: Sie stehen nebeneinander (siehe unten), eine Reihe wird
mit jeder weiteren Marke also breiter, aber nicht höher — der Grund für die
Staffelung fällt weg. Bis 2026-09-28 standen sie untereinander und wurden ab
zwei Marken im Dokument auf 19pt verkleinert.

Die Zahl ist die Kantenlänge eines quadratischen Logos, nicht dessen Höhe im
Layout — ein flacher Schriftzug wird bei derselben Zahl breiter und niedriger.

Die beiden Ebenen bleiben getrennt: Projektlogos sind bewusst die kleinere
Stufe. Steht dieselbe Datei in beiden Ebenen, meldet `render_cv.py` das als
Prüfhinweis, statt eine der beiden Größen anzugleichen.

### Projektlogos nebeneinander

Hat ein Projekt mehrere Kunden („Opel, Peugeot, Citroën"), stehen deren Logos
**in einer Reihe** über dem Kundennamen: linksbündig an dessen Textkante, auf der
Mitte zueinander ausgerichtet, `projektlogo_reihe` (16pt) auseinander. Reicht die
308pt-Spalte nicht, bricht die Reihe um, mit demselben Abstand zwischen den
Reihen. Der Kundenname folgt `projektlogo_kunde` (8pt) unter der Unterkante der
Reihe. Design-Feedback vom 2026-09-28: gestapelt wurden die Logos höher als der
Kundenblock daneben und lasen sich wie eine Liste statt wie eine Markengruppe.

In der **Logospalte der Station** bleibt es beim Stapel: nebeneinander wären
mehrere Marken in 88pt winzig.

Eine WeasyPrint-Falle hängt daran: **Ein `<img>` direkt als Flex-Element bekommt
in WeasyPrint (66) die Breite 0** — alle Logos einer Reihe lagen im PDF
übereinander an derselben Stelle. Deshalb steckt jedes Projektlogo in einer
eigenen Hülle (`<span class="project__logo">`), und die ist das Flex-Element.
`selbsttest.py` (`pruefe_projektlogos`) misst die Reihe im fertigen PDF nach.

### Rechtsbündig in der Logospalte

Stationslogos stehen rechtsbündig in ihrer 88pt-Spalte (`margin-left: auto`),
also an der Kante zum Text. Sie sind verschieden breit; linksbündig franst die
Spalte an der Innenkante aus und der Abstand zum Stationstext springt von
Station zu Station. Rechtsbündig steht überall derselbe Abstand.

Projektlogos sind davon ausgenommen: Sie stehen nicht in der Logospalte,
sondern über dem Kundennamen, und richten sich an dessen linker Textkante aus.

`nm-logo.svg` entspricht der Komponente `nm-logo-2025` (horizontal, brand) aus
der Figma-Bibliothek: Bildmarke `#009193`, Wortmarke `#111111`, Verhältnis
133.231 × 13.5.
