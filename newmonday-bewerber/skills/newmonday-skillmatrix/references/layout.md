# Layout der Skillmatrix — Design System, Maße, Renderweg

Die Skillmatrix folgt dem New-Monday-Design-System der Figma-Masterdatei
`Portfolio - CV Master`, Seite **Skillmatrix** (Frame `4158:4223`, 1444 breit).
Alle Werte stehen **einmal**, in `assets/tokens.json`, unter den Namen der
Figma-Library. Von dort lesen:

| Abnehmer | wie |
|---|---|
| PDF | `design_system.css()` erzeugt `@font-face`, `:root`-Variablen je Komponente (`--skillkarte-padding` …) und die Textklassen `.t-<verwendung>`; `skillmatrix.css` trägt nur Struktur und `var(--…)` |
| Figma, Weg B | `figma_plan.py` baut den Knotenbaum aus denselben Einträgen |
| Figma, Weg A | braucht die Datei nicht — der Klon hängt an den Komponenten und der Library |
| Zertifikate | `zertifikate.py` rechnet aus `zertifikate`, `zertkachel`, `zertbild`, `zertbuehne`, `qualikarte`, `qualitags` und `qualitag` die Sektion vor – Karte, Bündelung, Bildgrößen, Zeilengrenzen, Höhe – für PDF und Plan gleich |
| Zuschnitt | `extract_input.py`, `zert_bilder.py`, `kopf_ausschnitt.py` und die Foto-Skripte nehmen Foto- und Kachelformat sowie die Kopflage (`kopf-oben-anteil`, `kinn-anteil`) aus `komponenten` |

**Die Regel:** Ein Wert wird nur in `tokens.json` geändert — nie im CSS, im
Template oder im Plan. Nach jedem Rendern prüft `render_skillmatrix.py` das PDF
gegen die Tokens (Seitenbreite, eingebettete Schriften, Schrift/Schnitt/Größe/
Farbe jeder Textzeile, Flächen- und Linienfarben) und endet mit Code 2, wenn
etwas abweicht. Dieselbe Prüfung einzeln:
`python3 ${CLAUDE_SKILL_DIR}/scripts/design_system.py pruefe <pdf>`.

Die Tabellen unten sind ein **Überblick zum Nachschlagen, Stand 2026-09-28**
(= `_quelle.ausgelesen` in `tokens.json`), die Zertifikatssektion Stand
2026-10-03. Maßgeblich ist immer `tokens.json`;
wer dort etwas ändert, zieht diese Tabellen im selben Zug nach (Abgleich,
Schritt 2).

## Farben

| Token | Wert | Verwendung |
|---|---|---|
| `brand/primary` | `#009193` | Kopf, Fuß, Rolle, volle Punkte, „+3“ gebündelter Zertifikate, Schwerpunkt-Rahmen, Icons, Verlauf |
| `base/black` | `#111111` | Name, Titel, Überschriften, Schwerpunkte |
| `base/white` | `#ffffff` | Hero, Karten, Tags der Qualifikationskarte, Texte im Fuß |
| `neutral/80` | `#48575a` | Hero-Beschreibung, Kartentexte, Kategorielabel und -linie, Satz, Tag-Text und Tag-Rahmen der Qualifikationskarte |
| `neutral/60` | `#738082` | Badge-Text und -Rahmen, „Aussteller · Datum" der Zertifikate |
| `neutral/40` | `#9ea8aa` | Rahmen der Skill-Karten, Zertifikatskacheln, Zertifikatsbilder, Qualifikationskarte und Fotokarte |
| `neutral/15` | `#ebf2f5` | Linie über dem Rumpf |
| `neutral/10` | `#f8fafc` | Rumpf, Badge, Bühne unter den Zertifikatsbildern, leere Punkte, Texte auf dem Verlauf |
| `Colors/Background/bg-primary_hover` | `#ebf2f5` | Grund der Fotokarte |
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

## Seitenaufbau

Eine einzige lange Seite, **1444pt breit**, Höhe nach Inhalt. Inhalt 1188 breit,
Ränder `spacing-10xl`. Von oben:

- **Kopf** 65,16 hoch, `brand/primary`, Padding 24 / 32 (`spacing-3xl` /
  `spacing-4xl`), Logo (Marke + Wortmarke, 201 × 20,16) vertikal zentriert —
  landet also bei 32 / 22,5.
- **Hero** weiß, Padding 64 / 128. Links die Textspalte (640): Badge → 32 → Name
  und Rolle (je 8 Luft darunter) → 24 → Beschreibung (8 darunter) → 32 →
  Schwerpunkte (je 52 hoch, 16 Abstand, einzeilig). Rechts die Fotokarte
  437,33 × 435,34: Rahmen 1 `neutral/40`, Radius 16, Foto 435,33 × 433,34 mit
  90 % Deckkraft (Kopf waagerecht mittig, Haaransatz bei 5 %, Kinn bei 70 %),
  unten der Verlauf mit 24 Padding, Name und Erfahrung.
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
      Zeilen, nie gekürzt) → 8 → Tags. Jedes Tag: Padding 4/8, Rahmen 2
      `neutral/80` innen, Radius 6, weiß, Text `text-xs/reg` `neutral/80`;
      33 hoch, 8 auseinander, mit 8 darüber, umbrechend. Mit einer Tag-Zeile und
      einzeiligem Satz 1 + 24 + 30 + 20 + 20 + 8 + 41 + 24 + 1 = 169 – so hoch
      wie die Komponente „Zertifikate Erklärung“ (`2284:964`), die der Nutzer
      in Florians Datei angelegt hat.
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
      Karte (169) 8 Kacheln = 62 + 169 + 32 + 2 × 259 + 24 = 805.
  - *Kernkompetenzen:* Überschrift → 24 → Kategorien, 40 auseinander. Je
    Kategorie das Label (10 Padding, Versalien, 8 Luft, Linie 1 `neutral/80`) →
    16 → Karten, drei je Zeile, 24 Abstand, Zeile gleich hoch, mindestens 108
    (Titel plus zwei Zeilen Beschreibung — so fest ist die Karte in Figma).
    Karte: Padding 16, Rahmen 1 `neutral/40`, Radius 16, `shadow-xs`; Titel und
    fünf Punkte (8, Abstand 6) → 8 → Beschreibung.
  - *Tools:* Überschrift (Tools-Icon) → 24 → höchstens sechs Karten, ohne
    Kategorielabel, im selben Raster und mit denselben Karten wie die
    Kernkompetenzen (24 Abstand, 380 breit).
- **Fuß** `brand/primary`, Padding 54 / 104: Frage (Breite 840) mit 32 Luft und
  Linie 1 weiß auf den untersten 1pt → 32 → Logo und drei Kontaktspalten, 160
  auseinander; Label → 10 → Werte (Mail und Telefon 4 auseinander).

## Bekannte Abweichungen von der Figma-Vorlage

Die Vorlage hat drei Unstimmigkeiten (Details in `figma-vorlage.md`). Das PDF
folgt dort dem System, nicht dem Fehler:

- Die Kategorielinie endet 10 vor der rechten Kante statt 61 darüber hinaus.
- Das Tools-Raster hat 24 Abstand und 380 breite Karten wie die Kernkompetenzen;
  die Vorlage zeigt dort das Master-Raster mit 16 und 385.
- Die Zertifikatssektion hat einen anderen Aufbau (Feedback 2026-10-03): Die
  Vorlage zeigt eine Karte mit Kante, Beschreibung und Chips über einem
  Bilderraster 3 × 380 × 278,05; das wurde bei vielen Zertifikaten zu lang.
  Stattdessen stehen die Zertifikate als Kacheln, darüber die
  Qualifikationskarte im Aufbau der Komponente, die der Nutzer in Florians
  Datei angelegt hat (Rahmen statt Kante und Schatten, Tags auf Weiß). Im
  Master gibt es dafür noch keine Komponente.

Die Beispielmatrix ist 3788 hoch: Sie führt die Tools nur in der Tools-Sektion
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
im CV-Skill. Das Layout ist auf WeasyPrint abgestimmt:

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
