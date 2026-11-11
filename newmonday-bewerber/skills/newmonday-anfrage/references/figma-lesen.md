# Den Bestand aus dem Original-Figma lesen

Für newmonday-anfrage ist das **Original-Figma-File des Kandidaten die einzige
Quelle**. Gelesen wird nur: im Original-File wird nichts angelegt, verschoben
oder gelöscht, auch keine Hilfsrahmen. Ergebnis ist ein Laufordner, der so
aussieht wie nach einem fertigen Lauf von newmonday-bewerbermappe – nur dass
die JSON-Dateien aus Figma stammen.

Vorab: Skill `figma:figma-use` laden, `create_session` mit dem fileKey.
**Antworten des Figma-MCP klein und in ASCII halten** – ab etwa 20 KB oder mit
Umlauten/Emojis im Rückgabetext bricht die Verbindung ab („Failed to parse SSE
message“). `scripts/figma_lesen.js` maskiert deshalb alles außer ASCII als
`\uXXXX`; beim Übernehmen in die JSON zurückwandeln.

## 1. Die Frames finden

Ein lesender `use_figma`-Aufruf listet die Seiten und je Seite die Kinder auf
oberster Ebene (Name, Typ, ID, x, y, Breite, Höhe; Sections mit ihren Kindern).
Die New-Monday-Frames heißen:

| Dokument | Name |
|---|---|
| Lebenslauf | „CV — Vorname Nachname — Seite n“, anonym „CV — V. N. — Seite n“ |
| Skill Matrix | „Skillmatrix — …“ (lang), „Skillmatrix A4 — … — Seite n“ |
| Portfolio | „Portfolio — …“ (Sammelrahmen mit den Folien) |

Gibt es mehrere Fassungen, gilt die **allgemeine** (ohne Anfrage-Zusatz wie
Job ID oder Stellenname im Namen), davon die neueste – die am weitesten rechts
bzw. mit der höchsten ID. Frames mit Anfrage-Zusatz sind frühere Anfragen und
nie Bestand. Ist unklar, welche Fassung gilt, die Kandidaten mit Namen und
Position nennen; der Orchestrator fragt.

## 2. Auslesen

Je Frame `scripts/figma_lesen.js` mit `FRAME_ID` und `START` – erst
`START = 0`, dann so lange weiter, bis „ZEILEN a-b von n“ das Ende zeigt.
Mehrere Frames dürfen in einer Nachricht parallel gelesen werden (jeder Aufruf
setzt seine Seite selbst). Bricht ein Aufruf ab, `ANZAHL` halbieren.

Was in den Zeilen steckt:

- **`I` – Instanz mit Properties.** Fast alle Inhalte stehen hier: Texte als
  Text-Properties (`Name=…`, `Titel=…`, `Text=…`), Sichtbarkeit als
  `… anzeigen=true/false` bzw. `Eintrag n=false`, Varianten (`Fassung=…`,
  Logo- und Seitenzahlfarbe der Folien). **Ausgeblendete Einträge
  (`=false`) gehören nicht zum Bestand.**
- **`T` – Text ohne passende Property:** ein Override von Hand. Er gilt vor
  der Property.
- **`B` – Bildfüllung** mit `imageHash`. Der Hash ist der SHA-1 der
  Bilddatei – so lässt sich prüfen, ob ein lokales Bild dasselbe ist
  (`shasum`).
- **`F` – Frames/Gruppen** der oberen Ebenen: Folien, und auf Folien **freie
  Bildgruppen außerhalb der Folie-Instanz** – das ist Handpflege (eine
  fertige Collage o. Ä.) und gilt vor dem Bildplatz der Instanz.

## 3. In die JSON-Formate übertragen

Ziel sind die Formate der drei Skills (`cv.json`/`cv-anonym.json`,
`skillmatrix.json`, `portfolio.json` – beschrieben in deren SKILL.md und
`beispiel/`-Ordnern). Die Property-Namen der Bibliothek entsprechen den
Feldern weitgehend; die Zuordnung je Komponente steht in den
`references/figma.md` der drei Skills.

**Liegt ein früherer Laufordner des Kandidaten vor** (`auftrag.json` mit
`kandidat` = Name, etwa auf dem Schreibtisch), dient seine JSON als Gerüst:
Struktur und Feldnamen von dort, **jeder Wert aus Figma**. Jede Stelle, an der
Figma vom Gerüst abweicht, kommt in `bestand.md` (Handpflege) – Texte,
Bewertungen, Bilder, Reihenfolge und Zahl der Folien, Logo-/Seitenzahlfarben.

**Ohne früheren Laufordner** entsteht die JSON allein aus den Zeilen. Was sich
nicht eindeutig zuordnen lässt, steht in `bestand.md` unter „Unklar“.

## 4. Bilder

`download_assets` auf die Knoten mit Bildfüllung: Foto, Logos, Screens,
Zertifikatsbilder. Ablage unter `_arbeit/eingang/bestand/bilder/`, Dateiname
`<dokument>-<folie oder abschnitt>-<n>.<endung>`; nach dem Download per
`shasum` gegen den Hash prüfen. **Fertige Collagen und freie Bildgruppen
bleiben ein einziges Bild** – nie vom Skill neu rastern lassen. Gedrehte
Screens werden nicht exportiert (das bräuchte Klone im Original-File); dann
den Bildplatz des Gerüsts bzw. das Bild als Ganzes nehmen und es in
`bestand.md` notieren.

## 5. Ablage im Laufordner

```
_arbeit/
  eingang/bestand/cv.json, cv-anonym.json, skillmatrix.json, portfolio.json
  eingang/bestand/bilder/…
  eingang/bestand/bestand.md       was gelesen wurde, Handpflege, Unklares
  cv/cv.json, cv/cv-anonym.json    Kopien aus eingang/bestand/
  skillmatrix/skillmatrix.json
  portfolio/portfolio.json
```

`eingang/bestand/` wird danach nicht mehr angefasst – es ist die Messlatte für
`scripts/vergleich.py` („nichts entfernt“). Die Kopien in den Skill-Ordnern
sind der Ausgangspunkt für Vorbereiten und Bauen.

Rückgabe an den Orchestrator: je Dokument die gelesenen Frame-IDs, Zahl der
Einträge (Stationen, Kompetenzen, Folien), Zahl der Handpflege-Abweichungen
und alles unter „Unklar“.
