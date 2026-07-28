# Schweregrade & Finding-Template

## Schweregrade

Ordne jedem Finding einen von vier Graden zu. Sie steuern Farbe und Reihenfolge in den Slides.

| Grad | Label | Bedeutung |
|------|-------|-----------|
| 🔴 **Kritisch** | Blocker | Hindert Nutzer:innen an einer Kernaufgabe oder schließt Gruppen aus (z. B. Checkout unbedienbar, Formular ohne Label, Kontrast weit unter Schwelle auf zentralem Element). Sofort beheben. |
| 🟠 **Hoch** | Major | Deutliche Reibung/Frust, viele Nutzer betroffen, Workaround existiert aber (z. B. unklarer primärer CTA, inkonsistente Navigation). |
| 🟡 **Mittel** | Minor | Spürbar, aber begrenzt; einzelne Situationen oder wenige Nutzer. |
| 🔵 **Niedrig** | Politur | Kosmetik/Feinschliff, kein echtes Nutzungshindernis. |

Belege den Grad, statt ihn zu behaupten – über die Wirkung auf die Nutzungsaufgabe, nicht über persönlichen Geschmack.

## Finding-Template

Schreibe jedes Finding in `findings.md` exakt nach diesem Schema. Diese Felder werden 1:1 zu einer Slide.

```markdown
### F<NN> – <prägnanter Titel>
- **Brille / Heuristik:** <z. B. Nielsen #4 Konsistenz | WCAG 1.4.3 Kontrast | Visuell | Mobile>
- **Schweregrad:** <🔴 Kritisch | 🟠 Hoch | 🟡 Mittel | 🔵 Niedrig>
- **Beobachtung:** <Was ist konkret der Fall? Sachlich, am Screenshot nachvollziehbar. Bei Messwerten: Zahl nennen, z. B. „Kontrast 2.8:1 statt geforderter 4.5:1".>
- **Wirkung:** <Warum ist das ein Problem für echte Nutzer:innen? Welche Aufgabe wird erschwert, wer ist betroffen?>
- **Empfehlung:** <Konkreter, umsetzbarer Lösungsvorschlag. Wenn möglich mit Zielwert, z. B. „Textfarbe auf #595959 abdunkeln → 7:1".>
- **Screenshot:** findings/f<NN>.png
```

## Executive Summary

An den Anfang von `findings.md` (und auf die zweite Slide) gehört ein Executive Summary:
- 2–3 Sätze Gesamteindruck (ehrlich, aber wertschätzend – Stärken zuerst nennen).
- Die **3–5 wichtigsten Punkte** als Bulletpoints, jeweils mit Schweregrad.
- Optional eine Einordnung: Wie viele Findings pro Schweregrad / pro Brille.

## Qualitätsregeln

- **Ein Finding = ein klar abgegrenztes Problem.** Nicht mehrere Punkte in ein Finding stopfen.
- **Kein Finding ohne Beleg.** Screenshot oder Messwert aus `survey.json`. Wenn du es nicht zeigen kannst, ist es kein Finding.
- **Stärken benennen.** Ein guter Audit sagt auch, was gut funktioniert – das macht die Kritik glaubwürdiger und gibt Orientierung, was erhalten bleiben soll. Nimm 1–2 „Das funktioniert gut"-Punkte ins Summary.
- **Keine erfundenen Zahlen.** Nur gemessene Werte (Kontrast, Tap-Target-Größe, Anzahl fehlender Alt-Texte). Niemals Conversion-/Traffic-/Prozentzahlen erfinden.
- **Lösungsorientiert formulieren.** Jede Beobachtung endet in einer umsetzbaren Empfehlung.
