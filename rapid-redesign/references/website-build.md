# Ergebnis-Website (statisches Folien-Deck im Rapid-Redesign-Stil)

Das Endergebnis des Audits ist eine **lokale, statische Website** – kein Figma-File, kein Build-Schritt. Ein **Folien-Deck**: **eine Sektion pro Ansicht**, Navigation per **Weiter/Zurück**, Tastatur und Mini-Nav oben. Man öffnet es direkt im Browser (`index.html`) und gibt es per Ordner/Link weiter. **Kein langer Scroll-Onepager** – jede Folie hat genau einen Fokus. Optik und Aufbau orientieren sich an der New-Monday-**Rapid-Redesign-Angebotspräsentation** (Figma `OLhdXoioocN3quqAtXVttL`, „Union Retainer-Angebot"): Cover in Kundenfarbe → farbige Sektions-Bänder → Content-Sektionen mit Cards, Stat-Donuts, Charts, Tabellen → „Danke"-Abschluss. Styling strikt nach `design-system-newmonday.md`.

## Die index.html wird NICHT von Hand geschrieben

**Du schreibst eine `deck.json` (Texte + Bildpfade), ein Skript baut das Deck.**
Struktur, CSS, Deck-Navigation und Admin-Modus kommen aus den Vorlagen – sie sind
bei jedem Audit identisch und kosten dich keine Zeile.

```bash
scripts/.venv/bin/python scripts/build_deck.py audits/<domain>-<datum>/deck.json \
  --out audits/<domain>-<datum>/site/index.html
```

**Vollständige Feldreferenz: `references/deck-content-schema.md`** – das ist die
einzige Datei, die du zum Texten brauchst.

```
audits/<domain>-<YYYY-MM-DD>/
  deck.json       ← DEIN Output: nur Inhalt
  site/
    index.html    ← gebaut, nicht von Hand editiert
    assets/       ← Screenshots, Kundenlogo, Illustrationen
```

Zusammengesetzt wird aus:

| Baustein | Quelle |
|---|---|
| Kopf (Titel, Fonts, `<style>`, Logo-Sprite, Mini-Nav) | `templates/deck.head.html` |
| Kanonisches CSS | `references/site-styles.css` (unverändert eingesetzt) |
| Jede Folie | `templates/slides/<type>.html` |
| Deck-Navigation + Folien-Skript | `templates/deck.tail.html` |
| Admin-/Edit-Modus | `references/admin-mode-snippet.html` |

- **Self-contained bleibt es trotzdem:** Das Ergebnis ist eine einzelne `index.html`
  mit inline `<style>`/`<script>`. Der Build ist nur ein Zusammensetzen – kein
  Build-Tool, keine Abhängigkeiten, nichts, was der Kunde installieren müsste.
- **Bilder:** Screenshots als PNG in `assets/`, relativ referenziert (`assets/f01.png`).
  Große PNGs werden **nicht** base64-inlined.
- **Fonts:** Google-Fonts-`<link>` für Rethink Sans + Inter mit System-Fallback.
- **Fehlt ein Pflichtfeld, bricht der Build ab** (mit Folie + Key). Das ist Absicht:
  lieber ein Fehler als eine stille Lücke im Kunden-Deck.
- **Fertig testen:** Preview-Server starten und die Folien gegenlesen. Danach dem
  Nutzer den Pfad `audits/<domain>-<date>/site/index.html` nennen.

### Vorlagen ändern

`templates/slides/<type>.html` ändern → **jedes künftige Deck** ändert sich mit.
Danach prüfen, dass das Referenz-Deck noch exakt reproduziert wird:

```bash
scripts/.venv/bin/python scripts/build_deck.py audits/worksdone.de-2026-07-16/deck.json --out /tmp/probe.html
```

`audits/worksdone.de-2026-07-16/deck.json` ist das **Referenz-Deck** (die freigegebene
worksdone-Präsentation) und zugleich das beste Beispiel für eine gefüllte `deck.json`.

## Cover in Kundenfarbe (Vorgabe 3)

Die **erste Sektion (Hero/Cover)** wird in der **Primärfarbe der auditierten Firma** eingefärbt – nicht in New-Monday-Teal. Die Farbe kommt aus `survey.json → brandColor` (siehe Capture-Script). Setze sie als `--client` und wähle `--client-ink` (weiß oder `#0b1416`) automatisch nach Kontrast (WCAG ≥ 4.5 gegen die Kundenfarbe). Beispiel worksdone.de → Violett `#512ffc` (live erkannt). Ist keine Farbe sicher erkennbar, Fallback auf New-Monday-Teal und im Text vermerken.

Alle **übrigen** Sektionen nutzen das New-Monday-System (Teal-Bänder, Coral-Findings, Neutrals).

## Sektions-Katalog (modular – Auswahl kommt aus dem Intake)

Die Website ist aus **Sektions-Bausteinen** zusammengesetzt. **Kern-Sektionen** sind immer dabei; **optionale** Sektionen werden nur gebaut, wenn sie im Intake (`audit-intake.md`) gewählt wurden – keine leeren Platzhalter für Nicht-Gewähltes. Reihenfolge = RR-Reihenfolge (aus der PB-Liftechnik-Präsi). Jeder Baustein entspricht einem `type` in der `deck.json` (siehe `deck-content-schema.md`).

**Struktur-Signatur (RR):** Sektions-Gruppen werden von einem farbigen **Divider-Band** (Teal-Vollfläche, großer weißer Titel + Kicker, Logo oben rechts) eingeleitet – wie die vertikalen Bänder in der Präsi.

**Feste Intro-Sequenz (immer, in dieser Reihenfolge):** Cover → **Über New Monday** → **Referenzen & Expertise** → **Über das Projekt** → **Unser Redesign-Fokus** → **Unser Vorgehen**. Danach folgen Executive Summary/Scope und die (optionalen) Strategie-, Findings- und Abschluss-Sektionen. Die Intro-Slides entsprechen den festen RR-Slides 3–7 (`OLhdXoioocN3quqAtXVttL`, nodes 3856-1138 / 3856-1317 / 3856-1119 / 3856-1002 / 3856-922).

| # | Sektion | Kern/Opt | Inhalt & Bau |
|---|---------|----------|--------------|
| 1 | **Cover / Hero** | Kern | *Kundenfarbe (Verlauf `--client` → `--client-2`).* Kopfzeile: Kicker „UX/UI-Audit" **oben links**, NM-Logo weiß **oben rechts** (eine Zeile, `align-items:center`, keine Zierlinie). Mitte: **Logo der auditierten Firma** über dem Titel (`.client-logo`, weiß eingefärbt via `filter:brightness(0) invert(1)` → sicherer Kontrast auf der Markenfarbe; Quelle: Logo-Datei der Website, SVG bevorzugt, sonst hochauflösendes PNG/WebP mit Transparenz), darunter **Titel „Rapid Redesign"**, darunter **Domain als Untertitel**, darunter Meta = **„New Monday GmbH · <Monat Jahr>"**. Keine Seitenanzahl/Viewports/Zielgruppe/„Playwright". |
| 2 | **Agenda / Inhalt** | **Opt (i. d. R. weg)** | Das Deck hat eine Mini-Nav und einen Folienzähler — ein Inhaltsverzeichnis ist doppelt. Nur auf ausdrücklichen Wunsch. |
| 3 | **Über New Monday** | Kern (fix) | RR-Slide 3 (`3856-1138`) — **Texte wörtlich aus der Figma-Vorlage**, nicht neu erfinden: Titel + Coral-Unterstrich, Fließtext „New Monday ist seit 2018 spezialisiert …“, teal Statement „Wir verwandeln komplexe Unternehmenssoftware …“, Label „Beste UX Design Agentur 2026“. Dazu das **echte UXDA-Siegel** (`assets/uxda.svg`, unten links) und **zwei Team-Fotos** (`assets/img/new-monday-1.jpg` Workshop, `-2.jpg` Laptop). Alles liegt in `references/assets/` und wird vom Build automatisch kopiert. |
| 4 | **Referenzen & Expertise** | Kern (fix) | RR-Slide 4 (`3856-1317`) — **Texte und Logo-Wand wörtlich aus der Figma-Vorlage**: Titel „Deine UX in besten Händen: Setze auf Expert:innen“, Fließtext links, Wand rechts. **5 Gruppen, 23 Logos** (Technologie und Beratung · Finanzen · Automobil und Transportwesen · Energie und Industrie · Media und Verlagswesen). Die Logos liegen als echte SVGs in `references/assets/logos/` (direkt aus dem Figma-File gezogen) und werden vom Build kopiert. **Einheitlich ist die HÖHE (30px), nicht die Box** — alle Logo-SVGs haben viewBox-Höhe 74, dadurch wirken sie gleich groß bei natürlicher Breite. Eine feste Box verzerrt Logos (ein VW-Kreis braucht andere Proportionen als ein Axel-Springer-Schriftzug). Award-/Siegel-Grafiken gehören **nicht** in die Kundenwand. |
| 5 | **Über das Projekt** | Kern (**projektspezifisch**) | RR-Slide 5: Kundenbeschreibung (was macht die Firma, wen adressiert die Website) + Redesign-Chance; rechts teal Statement + „Unser Ansatz"-Card (3 Punkte). Text an das Audit-Projekt anpassen. |
| 6 | **Unser Redesign-Fokus** | Kern (**projektspezifisch**) | RR-Slide 6: zwei Cards „Ziele" (4 Punkte) + „Wirkung". Text an das Projekt anpassen. |
| 7 | **Unser Vorgehen** | Kern (fix) | RR-Slide 7: 6 nummerierte Karten – Proto Personas · Jobs-to-be-done · Audit · Wettbewerbsanalyse · Information Architecture · Konzept & Mockup. |
| 8 | **Executive Summary** | Kern | **Führt mit dem, was der Zielgruppe wichtig ist** (nicht mit technischen Zahlen): Gesamteindruck + 4–5 strategische Punkte aus Persona-Sicht + Stärken-Block (grün, „Das trägt bereits"). Technische Qualität nur als **kurzer, sekundärer Verweis** mit Anker auf den aufklappbaren Teil 2 – kein Severity-Donut im Vordergrund. |
| 9 | **Scope & Methodik** | Kern | **Alle** geprüften Seiten (Liste/Tabelle/Zähler), Viewports, zwei Ebenen + fünf Brillen, Tool Playwright. |
| — | *Divider „Strategische Einschätzung"* | — | Teal-Band. **Headline im „&lt;Ziel&gt; durch &lt;Mittel&gt;"-Format, zielgruppenbezogen** (z. B. Marketing → „Conversion erhöhen durch gezielte Zielgruppenansprache."; Entscheider → „Wachstum sichern durch …"; Tech → „Qualität steigern durch …"; Design → „Bessere Experience durch …"). Kicker „Teil 1 · Strategische Einschätzung". |
| 10 | **Zielgruppe / Persona** | Kern (empf.) | **Reiche Persona:** echtes Porträtfoto (kein Initialen-Platzhalter; frei nutzbare Quelle wie Unsplash, passend zu Rolle/Alter auswählen), Name/Rolle, **Leitspruch** (Zitat) und vier Blöcke **Ziele · Bedürfnisse · Motivation · Frustrationen**. **1–3 Personas möglich** – je nach Redesign-Fokus: Container `.personas-wrap` mit `data-count="1|2|3"` steuert das Layout. Grundlage für die strategischen Erkenntnisse. |
| 10b | **Jobs To Be Done** | Kern (empf.) | RR-Slide (`3856-860`), **direkt nach der Persona-Folie**, 1:1 nach Figma-Vorlage: Titel „Jobs To Be Done", darunter **zwei weiße Karten** — links **FUNKTIONALE JOBS**, rechts **EMOTIONALE JOBS** (teal Versal-Label), je Karte **3 Aussagen** in der Display-Schrift mit Hairline unter jeder Aussage; Coral-Schwung (`gfx/jtbd-schwung.svg`) oben rechts angeschnitten. **Die Jobs werden pro Projekt aus der Fokus-Persona abgeleitet** (funktional = was erledigt werden muss, emotional = wie es sich anfühlen soll) — nie die Beispieltexte der Vorlage übernehmen. Persona-Varianten via `personaVarianten` empfohlen, damit die Jobs im Admin mit der Fokus-Persona umschalten. |
| 11 | **Positionierung** | Opt | Markenpositionierung: Fokus, Merkmale, Zusatznutzen (nummerierte Aspekte) + Kern-Claim. |
| 12 | **Strategische Erkenntnisse** | **Kern (Herzstück)** | **Aus der Persona abgeleitet, nicht technisch.** Eingeleitet von einer **Übergangsfolie „Audit"** (Teal-Divider; Untertitel = Zielsatz im Format „‹Ziel/Need› durch ‹Mittel›"). Danach **je Erkenntnis eine eigene Folie** (Kicker „Erkenntnis 0X · Bereich", Aussage als Titel, kurzer Text links + **stützender Screenshot** rechts). Abschluss: **„Was gut funktioniert"** – ebenfalls **mit Beleg-Screenshots** der Seite, **max. 3 Punkte pro Folie**, darüber hinaus eine weitere Folie. |
| 13 | **Wettbewerber & Inspiration** | Opt | **Pro Wettbewerber eine eigene Folie**: echter Startseiten-Screenshot links, rechts **„Macht gut"** (✓ grün) / **„Macht schlechter"** (✕ coral). **Inspiration nach RR-Vorlage** (Figma-Node `3856-1460`): zweispaltig – **links** großer Titel „Inspiration", darunter ein **Daumen-hoch-Icon**, eine Zwischenüberschrift (z. B. „Struktur und Design") und **3 Bulletpoints**, was daran funktioniert; **rechts** die Beispiel-Screenshots groß und leicht angeschrägt (`rotate(-2.5deg)` / `rotate(2deg)`). **Keine Bildunterschriften** – der Text steht gebündelt links, nicht frei neben der Überschrift. Mehrere Inspirations-Folien statt einer vollen. |
| — | *Divider „Detail-Findings"* | — | Teal-Band. |
| 14 | **Detail-Findings (technisch)** | Kern | **Als aufklappbares Accordion** (`<details>`/`<summary>`): Summary = Schweregrad-Pill + Titel; im Aufklapp Brille + Beobachtung/Wirkung/Empfehlung (+ Screenshot bei F mit Beleg-Bild). **Sekundär** gegenüber den strategischen Erkenntnissen. Nach Schweregrad; site-weite Muster markieren. |
| 15 | **Priorisierung / Roadmap** | Kern | „Quick Wins" (teal) vs. „Größere Maßnahmen" (neutral); optional 2×2-Matrix. |
| — | *Divider „Unser Vorschlag"* | — | Teal-Band (wenn Wireframes folgen). |
| 16 | **Unser Vorschlag (Wireframes)** | Opt | Redesign-Skizze(n) für 1–2 Kernseiten als **echte HTML/CSS-Wireframe-Blöcke**, als „Vorschlag/Wireframe" beschriftet. Darunter **immer „Was wir verbessern würden"** als **Bulletliste** (`.wf-list`, echte `list-style` Bullets – **keine** Rand-Striche/`border-left`), je Punkt: fettes Verbesserungs-Statement + kurzer Satz **warum**, plus die Finding-Referenz als kleine Pill (`.fref`, z. B. F01). Kein fertiges Pixel-Design vortäuschen. |
| 17 | **Next Steps / Angebot** | Opt | „Komplettes Redesign aus einer Hand" **mit RR-Illustration** + **Ziel** (✓) + **Ergebnis** (✳) + **Dauer** (ca. 8–10 Wochen) + **Investition** (Richtwert, projektabhängig bestätigen). **Eckdaten-Karten sind GENAU diese zwei (Dauer + Investition) — keine zusätzlichen Karten erfinden (z. B. „Ihr Aufwand").** **Projektablauf als eigene Folie mit Zeitstrahl** (`.tl`: durchgehende Linie + Punkt je Phase über den Phasen-Karten). |
| 18 | **Abschluss / Danke** | Kern | **Teal-Vollband** (nicht Kundenfarbe): NM-Logo zentriert oben, „That's all, folks." + großes **„Danke!"** links, Tagline rechts, 3-Spalten-Footer **Find us / Let's connect / Follow us** mit den NM-Firmendaten aus `design-system-newmonday.md`. |

### Wiederkehrende RR-Bausteine (aus der Präsi übernehmen)
- **Divider-Band** als Signatur der Sektions-Gruppen (Teal-Vollfläche, weißer Titel, Logo).
- **Stat-Donut** (SVG/`conic-gradient`) für Kennzahlen (geprüfte Seiten, Findings je Schweregrad).
- **Balken/Fortschritt** für Verteilungen (reine `<div>`-Balken, keine Chart-Lib).
- **Cards** in `--n-50` mit `--shadow`, `--r-lg`; **Persona-Cards** mit Avatar-Kreis.
- **Tabelle** für Seiten-Übersicht (alle Seiten) / Priorisierung.
- **Browser-Mockup-Rahmen** (Fenster-Punkte) um Screenshots von Startseite/Wettbewerbern/Wireframes.

## Folien-Modus (Deck) – verbindlich

**Eine Folie = ein Gedanke.** Inhalt darf die Ansicht nicht überlaufen; lieber mehr Folien als eine hohe Sektion.

- **Technik:** Alle Inhalts-Blöcke sind direkte `<header>/<section>/<footer>`-Kinder von `<body>`. Sichtbar ist nur die Folie mit `.active`:
  `body > header:not(.active), body > section:not(.active), body > footer:not(.active){display:none}`
  (Das `:not(.active)` ist nötig, damit es `.cover/.divider/.closing` mit eigenem `display:flex` überstimmt.)
- **Steuerung** (im kanonischen Stylesheet + Deck-Script enthalten): Weiter/Zurück-Buttons **unten mittig** mit Zähler „14 / 30" (nicht unten rechts – dort sitzt der Admin-Toggle), **Pfeiltasten/PageUp/PageDown**, **Mini-Nav oben** springt zur Folie (ab Folie 2 eingeblendet).
- **Mini-Nav:** deckt **alle** Gruppen ab – auch die vor der Summary (Über uns · Referenzen · Projekt · Vorgehen · Summary · Scope · Zielgruppe · Positionierung · Audit · Wettbewerber · Findings · Roadmap · Vorschlag · Next Steps). `flex-wrap:wrap` + `align-items:center` (sonst strecken sich die Links und der aktive Punkt wird zum Kreis). **Der aktive Punkt wird hervorgehoben** (teal Pill) – aktiv ist der letzte Nav-Punkt, dessen Folie ≤ der aktuellen Folie liegt. Der **Fortschrittsbalken `#bar` liegt INNERHALB der Nav an deren Unterkante** (`position:absolute;bottom:0`), nicht darüber. Ein `MutationObserver` rendert neu, wenn der Admin-Modus Folien hinzufügt/entfernt/verschiebt (neu hinzugefügte Folie wird angesprungen).
- **Abstand zur Navigation:** aktive Folien bekommen oben deutlich mehr Luft als unten (`padding-block: clamp(7rem,13vh,9.5rem) clamp(4rem,8vh,5.5rem)`), damit die Überschrift nicht an der fixen Mini-Nav klebt (die auf schmalen Viewports zweizeilig umbricht).
- **Kein Scroll-Reveal:** `.rv` wird im Deck neutralisiert; jede Folie blendet sich beim Wechsel kurz ein.

**Splitting-Regeln (Fokus):**
- **Pro Erkenntnis/Challenge eine eigene Folie** (Kicker „Erkenntnis 0X · Bereich" + Aussage als Titel + kurzer Text links + stützender Screenshot rechts).
- **Pro Wettbewerber eine eigene Folie**: Screenshot links, rechts **„Macht gut"** (✓, grün) und **„Macht schlechter"** (✕, coral).
- **Inspiration: nur Bilder** – Dribbble-Screenshots von Designs, die funktionieren (`dribbble.com/shots/popular/web-design`, `dribbble.com/search/<thema>`), **ohne** erklärenden Text; Promo-Banner/Filterleiste vorher wegschneiden (`sips -c 1140 2880`), ein großes Board pro Folie.
- **Lange Blöcke trennen:** z. B. „Komplettes Redesign" (Ziel/Ergebnis/Dauer/Investition) und „Projektablauf" (Timeline) sind zwei Folien.
- Technische Detail-Findings bleiben **eine** Folie (Accordion, eingeklappt kompakt).


### RR-Illustrationen (vom Nutzer bereitgestellt)
Die Original-Illustrationen der Rapid-Redesign-Vorlage nach `assets/gfx/` kopieren und einsetzen:
- **Unser Redesign-Fokus** und **Komplettes Redesign aus einer Hand** → `redesign-fokus.svg` (links, `.gfx-row`: Grafik + Karten).
- **Zentrale Aspekte der Markenpositionierung** → `aspekte.svg` (links, Aspekte rechts).
- **Unser Vorgehen** → `schleife.svg` als dekorative Coral-Schleife (`.gfx-deco`, `position:absolute`, hinter dem Inhalt).

### Layout-Regeln des Decks (nicht aufweichen)
- **Überschriften stehen auf JEDER Inhaltsfolie an derselben Stelle.** Inhaltsfolien sind
  oben ausgerichtet (`justify-content:flex-start` + `--kopf`), nicht zentriert. Wer eine
  neue Folie baut: Kicker + `h2.sec-title` zuerst, Kopf-Grids mit `align-items:start`.
  Prüfbar: `.sec-title`-Position messen – alle Inhaltsfolien müssen gleich liegen.
- **Eine Folie = eine Ansicht.** Nichts darf scrollen, auch nicht bei ~640px Fensterhöhe
  (Laptop mit Browser-Chrome). Dafür gibt es `@media (max-height:820px|680px)`-Stufen.
  Wenn eine Folie überläuft: **in die Breite gehen oder splitten**, nicht schrumpfen.
- **Beleg-Screenshots deckeln ihre Höhe** (`max-height` statt natürlicher Höhe), sonst
  bestimmt das Bild den Abstand zwischen Überschrift und Text.

### CSS-Fallstricke (wichtig)
- **Aufzählungen (`.ck-list`/`.x-list`/`.ast-list`) sind KEINE Flex-Container.** Als Flex
  wird jedes Inline-Element (z. B. `<b>Label:</b>`) zu einer eigenen Spalte – Label links,
  Text daneben umbrochen. Marker gehört absolut positioniert, Inhalt in den Textfluss.
- **Grid-Spalten mit `minmax(0,1fr)`, nicht `1fr`.** `1fr` hat ein implizites `auto`-Minimum;
  breiter Inhalt drückt die Spalte auf (im Admin-Katalog wurden aus 2× gleich breit
  95px/451px).
- **Messfalle:** `@keyframes slideIn` startet mit `translateY(10px)`. Wer direkt nach dem
  Folienwechsel misst, misst 10px Overflow, der keiner ist – **~420ms warten**.
- **Keine `<button>` in Folien-Vorlagen ohne Not.** Der Admin-Katalog rendert jede Folie
  in einem `<button>`; ein verschachtelter Button ist ungültiges HTML – der Parser löst
  ihn heraus und zerlegt die Kachel. `build_deck.py` (`nur_vorschau`) entfernt sie
  deshalb aus den Katalog-Miniaturen.
- **Katalog-Platzhalter zeigen auf `assets/platzhalter.svg`**, nie auf Projekt-Assets
  (`f01.png`, `client-logo.webp`) – die gibt es im Katalog-Kontext nicht → 404 in jedem
  ausgelieferten Deck.
- **`.wrap` braucht `width:100%`.** In Flex-Column-Containern (Cover/Divider/Closing) deaktiviert `margin-inline:auto` sonst das Stretchen → die Zeile schrumpft auf Inhaltsbreite und wirkt zentriert (Kopfzeile „verschoben").
- **`nav.mini` braucht `align-items:center`** – sonst strecken sich die Links über die volle Nav-Höhe und der aktive Punkt wird zum Kreis. Mit `flex-wrap:wrap` bricht die Nav auf schmalen Viewports sauber um.
- Folien-Höhe im Blick behalten: passt der Inhalt nicht, **splitten** (z. B. Executive Summary → „Executive Summary" + „Das trägt bereits").

## Kanonisches Stylesheet (Konsistenz über alle Audits)

**`references/site-styles.css` unverändert** in den `<style>`-Block der `index.html` einsetzen. Es enthält Tokens, Typo, Abstände, alle Komponenten und das Deck-CSS.

> **Einzige erlaubte Änderung:** `--client` / `--client-2` / `--client-ink` (Primärfarbe der auditierten Firma, nur Cover). **Abstände, Schriftarten, Farben und Komponenten werden nicht pro Projekt neu erfunden** – sie sind bei jeder Anwendung des Skills identisch.

## Admin-/Edit-Modus (Teil jedes Deliverables)
Jede Audit-Website enthält einen **self-contained Admin/Edit-Modus** (Vanilla JS+CSS, kein Build) – als `<style id="admin-style">` + `<script id="admin-script">` direkt vor `</body>`. **Fertiger, getesteter Baustein: `references/admin-mode-snippet.html`** – unverändert einfügen (nicht neu erfinden).

Funktionen (Toggle „✎ Bearbeiten" unten rechts):
- **Text bearbeiten** (Inline-contentEditable auf Leaf-Text-Elementen), **Bild tauschen** (Datei → data-URL), **Reihenfolge** (▲▼ je Block), **Abschnitt hinzufügen** (Vorlagen: Titel+Text · Zwei Spalten · Divider) und **entfernen** (✕ mit Rückfrage).
- **Figma-Frame einbetten** („🎨 Figma-Frame"): Link zu einem Figma-Frame einfügen → es entsteht eine neue Folie, die den Frame **live 1:1** zeigt. Die URL wird automatisch zur Embed-URL (`www.figma.com` → `embed.figma.com` + `embed-host=share`). **Voraussetzung:** Die Figma-Datei muss auf „Jeder mit dem Link – kann ansehen" stehen, sonst sieht der Betrachter eine Rechte-Meldung. Der Embed bleibt beim Export erhalten (als iframe, braucht also Internet); soll der Stand **eingefroren** werden, stattdessen beim Bauen einen Screenshot des Frames über die Figma-Tools holen und als Bild einsetzen.
- **Persistenz** via localStorage (nur auf der Autoren-Seite).
- **Export**: lädt eine saubere standalone `index.html` – Admin-UI entfernt, Bilder als data-URL eingebacken, `data-nm-frozen` am `<html>` (normale Betrachter sehen **keinen** Editor); die Export-Datei bleibt via `?edit`/`?admin` weiter bearbeitbar.

Kompatibilitäts-Voraussetzungen (die dieser Katalog ohnehin erfüllt): Inhalts-Blöcke sind direkte `<header>/<section>/<footer>`-Kinder von `<body>` (Fixed-Elemente `#bar`, `nav.mini` sind ausgenommen); Design-Klassen `.wrap/.sec-title/.kicker/.lead/.card/.cols-2/.divider` verwenden, damit neue Abschnitte passen; `.rv`-Reveal bleibt intakt.

## Technische Leitplanken
Diese Punkte stecken bereits in `site-styles.css` und den Vorlagen – sie sind hier
dokumentiert, damit sie bei Vorlagen-Änderungen nicht verloren gehen:

- **Nur HTML/CSS/JS**, keine Frameworks, keine npm-Abhängigkeiten. Der Build ist ein
  reines Zusammensetzen von Textbausteinen.
- **Responsive:** Flexbox/Grid, `clamp()` für Typo, Bilder `max-width:100%`. Kein horizontales Scrollen des Bodys; breite Tabellen in `overflow-x:auto`.
- **Kein Scroll-Reveal:** Im Deck-Modus ist `.rv` neutralisiert; jede Folie blendet sich beim Wechsel kurz ein (`@keyframes slideIn`). `prefers-reduced-motion` respektieren.
- **Mini-Nav** oben, ab Folie 2 eingeblendet. Zeigt standardmäßig nur **voriges,
  aktuelles und nächstes Kapitel** – die volle Liste ist Orientierungslärm; der
  Knopf „Alle" klappt sie auf. Fortschrittsbalken an der Nav-Unterkante.
- **Druckbar:** `@media print` – im Druck werden alle Folien sichtbar geschaltet, Hintergründe erhalten (`print-color-adjust:exact`).
- **Barrierefrei** (wir auditieren Barrierefreiheit – die eigene Seite muss sauber sein): Kontrast ≥ 4.5, semantische `<section>`/`<h2>`-Struktur, `alt`-Texte an allen Screenshots, Fokuszustände.

## Zielgruppen-Anpassung (Vorgabe 6)
Vor dem Bauen `audience-profiles.md` lesen. Die **Sektionsreihenfolge, Wortwahl und Gewichtung** richten sich nach der Zielgruppe: z. B. *Marketing* → Conversion-Hebel & Copy nach vorn und ausführlich, technische WCAG-Details knapper; *Tech/Engineering* → Performance, Konsole, Code-nahe Empfehlungen betonen; *Entscheider* → Business-Impact, Roadmap, Aufwand/Wirkung. Der Hero-Untertitel und die Executive Summary benennen die Zielgruppe explizit.

## Vorgehen (Build)
1. `audience-profiles.md` + **`deck-content-schema.md`** lesen. `survey.json → brandColor`
   für die Cover-Farbe prüfen – **`brandCandidates` nach Score gegenlesen**, der
   Consent-Banner färbt die Erkennung gern falsch (pblift wurde auf 8/14 Seiten als
   Grün des Akzeptieren-Buttons statt als Markenrot erkannt).
2. Assets nach `site/assets/` kopieren: Finding-Screenshots, Kundenlogo, `uxda.svg`,
   `logos/`, `gfx/`, Wettbewerber- und Inspirations-Bilder.
3. **`deck.json` schreiben** – nur Inhalt, nach `deck-content-schema.md`.
4. Bauen:
   `scripts/.venv/bin/python scripts/build_deck.py audits/<domain>-<datum>/deck.json --out audits/<domain>-<datum>/site/index.html`
5. Preview-Server starten, Folien gegenlesen (Cover-Farbe korrekt? Bilder da? Läuft eine
   Folie über? Reihenfolge nach Schweregrad?). Inhaltliche Fehler in der `deck.json`
   beheben und neu bauen – **nicht** die `index.html` von Hand nachbearbeiten, sonst ist
   der nächste Build wieder anders.
6. Nutzer den Pfad `audits/<domain>-<date>/site/index.html` nennen.

## Prinzipien
- **Beleg statt Behauptung**, **nie erfundene Zahlen** – gilt unverändert (siehe SKILL.md). Kennzahlen nur aus `survey.json`.
- **Ein Finding = ein Block mit genau einem Screenshot.**
- Optik = New Monday (Teal/Coral/Neutrals, Rethink/Inter). Nur die **Cover-Sektion** trägt die Kundenfarbe.
