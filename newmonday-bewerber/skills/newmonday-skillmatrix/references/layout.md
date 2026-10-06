# Layout der Skillmatrix — Design System, Maße, Renderweg

Die Skillmatrix entsteht in **zwei Fassungen, immer beide**, aus derselben
`skillmatrix.json`: der langen (eine Seite, 1444 breit) und der A4-Fassung
(595 × 842, mehrseitig). Die lange folgt dem New-Monday-Design-System der
Figma-Masterdatei `Portfolio - CV Master`, Seite **Skillmatrix** (Frame
`4158:4223`); die A4-Fassung ist im Abschnitt „Die A4-Fassung“ unten hergeleitet.
Alle Werte stehen **einmal**, in `assets/tokens.json`, unter den Namen der
Figma-Library – die der A4-Fassung im Block `a4`, der Farben, Abstände und
Schriften von oben mitbenutzt (`design_system.fassung(ds, "a4")`). Von dort
lesen:

| Abnehmer | wie |
|---|---|
| PDF | `design_system.css()` erzeugt `@font-face`, `:root`-Variablen je Komponente (`--skillkarte-padding` …) und die Textklassen `.t-<verwendung>`; `skillmatrix.css` trägt nur Struktur und `var(--…)`. Für A4 dasselbe aus dem Block `a4` vor `skillmatrix-a4.css` |
| Figma, Weg B | `figma_plan.py` baut den Knotenbaum aus denselben Einträgen, für A4 je Seite einen (`figma_plan_a4.json`) |
| Figma, Weg A | braucht die Datei nicht — der Klon hängt an den Komponenten und der Library |
| Zertifikate | `zertifikate.py` rechnet aus `zertifikate`, `zertkachel`, `zertbild`, `zertbuehne`, `qualikarte`, `qualitags` und `qualitag` die Sektion vor – Karte, Bündelung, Bildgrößen, Zeilengrenzen, Höhe – für PDF und Plan gleich |
| Zuschnitt | `extract_input.py`, `zert_bilder.py`, `kopf_ausschnitt.py` und die Foto-Skripte nehmen Foto- und Kachelformat sowie die Kopflage (`kopf-oben-anteil`, `kinn-anteil`, `kopf-luft-anteil`) aus `komponenten.fotokarte` und `a4.komponenten.fotokarte` – je Fotokarte ein Zuschnitt |

**Die Regel:** Ein Wert wird nur in `tokens.json` geändert — nie im CSS, im
Template oder im Plan. Nach jedem Rendern prüft `render_skillmatrix.py` beide PDFs
gegen die Tokens ihrer Fassung (Seitenformat jeder Seite, eingebettete Schriften,
Schrift/Schnitt/Größe/Farbe jeder Textzeile, Flächen- und Linienfarben) und
endet mit Code 2, wenn etwas abweicht. Dieselbe Prüfung einzeln:
`python3 ${CLAUDE_SKILL_DIR}/scripts/design_system.py pruefe <pdf> [a4]`.

Die Tabellen unten sind ein **Überblick zum Nachschlagen, Stand 2026-09-28**
(= `_quelle.ausgelesen` in `tokens.json`), die Zertifikatssektion Stand
2026-10-03, die Bewertungspunkte Stand 2026-10-06. Maßgeblich ist immer
`tokens.json`; wer dort etwas ändert, zieht diese Tabellen im selben Zug nach
(Abgleich, Schritt 2).

## Farben

| Token | Wert | Verwendung |
|---|---|---|
| `brand/primary` | `#009193` | Kopf, Fuß, Rolle, volle Punkte, „+3“ gebündelter Zertifikate, Schwerpunkt-Rahmen, Icons, Verlauf |
| `base/black` | `#111111` | Name, Titel, Überschriften, Schwerpunkte |
| `base/white` | `#ffffff` | Hero, Karten, Tags der Qualifikationskarte, Texte im Fuß, Füllung der leeren Punkte |
| `neutral/80` | `#48575a` | Hero-Beschreibung, Kartentexte, Kategorielabel und -linie, Satz, Tag-Text und Tag-Rahmen der Qualifikationskarte |
| `neutral/60` | `#738082` | Badge-Text und -Rahmen, „Aussteller · Datum" der Zertifikate |
| `neutral/40` | `#9ea8aa` | Rahmen der Skill-Karten, Zertifikatskacheln, Zertifikatsbilder, Qualifikationskarte und Fotokarte |
| `neutral/20` | `#c9cfd1` | derzeit ohne Verwendung (Variable aus „Foundation – Colors“); bis 2026-10-06 die Füllung der leeren Punkte |
| `neutral/15` | `#ebf2f5` | Linie über dem Rumpf |
| `neutral/10` | `#f8fafc` | Rumpf, Badge, Bühne unter den Zertifikatsbildern, Texte auf dem Verlauf |
| `Colors/Background/bg-primary_hover` | `#ebf2f5` | Grund der Fotokarte |
| `roh/punkt-rahmen` | `#6b7b7e` | Ring der leeren Punkte, Rahmen 1,5 innen – beide Fassungen. Rohwert ohne Figma-Variable, vom Nutzer am 2026-10-06 in Florians Datei gesetzt (`KoR4rzVSoMrvQot8z33gkv`, Frames `2384:48`, `2384:582`, `2384:737`); liegt zwischen `neutral/80` und `neutral/60` |
| `#22c55e` (ohne Token) | | Punkt im Verfügbarkeits-Badge |

## Abstände, Radien, Schatten

Abstände sind die Stufen `spacing-xs` 4 · `sm` 6 · `md` 8 · `lg` 12 · `xl` 16 ·
`2xl` 20 · `3xl` 24 · `4xl` 32 · `5xl` 40 · `7xl` 64 · `10xl` 128 · `11xl` 160,
dazu `spacer/--space-64-32` 64 (Padding unten im Rumpf).
Radien: `radius-2xl` 16 (Qualifikationskarte), `radius-full` 9999; roh in der
Vorlage: 16 (Karten, Fotokarte), 6 (Schwerpunkte, Tags), 4 (Punkte); roh als
Ergänzung des Skills: 8 (Bühne der Zertifikatsbilder), 4 (Zertifikatsbild).

| Schatten | Ebenen (x, y, Blur, Spread, Farbe) | an |
|---|---|---|
| `Shadows/shadow-xs` | 0, 1, 2, 0, Schwarz 5 % | Skill-Karten, Zertifikatskacheln |

Die Qualifikationskarte hat keinen Schatten, nur den Rahmen.

## Schrift

**Rethink Sans** für Name und Rolle, **Inter** für alles andere. Die Schnitte
liegen in `assets/fonts/` (Google Fonts, OFL) und werden eingebettet: Inter
Regular, Medium, SemiBold, Bold; Rethink Sans SemiBold. Fehlt eine Datei, bricht
das Rendern ab — ohne sie setzte jede Engine still eine Ersatzschrift.

| Textstil | Schrift | Größe / Zeile | Laufweite | Verwendung |
|---|---|---|---|---|
| `Display/display-lg/bold` | Rethink Sans 600 | 60 / 110 % | −0,3 % | Name, Rolle |
| `Body/text-lg/bold` | Inter 600 | 24 / 125 % | 0 | Sektionsüberschriften; „+3“ gebündelter Zertifikate (`brand/primary`) |
| `Body/text-md/bold` | Inter 600 | 20 / 150 % | 0 | „Erworbene Qualifikationen“ |
| `Body/text-md/reg` | Inter 400 | 20 / 150 % | 0 | Hero-Beschreibung |
| `Body/text-sm/bold` | Inter 600 | 16 / 150 % | 0 | Schwerpunkte, Kartentitel, Zertifikatstitel |
| `Body/text-xs/reg` | Inter 400 | 14 / 150 % | 0,5 | Badge, „Aussteller · Jahr", Kartentexte, Tags, Kontaktwerte |
| `Body/text-xs/med-AG` | Inter 500 | 14 / 150 % | 0,5 | Kategorielabel, Kontaktlabel (Versalien) |
| roh | Inter 700 | 20 / 28 | 0 | Name auf der Fotokarte |
| roh | Inter 500 | 14 / 20 | 0 | Erfahrung auf der Fotokarte |
| roh | Inter 400 | 14 / 20 | 0 | Satz der Qualifikationskarte |
| roh | Inter 600 | 30 / 36 | 0 | Fußfrage |

„roh" heißt: Die Vorlage setzt dort keinen Text-Style. In `tokens.json` stehen
diese Stile unter `roh/…`, damit auch sie nur an einer Stelle stehen.

## Seitenaufbau (lange Fassung)

Eine einzige lange Seite, **1444pt breit**, Höhe nach Inhalt. Inhalt 1188 breit,
Ränder `spacing-10xl`. Von oben:

- **Kopf** 65,16 hoch, `brand/primary`, Padding 24 / 32 (`spacing-3xl` /
  `spacing-4xl`), Logo (Marke + Wortmarke, 201 × 20,16) vertikal zentriert —
  landet also bei 32 / 22,5.
- **Hero** weiß, Padding 64 / 128. Links die Textspalte (640): Badge → 32 → Name
  und Rolle (je 8 Luft darunter) → 24 → Beschreibung (8 darunter) → 32 →
  Schwerpunkte (je 52 hoch, 16 Abstand, einzeilig). Rechts die Fotokarte
  437,33 × 435,34: Rahmen 1 `neutral/40`, Radius 16, Foto 435,33 × 433,34 mit
  90 % Deckkraft (Kopf waagerecht mittig, Haaransatz bei 5 %, Kinn bei 70 %,
  mindestens 5 % Luft über dem Scheitel), unten der Verlauf mit 24 Padding,
  Name und Erfahrung.
- **Rumpf** `neutral/10`, oben 1pt Linie `neutral/15`, Padding oben 64, unten 64
  (`spacer/--space-64-32`), Sektionen 64 auseinander. Der Rumpf reicht bis an
  den Fuß — kein weißer Streifen dazwischen.
  - *Zertifikate:* Überschrift (Icon 24, 12 Abstand; 30 hoch) → 32 →
    Qualifikationskarte (falls belegt) → 32 → Kacheln. Die ganze Sektion ist
    **höchstens 924 hoch** (`zertifikate.max-hoehe`), die Karte eingerechnet;
    darüber bündelt `zertifikate.py` (SKILL.md, Schritt 3).
    - **Qualifikationskarte** volle Breite 1188, Rahmen 1 `neutral/40` innen,
      Radius 16, weiß, kein Schatten, Padding 24: „Erworbene Qualifikationen“
      (`text-md/bold`) → 20 → Satz (14/20 roh, `neutral/80`, höchstens zwei
      Zeilen, nie gekürzt) → 8 → Tags. Jedes Tag: Padding 4/8, Rahmen 1
      `neutral/80` innen, Radius 6, weiß, Text `text-xs/reg` `neutral/80`;
      31 hoch, 8 auseinander, mit 8 darüber, umbrechend. Mit einer Tag-Zeile und
      einzeiligem Satz 1 + 24 + 30 + 20 + 20 + 8 + 39 + 24 + 1 = 167 – so hoch
      wie die Komponente „Zertifikate Erklärung“ (`2284:964`), die der Nutzer
      in Florians Datei angelegt und am 05.10.2026 auf 1er-Rahmen gesetzt hat.
    - **Kacheln**: vier zu 279, 24 auseinander, wie die Skill Card (Padding 16,
      Rahmen 1 `neutral/40`, Radius 16, `shadow-xs`). Bühne 245 × 140
      (`neutral/10`, Radius 8, Padding 12) mit dem Bild mittig, eingepasst –
      Seitenverhältnis der Datei, nie beschnitten, nie verzerrt –, Rahmen 1
      `neutral/40`, Radius 4. Ohne Bild steht ein weißes Feld im Kachelformat
      41 : 30 mit dem Zertifikats-Icon, bei gebündelten Einträgen mit „+3“.
      → 12 → Textfeld 73: Titel (`text-sm/bold`, endet nach zwei Zeilen mit
      Auslassungszeichen) → 4 → „Aussteller · Jahr“; zusammen höchstens drei
      Zeilen, sonst zeigt der Aussteller seine Kurzform. Kachel 259, Reihen 24
      auseinander. Ohne Karte 12 Kacheln = 62 + 3 × 259 + 2 × 24 = 887, mit
      Karte (167) 8 Kacheln = 62 + 167 + 32 + 2 × 259 + 24 = 803.
  - *Kernkompetenzen:* Überschrift → 24 → Kategorien, 40 auseinander. Je
    Kategorie das Label (10 Padding, Versalien, 8 Luft, Linie 1 `neutral/80`) →
    16 → Karten, drei je Zeile, 24 Abstand, Zeile gleich hoch, mindestens 108
    (Titel plus zwei Zeilen Beschreibung — so fest ist die Karte in Figma).
    Karte: Padding 16, Rahmen 1 `neutral/40`, Radius 16, `shadow-xs`; Titel und
    fünf Punkte (8 × 8, Radius 4, Abstand 6) → 8 → Beschreibung. Volle Punkte
    `brand/primary`, leere als **Ring**: weiß, Rahmen 1,5 innen
    `roh/punkt-rahmen`, gleich groß und gleich rund – so hat der Nutzer sie am
    2026-10-06 in Florians Datei gesetzt (`2384:48`). Die Reihe behält ihren
    Takt; erreicht und offen unterscheidet nur die Füllung. Der Rahmen liegt
    innen: im PDF `border` bei `box-sizing: border-box`, in Figma
    `strokeAlign = "INSIDE"`.
  - *Tools:* Überschrift (Tools-Icon) → 24 → höchstens sechs Karten, ohne
    Kategorielabel, im selben Raster und mit denselben Karten wie die
    Kernkompetenzen (24 Abstand, 380 breit).
- **Fuß** `brand/primary`, Padding 54 / 104: Frage (Breite 840) mit 32 Luft und
  Linie 1 weiß auf den untersten 1pt → 32 → Logo und drei Kontaktspalten, 160
  auseinander; Label → 10 → Werte (Mail und Telefon 4 auseinander).

## Die A4-Fassung

Vorlage ist der vom Nutzer am 2026-10-06 abgenommene Vorschlag in Florians
Datei (`KoR4rzVSoMrvQot8z33gkv`, Seite „Skillmatrix“, Frames `2347:48`,
`2348:48`, `2349:48`). Rand, Kopfzeile und Fuß kommen aus dem Lebenslauf
(`newmonday-cv/assets/tokens.json`), damit Lebenslauf und Skill Matrix im Set
gleich aussehen. Die Werte stehen in `tokens.json` unter `a4`.

**Warum diese Maße.** A4 hoch in Punkt ist 595 × 842 (1 Figma-px = 1pt, wie im
Lebenslauf). Der Satzspiegel des Lebenslaufs – oben 60, links 60, rechts 107,
unten 32 – lässt **428** Breite. Darin teilt sich alles ohne Rest: zwei Spalten
zu **202** mit **24** Fuge (202 + 24 + 202), vier Kacheln zu **95** mit 16 Fuge
(4 × 95 + 3 × 16), Textspalte und Fotokarte im Hero 296 + 24 + 108. Die
Schriftgrade folgen dem Lebenslauf: **10pt Fließtext** (14pt Zeile), Name 32/36
Rethink Sans, Rubriken 14/19, Labels 8/10. Was in der langen Fassung eine Karte
mit Schatten ist, ist hier eine Zeile mit Haarlinie – Schatten und viele Karten
vertragen sich nicht mit Papier und 10pt.

| Element | Maß | Herkunft |
|---|---|---|
| Seite | 595 × 842, Rand 60 / 107 / 32 / 60, Inhalt 428 | Lebenslauf `seite` |
| Kopfzeile | auf jeder Seite: Logo `nm-logo.svg` 133,231 × 13,5 links bei 60 / 60; auf Seite 1 rechts das Badge | Lebenslauf `kopflogo_*` |
| Badge | Padding 4 / 8, Punkt 6, Abstand 6, Rahmen 1 `neutral/60`, Grund `neutral/10`, Text 8/10 Versalien, Laufweite 0,3, `neutral/60`; 20 hoch, senkrecht mittig in der Kopfzeile | Badge der langen Fassung, verkleinert |
| Inhalt beginnt | 60 + 13,5 + 35,5 = **109** | Lebenslauf `kopf_intro` |
| Blöcke | 32 auseinander (Hero, Zertifikate, Kernkompetenzen, Tools) | `spacing-4xl` |
| Hero | Name 32/36 → 8 → Rolle Inter 10/12 `base/black` (klein wie im Lebenslauf) → 16 → Schwerpunkte; rechts die Fotokarte; darunter 12 → Beschreibung 10/14 `neutral/80` über 428 | Vorschlag, Name und Rolle aus dem Lebenslauf |
| Schwerpunkte | Padding 5 / 8, Rahmen 1,5 `brand/primary`, Radius 4, Text 10/14 fett; 27 hoch, 6 auseinander, brechen um | Vorschlag |
| Fotokarte | 108 × 99 (= Höhe der Textspalte: 36 + 8 + 12 + 16 + 27), Radius 8, Rahmen 1 `neutral/40` obenauf, Grund `bg-primary_hover`, Foto 90 %, **kein Verlauf, kein Name** | Vorschlag |
| Sektionstitel | Icon 14, 6 Abstand, Inter 14/19 fett, Laufweite −0,07; 16 bis zum Inhalt | Lebenslauf `rubrik` |
| Qualifikationskarte | die **einzige Karte mit Rahmen**: Padding 14, Rahmen 1 `neutral/40`, Radius 8; Titel 10/14 fett → 8 → Satz 10/14 `neutral/80` → 8 → Tags; 16 bis zu den Kacheln | Vorschlag |
| Tags | Padding 3 / 6, Rahmen 1 `neutral/40`, Radius 4, ohne Grund, Text 10/13; 21 hoch, 6 auseinander | Lebenslauf `zert_tag` |
| Kacheln | **ohne Rahmen**, vier zu 95, 16 Fuge, Reihen 20 auseinander, huggen ihren Text; Bühne 95 × 68 (Padding 6, `neutral/10`, Radius 4), Bild eingepasst mit Rahmen 1, Radius 2; 6 → Titel 10/14 fett → 2 → „Aussteller · Jahr“ 8/10 `neutral/60`. Dieselben Kacheln wie in der langen Fassung (Reihenfolge, Bündel, Kurzform des Ausstellers) | Vorschlag |
| Kategorie | Label 8/10 Medium, Versalien, Laufweite 0,3, `neutral/80`, bündig links; 6 Luft, Linie 1 `neutral/80` über 428 – zusammen 17; Kategorien 16 auseinander | Vorschlag |
| Einträge (Kernkompetenzen und Tools) | **Zeilen ohne Karten**, zwei Spalten zu 202, 24 Fuge; je Eintrag 7 Luft, Titel 10/14 fett und fünf Punkte (6, Radius 3, 4 Abstand, 4 von oben; leere als Ring wie in der langen Fassung, Rahmen 1,5 innen `roh/punkt-rahmen`), 2, Beschreibung 10/14 `neutral/80`, 7 Luft; Einträge einer Zeile gleich hoch; ab der zweiten Zeile oben eine **Haarlinie 0,5 `neutral/40`** (innen, zählt mit) | Vorschlag; Ringe aus `2384:582`, `2384:737` (2026-10-06) |
| Tools | ohne Label: Überschrift → 16 → Linie 1 `neutral/80` → Zeilen | Vorschlag |
| Fuß | nur auf der letzten Seite, Unterkante bei 842 − 32 = **810**: 475 breit, Linie 1 `base/black`, 16 → Logo 78,95 × 8 links, drei Spalten zu 86,67 mit 48 Abstand rechts; Label 7/8 fett Versalien → 10 → Werte 8/10, Mail und Telefon 4 auseinander; Ansprechpartner, Kontakt und „New Monday GmbH, Stresemannstr. 23, 10963 Berlin“ wie im Lebenslauf | Lebenslauf `fuss_*` |

Nachgemessen an Florians Daten: Name 109, Zertifikate 294, Kacheln 481 (Reihen
128 und 142), Kategorien auf Seite 2 bei 144 / 394 / 602 (234, 192, 192 hoch),
Tools auf Seite 3 bei 424, Fuß 745–810 – auf den Punkt wie im Vorschlag.

**Seitenumbruch.** Kein Block bricht in sich um: Kategorie, Tools,
Qualifikationskarte und jede Kachelreihe stehen ganz auf einer Seite
(`break-inside: avoid`), eine Überschrift bleibt bei dem, was ihr folgt
(`break-after: avoid`). Folgt eine Kategorie auf einer neuen Seite, steht sie
oben ohne Wiederholung der Überschrift; der Abstand davor fällt am
Seitenanfang weg. Weil die Reihenfolge feststeht, ist das Füllen Seite für Seite
schon die kleinste Seitenzahl.

**Der Fuß sitzt unten**, wie im Lebenslauf: Vor ihm steht eine Luft
(`.fussluft`), im ersten Durchgang 32 (`fuss.abstand-min`); dann misst das
Renderskript im Layout, wo der Fuß endet, und setzt die Luft so, dass er bei 810
aufsitzt. Passt der Fuß nicht mehr auf die letzte Inhaltsseite, rückt er mit
seiner Luft auf eine eigene – das meldet das Skript. In Figma füllt der Inhalt
der letzten Seite die Höhe (FILL), der Fuß steht darunter am Rand.

**Die Kopfzeile läuft mit.** Sie steht im Template zweimal, als laufende
Elemente (`position: running(kopferste)` mit Badge, `running(kopf)` ohne), und
`@page` setzt sie in den oberen Rand – `:first` mit Badge, alle weiteren nur mit
Logo. Der obere Rand ist deshalb 109, die Kopfzeile sitzt mit `padding-top` 60
darin. Das kann nur WeasyPrint; ohne WeasyPrint entsteht die A4-Fassung nicht.

**Die Seitenaufteilung steht im PDF.** Jeder Block trägt im Template ein
`data-block`; das Renderskript liest aus dem Layout, auf welcher Seite er
steht, und legt das in der Dokumentinfo des A4-PDFs ab (`/NewMondaySeiten`,
etwa `{"seiten": 3, "bloecke": {"hero": 1, "kategorie-4": 3, "fuss": 3}}`).
`figma_plan.py` baut die Seiten daraus und hält die Kategorielabels gegen den
Seitentext – wie der Lebenslauf liest es die Aufteilung aus dem PDF, statt sie
zu raten.

**Bewusste Abweichungen vom Vorschlag:** Die Tools stehen in der Reihenfolge
der JSON (im Vorschlag waren ChatGPT und Lighthouse vertauscht), der Fuß sitzt
in Figma per FILL des Inhalts unten statt über einen festen Abstandsrahmen, die
Kachelreihen haben in Figma feste Kachelbreiten (95) statt FILL, und das Foto ist
eigens für 108 : 99 geschnitten, mit Luft über dem Haar (im Vorschlag war der
lange Zuschnitt eingesetzt und die Haare oben angeschnitten).

## Der Fotozuschnitt je Fotokarte

Beide Fotokarten haben ein eigenes Seitenverhältnis (lang 435,33 : 433,34, A4
108 : 99). Ein Zuschnitt für beide hieße: In der breiteren A4-Karte schneidet
`object-fit: cover` oben und unten weg – genau so waren im Vorschlag die Haare
angeschnitten. Deshalb schneidet `kopf_ausschnitt.py` je Karte eigens, aus dem
Original (`foto-<name>.png`, `foto-<name>-a4.png`):

| Token (`fotokarte`) | lang | A4 | Bedeutung |
|---|---|---|---|
| `kopf-oben-anteil` | 0,05 | 0,10 | Ziel: Scheitel bei diesem Anteil der Bildhöhe |
| `kinn-anteil` | 0,70 | 0,82 | Ziel: Kinn |
| `kopf-luft-anteil` | 0,05 | 0,08 | **Mindestluft über dem Scheitel** – darüber wird nie geschnitten |
| Kinngrenze | Beginn des Verlaufs (0,78, gerechnet) | `kinn-max-anteil` 0,92 | tiefer darf das Kinn nicht |

Reicht das Original nicht, in dieser Reihenfolge: größer schneiden (mehr
Schultern, notfalls nicht ganz mittig), dann oben Hintergrund ergänzen – nur bei
einfarbigem oberem Bildrand (Streuung bis 3 Grauwerte, sonst sähe man die Naht)
–, sonst melden. Die Luft geht dabei dem Kinn vor. Die A4-Karte verträgt einen
größeren Kopf als die lange (Ziel 72 % statt 65 % der Höhe): Sie ist klein, und
kein Verlauf deckt das Kinn. Geprüft an Florians Foto, das oben wenig Rand hat
(Scheitel 55 px unter der Bildkante): lang Scheitel 5 %, Kinn 77 %; A4 Scheitel
8 %, Kinn 86 % – ohne Ergänzung, der Kopf ganz im Bild. Mit 10 % Mindestluft
hätte das Skript oben 13 px Hintergrund ergänzt.

## Bekannte Abweichungen von der Figma-Vorlage

Die Vorlage hat drei Unstimmigkeiten (Details in `figma-vorlage.md`) und ist
bei den Punkten älter als der Skill. Das PDF folgt dort dem System, nicht dem
Fehler:

- Die Kategorielinie endet 10 vor der rechten Kante statt 61 darüber hinaus.
- Leere Punkte sind Ringe (2026-10-06). Die Komponente `Dots` im Master füllt
  sie noch flächig (`neutral/10`, Stand 2026-09-28) – Weg A übernimmt das, bis
  die Komponente nachgezogen ist.
- Das Tools-Raster hat 24 Abstand und 380 breite Karten wie die Kernkompetenzen;
  die Vorlage zeigt dort das Master-Raster mit 16 und 385.
- Die Zertifikatssektion hat einen anderen Aufbau (Feedback 2026-10-03): Die
  Vorlage zeigt eine Karte mit Kante, Beschreibung und Chips über einem
  Bilderraster 3 × 380 × 278,05; das wurde bei vielen Zertifikaten zu lang.
  Stattdessen stehen die Zertifikate als Kacheln, darüber die
  Qualifikationskarte im Aufbau der Komponente, die der Nutzer in Florians
  Datei angelegt hat (Rahmen statt Kante und Schatten, Tags auf Weiß). Im
  Master gibt es dafür noch keine Komponente.

Die Beispielmatrix ist 3786 hoch: Sie führt die Tools nur in der Tools-Sektion
(SKILL.md, Schritt 3), ihre Kategorien folgen dem Katalog – fünf statt vier, mit
19 Karten –, und die acht Zertifikate stehen als zwei Kachelreihen unter der
Qualifikationskarte statt in Karte und Raster.

Dazu kommen Ergänzungen, für die es in Figma kein Gegenstück gibt. Bei den
Vorlagentexten sieht man keinen Unterschied, sie greifen erst bei langen Texten:

- Kartentitel halten 12 Abstand zu den Punkten und brechen um
  (`titel-abstand-min` als Rohwert). In Figma stehen sie per SPACE_BETWEEN ohne
  Mindestabstand und laufen über.
- Name und Rolle im Hero brechen innerhalb der 640er Spalte um; in Figma laufen
  sie in die Fotokarte.
- Name und Erfahrung auf der Fotokarte haben 389,33 Breite (Karte − 2 × 24). In
  der Vorlage sind die Textrahmen fest 385,34 breit und der Verlauf 437 statt
  437,33 — lange Namen brechen dort etwa 4pt früher um.

## Abgleich mit Figma — wenn sich das Design System ändert

1. Die verwendeten Variablen und Styles aus der Masterdatei lesen:
   `get_variable_defs` auf `4158:4223` liefert Farben, Abstände, Radien, Schatten
   und Textstile mit Namen. Maße, Konturen und Rohwerte je Element liefert ein
   lesender `use_figma`-Aufruf über den Frame (Layout, Padding, Abstand,
   Füllungen samt gebundener Variable, Konturen je Seite, Radius, Effekte,
   Textsegmente samt Style).
2. `assets/tokens.json` nachziehen — Werte unter den Figma-Namen; in `komponenten`
   einen Namen, wo Figma eine Variable bindet, eine Zahl, wo Figma roh ist.
   `_quelle.ausgelesen` auf das Datum setzen. Im selben Zug die Tabellen und den
   Seitenaufbau in dieser Datei nachziehen, samt Datum.
3. Haben sich Logo oder Icons geändert: als SVG exportieren
   (`exportAsync({ format: "SVG_STRING", svgOutlineText: true })`) und
   `assets/nm-logo-weiss.svg`, `icon-zertifikat.svg`, `icon-kernkompetenzen.svg`,
   `icon-tools.svg`
   ersetzen. Exporte auf `NaN` in Pfaden prüfen — Figma schreibt sie gelegentlich.
4. Neue Schriftschnitte in `assets/fonts/` legen und unter `schriften` und
   `figma_schnitte` eintragen.
5. Die Beispielmatrix rendern (`INSTALL.md`, Selbsttest): Die Designprüfung muss
   durchlaufen, und das Ergebnis wird neben einen `get_screenshot` des Frames
   gelegt.
6. Ändert sich nicht nur ein Wert, sondern der Aufbau (neues Element, andere
   Verschachtelung), ziehen `template.html`, `skillmatrix.css` und
   `figma_plan.py` gemeinsam nach — und `references/figma-vorlage.md`, falls sich
   Knoten-IDs oder Layer der Vorlage geändert haben.

## Renderweg

WeasyPrint zuerst, sonst headless Chrome, sonst wkhtmltopdf — dieselbe Kette wie
im CV-Skill; der Ausweichweg gilt nur für die lange Fassung (die A4-Fassung
braucht laufende Elemente und die Layoutmessung, siehe oben). Das Layout ist auf
WeasyPrint abgestimmt:

- **Kein box-shadow.** WeasyPrint kennt die Eigenschaft nicht und ignoriert sie
  wortlos. `render_skillmatrix.py` vermisst deshalb im ersten Durchgang jede
  Karte mit `data-schatten`, zeichnet ihren Schatten mit den Werten aus
  `tokens.json` als Bild (Gauß-Blur wie box-shadow) und legt es im zweiten
  Durchgang dahinter. Chrome zeichnet `box-shadow` selbst; dafür steht es
  zusätzlich im CSS.
- **Höhe aus dem Layout.** Die Seitenhöhe ist die Unterkante des gelayouteten
  Inhalts. Nur auf dem Ausweichweg wird sie am Bild gemessen (letzte nicht weiße
  Pixelzeile) — deshalb darf `html`/`body` weiterhin keinen Hintergrund haben.
- **Kein CSS-Grid.** Kartenzeilen sind Flex-Zeilen mit festen Breiten, die das
  Template selbst in Dreiergruppen schneidet; `align-items: stretch` macht die
  Karten einer Zeile gleich hoch.
- **Kein `filter`.** Das Foto kommt bereits in Graustufen aus `extract_input.py`.
- **`var()` geht überall**, auch in Kurzschreibweisen (`padding`, `border`).
- **`line-clamp` geht** (WeasyPrint ab 54): Zertifikatstitel und „Aussteller ·
  Jahr“ enden nach der geplanten Zeilenzahl mit „…“. In Figma ist das
  `textTruncation = "ENDING"` mit `maxLines`.
- **Umbrechende Tags mit Rand statt `gap`:** Jedes Tag trägt 8 oben und rechts
  als `margin`, die Reihe ist `flex-wrap: wrap`. So hat jede Zeile denselben
  Abstand darüber wie die erste zum Satz. Das letzte Tag einer Zeile braucht
  dadurch 8 mehr Platz als in Figma – PDF und Plan brechen höchstens früher um,
  nie später.
- **Bilder in Flex-Zeilen mit `margin: auto` zentrieren.** WeasyPrint richtet
  ein `<img>` nicht nach `justify-content` aus; Zertifikatsbilder und das Icon
  im Platzhalterfeld säßen sonst links.
- **Konturen innen:** In Figma zählen Konturen im Layout mit — im CSS sind das
  `border` plus `padding` bei `box-sizing: border-box`. Die Linie unter der
  Fußfrage zählt in Figma nicht mit und ist deshalb ein `::after`.
