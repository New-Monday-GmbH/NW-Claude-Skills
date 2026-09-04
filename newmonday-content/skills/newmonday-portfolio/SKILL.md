---
name: newmonday-portfolio
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*) Bash(pdftoppm *) Bash(pdfinfo *) WebSearch WebFetch AskUserQuestion Read Write Edit
description: Wandelt die Unterlagen eines Kandidaten in ein fertiges Portfolio im New-Monday-Layout als PDF – 16:9-Folien mit Profilseite, Kundenwand, Design-Prozess, Projektstrecken und Kontaktseite. Eingang ist ein Portfolio als PDF, ein Link zu einer Portfolio-Website, ein LinkedIn-PDF-Export und/oder ein Lebenslauf. Nutze diesen Skill immer, wenn ein Portfolio, eine Arbeitsprobe, eine Projektstrecke oder eine Case-Sammlung aufbereitet, umformatiert, "ins New Monday Layout gebracht", vereinheitlicht oder für Kunden fertiggemacht werden soll – auch wenn nur eine PDF-Datei mit Projekten ohne weitere Erklärung geschickt wird, und auch dann, wenn das Wort "Layout" oder "New Monday" gar nicht fällt. Für Lebensläufe ist newmonday-cv zuständig, nicht dieser Skill.
---

# New Monday Portfolio

Aus den Unterlagen eines Kandidaten wird ein Portfolio im New-Monday-Layout:
23 bis 39 Folien im Format 1920 × 1080 pt – 14 feste plus drei bis fünf je
Projekt; ohne `person.ki` entfällt die KI-Folie und es sind 13 feste.
Das Layout ist aus den bestehenden
Portfolios gemessen und liegt als HTML/CSS im Skill. Es wird nicht neu erfunden
und nicht "verbessert" – es wird befüllt.

**Beste Eingangslage sind drei Quellen**: das Portfolio des Kandidaten als PDF
oder Website, der Lebenslauf und der LinkedIn-PDF-Export. Bei Widersprüchen
gilt: **Portfolio vor Lebenslauf vor LinkedIn.**

## Die eine Regel, die alles andere schlägt

**Inhalte werden übernommen, nicht umgeschrieben.** Erlaubt ist ausschließlich
das Glätten von Rechtschreibung, Zeichensetzung und Grammatik. Zur Grammatik
zählt auch die Sprachmischung innerhalb einer sonst deutschen Wendung: „KI
Expert" wird zu „KI Experte" geglättet – ein halb englisches Wort in einem
deutschen Titel ist ein Grammatikfehler, kein Stilmittel. Feststehende
englische Fachbegriffe („Senior UX Designer", „Vibe Coding") bleiben, wie sie
sind. Jede solche Glättung steht in der Übergabe. Nicht erlaubt:

- Formulierungen straffen, umstellen oder "auf den Punkt bringen"
- Projektbeschreibungen zusammenfassen oder in andere Worte fassen
- Zahlen, Zeiträume, Rollen oder Kunden ergänzen oder plausibler machen
- Erfundene Angaben, auch keine "offensichtlich gemeinten"

Ein Portfolio geht an Kunden und behauptet etwas über die Arbeit eines echten
Menschen. Jede stille Ergänzung ist eine Behauptung, die jemand anders
verantworten muss. Fehlt etwas, wird gefragt – nicht geraten. Das gilt
ausdrücklich auch für das Statement auf Seite 4: Es steht oft nicht im
Material und wird dann **erfragt, nicht geschrieben**.

Ein Portfolio ist Eigenwerbung. Bewertende Formulierungen des Kandidaten
("preisgekrönt", "führend") werden übernommen, wenn sie dort stehen – aber
nicht von dir hinzugefügt.

**Fünf Stellen sind davon ausgenommen, und nur diese fünf.** Sie stehen hier
oben, damit niemand sie erst auf halber Strecke findet:

- **Der Text der KI-Folie** (Seite 10), wenn im Material nichts oder nur
  Bruchstücke dazu stehen. Was er behaupten darf und was nicht, steht in
  Schritt 4 unter „Die KI-Folie".
- **`cover_titel`**, abgeleitet aus der Rolle. Eine Zeile, und sie steht in der
  Übergabe – siehe Schritt 3.
- **Die Übersetzung**, wenn die gewählte Sprache nicht die des Eingangs ist. Nur
  auf ausdrückliche Ansage, nie von sich aus – siehe Schritt 0.
- **`kunde_text`**, die Kundenbeschreibung der Projekt-Kopfseite – aber nur
  als Wiedergabe belegter Quellen (Selbstdarstellung des Kunden, Wikipedia),
  nie aus dem Gedächtnis des Modells, und immer mit Quelle in der Übergabe.
  Wie recherchiert wird, steht in Schritt 0.
- **Die Prozesstexte der Seiten 6–9** (`prozess[].kurztext` und `langtext`),
  wenn das Material keinen fertigen Prozess liefert. Dann gilt die Kaskade in
  Schritt 4 unter „Der Design-Prozess sind genau drei Schritte": erst wörtlich
  übernehmen, dann aus CV, LinkedIn und Portfolio erweitern, zuletzt daraus
  ableiten – und immer in der Übergabe kennzeichnen.

Alles andere kommt aus dem Material oder gar nicht. Das gilt auch für die
Einleitungszeile der Lösungsseiten (`loesungen[].titel`): Sie sieht aus wie ein
Titel, den man schreiben könnte, und ist keiner – siehe Schritt 4.

## Umgebung

Beim ersten Lauf auf einem unbekannten System zuerst:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/pruefe_umgebung.py
```

- **Render-Engine**: Das Layout ist auf WeasyPrint abgestimmt. Fehlt sie, weicht
  das Skript auf Chrome aus und sagt das – dann Seitenumbrüche und Textlängen
  gegenprüfen, bevor das PDF rausgeht.
- **Netz**: Lokal und in Claude Desktop offen, im Browser-Chat blockt der Proxy
  fremde Domains. Das betrifft die Logosuche und das Auslesen einer
  Portfolio-Website.
- **Ausgabeort**: In Claude Code ins Arbeitsverzeichnis des Nutzers, im
  Browser-Chat nach `/mnt/user-data/outputs/`. Ausnahme sind neue Logos: die
  gehören dauerhaft in die Bibliothek, damit sie wächst.
- **Logobibliothek**: gemeinsam mit `newmonday-cv`. Liegt dieser Skill daneben,
  nutzen beide denselben Ordner – siehe `scripts/logo_lib.py`.

## Gefragt wird mit Klickboxen, nicht im Fließtext

**Jede Frage, deren Antwort aus einer überschaubaren Menge stammt, läuft über
`AskUserQuestion`.** Der Nutzer soll klicken, nicht tippen. Nur zwei Dinge
stehen als Text daneben: **Material**, das geschickt werden muss, und die
**Übergabe** am Ende.

Der Skill kommt mit **zwei** Fragenachrichten aus – einer vor dem Auslesen
(Schritt 0) und einer davor, bevor gebaut wird (Schritt 3). Wo mehr als vier
Fragen zusammenkämen, werden sie zusammengelegt, nicht in eine dritte Nachricht
ausgelagert. Bei jeder Frage steht die Option zuerst, die aus dem Eingang am
wahrscheinlichsten folgt, mit `(Empfohlen)` im Label.

Rote Flagge: Du tippst gerade eine Frage samt Antwortmöglichkeiten in den
Fließtext. Dann gehört sie in `AskUserQuestion`.

## Ablauf

Alle Aufrufe nutzen `${CLAUDE_SKILL_DIR}` – den Ordner, in dem diese SKILL.md
liegt. Das Arbeitsverzeichnis ist das des Nutzers; relative Pfade wie
`scripts/render_portfolio.py` gehen deshalb ins Leere.

### 0. Vor dem Start fragen — immer, in einer einzigen Nachricht

1. **Die Sprache**, als `AskUserQuestion`:

   ```
   Frage:   Soll das Portfolio auf Deutsch oder Englisch sein?
   Header:  Sprache
   Optionen: Deutsch | Englisch
   ```

   Die Frage wird **immer** gestellt, auch wenn der Eingang eindeutig
   einsprachig aussieht – ein englisches Portfolio kann für einen deutschen
   Kunden gedacht sein. Die Antwort kommt als `"sprache": "de"` oder `"en"` in
   die `portfolio.json` und steuert alle Rubriken.

   Ist die gewählte Sprache nicht die des Eingangs, muss übersetzt werden. Das
   ist die dritte der fünf Ausnahmen oben und braucht eine ausdrückliche
   Ansage – von sich aus wird nie übersetzt.

2. **Material**, als Text in derselben Nachricht, sinngemäß so:

   > Am besten schickst du mir drei Dinge: das Portfolio (PDF oder Link zur
   > Website), den Lebenslauf und den LinkedIn-PDF-Export (auf dem Profil:
   > *Mehr* → *Als PDF speichern*). Der LinkedIn-Export füllt zuverlässig die
   > Lücken, die Portfolios typischerweise lassen – vollständige Firmennamen,
   > Zeiträume, Rollen.

   **Der Hinweis auf den LinkedIn-Export gehört in jeden Lauf**, nicht nur bei
   Lücken. Ein Portfolio zeigt Arbeit, keinen Werdegang; genau die Angaben, die
   die Profilseite braucht, stehen dort selten.

   **Fehlt der Lebenslauf, wird ausdrücklich darum gebeten** – auch dann, wenn
   Portfolio und LinkedIn-Export vollständig aussehen. Er ist die erste Quelle
   für das Profilfoto, und im LinkedIn-PDF ist so gut wie nie eins drin.

3. **Firmenlogos als SVG.** Die Logodatenbanken führen globale Marken
   zuverlässig, deutsche Mittelständler und Agenturen fast nie – und genau die
   stehen in diesen Portfolios. Deshalb gleich darum bitten, die Kundenlogos als
   SVG mitzuschicken, am besten aus dem Presse- oder Brand-Bereich der
   Firmenseite. Die Bitte ist eine Abkürzung, keine Bedingung: Was nicht kommt,
   suchst du selbst (Schritt 5).

4. **Einzelne Screenshots der Anwendung, pro Projekt drei bis acht.**
   Das ist der Materialposten, an dem die Projektstrecke hängt: Lösungs- und
   Abschlussseite sind eine **diagonale Kaskade** – wenige, große Screens
   auf satter, dunkler Markenfarbe, alle um denselben leichten Winkel
   gekippt, diagonal versetzt und an den Kanten entschlossen angeschnitten,
   wie in den Referenzportfolios. **Wie sie dort liegen, entscheidet der
   Skill selbst**; die Regeln stehen in `references/layout.md`. Das Material
   liefert die Screens, nicht ihre Anordnung; fest gesetzt sind nur die
   Grundfläche und die HQ-Fotos. **Die Kaskade lebt von Größe, nicht von
   Menge**: Eine Lösungsseite trägt 1–3 Desktop-Screens (bis 6 Mobile), die
   Abschlussseite 2–6 (bis 8 Mobile) – jeder Screen liegt um die halbe
   Folienbreite groß, wie in den Vorlagen. Mehr Screens zeigt die Fläche
   nicht; die Reihenfolge in der JSON entscheidet, welche stehen, der erste
   bekommt den Hero-Platz. Die Fläche wird mit 2 px je Punkt gerechnet:
   ein Desktop-Screen liegt 1 450 bis 1 920 px breit, ein Phone 620 bis
   780 px. Deshalb um Originalexporte in voller Auflösung bitten – ein
   1 920er-Export trägt jede Lage ohne Hochrechnen. `screens.py` misst
   jeden Screen gegen seine tatsächlich platzierte Größe und **platziert
   nicht, was deutlich hochgerechnet würde**: Zu weiche Screens schrumpfen
   erst in ihrem Platz, dann fliegen sie raus, und bleibt nichts Scharfes
   übrig, steht auf der Seite die reine Grundfläche. Eine blanke Fläche ist
   besser als eine unscharfe Kaskade. Die Meldungen dazu sind der Anlass,
   schärfere Dateien anzufragen, nicht eine Fußnote.

   **Ein aus einem PDF geschnittenes Mosaik taugt dafür nicht.** Was dort
   herauskommt, ist ein Bild mit mehreren Screens darauf, komprimiert, mit
   Rändern und Beschriftungen. Geneigt und übereinandergelegt sieht man jede
   dieser Kanten. Also um die Originaldateien bitten – Exporte aus Figma, aus
   dem Prototyp oder aus dem Design-System, ein Screen je Datei. Kommt doch
   ein Screen auf einer Mockup-Karte mit Rand an, beschneidet `screens.py`
   ihn selbst auf den Inhalt und meldet es – das ist die Notlösung, nicht der
   Weg.

   **Liegt das Material als Figma-Datei vor, werden die Screens nicht
   angefordert, sondern selbst herausgeholt** – sie stecken ja drin. Wie,
   steht in Schritt 1 unter „Figma-Datei als Quelle" (Klon-Export für
   gedrehte Collagen). Ein Deck ohne Projekt-Screens, obwohl eine Figma-Datei
   mit den Screens vorlag, kam genau so als Rückmeldung zurück. Die Bitte an
   den Kandidaten bleibt der Rückfallweg für alles, was auch in der
   Figma-Datei nur als angeschnittene Bitmap liegt.

   Dazu, falls vorhanden, je Kunde ein Foto der Firmenzentrale. Findet sich
   keins, sucht der Skill selbst eins (Schritt 5).

5. **Ein paar Sätze über jeden Kunden**, zwei bis drei Absätze: was die Firma
   macht, für wen, wie groß sie ist. Die rechte Spalte der Projekt-Kopfseite
   trägt genau diesen Text (`kunde_text`), und sie ist 693 pt breit – ein gutes
   Drittel der Folie. In den Referenzportfolios steht dort immer Text; eine
   weiße Kundenspalte liest sich wie ein vergessenes Feld.

   Danach fragen, weil es sonst niemand mitschickt – aber **nicht darauf
   warten**: Kommt vom Kandidaten nichts, recherchiert der Skill den Text
   selbst im Netz. Das ist die vierte Ausnahme von der Übernahme-Regel, und sie
   hat eine feste Quellenkette: die Selbstdarstellung des Kunden (Über uns,
   Presse, LinkedIn-Unternehmensseite), dann Wikipedia. Aus dem, was dort
   steht, werden zwei bis drei kurze Absätze – wer die Firma ist, was sie tut,
   für wen, und was die im Projekt betroffene Plattform oder das Produkt ist.
   Jede Zahl (Mitarbeiter, Standorte, Gründungsjahr) steht nur da, wenn sie in
   einer der Quellen steht, und die Quellen kommen je Kunde in die Übergabe.
   **Woher der Text nie kommt**: aus dem, was ein Modell über die Firma zu
   wissen glaubt – recherchiert wird mit Websuche, nicht aus dem Gedächtnis.
   Leer bleibt die Spalte nur noch, wenn auch das Netz nichts hergibt, etwa
   bei einem anonymisierten Kunden.

   Rote Flagge: Du schreibst gerade einen Kundentext ohne offene Quelle neben
   dir. Dann steht auf einer Kundenseite eine Beschreibung dieses Kunden, die
   niemand belegt hat – und der Kunde liest sie.

### 1. Eingang auslesen

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py portfolio.pdf arbeit/
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py lebenslauf.pdf arbeit/cv/
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py linkedin.pdf arbeit/li/
```

Schreibt `text.txt`, legt alle Bilder in Originalauflösung nach `bilder/`,
Porträtkandidaten (Graustufen, aufs Layoutformat beschnitten) nach `fotos/` und
bewertet in `bilder.txt` jede Auflösung gegen die Zielflächen.

Bei einer **Portfolio-Website** die Startseite und die Projektseiten abrufen und
die Bilder von dort ziehen. Im Browser-Chat blockt der Proxy fremde Domains –
dann den Nutzer um einen PDF-Export der Seiten bitten.

#### Figma-Datei als Quelle

Kommt das Material als **Figma-Link**, ist die Figma-MCP-Anbindung der Weg –
nicht der Browser, der ohne Login nur einen eingeschränkten Viewer zeigt:

- **Struktur**: `get_metadata` ohne nodeId listet die Seiten, mit nodeId die
  Folien-Frames samt IDs. `use_figma` (read-only) listet auch das, was
  `get_metadata` an großen Knoten abschneidet.
- **Texte**: je Folie ein `get_screenshot` in hoher Auflösung
  (`maxDimension` großzügig) und abschreiben. Kleingedrucktes vor dem
  Abschreiben ausschneiden und vergrößern – so fallen Tippfehler im Material
  auf, statt ins PDF zu wandern.
- **Bilder**: `download_assets` je Folie liefert `rawImages` – die
  Original-Uploads in voller Auflösung (Profilfoto, Fotos, Bitmap-Screens) –
  und `svgAssets` (Logos, Wortmarken).
- **Screens, die als Vektor-Frames liegen**: In den Vorlagen liegen die
  App-Screens oft gedreht und überlappend in Collagen, am Folienrand
  angeschnitten. **Nie den gedrehten Verbund exportieren** – der Export
  backt Drehung und Beschnitt ein, und zurückrechnen lässt sich das nicht.
  Stattdessen mit `use_figma` je Screen-Frame einen Klon anlegen
  (`clone()`, `rotation = 0`, an eine freie Stelle der Seite), den Klon per
  `download_assets` mit Scale 2–3 exportieren und **hinterher löschen**.
  Das braucht Schreibzugriff auf die Datei; fehlt er, die Screens beim
  Kandidaten als Originalexporte anfordern – ein Screen je Datei.

**Zwei Dinge, die `extract_input.py` nicht wissen kann:**

- **Nicht jeder Porträtkandidat ist der Kandidat.** Ein bestehendes
  New-Monday-Portfolio führt auf der letzten Seite das Foto des Ansprechpartners
  – das Skript meldet es als Kandidat. Jeden Vorschlag ansehen, bevor einer ins
  Dokument geht.
- **Bilder sind unsortiert.** Welches Bild zu welchem Projekt gehört, ergibt
  sich aus der Seitenzahl im Dateinamen (`s14-07.jpg` = Seite 14) und dem Text
  dieser Seite.

**Das Profilfoto** kommt aus dem Lebenslauf, sonst aus dem Portfolio, sonst vom
Kandidaten. Der LinkedIn-Export zählt hier nicht als Quelle – im PDF steht das
Profilbild fast nie mit drin, und die Suche danach kostet nur Zeit. Liegt kein
Lebenslauf bei, ist die Bitte darum (Schritt 0) der kürzere Weg als eine eigene
Anfrage nach einem Foto. Es wird **immer entfärbt** – das macht das Layout
selbst.

### 2. Die drei Quellen zusammenführen

- **Bei Widersprüchen gewinnt das Portfolio**, danach der Lebenslauf, zuletzt
  LinkedIn. Ohne Rückfrage – aber die Abweichung kommt mit beiden Werten in die
  Übergabe. Manche sind Tippfehler, die jemand korrigieren möchte.
- **Firmennamen in der vollständigen Form aus LinkedIn**, auch wenn das
  Portfolio sie kürzt: "Yareto GmbH" statt "Yareto". Das ist kein Widerspruch,
  sondern die genauere Schreibweise – und in ein Kundendokument gehört die
  vollständige Firmierung. Gilt nur für den Namen.
- **Anonymisierte Kunden bleiben anonym.** Nennt der Lebenslauf einen Kunden
  bewusst nur als Gattung ("ein Versicherer"), das Portfolio ihn aber beim
  Namen, ist das keine Lücke, sondern eine Entscheidung. In die Übergabe damit,
  nicht stillschweigend auflösen.
- **LinkedIn-Artefakte ignorieren**: "Top-Kenntnisse" dort ist algorithmisch
  erzeugt, Ortsangaben kommen teils lokalisiert zurück, freiberufliche Stationen
  stehen oft jahrelang auf "Present".

### 3. Die zweite Frage-Nachricht — alles, was vor der JSON offen ist

Eine einzige `AskUserQuestion`, gestellt **nach** dem Auslesen und **vor** dem
Bauen. Vier Fragen passen hinein:

1. **Welche Projekte, in welcher Reihenfolge?** `multiSelect`. Vorgeschlagen
   werden die drei bis fünf mit der besten Beleglage – genug Text **und** genug
   Screens für eine Abschlussseite. Die Reihenfolge ist nicht chronologisch,
   sondern nach Stärke: das überzeugendste zuerst.
2. **Welche Projekte sind vertraulich (NDA)?** `multiSelect`, nur wenn es
   plausible Kandidaten gibt. Siehe unten.
3. **Das Statement für Seite 4**, falls im Material keins steht – siehe unten.
4. **Welche KI-Werkzeuge nutzt der Kandidat?** `multiSelect`, nur wenn das
   Material keine nennt. Die Logos auf Seite 10 behaupten, dass jemand mit
   genau diesen Werkzeugen arbeitet. Den Text der Folie darf der Skill notfalls
   selbst schreiben, die Werkzeugliste nicht. Weiß es niemand, bleibt die
   Kachelreihe leer.

**Der Cover-Titel stand hier früher mit in der Liste.** Von den fünf Kandidaten
hat er den schwächsten Anspruch auf einen Platz: Er folgt aus der Rolle, steht
auf genau einer Zeile, und wer ihn anders will, sagt ein Wort und bekommt das
PDF neu. Ein fehlender NDA-Vermerk, ein erfundenes Statement und eine erfundene
Werkzeugliste kosten mehr als einen zweiten Lauf. Also wird `cover_titel` aus
`rolle` abgeleitet – die zweite der fünf Ausnahmen oben – und in der Übergabe
genannt.

**Bis die Antworten da sind, wird nicht gebaut.** Ein Projekt nachträglich
herauszunehmen heißt, Seitenzahlen und Bildzuordnungen noch einmal
durchzugehen.

### 4. Daten strukturieren

Aus dem Material eine `portfolio.json` bauen. Beispiel mit echten Inhalten:
`beispiel/portfolio.json`. Es zeigt jedes Feld, aber nicht jede Menge: Im Skill
liegen nur zwei Projekte mit je zwei Screens, und der Lauf sagt das auch. Das
Beispiel ist die Vorlage für die Form, nicht für den Umfang – der steht in der
Tabelle unten.

```json
{
  "sprache": "de",
  "person": {
    "name", "rolle", "cover_titel", "jahr", "foto", "erfahrung_jahre",
    "top_kenntnisse": [3], "kenntnisse": [7-8],
    "sprachen": [{ "sprache", "niveau" }],
    "links":    [{ "titel", "url" }],
    "statement_rolle", "statement": { "text", "zitat": true },
    "ki": { "text", "tools": [] }
  },
  "kunden":  [{ "name", "logo" }],
  "prozess": [{ "titel", "kurztext", "langtext" }],
  "projekte": [{
    "kunde", "projektname", "logo", "markenfarbe", "projekt", "kunde_text",
    "rolle": [], "nda": false,
    "summary":   { "text", "bild" },
    "loesungen": [{ "titel", "text", "punkte": [], "screens": [] }],
    "screens": []
  }]
}
```

`projektname` ist die große Überschrift der Kopfseite – in den Vorlagen steht
dort der Name der Anwendung ("Prectavi", "Samsung Circle", "NMVS Core"), nicht
der Kunde: der steht schon als Logo darüber. Wie jedes andere Feld wird er
übernommen, nicht ausgedacht; nennt das Material keinen, bleibt er weg und die
Seite trägt den Kundennamen. Zwei Projekte beim selben Kunden sind dann
allerdings über ihre Überschrift nicht zu unterscheiden – das ist der Moment,
den Projektnamen beim Kandidaten zu erfragen.

`logo` nimmt einen Dateinamen **oder eine Liste**: Projekte mit mehreren
Auftraggebern („Postbank, FYRST", „Opel, Peugeot und Citroën") führen alle
Marken nebeneinander auf der Kopfseite – so stehen sie auch in den Showcases
der Kandidaten. Ein einzelnes Logo, wo der Kundenname mehrere Marken nennt,
liest sich wie ein Versehen; genau das kam als Rückmeldung zurück. Die
Markenfarbe liest `markenfarbe.py` bei einer Liste aus dem **ersten** Logo.

`summary.bild` ist das **Foto der Firmenzentrale des Kunden**, nicht mehr ein
Projektbild. `loesungen[].screens` sind die Screens, die auf der markenfarbenen
Fläche der jeweiligen Lösungsseite fliegen, `projekte[].screens` die der
randlosen Abschlussseite. Ältere Dateien mit `projekte[].bild` oder
`loesungen[].bild` laufen weiter – die Felder werden ignoriert.

**Textlängen — was eine Fläche trägt.** Die Werte sind aus den bestehenden
Portfolios gemessen und am fertigen PDF nachgeprüft. Das Renderskript misst
ebenfalls nach und meldet Überlauf, aber es ist billiger, gleich in der
Größenordnung zu bleiben:

| Feld | Umfang |
|---|---|
| `cover_titel` | eine Zeile, bis ~30 Zeichen |
| `rolle` | bis ~40 Zeichen |
| `top_kenntnisse` | **genau 3**, je 1–4 Wörter |
| `kenntnisse` | **6 bis 7** Einträge, je bis ~45 Zeichen – die Karte braucht Luft zur Top-Kenntnisse-Karte |
| `sprachen` | **alle aus dem Material** – bei Platznot gleiche Niveaus zusammenfassen, siehe unten |
| `links` | alle beruflichen Auftritte – Portfolio-Website zuerst, siehe unten |
| `statement.text` | 20–40 Wörter |
| `prozess[].titel` | 1–3 Wörter |
| `prozess[].kurztext` | 12–25 Wörter |
| `prozess[].langtext` | 60–110 Wörter, zwei Absätze – bei mehrzeiligem `titel` weniger |
| `ki.text` | 50–80 Wörter, zwei Absätze, **ohne `**fett**`** – darunter steht die Werkzeugreihe |
| `ki.tools` | bis 6 Logos – was darüber steht, zeigt die Seite nicht |
| `projektname` | 1–3 Wörter, eine Zeile – nur aus dem Material, sonst weglassen |
| `projekt` | 55–75 Wörter – die Spalte trägt darunter auch „Meine Rolle", siehe unten |
| `kunde_text` | bis ~100 Wörter – volle Spaltenhöhe, siehe unten |
| `projekte[].rolle` | **1–3 Rollenbezeichnungen, keine Aufgaben** – siehe unten |
| `summary.text` | 40–90 Wörter |
| `loesungen[].titel` | 5–8 Wörter, höchstens zwei Zeilen – nur aus dem Material |
| `loesungen[].text` | 50–130 Wörter, alternativ 2–4 `punkte` |
| `loesungen[].screens` | 1 bis 3 Desktop-Screens, bei Mobile bis 6 – der erste ist der Hero |
| `projekte[].screens` | 2 bis 6 Desktop-Screens, bei Mobile bis 8 – der erste ist der Hero |

Jede weitere Zeile im `prozess[].titel` schiebt den Langtext um 115 pt nach
unten – vier Zeilen, rund 30 Wörter. Gemessen trägt die Spalte unter „Analyse"
gut 145 Wörter, unter dem zweizeiligen „Qualitative User Tests" 115 und unter
einem dreizeiligen Titel 80. Auf der KI-Folie endet der Text über der
Werkzeugreihe, nach rund 80 Wörtern; die Kacheln stehen fest bei 80 pt, egal
wie viele es sind – eine frühere Fassung ließ wenige Kacheln wachsen, und
genau das sah gegen die Referenz verrutscht aus.

**Keine Sprache fliegt raus.** `sprachen` führt jede Sprache, die im Material
steht – eine gestrichene Sprache ist eine stille Kürzung des Profils, und
genau die kam als Rückmeldung zurück (Französisch fehlte auf Seite 2). Die
Sprachen-Karte wächst seit dem mit, aber die rechte Spalte der Profilseite ist
endlich: Ab vier Einträgen gleiche Niveaus zu einer Zeile zusammenfassen, so
wie es die Kandidaten in ihren eigenen Decks tun – `{"sprache": "Deutsch,
Italienisch", "niveau": "Muttersprache"}`. Das Renderskript warnt, wenn die
Spalte unten aus der Folie läuft; die Antwort darauf ist Zusammenfassen, nie
Streichen.

**`links` führt alle beruflichen Auftritte aus dem Material** – die
Portfolio-Website zuerst, dann LinkedIn, dann Xing oder Dribbble, wenn sie im
Material stehen. Wer ein eigenes Portfolio betreibt, wird darüber gefunden;
eine Connect-Karte, die nur LinkedIn zeigt, unterschlägt den stärksten Link –
auch das kam als Rückmeldung zurück. Passwortgeschützte Portfolios stehen
trotzdem drin: Der Kunde fragt das Passwort beim Kandidaten an.

**Auf der Kopfseite trägt die linke Spalte zwei Blöcke.** `projekt` und
`kunde_text` stehen in zwei gleich breiten 575-pt-Spalten wie in der Referenz
(Paul Hecker, p-13/18/23). „Meine Rolle" folgt dem Textfluss der linken
Spalte, direkt unter dem Projekttext – nicht mehr an der Blattkante: Der
Block, der von unten nach oben wuchs, klebte bei kurzen Texten sichtbar allein
am Rand, und genau das kam als Rückmeldung zurück. Die rechte Spalte gehört
ganz dem Kundentext. Gemessen, bei einzeiligem Projektnamen und drei Absätzen:

| Feld | Platz |
|---|---|
| `kunde_text` | bis ~100 Wörter (volle Spalte) |
| `projekt` bei 1 Rollen-Stichpunkt | bis ~75 Wörter |
| `projekt` bei 2 Stichpunkten | bis ~65 Wörter |
| `projekt` bei 3 Stichpunkten | bis ~60 Wörter |

Eine Zeile fasst sechs bis sieben Wörter, jede Leerzeile zwischen Absätzen
belegt selbst eine. Bricht der Projektname auf zwei Zeilen um, gehen in beiden
Spalten drei Zeilen ab; ein Stichpunkt, der selbst umbricht, kostet noch eine.
In den Referenzportfolios tragen die Spalten 55 bis 80 Wörter – wer sich daran
hält, bleibt automatisch im Maß.

**„Meine Rolle" nennt Rollen, keine Aufgaben – höchstens drei.** In den
Referenzen steht dort eine Berufsbezeichnung („Lead UI/UX Designer",
„Operational UI Designer, Content Designer"), nicht eine Liste von
Tätigkeiten. „Prototyping", „Usability Testing" oder „Stakeholder-Management"
sind Aufgaben: Sie gehören in den Projekttext oder in die Kenntnisse der
Profilseite, nicht unter dieses Label – sechs solcher Stichpunkte lesen sich
wie ein zweites Skill-Set und drücken beide Textspalten zusammen. Die Rolle
kommt aus dem Material: aus der Projektbeschreibung („Als Lead UX Designer
habe ich …"), sonst aus der Stationsbezeichnung im Lebenslauf oder LinkedIn zu
diesem Zeitraum. Nennt das Material nur Aufgaben, steht dort die eine Rolle
aus der Station – und die Aufgaben bleiben im Fließtext. Das Renderskript
meldet mehr als drei Einträge.

Absätze werden durch **eine Leerzeile** im Text getrennt. `**fett**` setzt
Halbfett und wirkt in allen Fließtexten, Stichpunkten und Kartenzeilen – auch in
`kenntnisse`, `top_kenntnisse` und den Rollen-Stichpunkten. Nicht in
Überschriften, nicht in `sprachen` und `links`: dort stehen die Sternchen sonst
im PDF.

Bricht eine 96-pt-Überschrift nicht um, weil sie aus einem langen Wort besteht,
gehört ein weicher Trenner hinein: `"Konzept-\nentwicklung"`. In der
Schrittleiste unten steht das Wort dann wieder zusammen. Braucht ein Titel
trotzdem mehr als drei Zeilen, setzt das Skript ihn kleiner und sagt es – das
ist eine Notbremse, kein Freibrief für lange Titel.

#### Ein Projektblock sind drei bis fünf Seiten

In dieser Reihenfolge, ohne Ausnahme:

1. **Kopfseite.** Kundenlogo – bei mehreren Auftraggebern alle Logos
   nebeneinander, `logo` als Liste –, Projektname, darunter zwei gleich breite Spalten
   `projekt` und `kunde_text`, unten links `rolle` als Stichpunkte. **Kein
   Bild.** Die beiden Spalten teilen sich die Fläche, die früher das
   Aufmacherbild hatte – deshalb darf der Kundentext jetzt ausführlich sein.
2. **Summary.** Rechts das Foto der Firmenzentrale (`summary.bild`), links
   `summary.text`. Das Gebäude ist der einzige Ort im Dokument, an dem der Kunde
   selbst zu sehen ist; ein Stockfoto vom Schreibtisch gehört nicht dorthin.
3. **Null bis zwei Lösungsseiten.** Rechts die Markenfarbe mit den Screens aus
   `loesungen[].screens`, links `titel` als fette Einleitungszeile – fehlt er,
   steht dort das Label „Die Lösung" –, darunter `text` und `punkte`.
4. **Abschlussseite.** Randlos die Markenfarbe über die ganze Folie, darauf die
   Screens aus `projekte[].screens`. Kein Text außer Wortmarke, Seitenzahl und
   – falls gesetzt – dem NDA-Hinweis.

Wer wenig Material hat, lässt die Lösungsseiten weg, nicht die Abschlussseite.
Sie braucht nur Bilder, und Bilder sind das, was ein Portfolio ohnehin hat. Auch
zwei Screens füllen die Folie – sie stehen in der Kaskade ohnehin groß und
zeigen jede Unschärfe. Das mitgelieferte Beispiel ist genau dieser Fall.

#### Die Einleitungszeile der Lösungsseite steht im Material oder nirgends

`loesungen[].titel` ist die fette Zeile über dem Lösungstext. Sie kommt aus dem
Material: die Überschrift, die im Portfolio über diesem Abschnitt steht, die
Zwischenzeile der Case-Study, der Titel der Projektseite. Steht dort keine,
**bleibt das Feld weg**. Dann setzt das Layout das Label „Die Lösung" ein, so
wie es in den älteren Portfolios steht. Das ist kein Notbehelf, sondern der
Normalfall.

Was verboten ist: den Lösungstext darunter zu einer Zeile verdichten. Das ist
Zusammenfassen, und Zusammenfassen steht ganz oben auf der Liste der Dinge, die
dieser Skill nicht tut. Die Zeile steht fett über dem Absatz und liest sich wie
das Ergebnis des Projekts – wer sie formuliert, behauptet etwas über die Arbeit
eines anderen.

Rote Flagge: Du liest den Lösungstext und suchst darin den Kern für die
Überschrift. Dann gibt es keine, und das Feld bleibt leer.

#### Die KI-Folie

Seite 10 heißt „KI-Einsatz" und trägt `ki.text` sowie die Werkzeuglogos aus
`ki.tools`. Der Inhalt kommt **zuerst aus dem Material**: Tool-Listen in den
Projekten nennen oft ChatGPT, Copilot oder Midjourney, Selbstbeschreibungen auf
Website und LinkedIn beschreiben manchmal den eigenen Umgang mit KI. Steht dort
ein fertiger Text, wird er übernommen wie jeder andere auch. Trägt das
Material nur Bruchstücke – eine Tool-Liste, ein KI-Zertifikat, einen halben
Satz –, wird der Text daraus **erweitert**: die belegten Fakten bleiben
wörtlich, der Skill verbindet sie nach den Regeln unten.

Eine Formregel zu dieser Folie: **`ki.text` bleibt mager** – `**fett**` wird
dort nicht gesetzt, das Renderskript entfernt die Marken; markierte Halbsätze
lasen sich auf dieser Seite wie Werbeclaims, und die Referenzen kennen dort
keinen Fettdruck. Ein `ki.kurztext` aus älteren Dateien wird ignoriert – er
füllte einmal eine vierte Prozessspalte, die es nicht mehr gibt.

Steht dort nichts, **schreibt der Skill den Text selbst**. Das ist die erste der
fünf Ausnahmen ganz oben, und weil es eine Ausnahme ist, hängt sie – wie das
Erweitern – an zwei Bedingungen, die beide gelten müssen:

- **Der Text bleibt allgemein.** Er beschreibt eine Haltung zu KI im
  Designprozess – Beschleunigung, kritische Prüfung, Verantwortung bleibt beim
  Menschen. Er nennt kein Projekt, keine Zahl und keinen Kunden. Werkzeuge nennt
  er nur, wenn sie im Material stehen oder in Schritt 3 bestätigt wurden – der
  Text erfindet keine dazu.
- **Er wird in der Übergabe als erweitert oder selbst formuliert
  gekennzeichnet**, mit der Bitte um Freigabe. Wörtlich etwa: „Den Text auf
  der KI-Folie habe ich selbst formuliert, im Material stand nichts dazu –
  bitte einmal freigeben oder ersetzen."

Rote Flagge: Du hast einen KI-Text geschrieben und die Übergabe erwähnt ihn
nicht. Dann steht im Portfolio eines echten Menschen ein Satz, den er nie gesagt
hat, und niemand weiß es.

#### Das Statement auf Seite 4

Steht im Material ein Zitat, ein Leitsatz oder ein Über-mich-Absatz, wird er
übernommen (`"zitat": true` setzt die »Anführungszeichen«). Steht dort nichts,
**wird keins geschrieben**. Dann in Schritt 3 danach fragen – ein Satz über die
eigene Haltung ist nichts, was jemand anders für einen Kandidaten formuliert.
Kommt keiner, bleibt die Fläche leer; das Layout trägt das.

`statement_rolle` ist die große Rollenzeile links, mit `\n` von Hand umbrochen:
`"User\nInterface &\nExperience\nDesigner"`.

#### Der Design-Prozess sind genau drei Schritte

Seite 6 zeigt die drei Schritte nebeneinander, die Seiten 7 bis 9 je einen im
Detail – dieselben Titel, in derselben Reihenfolge. Die Inhalte kommen aus dem
Material des Kandidaten, in dieser Kaskade:

1. **Übernehmen.** Steht im Material ein fertiger Prozess – ein Prozesskapitel
   im Portfolio, eine Selbstbeschreibung auf der Website, ein Über-mich-Teil –,
   wird er übernommen wie jeder andere Text.
2. **Erweitern.** Steht dort nur Halbes – ein Dreiklang im Profiltext („Von
   Discovery und Konzept bis zur Umsetzung"), verstreute Sätze zur
   Arbeitsweise in CV oder LinkedIn –, werden Titel und Texte daraus
   aufgebaut: die wörtlichen Sätze zuerst, dann so viel eigene Verbindung wie
   nötig, bis Kurz- und Langtext die Maße aus der Tabelle tragen.
3. **Ableiten.** Erst wenn auch das fehlt, leitet der Skill die drei Schritte
   komplett selbst ab – aus dem, was Projekte und Werdegang über die
   Arbeitsweise zeigen.

Nie richtig ist ein PDF mit Platzhaltern auf den Prozessseiten, solange CV
oder LinkedIn eine Selbstbeschreibung hergeben – genau so ein Deck ging einmal
raus, und die Rückmeldung kam prompt. Jeder erweiterte oder abgeleitete
Prozesstext wird in der Übergabe gekennzeichnet, mit der Bitte um Freigabe.
Die drei Bilder dazu liegen fest im Skill und bleiben in jedem Portfolio
gleich.

Seite 10 („KI-Einsatz") hängt hinter den drei Detailseiten, ist aber **kein
vierter Schritt** und gehört nicht in `prozess`: KI läuft in allen Phasen mit,
und als letzte Station dargestellt sah sie aus wie eine Phase nach der
Umsetzung – genau das kam als Rückmeldung zurück. Deshalb bleibt Seite 6
**immer dreispaltig**, die Schrittleiste der Seiten 7–9 zählt drei Balken, und
die KI-Seite trägt gar keine: Sie ist eine eigene Arbeitsweise-Seite, kein
Prozessschritt.

### 5. Logos zuordnen

**Das läuft in einem Durchgang, nicht Firma für Firma:**

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/logos_ergaenzen.py portfolio.json
python3 ${CLAUDE_SKILL_DIR}/scripts/logos_ergaenzen.py portfolio.json --domains domains.json
```

Das Skript geht die Kundenwand, jedes Projekt ohne `logo` **und die
Werkzeugreihe der KI-Folie** durch, sucht in der gemeinsamen Bibliothek und
dann in der Quellenkette und trägt den Dateinamen direkt ein. In
`person.ki.tools` dürfen deshalb bloße Werkzeugnamen stehen („ChatGPT",
„Claude", „Midjourney") – sie werden gegen echte SVGs aufgelöst.

**Projekte mit mehreren Auftraggebern befüllt der Durchgang nicht**: Er
meldet sie als offen, denn ein kombinierter Kundenname („Postbank & FYRST")
ist keine Firma, die eine Datenbank kennt. Dort die Marken einzeln suchen
(Bibliothek, `add_logo.py`, Websuche) und `logo` von Hand als Liste
eintragen.

**Die Werkzeugreihe zeigt immer das Originallogo in Originalfarben als SVG –
und zwar die reine Bildmarke, nicht die Wort-Bild-Marke.** In der kleinen
Kachel wird ein Schriftzug unlesbar; genau so ein Logo (Perplexity mit
Schriftzug) kam als Fehler zurück. Führt die Bibliothek nur die
Wort-Bild-Marke, die Bildmarke aus der Originaldatei freistellen (der
Icon-Pfad steckt meist darin – das ist kein Nachzeichnen) oder die
Icon-Variante im Netz suchen. Kachelgröße und Kästen bleiben, wie sie sind. Simple Icons führt praktisch
jedes KI-Werkzeug, liefert aber grundsätzlich einfarbig Schwarz – das genügt
nur für Marken, die selbst schwarz auftreten (ChatGPT, Midjourney,
ElevenLabs). Für farbige Marken (Claude, Gemini, Perplexity …) gehört die
farbige Original-Variante in die Bibliothek – Wikimedia Commons oder die
Brand-Seite des Anbieters –, und die Kachelreihe wird wie die Firmenlogos
gerastert und angesehen, bevor das PDF rausgeht. Genau diese Reihe stand
einmal komplett schwarz im Deck, während die Firmenlogos längst farbig waren.

**Werkzeug- und Firmenlogos werden nie selbst gezeichnet.** Ein aus dem
Gedächtnis nachgebautes SVG sitzt verschoben in der Kachel und stimmt im
Detail nicht – genau so kamen die Werkzeuglogos der KI-Folie als Fehler
zurück. Was die Kette nicht findet, wird im Netz gesucht (`<Tool> logo svg`)
und mit `add_logo.py` abgelegt. Rote Flagge: Du schreibst gerade `<svg>` oder
`<path>` von Hand. Dann fehlt die Quelle – Websuche.

**Kommt die Kette leer zurück, suchst du selbst weiter — im Web.** Die
Quellenkette hat fünf Datenbanken abgefragt, nicht das Netz. Deutsche Agenturen
und Mittelständler stehen in keiner davon; ihr Logo liegt auf ihrer eigenen
Presseseite. **Für jede offene Firma mindestens eine Websuche**, bevor du sie
als fehlend meldest – in dieser Reihenfolge:

1. `<Firma> Logo SVG`, `<Firma> Logo download`
2. `<Firma> Presse`, `<Firma> Media Kit`, `<Firma> Markenrichtlinien`
3. Die Firmenseite selbst: Presse, Über uns, Impressum. Das Logo im Seitenkopf
   ist oft ein SVG, das sich direkt laden lässt.

Zwei Funde reichen: die **Domain** (dann in `domains.json` eintragen und
`--domains` noch einmal laufen lassen) oder die **Bild-URL**:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/add_logo.py "https://firma.de/presse/logo.svg" firma
python3 ${CLAUDE_SKILL_DIR}/scripts/add_logo.py ~/Downloads/firma.svg firma
```

`add_logo.py` bessert zu kleine Logos selbst auf: unter 242 px Höhe prüft es, ob
das Bild zweifarbig ist, und vektorisiert es dann über potrace. Wenn nicht, wird
nur hochgerechnet – das glättet, erzeugt aber keine Details, und das Skript sagt
das auch.

Rote Flagge: Du schreibst gerade "Folgende Logos fehlen" und hast in diesem Lauf
keine einzige Websuche gemacht. Dann zurück nach oben.

Danach zu prüfen:

- **Neu gefundene Logos ansehen.** Die Suche trifft manchmal eine gleichnamige
  Firma oder ein abgelegtes Altlogo.
- **Logos in Originalfarben.** Nichts wird entfärbt oder ans Layout angeglichen.
  Die automatische Suche liefert oft die schwarze Variante, auch wenn die Marke
  farbig ist – dann die farbige von der Markenseite nachlegen. Einfarbig bleibt
  ein Logo nur, wenn die Marke selbst einfarbig auftritt (Opel, Peugeot).
  **Das gilt ausdrücklich auch für Treffer aus der Bibliothek**: Sie führt aus
  CV-Läufen einfarbige Bestände – ein schwarzes DATEV lag dort, die Marke ist
  grün, und genau so ging es aufs Kundenwand-PDF. Deshalb vor dem Rendern die
  ganze Wand rastern und ansehen: Jede schwarz gerenderte Marke gegen ihren
  echten Auftritt prüfen (Websuche oder Markenseite), die farbige Fassung mit
  `add_logo.py` nachlegen – sie ersetzt den Bibliothekseintrag dauerhaft, damit
  der nächste Lauf sie gleich bekommt.
- **Fehlt ein Logo, entfällt sein Platz auf der Wand** – die übrigen rücken
  zusammen, die Projektseite rendert ohne. Deshalb gehört jedes offene Logo in
  die Übergabe, damit jemand es nachliefern kann.

#### Fotos der Firmenzentralen

Im selben Durchgang, wenn `summary.bild` bei einem Projekt fehlt:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/hq_bilder.py portfolio.json
python3 ${CLAUDE_SKILL_DIR}/scripts/hq_bilder.py portfolio.json --setzen
python3 ${CLAUDE_SKILL_DIR}/scripts/hq_bilder.py portfolio.json --quelle
python3 ${CLAUDE_SKILL_DIR}/scripts/hq_bilder.py "Deutsche Bank" --zweites
python3 ${CLAUDE_SKILL_DIR}/scripts/hq_bilder.py --selbsttest
```

`--zweites` arbeitet im Firmen-Modus (mit dem Firmennamen als Argument), nicht
im JSON-Modus – dort wird das Flag ignoriert.

Das Skript sucht je Kunde ein Foto der Firmenzentrale (Wikimedia, Wikipedia) und
legt es in einer eigenen Bibliothek neben den Logos ab, damit es beim nächsten
Portfolio mit demselben Kunden schon da ist. Mit `--setzen` trägt es den Pfad
als `summary.bild` ein.

**Zwei Projekte beim selben Kunden brauchen zwei Motive.** Sonst steht dasselbe
Haus zweimal im Deck, und es liest sich wie ein Versehen. `--zweites` sucht um
die schon belegten Bilder herum, in der Bibliothek wie im Netz; die zweite Datei
heißt `hq-<firma>-2.jpg` und gehört so ins `material/`. Findet sich kein zweites
Motiv, bleibt es beim ersten – eine leere Seite wäre schlechter – und das Skript
meldet es unter „Zweimal dasselbe Haus". `--selbsttest` prüft ohne Netz, ob die
Namensprüfung noch trägt (Mutterkonzern, Autohaus, gleicher Ortsname); nach
Änderungen an der Suche gehört er dazu.

**Das Ergebnis ist ein Vorschlag, kein Befund** – genau wie bei der Markenfarbe.
Firmennamen wiederholen sich, Bildunterschriften lügen, und ein fremdes Gebäude
auf einer Kundenseite fällt jedem auf, der beim Kunden arbeitet. Also jedes
gefundene Foto ansehen – und dabei zwei Fragen stellen:

- **Ist es das richtige Gebäude?** Der Sitz der Firma, nicht ein Werk, eine
  Filiale oder ein gleichnamiges Haus.
- **Ist es ein ansehnliches Motiv?** Sonne, blauer Himmel, freundliches
  Licht – so stehen die Gebäude in der Referenz (Paul Hecker). Ein grau
  verhangenes, tristes Foto – Regenhimmel, Zaun, Parkplatz im Vordergrund –
  zieht die ganze Summary-Seite runter; genau so ein Motiv stand im
  Freia-Deck. `hq_bilder.py` meidet solche Bilder inzwischen selbst
  (`wirkt_trist`, kalibriert über die Farbsättigung) und warnt, wenn nur ein
  tristes bleibt – dann ein besseres Motiv suchen oder beim Kunden anfragen,
  statt die Warnung zu überlesen.
- **Ist es ein Foto?** Wikimedia führt zunehmend KI-generierte Bilder und
  Renderings, und die Dateinamen-Schranke fängt nur die ehrlich beschrifteten
  ab. Die Merkmale sind bekannt: zu glatte Fassaden, verbogene oder schwebende
  Logos, unmögliche Geometrie, ein Himmel wie lackiert. Ein Bild, das so
  aussieht, gilt **nicht als Foto**: Es fliegt **aus der Foto-Bibliothek
  raus** – die Datei unter `hq/` neben der Logobibliothek löschen, ihren
  Eintrag in `quellen.json` dazu –, denn die Bibliothek führt echte Fotos und
  darf ein Bild, das nur so tut, nicht beim nächsten Kunden-Portfolio als
  Erstwahl wieder ausliefern. Ob es in **diesem** Deck trotzdem stehen darf,
  regelt die Kaskade unten: als gekennzeichnetes KI-Bild ja, als
  vermeintliches Foto nie.

#### Bleibt die Suche leer: KI-Bild generieren, nicht Platzhalter setzen

Eine Summary-Seite ohne Gebäude liest sich wie ein vergessenes Feld – genau
das kam als Rückmeldung zurück. Deshalb gilt für `summary.bild` diese
Kaskade, in dieser Reihenfolge:

1. **Bild aus dem Kandidatenmaterial.** Auch wenn es erkennbar KI-generiert
   ist – der Kandidat hat es für sein eigenes Deck gewählt, es wird
   übernommen und in der Übergabe als KI-Bild genannt. In die Foto-Bibliothek
   wandert es nicht.
2. **Echtes Foto** aus Bibliothek und Netz (`hq_bilder.py`), mit den drei
   Prüfungen oben.
3. **Selbst generieren.** Liefert auch das Netz nichts Brauchbares, wird ein
   KI-Bild erzeugt – mit der Bildgenerierung, die die Umgebung hergibt
   (Bildgenerierungs-Tool oder -Skill). Fotorealistisch, ein plausibles
   Firmengebäude passend zu Branche, Größenordnung und Region; freundliches
   Licht, blauer Himmel – dieselben Maßstäbe wie an ein echtes Motiv. **Ohne
   Firmenschriftzug am Gebäude**: Ein erfundenes Gebäude mit echtem Logo
   behauptet, der Sitz der Firma zu sein – ohne Schriftzug ist es erkennbar
   Illustration. Die Datei heißt `hq-<firma>-ki.jpg`, damit sie nie mit einem
   Foto verwechselt wird, und bleibt im `material/`-Ordner des Laufs, nicht
   in der Bibliothek.

Erst wenn auch keine Bildgenerierung zur Verfügung steht, bleibt der
Platzhalter – dann gehört das Bild in die Nachforderungszeilen der Übergabe.
**Jedes generierte oder aus KI-Material übernommene Bild steht in der
Übergabe**, wörtlich etwa: „Die Gebäude von X und Y sind KI-generiert – im
Netz fand sich kein Foto. Bitte einmal ansehen und freigeben oder ein echtes
Foto schicken."

**`--quelle` gehört zu jedem Lauf, in dem ein Foto verwendet wird.** Es druckt
Datei, Urheber und Lizenz aus der `quellen.json`, die neben den Bildern liegt.
Die Fotos stehen meist unter CC-BY, und CC-BY verlangt eine Nennung – in einem
Dokument, das an Kunden geht, ist das keine Formalie. Der Ausdruck wandert
unverändert in die Übergabe. Steht dort „Herkunft unbekannt", wurde das Bild von
Hand abgelegt: dann vor der Übergabe klären, nicht weglassen.

### 6. Markenfarben der Projekte

Die Lösungs- und die Abschlussseite liegen auf der Farbe des Kunden, auf der
Abschlussseite randlos über die ganze Folie. Das Skript liest sie aus dem
Logo – bei SVGs durch Rastern, damit die Fläche zählt und nicht die Zahl der
Farbangaben im Quelltext:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/markenfarbe.py portfolio.json
python3 ${CLAUDE_SKILL_DIR}/scripts/markenfarbe.py portfolio.json --setzen
```

**Das Ergebnis ist ein Vorschlag, kein Befund.** Ein Logo aus zwei Marken, ein
Farbverlauf oder ein Sekundärton können danebenliegen, und eine falsche
Markenfarbe auf einer Kundenseite fällt sofort auf. Deshalb: die vorgeschlagenen
Werte gegen die Marke gegenprüfen (Presse- oder Brandseite nennt die Hex meist
selbst) und in der Übergabe nennen.

Findet das Skript nichts Farbiges – bei schwarzen Wortmarken der Normalfall –,
gibt es nichts zurück. Dann bleibt `markenfarbe` weg und die Fläche neutral. Das
ist richtiger als ein geratener Ton.

### 7. Rendern

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_portfolio.py portfolio.json ausgabe/nachname-vorname-portfolio.pdf
```

Die Flächen mit den Screens entstehen dabei vorab als Bild –
`scripts/screens.py` legt sie an, aus `loesungen[].screens` für die
Lösungsseiten und aus `projekte[].screens` für die Abschlussseite. Die
Anordnung ist die gestalterische Entscheidung des Skills: eine **diagonale
Kaskade** wie in den Referenzportfolios – wenige, große Screens, alle um
denselben leichten Winkel gekippt (die Kaskade wird als Ganzes genau einmal
gedreht, kein Screen einzeln), diagonal versetzt und an den Kanten
entschlossen angeschnitten: der obere Screen blutet über die obere Kante
hinaus, der untere über die rechte und untere. Keine Browserfenster, keine
Geräterahmen: nur Karten mit leicht gerundeten Ecken und flachem Schatten
auf **satter, dunkler Markenfarbe** – zu helle Töne werden Richtung Schwarz
gezogen, ohne Markenfarbe steht ein dunkles Petrol. Der Grund zeigt sich
als Negativraum der Diagonale; das ist gewollt und keine Lücke. Wortmarke,
Seitenzahl und NDA-Hinweis können auf Screens liegen; unter ihren Ecken
liegt deshalb ein weicher dunkler Verlaufsschleier in der abgedunkelten
Markenfarbe. Die Maße stehen in `references/layout.md`. Das Ergebnis ist
deterministisch und ohne Zufall: derselbe Eingang ergibt dieselbe
Anordnung, ein zweiter Lauf verschiebt also nichts.

Das Skript sucht sich die Engine selbst und prüft danach das fertige PDF. Es
meldet:

- **Textüberlauf.** In einem Folienlayout bricht nichts um. Zu langer Text läuft
  erst über das, was unter ihm steht – auf der Kopfseite über „Meine Rolle" –,
  dann über die Blattkante. Was jenseits der Kante liegt, setzt WeasyPrint in
  die Textebene der **Folgefolie**: dort unsichtbar, aber im PDF auffindbar. Auf
  der Folie fehlen einfach ein paar Sätze, und beim Überfliegen fällt das nicht
  auf. Gemeldet wird jeder Block, der aus seiner Inhaltszone tritt.
- **Zu kleine Bilder**, gemessen gegen die Breite ihrer Fläche in Punkt.
- **Screens, die dieselbe Ansicht zeigen** – die Fläche nimmt sie nur einmal auf
  und sagt, welche sie ausgelassen hat. Dann fehlt ein Screen im Satz.
- **Fehlende Dateien und gesetzte Platzhalter.**
- **Ungewöhnliche Mengen**: weniger als drei oder mehr als fünf Projekte,
  ein Design-Prozess mit anderer Schrittzahl als drei.

**Der Zwischenspeicher liegt neben der `portfolio.json`, nicht beim PDF.** Die
gerechneten Markenflächen landen in `arbeit/screens/`, ein Bild je Lösungs- und
Abschlussseite. Sie sind Arbeitsdateien: Sie sparen dem zweiten Lauf nach einer
Textkorrektur die Rechenzeit, sonst nichts, und dürfen weg. Im Ausgabeordner
liegen sie mit Absicht nicht – der wird weitergereicht, und ein Zwischenspeicher
ginge sonst mit. Zur Größenordnung: Fünf Projekte ergeben rund 6 MB
Zwischenspeicher und ein PDF von rund 12 MB. Das PDF besteht zum größten Teil
aus diesen Flächen; wer es per Mail schickt, prüft vorher die Größengrenze.

**Das fertige PDF ansehen, nicht nur die Meldungen lesen.** Besonders die
Projektseiten: ob auf der Summary-Seite wirklich das Gebäude dieses Kunden
steht, ob es wie ein Foto aussieht und nicht wie ein Rendering und ob es
freundlich wirkt statt grau und trist, ob die Markenfarbe zur Marke passt, ob
das Kundenlogo lesbar ist – und ob auf den Lösungs- und Abschlussseiten von
jedem Screen genug zu sehen ist und jeder scharf steht. Die Screens laufen
über die Kanten und der dunkle Grund zeigt sich zwischen ihnen; beides ist
gewollt – so stehen die Kaskaden in den Referenzen. Nicht gewollt wäre ein
Screen, der klein und frei in der Mitte schwebt, statt an einer Kante zu
hängen: Das ist der Blick, mit dem die alte Fläche als „random rumfliegend“
zurückkam. Screens, die das Qualitäts-Gate ausgelassen hat, stehen in den
Meldungen: Sie gehören mit der Bitte um Originalexporte in die Übergabe.
Eine Lösungs- oder Abschlussseite, die nur Markenfarbe zeigt, ist kein
Fehler, sondern das Gate – dann fehlen scharfe Screens, und genau das steht
in der Übergabe unter „Folgende Bilder fehlen".

```bash
pdftoppm -png -r 60 ausgabe/nachname-vorname-portfolio.pdf arbeit/blick
```

### 8. Übergeben

PDF ausgeben und in wenigen Zeilen berichten:

- Welche Projekte drin sind und in welcher Reihenfolge
- Woher das Profilfoto stammt, falls nicht aus dem Lebenslauf
- Wo die Quellen auseinandergehen – mit beiden Werten
- Welche Markenfarben vorgeschlagen wurden, mit der Bitte um einen Blick
- **Der Bildnachweis der Firmenzentralen**, wörtlich aus `hq_bilder.py --quelle`:
  Datei, Urheber, Lizenz. Dazu die Bitte, die Gebäude anzusehen – und
  **welche Gebäude KI-generiert sind** (selbst erzeugt oder aus dem
  Kandidatenmaterial), mit der Bitte um Freigabe oder ein echtes Foto
- Woher die Kundentexte stammen, wenn sie nicht vom Kandidaten kommen
- Welcher Cover-Titel aus der Rolle abgeleitet wurde
- **Ob KI- oder Prozesstexte erweitert oder selbst formuliert sind**, mit der
  Bitte um Freigabe
- Welche Rechtschreibfehler korrigiert wurden
- Was im Eingang unklar war – als Frage, nicht als stille Annahme

#### Ganz zum Schluss: was zur Vollständigkeit fehlt

Nach allem anderen, als letzte Zeilen, höchstens drei Sätze, **wörtlich** so:

> Folgende Kundenlogos fehlen: Yareto, Brickmakers – einfügen, um Portfolio zu vervollständigen

> Folgende Bilder fehlen: apoBank (Screens), Yareto (Firmenzentrale) – schick sie mir hier in den Chat, dann baue ich das PDF neu

> Profilfoto einfügen, um Portfolio zu vervollständigen

Regeln dazu:

- **Fehlt nichts, steht hier nichts.** Keine Erfolgsmeldung.
- **Erst nach der eigenen Suche.** Eine Firma gehört nur dann in die Zeile, wenn
  Bibliothek, Skript **und** Websuche nichts ergeben haben.
- **Keine Erklärung dazu.** Nicht begründen, nichts vorschlagen, kein "leider".
- Genannt werden **Firmennamen**, nicht Dateinamen.

## Sonderfälle

**Fehlende Bilder.** Der Skill baut alle Seiten und setzt beschriftete
Platzhalterflächen. Das Dokument ist damit vollständig und sofort zu beurteilen,
und es ist eindeutig, was noch fehlt. In der Übergabe steht die Bitte, die
Bilder in den Chat zu schicken – kommen sie, wird die `portfolio.json` ergänzt
und **neu gerendert**, ohne dass irgendetwas anderes noch einmal gefragt wird.

**NDA-Projekte.** Bei jedem Projekt, das vertraulich sein könnte, in Schritt 3
fragen. Ist es vertraulich, wird `"nda": true` gesetzt – dann steht der
Datenschutzhinweis auf den Lösungs- und der Abschlussseite. **Originalscreens
dürfen dann nicht gezeigt werden**: der Kandidat muss eine abgewandelte
Darstellung liefern. Das wiegt jetzt schwerer als früher, weil die
Abschlussseite aus nichts anderem besteht als aus Screens. Also ausdrücklich in
die Übergabe, nicht in eine Fußnote.

**Sehr wenige Projekte.** Unter drei wird es dünn, aber ein Portfolio mit zwei
starken Projekten ist besser als eins mit fünf schwachen. Das Renderskript
meldet die Zahl, verhindert sie aber nicht. Bei nur einem Projekt beim Nutzer
nachfragen, ob das Material vollständig ist.

**Sehr viele Projekte.** Über fünf wird das Dokument zum Katalog. Dann die
stärksten fünf vorschlagen und die übrigen in der Übergabe nennen – wer sie doch
will, sagt es.

**Kein Portfolio, nur Lebenslauf und LinkedIn.** Projekttexte lassen sich daraus
übernehmen, Screens nicht. Der Skill baut das Dokument mit Platzhaltern und
fordert die Screens je Projekt namentlich an. Das Bild der Firmenzentrale
besorgt er selbst – als Foto aus Bibliothek und Netz, sonst KI-generiert nach
der Kaskade in Schritt 5.

## Was fest steht und nicht zur Disposition steht

- **Seitenfolge**: Cover · Profil · Meine Kunden · Statement · Divider ·
  Design-Prozess · Arbeitsweise 1–3 · KI-Einsatz · New Monday Agentur ·
  Divider · Projektblöcke · Divider · Kontakt. Daran wird nicht getauscht.
- **Statische Seiten**: die drei Divider, die Agenturseite und die Kontaktseite.
  Ihr Inhalt kommt aus dem Skript, nicht aus dem Kandidatenmaterial.
- **Ansprechpartner im Footer**: immer Manuel Klein, CCO.
- **Agenturzahlen**: 26 Teammitglieder, gegründet 2018, 100 % Zufriedenheit,
  UX-Design-Awards-Badge. Stehen als Konstanten in `render_portfolio.py` und
  werden dort gepflegt, nicht im Template.
- **Schrift ist Inter**, liegt in `assets/fonts/` und wird eingebettet.
- **Profilfoto immer in Graustufen.**
- **Ein Projektblock hat drei bis fünf Seiten**: Kopf, Summary und Abschluss
  immer, dazu null bis zwei Lösungsseiten je nach Material.
- **Auf den Projektseiten fest**: die Markenfläche (Lösungs- und
  Abschlussseite) und das HQ-Foto der Summary. Die **Anordnung der Screens
  darauf ist dagegen die gestalterische Entscheidung des Skills** –
  `screens.py` setzt sie nach den in `references/layout.md` vermessenen
  Regeln, das Kandidatenmaterial gibt sie nicht vor.
- **Kein Umbau des Layouts.** Neue Rubriken, andere Farben, zusätzliche Seiten:
  nur nach ausdrücklicher Ansage.

## Wenn das Layout doch angefasst werden muss

Maße, Farben, Typoskala und die Begründungen dahinter stehen in
`references/layout.md`. Dort steht auch, warum die Seiten absolut positioniert
sind und welche Fallen WeasyPrint dabei stellt – diese Stelle bitte vor jeder
Änderung lesen.
