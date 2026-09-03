---
name: newmonday-skillmatrix
description: Erstellt aus Lebenslauf, Portfolio und LinkedIn-Export eine Skill Matrix im New-Monday-Layout als PDF – eine einseitige, weblayoutartige Kompetenzübersicht mit Hero (Name, Rolle, Verfügbarkeit, Foto), Zertifikaten und nach Kategorien gruppierten Kernkompetenzen mit 1–5-Punkte-Bewertung. Nutze diesen Skill immer, wenn eine Skill Matrix, Skillmatrix, Kompetenzmatrix, Kompetenzübersicht oder ein Skill-Profil erstellt, aufbereitet, vereinheitlicht oder "ins New Monday Layout gebracht" werden soll – auch wenn nur "Skill Matrix für <Name>" mit ein paar PDFs geschickt wird und das Wort "New Monday" gar nicht fällt. Gilt auch, wenn die Skill Matrix zusätzlich in ein Figma-File, als Figma-Frame oder als bearbeitbare Datei für Designer abgelegt werden soll. Für Lebensläufe ist newmonday-cv zuständig, für Portfolios newmonday-portfolio; die Skillmatrix ist das dritte Dokument im Set.
---

# New Monday Skillmatrix

> **Version 2, noch nicht aktiv.** Diese Datei ersetzt `SKILL.md` erst, wenn sie
> umbenannt wird — Claude Code lädt ausschließlich `SKILL.md`. Neu gegenüber
> Version 1 ist Schritt 4a: Er kennt jetzt zwei Figma-Wege und wählt in der
> New-Monday-Masterdatei den Weg über die Vorlage statt des gezeichneten
> Nachbaus. Das ist die Antwort auf erfundene Grafiken und auf Layouts, die vom
> Original abweichen.

Aus Lebenslauf, LinkedIn-Export und Portfolio wird eine Skill Matrix im
New-Monday-Layout: eine einzige lange PDF-Seite mit Hero, Zertifikaten und
bewerteten Kernkompetenzen. Das Layout liegt als HTML/CSS-Template im Skill
und ist aus dem Vorlagen-PDF `Skill Matrix Wissem` nachgemessen. Das Template
wird nicht neu erfunden und nicht "verbessert" – es wird befüllt.

Bester Eingang sind **drei Quellen**: der Lebenslauf als PDF, der
LinkedIn-PDF-Export und das Portfolio (Link oder PDF). Dazu, falls vorhanden,
die Zertifikate als Bilder oder PDFs.

## Die eine Regel, die alles andere schlägt

**Jedes Attribut in der Matrix braucht einen Beleg im Eingang.** Ein Skill
steht nur dann in der Matrix, wenn Lebenslauf, LinkedIn, Portfolio oder ein
Zertifikat ihn hergeben – eine Station, ein Projekt, ein Tool, ein Kurs.
Nichts wird ergänzt, weil es "zum Profil passt" oder "sicher stimmt". Die
Matrix geht an Kunden und behauptet Kompetenzen über einen echten Menschen.

Zwei Dinge in diesem Dokument sind trotzdem Urteile und keine Zitate – die
**Auswahl** der Attribute und ihre **Bewertung** (1–5 Punkte). Genau deshalb
werden beide dem Nutzer **vor dem Rendern** vorgelegt, mit Beleg, und erst
nach Freigabe gebaut (Schritt 2). Still gesetzt wird keine einzige Zahl.

Für alle übernommenen Texte gilt dieselbe Regel wie im CV-Skill: Inhalte
werden übernommen, nicht umgeschrieben; erlaubt ist nur das Glätten von
Rechtschreibung und Grammatik. Neu formuliert werden ausschließlich die
Hero-Beschreibung (nach den Regeln in Schritt 2c) und Beschreibungen für
Attribute, die nicht im Katalog stehen (nach `references/attribute-katalog.md`).

## Umgebung

Beim ersten Lauf auf einem unbekannten System zuerst:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/pruefe_umgebung.py
```

Das nennt fehlende Abhängigkeiten samt Installationsbefehl. Meldet es Lücken,
dem Nutzer den Befehl weiterreichen statt zu raten. Die Punkte aus dem
CV-Skill gelten auch hier: Render-Engine ist WeasyPrint (Chrome als
Ausweichweg), im Browser-Chat blockt der Proxy fremde Domains (betrifft
LinkedIn- und Website-Foto), Ausgabe gehört ins Arbeitsverzeichnis des
Nutzers bzw. nach `/mnt/user-data/outputs/`, nie in den Skill-Ordner.

Für den Figma-Frame (Schritt 4a) braucht es zusätzlich das Figma-MCP-Werkzeug
und ein angemeldetes Konto mit **Bearbeitungsrechten** auf der Zieldatei.
`whoami` sagt, welches Konto verbunden ist – das ist bei Zugriffsfehlern die
erste Frage, nicht die letzte. Fehlt das Werkzeug, entfällt nur der Frame.

## Gefragt wird mit Klickboxen, nicht im Fließtext

Wie im CV-Skill: **Jede Frage mit überschaubarer Antwortmenge läuft über
`AskUserQuestion`.** Material (Dateien, Links, Fotos) wird als Text derselben
Nachricht erbeten, Freigaben und Berichte am Ende sind Text. Fragen werden
gebündelt – dieser Skill kommt mit **zwei** Frage-Nachrichten aus: einer vor
dem Auslesen (Schritt 0, drei Klickboxen in einem Aufruf) und einer als Freigabe
der Matrixinhalte (Schritt 2e). Bei jeder Frage steht die wahrscheinlichste
Option zuerst, mit `(Empfohlen)`.

## Ablauf

Alle Aufrufe nutzen `${CLAUDE_SKILL_DIR}` — den Ordner dieser SKILL.md. Das
Arbeitsverzeichnis ist das des Nutzers; relative Pfade wie
`scripts/render_skillmatrix.py` gehen deshalb ins Leere.

### 0. Vor dem Start fragen — immer, in einer einzigen Nachricht

1. **Die Sprache.** Als `AskUserQuestion`:

   ```
   Frage:   Soll die Skill Matrix auf Deutsch oder Englisch sein?
   Header:  Sprache
   Optionen: Deutsch  |  Englisch
   ```

   Sie steuert die Rubriken ("Kernkompetenzen" / "Core Skills", "Ausgestellt
   von:" / "Issued by:", die Fußzeile) – und darüber hinaus **jeden Satz im
   Dokument**. Der Katalog führt jedes Attribut zweisprachig; genommen wird
   immer die Spalte der gewählten Sprache. Eine deutsche Matrix, auf deren
   Karten "Using AI to analyze user data." steht, ist ein Fehler und kein
   Fachbegriff. Das gilt genauso für die Hero-Beschreibung und für jede
   Beschreibung, die neu formuliert werden muss.

   **Nicht übersetzt werden Attribut- und Kategorienamen.** Sie sind
   Fachbegriffe und stehen auch in den deutschen Vorlagen englisch – eine
   deutsche Matrix trägt "Wireframing & Prototyping", "Design Systems" und
   "Tools & Implementation". Ebenso bleiben Toolnamen und eingeführte
   Fachwörter innerhalb der Beschreibungen englisch ("Auto-Layout",
   "Edge Cases", "WCAG", "Jobs-to-be-Done"). Übersetzt wird, was ein Satz
   ist.

   **Produktnamen tragen die Schreibweise des Herstellers.** Belegbare
   Eigenschreibung schlägt jede andere Variante – auch die aus dem Auftrag:
   "Fullstory", nicht "FullStory"; "Hotjar", nicht "HotJar"; "UXPin", nicht
   "UxPin". Wer eine Schreibweise korrigiert, nennt das in der Übergabe, statt
   es stillschweigend zu tun. Ist die Eigenschreibung nicht zu belegen, bleibt
   die vorgegebene stehen.

2. **Die Verfügbarkeit.** Ebenfalls als Klickbox – sie steht als Badge ganz
   oben im Dokument und ist keine Ableitung aus dem Lebenslauf:

   ```
   Frage:   Ab wann ist <Vorname> verfügbar?
   Header:  Verfügbar
   Optionen: ab sofort (Empfohlen)  |  <laufender Monat + 1>  |  <laufender Monat + 2>
   ```

   Die Antwort kommt als `"verfuegbar_ab": "sofort"` bzw. `"Juli 2026"` in
   die JSON; das Badge macht daraus "VERFÜGBAR AB SOFORT" bzw.
   "VERFÜGBAR AB JULI 2026".

3. **Zusätzlich als Figma-Frame?** Die dritte Klickbox derselben Nachricht:

   ```
   Frage:   Soll die Skill Matrix zusätzlich als bearbeitbarer Frame in einem
            Figma-File landen?
   Header:  Figma
   Optionen: Ja, zusätzlich ins Figma-File (Empfohlen)
           | Nein, nur das PDF
   ```

   Bei „Ja" braucht es den Link – Material, also im Text derselben Nachricht,
   wörtlich so:

   > Schick mir den Link zum Figma-File, in das die Skill Matrix soll
   > (figma.com/design/…). Zeigt der Link auf eine bestimmte Seite, lege ich
   > sie dort ab, sonst auf einer neuen Seite. Ich brauche **Bearbeitungs**rechte
   > auf der Datei – Leserechte reichen nicht.

   Der Frame entsteht erst nach dem Rendern, siehe Schritt 4a. Drei Regeln dazu:

   - **Kommt „Ja" ohne Link**, wird er einmal im Fließtext nachgefragt – nicht
     über eine dritte `AskUserQuestion`-Nachricht.
   - **Der Link blockiert nichts.** Bleibt er aus, entsteht trotzdem das PDF,
     und der Figma-Teil entfällt mit einem Satz in der Übergabe. Eine Skill
     Matrix ohne Figma-Frame ist vollständig.
   - **Nur Design-Dateien.** `figma.com/design/…` ja; `/board/` (FigJam),
     `/slides/`, `/make/` und `/proto/` nein. Dann sagen, was gebraucht wird,
     statt es zu versuchen.

4. **Das Material**, als Text derselben Nachricht, wörtlich in dieser Art:

   > Schick mir bitte den Lebenslauf als PDF, den LinkedIn-Export als PDF
   > (auf dem Profil: *Mehr* → *Als PDF speichern*) plus den Link zum
   > Profil, und das Portfolio als Link oder PDF. Wenn es Zertifikate gibt,
   > die mit in die Matrix sollen: als Bild oder PDF dazu – sie bekommen
   > eine eigene Sektion mit Bilderraster.

   Was davon fehlt, fehlt – gebaut wird mit dem, was kommt. Aber jede
   fehlende Quelle macht die Belegbasis schmaler, und ohne Zertifikate
   entfällt die Zertifikatssektion ersatzlos (das ist in Ordnung – Florians
   Vorlage hat auch nur eine Zertifikatskarte und kein Bilderraster).

5. **Ein Foto**, falls Lebenslauf, LinkedIn und Portfolio keins hergeben –
   erst nach Schritt 1a anfragen, nicht hier. Hier nur erwähnen, dass ein
   richtiges Foto in guter Auflösung willkommen ist: die Fotokarte im Hero
   ist groß (433pt breit), das LinkedIn-Thumbnail ist dafür sichtbar weich.

### 1. Eingang auslesen

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <lebenslauf.pdf> arbeit/
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <linkedin-export.pdf> arbeit/linkedin/
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <portfolio.pdf> arbeit/portfolio/
```

Schreibt je Quelle `text.txt` und legt Porträtkandidaten in `fotos/` ab –
bereits in Graustufen und auf das Kartenformat (433 × 390pt, oben bündig)
beschnitten. Bei einem Portfolio-Link die Seite abrufen und die
Projektseiten dazu.

Für das Zusammenführen der Quellen gelten die Regeln des CV-Skills
unverändert: **Bei Widersprüchen gewinnt der Lebenslauf**, LinkedIn ergänzt
nur Lücken, das Portfolio ist Eigenwerbung (Fakten übernehmen, Bewertungen
nicht), LinkedIn-Artefakte wie "Top-Kenntnisse" ignorieren. Die Rubrik
"Kenntnisse" im LinkedIn-Export ist trotzdem nützlich – als **Hinweis**,
wonach im Lebenslauf und Portfolio zu suchen ist, nie als alleiniger Beleg.

**Zertifikate aufbereiten**, falls welche gekommen sind:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/zert_bilder.py <zert1.pdf> <zert2.png> … arbeit/zertifikate/
```

Die Reihenfolge der Argumente ist die Reihenfolge im Raster. Das Skript
meldet Formate, die von der Kachel (395 × 284pt) stark abweichen – solche
Bilder werden im Raster mittig beschnitten, das vorher sagen, nicht danach.

### 1a. Das Foto — dieselbe Rangfolge wie im CV-Skill

1. Foto aus dem **Lebenslauf** (oder separat geschickt),
2. sonst **LinkedIn**: `python3 ${CLAUDE_SKILL_DIR}/scripts/linkedin_foto.py "<profil-url>" arbeit/`,
3. sonst **Portfolio/Website**: `python3 ${CLAUDE_SKILL_DIR}/scripts/website_foto.py "<url>" arbeit/`,
4. sonst **beim Kandidaten anfragen**.

Alle Wege legen das Foto fertig beschnitten in `arbeit/fotos/` ab. Die
Warnungen der Skripte ernst nehmen: die Fotokarte ist sechsmal so breit wie
der Fotokasten im CV, **unter 100 dpi wird das Bild sichtbar weich** – das
400px-Thumbnail von LinkedIn liegt bei ~65 dpi und taugt nur als Notlösung.
Liegt im Lebenslauf oder Portfolio ein größeres Bild, das zu nehmen. Jedes
automatisch gefundene Foto ansehen, bevor es ins Dokument geht (fremde
Gesichter, siehe CV-Skill). Ohne Foto funktioniert das Layout – die Karte
zeigt dann nur den Farbverlauf mit Name und Erfahrung – aber es wirkt leer.

### 2. Attribute auswählen und bewerten

Das ist der Kern dieses Skills. Zuerst `references/attribute-katalog.md`
lesen – er ist der Wortschatz der Matrix.

#### 2a. Kategorien festlegen

Kategorien werden **nicht erfunden**. Genommen werden Abschnittstitel aus
`references/attribute-katalog.md` – dort stehen dreizehn, und sie decken jedes
Profil ab, das dieses Haus vermittelt.

**Die Sektion Kernkompetenzen trägt höchstens 24 Skills:** vier Kategorien zu
je sechs, gesetzt als **drei Karten pro Reihe, zwei Reihen** je Kategorie. Das
ist keine Empfehlung, sondern das Layout – ein siebter Skill hat keinen Platz,
eine fünfte Kategorie sprengt die Seite. Weniger ist erlaubt und oft besser:
eine Kategorie mit zwei Skills wird mit einer verwandten zusammengelegt, drei
Kategorien sind ein vollständiges Dokument.

Ausgewählt werden die Kategorien, die das Profil **belegt**, die stärkste
zuerst. Ein Profil ohne KI-Belege bekommt keine AI-Kategorie; ein
Barrierefreiheits-Schwerpunkt bekommt `Accessibility & Inclusive Design`.

**`Tools` ist keine Kategorie, sondern eine eigene Sektion.** Sie bekommt eine
eigene Überschrift mit Icon – genau wie „Kernkompetenzen" – und steht **vor**
den Kernkompetenzen. Sie zählt nicht gegen die 24, weil sie Werkzeuge listet
und keine Fähigkeiten. Ein Kategorielabel innerhalb der Sektion entfällt: Die
Überschrift sagt bereits „Tools", ein zweites Label darunter wäre doppelt.

Damit trägt der Rumpf in dieser Reihenfolge: **Tools → Kernkompetenzen**
(→ Zertifikate, falls belegt). Befüllt wird Tools aus dem Katalogabschnitt
`Tools`, und auch hier gilt: nur was der Eingang belegt.

`Coding Skills` ist dagegen eine gewöhnliche Kategorie innerhalb der
Kernkompetenzen und ersetzt dann eine der vier.

#### 2b. Attribute wählen

Je Kategorie die Skills, die der Eingang **belegt** – über Stationen,
Projekte, Tool-Listen, Portfolio-Cases oder Zertifikate.

**Die Katalogabschnitte sind Ablage, keine Schranke.** Eine Matrix-Kategorie
darf ihre Attribute aus jedem Abschnitt ziehen; entscheidend ist, was der
Eingang hergibt, nicht wo das Attribut im Katalog einsortiert ist. Ein Profil
mit vier Stationen, die "Frontend Development" als Skill führen, bekommt
`HTML / CSS` in seine Development-Kategorie – auch wenn der Eintrag im Katalog
unter `Coding Skills` steht. Wer stattdessen abschnittstreu befüllt, wählt
nach Ordnerstruktur statt nach Beleg und schiebt den konkreten Eintrag
zugunsten eines vageren beiseite, der zufällig im richtigen Abschnitt liegt.

Steht ein Attribut
im Katalog, werden **Name und Beschreibung wörtlich** übernommen – die
Beschreibung aus der **Spalte der gewählten Sprache**, der Name unverändert.
Nur was dort fehlt, wird neu formuliert (Stilregeln am Ende des Katalogs),
und zwar ebenfalls in der Dokumentsprache. So tragen alle Matrizen für
denselben Skill denselben Text.

#### 2c. Hero-Inhalte

- **Name, Rolle**: aus dem Lebenslauf. Die Rolle ist die, mit der die
  Person vermittelt wird (z.B. "Senior UX/UI Designer") – im Zweifel die
  Rollenbezeichnung aus dem aktuellsten CV-Titel, nicht aus der letzten
  Station.
- **Erfahrung**: wie im CV-Skill – Angabe aus dem Lebenslauf übernehmen,
  sonst ab der ersten Berufsstation rechnen, abgerundet, ohne
  Ausbildungs- und Weiterbildungszeiten. Format `"12+ Jahre Erfahrung"`
  bzw. `"12+ years of experience"`.
- **Beschreibung** (die zwei Zeilen unter der Rolle): der einzige längere
  neue Text im Dokument. Sie steht in der **Ich-Perspektive** – in der
  Skill Matrix spricht der Kandidat selbst, sie ist kein Steckbrief über
  ihn. Also "Ich gestalte digitale Produkte von der Research-Phase bis zur
  Umsetzung.", nicht "Gestaltet digitale Produkte …" und erst recht nicht
  "Enrico gestaltet …". Auf Englisch genauso: "I design …". Sonst dieselben
  Regeln wie beim Kurzprofil des CV-Skills: nur aus Material, das im
  Eingang steht; keine Eigenschaftszuschreibungen ("leidenschaftlich",
  "erfahren"); ein bis zwei Sätze. **Immer melden, dass er generiert ist,
  und zur Freigabe stellen** (Schritt 2e erledigt beides).
- **Schwerpunkte**: **genau drei** Begriffe für die umrandeten Buttons,
  aus den stärksten belegten Themen des Profils. Kurz halten – zwei bis
  vier Wörter je Button, sonst bricht die Zeile.

#### 2d. Bewerten — die Skala

| Punkte | Bedeutung | Typische Belege |
|---|---|---|
| 5 | Kernkompetenz, Expertenniveau | jahrelang in Projekten, Zertifikat plus Praxis, eigene Systeme/Prozesse aufgebaut |
| 4 | Sehr sicher, regelmäßig im Einsatz | mehrere Projekte oder Stationen, aber nicht der Kern des Profils |
| 3 | Solide, wiederkehrend eingesetzt | vereinzelte Projekte, Kurspraxis, Nebenrolle im Alltag |
| 1–2 | Berührungspunkte | **kommt nicht in die Matrix** – weglassen statt abwerten |

**Drei Punkte sind die Untergrenze für die Ausgabe.** Ein Skill mit 1 oder 2
Punkten wird nicht angezeigt – nicht abgewertet, nicht in Klammern, nicht
kleiner gesetzt, nicht als leere Karte: weggelassen. Wer eine 2 vergibt, hat
die Entscheidung schon getroffen, dass der Skill nicht ins Dokument gehört.
Steht am Ende eine Karte mit weniger als drei gefüllten Punkten im Frame, ist
das ein Fehler und keine Geschmacksfrage – im Figma-Frame wird sie auf
`visible = false` gesetzt, in der JSON gar nicht erst geführt.

Was schwächer belegt ist, gehört nicht in ein Verkaufsdokument. Und
**nicht alles ist eine 5** – eine
Matrix, in der jede Zeile fünf volle Punkte trägt, liest sich wie ein
Prospekt, nicht wie eine Einschätzung. Wissems Vorlage hat 4er und einen
3er; die Abstufung macht die 5er glaubwürdig. Für jede Bewertung den Beleg
notieren – er wird in Schritt 2e mit angezeigt und macht die Zahl
nachvollziehbar statt verhandelbar.

#### 2e. Die Freigabe — eine Nachricht, dann erst bauen

Vor dem Bauen der JSON bekommt der Nutzer **eine** Nachricht mit allem, was
Urteil ist:

1. Die **Hero-Beschreibung** im Wortlaut, als generiert gekennzeichnet.
2. Die **drei Schwerpunkte**.
3. Die **komplette Matrix als Tabelle**: Kategorie, Attribut, Punkte, Beleg
   (eine Zeile je Attribut, Beleg in Stichworten – "3 Jahre Design-System
   bei X", "CPUX-F 2021", "Portfolio-Case Y").
4. Dazu **eine** `AskUserQuestion`:

   ```
   Frage:   Passen Auswahl und Bewertung so?
   Header:  Freigabe
   Optionen: Ja, so bauen (Empfohlen)  |  Ich möchte etwas ändern
   ```

   Bei "ändern" beschreibt der Nutzer die Änderungen als Text; danach die
   aktualisierte Tabelle noch einmal kurz zeigen, nicht die ganze Nachricht
   wiederholen.

**Bis die Freigabe da ist, wird nicht gerendert.**

### 3. Daten strukturieren

Aus den freigegebenen Inhalten eine `skillmatrix.json` bauen. Vollständiges
Beispiel: `beispiel/skillmatrix.json` (das ist Wissems Matrix aus der
Vorlage – einzige Abweichung ist die Hero-Beschreibung, die dort in die
Ich-Perspektive gebracht wurde; das Vorlagen-PDF trägt sie noch in der
dritten Person).

```json
{
  "sprache": "de",
  "person": {
    "name", "rolle", "verfuegbar_ab", "erfahrung",
    "beschreibung", "schwerpunkte": [], "foto"
  },
  "zertifikate": [{ "titel", "aussteller", "jahr", "beschreibung", "tags": [] }],
  "zertifikat_bilder": [],
  "kompetenzen": [{ "kategorie", "skills": [{ "name", "punkte", "beschreibung" }] }]
}
```

Dazu:

- **`zertifikate`**: je Zertifikat eine Karte, mit Ausstellungsjahr im
  Badge. Gehören mehrere Zertifikate erkennbar zu einem Weiterbildungsblock,
  dürfen sie wie in der Wissem-Vorlage zu einer Karte gebündelt werden
  ("A & B & C") – das ist eine Darstellungsentscheidung, im Zweifel den
  Nutzer in Schritt 2e mitentscheiden lassen. `tags` sind die Themen aus dem
  Zertifikatsinhalt, sechs bis acht reichen.
- **`zertifikat_bilder`**: die Ausgabe von `zert_bilder.py`, in
  Rasterreihenfolge. Ohne Bilder entfällt das Raster, ohne `zertifikate`
  die ganze Sektion – beides ist zulässig.
- **`zertifikate_titel`** (optional, oberste Ebene): überschreibt die
  Sektionsüberschrift, z.B. `"Zertifizierungen UX/UI"` wie in Florians
  Vorlage.
- **`punkte`**: ganze Zahl 3–5, siehe Skala. Das Renderskript warnt
  darunter.
- **Reihenfolge der Kategorien**: die stärkste zuerst – bei einem
  KI-Profil AI, sonst Strategie & Research. Die Vorlagenreihenfolge nur
  übernehmen, wenn sie zum Profil passt.

### 4. Rendern

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_skillmatrix.py skillmatrix.json ausgabe/
```

**Den Dateinamen setzt das Skript**, nicht der Aufruf: es baut ihn aus
`person.name` und `person.rolle` zusammen und legt die Datei im
angegebenen Ordner ab.

```
New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf
```

Steht im Aufruf trotzdem ein Dateiname, gilt davon nur der Ordner — das
Skript meldet die Umbenennung. Der Name im Bericht an den Nutzer ist der,
den das Skript ausgibt, nicht der aus dem Aufruf. Die Datei heißt so, wie
sie beim Kunden ankommt, deshalb wird hier nicht abgekürzt und nicht
umbenannt.

Das Skript rendert zweimal (Vorratshöhe, dann exakte Inhaltshöhe – die
Matrix ist eine einzige lange Seite), sucht sich die Engine selbst und
meldet Auffälligkeiten nach stderr: fehlende Felder, Punkte außerhalb der
Skala, überlange Beschreibungen, mehr als drei Schwerpunkte, fehlende
Bilddateien. Die Hinweise sind zu lesen und abzuarbeiten, nicht zu
überfliegen.

**Das Ergebnis ansehen, bevor es rausgeht** – immer, nicht nur bei
Warnungen:

```bash
pdftoppm -png -r 40 "ausgabe/New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf" arbeit/vorschau
```

Auf der Vorschau prüfen: Steht das Gesicht frei vom Farbverlauf? Brechen
die Schwerpunkt-Buttons einzeilig? Läuft kein Kartentitel in die Punkte?
Sind die Zertifikatsbilder nicht unglücklich beschnitten? Wirkt eine
Kategoriezeile halb leer (eine einzelne Karte in der letzten Zeile ist in
Ordnung – die Vorlage hat das auch)?

### 4a. Den Figma-Frame ablegen — nur wenn danach gefragt wurde

Entfällt, wenn in Schritt 0 „Nein" kam oder kein Link vorliegt. **Das PDF ist an
dieser Stelle fertig** und geht so oder so raus.

**Es gibt zwei Wege, und die Wahl ist keine Geschmacksfrage.** Zuerst nachsehen,
ob die Zieldatei die New-Monday-Komponenten führt:

```js
figma.root.children.map(p => p.name)        // gibt es eine Seite "Components"?
```

| Zieldatei | Weg | Rezept |
|---|---|---|
| **Masterdatei** `Portfolio - CV Master` oder jede Datei mit den New-Monday-Komponenten | **Vorlage klonen und befüllen** | `references/figma-vorlage.md` |
| fremde oder leere Datei ohne diese Komponenten | aus dem Bauplan zeichnen | `references/figma.md` |

**Im Zweifel der erste Weg.** Gezeichnet wird jedes Element aus Maßen — und
jedes Element, für das keine Maße vorliegen, wird geraten. Genau dort entstehen
erfundene Icons, Verläufe und Bildinhalte. Ein Klon der Vorlage kann das nicht,
weil er nichts neu erfindet, und er bleibt an die Komponenten der Datei
gebunden: Ändert jemand später `Skill Card`, ziehen alle Matrizen mit.

#### Weg A — Vorlage klonen (Masterdatei)

Kein Bauplan nötig. Die Vorlage `Nachbau` klonen, auf die Zielseite hängen,
Texte über `characters` matchen und überschreiben, `Dots` über die Variante
`Filled` setzen, Foto über den `imageHash` einsetzen. Vollständig mit allen
Fallstricken in `references/figma-vorlage.md` — darunter die drei, die still
danebengehen:

- **Sektionen ohne Beleg entfernen**, nicht mit Vorlageninhalt stehen lassen.
  Ohne Zertifikate im Eingang fliegt die Zertifikatssektion raus; sonst
  behaupten die Zertifikatsbilder der Vorlage Qualifikationen, die der Kandidat
  nie erworben hat.
- **`resetOverrides()` vor dem Befüllen** einer `Skill Section` — in der
  Vorlage sind dort Kartenslots per Override gelöscht, und eine Schleife über
  die vorhandenen Karten schluckt den Überhang wortlos.
- **Der Frame ist 1444pt breit**, nicht 1440. Die 1440 aus `layout.md` stammen
  aus dem PDF-Nachbau.

#### Weg B — aus dem Bauplan zeichnen (fremde Datei)

Erst den Bauplan, dann bauen:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py skillmatrix.json arbeit/ \
        --pdf "ausgabe/New-Monday - … - Skillmatrix.pdf"
```

Das schreibt `arbeit/figma_plan.json`: **ein** Frame, darin die vier Bänder
(Kopf, Hero, Rumpf, Fuß) in Lesereihenfolge, alle Werte fertig ausgerechnet.
`--pdf` ist optional und trägt nur die gemessene Seitenhöhe als **Sollwert** in
den Plan; am Ende wird die Frame-Höhe dagegen gehalten (±20pt sind normal, mehr
ist ein Hinweis).

Gebaut wird mit `use_figma` nach dem Rezept in `references/figma.md`. Dort stehen
Linkauslesung, Zielseite, Schnittnamen, das Band-Rezept, der Weg für Logos, Foto
und Zertifikatsbilder und die Aufteilung in rund zehn Aufrufe.

---

**Für beide Wege gilt: vor dem ersten Aufruf den Skill `figma-use` laden** —
ohne ihn sind die Fallstricke des Plugin-API nicht zu umgehen.

Vier Dinge stehen fest:

- **Figma hält das PDF nicht auf.** Schlägt irgendetwas fehl — Werkzeug nicht
  verbunden, nicht angemeldet, keine Bearbeitungsrechte, falscher Dateityp, Proxy
  blockt —, wird das PDF trotzdem übergeben und der Grund genannt. Nicht
  abbrechen, nicht nachträglich am PDF drehen, und keinen zweiten Anlauf mit
  anderen Daten.
- **In eine fremde Datei kommt nichts Globales.** Keine Text-Styles, keine
  Variablen, keine Komponenten. Der Frame trägt rohe Werte. Was schon in der
  Datei liegt, wird nicht umbenannt, nicht verschoben und nicht gelöscht.
- **Nichts überschreiben.** Steht dort schon ein Frame gleichen Namens, kommt der
  neue daneben, nicht darüber.
- **Kein Ersatz-Layout.** Reicht es nicht für den Frame, wird kein vereinfachter
  gebaut. Entweder das Dokument oder nichts.

### 5. Übergeben

PDF ausgeben und in wenigen Zeilen berichten:

- Die generierte Hero-Beschreibung im Wortlaut (falls seit der Freigabe
  geändert), mit Bitte um finalen Blick.
- Welche Attribute **nicht** aus dem Katalog stammen und neu formuliert
  wurden.
- Wo Quellen einander widersprachen – mit beiden Werten; ins Dokument kam
  der Lebenslauf.
- Woher das Foto stammt (falls automatisch geholt) und die dpi-Zahl, falls
  unter 100.
- Was das Renderskript bemängelt hat und wie damit umgegangen wurde.
- **Der Figma-Frame**, falls einer gewünscht war: der Link auf den Frame
  (`…?node-id=…`) und auf welcher Seite der Datei er liegt. Ist er nicht
  zustande gekommen, steht hier stattdessen der Grund in einem Satz. Weicht
  die Frame-Höhe um mehr als 20pt von der PDF-Höhe ab, gehört auch das hierher
  – dann bricht in Figma ein Text anders um als im PDF und sollte nachgesehen
  werden.

Ganz zum Schluss, nur wenn wirklich etwas fehlt, im Stil des CV-Skills:

> Profilfoto einfügen, um die Skill Matrix zu vervollständigen

> Zertifikate als Bilder nachreichen, um die Skill Matrix zu vervollständigen

Fehlt nichts, steht hier nichts.

## Was fest steht und nicht zur Disposition steht

- **Eine Sprache im ganzen Dokument.** Die gewählte Sprache gilt für jeden
  Satz – Rubriken, Hero-Beschreibung, jede Kartenbeschreibung. Gemischte
  Dokumente gibt es nicht. Ausgenommen sind allein Attribut- und
  Kategorienamen sowie Toolnamen, die als Fachbegriffe englisch bleiben.
  Das Renderskript warnt, wenn eine Beschreibung nach der falschen Sprache
  aussieht.
- **Hero-Beschreibung in der Ich-Perspektive.** In der Skill Matrix spricht
  der Kandidat selbst.
- **Sektionsreihenfolge**: Hero → Zertifikate → Kernkompetenzen → Fuß, wie
  in der Wissem-Vorlage. Einzige zulässige Abweichung ist die
  Florian-Variante mit den Zertifikaten am Ende:
  `"zertifikate_position": "ende"` in der JSON. Nur auf Wunsch des Nutzers,
  Standard ist vorn.
- **Bewertungsskala**: fünf Punkte, gefüllt in der Markenfarbe. Keine
  Prozente, keine Balken, keine Sterne.
- **Schrift ist Inter**, liegt in `assets/fonts/`, wird eingebettet.
- **Farben und Maße** stehen in `references/layout.md` und stammen aus der
  Vorlage – kein Umbau, keine neuen Rubriken, keine anderen Farben ohne
  ausdrückliche Ansage.
- **Ansprechpartner im Fuß**: immer Manuel Klein, CCO. Steht als Vorgabe im
  Renderskript.
- **Keine anonymisierte Variante.** Name und Foto gehören ins Dokument.
- **Das PDF ist der Ausgang, der Figma-Frame die Zugabe.** Er wird nie statt
  des PDFs geliefert und nie vor ihm gebaut.
- **Kein Inhalt aus der Vorlage bleibt stehen.** Weder ein Name noch ein
  Zertifikatsbild noch eine Beispielbeschreibung. Was das Material nicht
  hergibt, wird entfernt oder ausgeblendet – nie mit fremdem Inhalt
  ausgeliefert. Nach jedem Figma-Lauf wird der Frame gegen die Namen aus der
  Vorlage geprüft; ein Treffer ist ein Fehler, kein Schönheitsfehler.

## Wenn das Layout doch angefasst werden muss

Maße, Typo, Farben und die WeasyPrint-Eigenheiten (kein Grid, kein
CSS-Filter, feste Kartenbreiten, warum `body` keinen Hintergrund haben darf)
stehen in `references/layout.md` – vor jeder Änderung lesen, sonst bricht
die Höhenmessung des Renderskripts.

Wer dort etwas ändert, muss `scripts/figma_plan.py` mitziehen: Es trägt dieselben
Abstände, Breiten und Schriftwerte ein zweites Mal, damit der gezeichnete
Figma-Frame (Weg B) nicht vom PDF abweicht. Wie daraus ein Frame wird, steht in
`references/figma.md`.

**Weg A ist davon nicht betroffen** – der Klon holt seine Maße aus der Vorlage
und nicht aus dem CSS. Umgekehrt gilt: Ändert sich die Vorlage in der
Masterdatei, ist `references/figma-vorlage.md` nachzuziehen, insbesondere die
Tabelle der Komponenten und die Liste der Hero-Ersetzungen.
