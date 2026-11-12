# Die kopierten Frames anpassen statt neu bauen

Für newmonday-anfrage gilt: Im Anfrage-File liegen Kopien der
Bestands-Frames (SKILL.md, Phase 3, Punkt 2). Der Bauen-Subagent ändert die
JSON, rendert die PDFs mit den Skripten des Skills und passt danach **diese
Kopien** an. Den Figma-Bau-Schritt des Skills (`figma_plan.py`, Bau-Skripte,
`figma_assets.py`) lässt er aus.

Vorab: Skill `figma:figma-use` laden, `create_session` mit dem fileKey des
Anfrage-Files. Antworten klein halten, Nicht-ASCII in Rückgaben als
`\uXXXX` maskieren. Ab etwa 20 KB oder bei Umlauten bricht der Figma-MCP mit
„Failed to parse SSE message“ ab. Jede Änderung geht nur auf der Seite aus
`figma.link`, nichts wird gelöscht und nichts gelöst.

## 1. Was geändert werden muss

Geändert wird nur, was sich zwischen Bestand und neuer JSON unterscheidet.
Dafür `eingang/bestand/<datei>.json` gegen `<skill>/<datei>.json` diffen,
Wert für Wert. Wo jeder Wert in Figma sitzt, steht in `eingang/bestand/kopie.md`
(Bestand-ID → Kopie-ID) und in den Zeilen von `scripts/figma_lesen.js`. Das
Skript liest jetzt die Kopie statt des Originals. Die Property-Namen je
Komponente stehen in `references/figma.md` von newmonday-cv,
newmonday-skillmatrix und newmonday-portfolio.

## 2. Wie geändert wird

| Änderung | So |
|---|---|
| Text in einer Instanz | `instance.setProperties({"Text#…": neu})`, Property-Name aus `componentProperties`. Steht dort ein Override von Hand (`T`-Zeile in figma_lesen), gilt der Textknoten. |
| Text in einem rohen Frame | Textknoten: erst die Schriften laden (`getStyledTextSegments(['fontName'])`), dann `characters`. Bei angehängten Sätzen nur einfügen, nicht ersetzen. |
| Zusätzlicher Eintrag, Stichpunkt, Tool | Ausgeblendeten Platz der Komponente einblenden (`Eintrag n=true`, `… anzeigen=true`), dann den Text setzen. |
| Bewertung (Skill Matrix) | Variante `Bewertung` der Instanz umstellen, in der langen Fassung und in A4. |
| Reihenfolge (Projekte, Kategorien, Folien) | Kinder im Auto-Layout bzw. Sammelrahmen mit `insertChild` umstellen. Danach Seitenzahl-Properties der Folien lückenlos neu setzen. |
| Neue Folie (z. B. Schwerpunkt-Folie) | Eine vorhandene Folie derselben Komponente in diesem File duplizieren (`clone()`) bzw. die Master-Komponente per Key importieren und instanziieren, an die richtige Stelle setzen, Texte setzen. |
| Neues Bild (selten) | `upload_assets` und Bildfüllung des Platzes setzen. Fertige Bildflächen aus dem Bestand bleiben unangetastet. |

## 3. Wann doch neu gebaut wird

Nur in diesen Fällen, und dann nur das betroffene Dokument:

- **Die Seitenzahl ändert sich.** Das neu gerenderte PDF hat mehr oder
  weniger Seiten als der Bestand, und Kürzen ist nicht freigegeben. Vorher
  versuchen, die Ergänzung als angehängten Satz zu fassen statt als neue Zeile.
- **Die Komponente ist zu klein.** Ein Inhalt hat mehr Einträge, als die
  Komponente Plätze hat, zum Beispiel mehr als 12 Fähigkeiten im CV-Skillset
  oder mehr als 6 Stichpunkte in einer Lösungsfolie. Auch hier zuerst
  Zusammenfassen oder Anhängen prüfen.
- **Die Kopie fehlt oder ist unvollständig**, und der Nutzer hat in Phase 3
  „Ohne Figma weiter“ nicht gewählt.

Neu gebaut wird über den Figma-Weg des Skills. Das neue Dokument kommt rechts
neben die Kopie, die Kopie bleibt stehen. `uebergabe.md` nennt unter
„Hinweise“, welches Dokument neu gebaut wurde und warum.

## 4. Prüfen

- Kopie mit `scripts/figma_lesen.js` neu lesen und jeden geänderten Wert
  gegen die neue JSON halten: Text, Sichtbarkeit, Bewertung, Reihenfolge.
- Einen Screenshot jeder geänderten Seite bzw. Folie ansehen: nichts
  abgeschnitten, kein Überlauf, gleicher Umbruch wie im PDF.
- In `uebergabe.md` unter „Dateien“ die geänderten Node-IDs angeben, mit dem
  Vermerk „angepasst, nicht neu gebaut“.
