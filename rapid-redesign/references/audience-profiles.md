# Zielgruppen-Profile (wem stellen wir das Audit vor?)

Das Audit hat immer dieselbe **faktische Basis** (alle Findings, alle Messwerte), aber **Schwerpunkt, Reihenfolge, Sprache und Detailtiefe** richten sich nach der Person, der wir es vorstellen. Die Zielgruppe wird zu Beginn erfragt (SKILL.md Schritt 2). Ist keine genannt, Default **Entscheider:in / gemischt** verwenden und das im Hero vermerken.

**Nie Findings weglassen oder Fakten verbiegen.** Zielgruppen-Anpassung heißt: gewichten, einordnen, übersetzen – nicht zensieren. Ein kritisches WCAG-Finding bleibt kritisch, auch bei Marketing – es wird nur anders gerahmt (z. B. „rechtliches Risiko + verlorene Nutzer:innen" statt „Erfolgskriterium 1.4.3").

Die Zielgruppe wird **nicht** aufs Cover geschrieben. Sie zeigt sich in **Persona, Strategie-Divider-Headline und Executive Summary** und in der Priorisierung der Inhalte.

## ⚠️ Übersetzungspflicht — die wichtigste Regel dieser Datei

**Auf den Präsentations-Folien steht die WIRKUNG, nicht die UMSETZUNG.** Technische Anweisungen gehören **ausschließlich** in die aufklappbaren Detail-Findings unter „Was wir geprüft haben" — dort dürfen und sollen sie präzise sein. Auf Executive Summary, Erkenntnis-Folien, „Was gut funktioniert", Roadmap und Next Steps haben sie nichts verloren.

**Ausnahme: Zielgruppe Tech/Engineering.** Nur dort ist das Umsetzungs-Vokabular auf den Folien richtig.

### Verbotene Vokabeln auf Folien (außer bei Tech)
`hreflang` · `canonical` · `lang="de"` · `for`/`id` · `aria-label` · `alt`-Attribut · H1/H2 · 301/403/CORS · `<code>`-Auszeichnung · Selektoren · Dateipfade und URLs mit Slash (`/feature`) · nackte Kontrast-Ratios (`4.5:1`) · px-Werte (`44px`) · Token-Namen · Finding-IDs (`F06`) · Werkzeugnamen (Playwright, Chromium)

### Übersetzungstabelle (dasselbe Finding, vier Publika)

| Befund (technisch) | Marketing | Geschäftsführung | Design |
|---|---|---|---|
| `hreflang`/`canonical`/`lang` fehlen | „Google weiß nicht, welche Seite für wen gedacht ist — Suchtreffer fallen auf die falsche Version" | „Sichtbarkeit verschenkt: Anfragen landen bei Wettbewerbern" | „Sprach- und Seitenlogik ist nicht sauber modelliert" |
| Formular-Labels nicht verknüpft | „Wer das Formular per Sprachsteuerung oder Screenreader nutzt, kommt nicht durch — Anfragen gehen verloren" | „Anfragen brechen ab; zusätzlich Haftungsrisiko (BFSG)" | „Beschriftung und Feld sind nicht als Paar aufgebaut" |
| Kontrast < 4.5:1 | „Das stärkste Verkaufsargument ist zu blass, um zu überzeugen" | „Rechtliches Risiko seit BFSG + verlorene Interessenten" | „Sekundärtext-Stufe im Design-System ist zu hell" |
| Trefferflächen < 44px | „Auf dem Handy klickt man daneben — genau dort, wo gekauft wird" | „Mobile Abschlüsse gehen verloren" | „Button-Komponente hat zu wenig Klickfläche" |
| Zwei identische URLs | „Zwei Seiten kämpfen um dieselbe Google-Position und schwächen sich gegenseitig" | „Wir ranken unter Wert" | „Zwei Einstiege für denselben Inhalt — die Architektur ist doppelt" |

### Messwerte: Größenordnung auf die Folie, Präzision ins Accordion
„Alle Zahlen exakt erhalten" gilt für **Mengen** (109 Textstellen, 21 von 28 Seiten, 5 von 28) — die bleiben wörtlich stehen, sie sind das Beweismaterial. Es gilt **nicht** für **Mess-Einheiten aus dem Prüfwerkzeug** (Kontrast-Ratios, px-Größen, Ladezeiten in ms). Die stehen präzise im Detail-Accordion; auf der Folie steht die **Größenordnung in Alltagssprache**:

- ❌ „…bei 2.57:1 statt nötigen 4.5:1"  →  ✅ „…erreicht nur gut die Hälfte des nötigen Kontrasts"
- ❌ „Trefferflächen unter 44px"  →  ✅ „Buttons kleiner als eine Fingerkuppe"

Ausnahmen: **Tech** (volle Präzision) und **Design** (darf mit dem Zielwert arbeiten, weil das Team ihn setzt).

### Selbst-Check vor dem Bauen
Lies jeden Punkt auf Summary, Erkenntnissen, Roadmap und Next Steps und frage:
1. **Versteht das jemand ohne Technik-Hintergrund?** Wenn nein → übersetzen.
2. **Beantwortet der Satz die Leitfrage dieses Publikums** (siehe unten)? Wenn nein → umschreiben.
3. **Steht da eine Anweisung an Entwickler statt einer Wirkung?** Wenn ja → Wirkung nach vorn, Anweisung ins Accordion.

Bei **Marketing** heißt „Wirkung" konkret: Was erlebt, glaubt, übersieht oder fürchtet der Besucher — und an welcher Stelle des Funnels kostet das Abschlüsse? Emotion und Motiv der Zielgruppe sind hier legitime, sogar erwünschte Argumente.

## Strategisch zuerst, technisch aufklappbar (wichtig)
Der **Kern der Analyse** ist immer: **Was ist der Zielgruppe wichtig?** – abgeleitet aus einer reichen Persona. Diese strategischen Erkenntnisse (z. B. „Startseite spricht zu viele Zielgruppen an", „Features statt Lösungen", „Navigation beantwortet kein Geschäftsproblem") stehen **vorn und prominent**. Die **technischen Findings** (Kontrast, Touch-Ziele, Formulare, Konsole …) werden **erwähnt, aber sekundär** – in einem **aufklappbaren Accordion** (Teil 2). Executive Summary führt mit den strategischen Punkten, nicht mit Messzahlen.

### Reiche Persona (Struktur)
Avatar + Name/Rolle · **Leitspruch** (ein Satz in Ich-Form) · **Ziele** · **Bedürfnisse** · **Motivation** · **Frustrationen**. Aus dieser Persona werden die strategischen Erkenntnisse *sichtbar abgeleitet*.

**Beispiel Geschäftsführer (worksdone):** Leitspruch „Ich will jederzeit wissen, welche Projekte profitabel sind und wo wir gegensteuern müssen." → daraus abgeleitete Erkenntnisse: Startseite spricht zu viele Zielgruppen an / verkauft Features statt Lösungen / unscharfe Grafiken schwächen Vertrauen · Funktionsseiten sollten Alltagssituationen statt Features zeigen · Navigation benennt Funktionen statt Geschäftsprobleme · **Was gut funktioniert:** Zertifizierungen, Kundenstimmen, Referenzen; Pricing senkt Kaufbarrieren (kostenlos testen, keine Kreditkarte).

---

## Marketing / Growth
- **Leitfrage:** Wie holen wir mehr aus dem vorhandenen Traffic? → **Conversion & Wirkung.**
- **Nach vorn / ausführlich:** Conversion-Hebel, Above-the-fold-Klarheit, CTA-Klarheit & -Konsistenz, Reibung im Funnel, Trust/Beweis, Copy-Qualität (Nutzen statt Funktion), schwache Meta-Snippets. Nutze `conversion-content.md` als Hauptraster.
- **Knapper / übersetzt:** WCAG-Details nicht als Kriteriennummern, sondern als Wirkung („zu heller Text = zentrales Verkaufsargument kommt schwächer an", „Consent-Banner verdeckt den ersten Eindruck = Absprünge"). Konsole/Code nur, wenn es Marketing-Daten betrifft (z. B. defektes Tracking = Datenverlust – das interessiert Marketing sehr).
- **Sprache:** Wirkung, Funnel, erster Eindruck, Vertrauen, Botschaft. Weniger Fachjargon.
- **Roadmap-Fokus:** Quick Wins mit Conversion-Hebel zuerst.

## Tech / Engineering / IT
- **Leitfrage:** Was ist technisch kaputt oder riskant? → **Qualität, Performance, Barrierefreiheit als Umsetzung.**
- **Nach vorn / ausführlich:** Konsolenfehler, defektes Tracking/JS, WCAG-Erfolgskriterien mit konkreten Werten (Kontrast-Ratios, Zielgrößen px, fehlende Alt/Labels), Heading-/Semantik-Struktur, konkrete Umsetzungsempfehlungen (Tokens, Selektoren, px-Werte).
- **Knapper:** Marketing-Narrativ. Aber Conversion-Findings bleiben als „UX-Qualität" drin.
- **Sprache:** präzise, mit Kriterien-Nummern (WCAG 1.4.3), Messwerten und Lösungsansatz. Code-nah.
- **Roadmap-Fokus:** Aufwand realistisch einordnen, Quick Wins technischer Natur.

## Entscheider:in / Geschäftsführung / Owner (Default)
- **Leitfrage:** Lohnt sich das, und was zuerst? → **Business-Impact, Risiko, Priorisierung.**
- **Nach vorn:** Executive Summary, Stärken (Wertschätzung), 3–5 wichtigste Punkte mit Wirkung, Priorisierung/Roadmap (Aufwand × Wirkung), rechtliche Risiken (Consent/DSGVO, Barrierefreiheit als Pflicht).
- **Knapper:** Einzelne px-/Selektor-Details – in die Detail-Findings verlagern, in der Übersicht nur die Konsequenz.
- **Sprache:** knapp, konsequenzenorientiert, wenig Jargon, keine erfundenen Zahlen (qualitative Richtung: „senkt Reibung", „rechtliches Risiko").
- **Roadmap-Fokus:** klare Empfehlung „das zuerst", Quick Wins vs. größere Maßnahmen.

## Design / Product
- **Leitfrage:** Wo bricht die Experience? → **UX-Heuristiken, visuelle Konsistenz, Flows.**
- **Nach vorn:** Nielsen-Heuristiken, visuelles UI-Design (Hierarchie, Kontrast als Gestaltung, Konsistenz), Mobile/Responsive, Informationsarchitektur, Copy-Hierarchie.
- **Sprache:** Design-Vokabular (Hierarchie, Affordance, Konsistenz, Token), mit Screenshot-Belegen.
- **Roadmap-Fokus:** Design-System-Konsequenzen (z. B. zentrales „Text sekundär"-Token statt Einzelfixes).

---

## Umsetzung in der Website
- **Strategie-Divider-Headline** immer im Format **„&lt;Ziel&gt; durch &lt;Mittel&gt;"**, zielgruppenbezogen:
  - Marketing → „Conversion erhöhen durch gezielte Zielgruppenansprache."
  - Entscheider → „Wachstum & Effizienz sichern durch klare Priorisierung."
  - Tech → „Qualität & Performance steigern durch saubere Umsetzung."
  - Design → „Bessere Experience schaffen durch konsistente Gestaltung."
- **Überschrift der „Strategische Erkenntnisse"-Sektion** = derselbe Zielsatz „&lt;Need&gt; durch &lt;Mittel&gt;" – er benennt den Need, der erfüllt wird, wenn die gefundenen Punkte umgesetzt werden (z. B. „Conversion erhöhen durch gesteuerte Zielgruppenansprache").
- **Reihenfolge der Strategie-/Finding-Sektionen** nach obiger Priorität umsortieren.
- **Executive-Summary-Text** und **Hero-Untertitel** aus der Leitfrage der Zielgruppe ableiten.
- **Detailtiefe je Finding:** gewichtete Zielgruppe → ausführlicher; Nebenaspekte → kürzer, aber vorhanden.
- Bei **gemischtem Publikum** die Entscheider-Struktur nehmen und pro Sektion einen fachlichen Absatz ergänzen.
