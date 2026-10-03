# newmonday-bewerbermappe

Baut in einem Lauf alle drei Dokumente eines Kandidaten: Lebenslauf
(vollständig und anonym), Skill Matrix und Portfolio – als PDFs und als Frames
auf einer gemeinsamen Figma-Seite.

Zurück zu [Start](../Start.md).

## Wofür

Für den Normalfall, dass ein Kandidat das ganze Set bekommt. Der Skill baut
selbst nichts. Er sammelt ein, prüft, fragt und verteilt; gebaut wird von
[newmonday-cv](newmonday-cv.md), [newmonday-skillmatrix](newmonday-skillmatrix.md)
und [newmonday-portfolio](newmonday-portfolio.md), jeder in einem eigenen
Subagenten.

## Eingang

- Lebenslauf als PDF
- LinkedIn-Export als PDF und der Link zum Profil
- Portfolio als Link oder PDF
- Link zum Figma-File, falls ein bestehendes genutzt werden soll

Ohne Lebenslauf oder LinkedIn-Export beginnt kein Lauf, eins von beiden muss
da sein. Optional und zeitsparend: Logos als SVG, Screenshots je Projekt,
Zertifikate, ein Foto in guter Auflösung, ein paar Sätze zu jedem Kunden.

## Ausgang

Ein Laufordner mit dem Namen des Kandidaten:

- `ausgabe/` mit allen PDFs
- `eingang/` mit einer Kopie des gelieferten Materials
- `auftrag.json` mit Stand und Antworten des Laufs
- eine Figma-Seite „Vorname Nachname“ mit allen Frames

## So startest du ihn

In Claude Code etwa „Mach die Bewerbermappe für <Name>“ oder „alle Unterlagen
für <Name>“ und die Unterlagen dazulegen. Was schon im Chat liegt, wird nicht
noch einmal erbeten.

## Ablauf in sechs Phasen

1. **Eingang** – Sprache, Figma-Ziel und Material, in einer Nachricht.
2. **Lückencheck** – Material zuordnen, Umgebung und Figma-Zugriff prüfen,
   Laufordner anlegen.
3. **Vorbereiten** – jeder der drei Skills liest das Material und sammelt
   seine Fragen.
4. **Entscheidungen** – alle Fragen, Lücken und Widersprüche in einer Sitzung.
5. **Bauen** – Lebenslauf, dann Skill Matrix, dann Portfolio, ohne Rückfrage.
6. **Gesamtübergabe** – Dateien, Figma-Link und alles, was freizugeben ist.

## Die eine Regel

**Gefragt wird nur hier, gebaut wird nur dort.** Die Subagenten können keine
Fragen stellen, also holt die Bewerbermappe jede Antwort vorher ein. Nach
Phase 4 darfst du weggehen.

## Stolpersteine

- **Nicht im Skill-Repo ablegen.** Wird der Lauf in diesem Repo gestartet,
  fragt der Skill nach einem anderen Ort für den Laufordner (Schreibtisch oder
  Downloads). Kandidatendaten gehören nie ins Repo.
- **Die drei Skills müssen daneben liegen.** Bei der Installation per Symlink
  aus dem Repo ist das so.
- **Widersprechen sich die Unterlagen,** wählst du einmal die aktuellere
  Quelle. Sie gilt dann für alle drei Dokumente.
- **Die Übergabe ist lang und will gelesen werden.** Unter „Zur Freigabe“
  steht alles, was ein Skill selbst formuliert hat, und die Prüfmeldungen der
  Anonymisierung – dort steht womöglich noch der Name im anonymen PDF.
- **Ohne verbundenes Figma** entstehen nur die PDFs.
- **Ein neuer Lauf legt seine Frames neben die alten.** Die alten bleiben
  stehen, bis jemand sie löscht.

## Später weitermachen

- **Wiederaufnahme:** „Mach den Lauf <Name> weiter“ setzt an der ersten
  offenen Stelle an, auch in einer neuen Sitzung.
- **Nachlieferung:** Logos, Screens oder ein Foto in den Chat geben. Neu gebaut
  werden nur die betroffenen Dokumente.
- **Änderungswunsch:** etwa „Kurzprofil kürzer“ – das betroffene Dokument wird
  neu gebaut.

## Weiterlesen

- [SKILL.md](../../newmonday-bewerber/skills/newmonday-bewerbermappe/SKILL.md) – die vollständigen Regeln
- [formate.md](../../newmonday-bewerber/skills/newmonday-bewerbermappe/references/formate.md) – Aufbau von `auftrag.json`, `fragen.json` und `uebergabe.md`
- [Beispiel einer Übergabe](../../newmonday-bewerber/skills/newmonday-bewerbermappe/beispiel/lauf/cv/uebergabe.md)
