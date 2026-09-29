# Formate im Gesamtlauf

Über diese vier Dateien reden Orchestrator und Subagenten miteinander. Ein
vollständiger Beispiel-Lauf (Kandidat „Timo Muster“, erfunden) liegt in
`beispiel/lauf/`. `scripts/pruefe_lauf.py <laufordner>` prüft jede dieser
Dateien, die es im Laufordner gibt; `scripts/selbsttest.py` prüft das Beispiel.

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
| `ohne` | Materialposten, die der Nutzer bewusst nicht liefert – werden nicht mehr erbeten |
| `entscheidungen.<skill>.<id>` | Antwort auf die Frage mit dieser `id` aus `<skill>/fragen.json`, wörtlich (siehe unten) |
| `status.<skill>` | `vorbereiten` und `bauen`: `offen`, `fertig`, `fehler` oder `ausgelassen`; `fehler`: Grund oder `null` |

**Antworten** stehen so, wie `AskUserQuestion` sie zurückgibt: das Label ohne
„ (Empfohlen)“; bei mehreren Haken alle gewählten Labels, wie das Werkzeug sie
liefert; bei „Other“ der eingegebene Text. Hat die gewählte Option
`"text_noetig": true`, steht dort `<Label>: <Text>`. Fehlt eine `id`, wurde die
Frage nicht gestellt.

## `fragen.json` — schreibt der Subagent beim Vorbereiten

Beispiele: `beispiel/lauf/cv/fragen.json`, `…/skillmatrix/fragen.json`,
`…/portfolio/fragen.json`.

```json
{
  "skill": "newmonday-cv",
  "kandidat": "Timo Muster",
  "texte": ["Markdown, das vor den Fragen gezeigt wird"],
  "luecken": [{ "was": "Profilfoto", "folge": "…", "form": "…" }],
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
  „LinkedIn-Export“, „Zertifikate“, „Screens <Projekt>“, „Logo <Firma>“.
  `folge` sagt, was im Dokument passiert, wenn es nicht kommt; `form`, in
  welcher Form es kommen soll. Nichts, was unter `ohne` steht.

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
Alles, was der Skill selbst formuliert hat, im Wortlaut

## Quellen weichen ab
- <Feld>: <Quelle> „…“ / <Quelle> „…“ → im Dokument: <Quelle>

## Hinweise
Der Rest der Übergabe des Skills

## Ohne Rückfrage entschieden
- <Stelle>: was genommen wurde und warum

## Fehlt noch
Die Schlusszeilen des Skills, wörtlich
```