# newmonday-anfrage

Passt die bestehenden Unterlagen der passendsten Kandidaten auf eine konkrete
Ausschreibung an – Lebenslauf, Skill Matrix und Portfolio, als PDFs und in
einem neuen Figma-File je Anfrage.

Zurück zu [Start](../Start.md).

## Wofür

Für den Schritt nach dem Matching: Die Ausschreibung ist da, das Matching in
Claude Chat hat die Kandidaten gefunden, jetzt sollen deren Unterlagen auf die
Stelle zeigen. Gebaut wird wie in [newmonday-bewerbermappe](newmonday-bewerbermappe.md)
von den drei Dokument-Skills; neu ist, woher der Bestand kommt und wohin das
Ergebnis geht.

## Eingang

- die Ausschreibung, eingefügt in den Chat
- das Matching-Artifact aus Claude Chat ([newmonday-matching](newmonday-matching.md),
  Schritt 7) – der Skill findet das neueste selbst
- je Kandidat sein Original-Figma-File – der Skill sucht es im Figma-Ordner der
  Original-Files per Namen

Einmal pro Rechner: `~/.newmonday/anfrage.json` nach der Vorlage
`scripts/anfrage.config.beispiel.json` im Skill (Figma-Team, Ordner der
Original-Files, Projekt für Anfrage-Files, Ablageort).

## Ausgang

- `~/Desktop/Bewerberunterlagen/Ausschreibungen/<Job ID> <Stelle>/<Vorname Nachname>/` mit
  `New Monday - Vorname Nachname - CV.pdf`, `New Monday - V. N. - CV.pdf`,
  `… - Skillmatrix A4.pdf`, `… - Portfolio.pdf` (lange Skillmatrix und anonymer CV nur auf Anfrage);
  Arbeitsdateien in `_arbeit/`
- ein Figma-File „<Job ID> <Stelle>“ im Anfragen-Projekt, eine Seite je
  Kandidat
- eine Übergabe mit Abdeckungstabelle (Muss/Kann × Dokument) und einem
  Kurztext fürs Matching

## So startest du ihn

In Claude Code die Ausschreibung einfügen, etwa „Mach die Unterlagen zu dieser
Ausschreibung“. Der Skill zeigt das gefundene Matching und die Top 3 zum
Abhaken und fragt die Sprache.

## Die Regeln

- **Nichts erfinden** – keine neuen Projekte, Kunden, Zahlen, Zertifikate.
- **Nichts entfernen** – ergänzen und umsortieren. Austauschen nur
  Skill-Matrix-Schwerpunkte und Hero, Portfolio-Kenntnisse auf Seite 2, das
  Kurzprofil; Kürzungen fürs Layout nur mit Freigabe. `vergleich.py` prüft es.
- **Erwartbares ergänzen** – Methoden, die bei Rolle und Seniorität sehr
  wahrscheinlich sind, ergänzt der Skill selbst (auch an passenden Projekten,
  als Zusatz); Technologien, Tools, Normen, Zertifikate und Domänen fragt er
  dich.
- **Verwandte Domäne nach vorn** – mit der Tätigkeit, die belegt ist.
- **Original-Files werden nur gelesen.** Aufgeräumt wird in Figma von Hand.

## Stolpersteine

- Figma kann über den MCP keine Ordner listen; der Skill liest den Ordner im
  App-Browser. Dort muss man einmal bei Figma angemeldet sein.
- Handpflege in Figma (getauschte Bilder, Collagen, Farben) wird mitgelesen und
  übernommen – Sonderfälle stehen danach in `_arbeit/eingang/bestand/bestand.md`.
- Findet der Skill das Matching-Artifact nicht, es in Claude Chat einmal
  veröffentlichen (bleibt privat).
