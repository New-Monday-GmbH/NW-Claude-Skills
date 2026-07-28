# Prüfraster: Die fünf Brillen

Gehe die Website durch **alle fünf Brillen** durch. Jede liefert eine andere Art von Findings. Ein starkes Audit deckt alle vier ab, statt nur oberflächlich das Offensichtliche zu nennen. Nutze `survey.json` als Datenbeleg (Kontrast-Ratios, fehlende Alt-Texte, Tap-Target-Größen etc.) und die Screenshots als visuellen Beleg.

---

## Brille 1 – Nielsen: 10 Usability-Heuristiken

Prüfe für jede Heuristik: Wird sie erfüllt? Wo bricht sie? Ordne jedem Finding die passende Heuristik zu (Nummer + Name) – das strukturiert später die Slides.

1. **Sichtbarkeit des Systemstatus** – Bekommt der Nutzer Feedback? (Ladezustände, aktive Zustände, Fortschritt, Bestätigungen). Fehlt Feedback bei Klicks, Formularen, Warenkorb?
2. **Übereinstimmung System ↔ reale Welt** – Sprache verständlich, keine Fachjargon-/Systembegriffe? Icons und Metaphern erwartungskonform? Reihenfolge logisch?
3. **Nutzerkontrolle & Freiheit** – Gibt es „Zurück", Abbrechen, Undo? Kommt man aus Dialogen/Prozessen leicht wieder heraus? Erzwungene Schritte?
4. **Konsistenz & Standards** – Gleiche Dinge sehen gleich aus/heißen gleich? Buttons, Links, Interaktionsmuster einheitlich? Plattformkonventionen eingehalten?
5. **Fehlervermeidung** – Wird verhindert, dass Fehler entstehen? (Inline-Validierung, sinnvolle Defaults, Bestätigungen bei destruktiven Aktionen).
6. **Wiedererkennen statt Erinnern** – Sind Optionen/Infos sichtbar, statt dass man sie im Kopf behalten muss? (Sichtbare Navigation, Breadcrumbs, ausgefüllte Felder erkennbar).
7. **Flexibilität & Effizienz** – Gibt es Abkürzungen für Erfahrene? Suche, Filter, Autofill? Ist der Hauptweg schnell?
8. **Ästhetik & minimalistisches Design** – Kein visuelles Rauschen? Fokus auf das Wesentliche? Konkurrieren zu viele Elemente um Aufmerksamkeit?
9. **Fehler erkennen, verstehen, beheben** – Fehlermeldungen klar, in Klartext, mit Lösung? Kein „Error 404" ohne Hilfe?
10. **Hilfe & Dokumentation** – Sind Hilfe, FAQ, Kontakt auffindbar, wenn nötig?

---

## Brille 2 – WCAG: Barrierefreiheit

Belege mit den Messwerten aus `survey.json`. Orientiere dich an WCAG 2.1/2.2 Level AA.

- **Kontrast (1.4.3):** Normaltext ≥ 4.5:1, Großtext (≥24px, oder ≥18.66px bold) ≥ 3:1. `survey.json → contrastIssues` listet Unterschreitungen mit gemessener Ratio. Nenne konkrete Ratio + Ort.
- **Textalternativen (1.1.1):** Bilder mit Bedeutung brauchen Alt-Text. `imagesMissingAlt` zeigt fehlende. Dekorative Bilder brauchen leeres Alt – im Zweifel als Finding markieren.
- **Formular-Labels (1.3.1 / 3.3.2):** Jedes Feld braucht ein sichtbares, programmatisch verknüpftes Label. Placeholder ≠ Label. Siehe `formFieldsNoLabel`.
- **Tastaturbedienbarkeit (2.1.1):** Ist alles per Tab erreichbar? Sichtbarer Fokus-Indikator (2.4.7)? Prüfe im Screenshot, ob Fokus-States existieren; falls unklar, als Prüfpunkt vermerken.
- **Überschriften-Hierarchie (1.3.1 / 2.4.6):** Genau eine H1? Logische, lückenlose Reihenfolge? `headings` + `h1Count` prüfen.
- **Zielgröße (2.5.8):** Interaktive Elemente ≥ 24×24px (AA), empfohlen 44×44px. Siehe `smallTargets`.
- **Sprache (3.1.1):** `lang`-Attribut gesetzt und korrekt?
- **Seitenstruktur/Landmarks:** Klare Bereiche (Header, Nav, Main, Footer)?

---

## Brille 3 – Visuelles / UI-Design

Subjektiver, aber am Screenshot belegbar. Kalibriere an `examples/good/` und `examples/bad/`.

- **Visuelle Hierarchie:** Führt das Design den Blick? Ist die wichtigste Aktion (primärer CTA) klar dominant? Konkurrieren mehrere „primäre" Buttons?
- **Typografie:** Lesbare Schriftgrößen (Body ≥ 16px)? Zeilenlänge (~50–75 Zeichen)? Zeilenhöhe? Zu viele Schriftarten/Größen/Gewichte?
- **Spacing & Ausrichtung:** Konsistente Abstände? Sauberes Grid? Elemente ausgerichtet oder „schwimmend"? Genug Weißraum oder überfüllt?
- **Farbsystem:** Begrenzte, konsistente Palette? Farbe funktional eingesetzt (Aktion, Status) statt beliebig? Markenfarben konsistent?
- **Konsistenz der Komponenten:** Buttons, Cards, Inputs überall gleich gestaltet? Radien, Schatten, States einheitlich?
- **Bildsprache:** Qualität, Konsistenz, Zuschnitt der Bilder? Passen sie zusammen? Verpixelt/verzerrt?
- **CTA-Klarheit:** Sehen klickbare Dinge klickbar aus? Beschriftung handlungsorientiert („Jetzt starten" statt „Absenden")?

---

## Brille 4 – Mobile / Responsive

Nutze die Mobile-Screenshots (390px) und `viewports.mobile` aus `survey.json`.

- **Viewport-Meta:** Ist `<meta name=viewport>` gesetzt? (`viewportMeta`). Fehlt es, ist die Seite auf Mobile meist unbrauchbar.
- **Kein horizontales Scrollen:** Läuft Content über den Rand? Abgeschnittene Elemente im Full-Page-Mobile-Screenshot?
- **Tap-Targets:** Buttons/Links groß und weit genug auseinander? Siehe `smallTargets` (Mobile).
- **Lesbarkeit:** Schrift auf Mobile groß genug ohne Zoom? Body ≥ 16px verhindert Auto-Zoom auf iOS bei Inputs.
- **Reflow statt Zoom:** Passt sich das Layout an (Spalten → Stapel), statt die Desktop-Ansicht zu verkleinern?
- **Navigation:** Funktioniert das mobile Menü (Burger)? Ist es auffindbar?
- **Touch-Reihenfolge / Priorität:** Steht das Wichtigste oben? Sind Formulare mobil bequem ausfüllbar (richtige Input-Types)?
- **Fixe Elemente:** Verdecken Sticky-Header/Cookie-Banner auf kleinen Screens zu viel Inhalt?

---

## Brille 5 – Informationsarchitektur & Seitenstruktur

Diese Brille prüft, ob die Website **strukturell** funktioniert – unabhängig davon, wie einzelne Elemente gestaltet sind. Belege mit der Navigation im Screenshot, `headings` aus `survey.json` und `crawl.json` (welche Seiten existieren, wie hängen sie zusammen). Findings zählen auf der Scope-Folie zur Kategorie Usability (Beschriftungs-Findings ggf. zu Copy).

**Navigationsstruktur (IA):**
- **Sinnvoller Aufbau:** Ist die Hauptnavigation nach den **Aufgaben und Fragen der Nutzer** gegliedert – oder spiegelt sie die interne Organisation/Produktlogik der Firma? Passt die Gruppierung (gehören die Punkte unter ihrem Oberpunkt wirklich zusammen)?
- **Umfang & Tiefe:** Zu viele Top-Level-Punkte (Orientierung leidet) oder wichtige Ziele zu tief vergraben (> 2–3 Klicks)? Gibt es Sackgassen oder verwaiste Seiten (aus `crawl.json` ableitbar)?
- **Priorität & Reihenfolge:** Steht das Wichtigste (fürs Geschäft und für die Nutzer) vorn? Ist der Conversion-Pfad (z. B. Preise, Demo, Kontakt) prominent erreichbar?
- **Konsistenz:** Ist die Navigation auf allen Seiten identisch? Führen gleich benannte Links überall zum selben Ziel?

**Link- und Navigations-Beschriftungen:**
- **Nutzersprache statt Eigenjargon:** Verstehen Erstbesucher jeden Menüpunkt, ohne die Firma zu kennen? Erfundene Produktnamen, interne Begriffe oder Marketing-Wortschöpfungen als Nav-Label sind ein Finding.
- **Vorhersagbarkeit:** Sagt das Label eindeutig, was auf der Zielseite wartet? Decken sich Link-Text, Seitentitel und H1 der Zielseite?
- **Unterscheidbarkeit:** Sind ähnliche Punkte klar voneinander abgegrenzt („Leistungen" vs. „Services" vs. „Lösungen")? Generische Labels („Mehr", „Info") sind wertlos.

**Struktur & Aufbau der einzelnen Seiten:**
- **Aufbau entlang der Zielgruppe:** Folgt die Sektions-Reihenfolge der Seite den **Fragen der Zielgruppe in ihrer Entscheidungsreihenfolge** (Was ist das? Für wen? Was bringt es mir? Warum glaubwürdig? Was kostet es? Was tun?) – oder ist sie beliebig sortiert? Bewerte aus Sicht der Fokus-Persona.
- **Ein Job pro Seite:** Hat jede Seite eine klare Aufgabe und einen erkennbaren nächsten Schritt – oder will sie alles gleichzeitig?
- **Wichtiges zuerst:** Steht das Entscheidende above the fold bzw. früh im Lesefluss? Muss man scrollen/suchen, um den Kern zu verstehen?
- **Features vs. echte Lösungen:** Ein Muster, das wir sehr oft sehen – Seiten **listen Features auf, statt Lösungen für die Probleme der Zielgruppe zu zeigen**. Prüfe pro Kernseite: Wird ein konkretes Nutzerproblem benannt und die Lösung dafür erzählt (Problem → Lösung → Ergebnis), oder reiht die Seite Funktionsnamen aneinander, deren Nutzen sich der Besucher selbst übersetzen muss? (Inhaltliche Vertiefung: `conversion-content.md` → „Nutzen statt Funktion".)

---

## Priorisierung (für alle Findings)

Ordne jedem Finding einen **Schweregrad** zu (Details in `finding-workflow.md`). Faustregel für die Wirkung: *Wie viele Nutzer betrifft es × wie stark behindert es die Aufgabe × wie leicht ist es zu umgehen.* Barrierefreiheits-Verstöße (WCAG AA) sind grundsätzlich relevant, da sie ganze Nutzergruppen ausschließen und rechtlich (BFSG/EN 301 549) zunehmend verpflichtend sind.
