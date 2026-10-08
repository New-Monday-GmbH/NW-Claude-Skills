---
name: newmonday-bewerbermappe
description: Baut in einem Lauf alle drei New-Monday-Dokumente eines Kandidaten – Lebenslauf (vollständig und anonym), Skill Matrix und Portfolio –, jeweils als PDF und als Frames auf einer gemeinsamen Figma-Seite. Führt newmonday-cv, newmonday-skillmatrix und newmonday-portfolio nacheinander aus, stellt jede gemeinsame Frage nur einmal (Sprache, Figma, Material), prüft vorab, was an Unterlagen fehlt, und bündelt alle Entscheidungen in einer Sitzung, bevor gebaut wird. Nutze diesen Skill immer, wenn alle drei Dokumente für denselben Kandidaten entstehen sollen – "die ganze Mappe", "das komplette Set", "alle Unterlagen für <Name>", "CV, Portfolio und Skillmatrix", "Bewerbermappe", "mach alles fertig für <Name>" –, und wenn ein laufender Gesamtlauf fortgesetzt oder um nachgelieferte Logos, Screens oder Fotos ergänzt werden soll. Für genau ein Dokument sind newmonday-cv, newmonday-skillmatrix und newmonday-portfolio zuständig.
---

# New Monday Bewerbermappe

Aus den Unterlagen eines Kandidaten entstehen in einem Lauf alle drei
New-Monday-Dokumente: der Lebenslauf (vollständig und anonym), die Skill Matrix
und das Portfolio – jeweils als PDF und als Frames auf einer gemeinsamen
Figma-Seite. Dieser Skill baut selbst nichts. Er sammelt ein, prüft, fragt und
verteilt; gebaut wird von `newmonday-cv`, `newmonday-skillmatrix` und
`newmonday-portfolio`, jeder in einem eigenen Subagenten.

## Die eine Regel, die alles andere schlägt

**Gefragt wird nur hier, gebaut wird nur dort.** Subagenten können dem Nutzer
keine Fragen stellen – `AskUserQuestion` fehlt ihnen. Deshalb holt dieser Skill
jede Antwort ein, bevor ein Subagent sie braucht, und die Subagenten arbeiten nur
mit dem, was in `auftrag.json` steht. Umgekehrt schreibt dieser Skill keinen
Dokumentinhalt: keine `cv.json`, keine Matrix, keinen Kundentext, keine
Übersetzung. Was in einem Dokument steht, entscheidet der zuständige Skill nach
seinen eigenen Regeln.

Daraus folgt:

- **Jede Frage, die mehrere Skills stellen würden, kommt genau einmal** –
  Sprache, Figma-Ziel, Material, Foto, Logos.
- **Nach Phase 4 wird nicht mehr gefragt.** Wer den Entscheidungsblock
  beantwortet hat, darf weggehen.
- **Was ein Subagent ohne Rückfrage entscheiden musste, steht in der
  Übergabe** – nie still.

## Voraussetzungen

- Die drei Skills liegen neben diesem Skill. Bei der Installation per Symlink
  aus dem Repo ist das so. Im Folgenden steht `<skills>` für den absoluten Pfad
  von `${CLAUDE_SKILL_DIR}/..` – einmal mit `cd "${CLAUDE_SKILL_DIR}/.." && pwd`
  ermitteln und so in jeden Subagenten-Auftrag schreiben.
- Das `Agent`-Werkzeug, Subagent-Typ `general-purpose`.
- Für Figma: ein verbundener Figma-MCP-Server und Bearbeitungsrecht auf der
  Zieldatei. Fehlt beides, entstehen nur die PDFs.

## Gefragt wird mit Klickboxen

Wie in den drei Skills: Jede Frage mit überschaubarer Antwortmenge läuft über
`AskUserQuestion` – bis zu vier Fragen je Aufruf, die wahrscheinlichste Option
zuerst, mit „(Empfohlen)“ im Label. Material, das der Nutzer schicken muss,
steht als Text in derselben Nachricht. Gefragt wird nur in Phase 1, 2 und 4.

## Ablauf

### Phase 1 — Eingang

Eine Nachricht. Vorher prüfen, ob das Arbeitsverzeichnis zum Skill-Repo gehört
(Phase 2, Punkt 3) – dann kommt die Ablage-Frage mit in denselben Aufruf. Bis
zu drei Klickboxen in einem `AskUserQuestion`-Aufruf:

```
Frage:    Sollen Lebenslauf, Skill Matrix und Portfolio auf Deutsch oder Englisch sein?
Header:   Sprache
Optionen: Deutsch | Englisch
```

```
Frage:    In welches Figma-File sollen die drei Dokumente?
Header:   Figma
Optionen: In ein bestehendes File – ich schicke den Link (Empfohlen)
        | Leg ein neues File an
```

Die Sprachfrage wird gestellt, auch wenn der Eingang eindeutig einsprachig
aussieht – ein englischer Lebenslauf kann für einen deutschen Kunden gedacht
sein. Sie gilt für alle drei Dokumente.

Daneben als Text, wörtlich so:

> Schick mir bitte:
>
> - den **Lebenslauf** als PDF,
> - den **LinkedIn-Export** als PDF (auf dem Profil: *Mehr* → *Als PDF
>   speichern*) und den **Link zum Profil** (linkedin.com/in/…) – daraus hole
>   ich auch das Foto,
> - das **Portfolio** als Link zur Website oder als PDF,
> - den **Link zum Figma-File** (figma.com/design/…), falls es ein bestehendes
>   sein soll. Ich lege darin eine Seite mit dem Namen des Kandidaten an und
>   brauche Bearbeitungsrechte.
>
> Wenn es sie gibt, spart das Zeit: Firmen- und Kundenlogos als SVG, Screenshots
> je Projekt (einzelne Exporte, ein Screen je Datei), Zertifikate als Bild oder
> PDF, ein Foto in guter Auflösung, ein paar Sätze zu jedem Kunden, ein
> Xing-Profil.

**Was mit dem Aufruf schon kam, wird nicht noch einmal erbeten.** Dateien und
Links, die schon im Chat liegen, fallen aus der Liste; eine genannte Sprache
(„auf Englisch“) ersetzt die Sprachfrage, ein mitgeschickter Figma-Link die
Figma-Frage. Ist dann nichts mehr offen, entfällt die Nachricht ganz.

Die Ablage-Frage aus Phase 2, Punkt 3 steht, wenn nötig, als dritte Klickbox in
diesem Aufruf. Liegen die Unterlagen schon im Chat, den Namen vorher nach
Phase 2, Punkt 2 lesen; sonst heißt es in der Frage „für den Kandidaten“.

### Phase 2 — Lückencheck vor dem Lesen

Alles in dieser Phase erledigt dieser Skill selbst, ohne Subagenten.

1. **Material zuordnen.** Jede Datei nach ihrem Inhalt, nicht nach dem Namen:
   `pdftotext -l 1 <datei> - | head -40`. Ein LinkedIn-Export trägt auf Seite 1
   „Kontakt“ bzw. „Contact“, „Top-Kenntnisse“ bzw. „Top Skills“ und eine
   `linkedin.com/in/`-Adresse. Bleibt eine Zuordnung unklar, im Fließtext der
   Lücken-Nachricht nachfragen.
2. **Kandidatenname** aus der ersten Seite von Lebenslauf oder LinkedIn-Export.
   Bleibt der Text leer (als Bild gesetztes PDF), die erste Seite als Bild lesen.
   Mit der Zuordnung aus Punkt 1 ist das die einzige Inhaltsarbeit dieses
   Skills; der Name gibt Laufordner und Figma-Seite ihren Namen.
3. **Ablageort.** Der Laufordner heißt wie der Kandidat und liegt im
   Arbeitsverzeichnis – außer das Arbeitsverzeichnis gehört zum Skill-Repo:

   ```bash
   top=$(git rev-parse --show-toplevel 2>/dev/null) && [ -d "$top/newmonday-bewerber/skills" ] && echo "Skill-Repo"
   ```

   Dann kommen Kandidatendaten nicht dorthin. Die Frage dazu steht schon im
   Aufruf aus Phase 1:

   ```
   Frage:    Wohin soll der Laufordner für <Vorname Nachname>?
   Header:   Ablage
   Optionen: Schreibtisch (Empfohlen) | Downloads
   ```

   Über „Other“ nennt der Nutzer einen eigenen Ort. Existiert der Laufordner
   schon mit einer `auftrag.json`, ist das eine Wiederaufnahme – siehe unten.
4. **Umgebung.** Einmal je Skill:

   ```bash
   python3 <skills>/newmonday-cv/scripts/pruefe_umgebung.py
   python3 <skills>/newmonday-skillmatrix/scripts/pruefe_umgebung.py
   python3 <skills>/newmonday-portfolio/scripts/pruefe_umgebung.py
   ```

   Meldet eins eine Lücke, gehört der Installationsbefehl aus der Ausgabe in die
   Lücken-Nachricht.
5. **Figma lesen.** Per ToolSearch `whoami figma` suchen und `whoami` aufrufen.
   Antworten zwei Figma-Server, zählt der, dessen `whoami` durchläuft; ein nicht
   angemeldeter zweiter Server wird ignoriert. Dann:
   - Link ist eine Design-Datei: `figma.com/design/…`. `/board/`, `/slides/`,
     `/make/`, `/proto/` gehen nicht – das ist eine Lücke.
   - Datei lesbar: `get_metadata` mit dem `fileKey` (der Teil nach `/design/`).
   - Bei „neues File“: den Plan aus `whoami` nehmen, dessen Seat nicht „View“ ist.
     Gibt es mehrere, kommt eine Klickbox mit den Plannamen in die
     Lücken-Nachricht – auch dann, wenn bei „bestehendes File“ der Link fehlt und
     die Lücken-Nachricht deshalb ein neues File ankündigt (Punkt 7).
6. **Die Lücken-Nachricht** – nur, wenn etwas fehlt. Jeder fehlende Posten mit
   seiner Folge, in diesem Wortlaut:

   | Fehlt | Folge |
   |---|---|
   | Lebenslauf | Der Lebenslauf entsteht allein aus dem LinkedIn-Export, und die erste Fotoquelle fehlt. |
   | LinkedIn-Export | Firmennamen, Zeiträume und Rollen kommen nur aus dem Lebenslauf – vollständige Firmierungen und feiner aufgeteilte Stationen fehlen oft. |
   | LinkedIn-Link | Kein automatisches Profilfoto von LinkedIn und kein LinkedIn-Verweis im Lebenslauf. |
   | Portfolio | Das Portfolio entsteht nur aus Lebenslauf und LinkedIn, mit Platzhaltern statt Screens; Lebenslauf und Skill Matrix fehlt die dritte Quelle. |
   | Figma-Link (bei „bestehendes File“) | Ich lege ein neues Figma-File an. |
   | Figma nicht verbunden oder falscher Dateityp | Es entstehen nur die PDFs, keine Frames. |
   | Umgebung | <Skill> kann nicht rendern: <was fehlt>. Einrichten mit: `<Befehl>` |

   Dazu eine Klickbox:

   ```
   Frage:    Kannst du das nachliefern bzw. einrichten?
   Header:   Nachliefern
   Optionen: Ich liefere nach bzw. richte es ein (Empfohlen) | Ohne weitermachen
   ```

   Weder Lebenslauf noch LinkedIn-Export: Dann gibt es keine Klickbox, sondern
   nur die Bitte darum. Ohne eins von beiden beginnt kein Lauf.

   „Ich liefere nach bzw. richte es ein“: auf das Material bzw. die Einrichtung
   warten und die Punkte 1–6 dafür wiederholen. „Ohne weitermachen“: Die
   Materialposten kommen in `auftrag.json` unter `ohne` und werden in diesem
   Lauf nicht mehr angesprochen – auch von den Skills nicht. Stand „Figma
   nicht verbunden oder falscher Dateityp“ auf der Liste, wird Figma
   ausgelassen: `figma.aktiv = false`. Fehlte nur der Figma-Link, entsteht ein
   neues File (Punkt 7). Stand die Umgebung auf der Liste, bricht der
   betroffene Skill beim Rendern ab und steht in der Übergabe unter „Nicht
   gebaut“. Das optionale Material aus Phase 1 ist nie eine Lücke.
7. **Figma-Zielseite anlegen – zugleich der Schreibtest.** Nur wenn Figma
   bleibt. Erst den Skill `figma:figma-use` laden, dann per `use_figma`:
   - Link mit `node-id` → die Seite dieses Knotens, dazu ein Schreibtest (ein
     winziger Frame weit außerhalb, sofort wieder entfernt):

     ```js
     let n = await figma.getNodeByIdAsync("<node-id mit Doppelpunkt, z. B. 12:34>");
     while (n && n.type !== "PAGE") n = n.parent;
     if (!n) return { seite: null };
     await figma.setCurrentPageAsync(n);
     const t = figma.createFrame();
     t.resize(1, 1); t.x = -100000; t.y = -100000;
     n.appendChild(t); t.remove();
     return { seite: n.id, schreibtest: "ok" };
     ```

     Kommt `seite: null` zurück, gibt es den Knoten nicht mehr (gelöscht oder
     veraltet): weiter wie bei einem Link ohne `node-id`.

   - sonst die Seite „Vorname Nachname“ – vorhanden (früherer Lauf) oder neu:

     ```js
     const NAME = "<Vorname Nachname>";
     let seite = figma.root.children.find(p => p.name === NAME);
     const neu = !seite;
     if (neu) { seite = figma.createPage(); seite.name = NAME; }
     return { seite: seite.id, neu };
     ```

   - „neues File“: zuerst den Skill `figma:figma-create-new-file` laden, das File
     `Bewerbermappe — Vorname Nachname` mit `create_new_file` im Plan aus Punkt 5
     anlegen und dessen erste, leere Seite in „Vorname Nachname“ umbenennen,
     statt eine zweite anzulegen. Genauso, wenn „bestehendes File“ mangels Link
     auf ein neues File zurückfällt: Die Planwahl aus Punkt 5 gilt dann auch,
     ihre Klickbox stand in der Lücken-Nachricht.

   Aus der Seiten-ID `12:34` wird der Link, den alle drei Skills bekommen:
   `https://www.figma.com/design/<fileKey>/<Name aus dem Link oder "Bewerbermappe">?node-id=12-34`.
   Alle drei legen ihre Frames auf die Seite, auf die ein Link mit `node-id`
   zeigt, jeweils rechts neben das Vorhandene – an ihnen ändert sich dafür
   nichts.

   Im selben Aufruf der **Bibliotheks-Vorflug**: Alle drei Skills bauen ihre
   Frames aus Instanzen der veröffentlichten Master-Bibliothek „Portfolio - CV
   Master“ (nie gelöst – eine Änderung im Master erreicht die Datei per
   Bibliotheks-Update). Ob die Bibliothek aus dieser Datei erreichbar ist, zeigt
   ein Import per Key (A4/Kopfzeile, von Lebenslauf und Skill Matrix geteilt):

   ```js
   let bibliothek = true;
   try { await figma.importComponentByKeyAsync("a9260f0ab20fa2d65c59bff74fcc6985261ff06a"); }
   catch (e) { bibliothek = false; }
   ```

   Das Ergebnis kommt nach `figma.bibliothek` in `auftrag.json`. Bei `false`
   bauen die Skills roh (ihr Rückfall), und jede Übergabe nennt den Grund. Die
   Skills machen ihren eigenen Vorflug trotzdem; dieser hier sagt dem Nutzer
   nur früh, woran er ist.

   Scheitert das Schreiben (nur Leserecht, Datei gesperrt), eine Klickbox:
   *Ich richte es ein (Empfohlen)* | *Ohne Figma weiter* (→ `figma.aktiv = false`).
   Das ist die einzige
   Frage nach der Lücken-Nachricht, und sie kommt nur in diesem Fall. Bricht der
   Nutzer den Lauf später ab, bleibt die leere Seite stehen – das ist in Kauf
   genommen.
8. **Laufordner anlegen und `auftrag.json` schreiben.** Aufbau und Felder:
   `references/formate.md`. Die Dateien werden nach `eingang/` kopiert, nicht
   verschoben (Logos nach `eingang/logos/`, Screens nach `eingang/screens/`, je
   Projekt ein Unterordner, wenn der Nutzer sie so geliefert hat, Zertifikate
   nach `eingang/zertifikate/`). Alle Status auf `offen`. Dann:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/pruefe_lauf.py "<laufordner>"
   ```

   Weiter erst bei „Lauf in Ordnung“.

### Phase 3 — Vorbereiten

Je Skill in der Reihenfolge aus `auftrag.json` (`newmonday-cv`,
`newmonday-skillmatrix`, `newmonday-portfolio`) ein Subagent mit Phase
*vorbereiten* – Auftrag siehe unten, im Vordergrund
(`run_in_background: false`), einer nach dem anderen.

**Das Skill-Repo bleibt sauber.** Vor jedem Subagenten – hier und in Phase 5 –
den Stand des Repos festhalten, danach vergleichen:

```bash
# vorher
repo=$(cd "<skills>/newmonday-cv" && cd "$(pwd -P)" && git rev-parse --show-toplevel); git -C "$repo" status --porcelain --untracked-files=all | sort > "<laufordner>/repo-vorher.txt"
# nachher – was neu dazugekommen ist
repo=$(cd "<skills>/newmonday-cv" && cd "$(pwd -P)" && git rev-parse --show-toplevel); git -C "$repo" status --porcelain --untracked-files=all | sort | comm -13 "<laufordner>/repo-vorher.txt" -
```

Neu aufgetauchte, nicht versionierte Dateien (`??`) außerhalb der
Logobibliothek (`newmonday-cv/assets/logos/`) und der Fotobibliothek der
Firmenzentralen (`newmonday-cv/assets/hq/`) hat der Subagent dort liegen
lassen: nach `<laufordner>/<kurz>/arbeit/aus-dem-repo/` verschieben und in der
Statuszeile nennen. Geänderte versionierte Dateien außerhalb der Bibliotheken
nicht anfassen – das kann Arbeit des Nutzers sein –, sondern unter „Hinweise“
der Gesamtübergabe nennen.

Nach jedem:

1. `pruefe_lauf.py` laufen lassen. Meldet es Fehler in der `fragen.json` dieses
   Skills, einmal nachfassen – derselbe Auftrag mit der Zeile
   `Nur fragen.json korrigieren. Fehler: <Zeilen aus pruefe_lauf>`. Bleibt es
   falsch, gilt die Vorbereitung als gescheitert.
2. Status in `auftrag.json` setzen: `fertig` oder `fehler` (Grund nach `fehler`).
3. Eine Statuszeile an den Nutzer: „Lebenslauf gelesen – 3 Fragen, 1 Lücke,
   2 Abweichungen.“

Ein gescheiterter Skill hält die anderen nicht auf.

**Neu vorbereiten heißt neu fragen.** Wird ein Skill ein weiteres Mal
vorbereitet – nach einer Nachlieferung in Phase 4 oder nach der Übergabe, bei
einer Wiederaufnahme mit offenem `vorbereiten` –, zuerst `entscheidungen.<skill>`
ganz aus `auftrag.json` löschen. Die alten Antworten gehören zu den alten Fragen;
Phase 4 stellt seine Fragen dann neu. Meldet er dabei Abweichungen, die bei der
letzten Quellen-Frage noch nicht vorlagen, wird auch `vorrang` gelöscht und neu
gefragt.

### Phase 4 — Entscheidungen

Eine Sitzung, in dieser Reihenfolge:

1. **Lücken und Quelle.** Die `luecken` aller drei `fragen.json`,
   zusammengeführt: Gleiches `was` erscheint einmal, mit der Folge je Dokument
   („Profilfoto – Lebenslauf: die Fotospalte bleibt leer; Skill Matrix: die Karte
   zeigt nur den Verlauf“). Dazu gescheiterte Vorbereitungen mit Grund. Und, wenn
   eine `fragen.json` `abweichungen` meldet, eine Tabelle aller Widersprüche –
   gleiches Feld aus mehreren Skills einmal:

   | Feld | Lebenslauf | LinkedIn-Export | Portfolio |
   |---|---|---|---|

   Ein `AskUserQuestion`-Aufruf mit höchstens vier Fragen:
   - bei Lücken: *Ich liefere nach (Empfohlen)* | *Ohne weitermachen*
   - bei Abweichungen die Quellen-Frage:

     ```
     Frage:    Die Unterlagen widersprechen sich (siehe oben). Welche Quelle ist die aktuellere – sie gilt dann für alle drei Dokumente?
     Header:   Quelle
     Optionen: die Quellen, die in der Tabelle vorkommen: Lebenslauf | Portfolio | LinkedIn-Export
     ```

     „(Empfohlen)“ trägt die Quelle, die in den `abweichungen` am häufigsten als
     `neuer` belegt ist, sonst der Lebenslauf. Die Antwort kommt als `vorrang` in
     `auftrag.json` (`lebenslauf`, `portfolio`, `linkedin_export`; über „Other“
     `Anweisung: <Text>`). Ohne Abweichungen gibt es die Frage nicht.
   - je gescheitertem Skill: *Ohne <Dokument> weiter (Empfohlen)* | *Abbrechen*

   Wird nachgeliefert: Dateien nach `eingang/`, `material` ergänzen, bei den
   Skills, die die Lücke gemeldet haben, `entscheidungen.<skill>` löschen,
   `vorbereiten` auf `offen` und Phase 3 für sie wiederholen – neues Material
   kann ihre Fragen ändern. Dann zurück an den Anfang dieser Phase; Lücken, die
   schon beantwortet sind, kommen nicht wieder. „Ohne weitermachen“: die Posten
   unter `ohne` – als Materialschlüssel nach der Tabelle zu `ohne` in
   `references/formate.md`, Posten ohne Schlüssel mit ihrem `was`-Text.
   „Ohne <Dokument>“: dessen `vorbereiten` und `bauen` auf `ausgelassen`.
2. **Texte.** Alle `texte` in Bau-Reihenfolge, je Skill unter einer
   Zwischenzeile („**Skill Matrix**“). Vor allem Hero-Beschreibung, Schwerpunkte,
   Matrix- und Tools-Tabelle mit Belegen – der Nutzer braucht sie, um die
   Freigabe-Frage zu beantworten.
3. **Fragen.** Die `fragen` aller Skills in möglichst wenigen
   `AskUserQuestion`-Aufrufen – höchstens vier Fragen je Aufruf, in
   Bau-Reihenfolge, die Fragen eines Skills möglichst beisammen. Übergeben werden
   `question`, `header`, `multiSelect` und `options` mit `label` und
   `description`; `id` und `text_noetig` bleiben draußen. Innerhalb eines Aufrufs
   müssen die Fragetexte verschieden sein, denn die Antworten kommen nach
   Fragetext zurück; bei gleichem Text hängt der Orchestrator „ (<Dokument>)“ an.
   Übersprungen werden Skills ohne Fragen und Skills, deren `vorbereiten` nicht
   auf `fertig` steht.
4. **Antworten ablegen** in `auftrag.json` unter
   `entscheidungen.<skill>.<id>`. Die Antworten kommen nach Fragetext zurück;
   die `id` ist die der Frage mit diesem Text. Gespeichert wird wörtlich, was
   zurückkommt – ohne „ (Empfohlen)“, bei mehreren Haken so, wie das Werkzeug
   sie liefert, bei „Other“ der eingegebene Text. Ist der Text über „Other“
   keine Antwort, sondern eine Anweisung an den Skill („erfinde du was
   Passendes“, „nimm den Titel aus LinkedIn“), wird `Anweisung: <Text wörtlich>`
   gespeichert. Hat die gewählte Option `"text_noetig": true`, im Fließtext nach
   dem Text fragen und `<Label>: <Text>` speichern – auch dieser Text wird zu
   `Anweisung: …`, wenn er eine Anweisung ist. Danach `pruefe_lauf.py`.
5. **Ansage:** „Ab hier läuft alles ohne Rückfrage – erst der Lebenslauf, dann
   die Skill Matrix, dann das Portfolio. Das dauert eine Weile; am Ende kommt
   eine Übergabe.“

### Phase 5 — Bauen

Je Skill, dessen `vorbereiten` auf `fertig` und `bauen` auf `offen` steht, in
Bau-Reihenfolge ein Subagent mit Phase *bauen*. Nie zwei gleichzeitig: Alle drei
schreiben in dieselbe Figma-Seite und dieselbe Logobibliothek. Den Stand des
Skill-Repos vorher festhalten und danach vergleichen wie in Phase 3. Nach jedem:

1. `pruefe_lauf.py` laufen lassen. Meldet es Fehler in der `uebergabe.md` dieses
   Skills, einmal nachfassen wie in Phase 3 – derselbe Auftrag mit der Zeile
   `Nur uebergabe.md korrigieren. Fehler: <Zeilen aus pruefe_lauf>`. Bleibt sie
   falsch, gilt trotzdem die Rückgabe; Phase 6 nimmt die Datei, wie sie ist.
2. Status in `auftrag.json` setzen und die gemeldeten PDFs in `ausgabe/`
   nachsehen.
3. Eine Statuszeile: „Lebenslauf fertig – 2 PDFs, Figma auf der Seite.“ Die
   Skill Matrix liefert ebenfalls zwei PDFs, die lange und die A4-Fassung, und
   in Figma den langen Frame mit den A4-Seiten rechts daneben: „Skill Matrix
   fertig – 2 PDFs (lang, A4), Figma auf der Seite.“

Scheitert einer, geht es mit dem nächsten weiter; nachgefragt wird nicht.

### Phase 6 — Gesamtübergabe

Die drei `uebergabe.md` ganz lesen. Sie haben dieselben sechs Abschnitte
(`references/formate.md`); aus ihnen setzen sich die Punkte 1–5 und 7 Abschnitt
für Abschnitt zusammen, Punkt 6 kommt aus `status` in `auftrag.json`. Alles in
einer Nachricht:

1. **Fertig: Vorname Nachname** – die Dateien aus `ausgabe/` (von der Skill
   Matrix beide Fassungen, lang und A4) und der Link auf die Figma-Seite. Ist Figma bei einem Dokument gescheitert, steht hier der Grund –
   die PDFs sind trotzdem da.
2. **Zur Freigabe** – je Dokument, was dort steht, im Wortlaut: Kurzprofil,
   abgeleitete Skillset-Einträge mit Beleg und die Prüf-Meldungen von
   `anonymisieren.py` (dort steht womöglich noch der Name im anonymen PDF),
   Hero-Beschreibung und die endgültige Matrix, Cover-Titel, KI- und
   Prozesstexte, Kundentexte mit Quellen, KI-generierte Gebäude und alles, was
   ein Skill auf eine `Anweisung: …` hin selbst formuliert hat.
3. **Quellen weichen ab** – jede Abweichung einmal, mit den Werten je Quelle und
   der Fassung, die drinsteht. Es gilt in allen drei Dokumenten dieselbe Quelle:
   die aus `vorrang`, sonst der Lebenslauf.
4. **Hinweise** – je Dokument der Rest, **vollständig, nur ohne Wiederholungen**.
5. **Ohne Rückfrage entschieden** – aus allen drei, mit Dokument und Stelle.
   Leer: Abschnitt weglassen.
6. **Nicht gebaut** – Dokumente mit `fehler` oder `ausgelassen`, mit Grund.
   Leer: weglassen.
7. **Ganz zum Schluss** die Zeilen aus „Fehlt noch“ aller drei, **wörtlich**:
   die Logo-Zeilen zuerst, danach die übrigen, beides in Bau-Reihenfolge.
   Nichts dazuschreiben, nicht zusammenfassen – jeder Skill hat seinen Satz.
   Fehlt nirgends etwas, steht hier nichts.

Wurden Frames neben ältere eines früheren Laufs gelegt, steht das in den
Hinweisen: Die alten bleiben stehen, bis jemand sie löscht.

## Der Auftrag an die Subagenten

`Agent` mit `subagent_type: general-purpose`, im Vordergrund –
`run_in_background: false`, denn die Reihenfolge ist strikt. Die spitzen
Klammern füllt dieser Skill, alles andere steht wörtlich so im Auftrag:

```
Gesamtlauf newmonday-bewerbermappe · Skill: <skill> · Phase: <vorbereiten|bauen>
Laufordner: <laufordner>
Skill-Ordner: <laufordner>/<cv|skillmatrix|portfolio>/

1. Lade den Skill <skill> mit dem Skill-Werkzeug – genau diesen Namen, ohne
   Präfix (nicht anthropic-skills:<skill>, das ist eine andere Fassung). Steht
   das Werkzeug nicht zur Verfügung: lies <skills>/<skill>/SKILL.md; wo dort die
   Variable CLAUDE_SKILL_DIR steht, gilt <skills>/<skill>.
2. Lies dort den Abschnitt „Im Gesamtlauf“. Er sagt, welche Schritte zu dieser
   Phase gehören, und geht jeder anderen Anweisung des Skills vor.
3. Allgemeine Regeln:
   - Schritt 0 des Skills entfällt. Sprache, Figma-Ziel und Material stehen in
     <laufordner>/auftrag.json; Pfade darin sind relativ zum Laufordner.
   - Kein AskUserQuestion und keine Frage an den Nutzer in deiner Antwort.
     Vorbereiten: jede Frage nach fragen.json, jede Materialbitte nach
     „luecken“. Bauen: bei Unerwartetem die Option nehmen, die der Skill
     empfiehlt, und sie in uebergabe.md unter „Ohne Rückfrage entschieden“
     notieren.
   - Formate von fragen.json, notizen.md und uebergabe.md:
     <skills>/newmonday-bewerbermappe/references/formate.md
   - Arbeitsordner ist der Skill-Ordner: arbeit/, die JSON des Skills,
     fragen.json, notizen.md und uebergabe.md liegen dort. PDFs nach
     <laufordner>/ausgabe/.
   - Arbeite mit absoluten Pfaden und beginne jeden Shell-Befehl mit
     cd "<laufordner>/<cv|skillmatrix|portfolio>" – manche Skripte legen Dateien
     im aktuellen Verzeichnis ab, und das Arbeitsverzeichnis der Sitzung ist das
     Skill-Repo oder ein anderer Ordner.
   - Figma, wenn figma.aktiv true ist – dann immer, auch bei der Skill Matrix;
     sonst gar nicht. figma.link zeigt mit node-id auf die Seite, auf die alles
     kommt. Keine eigene Seite anlegen, nichts Vorhandenes anfassen. Gebaut
     wird über den Bibliotheksweg des Skills (Instanzen der Master-Bibliothek,
     nie lösen); steht figma.bibliothek auf false oder scheitert der Vorflug
     des Skills, sein roher Rückfall – in uebergabe.md vermerkt. Scheitert
     Figma, gehen die PDFs trotzdem raus, und der Grund steht in uebergabe.md.
   - Was in auftrag.json unter „ohne“ steht (Materialschlüssel oder der
     was-Text einer Lücke, Tabelle in formate.md), nicht mehr als Lücke melden
     und nicht noch einmal erbitten. Die Zeilen unter „Fehlt noch“ in
     uebergabe.md bleiben trotzdem wörtlich.
   - Antworten: auftrag.json → entscheidungen.<skill>.<id>, wörtlich, wie der
     Nutzer sie gegeben hat; die Optionen dazu stehen in fragen.json. Eine
     Antwort mit mehreren Haken gegen die Labels dort abgleichen, nie an Kommas
     trennen – Labels enthalten selbst Kommas. Beginnt eine Antwort mit
     „Anweisung:“, ist sie kein Wert, sondern eine Anweisung: ihr innerhalb der
     Regeln des Skills folgen; was du dabei selbst formulierst, steht in
     uebergabe.md unter „Zur Freigabe“ mit dem Vermerk „selbst formuliert, auf
     Anweisung“.
   - Widersprechen sich Lebenslauf, LinkedIn-Export und Portfolio: Vorbereiten
     meldet jeden Widerspruch in fragen.json unter „abweichungen“ (formate.md).
     Beim Bauen gilt die Quelle aus auftrag.json → vorrang, danach Lebenslauf,
     Portfolio, LinkedIn-Export; fehlt vorrang, der Lebenslauf. Das gilt in allen
     drei Dokumenten gleich und ersetzt im Gesamtlauf die Rangfolge des Skills.
     Die Ergänzungsregeln des Skills bleiben: Eine andere Quelle füllt Lücken,
     die Firmierung kommt vollständig aus LinkedIn, die feinere Angabe gilt,
     solange sie der gröberen nicht widerspricht.
   - Tools: Lebenslauf und Skill Matrix führen dieselben Tools – gleiche
     Einträge, gleiche Schreibweise; die Reihenfolge darf abweichen. Maßgeblich ist die
     Skill Matrix (Entwurf in skillmatrix/notizen.md, nach der Freigabe in
     skillmatrix.json); der Lebenslauf übernimmt sie wörtlich als
     skillset.tools, auch wenn sein Eingang andere Tools nennt.
   - Beim Bauen zuerst notizen.md lesen; was dort steht, nicht neu herleiten.
     Steht in diesem Auftrag „Nachgeliefert: …“, gilt dieses Material vor dem,
     was notizen.md sagt; was es an Aufbereitung braucht (etwa den Fotozuschnitt
     aus Schritt 1a oder die Zuordnung neuer Screens zu Projekten), gehört dann
     zum Bauen.
   - Zum Schluss: python3 <skills>/newmonday-bewerbermappe/scripts/pruefe_lauf.py
     "<laufordner>" – Fehler in deinen Dateien beheben.
4. Rückgabe, eine Zeile:
   vorbereiten → „fertig: <n> Fragen, <m> Lücken, <k> Abweichungen“ oder
                 „fehler: <Grund>“
   bauen → „fertig: <PDF-Dateien>; Figma: <node-id | aus | gescheitert – Grund>“
           oder „fehler: <Grund>“
```

Ans Ende des Auftrags kommen, wenn es sie gibt:

- bei einem Änderungswunsch nach der Übergabe (siehe unten) die Zeile
  `Änderung des Nutzers: <Text, wörtlich>`;
- beim Neu-Bauen nach einer Nachlieferung je Posten eine Zeile
  `Nachgeliefert: <Posten> → <Pfad relativ zum Laufordner>`, etwa
  `Nachgeliefert: Foto → eingang/foto.jpg`.

## Wiederaufnahme, Nachlieferung, Änderungen

**Wiederaufnahme.** Liegt ein Laufordner mit `auftrag.json` vor und soll es
weitergehen („mach den Lauf Timo Muster weiter“, auch in einer neuen Sitzung):
`pruefe_lauf.py`, dann `status` lesen und an der ersten offenen Stelle ansetzen –
`vorbereiten` offen → Phase 3 für diese Skills, ihre Antworten vorher gelöscht
(„Neu vorbereiten heißt neu fragen“); vorbereitet, aber Antworten zu Fragen aus
`fragen.json` fehlen – oder `vorrang`, obwohl `abweichungen` vorliegen → Phase 4,
nur für die fehlenden; `bauen` offen → Phase 5;
alles fertig → Phase 6 noch einmal. Beantwortetes wird nicht erneut gefragt –
außer die Fragen eines Skills, der neu vorbereitet wird: Seine Antworten sind
gelöscht, Phase 4 stellt sie neu.

**Nachlieferung nach der Übergabe.** Dateien nach `eingang/`, `material`
ergänzen, den Posten aus `ohne` streichen. Neu gebaut werden die Dokumente,
deren `uebergabe.md` das Material unter „Fehlt noch“ nennt. Ob dafür neu
vorbereitet werden muss – und welche Dokumente es trifft, wenn keine
„Fehlt noch“-Zeile das Material nennt –, sagt die Tabelle:

| Nachgeliefert | neu vorbereiten | neu bauen |
|---|---|---|
| Lebenslauf, LinkedIn-Export, Portfolio | alle drei (dann Phase 4) | alle drei |
| Zertifikate | Skill Matrix (dann Phase 4) | Skill Matrix |
| Foto | – | alle drei |
| Logos | – | Lebenslauf, Portfolio |
| Screens | – | Portfolio |

„Neu vorbereiten“ heißt `entscheidungen.<skill>` löschen, `vorbereiten` auf
`offen`, Phase 3 und danach Phase 4 mit allen Fragen dieses Skills. „Neu bauen“
heißt `bauen` auf `offen` und Phase 5 – ohne Rückfragen; der Bauen-Auftrag trägt
je nachgeliefertem Posten die Zeile `Nachgeliefert: <Posten> → <Pfad>`. Die
Frames kommen neben die alten, die Übergabe sagt das.

**Änderungswünsche nach der Übergabe** („Kurzprofil kürzer“, „Projekt X raus“):
Für das betroffene Dokument `bauen` auf `offen` und den Bauen-Auftrag mit der
Zeile `Änderung des Nutzers: …` schicken. Den Inhalt ändert der Skill, nicht
dieser.

## Was fest steht

- **Reihenfolge**: Lebenslauf → Skill Matrix → Portfolio, nacheinander, nie
  parallel.
- **Eine Sprache** für alle drei Dokumente.
- **Eine Quelle bei Widersprüchen** für alle drei Dokumente – die, die der Nutzer
  als die aktuellere wählt; gefragt wird nur, wenn sich die Unterlagen
  widersprechen.
- **Dieselben Tools** in Lebenslauf und Skill Matrix – die der Skill Matrix,
  wörtlich; die Reihenfolge darf abweichen. `pruefe_lauf.py` vergleicht beide
  (Warnung, solange eins noch nicht gebaut ist, danach Fehler). Ändert sich die
  Liste nach der Übergabe, werden beide Dokumente neu gebaut.
- **Eine Figma-Seite je Kandidat**, alle Frames darauf. Figma hält kein PDF auf.
- **Figma aus der Master-Bibliothek.** Frames bestehen aus Instanzen der
  veröffentlichten Bibliothek „Portfolio - CV Master“ und werden nie gelöst;
  roh nur als Rückfall, wenn die Bibliothek nicht erreichbar ist.
- **Kandidatendaten nie ins Skill-Repo** – nicht in den Skill-Ordnern, nicht im
  Repo-Arbeitsverzeichnis.
- **Kein Dokumentinhalt von diesem Skill.** Er ruft keine Render-, Logo- oder
  Figma-Skripte der drei Skills auf; einzig `pruefe_umgebung.py` in Phase 2.
- **Die Übergabe-Schlusszeilen der Skills bleiben wörtlich.**
