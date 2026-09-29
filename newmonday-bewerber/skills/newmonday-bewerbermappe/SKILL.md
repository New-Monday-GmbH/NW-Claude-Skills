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

Eine Nachricht. Zwei Klickboxen in einem `AskUserQuestion`-Aufruf:

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

   Dann kommen Kandidatendaten nicht dorthin, und die Lücken-Nachricht trägt
   eine Klickbox mehr – allein gestellt, wenn sonst nichts fehlt:

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
     Lücken-Nachricht.
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
   - Link mit `node-id` → die Seite dieses Knotens:

     ```js
     let n = await figma.getNodeByIdAsync("<node-id mit Doppelpunkt, z. B. 12:34>");
     while (n && n.type !== "PAGE") n = n.parent;
     return { seite: n ? n.id : null };
     ```

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
     statt eine zweite anzulegen.

   Aus der Seiten-ID `12:34` wird der Link, den alle drei Skills bekommen:
   `https://www.figma.com/design/<fileKey>/<Name aus dem Link oder "Bewerbermappe">?node-id=12-34`.
   Alle drei legen ihre Frames auf die Seite, auf die ein Link mit `node-id`
   zeigt, jeweils rechts neben das Vorhandene – an ihnen ändert sich dafür
   nichts.

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
*vorbereiten* – Auftrag siehe unten, im Vordergrund, einer nach dem anderen.
Nach jedem:

1. `pruefe_lauf.py` laufen lassen. Meldet es Fehler in der `fragen.json` dieses
   Skills, einmal nachfassen – derselbe Auftrag mit der Zeile
   `Nur fragen.json korrigieren. Fehler: <Zeilen aus pruefe_lauf>`. Bleibt es
   falsch, gilt die Vorbereitung als gescheitert.
2. Status in `auftrag.json` setzen: `fertig` oder `fehler` (Grund nach `fehler`).
3. Eine Statuszeile an den Nutzer: „Lebenslauf gelesen – 3 Fragen, 1 Lücke.“

Ein gescheiterter Skill hält die anderen nicht auf.

### Phase 4 — Entscheidungen

Eine Sitzung, in dieser Reihenfolge:

1. **Lücken.** Die `luecken` aller drei `fragen.json`, zusammengeführt:
   Gleiches `was` erscheint einmal, mit der Folge je Dokument („Profilfoto –
   Lebenslauf: die Fotospalte bleibt leer; Skill Matrix: die Karte zeigt nur den
   Verlauf“). Dazu gescheiterte Vorbereitungen mit Grund. Ein
   `AskUserQuestion`-Aufruf:
   - bei Lücken: *Ich liefere nach (Empfohlen)* | *Ohne weitermachen*
   - je gescheitertem Skill: *Ohne <Dokument> weiter (Empfohlen)* | *Abbrechen*

   Wird nachgeliefert: Dateien nach `eingang/`, `material` ergänzen, bei den
   Skills, die die Lücke gemeldet haben, `vorbereiten` auf `offen` und Phase 3
   für sie wiederholen – neues Material kann ihre Fragen ändern. Dann zurück an
   den Anfang dieser Phase; Lücken, die schon beantwortet sind, kommen nicht
   wieder. „Ohne weitermachen“: die Posten unter `ohne`. „Ohne <Dokument>“:
   dessen Status auf `ausgelassen`.
2. **Texte.** Alle `texte` in Bau-Reihenfolge, je Skill unter einer
   Zwischenzeile („**Skill Matrix**“). Vor allem Hero-Beschreibung, Schwerpunkte,
   Matrix- und Tools-Tabelle mit Belegen – der Nutzer braucht sie, um die
   Freigabe-Frage zu beantworten.
3. **Fragen.** Je Skill ein `AskUserQuestion`-Aufruf mit seinen `fragen`, in
   Bau-Reihenfolge. Übergeben werden `question`, `header`, `multiSelect` und
   `options` mit `label` und `description`; `id` und `text_noetig` bleiben
   draußen. Skills ohne Fragen werden übersprungen.
4. **Antworten ablegen** in `auftrag.json` unter
   `entscheidungen.<skill>.<id>`. Die Antworten kommen nach Fragetext zurück;
   die `id` ist die der Frage mit diesem Text. Gespeichert wird wörtlich, was
   zurückkommt – ohne „ (Empfohlen)“, bei mehreren Haken so, wie das Werkzeug
   sie liefert, bei „Other“ der eingegebene Text. Hat die gewählte Option
   `"text_noetig": true`, im Fließtext nach dem Text fragen und
   `<Label>: <Text>` speichern. Danach `pruefe_lauf.py`.
5. **Ansage:** „Ab hier läuft alles ohne Rückfrage – erst der Lebenslauf, dann
   die Skill Matrix, dann das Portfolio. Das dauert eine Weile; am Ende kommt
   eine Übergabe.“

### Phase 5 — Bauen

Je Skill, dessen `vorbereiten` auf `fertig` und `bauen` auf `offen` steht, in
Bau-Reihenfolge ein Subagent mit Phase *bauen*. Nie zwei gleichzeitig: Alle drei
schreiben in dieselbe Figma-Seite und dieselbe Logobibliothek. Nach jedem:
`pruefe_lauf.py`, Status setzen, die gemeldeten PDFs in `ausgabe/` nachsehen,
eine Statuszeile („Lebenslauf fertig – 2 PDFs, 4 Frames“). Scheitert einer, geht
es mit dem nächsten weiter; nachgefragt wird nicht.

### Phase 6 — Gesamtübergabe

Die drei `uebergabe.md` ganz lesen. Sie haben dieselben sechs Abschnitte
(`references/formate.md`), und die Übergabe setzt sich Abschnitt für Abschnitt
daraus zusammen, in einer Nachricht:

1. **Fertig: Vorname Nachname** – die Dateien aus `ausgabe/` und der Link auf die
   Figma-Seite. Ist Figma bei einem Dokument gescheitert, steht hier der Grund –
   die PDFs sind trotzdem da.
2. **Zur Freigabe** – je Dokument, was dort steht, im Wortlaut: Kurzprofil,
   Hero-Beschreibung und die endgültige Matrix, Cover-Titel, KI- und
   Prozesstexte, Kundentexte mit Quellen, KI-generierte Gebäude.
3. **Quellen weichen ab** – jede Abweichung einmal. Nennen zwei Skills dasselbe
   Feld mit denselben Werten, wird daraus eine Zeile mit der Fassung je
   Dokument. Die Regeln unterscheiden sich: Im Lebenslauf und in der Skill Matrix
   gewinnt der Lebenslauf, im Portfolio das Portfolio.
4. **Hinweise** – je Dokument der Rest, knapp.
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

`Agent` mit `subagent_type: general-purpose`, im Vordergrund. Die spitzen
Klammern füllt dieser Skill, alles andere steht wörtlich so im Auftrag:

```
Gesamtlauf newmonday-bewerbermappe · Skill: <skill> · Phase: <vorbereiten|bauen>
Laufordner: <laufordner>
Skill-Ordner: <laufordner>/<cv|skillmatrix|portfolio>/

1. Lade den Skill <skill> mit dem Skill-Werkzeug – genau diesen Namen, ohne
   Präfix (nicht anthropic-skills:<skill>, das ist eine andere Fassung). Steht
   das Werkzeug nicht zur Verfügung: lies <skills>/<skill>/SKILL.md und setze
   ${CLAUDE_SKILL_DIR} = <skills>/<skill>.
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
   - Figma, wenn figma.aktiv true ist – dann immer, auch bei der Skill Matrix;
     sonst gar nicht. figma.link zeigt mit node-id auf die Seite, auf die alles
     kommt. Keine eigene Seite anlegen, nichts Vorhandenes anfassen. Scheitert
     Figma, gehen die PDFs trotzdem raus, und der Grund steht in uebergabe.md.
   - Was in auftrag.json unter „ohne“ steht, nicht noch einmal erbitten.
   - Antworten: auftrag.json → entscheidungen.<skill>.<id>, wörtlich, wie der
     Nutzer sie gegeben hat; die Optionen dazu stehen in fragen.json.
   - Beim Bauen zuerst notizen.md lesen; was dort steht, nicht neu herleiten.
   - Zum Schluss: python3 <skills>/newmonday-bewerbermappe/scripts/pruefe_lauf.py
     "<laufordner>" – Fehler in deinen Dateien beheben.
4. Rückgabe, eine Zeile:
   vorbereiten → „fertig: <n> Fragen, <m> Lücken“ oder „fehler: <Grund>“
   bauen → „fertig: <PDF-Dateien>; Figma: <node-id | aus | gescheitert – Grund>“
           oder „fehler: <Grund>“
```

Bei einem Änderungswunsch nach der Übergabe (siehe unten) kommt als letzte Zeile
dazu: `Änderung des Nutzers: <Text, wörtlich>`.

## Wiederaufnahme, Nachlieferung, Änderungen

**Wiederaufnahme.** Liegt ein Laufordner mit `auftrag.json` vor und soll es
weitergehen („mach den Lauf Timo Muster weiter“, auch in einer neuen Sitzung):
`pruefe_lauf.py`, dann `status` lesen und an der ersten offenen Stelle ansetzen –
`vorbereiten` offen → Phase 3 für diese Skills; vorbereitet, aber Antworten zu
Fragen aus `fragen.json` fehlen → Phase 4, nur für die fehlenden; `bauen` offen →
Phase 5; alles fertig → Phase 6 noch einmal. Beantwortetes wird nicht erneut
gefragt.

**Nachlieferung nach der Übergabe.** Dateien nach `eingang/`, `material`
ergänzen, den Posten aus `ohne` streichen. Neu gebaut werden die Dokumente,
deren `uebergabe.md` das Material unter „Fehlt noch“ nennt. Ob dafür neu
vorbereitet werden muss – und welche Dokumente es trifft, wenn keine
„Fehlt noch“-Zeile das Material nennt –, sagt die Tabelle:

| Nachgeliefert | neu vorbereiten | neu bauen |
|---|---|---|
| Lebenslauf, LinkedIn-Export, Portfolio | alle drei (dann Phase 4 für neue Fragen) | alle drei |
| Zertifikate | Skill Matrix (dann Phase 4) | Skill Matrix |
| Foto | – | alle drei |
| Logos | – | Lebenslauf, Portfolio |
| Screens | – | Portfolio |

„Neu bauen“ heißt `bauen` auf `offen` und Phase 5 – ohne Rückfragen. Die
Frames kommen neben die alten, die Übergabe sagt das.

**Änderungswünsche nach der Übergabe** („Kurzprofil kürzer“, „Projekt X raus“):
Für das betroffene Dokument `bauen` auf `offen` und den Bauen-Auftrag mit der
Zeile `Änderung des Nutzers: …` schicken. Den Inhalt ändert der Skill, nicht
dieser.

## Was fest steht

- **Reihenfolge**: Lebenslauf → Skill Matrix → Portfolio, nacheinander, nie
  parallel.
- **Eine Sprache** für alle drei Dokumente.
- **Eine Figma-Seite je Kandidat**, alle Frames darauf. Figma hält kein PDF auf.
- **Kandidatendaten nie ins Skill-Repo** – nicht in den Skill-Ordnern, nicht im
  Repo-Arbeitsverzeichnis.
- **Kein Dokumentinhalt von diesem Skill.** Er ruft keine Render-, Logo- oder
  Figma-Skripte der drei Skills auf; einzig `pruefe_umgebung.py` in Phase 2.
- **Die Übergabe-Schlusszeilen der Skills bleiben wörtlich.**
