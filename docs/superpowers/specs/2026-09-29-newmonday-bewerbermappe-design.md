# newmonday-bewerbermappe — Design

Stand: 29.09.2026 · Basis: `main` @ `8a16765` · Branch: `newmonday-bewerbermappe`

## Ziel

Ein Skill, der die drei Dokument-Skills des Bundles `newmonday-bewerber` in einem
Lauf nacheinander ausführt: `newmonday-cv`, `newmonday-skillmatrix`,
`newmonday-portfolio`. Der Nutzer gibt die Unterlagen (Lebenslauf, LinkedIn-Export
und -Link, Portfolio als Link oder PDF) und einen Figma-Link einmal ab,
beantwortet jede Frage, die mehrere Skills stellen, genau einmal, und bekommt
alle Entscheidungsfragen in einer Sitzung, bevor gebaut wird. Fehlt etwas, sagt
der Skill das vor dem Bauen und fragt, ob es nachgeliefert werden kann.

## Getroffene Entscheidungen

| Frage | Entscheidung |
|---|---|
| Skill-Stand | `main` auf GitHub (alle drei Skills per Symlink aus diesem Repo) |
| Zweite Fragerunde der Skills | **gebündelt vorab**: erst alles lesen, dann alle Entscheidungen in einem Block, danach Bau ohne Unterbrechung |
| Figma-Ablage | **eine Seite je Kandidat** („Vorname Nachname“), darauf CV (vollständig + anonym), Skillmatrix, Portfolio nebeneinander. Zeigt der Link auf eine Seite, kommt alles dorthin |
| Startmonat NM (CV) vs. Verfügbarkeit (Skillmatrix) | **getrennt fragen** |
| Aufbau | **Orchestrator-Skill im Hauptgespräch + Subagent je Skill und Phase** |
| Bau-Reihenfolge | CV → Skillmatrix → Portfolio, strikt nacheinander |
| Name | `newmonday-bewerbermappe` |

Die Reihenfolge: Der CV füllt die gemeinsame Logobibliothek, die das Portfolio
nutzt; das Portfolio ist am längsten und hat am ehesten fehlendes Material.
Nacheinander statt parallel, weil alle drei in dieselbe Figma-Seite und dieselbe
Logobibliothek schreiben.

## Architektur

```
Hauptgespräch                         Subagenten (general-purpose, frischer Kontext)
─────────────                         ──────────────────────────────────────────────
newmonday-bewerbermappe
  Phase 1 Eingang        (fragt)
  Phase 2 Lückencheck I  (fragt)
  Phase 3 Vorbereiten    ───────────▶ CV · vorbereiten      → fragen.json, notizen.md
                         ───────────▶ Skillmatrix · vorb.   → fragen.json, notizen.md
                         ───────────▶ Portfolio · vorb.     → fragen.json, notizen.md
  Phase 4 Entscheidungen (fragt)
  Phase 5 Bauen          ───────────▶ CV · bauen            → PDFs, Frames, uebergabe.md
                         ───────────▶ Skillmatrix · bauen   → PDF, Frame, uebergabe.md
                         ───────────▶ Portfolio · bauen     → PDF, Frames, uebergabe.md
  Phase 6 Gesamtübergabe
```

Warum so:

- **Fragen nur im Hauptgespräch.** `AskUserQuestion` ist in Subagenten gesperrt
  (Claude-Code-Doku, „Available tools for subagents“: *always removed*). Jede
  Frage an den Nutzer stellt deshalb der Orchestrator.
- **Skill-Arbeit in Subagenten.** Die drei Skills haben zusammen gut 3 000 Zeilen
  Anleitung plus Referenzen, dazu Skript- und Figma-Ausgaben. In einem einzigen
  Kontext würde mitten im Bau zusammengefasst und Skill-Regeln gingen verloren.
  Jeder Subagent lädt genau einen Skill, erledigt eine Phase und gibt eine
  Statuszeile zurück.
- **Der Orchestrator ist generisch.** Er kennt die Fragen der Skills nicht,
  sondern reicht weiter, was in `fragen.json` steht, und legt die Antworten
  unter derselben ID ab. Neue Fragen in einem Skill brauchen keine Änderung am
  Orchestrator.

## Ablauf

### Phase 1 — Eingang

Eine Nachricht:

- `AskUserQuestion` mit zwei Fragen:
  - **Sprache**: Deutsch | Englisch — gilt für alle drei Dokumente.
  - **Figma**: In ein bestehendes File – ich schicke den Link (Empfohlen) | Leg ein neues File an.
- Als Text daneben die Materialliste: Lebenslauf (PDF), LinkedIn-Export (PDF,
  *Mehr → Als PDF speichern*) plus Profil-Link, Portfolio (Link oder PDF),
  Figma-Link (`figma.com/design/…`, Bearbeitungsrechte). Optional, einmal
  erwähnt: Firmen- und Kundenlogos als SVG, Screenshots je Projekt (einzelne
  Exporte, ein Screen je Datei), Zertifikate, ein Foto in guter Auflösung, ein
  paar Sätze je Kunde, Xing-Link.

Was schon mit dem Aufruf kam (Dateien, Links, „auf Englisch“), wird nicht noch
einmal erbeten bzw. gefragt.

### Phase 2 — Lückencheck I (vor dem Lesen)

Der Orchestrator prüft selbst, ohne Subagent:

1. **Material vorhanden?** Pflicht ist nur ein Lebenslauf **oder** ein
   LinkedIn-Export – ohne beides stoppt der Lauf mit der Bitte darum. Erwartet
   (fehlt → nachfragen): Lebenslauf, LinkedIn-Export, LinkedIn-Link, Portfolio,
   Figma-Link. Optionales wird nicht angemahnt.
2. **Umgebung**: `pruefe_umgebung.py` aller drei Skills. Fehlt etwas, kommt der
   Installationsbefehl in die Nachricht.
3. **Kandidatenname**: aus der ersten Seite von Lebenslauf bzw. LinkedIn-Export
   (`pdftotext -l 1`); bleibt der Text leer (Bild-PDF), die erste Seite als Bild
   lesen. Das ist die einzige inhaltliche Lesearbeit des Orchestrators; er
   braucht den Namen für Laufordner und Figma-Seite.
4. **Figma**, in dieser Reihenfolge:
   - Werkzeug verbunden (`whoami`). Genutzt wird der Figma-Server, dessen
     `whoami` antwortet; ein zweiter, nicht angemeldeter Figma-Server wird
     ignoriert.
   - Link ist eine Design-Datei (`/design/`, nicht `/board/`, `/slides/`,
     `/make/`, `/proto/`) und lesbar (`get_metadata`).
   - **Zielseite anlegen – das ist zugleich der Schreibtest.** Skill
     `figma:figma-use` laden, dann per `use_figma`: Link mit `node-id` → dessen
     Seite nehmen; sonst Seite „Vorname Nachname“ anlegen bzw., wenn sie schon
     existiert (früherer Lauf), nehmen. Bei „neues File“ zuerst das File mit
     `create_new_file` anlegen (Skill `figma:figma-create-new-file`).
     Die Seiten-ID merkt sich der Orchestrator für `auftrag.json` (geschrieben
     am Ende von Phase 2). Leserechte allein fallen erst beim
     Schreiben auf – deshalb hier und nicht erst in Phase 5, wo niemand mehr
     gefragt wird. Bricht der Nutzer den Lauf später ab, bleibt die leere Seite
     stehen; das ist in Kauf genommen.
5. **Ablageort**: Ist das Arbeitsverzeichnis das Skill-Repo selbst oder liegt es
   darin, kommen Kandidatendaten nicht dorthin (siehe README, „Was hier NICHT
   hineingehört“). Dann kommt eine Klickfrage nach dem Ort dazu – in der
   Lückennachricht, oder allein, wenn sonst nichts fehlt:
   *Schreibtisch (Empfohlen)* | *Downloads* | Other.

Fehlt etwas: **eine** Nachricht mit jedem fehlenden Posten und seiner Folge
(„Kein LinkedIn-Export → Firmennamen und Zeiträume nur aus dem Lebenslauf“,
„Kein Portfolio → Portfolio-Dokument mit Platzhaltern statt Screens“, „Figma
nicht verbunden → nur PDFs“) plus `AskUserQuestion`:
*Ich liefere nach (Empfohlen)* | *Ohne weitermachen*. Was abgelehnt wird, steht
in `auftrag.json` unter `ohne` und wird nicht noch einmal angesprochen.

Danach legt der Orchestrator den Laufordner an, kopiert die Dateien nach
`eingang/` und schreibt `auftrag.json`.

### Phase 3 — Vorbereiten

Je Skill in Bau-Reihenfolge ein Subagent, Phase *vorbereiten* (Auftrag siehe
unten). Nach jedem eine Statuszeile an den Nutzer („CV gelesen – 4 Fragen, 1
Lücke“). Schlägt einer fehl, geht es mit dem nächsten weiter; der Fehler kommt
in Phase 4.

### Phase 4 — Entscheidungen

In dieser Reihenfolge, in einer Sitzung:

1. **Lückencheck II.** Die `luecken` aller drei `fragen.json`, zusammengeführt
   und entdoppelt (ein fehlendes Foto nennen CV und Skillmatrix beide – es
   erscheint einmal). Dazu gescheiterte Vorbereitungen mit Grund.
   `AskUserQuestion`: *Ich liefere nach* | *Ohne weitermachen*; bei
   gescheiterter Vorbereitung zusätzlich *Ohne dieses Dokument weiter* |
   *Abbrechen*.
   Wird nachgeliefert: Dateien nach `eingang/`, `auftrag.json` ergänzen, die
   Vorbereitung **der Skills, die die Lücke gemeldet haben**, neu laufen lassen,
   dann erst weiter mit Punkt 2 – neues Material kann die Fragen ändern
   (Zertifikate ändern die Matrix).
2. **Texte.** Alle `texte` in Bau-Reihenfolge, mit Skill-Überschrift – vor allem
   Hero-Beschreibung, Schwerpunkte, Matrix- und Tools-Tabelle mit Belegen.
3. **Fragen.** Je Skill ein `AskUserQuestion`-Aufruf mit dessen `fragen` (höchstens
   vier), in Bau-Reihenfolge. Skills ohne Fragen werden übersprungen.

Antworten gehen wörtlich nach `auftrag.json` → `entscheidungen.<skill>.<id>`:
das gewählte Label ohne „(Empfohlen)“, bei `multiSelect` eine Liste, bei „Other“
der eingegebene Text. Danach wird nicht mehr gefragt.

Wählt der Nutzer bei der Matrix-Freigabe „ändern“ und beschreibt die Änderung,
setzt der Bauen-Subagent sie um; die endgültige Tabelle steht in der
Gesamtübergabe. Eine zweite Freigaberunde gibt es nicht.

### Phase 5 — Bauen

Je Skill in Bau-Reihenfolge ein Subagent, Phase *bauen*. Nach jedem eine
Statuszeile. Scheitert einer, geht es mit dem nächsten weiter. Die Figma-Seite
steht seit Phase 2; die Skills setzen ihre Frames rechts neben Vorhandenes.

### Phase 6 — Gesamtübergabe

Eine Nachricht, aus den drei `uebergabe.md` zusammengesetzt:

1. Die Dateien in `ausgabe/` (Namen wie von den Render-Skripten gesetzt) und der
   Link auf die Figma-Seite.
2. **Zur Freigabe**, je Dokument: Kurzprofil (CV), Hero-Beschreibung und
   endgültige Matrix (Skillmatrix), Cover-Titel, KI- und Prozesstexte,
   Kundentexte mit Quellen, KI-generierte Gebäude (Portfolio).
3. **Abweichungen zwischen den Quellen – einmal**, nicht je Skill. Der Hinweis,
   welche Fassung ins jeweilige Dokument kam, bleibt, denn die Regeln
   unterscheiden sich (CV und Skillmatrix: Lebenslauf gewinnt; Portfolio:
   Portfolio gewinnt).
4. Was ein Subagent beim Bauen ohne Rückfrage entschieden hat (Empfohlen-Option
   genommen), mit Stelle.
5. Gescheiterte Dokumente mit Grund.
6. Zum Schluss die „fehlt noch“-Zeilen aller drei Skills **wörtlich**, wie sie
   die Skills setzen, Logos zuerst. Fehlt nichts, steht hier nichts.

Liefert der Nutzer danach etwas nach, siehe Wiederaufnahme.

## Dateien

### Laufordner

Im Arbeitsverzeichnis des Nutzers:

```
<Vorname Nachname>/
  eingang/          gelieferte Dateien, unverändert (Unterordner logos/, screens/, zertifikate/)
  auftrag.json      schreibt nur der Orchestrator
  cv/               arbeit/, cv.json, fragen.json, notizen.md, uebergabe.md
  skillmatrix/      arbeit/, skillmatrix.json, fragen.json, notizen.md, uebergabe.md
  portfolio/        arbeit/, portfolio.json, fragen.json, notizen.md, uebergabe.md
  ausgabe/          alle PDFs
```

Je Skill ein eigener Ordner, weil alle drei in `arbeit/fotos/`,
`arbeit/text.txt` und `arbeit/figma_plan.json` schreiben.

### `auftrag.json`

```json
{
  "version": 1,
  "laufordner": "/abs/pfad/Timo Muster",
  "kandidat": "Timo Muster",
  "sprache": "de",
  "reihenfolge": ["newmonday-cv", "newmonday-skillmatrix", "newmonday-portfolio"],
  "figma": {
    "aktiv": true,
    "link": "https://www.figma.com/design/<fileKey>/…",
    "file_key": "<fileKey>",
    "seite_id": "12:34",
    "neues_file": false
  },
  "material": {
    "lebenslauf": "eingang/lebenslauf.pdf",
    "linkedin_export": "eingang/linkedin.pdf",
    "linkedin_url": "https://www.linkedin.com/in/…",
    "xing_url": null,
    "portfolio_url": "https://…",
    "portfolio_pdf": null,
    "foto": null,
    "logos": "eingang/logos/",
    "screens": "eingang/screens/",
    "zertifikate": "eingang/zertifikate/",
    "kundentexte": null
  },
  "ohne": ["linkedin_export"],
  "entscheidungen": {
    "newmonday-cv": { "nm_rolle": "User Experience Design Specialist", "nm_start": "Oktober 2026" }
  },
  "status": {
    "newmonday-cv":          { "vorbereiten": "fertig", "bauen": "offen", "fehler": null },
    "newmonday-skillmatrix": { "vorbereiten": "offen",  "bauen": "offen", "fehler": null },
    "newmonday-portfolio":   { "vorbereiten": "offen",  "bauen": "offen", "fehler": null }
  }
}
```

Pfade relativ zum Laufordner. `status` je Phase: `offen` | `fertig` | `fehler` |
`ausgelassen` (Nutzer: „ohne dieses Dokument“). Den Status setzt der
Orchestrator nach der Rückmeldung des Subagenten.

### `fragen.json` (vom Vorbereiten-Subagenten)

```json
{
  "skill": "newmonday-cv",
  "kandidat": "Timo Muster",
  "texte": ["Markdown, das vor den Fragen gezeigt wird"],
  "luecken": [
    { "was": "Profilfoto", "folge": "Fotospalte bleibt leer", "form": "Bilddatei, Porträt, mind. 800 px hoch" }
  ],
  "fragen": [
    { "id": "nm_rolle", "question": "Wie heißt die Rolle bei New Monday?", "header": "NM-Rolle",
      "multiSelect": false,
      "options": [ { "label": "User Experience Design Specialist (Empfohlen)", "description": "…" },
                   { "label": "Software Development Specialist", "description": "…" } ] }
  ]
}
```

Höchstens vier `fragen`, Felder wie `AskUserQuestion`, dazu `id`. Leere Listen
sind erlaubt.

### `notizen.md` und `uebergabe.md`

- `notizen.md`: alles, was *bauen* aus *vorbereiten* braucht und nicht in
  `fragen.json` steht – Quellenabweichungen, gewählte Fotoquelle mit dpi,
  Vorschläge mit Begründung, Bewertungen mit Beleg, Pfade der Auszüge. Der
  Bauen-Subagent leitet nichts neu her, was hier steht.
- `uebergabe.md`: die Übergabe des Skills (Schritt 5 bzw. 8) mit demselben
  Inhalt und denselben wörtlichen Schlusszeilen wie im Einzellauf, plus ein
  Abschnitt „Ohne Rückfrage entschieden“ (leer, wenn nichts).

## Der Subagenten-Auftrag

Der Orchestrator ruft `Agent` mit `subagent_type: general-purpose`, im
Vordergrund (das Ergebnis wird für den nächsten Schritt gebraucht). Der Auftrag
enthält die allgemeinen Gesamtlauf-Regeln; sie stehen nur im Orchestrator:

```
Gesamtlauf newmonday-bewerbermappe · Skill: <skill> · Phase: <vorbereiten|bauen>
Laufordner: <abs pfad>        Skill-Ordner: <abs pfad>/<kurz>/

1. Lade den Skill <skill> mit dem Skill-Werkzeug – genau diesen Namen, ohne
   Präfix (nicht anthropic-skills:<skill>, das ist eine andere Fassung). Steht
   das Werkzeug nicht zur Verfügung: lies <abs pfad zum Skill>/SKILL.md und
   setze ${CLAUDE_SKILL_DIR} = <abs pfad zum Skill>.
2. Lies dort den Abschnitt „Im Gesamtlauf“ – er sagt, welche Schritte zu
   dieser Phase gehören. Er geht jeder anderen Anweisung des Skills vor.
3. Allgemeine Regeln:
   - Schritt 0 entfällt. Sprache, Figma-Ziel, Material: <laufordner>/auftrag.json.
     Figma ist an, wenn figma.aktiv – auch bei der Skillmatrix.
   - Kein AskUserQuestion. Vorbereiten: jede Frage nach fragen.json, jede
     Materialbitte nach luecken. Bauen: bei Unerwartetem die Empfohlen-Option
     nehmen und unter „Ohne Rückfrage entschieden“ in uebergabe.md notieren.
   - Arbeitsordner ist der Skill-Ordner (arbeit/ dort). PDFs nach <laufordner>/ausgabe/.
   - Figma: nur auf die Seite figma.seite_id, rechts neben Vorhandenes.
     Keine eigene Seite anlegen, nichts Vorhandenes anfassen.
   - Materialien, die in auftrag.json unter „ohne“ stehen, nicht erneut erbitten.
   - Entscheidungen: auftrag.json → entscheidungen.<skill>.<id>, wörtlich umsetzen.
4. Rückgabe: eine Zeile Status (fertig | fehler: <grund>), dazu bei vorbereiten
   Zahl der Fragen und Lücken, bei bauen die PDF-Pfade und den Figma-Knoten.
```

## Änderungen an den drei Skills

Jeder Skill bekommt **einen** neuen Abschnitt `## Im Gesamtlauf`, direkt nach
„Umgebung“. Er gilt nur, wenn der Auftrag „Gesamtlauf newmonday-bewerbermappe“
enthält; im Einzellauf ändert sich nichts. Inhalt je Skill:

| Skill | *vorbereiten* | Fragen-IDs | *bauen* |
|---|---|---|---|
| `newmonday-cv` | Schritte 1–1c (Auslesen, Foto, Zusammenführen, Portfolio); Schritt 1d als `fragen` | `nm_rolle`, `nm_start`, `fachfremd`*, `weiterbildung`* | Schritte 2–5, beide Fassungen, Frames auf die vorgegebene Seite |
| `newmonday-skillmatrix` | Schritte 1–2d; aus 2e Hero-Beschreibung, Schwerpunkte, Matrix- und Tools-Tabelle als `texte` | `verfuegbar_ab` (bisher Schritt 0), `freigabe`, `tools`* | Schritte 3–5; Figma-Weg A/B wie im Skill |
| `newmonday-portfolio` | Schritte 1–2; Auflösungsbewertung aus `bilder.txt` und fehlende Screens je Projekt als `luecken`; Figma-Datei als Quelle wie in Schritt 1 | `projekte`, `nda`*, `statement`*, `ki_tools`* | Schritte 4–8, inkl. Logos, Kundentext-Recherche, Firmenzentralen, Markenfarben |

\* nur, wenn es etwas zu entscheiden gibt – dieselben Bedingungen wie im Einzellauf.

Dazu je Skill:

- was in `notizen.md` gehört (skillspezifisch, z. B. Matrix: Bewertung + Beleg je
  Attribut; Portfolio: Bildzuordnung je Projekt);
- dass die Übergabe nach `uebergabe.md` geht;
- beim CV: Kurzprofil wird beim Bauen erzeugt und steht in `uebergabe.md` zur
  Freigabe, wie im Einzellauf;
- bei der Skillmatrix: `freigabe` = „ändern“ + Text → Änderungen umsetzen, die
  endgültige Tabelle in `uebergabe.md`.

Nicht geändert werden: die Skill-Beschreibungen (die des CV steht bei 1 009 von
1 024 Zeichen), Layouts, Templates, Render- und Figma-Skripte.

## Neuer Skill `newmonday-bewerbermappe`

```
newmonday-bewerber/skills/newmonday-bewerbermappe/
  SKILL.md                       Orchestrator: Phasen 1–6, Subagenten-Auftrag, Wiederaufnahme
  references/formate.md          auftrag.json, fragen.json, notizen.md, uebergabe.md – Felder und Beispiele
```

Frontmatter-`description` (≤ 1 024 Zeichen): auslösen, wenn alle drei Dokumente,
„die ganze Mappe“, „das komplette Set“, „CV, Portfolio und Skillmatrix“,
„Bewerbermappe“ oder „alle Unterlagen für <Name>“ verlangt werden. Für ein
einzelnes Dokument bleiben die Einzelskills zuständig.

Kein Skript im ersten Wurf. Laufordner, Kopieren und JSON schreibt der
Orchestrator mit den Standardwerkzeugen; ein Hilfsskript kommt erst, wenn der
Test zeigt, dass es gebraucht wird.

Außerdem: Eintrag in `README.md` (Tabelle + Symlink-Zeile) und
`newmonday-bewerber/README.md`, Plugin-Version 1.2.0 → 1.3.0 in `plugin.json`
und `marketplace.json`.

## Fehlerfälle

| Fall | Verhalten |
|---|---|
| Weder Lebenslauf noch LinkedIn-Export | Stopp in Phase 2 mit der Bitte darum |
| Umgebung unvollständig | Befehl in Phase 2; *ich richte es ein* \| *ohne weitermachen* (dann bricht der betroffene Skill beim Rendern ab und wird als Fehler gemeldet) |
| Figma nicht verbunden / nur Leserecht / falscher Dateityp | in Phase 2 melden (Schreibtest = Seite anlegen); *ich richte es ein* \| *ohne Figma weiter* → `figma.aktiv = false` |
| Vorbereiten scheitert | Phase 4 nennt Grund; *ohne dieses Dokument weiter* \| *abbrechen* |
| Bauen scheitert | weiter mit dem nächsten Skill; Grund in der Gesamtübergabe |
| Figma scheitert beim Bauen | PDF geht trotzdem raus (Regel aller drei Skills), Grund in der Übergabe |

## Wiederaufnahme

`auftrag.json` ist der Stand. „Mach den Lauf *Timo Muster* weiter“ (auch in einer
neuen Sitzung) → Orchestrator liest `status` und setzt an der ersten offenen
Stelle an. Offene Entscheidungen werden dabei gefragt, beantwortete nicht.

Nachlieferung nach Abschluss (Logos, Screens, Foto): Dateien nach `eingang/`,
`auftrag.json` ergänzen, bei den betroffenen Skills `bauen` auf `offen` setzen
und nur diese neu bauen – ohne Rückfragen. Betroffen ist, wessen `uebergabe.md`
das Material in den „fehlt noch“-Zeilen nennt.

## Nicht im Umfang

- Paralleles Vorbereiten oder Bauen (Figma-Seite und Logobibliothek sind geteilt;
  LinkedIn antwortet bei schnellen Folgeabrufen mit HTTP 999)
- Unterschiedliche Sprachen je Dokument
- Eigene Subagent-Typen unter `.claude/agents/`
- Eine zweite Freigaberunde für die Matrix
- Änderungen an Layouts, Templates oder Render-Skripten der Einzelskills

## Test

0. **Machbarkeit – erledigt am 29.09.2026.** Ein `general-purpose`-Subagent
   fand per ToolSearch die Figma-MCP-Werkzeuge (`whoami`, `use_figma`,
   `get_metadata`, `create_new_file`), `whoami` lief durch; er hatte den
   `Skill`-Befehl, sah `newmonday-cv`, `newmonday-portfolio`,
   `newmonday-skillmatrix` und `figma:figma-use`, und kein `AskUserQuestion`.
   Nebenbefunde, die ins Design eingeflossen sind: `newmonday-cv` gibt es
   zusätzlich als `anthropic-skills:newmonday-cv` (→ Name ohne Präfix im
   Auftrag); ein zweiter Figma-Server ist nicht angemeldet (→ der Server nehmen,
   dessen `whoami` antwortet); das Konto hat in einem Team nur einen View-Seat
   (→ Schreibtest in Phase 2).
1. **Einzellauf unverändert**: `selbsttest.py` von CV und Portfolio sowie das
   Beispiel-Render der Skillmatrix (`beispiel/skillmatrix.json`) laufen vor und
   nach der Änderung gleich.
2. **Gesamtlauf** mit einem echten Kandidaten-Set (Lebenslauf, LinkedIn-Export,
   Portfolio) in eine Test-Figma-Datei. Prüfen: Sprache und Figma genau einmal
   gefragt; kein Subagent fragt; drei gültige `fragen.json`; alle PDFs in
   `ausgabe/`; alle Frames auf der Seite „Vorname Nachname“ nebeneinander, nichts
   überlappt; Gesamtübergabe nennt jede Abweichung einmal.
3. **Lückencheck**: derselbe Lauf ohne LinkedIn-Export löst die Nachfrage mit
   Folge aus; „ohne weitermachen“ läuft durch und fragt nicht erneut.
4. **Wiederaufnahme**: Lauf nach Phase 3 abbrechen, in neuer Sitzung
   fortsetzen – es wird nicht neu vorbereitet.

## Offen

- Kandidaten-Set und Test-Figma-Datei für Test 2–4 (vom Nutzer).

## Nachträge aus der Planung (29.09.2026)

Sie gehen den Abschnitten oben vor.

- **Zwei kleine Skripte statt keinem.** `scripts/pruefe_lauf.py` prüft
  `auftrag.json`, jede `fragen.json` und jede `uebergabe.md` – der Orchestrator
  braucht das zur Laufzeit, weil eine fehlerhafte `fragen.json` den
  `AskUserQuestion`-Aufruf scheitern ließe. `scripts/testmaterial.sh` rendert
  den Beispiel-Lebenslauf aus `newmonday-cv` als Test-Eingang ohne echte
  Kandidatendaten. Dazu `scripts/selbsttest.py` und ein erfundener Beispiel-Lauf
  in `beispiel/lauf/`.
- **Figma-Ziel als Link.** Der Orchestrator schreibt nach `figma.link` einen Link
  mit der `node-id` der Kandidatenseite. Alle drei Skills legen ihre Frames schon
  heute auf die Seite, auf die ein Link mit `node-id` zeigt, rechts neben das
  Vorhandene – an ihrer Figma-Logik ändert sich dadurch nichts. `figma.seite_id`
  bleibt als Kontrollwert und muss zur `node-id` passen.
- **`uebergabe.md` hat sechs feste Abschnitte**: Dateien, Zur Freigabe, Quellen
  weichen ab, Hinweise, Ohne Rückfrage entschieden, Fehlt noch. Der Orchestrator
  setzt die Gesamtübergabe Abschnitt für Abschnitt daraus zusammen.
- **Antworten wörtlich.** `entscheidungen.<skill>.<id>` hält die Antwort so, wie
  `AskUserQuestion` sie liefert (bei mehreren Haken keine Liste). Eine Option mit
  `"text_noetig": true` lässt den Orchestrator im Fließtext nach dem Text fragen;
  gespeichert wird `<Label>: <Text>`.
- **Einfügestelle** der Abschnitte „Im Gesamtlauf”: direkt vor
  `## Gefragt wird mit Klickboxen, nicht im Fließtext` – das ist in allen drei
  Skills der Abschnitt nach „Umgebung”.
