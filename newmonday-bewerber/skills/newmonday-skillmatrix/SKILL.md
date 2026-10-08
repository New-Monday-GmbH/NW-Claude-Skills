---
name: newmonday-skillmatrix
description: Erstellt aus Lebenslauf, Portfolio und LinkedIn-Export eine Skill Matrix im New-Monday-Layout, immer in zwei Fassungen als PDF – eine lange, weblayoutartige Seite (1444 breit) und eine kompakte A4-Fassung im Format des Lebenslaufs – mit Hero (Name, Rolle, Verfügbarkeit, Foto), Zertifikaten und nach Kategorien gruppierten Kernkompetenzen mit 1–5-Punkte-Bewertung. Nutze diesen Skill immer, wenn eine Skill Matrix, Skillmatrix, Kompetenzmatrix, Kompetenzübersicht oder ein Skill-Profil erstellt, aufbereitet, vereinheitlicht oder "ins New Monday Layout gebracht" werden soll – auch wenn nur "Skill Matrix für <Name>" mit ein paar PDFs geschickt wird und das Wort "New Monday" gar nicht fällt. Gilt auch, wenn die Skill Matrix zusätzlich in ein Figma-File, als Figma-Frame oder als bearbeitbare Datei für Designer abgelegt werden soll. Für Lebensläufe ist newmonday-cv zuständig, für Portfolios newmonday-portfolio; die Skillmatrix ist das dritte Dokument im Set.
---

# New Monday Skillmatrix

Aus Lebenslauf, LinkedIn-Export und Portfolio wird eine Skill Matrix im
New-Monday-Layout mit Hero, Zertifikaten und bewerteten Kernkompetenzen – in
**zwei Fassungen, immer beide**, aus derselben `skillmatrix.json`:

| Fassung | Format | Wofür |
|---|---|---|
| **lang** | eine einzige Seite, 1444pt breit, so hoch wie der Inhalt | die Webseiten-Ansicht aus dem Figma-Master, Karten mit Schatten |
| **A4** | 595 × 842pt, mehrseitig, Rand, Kopf und Fuß wie im Lebenslauf | zum Drucken und Anhängen; Zeilen statt Karten, 10pt Fließtext |

Beide haben denselben Inhalt – dieselbe Auswahl, Reihenfolge, Bündelung der
Zertifikate und dieselben Texte; nur die Form unterscheidet sich. Die lange
Fassung folgt dem New-Monday-Design-System der Figma-Masterdatei (Seite
„Skillmatrix“), die A4-Fassung dem vom Nutzer abgenommenen Vorschlag
(2026-10-06, Herleitung in `references/layout.md`). Farben, Abstände, Radien,
Schatten und Schriften stehen einmal, in `assets/tokens.json` – die A4-Werte im
Block `a4`. PDF und Figma-Frames lesen beide von dort, und das Renderskript
prüft jedes PDF dagegen. Das Template wird nicht neu erfunden und nicht
"verbessert" – es wird befüllt.

Bester Eingang sind **drei Quellen**: der Lebenslauf als PDF, der
LinkedIn-PDF-Export und das Portfolio (Link oder PDF). Dazu, falls vorhanden,
die Zertifikate als Bilder oder PDFs.

## Die eine Regel, die alles andere schlägt

**Jedes Attribut in der Matrix braucht einen Beleg im Eingang.** Ein Skill
steht nur dann in der Matrix, wenn Lebenslauf, LinkedIn, Portfolio oder ein
Zertifikat ihn hergeben – eine Station, ein Projekt, ein Tool, ein Kurs.
Nichts wird ergänzt, weil es "zum Profil passt" oder "sicher stimmt". Die
Matrix geht an Kunden und behauptet Kompetenzen über einen echten Menschen.

Die einzige Ausnahme sind **Tools, wenn der Eingang gar keine nennt**: Dann
schlägt der Skill in der Freigabe (Schritt 2e) rollentypische Tools vor und
fragt, ob sie ergänzt werden sollen. Ergänzt wird nur mit ausdrücklichem Ja,
und in der Übergabe steht, welche Tools ohne Beleg auf Wunsch aufgenommen wurden.

Zwei Dinge in diesem Dokument sind trotzdem Urteile und keine Zitate – die
**Auswahl** der Attribute und ihre **Bewertung** (1–5 Punkte). Genau deshalb
werden beide dem Nutzer **vor dem Rendern** vorgelegt, mit Beleg, und erst
nach Freigabe gebaut (Schritt 2). Still gesetzt wird keine einzige Zahl.

Für alle übernommenen Texte gilt dieselbe Regel wie im CV-Skill: Inhalte
werden übernommen, nicht umgeschrieben; erlaubt ist nur das Glätten von
Rechtschreibung und Grammatik – dazu gehört die Durchkopplung („UX-Design“,
Schritt 0). Neu formuliert werden ausschließlich die
Hero-Beschreibung und die Karte „Erworbene Qualifikationen“ (nach den Regeln in
Schritt 2c) sowie Beschreibungen für Attribute, die nicht im Katalog stehen
(nach `references/attribute-katalog.md`).

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

**Die A4-Fassung braucht WeasyPrint** (laufende Kopfzeile, gemessener Fuß);
auf dem Ausweichweg über Chrome entsteht nur die lange, und das Renderskript
sagt das.

Für die Figma-Frames (Schritt 4a) braucht es zusätzlich das Figma-MCP-Werkzeug
und ein angemeldetes Konto mit **Bearbeitungsrechten** auf der Zieldatei.
`whoami` sagt, welches Konto verbunden ist – das ist bei Zugriffsfehlern die
erste Frage, nicht die letzte. Fehlt das Werkzeug, entfällt nur der Frame.

## Im Gesamtlauf

Dieser Abschnitt gilt nur, wenn der Auftrag mit „Gesamtlauf
newmonday-bewerbermappe“ beginnt. Dann läuft dieser Skill als Subagent in einer
von zwei Phasen, und der Auftrag bringt die allgemeinen Regeln mit: keine
Rückfragen, Laufordner, `auftrag.json`, die Formate in
`newmonday-bewerbermappe/references/formate.md`. Hier steht nur, was für die
Skill Matrix dazukommt. Wo dieser Abschnitt etwas regelt, geht er dem Rest des
Skills vor; im Einzellauf gilt er nicht.

**Schritt 0 entfällt.** Was er einholt, steht in `auftrag.json`:

| Schritt 0 | aus `auftrag.json` |
|---|---|
| Sprache | `sprache` |
| Figma | Die Frames (lang und A4) entstehen, wenn `figma.aktiv` true ist – eine eigene Frage danach gibt es nicht. `figma.link` trägt die `node-id` der Kandidatenseite, also gilt „Zielseite“ mit `node-id` (`references/figma.md`). |
| Material | `material` – Zertifikate aus dem Ordner `material.zertifikate`; je Datei ein Eintrag, Titel, Aussteller und Datum vom Zertifikat abgelesen, neueste zuerst |
| Verfügbarkeit | wandert in die Fragen der Phase *vorbereiten* |
| Anfrage | `anfrage`, falls der Auftrag eine mitbringt (Schritt 0, Punkt 6); fehlt das Feld, gilt die Reihenfolge ohne Anfrage |

**Phase vorbereiten: Schritte 1 bis 2d.** Statt der Freigabe-Nachricht aus 2e
entsteht `fragen.json`:

- `texte`: was 2e dem Nutzer zeigt, ein Markdown-Block je Punkt – die
  Hero-Beschreibung im Wortlaut (als generiert gekennzeichnet) mit den drei
  Schwerpunkten, die Matrix-Tabelle (Kategorie, Attribut, Punkte, Beleg), die
  Tools-Tabelle (Tool, Punkte, Beleg bzw. „Vorschlag, nicht belegt“), die
  Zertifikatstabelle (Titel, Aussteller, Datum, Bild ja/nein) in der
  Reihenfolge neueste zuerst und die Karte „Erworbene Qualifikationen“ (Satz
  als generiert gekennzeichnet, je Tag das Zertifikat, aus dem es stammt).
  Bündelt `zertifikate.py` wegen Platzmangels (Schritt 3), steht dabei, welche
  Einträge zu welcher Kachel werden.
- `fragen`:
  - `verfuegbar_ab` – Wortlaut und Optionen wie in Schritt 0, Punkt 2.
  - `freigabe` – wie in 2e; die Option „Ich möchte etwas ändern“ trägt
    `"text_noetig": true`.
  - `tools` – nur, wenn der Eingang keine Tools nennt, wie in 2e.
- `luecken`: „Profilfoto“, wenn Schritt 1a bei „beim Kandidaten anfragen“ endet
  oder das beste Foto unter 100 dpi liegt (Folge mit dpi-Zahl); „Zertifikate“,
  wenn Lebenslauf, LinkedIn oder Portfolio Zertifikate nennen, aber keine
  Dateien dazu im Eingang liegen (Folge: die Einträge stehen ohne Bild, mit dem
  Platzhalterfeld).

In `notizen.md`:

- der vollständige Entwurf als JSON-Block im Aufbau der `skillmatrix.json`
  (Schritt 3), mit dem Beleg je Skill und Tool als zusätzlichem Feld `beleg`;
- die Fotoquelle mit Datei, dpi und den beiden Kontrollbildern (lang, A4), und
  ob der Kopf mittig und mit Luft über dem Haar steht;
- jede Abweichung zwischen den Quellen mit beiden Werten.

Jeder Widerspruch zwischen den Quellen kommt außerdem als Eintrag unter
`abweichungen` in `fragen.json` (Aufbau in `formate.md`) – daraus fragt der
Orchestrator einmal, welche Quelle die aktuellere ist. Der Entwurf nimmt bis
dahin die Fassung des Lebenslaufs.

Keine `skillmatrix.json`, nichts rendern.

**Phase bauen: Schritte 3 bis 5**, aus dem Entwurf in `notizen.md` (das Feld
`beleg` fällt dabei weg). Die Antworten stehen in
`entscheidungen.newmonday-skillmatrix`:

- `verfuegbar_ab` → `person.verfuegbar_ab`: `"sofort"` bei „ab sofort“, sonst
  der Monat, wie er dasteht.
- `freigabe`: „Ja, so bauen“ → der Entwurf unverändert. Alles andere ist
  „Ich möchte etwas ändern: <Text>“ – den Text umsetzen, nach denselben Regeln
  wie Änderungen in 2e.
- `tools`: wie in 2e.

Widersprechen sich die Quellen, gilt statt „Bei Widersprüchen gewinnt der
Lebenslauf“ (Schritt 1) die Quelle aus `vorrang` in `auftrag.json`, danach
Lebenslauf, Portfolio, LinkedIn – in allen drei Dokumenten gleich; fehlt
`vorrang`, der Lebenslauf. Weicht der Entwurf dadurch ab (etwa Rolle oder
Erfahrung im Hero), wird er angepasst und die Änderung unter „Zur Freigabe“
genannt.

**Die Tools-Liste gilt auch für den Lebenslauf.** Im Gesamtlauf übernimmt der
Lebenslauf `tools[].name` wörtlich als `skillset.tools` (die Reihenfolge darf
dort abweichen) – Lebenslauf und Skill Matrix führen dieselben Tools. Deshalb
die Namen so wählen, dass sie auch als Listeneintrag im Lebenslauf stehen
können, und eine Änderung an der Liste nach der Übergabe als Grund nennen, den
Lebenslauf neu zu bauen. `pruefe_lauf.py` vergleicht beide Listen.

Schritt 4 rendert beide Fassungen nach `<laufordner>/ausgabe/` – zwei PDFs. Schritt
4a läuft, wenn `figma.aktiv` true ist, und legt beide ab: den langen Frame und
rechts daneben die A4-Seiten. Die Rückgabe nennt beide PDFs und als node-id den
langen Frame und die A4-Seiten. Die Übergabe aus Schritt 5 geht
nach `uebergabe.md`: Hero-Beschreibung und die **endgültige** Matrix-Tabelle
unter „Zur Freigabe“ – nach einer Änderung ist das die einzige Stelle, an der der
Nutzer sie sieht –, Abweichungen unter „Quellen weichen ab“, der Rest unter
„Hinweise“, die Schlusszeilen wörtlich unter „Fehlt noch“.

## Gefragt wird mit Klickboxen, nicht im Fließtext

Wie im CV-Skill: **Jede Frage mit überschaubarer Antwortmenge läuft über
`AskUserQuestion`.** Material (Dateien, Links, Fotos) wird als Text derselben
Nachricht erbeten, Freigaben und Berichte am Ende sind Text. Fragen werden
gebündelt – dieser Skill kommt mit **zwei** Frage-Nachrichten aus: einer vor
dem Auslesen (Schritt 0, drei Klickboxen in einem Aufruf, Material und
Anfrage als Text) und einer als Freigabe
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

   Sie steuert die Rubriken ("Kernkompetenzen" / "Core Skills", "+ 3 weitere
   Kurse von …" / "+ 3 more courses from …", die Fußzeile) – und darüber hinaus
   **jeden Satz im Dokument**. Eine deutsche Matrix, auf deren Karten "Using
   AI to analyze user data." steht, ist ein Fehler und kein Fachbegriff. Das gilt genauso
   für die Hero-Beschreibung und für jede Beschreibung, die neu formuliert
   werden muss.

   **Der Katalog führt die Beschreibungen nur auf Deutsch** – so, wie sie im
   Figma-Pool stehen. Für eine **englische** Matrix wird jede Beschreibung
   beim Bauen übersetzt und das in der Übergabe gemeldet; Toolnamen und
   Fachbegriffe bleiben dabei stehen. Erfundene englische Fassungen zu
   behaupten, die es im Pool nicht gibt, war der Fehler der Vorgängerversion.

   **Namen: Fachbegriffe bleiben englisch, Übersetzungen werden deutsch.**
   Kategorienamen bleiben in jeder Matrix englisch ("Interaction & Visual
   Design", "Coding Skills"). Ein Attributname bleibt in einer deutschen Matrix
   nur dann englisch, wenn er ein eingeführter Fachbegriff ist, den man im
   deutschen UX-Alltag so sagt – "Wireframing & Prototyping", "Design Systems",
   "Information Architecture", "Journey Mapping", "Qualitative Research",
   "Accessibility Audits", "Workshop Facilitation", "Stakeholder-Management"
   (gekoppelt, siehe unten), "Emotional Design". **KI-Begriffe bleiben
   englisch** – "AI Prototyping", "AI in Research", "AI Workflows & Agents": So
   stehen sie in der Branche und in der Vorschau, die der Nutzer gewählt hat.
   Ist der englische Name nur eine Übersetzung, heißt das Attribut deutsch:
   "Frontend-Verständnis" statt
   "Frontend Understanding", "Zusammenarbeit mit Entwicklern" statt "Dev
   Collaboration", "Regulatorische Anforderungen" statt "Regulatory
   Compliance". Welche Form gilt, steht im Katalog in der Spalte „deutsch“ (leer = bleibt
   englisch; *Grenzfall* = bleibt englisch, Alternative daneben). Für neue
   Attribute gilt dieselbe Abwägung, im Zweifel bleibt der englische Name.
   Eine **englische** Matrix trägt durchgehend die englischen Namen. Toolnamen
   und eingeführte Fachwörter innerhalb der Beschreibungen bleiben in jeder
   Sprache stehen ("Auto-Layout", "Edge Cases", "WCAG", "Jobs-to-be-Done").
   Das Renderskript meldet, wo eine Matrix vom Katalognamen ihrer Sprache
   abweicht.

   **Produktnamen tragen die Schreibweise des Herstellers.** Belegbare
   Eigenschreibung schlägt jede andere Variante – auch die aus dem Auftrag:
   "Fullstory", nicht "FullStory"; "Hotjar", nicht "HotJar"; "UXPin", nicht
   "UxPin". Wer eine Schreibweise korrigiert, nennt das in der Übergabe, statt
   es stillschweigend zu tun. Ist die Eigenschreibung nicht zu belegen, bleibt
   die vorgegebene stehen.

   **Zusammengesetzte Begriffe mit englischem Bestandteil werden im deutschen
   Text durchgekoppelt (Duden):** „UX-Design“, „UX-Konzeption“,
   „Usability-Testing“, „Stakeholder-Management“, „User-Centered Design“ –
   nicht „UX Design“, „Usability Testing“ oder „User Centered Design“. Das
   gilt auch in Jobtiteln („UX/UI-Designer“). Ohne Kopplung bleiben:

   - **Eingeführte englische Fachbegriffe ohne deutsches Grundwort**: „User
     Research“, „UX Research“, „Information Architecture“, „Wireframing &
     Prototyping“. Kommt ein deutsches Wort dazu, wird gekoppelt:
     „User-Research-Interviews“.
   - **Eigennamen**: Firmen, Produkte und Zertifikate behalten ihre
     Schreibweise („Google UX Design Certificate“).
   - **Die Rolle, wie der Kandidat sie selbst führt** („UX & AI Designer“):
     wörtlich, in allen drei Dokumenten gleich.
   - **Englische Dokumente** (`sprache: en`).

   In der Skill Matrix gilt das für Hero-Beschreibung, Schwerpunkte, Satz und
   Tags der Qualifikationskarte, jede Beschreibung und die Attributnamen. Für
   Katalog-Attribute steht die gekoppelte Form in der Spalte „deutsch“
   („User-Centered Design“, „UI-Design“, „Design-QA“); Adjektiv plus Substantiv
   bleibt offen („Emotional Design“, „Responsive Web Design“). Kategorienamen
   sind englische Bezeichner und bleiben, wie sie sind („Usability Testing &
   Evaluation“). Das Renderskript meldet offene Schreibweisen aus einer kurzen
   Liste (`DURCHKOPPLUNG`: „UX Design“, „UX Konzeption“, „Usability Testing“,
   „Stakeholder Management“, „User Centered Design“) – ein Netz für die
   häufigsten Fälle, nicht die Regel: Was nicht darauf steht, wird trotzdem
   gekoppelt.

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
   Frage:   Soll die Skill Matrix zusätzlich als bearbeitbare Frames in einem
            Figma-File landen?
   Header:  Figma
   Optionen: Ja, zusätzlich ins Figma-File (Empfohlen)
           | Nein, nur die PDFs
   ```

   Bei „Ja" braucht es den Link – Material, also im Text derselben Nachricht,
   wörtlich so:

   > Schick mir den Link zum Figma-File, in das die Skill Matrix soll
   > (figma.com/design/…). Zeigt der Link auf eine bestimmte Seite, lege ich
   > sie dort ab, sonst auf einer neuen Seite. Ich brauche **Bearbeitungs**rechte
   > auf der Datei – Leserechte reichen nicht.

   Die Frames entstehen erst nach dem Rendern, siehe Schritt 4a – der lange und
   daneben die A4-Seiten. Drei Regeln dazu:

   - **Kommt „Ja" ohne Link**, wird er einmal im Fließtext nachgefragt – nicht
     über eine dritte `AskUserQuestion`-Nachricht.
   - **Der Link blockiert nichts.** Bleibt er aus, entstehen trotzdem die PDFs,
     und der Figma-Teil entfällt mit einem Satz in der Übergabe. Eine Skill
     Matrix ohne Figma-Frame ist vollständig.
   - **Nur Design-Dateien.** `figma.com/design/…` ja; `/board/` (FigJam),
     `/slides/`, `/make/` und `/proto/` nein. Dann sagen, was gebraucht wird,
     statt es zu versuchen.

4. **Das Material**, als Text derselben Nachricht, wörtlich in dieser Art:

   > Schick mir bitte den Lebenslauf als PDF, den LinkedIn-Export als PDF
   > (auf dem Profil: *Mehr* → *Als PDF speichern*) plus den Link zum
   > Profil, und das Portfolio als Link oder PDF. Wenn es Zertifikate gibt,
   > die mit in die Matrix sollen: als Bild oder PDF dazu – jedes bekommt in
   > der Zertifikatssektion eine eigene Kachel mit Bild.

   Was davon fehlt, fehlt – gebaut wird mit dem, was kommt. Aber jede
   fehlende Quelle macht die Belegbasis schmaler. Ohne Zertifikate entfällt
   die Zertifikatssektion ersatzlos; Zertifikate ohne Bild stehen mit einem
   Platzhalterfeld statt des Bildes – beides ist in Ordnung.

5. **Ein Foto**, falls Lebenslauf, LinkedIn und Portfolio keins hergeben –
   erst nach Schritt 1a anfragen, nicht hier. Hier nur erwähnen, dass ein
   richtiges Foto in guter Auflösung willkommen ist: die Fotokarte im Hero
   ist groß und fast quadratisch, das LinkedIn-Thumbnail ist dafür sichtbar
   weich – und mit etwas Rand über dem Kopf, sonst wird es eng.

6. **Die Anfrage, falls es eine gibt** – optional, als Text derselben
   Nachricht, keine Klickbox:

   > Ist die Skill Matrix für eine bestimmte Anfrage – eine Ausschreibung,
   > eine Projektbeschreibung, einen Kundenwunsch? Dann schick sie mit; ich
   > richte die Reihenfolge der Kategorien danach aus.

   Kommt keine, wird ohne Anfrage gebaut (KI-Kategorie zuerst, Schritt 2a) –
   nachgefragt wird nicht. Kommt sie später, mit dem Material oder als Satz
   im Auftrag („für die Ausschreibung bei X“), gilt sie genauso. Aus ihr wird
   in Schritt 1 eine Zeile für das Feld `anfrage` (Schritt 3): wer gesucht
   wird und welche Themen zählen, etwa „Junior-Designer, Fokus
   Barrierefreiheit, Dev-ready Handover, Design-QA“.

### 1. Eingang auslesen

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <lebenslauf.pdf> arbeit/
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <linkedin-export.pdf> arbeit/linkedin/
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <portfolio.pdf> arbeit/portfolio/
```

Schreibt je Quelle `text.txt` und legt Porträtkandidaten in `fotos/` ab –
bereits in Graustufen, je Fassung im Format ihrer Fotokarte (`foto-<name>.png`
für die lange, `foto-<name>-a4.png` für die A4-Fassung) und mit dem Kopf ganz
im Bild (siehe 1a); je Zuschnitt liegt ein Kontrollbild in `fotos/kontrolle/`. Bei einem Portfolio-Link die Seite abrufen und die
Projektseiten dazu.

**Bleibt `text.txt` leer, ist das PDF als Bild gesetzt** (häufig bei gestalteten
Lebensläufen). Dann die Seiten als Bild lesen — das PDF direkt öffnen oder mit
`pdftoppm -png -r 80` rendern — und die Inhalte von dort nehmen. Umgekehrt
liefert ein PDF mit vielen Projektbildern Dutzende Porträtkandidaten: nach dem
Motiv suchen, nicht den größten nehmen.

Für das Zusammenführen der Quellen gelten die Regeln des CV-Skills
unverändert: **Bei Widersprüchen gewinnt der Lebenslauf**, LinkedIn ergänzt
nur Lücken, das Portfolio ist Eigenwerbung (Fakten übernehmen, Bewertungen
nicht), LinkedIn-Artefakte wie "Top-Kenntnisse" ignorieren. Die Rubrik
"Kenntnisse" im LinkedIn-Export ist trotzdem nützlich – als **Hinweis**,
wonach im Lebenslauf und Portfolio zu suchen ist, nie als alleiniger Beleg.

**Die Anfrage auslesen**, falls eine gekommen ist (Schritt 0, Punkt 6): wer
gesucht wird und welche Themen zählen, in einer Zeile für `anfrage`. Sie ist
eine Gewichtung, kein Beleg – was sie verlangt, der Eingang aber nicht hergibt,
kommt nicht in die Matrix. Daraus folgt in Schritt 2 die Reihenfolge der
Kategorien (2a) und, soweit belegt, die Ausrichtung von Schwerpunkten und
Hero-Beschreibung (2c).

**Zertifikate aufbereiten**, falls welche gekommen sind:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/zert_bilder.py <zert1.pdf> <zert2.png> … arbeit/zertifikate/
```

Je Zertifikat ein Bild; am besten in der Reihenfolge neueste zuerst, so wie die
Einträge später in der JSON stehen. Titel, Aussteller und Datum vom Zertifikat
ablesen (Monat und Jahr, wenn draufsteht) – das Skript gibt dafür das Gerüst
der `zertifikate`-Liste aus. Beschnitten wird im Layout nichts: Jedes Bild wird
mit seinem Seitenverhältnis eingepasst. Formate, die stark vom Kachelformat
41 : 30 abweichen, meldet das Skript, weil sie dann klein wirken – dann lieber
einen besseren Ausschnitt suchen. Nachweis-IDs, Mitgliedsnummern und
Verifizierungs-Adressen kommen nicht ins Dokument.

### 1a. Das Foto — dieselbe Rangfolge wie im CV-Skill

1. Foto aus dem **Lebenslauf**, oder separat geschickt – dann ebenfalls durch
   den Zuschnitt: `python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <foto.jpg> arbeit/`,
2. sonst **LinkedIn**: `python3 ${CLAUDE_SKILL_DIR}/scripts/linkedin_foto.py "<profil-url>" arbeit/`,
3. sonst **Portfolio/Website**: `python3 ${CLAUDE_SKILL_DIR}/scripts/website_foto.py "<url>" arbeit/`,
4. sonst **beim Kandidaten anfragen**.

Alle Wege legen das Foto fertig beschnitten in `arbeit/fotos/` ab, zweimal:
`foto-<name>.png` und `foto-<name>-a4.png`. Die
Warnungen der Skripte ernst nehmen: die Fotokarte ist sechsmal so breit wie
der Fotokasten im CV, **unter 100 dpi wird das Bild sichtbar weich** – das
400px-Thumbnail von LinkedIn kommt nach dem Kopfzuschnitt meist auf 40–60 dpi
und taugt nur als Notlösung.
Liegt im Lebenslauf oder Portfolio ein größeres Bild, das zu nehmen. Jedes
automatisch gefundene Foto ansehen, bevor es ins Dokument geht (fremde
Gesichter, siehe CV-Skill). Ohne Foto funktioniert das Layout – die Karte
zeigt dann nur den Farbverlauf mit Name und Erfahrung – aber es wirkt leer.

**Der Kopf steht ganz im Bild, mittig, mit Luft über dem Haar.** Den Ausschnitt
setzt `scripts/kopf_ausschnitt.py`, das alle Foto-Wege aufrufen – **je Fotokarte
eigens**, denn die beiden Fassungen haben verschiedene Formate (lang 435 × 433,
fast quadratisch; A4 108 × 99, breiter). Es findet den Kopf (macOS Vision:
Gesicht, Kinn und Personenmaske für Scheitel und Kopfumriss) und schneidet so,
dass die **Kopfmitte waagerecht in der Bildmitte** steht und Scheitel und Kinn
dort sitzen, wo `tokens.json` es für die Karte vorgibt (`kopf-oben-anteil`,
`kinn-anteil`; lang wie im Figma-Master 5 % und 70 %, A4 10 % und 82 %).
**Angeschnitten wird der Kopf nie:** Über dem Scheitel bleibt mindestens
`kopf-luft-anteil` frei (lang 5 %, A4 8 % der Bildhöhe), das Kinn bleibt über der
Kinngrenze (lang: Beginn des Verlaufs, A4: `kinn-max-anteil`). Passt das nicht,
geht das Skript in dieser Reihenfolge vor:

1. **Größer schneiden** – der Kopf wird kleiner, es zeigt mehr Schultern; die
   waagerechte Mitte gibt dafür nach.
2. **Oben Hintergrund ergänzen**, wenn das Original über dem Kopf zu wenig Rand
   hat – nur bei einfarbigem oberen Bildrand (Streuung höchstens 3 Grauwerte),
   sonst sähe man die Naht. Das Skript meldet, wie viele Pixel es ergänzt hat.
3. **Melden**: „Zu wenig Luft über dem Scheitel“ – dann ein anderes Foto nehmen
   oder anfragen.

Je Zuschnitt meldet das Skript eine Zeile, etwa „Kopf bei 50 % der Breite,
Scheitel 8 %, Kinn 86 %, 300 dpi“.

- **Die Kontrollbilder ansehen**, bevor das Foto in die JSON kommt:
  `fotos/kontrolle/foto-<name>.png` und `…-a4.png` zeigen das Foto so, wie es
  auf der jeweiligen Karte sitzt – mit Verlauf (lang), roter Mittellinie, orangem
  Kopfrahmen und der Mindestluft als blauer Linie. Die Kopfmitte liegt auf der
  roten Linie, die Haare unter der blauen.
- **„Kopf nicht mittig“** heißt: Das Original hat auf einer Seite zu wenig Rand.
  Dann nicht von Hand schieben, sondern ein anderes Bild nehmen (größere Fassung
  aus Lebenslauf, Portfolio oder Website) oder beim Kandidaten eins anfragen –
  und in der Übergabe melden, falls es so bleibt.
- **Mehrere Gesichter:** Das Skript nimmt das größte und sagt das. Prüfen, ob es
  die richtige Person ist.
- **Ohne Kopferkennung** (kein macOS, Kopf nicht gefunden) schneidet das Skript
  waagerecht mittig und oben bündig und meldet das. Dann den Kopf im Original
  ablesen – Pixel von Haaransatz bis Kinn und von Ohr zu Ohr – und neu
  schneiden:

  ```bash
  python3 ${CLAUDE_SKILL_DIR}/scripts/kopf_ausschnitt.py <original> arbeit/fotos/ --kopf x0,y0,x1,y1
  ```

In die JSON kommt nur `person.foto` (der lange Zuschnitt); den A4-Zuschnitt
findet das Renderskript daneben (`<foto>-a4.png`). Fehlt er, schneidet es ihn
aus dem langen Foto und meldet, dass er aus dem Original besser wäre.
`person.foto_a4` setzt ihn ausdrücklich, falls er anders heißt.

### 2. Attribute auswählen und bewerten

Das ist der Kern dieses Skills. Zuerst `references/attribute-katalog.md`
lesen – er ist der Wortschatz der Matrix.

#### 2a. Kategorien festlegen

Kategorien werden **nicht erfunden und nicht umgebaut**. Genommen werden
Abschnittstitel aus `references/attribute-katalog.md` – dort stehen dreizehn,
und sie decken jedes Profil ab, das dieses Haus vermittelt.

**Jedes Attribut steht in seiner Katalog-Kategorie, wenn die in der Matrix
vorkommt** – sonst in der inhaltlich nächsten Kategorie der Matrix, nie in einer
fachfremden. Beispiele: `Accessibility Audits` (Katalog: Usability Testing)
steht unter `Accessibility & Inclusive Design`, `Design Systems` unter
`Interaction & Visual Design`, `User-Centered Design` und `Workshop
Facilitation` unter `User Research & Insights`, wenn ihre eigenen Kategorien
fehlen. „Frontend-Verständnis“ und „Zusammenarbeit mit Entwicklern“ gehören
dagegen nie zu Accessibility. Welche Kategorien verwandt sind, steht als
Tabelle `VERWANDT` in `scripts/render_skillmatrix.py` (nächste zuerst). Ist die
nächste schon voll, kommt die übernächste. Bringt der Kandidat eine alte Skill
Matrix mit, werden aus ihr Auswahl, Punkte und Beschreibungen übernommen – die
Kategorie nicht. Alte Matrizen sortieren nach Gefühl; so landeten
„Frontend-Verständnis“ und „Zusammenarbeit mit Entwicklern“ einmal unter
Barrierefreiheit, und der Skill hat es übernommen. Steht ein Attribut nicht im
Katalog, kommt es in die Katalog-Kategorie, zu der es inhaltlich gehört. Das
Renderskript meldet jedes Katalog-Attribut außerhalb seiner Kategorie:
verwandt als Hinweis („weil <Katalog-Kategorie> fehlt“, gehört in die
Übergabe), fachfremd als `WARNUNG` – die wird behoben, nicht übergeben.

**Eine eigene Kategorie lohnt sich ab zwei Attributen.** Ein einzelnes geht in
die nächstverwandte. **Die Sektion Kernkompetenzen trägt höchstens 24 Skills,
höchstens sechs je Kategorie** (drei Karten pro Reihe, zwei Reihen) **und
höchstens fünf Kategorien**, üblich sind drei bis vier. **Belegte Attribute
gehen nicht verloren:** Gestrichen wird nur, wenn diese Grenzen es erzwingen –
dann die schwächsten, mit Hinweis und unter „nicht aufgenommen“ in der Freigabe
(2e).

Ausgewählt werden die Kategorien, die das Profil **belegt**. Ein
Barrierefreiheits-Schwerpunkt bekommt `Accessibility & Inclusive Design`.

**Die Reihenfolge der Kategorien folgt der Anfrage, wenn es eine gibt.**

- **Mit Anfrage** (Ausschreibung, Projektbeschreibung, Kundenwunsch – Schritt
  0, Punkt 6) steht die Kategorie zuerst, die für die Anfrage am wichtigsten
  ist, danach absteigend nach Bedeutung für sie – auch wenn die KI-Kategorie
  dadurch nach hinten rückt. Beispiel: Für „Junior-Designer, Fokus
  Barrierefreiheit, Dev-ready Handover, Design-QA“ steht `Development
  Collaboration` vorn, dann `Accessibility & Inclusive Design`, dann `AI &
  Emerging Tech`. Was die Anfrage nicht berührt, folgt nach Stärke.
- **Ohne Anfrage steht eine KI-Kategorie zuerst** (`AI & Emerging Tech`; das
  Skript erkennt jede Kategorie, deren Name mit „AI“ oder „KI“ beginnt),
  danach die stärkste.

Beide Regeln ordnen nur, sie ergänzen nichts: Ein Profil ohne KI-Belege
bekommt keine AI-Kategorie, und eine Anfrage nach Barrierefreiheit macht aus
keinem Beleg einen.

**`Tools` ist keine Kategorie, sondern eine eigene Sektion.** Sie bekommt eine
eigene Überschrift mit dem Tools-Icon – genau wie „Kernkompetenzen" – und steht
**nach** den Kernkompetenzen, so wie in der Figma-Vorlage. Sie zählt nicht gegen
die 24, weil sie Werkzeuge listet und keine Fähigkeiten. Ein Kategorielabel
innerhalb der Sektion entfällt: Die Überschrift sagt bereits „Tools", ein
zweites Label darunter wäre doppelt. Die Karten sind dieselben wie bei den
Kernkompetenzen – Name, fünf Punkte, Beschreibung –, im selben Raster.

Damit trägt der Rumpf in dieser Reihenfolge: **Zertifikate (falls belegt) →
Kernkompetenzen → Tools**.

**Befüllt wird Tools mit den Tools, die der Eingang nennt** – aus Tool-Listen,
Projektsteckbriefen, Stationen, Icons im Lebenslauf. **Höchstens sechs** (eine
Sektion, zwei Reihen), die meistgenutzten zuerst. Steht ein Tool im
Katalogabschnitt `Tools`, gelten Name und Beschreibung wörtlich; sonst wird es
im Katalogstil neu angelegt (Herstellerschreibweise, eine Zeile, was die Person
damit tut). Bewertet wird wie jeder Skill, 3–5 Punkte, mit Beleg.

**Ein Tool steht nur einmal im Dokument – in der Tools-Sektion.** Was dort
steht, wird in den Kernkompetenzen nicht noch einmal als Skill geführt: nicht in
einer Kategorie wie `Tools & Implementation` und nicht als Teil eines
Sammelnamens (`Figma / FigJam` in den Tools schließt `Figma` in den
Kernkompetenzen aus). Umgekehrt wird kein Skill der Kernkompetenzen zusätzlich
als Tool gezeigt. Bleibt eine Kategorie dadurch mit einem Skill zurück, geht er in
die nächstverwandte (siehe oben). Das Renderskript meldet Doppelungen.

**Nennt der Eingang gar keine Tools**, wird nichts still ergänzt. Stattdessen
kommen in Schritt 2e rollentypische Tools als Vorschlag in die Freigabe – bei
UX/UI-Profilen zuerst aus dem Katalog (etwa `Figma / FigJam`) –, deutlich als
„Vorschlag, nicht belegt" markiert und mit vorgeschlagenen Punkten (Kernwerkzeug
der Rolle 4, sonst 3). Ob sie ins Dokument kommen, entscheidet die Tools-Frage
in derselben Freigabe. Ohne Ja entfällt die Tools-Sektion.

`Coding Skills` ist dagegen eine gewöhnliche Kategorie innerhalb der
Kernkompetenzen und zählt wie jede andere gegen die fünf.

#### 2b. Attribute wählen

Je Kategorie die Skills, die der Eingang **belegt** – über Stationen,
Projekte, Tool-Listen, Portfolio-Cases oder Zertifikate.

**Ausgewählt wird nach Beleg, einsortiert nach Katalog.** Welche Attribute in
die Matrix kommen, entscheidet der Eingang – nicht, welcher Katalogabschnitt
gerade Platz hat. Wo sie stehen, entscheidet der Katalog (2a). Ein Profil mit
vier Stationen, die "Frontend Development" als Skill führen, bekommt
`HTML / CSS`, und zwar unter `Coding Skills`, wo der Katalog es führt, wenn die
Kategorie in der Matrix steht – sonst unter der nächstverwandten,
`Development Collaboration` (2a). Den konkreten Eintrag zugunsten eines vageren
zu verdrängen, der zufällig in einer vorhandenen Kategorie liegt, ist kein
Ausweg.

Steht ein Attribut im Katalog, werden **Name und Beschreibung wörtlich**
übernommen – der Name in der Form der Dokumentsprache (für eine deutsche Matrix
die Spalte „deutsch“, wo sie gefüllt ist, sonst der englische Name), die
Beschreibung so, wie sie im Katalog steht. Ausnahme ist eine alte Skill Matrix
des Kandidaten: Ihre Beschreibungen gehen vor (2a), geglättet nach den Regeln
oben. Nur was im Katalog fehlt, wird neu formuliert (Stilregeln am Ende des
Katalogs), und zwar ebenfalls in der Dokumentsprache. So tragen alle Matrizen
für denselben Skill denselben Namen am selben Ort.

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
- **Mit Anfrage** dürfen sich Schwerpunkte und Hero-Beschreibung an ihr
  ausrichten: Unter den belegten Themen kommen die nach vorn, die für die
  Anfrage zählen (für die Anfrage oben etwa „UX-Design“, „Dev-ready Handover“,
  „Barrierefreiheit“). **Nur mit belegtem Material, nichts erfinden** – kein
  Schwerpunkt und kein Halbsatz, den der Eingang nicht hergibt, nur weil die
  Anfrage ihn nennt. Was die Anfrage verlangt und fehlt, steht in der Freigabe
  (2e), nicht im Dokument.
- **Erworbene Qualifikationen** – die Karte über den Zertifikatskacheln, nur
  wenn es Zertifikate gibt: ein Satz und sechs bis zehn Tags. **Jedes Tag muss
  sich aus mindestens einem der aufgeführten Zertifikate ableiten lassen** –
  aus Titel, Aussteller oder Kursinhalt. Was nur Lebenslauf oder Portfolio
  belegen, gehört in die Kernkompetenzen, nicht in diese Karte. Der Satz fasst
  die Weiterbildung zusammen, die die Zertifikate zeigen: höchstens zwei
  Zeilen, ohne Eigenschaftszuschreibungen, nichts, was die Zertifikate nicht
  hergeben. Tag-Namen folgen der Namensregel aus Schritt 0. Ändern sich die
  Zertifikate (Nachlieferung, Streichung, Bündelung), werden Tags und Satz neu
  abgeglichen. Der Text der Vorlagenkarte („Umfassende Weiterbildung in UX
  Research …“) beschreibt Wissems Zertifikate und wird nicht übernommen. Satz
  und Tags sind generiert: **melden und zur Freigabe stellen** (2e). Gibt der
  Nutzer Satz oder Tags vor, gelten sie wörtlich.

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
   bei X", "CPUX-F 2021", "Portfolio-Case Y"), die Kategorien in der
   Reihenfolge des Dokuments. Bei einer Anfrage darüber die Zeile für
   `anfrage` und ein Satz, warum die erste Kategorie vorn steht – und was die
   Anfrage verlangt, der Eingang aber nicht belegt. Steht ein Attribut in einer
   nächstverwandten Kategorie, dazu in Klammern die Katalog-Kategorie. Darunter,
   falls die Grenzen es erzwungen haben, die belegten Attribute, die **nicht
   aufgenommen** wurden – mit Punkten und Grund (2a).
4. Die **Tools** als eigene kleine Tabelle: Tool, Punkte, Beleg. Nennt der
   Eingang keine Tools, stehen hier die rollentypischen Vorschläge, jeder mit
   „Vorschlag, nicht belegt" statt eines Belegs.
5. Die **Zertifikate**, falls welche kommen: Titel, Aussteller, Datum, Bild
   ja/nein – neueste zuerst, so wie sie als Kacheln ins Dokument gehen. Sind es
   mehr, als die Sektion trägt, welche Einträge gebündelt werden – die Ausgabe
   von `python3 ${CLAUDE_SKILL_DIR}/scripts/zertifikate.py <entwurf.json>`
   nennt es.
6. Die **Karte „Erworbene Qualifikationen“**, falls es Zertifikate gibt: der
   Satz im Wortlaut, als generiert gekennzeichnet, und die Tags als Tabelle
   Tag – Zertifikat, aus dem es stammt. Ein Tag ohne Zertifikat kommt nicht in
   die Karte (2c).
7. Dazu **eine** `AskUserQuestion` mit der Freigabe:

   ```
   Frage:   Passen Auswahl und Bewertung so?
   Header:  Freigabe
   Optionen: Ja, so bauen (Empfohlen)  |  Ich möchte etwas ändern
   ```

   Nennt der Eingang keine Tools, trägt **derselbe Aufruf** eine zweite Frage:

   ```
   Frage:   In den Unterlagen stehen keine Tools. Sollen die vorgeschlagenen,
            für <Rolle> typischen Tools ergänzt werden?
   Header:  Tools
   Optionen: Ja, Vorschläge ergänzen (Empfohlen)  |  Nein, ohne Tools-Sektion
   ```

   Bei "ändern" beschreibt der Nutzer die Änderungen als Text; danach die
   aktualisierte Tabelle noch einmal kurz zeigen, nicht die ganze Nachricht
   wiederholen.

**Bis die Freigabe da ist, wird nicht gerendert.**

### 3. Daten strukturieren

Aus den freigegebenen Inhalten eine `skillmatrix.json` bauen. Vollständiges
Beispiel: `beispiel/skillmatrix.json` (das ist Wissems Matrix aus der
Vorlage mit sechs Abweichungen: Die Hero-Beschreibung steht in der
Ich-Perspektive, das Vorlagen-PDF trägt sie noch in der dritten Person. Die
Werkzeuge stehen nur in den Tools – `Figma / FigJam` und `Adobe CC` –, die
Vorlage führt sie zusätzlich unter `Tools & Implementation`. Das Foto ist mit
dem Kopf in der Mitte zugeschnitten, `material/foto-karte.png`, daneben der
A4-Zuschnitt `material/foto-karte-a4.png`. Die
Zertifikate stehen einzeln als Kacheln statt als gebündelte Karte über einem
Bilderraster – zwei davon ohne Bild, wie die Vorlage sie nennt –, darüber die
Karte „Erworbene Qualifikationen“ mit Satz und Tags der Vorlagenkarte. Und die
Kategorien folgen dem Katalog (2a): Statt „AI“, „Strategie & Research“,
„Interaction & Visual Design“ und „Tools & Implementation“ stehen fünf
Katalog-Kategorien da; „Product Thinking“ und „Workshop Facilitation“ stehen
nächstverwandt unter `User Research & Insights`, weil ihre Kategorien fehlen,
„Concepts“ heißt nach der Namensregel „Konzeption“ und „Micro-interactions“
nach dem Katalog „Microinteractions“. Schließlich ist durchgekoppelt (Schritt
0): „Usability-Testing“ im Satz, „Stakeholder-Management“ unter den Tags,
„Design-System-Testing“ unter den Kernkompetenzen. Eine `anfrage` hat das
Beispiel nicht – die KI-Kategorie steht vorn).

```json
{
  "sprache": "de",
  "anfrage": "optional, eine Zeile",
  "person": {
    "name", "rolle", "verfuegbar_ab", "erfahrung",
    "beschreibung", "schwerpunkte": [], "foto", "foto_a4 (optional)"
  },
  "zertifikate": [{ "titel", "aussteller", "datum", "bild" }],
  "qualifikationen": { "text", "tags": [] },
  "kompetenzen": [{ "kategorie", "skills": [{ "name", "punkte", "beschreibung" }] }],
  "tools": [{ "name", "punkte", "beschreibung" }]
}
```

Dazu:

- **`anfrage`** (optional): die Anfrage, für die die Matrix gebaut wird, in
  einer Zeile (Schritt 0, Punkt 6) – etwa `"Junior-Designer, Fokus
  Barrierefreiheit, Dev-ready Handover, Design-QA"`. Sie steht nicht im
  Dokument; sie sagt den Skripten, dass die Reihenfolge der Kategorien in der
  JSON gewollt ist (siehe „Reihenfolge der Kategorien“ unten). Ohne Anfrage
  das Feld weglassen.
- **`person.foto`**: der Zuschnitt der langen Fotokarte (`foto-<name>.png`). Den
  A4-Zuschnitt (`foto-<name>-a4.png`) findet das Renderskript daneben;
  `person.foto_a4` nur, wenn er anders heißt oder woanders liegt (Schritt 1a).
- **`tools`**: die Tools-Sektion nach den Kernkompetenzen, höchstens sechs
  Einträge, gleicher Aufbau wie ein Skill. Fehlt der Schlüssel oder ist die
  Liste leer, entfällt die Sektion (PDF und Figma).
- **`zertifikate`**: je Zertifikat ein Eintrag, **neueste zuerst** – auch
  Kurse einer Reihe einzeln, gebündelt wird nur vom Skript und nur bei
  Platzmangel (siehe unten). Ohne Zertifikate entfällt die Sektion.
  - `titel`: so, wie er auf dem Zertifikat steht.
  - `aussteller`: Name des Ausstellers. Hat er eine Kurzform, sie vorn mit
    Gedankenstrich führen („UXQB – International Usability …“): Wird es eng,
    zeigt das Layout nur die Kurzform.
  - `datum`: „Monat Jahr“ in der Dokumentsprache („September 2026“) oder nur das
    Jahr, wenn kein Monat belegt ist. Die Kachel zeigt nur das Jahr; der Monat
    ordnet Zertifikate desselben Jahres.
  - `bild` (optional): die Datei aus `zert_bilder.py`. Ohne Bild steht ein
    Platzhalterfeld mit dem Zertifikats-Icon.

  `beschreibung`, `tags` und die frühere Bilderliste `zertifikat_bilder`
  gibt es nicht mehr: Die Sektion zeigt Titel, Aussteller und Datum – das, was
  ein Kunde prüft. **Alte JSONs:** `jahr` wird als `datum` übernommen,
  `beschreibung`, `tags`, `hervorheben` und `zertifikate_darstellung` werden
  übergangen, alles mit Hinweis. Steht
  `zertifikat_bilder` darin, brechen Render- und Planskript mit einer
  Umstellanleitung ab – welches Bild zu welchem Zertifikat gehört, lässt sich
  nicht erraten, und ein Bild neben dem falschen Titel ist eine Falschaussage.
- **Die Zertifikate stehen als Kacheln**, vier je Reihe: Bild oben auf grauer
  Bühne, darunter Titel (höchstens zwei Zeilen) und „Aussteller · Jahr“. Eine
  andere Darstellung gibt es nicht – Liste und Top 3 standen am 2026-10-03 zur
  Wahl, entschieden wurde für die Kacheln.

  **Die Sektion ist höchstens 924 hoch** (Figma-px = pt), von der Überschrift
  bis zur letzten Kachelreihe, die Karte „Erworbene Qualifikationen“
  eingerechnet: ohne Karte drei Reihen (12 Kacheln), mit Karte zwei (8). Sind
  es mehr Zertifikate, fasst `scripts/zertifikate.py` die **ältesten Einträge
  eines Ausstellers** zu einer Kachel zusammen („+ 3 weitere Kurse von
  Anthropic“, darunter Jahre und Titel), immer beim Aussteller mit den meisten
  Einträgen, bis es passt. Der neueste Eintrag jedes Ausstellers bleibt
  sichtbar. Reicht auch das nicht – mehr Aussteller als Kacheln –, kommen die
  ältesten Kacheln in eine **Sammelkachel** („+ 5 weitere Zertifikate“).
  Gestrichen wird nichts. Render- und Planskript planen gleich, PDF und Figma
  zeigen also dasselbe – und die A4-Fassung dieselben Kacheln, nur kleiner;
  beide melden jede Bündelung – sie gehört in die Übergabe, und die Tags der
  Karte werden danach abgeglichen. Gekürzt wird
  sonst nur mit Auslassungszeichen (Titel über zwei Zeilen) oder auf die
  Kurzform des Ausstellers; das Jahr bleibt immer stehen.
- **`qualifikationen`** (optional): die Karte „Erworbene Qualifikationen“
  (en: „Acquired qualifications“, die Überschrift setzt das Layout) zwischen
  Sektionsüberschrift und Kacheln. `text`: ein Satz, höchstens zwei Zeilen;
  `tags`: sechs bis zehn, jedes von einem Zertifikat belegt (2c). Die Karte
  wird nie gekürzt – ein längerer Satz oder mehr Tags gehen von den Kacheln
  ab, das Skript meldet es. Ohne Zertifikate entfällt sie mit der Sektion.
- **`zertifikate_titel`** (optional, oberste Ebene): überschreibt die
  Sektionsüberschrift, z.B. `"Zertifizierungen UX/UI"` wie in Florians
  Vorlage.
- **`punkte`**: ganze Zahl 3–5, siehe Skala. Das Renderskript warnt
  darunter.
- **Reihenfolge der Kategorien** (2a): **mit `anfrage`** die wichtigste für
  die Anfrage zuerst, danach absteigend nach Bedeutung für sie. Render- und
  Planskript lassen die Reihenfolge der JSON dann, wie sie ist, und melden sie
  (Hinweis „Anfrage …: Kategorien in der Reihenfolge der JSON — 1. …“) – die
  Meldung gehört in die Übergabe. **Ohne `anfrage` die KI-Kategorie immer
  zuerst** (Name beginnt mit „AI“ oder „KI“), danach die stärkste – sonst
  meist Strategie & Research. Dann setzen beide Skripte eine KI-Kategorie, die
  weiter hinten steht, selbst nach vorn und melden das; die JSON dann
  nachziehen. Die Vorlagenreihenfolge nur übernehmen, wenn sie zum Profil
  passt.

### 4. Rendern — beide Fassungen in einem Aufruf

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_skillmatrix.py skillmatrix.json ausgabe/
```

**Die Dateinamen setzt das Skript**, nicht der Aufruf: es baut sie aus
`person.name` und `person.rolle` zusammen und legt beide Dateien im
angegebenen Ordner ab.

```
New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf      (lang)
New-Monday - Vorname Nachname - Jobtitel - Skillmatrix A4.pdf   (A4)
```

Steht im Aufruf trotzdem ein Dateiname, gilt davon nur der Ordner — das
Skript meldet die Umbenennung. Der Name im Bericht an den Nutzer ist der,
den das Skript ausgibt, nicht der aus dem Aufruf. Die Datei heißt so, wie
sie beim Kunden ankommt, deshalb wird hier nicht abgekürzt und nicht
umbenannt.

Die lange Fassung rendert es zweimal (Vorratshöhe, dann exakte Inhaltshöhe –
sie ist eine einzige lange Seite). Die A4-Fassung ebenfalls zweimal: erst mit
32pt Mindestluft vor dem Fuß, dann mit so viel Luft, dass der Fuß auf dem
unteren Rand der letzten Seite aufsitzt (wie im Lebenslauf). Kein Block bricht
dort in sich um – Kategorie, Tools, Qualifikationskarte, Kachelreihe stehen
ganz auf einer Seite, Überschriften bei dem, was folgt –, und weil die
Reihenfolge feststeht, kommt sie mit so wenigen Seiten aus wie möglich (für
Florian Feiler drei). Welcher Block auf welcher Seite steht, legt das Skript im
A4-PDF ab; daraus baut Schritt 4a die Seiten. Das Skript sucht sich die Engine
selbst und meldet Auffälligkeiten nach stderr: fehlende Felder, Punkte außerhalb der
Skala, überlange Beschreibungen, Schwerpunkte breiter als die Textspalte,
fehlende Bilddateien, eine nach vorn gesetzte KI-Kategorie oder – mit
`anfrage` – die gewählte Reihenfolge der Kategorien, Attribute außerhalb
ihrer Katalog-Kategorie, Namen, die nicht der Katalogform der Dokumentsprache
entsprechen, offene Schreibweisen wie „UX Design“ (Durchkopplung, Schritt 0),
erfundene Kategorien, umsortierte, gekürzte und gebündelte
Zertifikate, einen zu langen Satz oder zu wenige Tags in der
Qualifikationskarte; in der A4-Fassung (Präfix „A4:“) einen Block, der höher
ist als eine Seite, einen Fuß allein auf der letzten Seite und einen
nachträglich geschnittenen A4-Fotozuschnitt. Die Hinweise sind zu lesen und
abzuarbeiten, nicht zu überfliegen.

Die Zertifikatssektion wird im fertigen Layout vermessen, mit Karte:
„Zertifikatssektion: 803pt hoch (8 Kacheln, geplant 803, Grenze 924)“. Liegt
sie über 924, steht im Hinweis, um wie viel; weicht sie von der geplanten Höhe
ab, bricht ein Text anders um als geschätzt.

Dabei zeichnet es die Kartenschatten (WeasyPrint kennt kein `box-shadow`) und
prüft zum Schluss beide PDFs gegen `assets/tokens.json` (die A4-Fassung gegen
den Block `a4`): Seitenformat jeder Seite, eingebettete Schriften, Schrift,
Schnitt, Größe und Farbe jeder Textzeile, Flächen- und Linienfarben. **Endet es
mit „FEHLER — das PDF weicht vom Design System ab" (Code 2), geht kein PDF
raus.** Die Ursache ist fast immer ein
Wert, der außerhalb von `tokens.json` gesetzt wurde, oder eine Ersatzschrift
(etwa eine falsch geschriebene Schriftfamilie) – beheben, nicht übergehen.
Fehlende Schriftdateien fängt das Skript schon vor dem Rendern ab; dann
entsteht gar kein PDF. Die letzte Zeile eines sauberen Laufs lautet „Design
System eingehalten".

**Beide Ergebnisse ansehen, bevor sie rausgehen** – immer, nicht nur bei
Warnungen:

```bash
pdftoppm -png -r 40 "ausgabe/New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf" arbeit/vorschau
pdftoppm -png -r 72 "ausgabe/New-Monday - Vorname Nachname - Jobtitel - Skillmatrix A4.pdf" arbeit/vorschau-a4
```

Auf der Vorschau prüfen: Steht der Kopf mittig in der Fotokarte und das
Gesicht frei vom Farbverlauf? Stehen die
Schwerpunkt-Buttons in einer Zeile? Läuft kein Kartentitel in die Punkte,
und sind die leeren Punkte als Ringe zu sehen? Steht die richtige Kategorie
zuerst (mit Anfrage die wichtigste für sie, sonst die KI-Kategorie), und steht
jedes Attribut in seiner Katalog-Kategorie? Sind die Zertifikate unverzerrt,
neueste zuerst, nichts abgeschnitten oder überlappend, passt jedes Tag der Qualifikationskarte zu einem
der gezeigten Zertifikate, und ist die Sektion höchstens 924 hoch?
Wirkt eine Kategoriezeile halb leer (eine einzelne Karte in der letzten Zeile
ist in Ordnung – die Vorlage hat das auch)? In der A4-Fassung zusätzlich: Logo
auf jeder Seite, Badge nur auf Seite 1, keine Kategorie über einen
Seitenumbruch, der Fuß unten auf der letzten Seite, das Porträt mit Luft über
dem Haar?

### 4a. Die Figma-Frames ablegen — nur wenn danach gefragt wurde

Entfällt, wenn in Schritt 0 „Nein" kam oder kein Link vorliegt. **Die PDFs sind
an dieser Stelle fertig** und gehen so oder so raus.

Auch in Figma entstehen **beide Fassungen**: der lange Frame und **rechts
daneben die A4-Seiten** – je PDF-Seite eine („Skillmatrix A4 — Vorname
Nachname — Seite n“), 100 Abstand zum langen Frame und untereinander, oben
bündig mit ihm. Die Seitenaufteilung kommt aus dem A4-PDF, wie beim
Lebenslauf.

**Beide entstehen aus Instanzen der Master-Bibliothek** („Portfolio - CV
Master“, Keys in `assets/master-bibliothek.json`): der lange Frame aus
`Skillmatrix lang/Kopfzeile`, `/Hero`, `/Rumpf` und `/Fuß`, jede A4-Seite als
Instanz von `Skillmatrix A4/Seite`, deren Booleans die Blöcke der Seite
schalten. Befüllt wird über Component-Properties, exponierte Instanzen und
Bild-Overrides – so kommt jede spätere Änderung am Master per
Bibliotheks-Update in die Kandidatendatei. Rezept, Tabelle der befüllten
Properties, Mengen und bekannte Lücken in `references/figma.md`.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py skillmatrix.json arbeit/ \
        --pdf "ausgabe/New-Monday - … - Skillmatrix.pdf" \
        --pdf-a4 "ausgabe/New-Monday - … - Skillmatrix A4.pdf"
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --skript vorflug arbeit/ --seite <ID>
```

Danach in dieser Reihenfolge, je ein Aufruf: **Vorflug** (Seiten, Schriften,
ein Import per Key) → **ein `upload_assets`** für alle Bilder, Hashes per
`figma_assets.py --bilder` → **lang** und **A4** (`--skript lang|a4 … --bilder
arbeit/bilder.json` gibt den fertigen `use_figma`-Code aus) → ein
`get_screenshot` je Frame. Figma begrenzt die Aufrufe je Sitz – nichts
zwischendurch nachsehen, was die Rückgabe schon sagt.

**Vor dem ersten Aufruf den Skill `figma-use` laden** — ohne ihn sind die
Fallstricke des Plugin-API nicht zu umgehen.

Drei Stellen, die still danebengehen:

- **Nie eine Instanz lösen, kein Wert von Hand.** Gesetzt werden nur Inhalte:
  Texte, Booleans, Varianten, Bilder, Sichtbarkeit und die Paddings des
  Bildfelds der Zertifikatskacheln. Jede andere Überschreibung kappt die
  Bindung an den Master genau dort. Die Rückgabe `oben` zeigt nur Instanzen.
- **Kein Vorgabeinhalt bleibt stehen.** Was das Material nicht hergibt, schaltet
  ein Boolean ab oder blendet die Sichtbarkeit aus; ein Bild ohne Upload wird
  ausgeblendet, nie mit dem Beispielbild der Komponente geliefert. `reste` in
  der Rückgabe muss leer sein.
- **Zertifikatsbilder über das Bildfeld.** Die Breite einer Instanz lässt sich
  nicht überschreiben – der Plan setzt die Paddings der Bühne so, dass das Bild
  das Seitenverhältnis der Datei hat (FIT). Das Foto kommt als fertiger
  Zuschnitt aus Schritt 1a (FILL).

**Rückfall: roh bauen.** Meldet der Vorflug `bibliothek_ok: false` oder
`figma_plan.py` für eine Fassung „sprengt die Komponenten“ (mehr Kategorien,
Karten, Kacheln oder Tags, als die Komponenten tragen), kommt diese Fassung
aus den rohen Bauplänen (`arbeit/figma_plan.json`, `figma_plan_a4.json`,
Rezept in `references/figma-roh.md`). Das Ergebnis hängt an keiner Komponente
– das steht in der Übergabe, mit dem Grund.

Vier Dinge stehen fest:

- **Figma hält die PDFs nicht auf.** Schlägt irgendetwas fehl — Werkzeug nicht
  verbunden, nicht angemeldet, keine Bearbeitungsrechte, falscher Dateityp, Proxy
  blockt, Aufrufgrenze erreicht —, werden die PDFs trotzdem übergeben und der
  Grund genannt. Nicht abbrechen, nicht nachträglich am PDF drehen, und keinen
  zweiten Anlauf mit anderen Daten.
- **In die Zieldatei kommt nichts Globales** außer den importierten
  Bibliothekskomponenten. Keine Text-Styles, keine Variablen, keine eigenen
  Komponenten. Was schon in der Datei liegt, wird nicht umbenannt, nicht
  verschoben und nicht gelöscht; der Master wird nur gelesen.
- **Nichts überschreiben.** Steht dort schon ein Frame gleichen Namens, kommt der
  neue daneben, nicht darüber.
- **Kein Ersatz-Layout.** Reicht es nicht für den Frame, wird kein vereinfachter
  gebaut. Entweder das Dokument oder nichts.

### 5. Übergeben

Beide PDFs ausgeben und in wenigen Zeilen berichten:

- Die generierte Hero-Beschreibung im Wortlaut (falls seit der Freigabe
  geändert), mit Bitte um finalen Blick – ebenso Satz und Tags der Karte
  „Erworbene Qualifikationen“ mit dem Zertifikat je Tag, unter „Zur Freigabe“.
- Welche Attribute **nicht** aus dem Katalog stammen und neu formuliert
  wurden, welche Namen nach der Namensregel deutsch stehen, welche Attribute in
  einer nächstverwandten Kategorie stehen (Wortlaut der Hinweise) und – nur wenn
  die Grenzen es erzwungen haben – welche belegten Attribute nicht
  aufgenommen wurden.
- Welche Tools **ohne Beleg** auf Wunsch ergänzt wurden (nur wenn der Eingang
  keine nannte und die Tools-Frage mit Ja beantwortet wurde).
- Wo Quellen einander widersprachen – mit beiden Werten; ins Dokument kam
  der Lebenslauf.
- Woher das Foto stammt (falls automatisch geholt) und die dpi-Zahl, falls
  unter 100. Steht der Kopf nicht mittig, weil das Original zu wenig Rand hat,
  auch das – mit der Bitte um ein anderes Foto; ebenso, wenn das Skript oben
  Hintergrund ergänzt oder zu wenig Luft über dem Scheitel gemeldet hat.
- Was das Renderskript bemängelt hat und wie damit umgegangen wurde – immer
  mit dabei: welche Zertifikate gebündelt oder gekürzt wurden (Wortlaut aus
  den Hinweisen, samt Sammelkachel) – und bei einer Anfrage die gewählte
  Reihenfolge der Kategorien samt Anfrage, sonst dass eine KI-Kategorie nach
  vorn gerückt ist, falls das Skript das gemeldet hat.
- **Beide PDFs** mit ihrem Dateinamen; bei der A4-Fassung die Seitenzahl.
- **Die Figma-Frames**, falls gewünscht: der Link auf den langen Frame und auf
  die A4-Seiten (`…?node-id=…`) und auf welcher Seite der Datei sie liegen –
  und ob sie aus der Bibliothek kommen oder roh gebaut wurden (mit Grund), dazu
  die Lücken der Bibliothek, die gegriffen haben (`references/figma.md`). Ist
  einer nicht zustande gekommen, steht hier stattdessen der Grund in einem Satz. Weicht
  die Frame-Höhe um mehr als 20pt von der PDF-Höhe ab, gehört auch das hierher
  – dann bricht in Figma ein Text anders um als im PDF und sollte nachgesehen
  werden.

Ganz zum Schluss, nur wenn wirklich etwas fehlt, im Stil des CV-Skills:

> Profilfoto einfügen, um die Skill Matrix zu vervollständigen

> Zertifikate als Bilder nachreichen, um die Skill Matrix zu vervollständigen

Fehlt nichts, steht hier nichts.

## Was fest steht und nicht zur Disposition steht

- **Zwei Fassungen, immer beide**, aus derselben `skillmatrix.json`: die lange
  (1444 breit, eine Seite) und die A4-Fassung (595 × 842, mehrseitig) – als PDF
  und, wenn gewünscht, als Figma-Frames. Keine Fassung allein, kein Inhalt, der
  nur in einer steht.
- **A4: Rand, Kopf und Fuß wie im Lebenslauf.** Logo auf jeder Seite, das Badge
  oben rechts auf Seite 1, der Fuß unten auf der letzten Seite; Fließtext 10pt;
  Kernkompetenzen und Tools als Zeilen ohne Karten in zwei Spalten, die
  Qualifikationskarte die einzige Karte mit Rahmen, Zertifikatskacheln ohne
  Rahmen; keine Kategorie und kein Eintrag über einen Seitenumbruch.
- **Das Porträt ist nie angeschnitten** – in keiner Fassung: Luft über dem
  Scheitel (`kopf-luft-anteil`), je Fotokarte ein eigener Zuschnitt.
- **Eine Sprache im ganzen Dokument.** Die gewählte Sprache gilt für jeden
  Satz – Rubriken, Hero-Beschreibung, jede Kartenbeschreibung. Gemischte
  Dokumente gibt es nicht. Ausgenommen sind Kategorienamen, Toolnamen und
  Attributnamen, die eingeführte Fachbegriffe sind (Namensregel in Schritt 0,
  Spalte „deutsch“ im Katalog).
  Das Renderskript warnt, wenn eine Beschreibung nach der falschen Sprache
  aussieht.
- **Hero-Beschreibung in der Ich-Perspektive.** In der Skill Matrix spricht
  der Kandidat selbst.
- **Sektionsreihenfolge**: Hero → Zertifikate → Kernkompetenzen → Tools →
  Fuß, wie in der Figma-Vorlage – in beiden Fassungen. Einzige zulässige Abweichung ist die
  Florian-Variante mit den Zertifikaten am Ende:
  `"zertifikate_position": "ende"` in der JSON. Nur auf Wunsch des Nutzers,
  Standard ist vorn.
- **Zertifikate als Kacheln, Sektion höchstens 924 hoch** – in PDF und Figma,
  bei jeder Zahl von Zertifikaten, die Karte „Erworbene Qualifikationen“
  eingerechnet. Reicht der Platz nicht, wird gebündelt (je Aussteller, zuletzt
  in einer Sammelkachel), nie still gestrichen – ein Zertifikat fällt nur mit
  Zustimmung des Nutzers weg.
- **Die Tags der Qualifikationskarte kommen aus den Zertifikaten.** Jedes Tag
  ist von einem gezeigten Zertifikat belegt; was nur Lebenslauf oder Portfolio
  hergeben, steht in den Kernkompetenzen.
- **Die Reihenfolge der Kategorien folgt der Anfrage**: Mit Anfrage steht die
  Kategorie zuerst, die für sie am wichtigsten ist, danach absteigend nach
  Bedeutung; ohne Anfrage steht die KI-Kategorie zuerst, danach die stärkste.
- **Jedes Attribut steht in seiner Katalog-Kategorie**, wenn die in der Matrix
  vorkommt, sonst in der nächstverwandten – nie in einer fachfremden und nie in
  der, die eine alte Matrix ihm gegeben hat. Höchstens fünf Kategorien, sechs
  Skills je Kategorie, 24 insgesamt; belegte Attribute fallen nur weg, wenn
  diese Grenzen es erzwingen.
- **Der graue Rumpf reicht bis an den Fuß** (lange Fassung). Zwischen der letzten Sektion und
  dem Fuß liegen 64 Innenabstand im Rumpf, kein weißer Streifen.
- **Bewertungsskala**: fünf Punkte – die erreichten gefüllt in der
  Markenfarbe, die übrigen als Ring (weiß, Rahmen 1,5 innen in
  `roh/punkt-rahmen`), gleich groß, in beiden Fassungen, PDF und Figma. Keine
  Prozente, keine Balken, keine Sterne.
- **Schriften: Rethink Sans für Name und Rolle, Inter für alles andere.** Die
  Schnitte liegen in `assets/fonts/` und werden eingebettet; fehlt eine Datei,
  bricht das Rendern ab, statt still eine Ersatzschrift zu setzen.
- **Farben, Abstände, Radien, Schatten und Maße** stehen ausschließlich in
  `assets/tokens.json` und stammen aus der Figma-Library der Masterdatei
  (Überblick in `references/layout.md`). Kein Wert wird im CSS, im Template oder
  im Figma-Plan von Hand gesetzt – kein Umbau, keine neuen Rubriken, keine
  anderen Werte ohne ausdrückliche Ansage.
- **Ansprechpartner im Fuß**: immer Manuel Klein, CCO. Steht als Vorgabe im
  Renderskript.
- **Keine anonymisierte Variante.** Name und Foto gehören ins Dokument.
- **Die PDFs sind der Ausgang, die Figma-Frames die Zugabe.** Sie werden nie
  statt der PDFs geliefert und nie vor ihnen gebaut.
- **Kein Inhalt aus der Vorlage bleibt stehen.** Weder ein Name noch ein
  Zertifikatsbild noch eine Beispielbeschreibung. Was das Material nicht
  hergibt, wird entfernt oder ausgeblendet – nie mit fremdem Inhalt
  ausgeliefert. Nach jedem Figma-Lauf muss die Rückgabe `reste` leer sein –
  ein sichtbarer Vorgabetext der Komponente ist ein Fehler, kein
  Schönheitsfehler.

## Wenn sich das Design System ändert

Einen Wert ändern heißt `assets/tokens.json` ändern – CSS, roher Figma-Plan und
Zuschnitt-Skripte ziehen von selbst nach. Hat sich das Design System in Figma
geändert, gilt der Abgleich in `references/layout.md`: Werte aus der
Masterdatei auslesen, `tokens.json` nachziehen, die Beispielmatrix rendern. Die
Designprüfung muss durchlaufen, und das Ergebnis wird neben den Figma-Frame
gelegt.

Ändert sich der Aufbau (ein neues Element, eine andere Verschachtelung), ziehen
`assets/template.html`, `assets/skillmatrix.css` und `scripts/figma_plan.py`
gemeinsam nach – für die A4-Fassung `assets/template-a4.html`,
`assets/skillmatrix-a4.css` und die `a4_*`-Funktionen in `figma_plan.py`. Die WeasyPrint-Eigenheiten (kein `box-shadow`, kein Grid, kein
CSS-Filter, warum `body` keinen Hintergrund haben darf) stehen in
`references/layout.md` – vor jeder Änderung lesen.

**Der Bibliotheksweg zieht Gestaltung von selbst nach** – Farben, Schriften und
Abstände kommen aus dem Master. Ändern sich dort Komponenten, Keys oder
Property-Namen, ist `assets/master-bibliothek.json` neu auszulesen (Rezept in
`references/figma.md`, „Den Katalog neu auslesen“), bei neuen Slots oder
umbenannten exponierten Instanzen auch `scripts/figma_bibliothek.py`.
