# newmonday-cv

Macht aus einem fremden Lebenslauf einen Lebenslauf im New-Monday-Layout.

Zurück zu [Start](../Start.md).

## Wofür

Für Kandidatenprofile, die an Kunden gehen. Jeder Lauf liefert zwei Fassungen:
die vollständige und eine anonymisierte für die Runde, in der ein Kunde ein
Profil bewertet, bevor er den Menschen dahinter kennt.

## Eingang

- Lebenslauf als PDF
- LinkedIn-Export als PDF – immer mitgeben, er füllt Lücken bei Firmennamen,
  Rollen und Zeiträumen
- Link zum LinkedIn-Profil, daraus kommt das Profilfoto
- optional: Xing-Profil, Portfolio (Link oder PDF), Firmenlogos als SVG, ein
  Foto

## Ausgang

Vier Ergebnisse in jedem Lauf:

- PDF vollständig und PDF anonymisiert
- Figma-Frames vollständig und anonymisiert

Gefragt wird nicht, ob etwas nach Figma soll, sondern nur wohin.

## So startest du ihn

In Claude Code den Lebenslauf dazulegen und etwa „Bring den Lebenslauf ins
New-Monday-Layout“ schreiben. Der Skill fragt zuerst nach Sprache und
Figma-Ziel, nach dem Lesen nach Rolle und Startmonat bei New Monday.

## Die eine Regel

**Inhalte werden übernommen, nicht umgeschrieben.** Zwei Stellen sind
ausgenommen:

- **Das Kurzprofil**, wenn der Eingang keins mitbringt. Es wird aus den
  Stationen gebaut und immer zur Freigabe vorgelegt.
- **Die erste Station bei New Monday.** Ihr Wortlaut ist vorgegeben.

## Was die anonyme Fassung ändert

- Platzhalterbild statt Foto
- Initialen statt Name, auch im Dateinamen, im PDF-Titel und in den
  Frame-Namen
- keine Verweise auf LinkedIn, Xing und Portfolio
- Namensnennungen im Fließtext werden ersetzt

Arbeitgeber, Kunden, Logos, Bildungseinrichtungen und die monatsgenauen
Zeiträume bleiben stehen. Die Fassung schützt davor, dass jemand die Person
erkennt, nicht davor, dass jemand sie ermittelt. Wer mehr braucht, sagt es
ausdrücklich: Zeiträume nur als Jahre, Firmen generisch, Bildungseinrichtungen
generisch, Sprachen im Skillset.

## Stolpersteine

- **Prüfmeldungen der Anonymisierung lesen.** Mehrdeutige Namensteile lässt
  der Skill stehen und meldet sie. Darunter kann eine echte Namensnennung
  sein.
- **Anonym ist das PDF, nicht das Figma-File.** In der Figma-Datei liegen beide
  Fassungen nebeneinander. Wer den Figma-Link weitergibt, gibt die
  vollständige Fassung weiter.
- **Fehlt WeasyPrint,** weicht der Skill auf Chrome aus und sagt das. Dann
  Seitenumbrüche und Skillset-Spalten gegenprüfen.
- **Logos deutscher Agenturen und Mittelständler** finden die Logodatenbanken
  fast nie. SVGs gleich mitzuschicken spart die Suche.
- **Übersetzt wird nur auf ausdrückliche Ansage.**
- **Neue Logos landen in `assets/logos/`** und sollen committet werden, siehe
  [README](../../README.md).

## Was feststeht

- Erste Station ist immer New Monday, und nur sie läuft auf „Heute“.
- Das Skillset hat immer vier Gruppen: Fähigkeiten, Branchen, Tools, Sprachen.
- Bildung und Skillset stehen auf Seite 1, Kurzprofil und Stationen ab Seite 2.
- Schriften sind Inter und Rethink Sans, keine Schatten, keine Rundungen.
- Beide Fassungen werden immer zusammen übergeben.

## Weiterlesen

- [SKILL.md](../../newmonday-bewerber/skills/newmonday-cv/SKILL.md) – die vollständigen Regeln
- [INSTALL.md](../../newmonday-bewerber/skills/newmonday-cv/INSTALL.md) – Einrichtung
- [layout.md](../../newmonday-bewerber/skills/newmonday-cv/references/layout.md) – vor jeder Layoutänderung lesen
- [figma.md](../../newmonday-bewerber/skills/newmonday-cv/references/figma.md) – wie aus dem Plan Frames werden
- [figma-abgleich.md](../../newmonday-bewerber/skills/newmonday-cv/references/figma-abgleich.md) – wenn sich das Design-System in Figma ändert
