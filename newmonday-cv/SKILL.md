---
name: newmonday-cv
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*) Bash(pdftoppm *) Bash(pdfinfo *)
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

### Die einzige Ausnahme: das Kurzprofil

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

## Ablauf

Alle Aufrufe unten nutzen `${CLAUDE_SKILL_DIR}` — den Ordner, in dem diese
SKILL.md liegt. Das Arbeitsverzeichnis ist das des Nutzers, nicht das des Skills;
relative Pfade wie `scripts/render_cv.py` gehen deshalb ins Leere. Wird die
Variable in deiner Umgebung nicht ersetzt, steht sie für genau diesen Ordner.

### 0. Vor dem Start fragen — immer, in einer einzigen Nachricht

Bevor irgendetwas gebaut wird, diese drei Punkte klären. Gebündelt, nicht
nacheinander: der Nutzer soll alles auf einmal beantworten und liefern können.

1. **Die Sprache.** Wörtlich so fragen:

   > Soll der Lebenslauf auf Deutsch oder Englisch sein?

   Das entscheidet über die Rubriken im Dokument und darüber, in welcher Sprache
   das Kurzprofil geschrieben wird. Die Frage wird **immer** gestellt, auch wenn
   der Eingang eindeutig einsprachig aussieht – ein englischer Lebenslauf kann
   trotzdem für einen deutschen Kunden gedacht sein. Die Antwort kommt als
   `"sprache": "de"` oder `"sprache": "en"` in die `cv.json`.

   Ist die gewählte Sprache nicht die des Eingangs, muss übersetzt werden. Das
   ist eine bewusste Ausnahme von der Regel oben und braucht eine ausdrückliche
   Ansage – von sich aus wird nie übersetzt.

2. **Firmenlogos als SVG.** Die automatische Suche findet globale Marken
   zuverlässig, deutsche Agenturen und Mittelständler dagegen fast nie. Genau die
   stehen aber in den meisten Lebensläufen. Deshalb gleich zu Beginn darum
   bitten, die Logos der Arbeitgeber als SVG mitzuschicken – am besten aus dem
   Presse- oder Brand-Bereich der jeweiligen Firmenseite. Was schon in
   `assets/logos/` liegt, muss nicht noch einmal geliefert werden.

3. **Das LinkedIn-Profil.** Wörtlich so fragen:

   > Gibt es ein LinkedIn-Profil? Wenn du mir den Link schickst
   > (linkedin.com/in/…), ziehe ich das Profilfoto automatisch.

   Ist das Profil öffentlich, holt `linkedin_foto.py` das Foto von dort – siehe
   Schritt 1a. Das erspart das Heraussuchen und Zuschneiden von Hand. Der Link
   ist **zusätzlich** zum PDF-Export nützlich, nicht statt seiner: für die
   Inhalte taugt er nichts (siehe Schritt 1), fürs Foto schon.

4. **Ein Foto**, falls es über LinkedIn nicht klappt. Bringt der Lebenslauf
   keins mit und gibt es keinen Profil-Link, danach fragen: als Bilddatei
   schicken lassen, `extract_input.py` wandelt sie in Graustufen und schneidet
   sie aufs Layoutformat zu. Ohne Foto funktioniert das Layout, wirkt aber leer
   – die Fotospalte bleibt frei.

Ebenfalls hier erwähnen, falls noch nicht vorhanden: den LinkedIn-PDF-Export
(siehe Schritt 1). Er gehört in dieselbe Nachricht.

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

### 1a. Foto aus dem LinkedIn-Profil holen

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

### 2. Daten strukturieren

Aus dem Text eine `cv.json` bauen. Vollständiges Beispiel: `beispiel/cv.json`.

```json
{
  "sprache": "de",
  "person": { "name", "rolle", "erfahrung", "foto", "kurzprofil" },
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
die Rubriken ("Bildung" / "Education"), die Footer-Beschriftungen und den
Portfolio-Hinweis. Der Inhalt der Stationen wird davon nicht angefasst.

`logo` nimmt einen Dateinamen oder eine Liste davon – siehe Schritt 3.
`beschreibung` ist der Fließtext einer Station. Manche Lebensläufe beschreiben
eine Station als Absatz statt als Aufgabenliste; dann gehört der Absatz dorthin
und nicht als einzelner Bullet in `aufgaben`. Beides zusammen geht auch.

Zum Modell:

- **Stationen sind Arbeitgeber, Projekte sind deren Kunden.** Bei Agentur-,
  Beratungs- und Zeitarbeitsstationen hängen die Kundenprojekte unter der
  Station. Bei Festanstellungen ohne Kundenbezug bleibt `projekte` leer und die
  Inhalte stehen in `aufgaben`.
- **`erfahrung`**: Steht die Angabe im Lebenslauf, wird sie übernommen. Fehlt
  sie, ab der **ersten Berufsstation** bis heute rechnen, abgerundet auf volle
  Jahre, im Format `"7+ Jahre Erfahrung"`. **Ausbildungs- und Studienzeiten
  zählen nicht mit** – sonst kommen Werte heraus, die nicht zum Alter der Person
  passen. Ein Werkstudentenjob ist eine Berufsstation, eine Ausbildung nicht.
- **`zusammenfassung`** ist eine Schlagwortzeile mit zwei bis drei Begriffen, die
  die Tätigkeit der Station benennen – etwa `"Frontend-Entwicklung, Code-Reviews,
  Mentoring"`. Die Begriffe müssen sich aus den darunterliegenden Aufgaben
  ergeben. Kein Fließtext.
- **`firma`** enthält nur den Firmennamen. Angaben zur Beschäftigungsform gehören
  nicht ins Dokument: keine Befristungen, keine Kündigungsfristen, keine Gehälter,
  und auch keine Hinweise wie "(freiberuflich in Vollauslastung, 40h/Woche)".
- **Ausbildungen stehen nur unter `bildung`**, nie zusätzlich als Station, auch
  wenn der Eingang sie doppelt führt.
- **`skillset.links`** trägt üblicherweise Fähigkeiten, Zertifizierungen und
  Branchenerfahrung, **`rechts`** Tools und Sprachen. Die Aufteilung ist frei,
  aber die linke Spalte sollte die längere sein.

  **Bildung und Skillset müssen zusammen auf eine Seite passen.** Sie beginnen
  auf einer neuen Seite und dürfen keine weitere nach sich ziehen. Als Richtwert
  tragen beide zusammen etwa 6 Gruppen mit je bis zu 6 Einträgen. Bringt der
  Eingang mehr mit – Senior-Profile haben oft 40 Kompetenzen und mehr –, wird
  zusammengefasst: verwandte Gruppen zusammenlegen, je Gruppe die aussagekräftigsten
  Einträge behalten. **Der Wortlaut der übernommenen Einträge bleibt unverändert**,
  gekürzt wird durch Weglassen, nicht durch Umformulieren. Was wegfällt, wird am
  Ende gemeldet. Das Renderskript warnt, wenn der Block trotzdem überläuft.
- **`projekte[].zeitraum`** weglassen, wenn er mit dem der Station identisch ist.
- **Reihenfolge**: neueste Station zuerst.
- `kontakt` und `hinweis` weglassen – die Vorgaben stehen im Skript.

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

### 5. Übergeben

PDF ausgeben und dazu in wenigen Zeilen berichten:

- Das Kurzprofil im Wortlaut, falls es generiert wurde, mit der Bitte um Freigabe
- Wo Lebenslauf und LinkedIn auseinandergehen – mit beiden Werten, damit
  Tippfehler auffallen. Ins Dokument kam der Lebenslauf.
- Was das Skript an Zeiträumen bemängelt hat
- Woher das Foto stammt, wenn es automatisch von LinkedIn kam – und die
  gemeldete dpi-Zahl, falls sie unter 200 lag. Der Nutzer soll entscheiden
  können, ob ihm das für sein Kundendokument reicht.
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
