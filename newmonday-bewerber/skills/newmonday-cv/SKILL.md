---
name: newmonday-cv
description: Wandelt einen eingehenden Lebenslauf in einen Lebenslauf im New-Monday-Layout um – als PDF und als Figma-Frame, jeweils in zwei Fassungen, der vollständigen und einer anonymisierten (Platzhalterbild statt Foto, Initialen statt Name, keine Links). Eingang ist ein CV als PDF, ein LinkedIn-PDF-Export, ein LinkedIn-Profil-Link (daraus kommt das Profilfoto) oder eingefügter Profiltext. Nutze diesen Skill immer, wenn ein Lebenslauf, CV, Kandidatenprofil oder Bewerberprofil aufbereitet, umformatiert, "ins New Monday Layout gebracht", vereinheitlicht oder für Kunden aufbereitet werden soll – auch wenn nur ein Lebenslauf-PDF ohne Erklärung kommt, und auch dann, wenn das Wort "Layout" oder "New Monday" gar nicht fällt. Gilt ebenso, wenn ein anonymisiertes, neutralisiertes oder geschwärztes Kandidatenprofil, ein Blindprofil, ein Profil "ohne Namen" oder eine Fassung "ohne Foto" verlangt wird, und wenn der Lebenslauf in einem Figma-File, als Figma-Frame oder als bearbeitbare Datei für Designer landen soll.
---

# New Monday CV

Aus einem fremden Lebenslauf wird ein Lebenslauf im New-Monday-Layout. Bester
Eingang sind zwei Quellen: der Lebenslauf als PDF **und** der LinkedIn-PDF-Export. Das Layout
liegt als HTML/CSS-Template im Skill und stammt 1:1 aus der Figma-Datei
`oezbaw261xDwxthPuX3ZpS` ("Portfolio - CV Master", Seite "CV"). Jeder Designwert –
Schriften, Größen, Abstände, Farben – steht einmal in `assets/tokens.json`; PDF
und Figma-Frame lesen beide von dort. Das Template wird nicht neu erfunden und
nicht "verbessert" – es wird befüllt.

**Am Ende stehen vier Dateien, nicht eine**: das PDF und der Figma-Frame, jeweils
in der vollständigen und in einer anonymisierten Fassung. Alle vier entstehen in
jedem Lauf. Gefragt wird nicht mehr, *ob* etwas nach Figma soll, nur noch *wohin*.

## Die eine Regel, die alles andere schlägt

**Inhalte werden übernommen, nicht umgeschrieben.** Erlaubt ist ausschließlich das
Glätten von Rechtschreibung, Zeichensetzung und Grammatik. Nicht erlaubt:

- Formulierungen straffen, umstellen, "auf den Punkt bringen" oder aufwerten
- Aufgaben ergänzen, zusammenfassen oder in andere Worte fassen
- Zahlen, Zeiträume, Titel oder Kunden korrigieren, ergänzen oder plausibler machen
- Erfundene Angaben, auch keine "offensichtlich gemeinten"

Wenn etwas fehlt oder widersprüchlich ist: nicht raten, sondern am Ende auflisten
und nachfragen. Ein Lebenslauf ist ein Dokument über einen echten Menschen, das
an Kunden geht – jede stille Korrektur ist eine Behauptung, die jemand anders
verantworten muss.

Zwei Stellen sind davon ausgenommen, und nur diese beiden: das **Kurzprofil**
(gleich unten) und die **erste Station bei New Monday** (Schritt 2). Beide stehen
nicht im Eingang, weil sie nicht aus ihm stammen können.

Die anonymisierte Fassung ist **keine dritte Ausnahme**, sondern ein zweites
Dokument: Sie entsteht aus derselben `cv.json` und lässt nur weg, was auf die
Person zeigt. Jeder Satz in ihr steht wörtlich auch in der vollständigen Fassung.
Der einzige Eingriff in fremden Text ist die Namensnennung im Fließtext – und die
wird gemeldet, siehe "Die anonymisierte Fassung".

### Die erste Ausnahme: das Kurzprofil

Bringt der Eingang kein Kurzprofil mit, wird eines aus den Stationen gebaut. Das
ist der einzige Text im Dokument, der neu geschrieben wird. Dafür gilt:

- **Nur aus Material, das im Lebenslauf steht.** Rollen, Technologien, Projekte,
  Kundenarten, Jahreszahlen. Jeder Halbsatz muss sich auf eine Zeile im Eingang
  zurückführen lassen.
- **Keine Eigenschaftszuschreibungen.** Kein "erfahren", "leidenschaftlich",
  "lösungsorientiert", "Teamplayer". Wer jemanden charakterisiert, den er nicht
  kennt, erfindet.
- **Keine Abkürzungen auflösen**, deren Bedeutung nicht dasteht. Aus "WMS" wird
  nicht "Warehouse Management System", auch wenn es naheliegt.
- **Erste Person, drei bis vier Sätze**, im Ton des Beispiels in `beispiel/cv.json`.
- **Immer melden**, dass das Kurzprofil generiert ist, und den Text zur Freigabe
  hinstellen. Er geht an Kunden und behauptet etwas über einen echten Menschen.

Bringt der Lebenslauf ein Kurzprofil mit, wird dieses übernommen – dann greift
wieder die Regel oben, also nur Rechtschreibung.

### Die zweite Ausnahme: die Station bei New Monday

Jeder Lebenslauf beginnt mit New Monday als erster Station. Deren Inhalt kommt
nicht aus dem Eingang, sondern von New Monday selbst – und ist deshalb
vorgegeben, nicht frei formuliert. Wortlaut und Regeln stehen in Schritt 2 unter
"Die erste Station ist immer New Monday".

## Die anonymisierte Fassung

Jeder Lauf liefert den Lebenslauf zweimal: einmal vollständig, einmal
anonymisiert. Die anonyme Fassung ist für die Runde gedacht, in der ein Kunde ein
Profil bewertet, bevor er den Menschen dahinter kennt. Sie soll ihn dieselbe
Entscheidung treffen lassen wie die vollständige – nur ohne die Person zu
erkennen.

Deshalb ist sie **keine geschwärzte Version des Dokuments, sondern dasselbe
Dokument mit weniger Person darin**. Layout, Stationen, Logos, Bildung und
Skillset stehen unverändert. Was verschwindet, ist eng umrissen:

- **Das Foto** wird zum Platzhalterbild aus dem Design (`assets/silhouette.svg`,
  eingesetzt aus `assets/silhouette-vorlage.svg`, Vorgabe vom 29.09.2026) –
  gleiche Maße, gleiche Stelle wie das Foto. Es kommt auch dann, wenn die Person
  gar kein Foto hatte: eine leere Fotospalte sieht in dieser Fassung nach Panne
  aus, nicht nach Absicht.
- **Der Name** wird zu Initialen: aus "Timo Muster" wird "T. M.". Akademische
  Titel bleiben stehen ("Dr. T. M."), Namenspartikel wie "von" fallen weg.
- **Die Verweise** unter der Erfahrungszeile entfallen ganz. LinkedIn, Xing und
  Portfolio führen alle in einem Klick zum Namen.
- **Namensnennungen im Fließtext** werden mitgezogen, falls das Kurzprofil oder
  eine Stationsbeschreibung die Person beim Namen nennt. Der **volle** Name immer;
  ein **einzelner** Namensteil nur, wenn nichts im Dokument dagegenspricht. Heißt
  jemand "Mai" oder war er bei der "Feiler GmbH", bleibt das einzelne Wort stehen
  und wird gemeldet – der Skill zerschießt lieber keinen Satz, als einen zu raten.
  **Diese Meldungen müssen gelesen werden**: Darunter kann eine echte
  Namensnennung sein, die dann von Hand in die `cv.json` gehört.

Drei Stellen kommen dazu, die im Dokument selbst nicht zu sehen sind und genau
deshalb übersehen werden:

- **Der Dateiname.** `New-Monday - T. M. - UX Designer - CV.pdf`. Ein Anhang, der
  im Namen den Kandidaten trägt, macht das Dokument darin sinnlos.
- **Der PDF-Titel in den Metadaten.** Er steht in der Fensterleiste jedes
  PDF-Betrachters, noch bevor jemand die erste Seite gelesen hat.
- **Die Frame- und Seitennamen in Figma.**

Alle drei stammen aus `person.name`. Deshalb wird nicht im Renderer
anonymisiert, sondern eine Stufe davor: `anonymisieren.py` schreibt eine zweite
`cv.json`, und **dieselbe** Kette läuft ein zweites Mal darüber (Schritt 4). Es
gibt keinen anonymen Modus im Renderer und keine zweite Vorlage – beide Fassungen
sind derselbe Skill über andere Daten, und deshalb können sie nicht
auseinanderlaufen.

### Was bewusst stehen bleibt

**Arbeitgeber, Kunden, Logos, Bildungseinrichtungen und die monatsgenauen
Zeiträume bleiben drin.** Sie sind der Grund, warum jemand das Profil überhaupt
liest – ein Lebenslauf ohne Firmen ist kein anonymer Lebenslauf, sondern keiner.
Die Fassung schützt davor, dass jemand die Person **erkennt**; sie schützt nicht
davor, dass jemand sie **ermittelt**, der es darauf anlegt. Wer das zweite
braucht, sagt es, und dann gelten die Stufen unten.

**Der Footer bleibt vollständig.** Manuel Klein steht dort mit Mail und Telefon.
Das ist die einzige Adresse, unter der ein Kunde nach diesem Profil fragen kann –
und genau dafür ist die Fassung gemacht.

**Anonym ist das PDF, nicht das Figma-File.** In der Figma-Datei liegen beide
Fassungen nebeneinander, und ihr Dateiname trägt den vollen Namen – anders ginge
es nicht, sie ist ja die Arbeitsdatei. Wer den Figma-Link weitergibt, gibt damit
die vollständige Fassung weiter. **Das gehört in die Übergabe**, jedes Mal: Der
Unterschied ist niemandem anzusehen, der nur den Link bekommt.

### Wenn mehr weg soll

Vier Stufen, die es gibt, aber nur auf ausdrückliche Ansage. **Von selbst wird
keine davon gezogen**: Jede kostet Aussagekraft, und wie viel davon vertretbar
ist, entscheidet nicht der Skill.

| Stufe | Wie |
|---|---|
| **Zeiträume nur als Jahre** | `--jahre` am Skript. Monatsgenaue Daten machen den Abgleich mit einem LinkedIn-Profil zur Fingerübung – das ist die wirksamste der vier Stufen. |
| **Firmen und Kunden generisch** | Eine Zuordnung `{"Cocomore": "Digitalagentur"}` schreiben und mit `--firmen-map` übergeben. Das Skript entfernt die Logos der ersetzten Firmen gleich mit; ein Logo neben "Digitalagentur" hebt die Anonymisierung sofort wieder auf. Die Oberbegriffe erfindet es nicht. |
| **Bildungseinrichtungen generisch** | Handarbeit in der `cv.json`, vor dem Anonymisieren: aus "TU Braunschweig" wird "Technische Universität". Abschluss und Fach bleiben stehen. |
| **Sprachen im Skillset** | Handarbeit in der `cv.json`, nur für Sprachen über Deutsch und Englisch hinaus – die beiden setzt das Renderskript ohnehin gleich für alle. "Armenisch – Muttersprache" verrät regelmäßig die Herkunft und steht selten in einem Zusammenhang mit der Stelle. |

Die beiden unteren Zeilen sind bewusst kein Schalter: Welcher Oberbegriff für eine
Hochschule noch stimmt und welcher Skillset-Eintrag eine Muttersprache ist, kann
ein Skript nicht entscheiden, ohne zu raten – und geraten wird in diesem Skill
nirgends.

## Umgebung

Der Skill läuft überall gleich, aber die Umgebungen unterscheiden sich in drei
Punkten. Beim ersten Lauf auf einem unbekannten System zuerst:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/pruefe_umgebung.py
```

Das nennt fehlende Abhängigkeiten samt Installationsbefehl für das jeweilige
System. Meldet es Lücken, dem Nutzer den Befehl weiterreichen statt zu raten.

- **Render-Engine**: Das Layout ist auf WeasyPrint abgestimmt. Fehlt sie, weicht
  das Skript auf Chrome aus und sagt das auch – dann Seitenumbrüche und
  Skillset-Spalten gegenprüfen, bevor die PDFs rausgehen.
- **Netz**: Lokal und in Claude Desktop ist es offen, im Browser-Chat blockt der
  Proxy fremde Domains. Das betrifft nur die Logosuche, siehe Schritt 3.
- **Ausgabeort**: In Claude Code ins Arbeitsverzeichnis des Nutzers schreiben,
  nicht in den Skill-Ordner. Im Browser-Chat nach `/mnt/user-data/outputs/`.
  Die einzige Ausnahme sind neue Logos: die gehören dauerhaft in
  `assets/logos/`, damit die Bibliothek wächst.

Für die Installation gibt es `INSTALL.md` – die ist für den Nutzer geschrieben,
nicht für dich, und kann bei Einrichtungsfragen weitergereicht werden.

## Im Gesamtlauf

Dieser Abschnitt gilt nur, wenn der Auftrag mit „Gesamtlauf
newmonday-bewerbermappe“ beginnt. Dann läuft dieser Skill als Subagent in einer
von zwei Phasen, und der Auftrag bringt die allgemeinen Regeln mit: keine
Rückfragen, Laufordner, `auftrag.json`, die Formate in
`newmonday-bewerbermappe/references/formate.md`. Hier steht nur, was für den
Lebenslauf dazukommt. Wo dieser Abschnitt etwas regelt, geht er dem Rest des
Skills vor; im Einzellauf gilt er nicht.

**Schritt 0 entfällt.** Was er einholt, steht in `auftrag.json`:

| Schritt 0 | aus `auftrag.json` |
|---|---|
| Sprache | `sprache` |
| Figma-Ziel | `figma.link` – er trägt die `node-id` der Kandidatenseite, also gilt in `references/figma.md` „Zielseite“ mit `node-id`. Ist `figma.aktiv` false, entfällt Schritt 4a. |
| Lebenslauf, LinkedIn-Export und -Link, Xing, Portfolio, Foto, Logos | `material` |

**Phase vorbereiten: Schritte 1 bis 1c.** Statt der Frage-Nachricht aus Schritt
1d entsteht `fragen.json`:

- `fragen`: `nm_rolle` und `nm_start` immer, `fachfremd` und `weiterbildung`
  nur, wenn es etwas zu entscheiden gibt – Wortlaut, Optionen, `multiSelect` und
  „(Empfohlen)“ genau wie in Schritt 1d. Entstünde durch das Streichen einer
  Station eine Lücke, steht sie in der `description` dieser Option.
- `luecken`: „Profilfoto“, wenn Schritt 1a bei „beim Kandidaten anfragen“ endet
  oder das beste Foto unter 200 dpi liegt – die Folge nennt die dpi-Zahl bzw.
  „die Fotospalte bleibt leer“, die Form „Bilddatei, Porträt, gut aufgelöst“.
- `texte`: leer.

In `notizen.md`:

- die gewählte Fotoquelle mit Datei, dpi und – bei Website-Fotos – Bildadresse;
- jede Abweichung zwischen Lebenslauf, LinkedIn und Portfolio mit beiden Werten
  (Schritte 1b und 1c) und welche Fassung ins Dokument kommt;
- Kunden, die der Lebenslauf anonymisiert und das Portfolio beim Namen nennt;
- was aus dem Portfolio ergänzt werden soll, Feld für Feld;
- die Pfade der Auszüge (`arbeit/…/text.txt`).

Keine `cv.json`, keine Logos, nichts rendern.

**Phase bauen: Schritte 2 bis 5**, beide Fassungen. Die Antworten stehen in
`entscheidungen.newmonday-cv`:

- `nm_rolle`, `nm_start` → Titel und Zeitraum von `stationen[0]` und die
  Textbausteine dazu (Schritt 2). Ein eigener Titel über „Other“ wird genommen,
  wie er dasteht.
- `fachfremd`, `weiterbildung` → die angehakten Einträge bleiben drin, alle
  anderen aus der Frage fallen weg. Fehlt die `id`, gab es nichts zu entscheiden
  – dann bleibt alles drin.

Stationen mit mehreren Marken (Schritt 3): ohne Rückfrage in einer Station, alle
Logos als Liste in `logo`, und das unter „Ohne Rückfrage entschieden“. Die
Übergabe aus Schritt 5 geht nach `uebergabe.md`: Kurzprofil unter „Zur
Freigabe“, die Abweichungen aus `notizen.md` unter „Quellen weichen ab“, der
Hinweis auf den vollen Namen im Figma-File und alles Übrige unter „Hinweise“, die
beiden Schlusszeilen wörtlich unter „Fehlt noch“.

## Gefragt wird mit Klickboxen, nicht im Fließtext

**Jede Frage, deren Antwort aus einer überschaubaren Menge stammt, läuft über
`AskUserQuestion`** – die klickbaren Kästchen in Claude Code. Das gilt für jede
Rückfrage in diesem Skill: Sprache, Figma-Ziel, Rolle bei New Monday,
Startmonat, fachfremde Stationen, Weiterbildungen. Auch dann, wenn die Frage kurz ist und im Fließtext
schneller getippt wäre. Der Nutzer soll klicken, nicht tippen.

Nur zwei Dinge stehen weiter als Text in derselben Nachricht:

- **Material**, das der Nutzer schicken muss: Dateien, Links, Logos, Foto. Dafür
  gibt es nichts anzuklicken.
- **Freigaben und Berichte** am Ende (Schritt 5). Das ist eine Übergabe, keine
  Frage.

Fragen werden gebündelt: `AskUserQuestion` nimmt bis zu vier Fragen auf einmal.
Der Skill kommt mit **zwei** solchen Nachrichten aus – einer vor dem Auslesen
(Schritt 0) und einer vor dem Bauen der `cv.json` (Schritt 1d). Wo mehr als vier
Fragen zusammenkämen, werden sie zusammengelegt, nicht in eine dritte Nachricht
ausgelagert.

Bei jeder Frage steht die Option zuerst, die aus dem Eingang am
wahrscheinlichsten folgt, mit `(Empfohlen)` im Label. Geraten wird damit nicht:
Die Entscheidung trifft weiterhin der Nutzer, er hat sie nur schneller.

Rote Flagge: Du tippst gerade eine Frage samt Antwortmöglichkeiten in den
Fließtext. Dann gehört sie in `AskUserQuestion`.

## Ablauf

Alle Aufrufe unten nutzen `${CLAUDE_SKILL_DIR}` — den Ordner, in dem diese
SKILL.md liegt. Das Arbeitsverzeichnis ist das des Nutzers, nicht das des Skills;
relative Pfade wie `scripts/render_cv.py` gehen deshalb ins Leere. Wird die
Variable in deiner Umgebung nicht ersetzt, steht sie für genau diesen Ordner.

### 0. Vor dem Start fragen — immer, in einer einzigen Nachricht

Bevor irgendetwas gebaut wird, diese Punkte klären. Gebündelt, nicht
nacheinander: der Nutzer soll alles auf einmal beantworten und liefern können.

1. **Die Sprache.** Als `AskUserQuestion`, nicht als Fließtext:

   ```
   Frage:   Soll der Lebenslauf auf Deutsch oder Englisch sein?
   Header:  Sprache
   Optionen: Deutsch  |  Englisch
   ```

   Das entscheidet über die Rubriken im Dokument und darüber, in welcher Sprache
   das Kurzprofil geschrieben wird. Die Frage wird **immer** gestellt, auch wenn
   der Eingang eindeutig einsprachig aussieht – ein englischer Lebenslauf kann
   trotzdem für einen deutschen Kunden gedacht sein. Die Antwort kommt als
   `"sprache": "de"` oder `"sprache": "en"` in die `cv.json`.

   Ist die gewählte Sprache nicht die des Eingangs, muss übersetzt werden. Das
   ist eine bewusste Ausnahme von der Regel oben und braucht eine ausdrückliche
   Ansage – von sich aus wird nie übersetzt.

2. **Wohin der Figma-Frame soll.** Nicht mehr *ob*: Der bearbeitbare Frame
   entsteht in jedem Lauf, genau wie das PDF. Gefragt wird nur nach dem Ziel,
   ebenfalls als `AskUserQuestion`, direkt neben der Sprachfrage:

   ```
   Frage:   In welches Figma-File soll der Lebenslauf?
   Header:  Figma
   Optionen: In ein bestehendes File – ich schicke den Link (Empfohlen)
           | Leg ein neues File an
   ```

   Bei der ersten Option braucht es den Link – Material, also im Text derselben
   Nachricht, wörtlich so:

   > Schick mir den Link zum Figma-File, in das der Lebenslauf soll
   > (figma.com/design/…). Zeigt der Link auf eine bestimmte Seite, lege ich ihn
   > dort ab, sonst auf einer neuen Seite. Ich brauche Bearbeitungsrechte auf
   > der Datei.

   Die Frames entstehen erst nach dem Rendern, siehe Schritt 4a. Drei Regeln dazu:

   - **Kommt der Link nicht**, wird er einmal im Fließtext nachgefragt – nicht
     über eine dritte `AskUserQuestion`-Nachricht. Bleibt er weiter aus, wird ein
     neues File angelegt, als wäre die zweite Option gewählt worden. Ein fehlender
     Link ist kein Grund, die bearbeitbare Fassung ausfallen zu lassen.
   - **Figma hält die PDFs nicht auf.** Geht dort etwas schief, gehen die PDFs
     trotzdem raus und der Grund steht in der Übergabe. Ein Lebenslauf ohne
     Figma-Frame ist vollständig.
   - **Nur Design-Dateien.** `figma.com/design/…` ja; `/board/` (FigJam),
     `/slides/`, `/make/` und `/proto/` nein. Dann sagen, was gebraucht wird,
     statt es zu versuchen – oder das neue File anlegen.

3. **Firmenlogos als SVG.** Die Logodatenbanken der Skripte führen globale
   Marken zuverlässig, deutsche Agenturen und Mittelständler dagegen fast nie.
   Genau die stehen aber in den meisten Lebensläufen. Deshalb gleich zu Beginn
   darum bitten, die Logos der Arbeitgeber als SVG mitzuschicken – am besten aus
   dem Presse- oder Brand-Bereich der jeweiligen Firmenseite. Was schon in
   `assets/logos/` liegt, muss nicht noch einmal geliefert werden.

   Die Bitte ist eine Abkürzung, keine Bedingung: Was nicht kommt, suchst du
   selbst, siehe Schritt 3.

4. **Die Profile.** Material, also im Text derselben Nachricht, wörtlich so:

   > Gibt es ein LinkedIn-Profil? Wenn du mir den Link schickst
   > (linkedin.com/in/…), ziehe ich das Profilfoto automatisch. Ein
   > Xing-Profil nehme ich auch – es kommt als Verweis mit ins Dokument.

   Ist das LinkedIn-Profil öffentlich, holt `linkedin_foto.py` das Foto von dort
   – siehe Schritt 1a. Das erspart das Heraussuchen und Zuschneiden von Hand.
   Der Link ist **zusätzlich** zum PDF-Export nützlich, nicht statt seiner: für
   die Inhalte taugt er nichts (siehe Schritt 1), fürs Foto schon. Beide Profile
   landen außerdem als Verweis in den Profilkopf des Dokuments, siehe `links` in
   Schritt 2. Aus Xing wird kein Foto geholt, der Link steht nur im Dokument.

5. **Das Portfolio.** Ebenfalls als Text, wörtlich so:

   > Gibt es ein Portfolio? Entweder als Link zur Website oder als PDF – ich
   > setze den Verweis in den Profilkopf und kann fehlende Angaben daraus
   > ergänzen.

   Drei Dinge hängen daran: der Verweis im Profilkopf, eine dritte Quelle für
   Lücken (Schritt 1c) und, wenn sonst nichts ein Foto hergibt, eine dritte
   Fotoquelle (Schritt 1a). Ein PDF taugt nur als Quelle, verlinken lässt es sich
   nicht – dann bleibt die Zeile weg oder trägt einen Hinweis ohne Adresse.

   **Kommt nichts, wird das übersprungen.** Nicht nachhaken, nicht als fehlend
   melden: Ein Lebenslauf ohne Portfolio ist vollständig. Die Verweise im
   Profilkopf zeigen nur, was da ist, und entfallen ganz, wenn es weder Profil
   noch Portfolio gibt.

6. **Ein Foto**, falls weder LinkedIn noch die Website eins hergeben (beides
   siehe Schritt 1a). Bringt der Lebenslauf keins mit und führt auch kein Link
   dorthin, danach fragen: als Bilddatei schicken lassen, `extract_input.py`
   wandelt sie in Graustufen und schneidet sie aufs Layoutformat zu. Ohne Foto
   funktioniert das Layout, wirkt aber leer – die Fotospalte bleibt frei.

Ebenfalls hier erwähnen, falls noch nicht vorhanden: den LinkedIn-PDF-Export
(siehe Schritt 1). Er gehört in dieselbe Nachricht.

Das ist **eine** Nachricht: Sprache und Figma als die beiden Klickboxen, die
Punkte 3 bis 6 als Text daneben. Rolle und Startmonat bei New Monday werden hier noch nicht
gefragt — für einen brauchbaren Vorschlag muss der Lebenslauf erst gelesen sein,
deshalb stehen sie in Schritt 1d.

### 1. Eingang auslesen

**Immer nach dem LinkedIn-PDF-Export fragen, nicht nur bei Lücken.** Der Export
enthält regelmäßig Dinge, die im Lebenslauf fehlen oder unscharf sind:
Arbeitgebernamen, feiner aufgeschlüsselte Rollen und Zeiträume, zusätzliche
Tätigkeiten, und ein Profilfoto. Im Testfall war der aktuelle Arbeitgeber im
Lebenslauf nur als "Zeitarbeit in Maschinenbau Unternehmen" beschrieben – aus dem
Export ging hervor, dass der Arbeitgeber Hays heißt und das Maschinenbau-
unternehmen dessen Kunde ist. Ohne den Export wäre eine ganze Station falsch
strukturiert gewesen.

Formulierung an den Nutzer: "Schick mir bitte zusätzlich Timos LinkedIn-Profil als
PDF (auf dem Profil: *Mehr* → *Als PDF speichern*) und den Link zum Profil."

Für die **Inhalte** ersetzt der Link den PDF-Export nicht: Der Web-Abruf der
Profilseite scheitert an der Login-Wall, verlässlich mit `ROBOTS_DISALLOWED`.
Fürs **Foto** dagegen genügt der Link, siehe Schritt 1a.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <eingang.pdf> arbeit/
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <foto.jpg> arbeit/     # Foto separat geliefert
```

Schreibt `arbeit/text.txt` und legt Porträtkandidaten in `arbeit/fotos/` ab
(bereits in Graustufen und auf das Layoutformat beschnitten). Aus PDFs werden
Logos und Alphamasken über einen Entropiefilter aussortiert; bleiben mehrere
Fotos übrig, das größte prüfen. Bei einer einzeln gelieferten Bilddatei greift
der Filter nicht, da ist die Absicht ja klar.

Kein Foto auffindbar: erst Schritt 1a, dann anfragen. Das Layout funktioniert ohne.

### 1a. Das Foto selbst holen — erst LinkedIn, dann die Website

**Die Rangfolge der Fotoquellen. Der Lebenslauf zuerst:**

1. **Das Foto aus dem Lebenslauf**, sobald `extract_input.py` einen brauchbaren
   Porträtkandidaten daraus gezogen hat. Ein separat geschicktes Bild zählt
   gleichrangig – auch das hat der Kandidat für diese Bewerbung ausgewählt.
2. **LinkedIn** (`linkedin_foto.py`), wenn der Lebenslauf keins mitbringt.
3. **Portfolio oder eigene Website** (`website_foto.py`), wenn auch LinkedIn
   nichts hergibt.
4. **Beim Kandidaten anfragen**, wenn keine der drei Quellen etwas liefert.

**Ein schöneres Foto im Portfolio ändert daran nichts.** Führt das Portfolio ein
größeres, schärferes oder freundlicheres Bild, kommt trotzdem das aus dem
Lebenslauf ins Dokument. Der Kandidat hat es dort für genau diesen Zweck
hingelegt; das Portfoliobild ist für eine andere Bühne gemacht – und wer auf
einer Website abgebildet ist, weiß `website_foto.py` ohnehin nicht (siehe unten).
Nicht abwägen, welches besser wirkt, und nicht nachfragen, welches lieber
genommen werden soll.

Die eine Ausnahme ist **technische Unbrauchbarkeit**: Das Foto aus dem
Lebenslauf ist beschnitten, zeigt kein Porträt oder liegt so klein vor, dass es
im Layoutformat (79 × 106pt) sichtbar pixelt – dieselbe 200er-dpi-Grenze wie
unten. Dann darf eine andere Quelle einspringen; in die Übergabe gehört, welche
und warum.

Liegt ein Profil-Link vor und hat der Eingang kein brauchbares Foto ergeben:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/linkedin_foto.py "https://www.linkedin.com/in/timo-muster" arbeit/
```

Das Skript nimmt volle URLs, `de.linkedin.com`-Adressen und den blanken
Profilnamen. Es legt das Foto fertig zugeschnitten in `arbeit/fotos/` ab – im
selben Format wie `extract_input.py`, also direkt als `foto` in die `cv.json`
eintragbar.

**Die dpi-Zeile in der Ausgabe lesen.** Über diesen Weg sind je nach Profil nur
etwa 136 bis 270 dpi erreichbar; LinkedIn signiert jede Bildgröße einzeln,
größere Varianten antworten mit 403. Unter 200 dpi warnt das Skript – dann ist
das Foto für ein Kundendokument sichtbar weich, und es lohnt, beim Kandidaten
ein richtiges Bild anzufragen. Der Automatismus spart Handarbeit, ersetzt aber
kein ordentliches Foto.

Was das Skript **nicht** kann, und was daran nicht zu reparieren ist:

- **Nur öffentliche Profile.** Steht die Fotosichtbarkeit auf "Nur Kontakte"
  oder ist das Profil nicht öffentlich, kommt kein Foto. Das Skript sagt das.
- **`HTTP 999` ist doppeldeutig.** Es kommt sowohl bei nicht existierenden oder
  nicht öffentlichen Profilen als auch dann, wenn zu viele Abrufe kurz
  hintereinander laufen – im Test antworteten zuvor funktionierende Profile
  nach einigen Abrufen plötzlich ebenfalls mit 999. Das Skript fasst zweimal
  mit Backoff nach. Bleibt es dabei, die URL im ausgeloggten Browser
  gegenprüfen, bevor du dem Nutzer sagst, das Profil sei nicht öffentlich.
- **Im Browser-Chat blockt der Proxy** `linkedin.com` wie jede fremde Domain.
  Dort führt nur der PDF-Export oder die gelieferte Bilddatei zum Ziel.

**Das Ergebnis ansehen, bevor es ins Dokument geht.** Auf der öffentlichen
Profilseite stehen unter "Weitere ähnliche Profile" die Fotos fremder Personen
– gemessen 13 fremde neben dem einen echten, und ausgerechnet die fremden
liegen in der größeren Variante vor. Das Skript verankert die Auswahl deshalb
am `og:image`-Tag, der immer zum Profil selbst gehört. Trotzdem gilt: Ein
falsches Gesicht in einem Kandidatenprofil fällt niemandem auf, der die Person
nicht kennt – ein Blick auf das Foto kostet zwei Sekunden.

#### Gibt LinkedIn nichts her, kommt die Website dran

Erst hier, also wenn weder der Lebenslauf noch LinkedIn ein Foto hergeben. Liegt
ein Portfolio oder eine eigene Website vor (Schritt 0), steht das Foto oft dort –
auf "Über mich", "Profil" oder der Teamseite, und häufig größer als das
400×400-Thumbnail von LinkedIn:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/website_foto.py "https://timo-muster.de" arbeit/
```

Das Skript liest die Startseite und bis zu drei Unterseiten, die nach Porträt
klingen, lädt deren Bilder und wirft weg, was technisch kein Porträt sein kann:
querformatig, winzig, zweifarbig, SVG. Was übrig bleibt, liegt fertig
zugeschnitten in `arbeit/fotos/`, je Kandidat mit Bildadresse und dpi-Zahl –
dieselbe 200er-Grenze wie oben.

**Wer auf dem Bild ist, weiß das Skript hier nicht.** Bei LinkedIn hängt die
Auswahl am `og:image` des Profils, auf einer Website an nichts: Teamfotos,
Kundengesichter, Stockmaterial und Keyvisuals laufen durch denselben Filter. Im
Test lieferte eine Agenturseite als größten Kandidaten ein Jubiläums-Keyvisual
und erst danach den Gründer. Also jeden Kandidaten ansehen und mit dem Bild aus
dem LinkedIn-Export oder dem Lebenslauf abgleichen, bevor eins ins Dokument
geht. Bleibt unklar, wer da steht: nicht einsetzen, sondern anfragen.

Manche Seiten weisen automatische Abrufe ab (`HTTP 403`), im Browser-Chat blockt
der Proxy fremde Domains ohnehin. Dann ist dieser Weg zu Ende und das Foto wird
beim Kandidaten angefragt.

### 1b. Zwei Quellen zusammenführen

Liegen Lebenslauf und LinkedIn-Export vor, gilt:

- **Bei Widersprüchen gewinnt immer der Lebenslauf.** Abweichende Zeiträume,
  andere Jobtitel, andere Firmennamen: Die Fassung aus dem Lebenslauf kommt ins
  Dokument, ohne Rückfrage. Nicht abwägen, welche plausibler wirkt – der
  Lebenslauf ist das, was die Person selbst für die Bewerbung aufbereitet hat.
- **Die Abweichung wird trotzdem gemeldet**, am Ende in der Übergabe, mit beiden
  Werten. Manche sind Tippfehler, die jemand korrigieren möchte: In einem Test
  stand eine Station im Lebenslauf auf "November 2021 – April 2022" und in
  LinkedIn ein volles Jahr früher; die Fassung aus dem Lebenslauf überlappte
  dabei die vorherige Station vollständig. Ins Dokument kam trotzdem die
  Lebenslauf-Fassung, in die Übergabe der Hinweis.
- **LinkedIn ergänzt, wo der Lebenslauf schweigt.** Das ist kein Widerspruch,
  sondern eine Lücke. Im Test hieß ein Arbeitgeber im Lebenslauf nur "Zeitarbeit
  in Maschinenbau Unternehmen"; aus dem Export ging hervor, dass der Arbeitgeber
  Hays heißt und das Maschinenbauunternehmen dessen Kunde ist. Ohne den Export
  wäre eine ganze Station falsch strukturiert gewesen.
- **Bei unterschiedlichem Detailgrad** die feinere Angabe nehmen, solange sie der
  gröberen nicht widerspricht.
- **Firmennamen sind die eine Ausnahme.** Sie werden in der vollständigen Form
  aus LinkedIn übernommen, auch wenn der Lebenslauf sie kürzt: "Cocomore AG"
  statt "Cocomore", "VALID Digitalagentur GmbH" statt "Valid Digital Agentur",
  "3pc GmbH Neue Kommunikation" statt "3pc Neue Kommunikation". Das ist kein
  Widerspruch in der Sache, sondern die genauere Schreibweise derselben Firma –
  und in einem Kundendokument gehört die vollständige Firmierung hin. Gilt nur
  für den Namen; Zeitraum, Jobtitel und Inhalte bleiben beim Lebenslauf.
- **LinkedIn-Artefakte ignorieren.** Die Rubrik "Top-Kenntnisse" ist
  algorithmisch erzeugt und gehört nicht ins Dokument. Ortsangaben kommen
  teilweise lokalisiert zurück ("Circondario di Paderborn" für den Kreis
  Paderborn) – solche Formen nicht übernehmen. Freiberufliche Stationen stehen
  oft jahrelang auf "Present", weil nie ein Enddatum gesetzt wurde; in einem Test
  ergaben sich daraus 25 angeblich laufende Engagements. Auch hier gilt der
  Lebenslauf.
- Tippfehler aus LinkedIn wie jede andere Rechtschreibung glätten ("Jesmine" →
  "Jasmine").

### 1c. Das Portfolio als dritte Quelle

Liegt ein Portfolio vor, wird es gelesen, bevor irgendwo "unklar" steht:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_input.py <portfolio.pdf> arbeit/portfolio/
```

Bei einer Website die Seite abrufen und die Projektseiten dazu. Was dort steht,
schließt Lücken, die Lebenslauf und LinkedIn offen lassen: Kundennamen zu
Projekten, die im Lebenslauf nur als Gattung stehen, Zeiträume, Technologien,
Rollen. Dieselbe Rangfolge wie in Schritt 1b – **der Lebenslauf schlägt beides**,
und das Portfolio ergänzt nur, wo er schweigt.

Drei Grenzen, die auch hier gelten:

- **Ein Portfolio ist Eigenwerbung.** Bewertende Formulierungen ("preisgekrönt",
  "führend", "innovativ") gehören nicht in den Lebenslauf, auch nicht sinngemäß.
  Übernommen werden Fakten: wer, wann, was, womit.
- **Kunden aus dem Portfolio nicht ungefragt einsetzen.** Wenn der Lebenslauf
  einen Kunden bewusst als "Speditionsdienstleister" anonymisiert, das Portfolio
  ihn aber beim Namen nennt, ist das kein Fund, sondern eine Entscheidung, die
  jemand getroffen hat. In die Übergabe damit, nicht ins Dokument.
- **Das Foto aus dem Portfolio bleibt liegen, wenn der Lebenslauf eins hat.**
  `extract_input.py` legt auch aus dem Portfolio-PDF Porträtkandidaten in
  `arbeit/portfolio/fotos/` ab – die sind nur dann dran, wenn Lebenslauf und
  LinkedIn nichts hergeben. Rangfolge und die eine Ausnahme stehen in Schritt 1a.

Was aus dem Portfolio kam, wird in der Übergabe genannt – Feld für Feld.

### 1d. Die zweite Frage-Nachricht — alles, was vor der `cv.json` offen ist

Eine einzige `AskUserQuestion`-Nachricht, gestellt **nach** dem Auslesen
(Schritte 1 bis 1c) und **vor** der `cv.json`. Vier Fragen passen hinein, mehr
nimmt das Werkzeug nicht:

1. **Die Rolle bei New Monday** – Titel der ersten Station, siehe Schritt 2.
2. **Der Startmonat bei New Monday** – Zeitraum derselben Station.
3. **Fachfremde Stationen** – rein oder raus.
4. **Weiterbildungen** – rein oder raus.

Die ersten beiden werden immer gefragt, die anderen beiden nur, wenn es etwas zu
entscheiden gibt. So sehen sie aus:

```
Frage:   Wie heißt die Rolle bei New Monday?
Header:  NM-Rolle
Optionen: User Experience Design Specialist (Empfohlen)
        | Software Development Specialist
```

```
Frage:   Ab wann ist <Vorname> bei New Monday?
Header:  NM-Start
Optionen: August 2026 (Empfohlen)   — der laufende Monat
        | September 2026            — der folgende Monat
```

Die empfohlene Option ist die, die zum Eingang passt: Bei einem UX-Lebenslauf
steht die UX-Rolle vorn, bei einem Entwicklerlebenslauf die Entwicklerrolle. Für
alles andere trägt der Nutzer über "Other" seinen eigenen Titel bzw. Monat ein –
etwa `Senior Frontend Developer` oder `Januar 2027`.

**Bis die Antworten da sind, wird nicht gebaut.** Titel und Zeitraum der ersten
Station lassen sich nicht nachträglich einsetzen, ohne Erfahrungsjahre und
Seitenumbrüche noch einmal durchzugehen.

#### Fachfremdes und Weiterbildungen — fragen, nicht entscheiden

New Monday vermittelt UX-Design und Entwicklung. Lebensläufe bringen daneben
regelmäßig Stationen mit, die damit nichts zu tun haben: eine Ausbildung zum
Bankkaufmann, zwei Jahre Gastronomie, Zivildienst, ein Nebenjob im Einzelhandel,
ein Ehrenamt. **Beides ist falsch – sie stillschweigend übernehmen und sie
stillschweigend weglassen.** Weglassen kann ein Profil straffen oder eine Lücke
in den Lebenslauf reißen, die der Kunde bemerkt; drinlassen kann Ballast sein
oder genau der Grund, warum jemand die Branche kennt, für die er sich bewirbt.
Das entscheidet der Nutzer, nicht du.

Dieselbe Nachricht klärt die zweite Frage: **Weiterbildungen rein oder raus?**
Zertifikatskurse, Bootcamps, Onlinekurse, Seminare, Lehrgänge. Auch die stehen
oft mitten zwischen den Berufsstationen, und ob sie ins Kundendokument gehören,
ist eine Entscheidung, keine Ableitung.

Beides sind zwei weitere Fragen derselben `AskUserQuestion`-Nachricht, je eine
mit `multiSelect`. Die Einträge selbst sind die Optionen, mit Zeitraum, damit
niemand raten muss, welche Station gemeint ist:

```
Frage:   Welche fachfremden Stationen sollen mit rein?
Header:  Fachfremd
multiSelect: ja
Optionen: Verkäufer, Media Markt (2014 – 2016)
        | Zivildienst, DRK Braunschweig (2013 – 2014)
```

```
Frage:   Welche Weiterbildungen sollen mit rein?
Header:  Weiterbildung
multiSelect: ja
Optionen: Professional Scrum Master I (2022)
        | Google UX Design Certificate (2021)
```

Angehakt heißt rein, nicht angehakt heißt raus. Stehen mehr als vier Einträge zur
Wahl – mehr Optionen nimmt eine Frage nicht –, treten an ihre Stelle
`Alle rein` / `Alle raus`, und der Nutzer nennt Ausnahmen über "Other".

Dazu gilt:

- **Nicht der Titel entscheidet, sondern die Tätigkeit.** Ein "Werkstudent
  Marketing", der die Website betreut hat, gehört in die Liste, nicht in eine
  stille Entscheidung. Im Zweifel fragen – die Liste ist billig, eine falsch
  gestrichene Station nicht.
- **Nichts vorsortieren.** Aufgeführt wird alles, was in Frage steht. Ein
  Vorschlag dazu ist erlaubt, die Entscheidung nicht.
- **Lücken benennen.** Entsteht durch das Weglassen ein Loch von mehr als ein
  paar Monaten, steht das in derselben Nachricht.
- **Weiterbildungen, die drin bleiben, stehen unter `bildung`** – nie als
  Station. Und sie zählen **nicht als Berufserfahrung**: `erfahrung` rechnet
  ohne sie, genau wie ohne Ausbildung und Studium.
- **Ist alles einschlägig, entfällt die Frage.** Keine Frage um der Frage
  willen, und keine Liste mit einer einzigen Zeile, die offensichtlich dazu
  gehört.
- **Bis die Antwort da ist, wird nicht gebaut.** Eine Station nachträglich
  herauszunehmen heißt, Erfahrungsjahre, Logos und Seitenumbrüche noch einmal
  durchzugehen.

### 2. Daten strukturieren

Aus dem Text eine `cv.json` bauen. Vollständiges Beispiel: `beispiel/cv.json`.

```json
{
  "sprache": "de",
  "person": {
    "name", "rolle", "erfahrung", "foto", "kurzprofil",
    "links": [{ "titel", "url", "text" }]
  },
  "stationen": [{
    "titel", "firma", "zeitraum", "logo", "zusammenfassung", "beschreibung",
    "aufgaben": [],
    "projekte": [{ "kunde", "zeitraum", "logo", "beschreibung", "aufgaben": [] }]
  }],
  "bildung": [{ "abschluss", "institution", "zeitraum", "themen": [] }],
  "skillset": {
    "faehigkeiten": [], "branchen": [], "tools": [], "sprachen": []
  }
}
```

`sprache` ist `"de"` oder `"en"` und kommt aus der Frage in Schritt 0. Sie steuert
die Rubriken ("Bildung" / "Education", "Kurzprofil" / "Profile") und die
Footer-Beschriftungen. Der Inhalt der Stationen wird davon nicht angefasst.

`person.links` sind die Verweise aus Schritt 0, in der Reihenfolge LinkedIn,
Xing, Portfolio. Sie stehen auf Seite 1 im Profilkopf, **direkt unter der Zeile
mit den Jahren Berufserfahrung**, alle in einer Zeile nebeneinander,
unterstrichen in der Markenfarbe – dezent, aber erkennbar anklickbar. Das
Kurzprofil steht dagegen auf Seite 2, als eigene Rubrik mit Überschrift und
Trennlinie, damit es sich nicht wie die erste Station liest.

Angezeigt wird der Verweis **benannt, nicht als Adresse**: "zum LinkedIn Profil",
"zum Xing Profil", "zum Portfolio". Verlinkt bleibt die volle `url`. Den
Anzeigetext setzt `render_cv.py` aus `titel` (siehe `VERWEISTEXT` dort, deutsch
und englisch); ein `text` in der cv.json überschreibt ihn. Ohne `url` erscheint
der Text ohne Unterstrich – das ist der Fall fürs Portfolio-PDF, das sich nicht
verlinken lässt:

```json
"links": [
  { "titel": "LinkedIn",  "url": "https://www.linkedin.com/in/timo-muster" },
  { "titel": "Xing",      "url": "https://www.xing.com/profile/Timo_Muster" },
  { "titel": "Portfolio", "url": "https://timo-muster.de" }
]
```

Gibt es weder Profil noch Portfolio, entfällt `links` und unter der
Erfahrungszeile steht nichts mehr.

`logo` nimmt einen Dateinamen oder eine Liste davon – siehe Schritt 3.
`beschreibung` ist der Fließtext einer Station. Manche Lebensläufe beschreiben
eine Station als Absatz statt als Aufgabenliste; dann gehört der Absatz dorthin
und nicht als einzelner Bullet in `aufgaben`. Beides zusammen geht auch.

#### Die erste Station ist immer New Monday

**`stationen[0]` ist New Monday, in jedem Lebenslauf.** Die Person wird über New
Monday vermittelt; das Dokument geht an Kunden, und dort steht die aktuelle
Station oben. Wie das aussieht, zeigt `beispiel/cv.json` und das gerenderte
Beispiel-PDF.

Das ist – neben dem Kurzprofil – die **zweite Ausnahme von der Regel, dass nichts
erfunden wird**. Der Inhalt dieser Station stammt nicht aus dem Lebenslauf,
sondern von New Monday. Genau deshalb ist er festgelegt und wird nicht frei
formuliert: Titel und Startmonat kommen aus den Klickfragen in Schritt 1d, die
Stichpunkte aus den beiden Textbausteinen unten.

```json
{
  "titel": "User Experience Design Specialist",
  "firma": "New Monday GmbH",
  "zeitraum": "August 2026 - Heute",
  "logo": "nm-logo.svg",
  "zusammenfassung": "UX Design, UX Konzeption",
  "aufgaben": ["…", "…", "…"]
}
```

**Die Stichpunkte sind allgemein gehalten**, weil die Person gerade erst anfängt
und es noch keine Projekte zu berichten gibt. **Höchstens vier**, und sie hängen
davon ab, ob es ein UX- oder ein Entwicklerprofil ist – das entscheidet dieselbe
Antwort, die den Titel setzt.

**UX-Profil** (`"zusammenfassung": "UX Design, UX Konzeption"`):

| Deutsch | Englisch |
|---|---|
| Konzeption und Gestaltung digitaler Produkte in Kundenprojekten | Concept and design of digital products in client projects |
| User Research, Wireframing und Prototyping | User research, wireframing and prototyping |
| Usability-Tests und Prüfung auf Barrierefreiheit | Usability testing and accessibility reviews |
| Abstimmung mit Stakeholdern, UI Design und Entwicklung | Coordination with stakeholders, UI design and development |

**Entwicklerprofil** (`"zusammenfassung": "Softwareentwicklung, technische Konzeption"`):

| Deutsch | Englisch |
|---|---|
| Umsetzung digitaler Produkte in Kundenprojekten | Development of digital products in client projects |
| Technische Konzeption und Architektur nach Projektanforderung | Technical concept and architecture based on project requirements |
| Code-Reviews, Tests und technische Dokumentation | Code reviews, testing and technical documentation |
| Abstimmung mit Design, Produkt und Stakeholdern | Coordination with design, product and stakeholders |

Die Bausteine werden **wörtlich übernommen**, nicht auf die Person zugeschnitten,
nicht mit Technologien aus ihrem Lebenslauf angereichert und nicht umformuliert.
Sie beschreiben die Rolle bei New Monday, nicht den Menschen. Trägt der Nutzer
über "Other" einen eigenen Titel ein, wird der Satz genommen, der inhaltlich
näher liegt.

Dazu gehört:

- **Keine `projekte`.** Wer anfängt, hat noch keine Kundenprojekte. Sobald welche
  dazukommen, hängen sie unter diese Station – so wie im Beispiel.
- **Die bisherigen Arbeitgeber bleiben eigene Stationen.** Sie werden **nicht**
  zu Projekten unter New Monday umgebaut; das wären sie nur, wenn die Person sie
  tatsächlich über New Monday betreut hätte.
- **`erfahrung` ändert sich dadurch nicht.** Die Zahl kommt aus dem eigenen
  Werdegang der Person, ein Monat bei New Monday rundet nichts auf.
- **Steht New Monday schon im Lebenslauf**, wird nichts zweites angelegt: Dann
  ist diese Station schon da und behält ihre Inhalte.
- **"Heute" steht nur bei New Monday.** Genau eine Station im Dokument läuft
  offen aus, und das ist `stationen[0]`. Bringt der Eingang die letzte eigene
  Station noch als "bis heute", "seit 2024" oder "Present" mit, bekommt sie ein
  Enddatum: **den Monat vor dem Startmonat bei New Monday**. Beginnt New Monday
  im August 2026, endet die Station davor im Juli 2026. Zwei offene Zeiträume
  nebeneinander lesen sich, als arbeite die Person an zwei Stellen gleichzeitig –
  im Kundendokument ist das ein Fehler, kein Detail.

  Dieses Enddatum ist die einzige Angabe im Dokument, die aus dem Startmonat
  abgeleitet ist und nicht aus dem Eingang stammt. **Deshalb gehört es in die
  Übergabe**, Schritt 5: Wer früher aufgehört hat oder noch parallel weiterläuft,
  kann den Monat dort korrigieren. Ältere Stationen, die im Eingang parallel
  liefen – eine Nebentätigkeit, eine eigene Agentur –, behalten ihre Zeiträume;
  die Regel gilt nur für offene Enden.

Zum Modell:

- **Stationen sind Arbeitgeber, Projekte sind deren Kunden.** Bei Agentur-,
  Beratungs- und Zeitarbeitsstationen hängen die Kundenprojekte unter der
  Station. Bei Festanstellungen ohne Kundenbezug bleibt `projekte` leer und die
  Inhalte stehen in `aufgaben`.
- **`erfahrung`**: Steht die Angabe im Lebenslauf, wird sie übernommen. Fehlt
  sie, ab der **ersten Berufsstation** bis heute rechnen, abgerundet auf volle
  Jahre, im Format `"7+ Jahre Erfahrung"`. **Ausbildungs-, Studien- und
  Weiterbildungszeiten zählen nicht mit** – sonst kommen Werte heraus, die nicht
  zum Alter der Person passen. Ein Werkstudentenjob ist eine Berufsstation, eine
  Ausbildung oder ein Zertifikatskurs nicht.
- **`zusammenfassung`** ist eine Schlagwortzeile mit zwei bis drei Begriffen, die
  die Tätigkeit der Station benennen – etwa `"Frontend-Entwicklung, Code-Reviews,
  Mentoring"`. Die Begriffe müssen sich aus den darunterliegenden Aufgaben
  ergeben. Kein Fließtext. Im Dokument steht sie im Stationskopf unter Titel,
  Firma und Zeitraum. Die Figma-Vorlage kennt diese Zeile nicht; sie bleibt
  trotzdem, das ist so entschieden.
- **`firma`** enthält nur den Firmennamen. Angaben zur Beschäftigungsform gehören
  nicht ins Dokument: keine Befristungen, keine Kündigungsfristen, keine Gehälter,
  und auch keine Hinweise wie "(freiberuflich in Vollauslastung, 40h/Woche)".
- **Ausbildungen stehen nur unter `bildung`**, nie zusätzlich als Station, auch
  wenn der Eingang sie doppelt führt. Für Weiterbildungen, die nach Schritt 1d
  drinbleiben, gilt dasselbe.
- **Vom Schulweg steht nur die letzte Station.** Führt der Eingang mehrere
  Schulabschlüsse – Realschule, Gymnasium, Oberstufenzentrum, Fachoberschule,
  Kolleg, Fachschule –, kommt nur der **neueste** ins Dokument, die früheren
  fallen weg. Ein Kundendokument belegt keinen Schulweg, es zeigt den Abschluss,
  auf dem alles Weitere aufbaut. **Studienabschlüsse, Ausbildungen und die nach
  Schritt 1d behaltenen Weiterbildungen sind davon nicht betroffen** – die stehen
  alle drin, auch mehrere nebeneinander. Nennt der Eingang zu einer Station
  keinen Abschluss, sondern nur Jahr und Haus (etwa "2008 // Media Design
  Hochschule"), zählt sie zum Schulweg: sie belegt eine Station, keinen Titel.
  Was wegfällt, wird in der Übergabe genannt.
- **`skillset` hat in jedem Lebenslauf dieselben vier Gruppen**: `faehigkeiten`,
  `branchen`, `tools`, `sprachen` (Vorgabe vom 29.09.2026 – vorher trug jeder
  Lebenslauf andere Gruppen, und genau das kam als Rückmeldung zurück). In der
  `cv.json` stehen nur die Einträge. Titel und Anordnung setzt `render_cv.py`,
  immer 2 × 2: links Fähigkeiten und Branchen, rechts Tools und Sprachen; im
  englischen Lebenslauf "Skills", "Industries", "Tools", "Languages". Keine
  weiteren Gruppen, keine eigenen Titel.

  - **Einsortieren, was passt.** Der Eingang benennt seine Gruppen frei.
    Schwerpunkte, Kernkompetenzen, Methoden, Arbeitsweise, Soft Skills →
    `faehigkeiten`; Branchen, Branchenerfahrung, Industrien → `branchen`;
    Software, Tools, Werkzeuge → `tools`. Zertifikate sind Weiterbildungen und
    gehen den Weg aus Schritt 1d – drin bleiben heißt: unter `bildung`. Der
    Wortlaut der Einträge bleibt. Doppelte fallen weg, auch fast gleiche ("UI/UX"
    neben "UI/UX Design": das genauere bleibt).
  - **Was nirgends passt, fällt aus dem Skillset** – eine Kundenliste etwa (die
    Kunden stehen ohnehin in Stationen und Projekten) oder Produktarten wie
    "Plattformen" und "Web und App". Nicht in eine Gruppe biegen, sondern
    weglassen und in der Übergabe nennen, mit allen Einträgen.
  - **Gibt der Eingang für eine Gruppe nichts her, wird abgeleitet** – nur aus
    dem, was Stationen und Projekte belegen. Branchen aus den Sektoren der
    Arbeitgeber und Kunden, für die jemand nachweislich gearbeitet hat (Deutsche
    Bank, Postbank, Norisbank → "Banking"; eine Energie-App → "Energie";
    Kampagnen einer Werbeagentur → "Werbung und Kampagnen"); Tools aus den
    Aufgaben ("Prototypen in Figma" → "Figma"); Fähigkeiten aus den Aufgaben.
    Der Firmentyp allein belegt nichts: Wer bei einer Agentur war, hat damit noch
    keine Branche. **Abgeleitetes steht in der Übergabe zur Freigabe**, mit Beleg
    – es ist dieselbe Art Behauptung wie ein generiertes Kurzprofil.
  - **Sprachen setzt das Renderskript.** Deutsch – Muttersprache und Englisch –
    Business Niveau stehen in jedem Lebenslauf, auch wenn der Eingang keine
    Sprachen oder andere Niveaus nennt (Vorgabe vom 29.09.2026, gleich wie im
    Portfolio). In `sprachen` gehören die weiteren Sprachen mit ihrem Niveau
    ("Französisch – Grundkenntnisse"). Steht dort Deutsch oder Englisch mit
    anderem Niveau, ersetzt die Vorgabe es und `render_cv.py` meldet das.
  - **Keine Gruppe fehlt still.** Findet sich auch durch Ableiten nichts, fehlt
    die Gruppe im Dokument, und das Renderskript meldet es – das gehört in die
    Übergabe.

  **Bildung und Skillset stehen auf Seite 1**, direkt unter dem Profilkopf, und
  müssen dort zusammen Platz finden – die Stationen beginnen danach auf Seite 2.
  Kopfzeile und Profilkopf nehmen zusammen rund 200pt, es bleiben also
  etwa 550pt statt einer ganzen Seite; die Verweise unter der Erfahrungszeile
  kosten nichts, die Fotospalte ist ohnehin höher. Als Richtwert trägt **jede der
  beiden Skillset-Spalten etwa 17 Zeilen**, Gruppentitel mitgezählt, bei zwei
  Bildungseinträgen samt Themen daneben – mit den beiden engeren Stufen des
  Renderskripts bis etwa 23. Das Kurzprofil zählt hier nicht mit – es steht auf
  Seite 2 und nimmt Seite 1 keinen Platz weg.

  Bringt der Eingang mehr mit – Senior-Profile haben oft 40 Kompetenzen und mehr
  –, ist die Reihenfolge: erst das Renderskript enger setzen lassen (das macht
  es von selbst, in zwei Stufen), **und erst dann kürzen** – in der längsten
  Gruppe der längeren Spalte, durch Weglassen der schwächsten Einträge. Gruppen
  verschieben oder zusammenlegen geht nicht mehr, die vier stehen fest. **Der
  Wortlaut der übernommenen Einträge bleibt unverändert**, gekürzt wird durch
  Weglassen, nicht durch Umformulieren. Was wegfällt, wird am Ende gemeldet. Das
  Renderskript sagt, wenn der Block trotz aller Stufen überläuft, und nennt die
  Gruppe, in der gekürzt werden sollte.
- **`projekte[].zeitraum`** weglassen, wenn er mit dem der Station identisch ist.
- **Reihenfolge**: New Monday zuerst, danach die eigenen Stationen, neueste
  zuerst.
- `kontakt` weglassen – die Vorgaben stehen im Skript.

### 3. Logos zuordnen

**Das läuft in einem Durchgang, nicht Firma für Firma:**

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/logos_ergaenzen.py cv.json
python3 ${CLAUDE_SKILL_DIR}/scripts/logos_ergaenzen.py cv.json --domains domains.json
```

Das Skript geht jede Station und jedes Projekt ohne `logo` durch, sucht das
Logo und trägt den Dateinamen direkt in die `cv.json` ein. Je Firma zuerst die
Bibliothek in `assets/logos/`, dann die Quellenkette aus `fetch_logo.py`. Es
meldet am Ende, was aus der Bibliothek kam, was neu gefunden wurde und welche
Firmen offen sind.

**Dieser Schritt gehört zu jedem Lauf.** Ein Lebenslauf ohne Logos wirkt
unfertig, und die Logospalte steht ohnehin im Raster.

Domains nachreichen, wo sie fehlen: Wikimedia kommt mit dem Firmennamen aus,
Brandfetch, logo.dev und der Favicon-Dienst brauchen eine Domain. Die Domains
recherchierst du selbst und legst sie daneben ab:

```json
{ "Hays": "hays.de", "TEAM GmbH, Paderborn": "team-pb.de" }
```

#### Kommt die Kette leer zurück, suchst du selbst weiter — im Web

Die Quellenkette der Skripte (Bibliothek → simple-icons → Wikimedia →
Brandfetch → logo.dev → Favicon) ist eine Automatik, kein Urteil. Findet sie
nichts, heißt das: kein Treffer in ein paar Logodatenbanken. Es heißt **nicht**,
dass es das Logo nicht gibt. Genau die Firmen, die in diesen Lebensläufen stehen
– deutsche Agenturen, Mittelständler, Institute – stehen in keiner dieser
Datenbanken. Ihr Logo liegt auf ihrer eigenen Presseseite.

**Für jede offene Firma mindestens eine Websuche, bevor du den Nutzer fragst.**
Das ist keine Kür und keine Frage der Zeit. Es ist der Unterschied zwischen
"nicht auffindbar" und "ich habe nicht nachgesehen" – und der Nutzer findet die
Logos anschließend in zwei Minuten mit derselben Suche, die du gehabt hättest.

Wonach gesucht wird, in dieser Reihenfolge:

1. `<Firma> Logo SVG`, `<Firma> Logo download`
2. `<Firma> Presse`, `<Firma> Pressebereich`, `<Firma> Media Kit`, `<Firma> Markenrichtlinien`
3. Die Firmenseite selbst öffnen: Presse, Über uns, Impressum. Das Logo im
   Seitenkopf ist oft ein SVG, das sich direkt laden lässt.

Zwei Funde sind brauchbar, beide reichen aus:

- **Die Domain.** Häufig ist das schon der ganze Fix: Wikimedia kommt mit dem
  Namen aus, Brandfetch, logo.dev und der Favicon-Dienst brauchen eine Domain,
  und die kannten die Skripte nicht. Domain in die `domains.json` eintragen und
  `logos_ergaenzen.py --domains` noch einmal laufen lassen.
- **Die Bild-URL.** `add_logo.py` nimmt neben Dateipfaden auch URLs:

  ```bash
  python3 ${CLAUDE_SKILL_DIR}/scripts/add_logo.py "https://firma.de/presse/logo.svg" firma
  ```

Erst wenn auch die Suche nichts hergibt, ist die Firma offen und kommt in die
Schlusszeile aus Schritt 5. Findest du die Datei, kannst sie aber nicht laden
(im Browser-Chat blockt der Proxy fremde Domains), dann gehört **der Link** in
die Übergabe, nicht bloß der Firmenname.

Was dabei durch den Kopf geht und trotzdem nicht stimmt:

| Gedanke | Was wirklich stimmt |
|---|---|
| "Die Quellenkette kam leer zurück, dann gibt es kein Logo." | Sie hat fünf Datenbanken abgefragt, nicht das Web. Deutsche Agenturen stehen in keiner davon. |
| "Der Skill sieht doch vor, den Nutzer zu fragen." | Ja – als **letzten** Schritt, nicht als zweiten. Nachfragen ohne eigene Suche ist Arbeit weiterreichen. |
| "Bei acht offenen Firmen dauert das zu lange." | Acht Suchen sind ein paar Minuten. Der Nutzer braucht für dieselben acht länger, weil er sie erst zusammensuchen und dann hochladen muss. |
| "Ich habe keine Domain, also kann ich nichts machen." | Die Domain ist das, wonach du suchst. Sie steht im ersten Treffer. |
| "Das Skript hat schon gesucht, doppelte Arbeit." | Das Skript kennt keine Suchmaschine. Es kennt Datenbanken. |

Rote Flagge: Du schreibst gerade "Folgende Firmenlogos fehlen" und hast in
diesem Lauf keine einzige Websuche gemacht. Dann ist die Zeile nicht fertig
recherchiert – zurück nach oben.

Danach zu prüfen:

- **Neu gefundene Logos ansehen.** Die Suche trifft manchmal eine gleichnamige
  Firma oder ein abgelegtes Altlogo. "People Interactive" etwa gibt es als Kölner
  Agentur und als indischen Konzern.
- **Stationen mit mehreren Marken** meldet das Skript gesondert – bei
  "Deutsche Bank, Postbank, FYRST & Norisbank" sucht es nur nach der ersten. Ein
  Logo pro Station bildet so einen Fall nicht ab; mit dem Nutzer klären, ob die
  Marken zu Projekten unter der Station werden sollen. Bleiben sie in einer
  Station, gehören alle gefundenen Dateinamen als Liste in `logo` – in der
  Reihenfolge, in der die Marken in der Firmenzeile stehen.
- **Anonymisierte Kunden** ("Speditionsdienstleister", "Maschinenbauunternehmen")
  haben naturgemäß kein Logo und bleiben offen. Das ist richtig so.

**Logos gehören in die Originalfarben der Marke, wo es sie gibt.** Nichts wird
entfärbt, aufgehellt oder ans Layout angeglichen – das Skript fasst Logofarben
ohnehin nicht an, also entscheidet allein, welche Datei in `assets/logos/` liegt.
Die automatische Suche liefert oft die schwarze Variante, auch wenn die Marke
farbig ist: Deutsche Bank ist blau, nicht schwarz. Deshalb jedes neu gefundene
Logo daraufhin ansehen und, wenn es die entfärbte Fassung ist, die farbige von
der Marken- oder Presseseite nachlegen und die Datei in der Bibliothek ersetzen.

Einfarbig bleibt ein Logo nur, wenn die Marke selbst einfarbig auftritt – Opel,
Peugeot und Citroën führen ihre aktuellen Wortbildmarken schwarz, das ist dann
richtig so und wird nicht "bunt gemacht". Genauso wenig wird eine Farbfassung
gegen eine schwarze getauscht, damit die Spalte einheitlicher wirkt: Ein
Lebenslauf mit gelbem Postbank-Logo neben schwarzem Peugeot-Logo ist korrekt,
weil beide Marken so auftreten.

Die Figma-Vorlage zeigt die Firmenlogos entfärbt. Das ist dort Darstellung, keine
Vorgabe: Im Skill bleiben die Originalfarben, so ist es entschieden. Wer das
Dokument mit Figma vergleicht, gleicht die Logos nicht an.

Einzelne Logos von Hand nachlegen, wenn das Skript sie nicht findet:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/add_logo.py ~/Downloads/hays.svg hays        # Datei liegt vor
python3 ${CLAUDE_SKILL_DIR}/scripts/fetch_logo.py "Hays" hays --domain hays.de   # gezielt suchen
```

Bekannt gewordene Sonderfälle gehören in `assets/logos/aliase.json`, damit die
Zuordnung beim nächsten Mal ohne Suche klappt:

```json
{ "New Monday": "nm-logo.svg" }
```

**Alle Netzwege brauchen offenes Netz** – lokal und in Claude Desktop gegeben.
Im Browser-Chat blockt der Proxy fremde Domains (`host_not_allowed`), und
Bilddateien lassen sich dort auch nicht über den Web-Abruf holen. Dort greift nur
die Bibliothek; für den Rest den Nutzer um die Dateien bitten.

Was auch danach offen bleibt: `logo` weglassen. Die Logospalte bleibt leer und
das Raster steht – der Text rückt **nicht** auf die volle Breite. So sehen alle
Lebensläufe gleich aus. Welche fehlen, kommt in die Schlusszeile der Übergabe,
siehe Schritt 5.

**Logos stehen rechtsbündig und wirken gleich schwer.** Beides macht
`render_cv.py` selbst, sobald die Dateinamen in der `cv.json` stehen – hier ist
nichts zu setzen und im CSS nichts nachzujustieren:

- **Rechtsbündig in der Logospalte**, also an der Kante zum Text. Die Logos sind
  verschieden breit; linksbündig springt der Abstand zum Stationstext von
  Station zu Station.
- **Gleiche Fläche statt gleicher Höhe.** Skaliert wird über die Fläche, nicht
  über die Höhe – sonst wirkt eine kompakte Bildmarke doppelt so schwer wie ein
  breiter Schriftzug (3pc gegen Cocomore). Das Skript liest das Seitenverhältnis
  aus der Logodatei und rechnet Breite und Höhe daraus aus.

**Dieselbe Marke ist überall gleich groß.** Führt eine Station mehrere Marken in
einer Zeile ("Deutsche Bank, Postbank, FYRST & Norisbank"), stehen deren Logos
in der Logospalte **untereinander** – nebeneinander wären sie in 88pt winzig.
Ein Logo, das an einer Stelle in so einer Markenreihe steht und an einer anderen
allein, erscheint an beiden Stellen im selben Maß: die Logogröße wird einmal
fürs ganze Dokument bestimmt, nach der größten Markenzahl, die irgendwo vorkommt.

**Projektlogos stehen nebeneinander.** Hat ein Projekt mehrere Kunden ("Opel,
Peugeot, Citroën"), stehen deren Logos in einer Reihe über dem Kundennamen,
auf der Mitte zueinander, 16pt auseinander – nicht gestapelt (Design-Feedback
vom 28.09.2026). Weil eine Reihe nicht höher wird, wenn eine Marke dazukommt,
sind Projektlogos **immer 26pt**, allein wie in der Reihe. Das macht
`render_cv.py` selbst; in der `cv.json` steht wie bisher nur die Liste der
Dateinamen.

Zwischen den beiden Ebenen bleibt ein Unterschied: Projektlogos sind bewusst
die kleinere Stufe. Steht dieselbe Datei einmal als Stationslogo und einmal als
Projektlogo, sagt das Renderskript das in seinen Prüfhinweisen.

**Zu kleine Logos bessert `add_logo.py` selbst auf.** Unter 242px Höhe (58pt bei
300 dpi) prüft es, ob das Bild zweifarbig ist – typisch für Wort- und
Strichmarken. Wenn ja, wird es über potrace vektorisiert und ist danach in jeder
Größe scharf. Wenn nein, wird nur hochgerechnet; das glättet, erzeugt aber keine
Details, und das Skript sagt das auch. Toten Rand schneidet es weg – ein
Badge-Logo mit breitem Rand schrumpft im Layout sonst so weit, dass die
Wortmarke unleserlich wird.

**Die Ausgabe der Skripte ist zu lesen, nicht zu überfliegen.** Sie melden die
erkannten Farben, den entfernten Rand und wie viel vom Kasten in Einsatzgröße
tatsächlich gedeckt ist. Bleibt darunter eine Warnung stehen, ist das Logo kaputt
und gehört nicht ins Dokument.

Zusätzlich das fertige PDF an der Logostelle in 300 dpi ansehen. Ein Logo kann
technisch fehlerfrei eingebettet und trotzdem unlesbar sein – im Test war ein
Schriftzug in einem zweiten Rotton statt in Weiß gelandet und in der Übersicht
nicht aufgefallen. Ein Blick auf die Miniatur reicht dafür nicht.

### 4. Rendern — beide Fassungen

Erst die anonyme Datenfassung schreiben, dann beide rendern:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/anonymisieren.py cv.json cv-anonym.json
python3 ${CLAUDE_SKILL_DIR}/scripts/render_cv.py cv.json        ausgabe/ --stufen-json arbeit/stufen.json
python3 ${CLAUDE_SKILL_DIR}/scripts/render_cv.py cv-anonym.json ausgabe/ --stufen-json arbeit/stufen-anonym.json
```

`anonymisieren.py` meldet, was es geändert hat. **Was es an Fließtextstellen
ersetzt hat, gehört in die Übergabe** – das ist die einzige Stelle, an der der
Skill fremden Text anfasst, ohne dass jemand es angeordnet hat. Welche Schalter es
darüber hinaus gibt, steht unter "Die anonymisierte Fassung".

`--stufen-json` schreibt mit, welche Verdichtungsstufen gegriffen haben. Das
braucht Schritt 4a: ohne die Datei setzen die Frames andere Abstände als die PDFs
und laufen über. **Je Fassung eine eigene Datei** – der anonymen fehlt die
Verweiszeile im Profilkopf, sie kann deshalb in einer anderen Stufe landen als die
vollständige.

**Den Dateinamen setzt das Skript**, nicht der Aufruf: es baut ihn aus
`person.name` und `person.rolle` zusammen und legt die Datei im angegebenen
Ordner ab.

```
New-Monday - Vorname Nachname - Jobtitel - CV.pdf
New-Monday - V. N. - Jobtitel - CV.pdf
```

**Die beiden Fassungen unterscheiden sich damit von selbst** und dürfen in
denselben Ordner. Ein zusätzliches "anonym" im Dateinamen braucht es nicht – und
es wäre auch keine gute Idee: Die anonyme Fassung ist die, die beim Kunden
ankommt, und sie soll nicht wie ein Zwischenstand aussehen.

Steht im Aufruf trotzdem ein Dateiname, gilt davon nur der Ordner – das Skript
meldet die Umbenennung. Der Name im Bericht an den Nutzer ist der, den das
Skript ausgibt, nicht der aus dem Aufruf. Die Datei heißt so, wie sie beim
Kunden ankommt, deshalb wird hier nicht abgekürzt und nicht umbenannt.

Das Skript sucht sich die Engine selbst: WeasyPrint, sonst headless Chrome, sonst
wkhtmltopdf. Fehlt alles, hilft `pip install weasyprint --break-system-packages`.
Zusätzlich prüft es die Zeiträume und meldet nach stderr: Ende vor Anfang,
Projekte außerhalb der Anstellung, fehlende Logodateien.

Es setzt Bildung und Skillset selbst enger, wenn sie sonst nicht neben den
Profilkopf auf Seite 1 passen, und sagt in welcher Stufe. Bleibt die Meldung
stehen, dass der Block über mehrere Seiten läuft, ist zu kürzen – nach der
Reihenfolge aus Schritt 2, nicht vorher.

Die Umbrüche in den Stationen macht das Layout selbst: **Eine Station beginnt
nur dann unten auf einer Seite, wenn dort noch mindestens zwei ihrer Stichpunkte
stehen.** Reicht der Platz nicht, rückt sie samt Logo komplett auf die nächste
Seite – ein Jobtitel mit einem einzelnen Bullet an der Blattkante liest sich wie
zwei angefangene Stationen. In der `cv.json` ist dafür nichts einzutragen und im
CSS nichts nachzujustieren; Hintergrund in `references/layout.md`.

### 4a. Die Figma-Frames ablegen

**Beide Fassungen kommen nach Figma**, nicht nur die vollständige, und nicht nur
auf Nachfrage. **Die PDFs sind an dieser Stelle fertig** und gehen so oder so raus.

Erst die Baupläne, dann bauen – je Fassung einer:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py cv.json "<pfad/zum.pdf>" arbeit/ \
        --stufen arbeit/stufen.json
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py cv-anonym.json "<pfad/zum-anonymen.pdf>" arbeit/anonym/ \
        --stufen arbeit/stufen-anonym.json
```

Jeder schreibt ein `figma_plan.json`: je PDF-Seite ein Frame, darin die Blöcke in
Lesereihenfolge, alle Werte fertig ausgerechnet. **Die Seitenaufteilung wird aus dem
gerenderten PDF gelesen, nicht geschätzt** — deshalb steht dieser Schritt nach dem
Rendern und nicht davor, und deshalb braucht jede Fassung ihren eigenen Plan aus
ihrem eigenen PDF. Ohne `pypdf` bricht das Skript ab; dann entfallen die Frames mit
einem Satz in der Übergabe.

Gebaut wird mit `use_figma` nach dem Rezept in `references/figma.md`. Dort stehen
Linkauslesung, Zielseite, Schnittnamen, das Frame-Rezept, der Weg für Logos und Foto
und wie die beiden Reihen zueinander stehen. **Vor dem ersten Aufruf den Skill
`figma-use` laden** — ohne ihn sind die Fallstricke des Plugin-API nicht zu umgehen.

Liegt kein Link vor, wird mit `create_new_file` eine Datei
`New Monday CV — Vorname Nachname` angelegt und beides dort hineingebaut. Der Link
darauf geht in die Übergabe.

Fünf Dinge stehen fest:

- **Erst die vollständige Fassung, dann die anonyme.** Bricht der zweite Lauf ab,
  steht wenigstens die vollständige in der Datei. Andersherum läge dort ein
  Lebenslauf ohne Namen, und niemand wüsste mehr, von wem.
- **Figma hält die PDFs nicht auf.** Schlägt irgendetwas fehl — Werkzeug nicht
  verbunden, nicht angemeldet, keine Bearbeitungsrechte, falscher Dateityp, Proxy
  blockt —, werden die PDFs trotzdem übergeben und der Grund genannt. Nicht
  abbrechen, nicht nachträglich am PDF drehen, und keinen zweiten Anlauf mit
  anderen Daten.
- **In eine fremde Datei kommt nichts Globales.** Keine Text-Styles, keine
  Variablen, keine Komponenten. Die Frames tragen rohe Werte. Was schon in der
  Datei liegt, wird nicht umbenannt, nicht verschoben und nicht gelöscht.
- **Nichts überschreiben.** Steht dort schon ein Frame gleichen Namens, kommt der
  neue daneben, nicht darüber.
- **Kein Ersatz-Layout.** Reicht es nicht für den Frame, wird kein vereinfachter
  gebaut. Entweder das Dokument oder nichts.


### 5. Übergeben

Beide PDFs ausgeben – die vollständige Fassung zuerst – und dazu in wenigen
Zeilen berichten:

- Das Kurzprofil im Wortlaut, falls es generiert wurde, mit der Bitte um Freigabe
- **Das Skillset**: was abgeleitet wurde (Branchen, Tools, Fähigkeiten, die der
  Eingang nicht nannte) mit Beleg aus Stationen oder Projekten und der Bitte um
  Freigabe; was aus dem Skillset gefallen ist, weil es in keine der vier Gruppen
  passt, mit allen Einträgen; und was `render_cv.py` zu Sprachen gemeldet hat
  (ergänzt oder Niveau ersetzt).
- Wo Lebenslauf und LinkedIn auseinandergehen – mit beiden Werten, damit
  Tippfehler auffallen. Ins Dokument kam der Lebenslauf.
- Was das Skript an Zeiträumen bemängelt hat
- Woher das Foto stammt, wenn es automatisch von LinkedIn oder von der Website
  kam – bei der Website mit der Bildadresse, damit nachvollziehbar bleibt, wen
  das Skript da gefunden hat – und die gemeldete dpi-Zahl, falls sie unter 200
  lag. Der Nutzer soll entscheiden können, ob ihm das für sein Kundendokument
  reicht. Kam das Foto aus dem Lebenslauf, ist das der Normalfall und muss nicht
  erwähnt werden. Wurde es dort **übergangen**, weil es technisch unbrauchbar
  war (Schritt 1a), steht das dagegen in der Übergabe – mit dem Grund.
- Was nach Schritt 1d draußen bleibt: die gestrichenen Stationen und
  Weiterbildungen namentlich, und ob dadurch eine Lücke entstanden ist.
- Welches Enddatum die letzte eigene Station bekommen hat, wenn sie im Eingang
  noch offen lief – mit der Bitte, den Ausstiegsmonat zu bestätigen. Abgeleitet
  ist er aus dem Startmonat bei New Monday, nicht aus dem Eingang.
- Welche Schulabschlüsse aus dem Bildungsblock weggefallen sind.
- Welche Rechtschreibfehler korrigiert wurden
- Was im Eingang unklar war und geraten werden müsste – als Frage, nicht als
  stille Annahme
- **Die anonyme Fassung**: in welcher Form der Name jetzt dasteht, und –
  falls `anonymisieren.py` welche gemeldet hat – an welchen Stellen im Fließtext
  ein Name ersetzt wurde, mit Feld und altem Wortlaut. **Was das Skript unter
  "Prüfen" als mehrdeutig stehen gelassen hat, gehört immer hierher**, mit dem
  Satz drumherum: Dort steht möglicherweise noch der Name im Dokument, und die
  Entscheidung darüber trifft nicht der Skill. Wurde eine der Stufen aus
  "Wenn mehr weg soll" gezogen, steht hier auch, welche. Ist keine gezogen worden,
  steht hier nichts dazu: Der Normalfall braucht keine Erklärung.
- **Die Figma-Frames**: der Link auf den ersten Frame jeder Fassung
  (`…?node-id=…`) und auf welcher Seite der Datei sie liegen. Wurde ein neues File
  angelegt, der Link darauf. Ist eine der beiden Reihen nicht zustande gekommen,
  steht hier stattdessen der Grund in einem Satz. Hat `figma_plan.py` gemeldet,
  dass eine Textmarke im PDF nicht wiederzufinden war, gehört auch das hierher: An
  dieser Stelle ist die Seitenkante im Frame geraten und sollte nachgesehen
  werden.

#### Ganz zum Schluss: was zur Vollständigkeit fehlt

Nach allem anderen, als letzte Zeilen der Übergabe, steht der Hinweis auf das,
was zur Vollständigkeit fehlt. Höchstens zwei Sätze, **wörtlich** so gesetzt:

> Folgende Firmenlogos fehlen: Hays, TEAM GmbH – einfügen, um Lebenslauf zu vervollständigen

> Profilfoto einfügen, um Lebenslauf zu vervollständigen

Regeln dazu:

- **Fehlt nichts, steht hier nichts.** Kein "alles vollständig", keine
  Erfolgsmeldung. Der Hinweis erscheint nur, wenn wirklich etwas fehlt.
- **Erst nach der eigenen Suche.** Eine Firma gehört nur dann in die Zeile,
  wenn Bibliothek, Skript **und** Websuche nichts ergeben haben (Schritt 3).
- **Fehlt beides**, kommen beide Zeilen untereinander, Logos zuerst.
- **Fehlt genau ein Logo**, trotzdem derselbe Satz mit dieser einen Firma.
- **Keine Erklärung dazu.** Nicht begründen, warum ein Logo fehlt, nicht
  vorschlagen, wo man es findet, kein "leider". Nur der Satz. Was dazu zu sagen
  war, steht schon oben.
- **Anonymisierte Kunden zählen nicht** ("Speditionsdienstleister",
  "Maschinenbauunternehmen"). Die haben kein Logo, das fehlen könnte, und
  gehören nicht in die Aufzählung.
- Genannt werden **Firmennamen**, nicht Dateinamen: "TEAM GmbH", nicht
  "team-gmbh.svg".

## Was fest steht und nicht zur Disposition steht

- **Seitenaufbau**: Seite 1 trägt die Kopfzeile (nur das Logo), den Profilkopf
  (Foto, Name, Rolle, Erfahrung, darunter die Verweise), Bildung und
  Skillset. Ab Seite 2 folgen Kurzprofil und Stationen, am Ende der Footer, der
  immer am unteren Rand der letzten Seite sitzt. Bildung und Skillset stehen
  vorn, nicht hinten – daran wird nicht getauscht.
- **Erste Station ist New Monday**, immer – und **nur sie läuft auf "Heute"**.
  Siehe Schritt 2.
- **Das Skillset hat immer dieselben vier Gruppen**, 2 × 2: links Fähigkeiten und
  Branchen, rechts Tools und Sprachen. Deutsch – Muttersprache und Englisch –
  Business Niveau stehen immer drin. Siehe Schritt 2.
- **Ansprechpartner im Footer**: immer Manuel Klein, CCO. Steht als Vorgabe im
  Renderskript.
- **Zwei Fassungen, immer.** Die vollständige und die anonymisierte, jeweils als
  PDF und als Figma-Frame. Die anonyme ersetzt die vollständige nie und wird nie
  allein übergeben: Wer sie bekommt, bekommt beide.
- **In der vollständigen Fassung gehören Name und Foto ins Dokument.**
  Anonymisiert wird ausschließlich in der zweiten, und dort nach den Regeln unter
  "Die anonymisierte Fassung" – nicht nach Gefühl und nicht auf halbem Weg.
- **Schriften sind Inter** (Regular, Bold) **und Rethink Sans SemiBold** für den
  Namen. Beide liegen in `assets/fonts/` und werden ins PDF eingebettet. Nicht
  durch Systemschriften ersetzen.
- **Keine Schatten, keine Rundungen.** Die Figma-Vorlage hat keine, das Dokument
  auch nicht.
- **Kein Umbau des Layouts.** Neue Rubriken, andere Farben, zusätzliche Spalten:
  nur nach ausdrücklicher Ansage.
- **Die PDFs sind der Ausgang**, die Figma-Frames die bearbeitbare Zweitschrift.
  Sie entstehen in jedem Lauf, aber nie statt der PDFs, und ihr Ausfall hält die
  PDFs nicht auf.

## Wenn das Layout doch angefasst werden muss

**Designwerte stehen nur in `assets/tokens.json`** – Schriften, Größen,
Zeilenhöhen, Laufweiten, Abstände, Farben, abgelesen aus der Figma-Datei, die dort
unter `quelle` steht. `assets/cv.css` und `scripts/figma_plan.py` tragen keine
eigenen Zahlen, sie lesen von dort; deshalb setzen PDF und Figma-Frame immer
dieselben Werte. Einen Wert ändern heißt: ihn in `tokens.json` ändern, sonst
nirgends. Das Platzhalterbild der anonymen Fassung ist eine Datei aus dem Design:
eine neue Fassung als `assets/silhouette-vorlage.svg` ablegen und
`python3 ${CLAUDE_SKILL_DIR}/scripts/silhouette.py` laufen lassen – das setzt sie
in den Fotoplatz aus `tokens.json` ein und schreibt `silhouette.svg` und `.png`.
Dasselbe nach einer Änderung von `raster.foto_breite` oder `foto_hoehe`.

Danach immer:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/selbsttest.py
```

Er misst am gerenderten PDF nach, ob Schrift, Größe und Farbe jeder Zeile und die
Abstände von Schriftlinie zu Schriftlinie den Tokens entsprechen, und schlägt an,
sobald in `cv.css` ein Wert als Literal steht oder Schatten und Rundungen
auftauchen.

**Hat sich das Design-System in Figma geändert**, gilt
`references/figma-abgleich.md`: Figma-Seite auslesen, mit `tokens.json`
vergleichen, die bewussten Abweichungen stehen lassen. Warum einige Tokens nicht
dem Figma-Eintrag entsprechen (gerundete Zeilenhöhen, 13pt-Takt der Listen) und
warum die Stationen mit Float statt Flexbox gebaut sind, steht in
`references/layout.md` – vor jeder Änderung lesen, sonst brechen Abstände oder
Seitenumbrüche. Wie aus dem Plan Frames werden: `references/figma.md`.
