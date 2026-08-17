---
name: newmonday-cv
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*) Bash(pdftoppm *) Bash(pdfinfo *) WebSearch WebFetch AskUserQuestion Read Write Edit
description: Wandelt einen eingehenden Lebenslauf in einen Lebenslauf im New-Monday-Layout als PDF um. Eingang ist ein CV als PDF, ein LinkedIn-PDF-Export, ein LinkedIn-Profil-Link (daraus wird das Profilfoto automatisch geholt) oder eingefügter Profiltext, Ausgang ein fertiges PDF im Agenturlayout. Nutze diesen Skill immer, wenn ein Lebenslauf, CV, Kandidatenprofil oder Bewerberprofil aufbereitet, umformatiert, "ins New Monday Layout gebracht", vereinheitlicht oder für Kunden aufbereitet werden soll – auch wenn nur eine PDF-Datei mit einem Lebenslauf ohne weitere Erklärung geschickt wird, und auch dann, wenn das Wort "Layout" oder "New Monday" gar nicht fällt.
---

# New Monday CV

Aus einem fremden Lebenslauf wird ein Lebenslauf im New-Monday-Layout. Bester
Eingang sind zwei Quellen: der Lebenslauf als PDF **und** der LinkedIn-PDF-Export. Das Layout
liegt als HTML/CSS-Template im Skill und stammt 1:1 aus der Figma-Datei
`KoR4rzVSoMrvQot8z33gkv` (Seite "CV"). Das Template wird nicht neu erfunden und
nicht "verbessert" – es wird befüllt.

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
  Skillset-Spalten gegenprüfen, bevor das PDF rausgeht.
- **Netz**: Lokal und in Claude Desktop ist es offen, im Browser-Chat blockt der
  Proxy fremde Domains. Das betrifft nur die Logosuche, siehe Schritt 3.
- **Ausgabeort**: In Claude Code ins Arbeitsverzeichnis des Nutzers schreiben,
  nicht in den Skill-Ordner. Im Browser-Chat nach `/mnt/user-data/outputs/`.
  Die einzige Ausnahme sind neue Logos: die gehören dauerhaft in
  `assets/logos/`, damit die Bibliothek wächst.

Für die Installation gibt es `INSTALL.md` – die ist für den Nutzer geschrieben,
nicht für dich, und kann bei Einrichtungsfragen weitergereicht werden.

## Gefragt wird mit Klickboxen, nicht im Fließtext

**Jede Frage, deren Antwort aus einer überschaubaren Menge stammt, läuft über
`AskUserQuestion`** – die klickbaren Kästchen in Claude Code. Das gilt für jede
Rückfrage in diesem Skill: Sprache, Rolle bei New Monday, Startmonat, fachfremde
Stationen, Weiterbildungen. Auch dann, wenn die Frage kurz ist und im Fließtext
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

2. **Firmenlogos als SVG.** Die Logodatenbanken der Skripte führen globale
   Marken zuverlässig, deutsche Agenturen und Mittelständler dagegen fast nie.
   Genau die stehen aber in den meisten Lebensläufen. Deshalb gleich zu Beginn
   darum bitten, die Logos der Arbeitgeber als SVG mitzuschicken – am besten aus
   dem Presse- oder Brand-Bereich der jeweiligen Firmenseite. Was schon in
   `assets/logos/` liegt, muss nicht noch einmal geliefert werden.

   Die Bitte ist eine Abkürzung, keine Bedingung: Was nicht kommt, suchst du
   selbst, siehe Schritt 3.

3. **Die Profile.** Material, also im Text derselben Nachricht, wörtlich so:

   > Gibt es ein LinkedIn-Profil? Wenn du mir den Link schickst
   > (linkedin.com/in/…), ziehe ich das Profilfoto automatisch. Ein
   > Xing-Profil nehme ich auch – es kommt als Verweis mit ins Dokument.

   Ist das LinkedIn-Profil öffentlich, holt `linkedin_foto.py` das Foto von dort
   – siehe Schritt 1a. Das erspart das Heraussuchen und Zuschneiden von Hand.
   Der Link ist **zusätzlich** zum PDF-Export nützlich, nicht statt seiner: für
   die Inhalte taugt er nichts (siehe Schritt 1), fürs Foto schon. Beide Profile
   landen außerdem als Verweis in den Profilkopf des Dokuments, siehe `links` in
   Schritt 2. Aus Xing wird kein Foto geholt, der Link steht nur im Dokument.

4. **Das Portfolio.** Ebenfalls als Text, wörtlich so:

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

5. **Ein Foto**, falls weder LinkedIn noch die Website eins hergeben (beides
   siehe Schritt 1a). Bringt der Lebenslauf keins mit und führt auch kein Link
   dorthin, danach fragen: als Bilddatei schicken lassen, `extract_input.py`
   wandelt sie in Graustufen und schneidet sie aufs Layoutformat zu. Ohne Foto
   funktioniert das Layout, wirkt aber leer – die Fotospalte bleibt frei.

Ebenfalls hier erwähnen, falls noch nicht vorhanden: den LinkedIn-PDF-Export
(siehe Schritt 1). Er gehört in dieselbe Nachricht.

Das ist **eine** Nachricht: die Sprachfrage als Klickbox, die Punkte 2 bis 5 als
Text daneben. Rolle und Startmonat bei New Monday werden hier noch nicht
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
    "links":  [{ "titel", "eintraege": [] }],
    "rechts": [{ "titel", "eintraege": [] }]
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
- **Läuft die letzte eigene Station noch "bis heute"**, überschneidet sie sich mit
  New Monday. Nicht stillschweigend ein Enddatum setzen – in die Übergabe damit,
  Schritt 5.

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
  ergeben. Kein Fließtext.
- **`firma`** enthält nur den Firmennamen. Angaben zur Beschäftigungsform gehören
  nicht ins Dokument: keine Befristungen, keine Kündigungsfristen, keine Gehälter,
  und auch keine Hinweise wie "(freiberuflich in Vollauslastung, 40h/Woche)".
- **Ausbildungen stehen nur unter `bildung`**, nie zusätzlich als Station, auch
  wenn der Eingang sie doppelt führt. Für Weiterbildungen, die nach Schritt 1d
  drinbleiben, gilt dasselbe.
- **`skillset.links`** trägt üblicherweise Fähigkeiten, Zertifizierungen und
  Branchenerfahrung, **`rechts`** Tools und Sprachen. Die Aufteilung ist frei,
  aber **die beiden Spalten sollen etwa gleich lang sein**. Der Block ist so hoch
  wie seine längere Spalte; eine halb leere zweite Spalte verschenkt Platz, den
  sonst jemand durch Streichen hereinholen muss. Zählt man Gruppentitel und
  Einträge zusammen, sollten beide Spalten auf ungefähr dieselbe Zeilenzahl
  kommen. Das Renderskript meldet es, wenn sie deutlich auseinanderliegen.

  **Bildung und Skillset stehen auf Seite 1**, direkt unter dem Profilkopf, und
  müssen dort zusammen Platz finden – die Stationen beginnen danach auf Seite 2.
  Kopfzeile und Profilkopf nehmen zusammen rund 200pt, es bleiben also
  etwa 550pt statt einer ganzen Seite (mit Verweisen unter der Erfahrungszeile
  gut 20pt weniger). Als Richtwert trägt **jede der beiden
  Skillset-Spalten etwa 20 Zeilen**, Gruppentitel mitgezählt, bei zwei
  Bildungseinträgen daneben. Das Kurzprofil zählt hier nicht mit – es steht auf
  Seite 2 und nimmt Seite 1 keinen Platz weg.

  Bringt der Eingang mehr mit – Senior-Profile haben oft 40 Kompetenzen und mehr
  –, ist die Reihenfolge: erst die Spalten ausgleichen, dann das Renderskript
  enger setzen lassen (das macht es von selbst, in zwei Stufen), **und erst dann
  kürzen**. Gekürzt wird durch Zusammenlegen verwandter Gruppen und Weglassen der
  schwächsten Einträge. **Der Wortlaut der übernommenen Einträge bleibt
  unverändert**, gekürzt wird durch Weglassen, nicht durch Umformulieren. Was
  wegfällt, wird am Ende gemeldet. Das Renderskript sagt, wenn der Block trotz
  aller Stufen überläuft.
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
**immer untereinander**, nie nebeneinander. Und ein Logo, das an einer Stelle in
so einer Markenreihe steht und an einer anderen allein, erscheint an beiden
Stellen im selben Maß: die Logogröße wird einmal fürs ganze Dokument bestimmt,
nach der größten Markenzahl, die irgendwo vorkommt.

Nur zwischen den beiden Ebenen bleibt ein Unterschied: Projektlogos sind
bewusst die kleinere Stufe. Steht dieselbe Datei einmal als Stationslogo und
einmal als Projektlogo, sagt das Renderskript das in seinen Prüfhinweisen.

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

### 4. Rendern

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_cv.py cv.json ausgabe/nachname-vorname.pdf
```

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

### 5. Übergeben

PDF ausgeben und dazu in wenigen Zeilen berichten:

- Das Kurzprofil im Wortlaut, falls es generiert wurde, mit der Bitte um Freigabe
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
- Ob die letzte eigene Station noch "bis heute" läuft und sich damit mit der
  New-Monday-Station überschneidet – mit der Frage, ob ein Enddatum hin soll.
- Welche Rechtschreibfehler korrigiert wurden
- Was im Eingang unklar war und geraten werden müsste – als Frage, nicht als
  stille Annahme

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
- **Erste Station ist New Monday**, immer. Siehe Schritt 2.
- **Ansprechpartner im Footer**: immer Manuel Klein, COO. Steht als Vorgabe im
  Renderskript.
- **Keine anonymisierte Variante.** Name und Foto gehören ins Dokument.
- **Schrift ist Inter**, liegt in `assets/fonts/` und wird ins PDF eingebettet.
  Nicht durch Systemschriften ersetzen.
- **Kein Umbau des Layouts.** Neue Rubriken, andere Farben, zusätzliche Spalten:
  nur nach ausdrücklicher Ansage.

## Wenn das Layout doch angefasst werden muss

Maße, Typo und Farben stehen in `references/layout.md`. Dort steht auch, warum die
Stationen mit Float statt Flexbox gebaut sind – diese Stelle bitte vor jeder
Änderung lesen, sonst brechen die Seitenumbrüche.
