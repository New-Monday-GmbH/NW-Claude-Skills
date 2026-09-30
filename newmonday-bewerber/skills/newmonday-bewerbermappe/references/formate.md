# Formate im Gesamtlauf

Über diese vier Dateien reden Orchestrator und Subagenten miteinander. Ein
vollständiger Beispiel-Lauf (Kandidat „Timo Muster“, erfunden) liegt in
`beispiel/lauf/`. `scripts/pruefe_lauf.py <laufordner>` prüft jede dieser
Dateien, die es im Laufordner gibt – außer `fragen.json` bzw. `uebergabe.md`
eines Skills, dessen `vorbereiten` bzw. `bauen` auf `fehler` oder `ausgelassen`
steht; die übergeht es mit einer Warnung. `scripts/selbsttest.py` prüft das
Beispiel.

```
<Vorname Nachname>/
  eingang/          gelieferte Dateien, unverändert (logos/, screens/, zertifikate/)
  auftrag.json      schreibt nur der Orchestrator
  cv/               arbeit/, cv.json, fragen.json, notizen.md, uebergabe.md
  skillmatrix/      arbeit/, skillmatrix.json, fragen.json, notizen.md, uebergabe.md
  portfolio/        arbeit/, portfolio.json, fragen.json, notizen.md, uebergabe.md
  ausgabe/          alle PDFs
```

Die Unterordner heißen `cv`, `skillmatrix` und `portfolio` – je Skill einer, weil
alle drei Skills nach `arbeit/fotos/`, `arbeit/text.txt` und
`arbeit/figma_plan.json` schreiben.

## `auftrag.json` — schreibt nur der Orchestrator

Beispiel: `beispiel/lauf/auftrag.json`.

| Feld | Inhalt |
|---|---|
| `version` | `1` |
| `laufordner` | absoluter Pfad |
| `kandidat` | „Vorname Nachname“ |
| `sprache` | `de` oder `en`, für alle drei Dokumente |
| `reihenfolge` | `["newmonday-cv", "newmonday-skillmatrix", "newmonday-portfolio"]` |
| `figma.aktiv` | `false` = keine Frames |
| `figma.link` | Link auf die Kandidatenseite mit `node-id` (`…?node-id=12-34`) – den geben die Skills als ihren Figma-Link aus Schritt 0 |
| `figma.file_key`, `figma.seite_id` | Teil nach `/design/`; Seiten-ID `12:34` (passt zur `node-id`) |
| `figma.neues_file` | `true`, wenn der Orchestrator das File angelegt hat |
| `material.*` | `lebenslauf`, `linkedin_export`, `portfolio_pdf`, `foto`: Dateien; `logos`, `screens`, `zertifikate`: Ordner; `linkedin_url`, `xing_url`, `portfolio_url`: Adressen; `kundentexte`: Datei oder Text. Pfade relativ zum Laufordner. Nicht Vorhandenes fehlt oder ist `null`. |
| `vorrang` | welche Quelle bei Widersprüchen gilt – in allen drei Dokumenten: `lebenslauf`, `portfolio`, `linkedin_export`, oder `Anweisung: <Text>` (Antwort über „Other“); fehlt es oder ist es `null`, gilt `lebenslauf`. Danach gelten die übrigen Quellen in der Reihe Lebenslauf, Portfolio, LinkedIn-Export |
| `ohne` | Posten, die der Nutzer bewusst nicht liefert – Materialschlüssel wie unter `material`, bei Lücken ohne Schlüssel deren `was`-Text (Tabelle unten); werden nicht mehr erbeten und nicht mehr als Lücke gemeldet |
| `entscheidungen.<skill>.<id>` | Antwort auf die Frage mit dieser `id` aus `<skill>/fragen.json`, wörtlich (siehe unten) |
| `status.<skill>` | `vorbereiten` und `bauen`: `offen`, `fertig`, `fehler` oder `ausgelassen`; `fehler`: Grund oder `null` |

**Antworten** stehen so, wie `AskUserQuestion` sie zurückgibt: das Label ohne
„ (Empfohlen)“; bei mehreren Haken alle gewählten Labels, wie das Werkzeug sie
liefert; bei „Other“ der eingegebene Text. Hat die gewählte Option
`"text_noetig": true`, steht dort `<Label>: <Text>`. Ist der Text über „Other“
oder nach `text_noetig` keine Antwort, sondern eine Anweisung an den Skill
(„erfinde du was Passendes“), steht dort `Anweisung: <Text wörtlich>`. Fehlt eine `id`, wurde die
Frage nicht gestellt – eine Mehrfachauswahl ohne Haken steht deshalb als `""`
da, nie weggelassen. Eine Antwort mit mehreren Haken wird gegen die Labels in
`fragen.json` abgeglichen, nie an Kommas getrennt: Labels enthalten selbst
welche („Verkäufer, Media Markt (2014 – 2016)“).

**`ohne`** hält Materialschlüssel. Eine Lücke aus `fragen.json`, die der Nutzer
nicht liefert, kommt so hinein:

| `luecken[].was` | unter `ohne` |
|---|---|
| „Profilfoto“ | `foto` |
| „Lebenslauf“ | `lebenslauf` |
| „Zertifikate“ | `zertifikate` |
| „Screens <Projekt>“ | `screens` |
| ohne Materialschlüssel, etwa „Projektname <Kunde>“, „Weitere Projekte“ | der `was`-Text selbst |

`ohne` heißt: keine Lücke mehr melden, nicht mehr erbitten. Die Zeilen unter
„Fehlt noch“ in `uebergabe.md` bleiben trotzdem wörtlich.

## `fragen.json` — schreibt der Subagent beim Vorbereiten

Beispiele: `beispiel/lauf/cv/fragen.json`, `…/skillmatrix/fragen.json`,
`…/portfolio/fragen.json`.

```json
{
  "skill": "newmonday-cv",
  "kandidat": "Timo Muster",
  "texte": ["Markdown, das vor den Fragen gezeigt wird"],
  "luecken": [{ "was": "Profilfoto", "folge": "…", "form": "…" }],
  "abweichungen": [{ "feld": "Zeitraum Cortado",
                     "werte": { "lebenslauf": "2017 – 2023", "portfolio": "Jun 2017 – Aug 2024" },
                     "neuer": "portfolio" }],
  "fragen": [{ "id": "nm_rolle", "question": "…?", "header": "NM-Rolle",
               "multiSelect": false,
               "options": [{ "label": "… (Empfohlen)", "description": "…" },
                           { "label": "…", "description": "…", "text_noetig": true }] }]
}
```

- **`fragen`**: höchstens vier – so viele nimmt ein `AskUserQuestion`-Aufruf.
  Felder wie bei `AskUserQuestion`, dazu `id` (snake_case, eindeutig). Jede
  `question` endet mit „?“ und kommt nur einmal vor – die Antworten kommen nach
  Fragetext zurück. `header` höchstens 12 Zeichen (länger ist eine Warnung, das
  Werkzeug kürzt). 2–4 Optionen, Labels eindeutig; „(Empfohlen)“ höchstens
  einmal und dann an erster Stelle. Wortlaut und Optionen so, wie der Skill die
  Frage im Einzellauf stellt.
- **`text_noetig`** (optional, an einer Option): Wer sie wählt, wird im
  Fließtext nach dem Text gefragt – für „Ich möchte etwas ändern“ oder „Ich gebe
  es ein“.
- **`texte`**: Markdown-Blöcke, die der Nutzer vor den Fragen sehen muss, um sie
  zu beantworten – etwa die Matrix-Tabelle. Sonst leer.
- **`luecken`**: Material, nach dem der Skill im Einzellauf fragen würde. `was`
  ist der Posten; gleiche Posten heißen in allen Skills gleich, damit der
  Orchestrator sie zusammenlegen kann: „Profilfoto“, „Lebenslauf“,
  „Zertifikate“, „Screens <Projekt>“, „Projektname <Kunde>“,
  „Weitere Projekte“. `folge` sagt, was im Dokument passiert, wenn es nicht
  kommt; `form`, in welcher Form es kommen soll. Nichts, was unter `ohne` steht
  (Schlüssel: Tabelle zu `ohne` oben).
- **`abweichungen`** (optional): jeder Widerspruch zwischen Lebenslauf,
  LinkedIn-Export und Portfolio. `feld` benennt die Angabe („Zeitraum
  Cortado“, „Rolle“); `werte` nennt je Quelle (`lebenslauf`, `linkedin_export`,
  `portfolio`) ihren Wert – mindestens zwei Quellen, die sich unterscheiden;
  `neuer` (optional) die Quelle, deren Angabe das Material als die jüngere
  belegt. Kein Widerspruch und deshalb nicht gemeldet: eine Lücke (eine Quelle
  schweigt), eine andere Schreibweise derselben Firma, eine feinere Angabe, die
  der gröberen nicht widerspricht. Aus allen `abweichungen` fragt der
  Orchestrator einmal, welche Quelle die aktuellere ist – sie gilt dann in allen
  drei Dokumenten (`vorrang` in `auftrag.json`).

## `notizen.md` — schreibt der Subagent beim Vorbereiten

Freies Markdown. Alles, was der Bauen-Subagent aus dem Vorbereiten braucht und
was nicht in `fragen.json` steht; welche Punkte das je Skill sind, steht in
dessen Abschnitt „Im Gesamtlauf“. Pfade relativ zum Skill-Ordner. Der
Bauen-Subagent leitet nichts neu her, was hier steht.

## `uebergabe.md` — schreibt der Subagent beim Bauen

Sechs Abschnitte, genau diese Überschriften, in dieser Reihenfolge – der
Orchestrator setzt die Gesamtübergabe Abschnitt für Abschnitt daraus zusammen.
Ist ein Abschnitt leer, steht darunter „–“. Beispiel:
`beispiel/lauf/cv/uebergabe.md`.

```
# Übergabe <skill>

## Dateien
PDF-Dateien in ausgabe/ und der Figma-Link auf den ersten Frame (…?node-id=…) –
oder der Grund, warum kein Frame entstand

## Zur Freigabe
Alles, was der Skill selbst formuliert hat, im Wortlaut – auch auf eine
„Anweisung: …“ hin (Vermerk „selbst formuliert, auf Anweisung“)

## Quellen weichen ab
- <Feld>: <Quelle> „…“ / <Quelle> „…“ → im Dokument: „…“ (<Quelle nach vorrang>)

## Hinweise
Der Rest der Übergabe des Skills

## Ohne Rückfrage entschieden
- <Stelle>: was genommen wurde und warum

## Fehlt noch
Die Schlusszeilen des Skills, wörtlich
```
