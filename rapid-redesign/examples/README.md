# Good / Bad Beispiele

Dieser Ordner kalibriert den Audit. Vor dem Bewerten (Schritt 3 in `SKILL.md`) werden die Beispiele hier gelesen, um zwei Fragen zu beantworten:

1. **Was ist „gut genug"?** – Woran erkennt man gute Umsetzung, damit nicht jede Kleinigkeit zum Finding wird (Overtriggering vermeiden).
2. **Wie sieht ein starkes Finding aus?** – Tonfall, Detailtiefe, Formulierung der Empfehlung.

> Dieser Ordner wird vom Team **nach und nach befüllt**. Ist er leer, halte dich strikt an das Template in `references/finding-workflow.md`. Je mehr echte Beispiele hier liegen, desto besser trifft der Audit euren Qualitätsanspruch.

## Struktur

```
examples/
├── good/   → Positivbeispiele: so soll es sein / so schreibt man ein gutes Finding
└── bad/    → Negativbeispiele: typische Probleme + wie man sie benennt
```

## Konvention pro Beispiel

Lege je Beispiel einen Unterordner an (`good/<kurz-slug>/` bzw. `bad/<kurz-slug>/`) mit:

- **`screenshot.png`** – das Bild (Ausschnitt der betroffenen Stelle).
- **`beispiel.md`** – kurze Einordnung. Bei `bad/` im Finding-Format aus `references/finding-workflow.md` (Brille, Schweregrad, Beobachtung, Wirkung, Empfehlung), damit es direkt als Muster dient. Bei `good/` ein bis zwei Sätze, *warum* es gut ist und welche Brille es erfüllt.

### Beispiel-Skelett `bad/kontrast-cta/beispiel.md`
```markdown
### Beispiel – CTA mit zu geringem Kontrast
- **Brille / Heuristik:** WCAG 1.4.3 Kontrast
- **Schweregrad:** 🔴 Kritisch
- **Beobachtung:** Primärer Button „Jetzt kaufen" hat Kontrast 2.4:1 (weiß auf Hellgrau).
- **Wirkung:** Für sehbeeinträchtigte Nutzer:innen kaum erkennbar – die Hauptaktion geht verloren.
- **Empfehlung:** Button-Fläche auf Markenblau (#1B4DB1) → Kontrast 6.9:1.
- **Screenshot:** screenshot.png
```

Tipp: Reale, anonymisierte Findings aus abgeschlossenen Projekten sind die wertvollsten Beispiele.
