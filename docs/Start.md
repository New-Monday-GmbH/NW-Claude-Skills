# Start

Einstieg in die Bewerber-Skills von New Monday. Die Notizen hier sind für
Menschen geschrieben und kurz. Die vollständigen Regeln stehen in den
`SKILL.md`-Dateien, die für Claude geschrieben sind – jede Notiz verlinkt
dorthin, statt sie zu wiederholen.

## Die vier Skills

| Skill | Ergebnis | Wann |
|---|---|---|
| [newmonday-bewerbermappe](skills/newmonday-bewerbermappe.md) | Alle drei Dokumente in einem Lauf, PDFs plus eine Figma-Seite je Kandidat | Wenn ein Kandidat das ganze Set bekommt |
| [newmonday-cv](skills/newmonday-cv.md) | Lebenslauf, vollständig und anonymisiert, je als PDF und Figma-Frame | Wenn nur der Lebenslauf gebraucht wird |
| [newmonday-skillmatrix](skills/newmonday-skillmatrix.md) | Skill Matrix als eine lange PDF-Seite, auf Wunsch als Figma-Frame | Wenn nur die Kompetenzübersicht gebraucht wird |
| [newmonday-portfolio](skills/newmonday-portfolio.md) | Portfolio als 16:9-Folien, PDF und Figma-Frames | Wenn nur das Portfolio gebraucht wird |

## Wie sie zusammenhängen

```
newmonday-bewerbermappe   fragt, prüft, verteilt – baut selbst nichts
  ├─ 1. newmonday-cv
  ├─ 2. newmonday-skillmatrix
  └─ 3. newmonday-portfolio
```

- Die Bewerbermappe stellt jede gemeinsame Frage einmal (Sprache, Figma-Ziel,
  Material) und lässt dann die drei Skills nacheinander bauen, immer in dieser
  Reihenfolge und nie parallel.
- Jeder der drei Skills läuft auch allein und stellt dann seine Fragen selbst.
- `newmonday-cv` und `newmonday-portfolio` teilen sich eine Logobibliothek. Sie
  liegt im CV-Skill und wächst mit jedem Kandidaten – neue Logos bitte
  committen, siehe [README](../README.md).

## Was für alle gilt

- **Übernehmen, nicht umschreiben.** Erlaubt ist nur das Glätten von
  Rechtschreibung und Grammatik. Die wenigen Ausnahmen stehen je Skill in der
  Notiz und werden in der Übergabe zur Freigabe vorgelegt.
- **Fehlt etwas, wird gefragt und nicht geraten.**
- **Das PDF ist das Ergebnis, Figma die bearbeitbare Zweitschrift.** Geht in
  Figma etwas schief, gehen die PDFs trotzdem raus.
- **Ansprechpartner im Footer** ist in allen drei Dokumenten Manuel Klein, CCO.
- **Designwerte stehen je Skill einmal in `assets/tokens.json`.** PDF und
  Figma-Frame lesen beide von dort.

## Dieser Ordner ist auch ein Obsidian-Vault

Das Repo lässt sich in Obsidian über „Ordner als Vault öffnen“ öffnen. Dann
sind diese Notizen und alle `SKILL.md`- und Referenzdateien durchsuchbar und
immer auf dem Stand des Repos.

- **Keine Kandidatendaten hierher.** Das Repo enthält nur die Werkzeuge. Die
  Bewerbermappe erkennt, wenn sie im Repo gestartet wird, und fragt dann nach
  einem anderen Ablageort.
- **`.obsidian/` wird nicht versioniert.** Die Obsidian-Einstellungen bleiben
  auf dem eigenen Rechner.
- **Links als normale Markdown-Links mit relativem Pfad**, damit sie auch auf
  GitHub funktionieren.
- **Wer in Obsidian eine `SKILL.md` ändert, ändert den Skill.** Die Dateien
  sind die Originale, keine Kopien.

## Weiter

- [Ideen und offene Punkte](Ideen%20und%20offene%20Punkte.md)
- [Installation und Logobibliothek](../README.md)
- [Installation des Bundles](../newmonday-bewerber/README.md)
- Entstehung der Bewerbermappe:
  [Design](superpowers/specs/2026-09-29-newmonday-bewerbermappe-design.md) und
  [Umsetzungsplan](superpowers/plans/2026-09-29-newmonday-bewerbermappe.md)
