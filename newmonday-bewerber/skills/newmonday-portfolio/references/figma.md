# Figma-Referenz — die Folien als bearbeitbare Frames

Neben dem PDF entstehen die Folien als Frames in einem Figma-File. Seit
Oktober 2026 sind sie **Instanzen der veröffentlichten Master-Bibliothek**
„Portfolio - CV Master“ (Seite „Components – Portfolio“): Eine Änderung im
Master erreicht per Bibliotheks-Update jede Kandidatendatei. Das ist der
Standard. Der frühere rohe Weg – Rechtecke, Texte und Vektoren aus dem Layout
nachgebaut – bleibt als Rückfall (unten, „Rückfall: der rohe Weg“).

**Vor dem ersten `use_figma`-Aufruf den Skill `figma-use` laden**; `skillNames:
"figma-use"` gehört an jeden Aufruf.

## Der Bibliotheksweg

### Was entsteht

Je Folie ein Frame 1920 × 1080 mit drei Schichten, wie in der Testbefüllung
des Masters („Test – Portfolio (Florian)“):

1. **Folie** – Instanz des Folientyps (Cover, Profil, Kundenwand, Statement,
   Trenner, Prozess-Übersicht, Prozess-Schritt, Schwerpunkt, Agentur,
   Projekt-Kopf, Projekt-Summary, Lösung, Vollbild, Kontakt)
2. **Freie Bilder** – leerer Rahmen für Screens und Collagen, die Designer
   von Hand ergänzen
3. **Chrome** – Instanz mit Wortmarke (farbig, hell, aus) und Seitenzahl
   (dunkel, hell, aus)

Befüllt wird nur über die Wege, die der Master dafür vorsieht:
Component-Properties (Texte, Schalter „… anzeigen“, Varianten wie „Art“),
exponierte verschachtelte Instanzen (Kenntnis-Zeilen, Panel-Karten,
Aufzählungspunkte, Logo-Slots, Werkzeugkacheln) und Bildfüllungen der
Bildebenen. **Keine Instanz wird gelöst.** Fettungen und Links setzt das Skript
als Bereich im Text der Instanz, das bleibt ein Override.

### Woher die Inhalte kommen

`scripts/figma_bibliothek.py` liest dasselbe HTML und dieselbe Layoutrechnung
wie das PDF. Den Folientyp sagt die Klasse der Seite (`seite--profil` → Profil,
`seite--arbeitsweise` → Prozess-Schritt mit Art „Schritt 1–3“, `seite--ki` →
Art „Werkzeuge“, `seite--abschluss` → Vollbild …), die Texte stehen in deren
Elementen – mit allem, was das Renderskript geregelt hat (Sprachvorgabe,
„3+“, Rollenzeile, Fettungen). Wortmarke und Seitenzahl kommen aus dem
Layout; nur die Prozess-Schritt-Folien folgen den festen Fotos im Master
(`chrome_fest` im Katalog). Diese Fotos gehen nicht mit, sie stehen fest in
der Komponente.

Keys, Property-Namen (mit `#`-Suffix), exponierte Instanzen, Bildebenen und
Mengengrenzen stehen in `assets/master-bibliothek.json`. Das Skript prüft jede
Property gegen diesen Katalog, bevor es etwas schreibt; im Figma-Skript sucht
es sie über den Namen vor dem `#`. Ändert sich der Master, wird der Katalog
neu gelesen (ein `use_figma` auf „Components – Portfolio“: Owner mit `key`,
`componentPropertyDefinitions`, `exposedInstances`) – die Property-Namen
selbst bleiben fest.

### Bilder

| Bildebene | Bild |
|---|---|
| Profil › Foto | Profilfoto in Graustufen, auf die Fläche beschnitten |
| Kundenwand › Logo 1–28, Kundenlogo › Logo 1–3 | Kundenlogos in Graustufen (`logo-grau-*`), SVGs als Rasterbild |
| Prozess-Schritt (Werkzeuge) › Werkzeug 1–6 | Werkzeuglogos, farbig |
| Projekt-Summary › Bild | Firmenzentrale |
| Lösung › Bild, Vollbild › Bild | die gerechnete Screenfläche aus `screens.py` |

Logo-Slots und Werkzeugkacheln sind Auto-Layouts, das Logo füllt sie. Lage und
Größe einer Ebene in einer Instanz lassen sich nicht überschreiben – das Skript
setzt deshalb den **Innenabstand des Slots**: Das Logo steht im
Seitenverhältnis seiner Datei genau dort, wo es im PDF steht.

`upload_assets` füllt nur Knoten mit einfacher ID; Ebenen in Instanzen haben
zusammengesetzte (`I12:3;45:6`). Der Start-Aufruf legt deshalb eine
**Bildablage** an – je Bild ein Trägerrechteck. Die Bilder gehen dorthin, die
Pakete übernehmen den `imageHash`, das letzte Paket entfernt die Ablage.

### Mengengrenzen

Die Komponenten tragen höchstens: 28 Kundenlogos, 10 Kenntnisse, 4 Sprachen,
4 Links, 4 Prozessschritte, 3 Texte je Prozess-Schritt (plus Untertitel), 4
Absätze auf Schwerpunkt und Summary, 4 Schwerpunkt-Karten, 6
Aufzählungspunkte, 6 KI-Werkzeuge, 3 Kundenlogos je Projekt. Was darüber
liegt, meldet `figma_plan.py` („Figma (Bibliothek): …“) – in Figma fehlt der
Rest, im PDF steht er; überzählige Absätze landen im letzten Absatz. Die
Meldung gehört in die Übergabe.

### Ablauf

**1. Bauplan schreiben** – nach dem Rendern, mit derselben `portfolio.json`:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py portfolio.json arbeit/figma/ [--knoten 12-34]
```

Es entstehen `00-start.js`, ein bis drei Pakete `NN-folien.js` (bis zu zwölf
Folien je Paket), `bilder/` und `bilder.json`.

**2. Start-Aufruf.** `00-start.js` als `code` an `use_figma`. Er importiert
zuerst eine Komponente per Key (**Vorflug**). Scheitert das, bricht er ab,
bevor etwas entsteht – dann weiter mit dem rohen Weg (unten), und in die
Übergabe: „Figma: Master-Bibliothek nicht erreichbar, Folien als rohe Frames
gebaut“. Sonst legt er Zielseite, Sammelrahmen und Bildablage an. Die Antwort
unverändert als `arbeit/figma/start.json` speichern, dann:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --einsetzen arbeit/figma/ --antwort arbeit/figma/start.json
```

Das trägt die IDs in die Pakete ein und schreibt `knoten.json`.

**3. Bilder hochladen.** Ein `upload_assets`-Aufruf: `count` = Zahl der Träger
in `knoten.json`, `nodeIds` = die Träger in dieser Reihenfolge, `scaleMode`
`FILL` (höchstens 60 je Aufruf, sonst in Blöcken). Die `submitUrl`s als
JSON-Liste nach `arbeit/figma/urls-FILL.json`, dann sofort:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --plan arbeit/figma/ --modus FILL --urls arbeit/figma/urls-FILL.json
```

**4. Folien bauen.** Jedes `NN-folien.js` der Reihe nach unverändert an
`use_figma`. Ein Paket, dessen Bild noch nicht in der Ablage liegt, bricht mit
Meldung ab – dann Schritt 3 nachholen.

**5. Kontrolle.** Ein `get_screenshot` auf den Sammelrahmen (`contentsOnly`,
`maxDimension` hoch genug) und gegen das PDF halten: Texte, Kundenwand,
Logos, Screenflächen. Dann den Link auf den Sammelrahmen für die Übergabe.

**Einzelne Folien neu bauen**: `--folien 2,5 --rahmen <Sammelrahmen>`. Der
Start-Aufruf nimmt dann den vorhandenen Sammelrahmen, jedes Paket ersetzt die
gleichnamige Folie an ihrer Stelle. Was dort von Hand geändert wurde, ist
danach weg – vorher fragen. Geplant wird intern immer das ganze Deck, damit
die Arbeitsweise-Seiten ihren Schritt behalten.

### Wenn es schiefgeht (Bibliothek)

| Symptom | Was dahintersteckt |
|---|---|
| „Bibliothek nicht erreichbar“ | Master in der Zieldatei nicht verfügbar – roher Weg |
| „Property … fehlt an …“, „Ebene … fehlt in …“ | Master geändert, Katalog veraltet – Katalog neu lesen, `figma_bibliothek.py` nachziehen |
| „Bild N ist noch nicht in der Bildablage“ | Upload fehlgeschlagen oder übersprungen |
| „This property cannot be overridden in an instance“ | Lage oder Größe einer Ebene in einer Instanz gesetzt – nur über Innenabstand oder Properties |

## Logos nie verzerren

Das Seitenverhältnis eines Logos kommt immer aus seiner Datei. Daraus folgt:

- **Rasterlogos gehen mit FIT auf ein Rechteck im Seitenverhältnis der
  Datei.** `figma_plan.py` setzt jedes eingepasste Bild selbst so
  (`im_verhaeltnis()`), verankert wie `object-position` im PDF – dann füllt
  FIT das Rechteck ohne Rand, und auch FILL schnitte nichts ab. Weicht die
  Fläche aus dem Layout mehr als 1 % von der Datei ab, meldet das Skript es
  („Figma: Bildfläche …“); bei `object-fit: fill` stünde das Bild dann schon
  im PDF verzerrt.
- **Vektorlogos werden gleichmäßig skaliert** (`rescale`), nie mit `resize`
  auf zwei Maße.
- **Im Logo-Slot** (Bibliotheksweg) bestimmt der Innenabstand des Slots die
  Fläche des Logos – im Seitenverhältnis der Datei, Füllmodus FIT.
- **FIT hilft nicht gegen eine gestauchte Datei.** Das beQ-Logo ging verzerrt
  nach Figma, obwohl dort korrekt mit FIT eingepasst war: Die Datei der
  Bibliothek war selbst gestaucht (948 × 869 statt 1018 × 547 px). Deshalb
  wird jedes Logo vor dem Rendern gegen seine Quelle angesehen (SKILL.md,
  Schritt 5) – nicht erst in Figma.
- **Von Hand in Figma**: Logos nur proportional skalieren (Shift beim
  Ziehen oder Skalieren-Werkzeug K), den Füllmodus eines Logos auf FIT lassen –
  im Modus „Crop“ zieht Figma das Bild mit, sobald die Fläche ihre Maße
  ändert.

## Kundenlogos in Graustufen

Kundenlogos stehen auf Kundenwand und Projektseiten schwarz-weiß (SKILL.md,
Schritt 5). Das Renderskript verweist im Layout auf die umgerechneten Dateien
im Zwischenspeicher (`arbeit/screens/logo-grau-*`), und `figma_plan.py` liest
dieses Layout – Figma bekommt also dieselben Dateien wie das PDF:

- **Im Bibliotheksweg** geht jedes Kundenlogo als Graustufen-Rasterbild in
  den Logo-Slot – auch SVGs, gerendert von WeasyPrint.
- **Vektorlogos** (roher Weg) tragen die Grauwerte schon als Füllung im SVG;
  der Vektorknoten in Figma hat graue Flächen, keine Filter.
- **Rasterlogos** und große SVGs, die als Bild gehen, werden als
  Graustufen-PNG hochgeladen, mit FIT auf ein Rechteck im Seitenverhältnis der
  Datei wie jedes Logo.

Figmas eigener Bildfilter („Sättigung −1“) wird bewusst nicht gesetzt: Er
liefert nur das Grau gleicher Luminanz, die Regel aus Folie 3 setzt den
Hauptton aber auf #111111 – mit dem Filter stünde Union Investment in Figma
mittelgrau und im PDF schwarz. Wer ein Logo in Figma von Hand tauscht, nimmt
die `logo-grau-*`-Datei aus dem Zwischenspeicher oder rechnet die neue Datei
mit `python3 ${CLAUDE_SKILL_DIR}/scripts/logo_grau.py <datei> --aus <ordner>`
um. Die Werkzeuglogos der KI-Folie bleiben farbig.

## Die Zieldatei

- **Link mit `node-id`** → die Frames kommen auf die Seite dieses Knotens.
- **Link ohne `node-id`** → neue Seite „Portfolio — Vorname Nachname".
- **Kein Link, „neues File" gewählt** → `create_new_file` (Skill
  `figma-create-new-file` laden). Den Plan nimmt `whoami`: der Plan mit einem
  Seat, der nicht „View" ist. Gibt es mehrere, fragen.
- **Nur `/design/`.** `/board/`, `/slides/`, `/make/`, `/proto/` gehen nicht –
  dann sagen, was gebraucht wird.

`fileKey` ist der Teil nach `/design/`, die `node-id` wird von `12-34` auf
`12:34` gedreht.

## Rückfall: der rohe Weg

Nur wenn der Vorflug scheitert: `figma_plan.py … --roh`. Die Frames entstehen dann aus dem Layout nachgebaut, ohne Bezug zum Master.

### Der Grundsatz: Figma bekommt dasselbe Layout wie das PDF

`scripts/figma_plan.py` baut das HTML mit demselben Code wie
`render_portfolio.py`, lässt WeasyPrint das Layout rechnen und liest es aus:
jede Fläche, jede Zeile, jedes Bild, mit Position, Größe, Schrift und Farbe.
Daraus schreibt es fertige `use_figma`-Skripte. Es gibt **keine zweite
Maßtabelle** – ändert sich `tokens.json` oder `portfolio.css`, ändern sich
PDF und Frames gemeinsam.

Was dabei entsteht, je Folie ein Frame 1920 × 1080 (Clip an):

| Im Layout | In Figma |
|---|---|
| Fläche mit Hintergrund (Streifen, Panel, Karte, Band) | Rechteck, Radien je Ecke |
| Rahmen rundum (Karten links auf der Profilseite) | Kontur am Rechteck, innen – die Fläche bleibt so groß wie in der Vorlage |
| Rahmen nur an einer Seite (Trennlinie zwischen zwei Kenntnissen) | flaches Rechteck in der Linienfarbe, so breit wie der Eintrag |
| Verlauf (`.bildschatten`) | Rechteck mit linearem Verlauf, oben nach unten |
| Textblock | ein Textknoten mit automatischer Breite, Zeilenhöhe in Punkt, Umbrüche wie im PDF |
| `**fett**`, Links | Bereiche mit eigenem Schnitt bzw. Hyperlink im selben Textknoten |
| SVG-Logo, Wortmarke | Vektorknoten (`createNodeFromSvg`), in seine Box eingepasst – Kundenlogos schon in Graustufen (siehe unten) |
| Rasterbild, großes SVG | Rechteck `bild:<nr>`, das Bild kommt per `upload_assets` – große SVGs rendert WeasyPrint zu PNG, derselbe Renderer wie im PDF. Logos und andere eingepasste Bilder: Rechteck im Seitenverhältnis der Datei, Füllmodus FIT |

**Die Zeilenumbrüche sind harte Umbrüche, die Textknoten haben automatische
Breite.** Die Umbrüche stehen genau dort, wo WeasyPrint umbricht, und Figma
bricht nie selbst um – mit fester Breite tat es das einmal doch, weil Figma
eine Telefonnummer einen Hauch breiter misst als WeasyPrint. Zentrierte und
rechtsbündige Texte bleiben auf ihrer Achse. Wer den Text in Figma kürzt,
setzt die Umbrüche von Hand neu.

**Große SVG-Logos gehen als Rasterbild**, gerendert von WeasyPrint: Eine
Kundenwand aus zwei Dutzend Vektorlogos sprengt sonst den Code-Deckel eines
Aufrufs. Der SVG-Leser von PyMuPDF kam dafür nicht in Frage – er zeichnete
HostEurope als schwarze Fläche und congstar ohne seine Pille.

**Farben und Schriften sind Rohwerte** aus dem gerenderten Layout – also genau
die Werte aus `tokens.json`. Es werden keine Styles, Variablen oder Komponenten
in der Zieldatei angelegt – darum ist das nur noch der Rückfall: Eine
Änderung am Master erreicht diese Frames nicht.

### Ablauf (roh)

**1. Bauplan schreiben** – nach dem Rendern, mit derselben `portfolio.json`:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py portfolio.json arbeit/figma/ --roh [--knoten 12-34]
```

`--knoten` nur, wenn der Link eine `node-id` trägt. Das Skript meldet Folien,
Textknoten, Rasterbilder und Pakete. Zu jedem Paket gehört eine Datei
`NN-folien.js` mit rund 44 000 Zeichen oder weniger – `use_figma` nimmt 50 000,
darüber warnt das Skript.

**2. Start-Aufruf.** Inhalt von `arbeit/figma/00-start.js` als `code` an
`use_figma`. Er legt die Zielseite an oder wählt sie, prüft, ob Rethink Sans
und Inter in den nötigen Schnitten verfügbar sind (sonst bricht er ab, bevor
etwas entsteht), und legt den Sammelrahmen an – ein vertikales Auto-Layout mit
300 pt Abstand, wie auf der Figma-Seite »Portfolio«. Zurück kommen `seite` und
`rahmen`.

**3. IDs einsetzen:**

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --einsetzen arbeit/figma/ --seite <seite> --rahmen <rahmen>
```

**4. Folien bauen.** Jede `NN-folien.js` der Reihe nach als `code` an
`use_figma` – eine Datei je Aufruf, unverändert. Jeder Aufruf gibt die IDs
seiner Folien zurück. Nach dem ersten Paket einmal `get_screenshot` auf eine
Folie: Stimmen Schrift und Lage, laufen die übrigen Pakete genauso.

**5. Bilder hochladen.** `99-bilder.js` als `code` an `use_figma`. Zurück kommt
je Füllmodus die Liste der Bildflächen, `{"FILL": [[knoten, nr], …], "FIT": […]}`
– `FILL` wird beschnitten wie im PDF, `FIT` eingepasst (Logos). Die Antwort
unverändert als `arbeit/figma/knoten.json` speichern. Dann je Modus **ein**
`upload_assets`-Aufruf: `count` = Zahl der Einträge, `nodeIds` = die Knoten in
genau dieser Reihenfolge, `scaleMode` `FILL` bzw. `FIT` (höchstens 60 je Aufruf;
bei mehr in Blöcken). Die zurückgegebenen `submitUrl`s in ihrer Reihenfolge als
JSON-Liste nach `arbeit/figma/urls-FILL.json` bzw. `urls-FIT.json`, dann:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --plan arbeit/figma/ --modus FILL --urls arbeit/figma/urls-FILL.json
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --plan arbeit/figma/ --modus FIT --urls arbeit/figma/urls-FIT.json
```

Das Skript ordnet über `knoten.json` und `bilder.json` jeder URL ihre Datei zu
und bricht ab, bevor es etwas hochlädt, wenn die Zahl nicht stimmt. Die URLs
verfallen nach zehn Minuten – also direkt nach `upload_assets` hochladen. Ein
Bild, das auf mehreren Folien steht (Kundenlogo auf Kopf-, Summary- und
Lösungsseite), hat eine Nummer, aber mehrere Knoten: Es wird je Knoten einmal
hochgeladen.

**6. Kontrolle.** `get_screenshot` auf zwei, drei Folien – Cover, eine
Arbeitsweise-Seite, eine Projekt-Kopfseite, falls vorhanden eine
Schwerpunkt-Folie – und gegen die PDF-Seite halten. Dazu die Kundenwand: Jedes
Logo hat dieselben Proportionen und dieselben Grauwerte wie im PDF.
Dann den Link auf den Sammelrahmen (`…?node-id=<rahmen>`) für die Übergabe.

### Einzelne Folien ersetzen (roh)

Nach einer Änderung am Skill müssen nicht alle Folien neu gebaut werden. Mit
`--folien` entstehen Pakete nur für die genannten Folien:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py portfolio.json arbeit/figma-neu/ --roh --folien 2
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --einsetzen arbeit/figma-neu/ --seite <seite> --rahmen <vorhandener Sammelrahmen>
```

Kein Start-Aufruf – die IDs sind die des vorhandenen Sammelrahmens. Jedes
Paket ersetzt die gleichnamige Folie („02") an ihrer Stelle; was Designer
**auf dieser Folie** in Figma geändert haben, ist danach weg – vorher fragen,
wenn das Deck schon in Arbeit ist. Pakete eines früheren Laufs im selben
Ordner löscht das Skript vorher, damit keines davon ungewollt Folien ersetzt.

**Kommen Schwerpunkt-Folien dazu oder fallen weg, geht das nicht.** Sie stehen
vor der Agenturseite, alle Folien dahinter rücken eine Nummer weiter – „14“
hieße im neuen Plan die Agenturseite, im alten Deck eine andere Folie. Dann
das Deck in einem neuen Sammelrahmen ganz neu bauen und den alten erst nach
Rückfrage entfernen.
`99-bilder.js` sammelt nur Bildflächen ein,
die noch den hellgrauen Platzhalter tragen, also nur die der neuen Folien;
Upload wie in Schritt 5.

### Wenn es schiefgeht (roh)

Alles hier ist Zugabe. Das PDF ist zu diesem Zeitpunkt fertig und geht so oder
so raus – mit einem Satz dazu, was an Figma nicht ging.

| Symptom | Was dahintersteckt |
|---|---|
| Werkzeug nicht vorhanden | Figma-MCP nicht verbunden |
| „you don't have edit access", 401/403 | Konto ohne Bearbeitungsrechte – `whoami` zeigt das Konto |
| „Schriften fehlen in Figma" | Rethink Sans oder Inter in der Datei nicht verfügbar; beide sind Google Fonts und in Figma normalerweise vorhanden |
| „IDs fehlen" | Schritt 3 vergessen |
| Paket über 50 000 Zeichen | sehr viele Vektorlogos auf einer Folie – `SVG_FOLIE_MAX` in `figma_plan.py` senken, dann gehen mehr als Rasterbild |
| Bildfläche bleibt hellgrau | Upload fehlgeschlagen oder Reihenfolge von `nodeIds` und URLs vertauscht |
| Logo wirkt gestaucht oder gedehnt | von Hand auf „Crop“ gestellt und die Fläche verzogen – sonst ist die Datei selbst verzerrt: gegen die Quelle prüfen, Original mit `add_logo.py` nachlegen, die Folie neu bauen |
| Upload hängt | im Browser-Chat blockt der Proxy fremde Domains |

`use_figma` ist atomar: Ein Paket, das wirft, hat nichts geschrieben. Nach
einem Fehler die Meldung lesen, reparieren, dasselbe Paket erneut senden.

## Was nicht passiert

- **Keine Styles, Variablen oder lokalen Komponenten** in der Zieldatei; im
  Bibliotheksweg nur Instanzen der Master-Bibliothek, nie gelöst.
- **Nichts umbenennen, verschieben oder löschen**, was dort schon liegt. Der
  Sammelrahmen steht rechts neben dem vorhandenen Inhalt, die eigene
  Bildablage räumt das letzte Paket weg. Einzige Ausnahme:
  Mit `--folien` ersetzt ein Paket im eigenen Sammelrahmen die gleichnamige
  Folie (siehe „Einzelne Folien in einem bestehenden Deck ersetzen“).
- **Kein Ersatz-Layout.** Reicht es nicht für die Frames, wird kein
  vereinfachtes Deck gebaut.
