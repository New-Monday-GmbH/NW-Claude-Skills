---
name: rapid-redesign
description: Erstellt ein New-Monday-Rapid-Redesign: ein UX/UI- und Usability-Audit der GANZEN Website inkl. aller Unterseiten (echter Browser via Playwright), mit einem Screenshot je Finding, einer strategischen Conversion- und Copy-Einschaetzung und als Ergebnis einem fertigen Folien-Deck (lokale Website) im Rapid-Redesign-Stil - zugeschnitten aufs Publikum (Marketing, Geschaeftsfuehrung, Tech, Design), Cover in der Markenfarbe der auditierten Firma. Nutze diesen Skill, wenn eine Website, Landingpage, ein Webshop oder Onlineauftritt bewertet, geprueft oder auditiert werden soll - auch ohne das Wort Audit: Usability, Barrierefreiheit/WCAG, Nielsen-Heuristiken, Mobile/Responsive, SEO und GEO, Conversion-Potenzial oder Qualitaet der Texte. Beispiele: "Rapid Redesign fuer example.com", "Pruef mal unsere Website", "Was ist an dieser Seite schlecht?", "Wie kann ich die Conversion erhoehen?", "UX-Review fuer Kunde X".
---

# Rapid Redesign — UX/UI-Audit-Skill

Dieser Skill produziert einen **expertengeführten UX/UI-Audit** einer Website – standardmäßig über die **ganze Website inkl. ALLER Unterseiten**, nicht nur die Startseite. Playwright liefert das Rohmaterial (Screenshots über mehrere Viewports, DOM-/Accessibility-Daten, Kontraste, Tap-Targets, CTA-/Copy-Texte, Konsolenfehler, erkannte Markenfarbe). Die Bewertung machst **du** auf zwei Ebenen:

- **Strategische Ebene (weniger technisch):** Conversion-Hebel und inhaltliche Qualität der Texte/Überschriften – das, was Entscheider:innen interessiert. Siehe `references/conversion-content.md`.
- **Technische Ebene:** fünf Prüf-Brillen (Nielsen, WCAG, Visuell, Mobile, Informationsarchitektur & Seitenstruktur) mit konkreten Findings. Siehe `references/audit-frameworks.md`.

Jedes technische Finding bekommt **genau einen fokussierten Screenshot**. Das Endergebnis ist eine **lokale, statische Website als Folien-Deck** (eine Sektion pro Ansicht, Weiter/Zurück, kein Build) auf Deutsch, aufgebaut und gestaltet wie eine New-Monday-**Rapid-Redesign-Präsentation**: Sie öffnet mit einer Cover-Sektion in der **Markenfarbe der auditierten Firma**, führt in die strategische Einschätzung und dann in die Detail-Findings.

Zielgruppe der Ergebnisse: Kund:innen und Entscheider:innen. Ton: konkret, wertschätzend, lösungsorientiert – nie Fehler-Schelte, sondern „Beobachtung → Wirkung → Empfehlung". **Der Schwerpunkt richtet sich nach der Person, der wir es vorstellen** (Marketing, Tech, Entscheider:in, Design – siehe `references/audience-profiles.md`).

## Ablauf (immer in dieser Reihenfolge)

### 0. Zwei Verzeichnisse auseinanderhalten (wichtig)
Der Skill kann überall installiert sein (`~/.claude/skills/rapid-redesign`, Projekt-Skill, Plugin). Merke dir zu Beginn **beide** Orte:

- **`$SKILL`** = der Ordner, in dem **diese SKILL.md** liegt. Dort liegen `scripts/`, `references/`, `templates/`. **Nie hart kodieren** – nimm den Pfad, unter dem du diese Datei geladen hast.
- **Arbeitsverzeichnis** = das Projekt des Nutzers. **Dort** entsteht `audits/<domain>-<datum>/` mit Rohmaterial, Findings und dem fertigen Deck.

```bash
SKILL="<Ordner dieser SKILL.md>"     # z. B. ~/.claude/skills/rapid-redesign
```
Alle Skript-Aufrufe unten nutzen `$SKILL`; alle `--out`-Pfade bleiben **relativ zum Arbeitsverzeichnis**.

### 1. Setup prüfen
Playwright muss installiert sein (Chromium wird mitgeliefert). Einmalig **pro Rechner**:
```bash
bash "$SKILL/scripts/setup.sh"
```
Das installiert `playwright` + Chromium in eine venv unter `$SKILL/scripts/.venv` (per `uv`, ohne Admin-Rechte). Existiert sie schon **und** ist Playwright drin, überspringen. Die venv wird **nicht** mitverteilt – sie ist maschinenspezifisch.

### 2. Intake – kurz klären, wofür der Audit ist
Führe zu Beginn ein **kurzes** Intake durch (per `AskUserQuestion`, sonst als Rückfrage). Details: **`references/audit-intake.md`**. Geklärt wird:
1. **Zielgruppe** (Marketing/Growth · Tech/Engineering · Entscheider:in/GF · Design/Product) → bestimmt Schwerpunkt, Reihenfolge und Sprache (`references/audience-profiles.md`).
2. **Fokus-Persona bestätigen** (wenn die Persona-Sektion gebaut wird — siehe `audit-intake.md`).

**Sektions-Umfang: standardmäßig ALLES.** Es wird das **volle Programm** gebaut (alle Strategie-/Kontext- und Abschluss-/Angebots-Sektionen) — **ohne** Checklisten-Abfrage. Nur ein kurzer Hinweis im Intake: „Ich baue das komplette Deck — sag Bescheid, falls Sektionen rausfallen sollen." **Wettbewerber:** alle relevanten selbst recherchieren und **alle erfassen** (echte Screenshots), ohne Auswahl-Rückfrage — die Liste wird im Ergebnis genannt, kürzen kann man im Admin.

Immer dabei: Cover, die feste Intro-Sequenz (RR-Slides 3–7), Executive Summary, Scope, Roadmap, Abschluss. „Über das Projekt" und „Redesign-Fokus" werden projektspezifisch getextet.

### 3. Seiten festlegen (Site-Crawl – ALLE Seiten)
Standardmäßig die **ganze Website** auditieren. Zuerst alle Unterseiten entdecken (Sitemap/robots.txt + Link-BFS):
```bash
"$SKILL/scripts/.venv/bin/python" "$SKILL/scripts/audit_capture.py" crawl "<START-URL>" --out "audits/<domain>-<YYYY-MM-DD>"
```
Liefert `crawl.json` mit allen internen Seiten. **Es werden alle gefundenen Seiten auditiert**, nicht nur eine Auswahl. Nur wenn die Website sehr groß ist (z. B. > 40 Seiten oder ein Shop mit hunderten Produktseiten), mit dem Nutzer abstimmen, ob repräsentative Vertreter je Seitentyp genügen – und das transparent machen. (Optionen: `--depth`, `--max-pages`.)

### 4. Rohmaterial erfassen (Survey pro Seite)
Für **jede** Seite aus `crawl.json` (plus die Startseite):
```bash
"$SKILL/scripts/.venv/bin/python" "$SKILL/scripts/audit_capture.py" survey "<URL>" --out "audits/<domain>-<YYYY-MM-DD>/pages/<slug>"
```
Erfasst pro Viewport (Desktop 1440px + Mobile 390px): Full-Page- und Above-the-fold-Screenshot, außerdem `survey.json` mit Headings-Struktur, **CTA-Labels**, **Fließtext-Absätzen**, fehlenden Alt-Texten, Kontrast-Kandidaten (WCAG-Ratio), zu kleinen Tap-Targets, Formularfeldern ohne Label, `<title>`/Meta/`lang`, Viewport-Meta, Konsolenfehlern **und der erkannten Markenfarbe** (`brandColor` + `brandCandidates`). Lies danach `survey.json` und sieh dir die Screenshots an. Die **Markenfarbe der Startseite** ist maßgeblich für die Cover-Sektion (Schritt 9).

### 5. Strategisch bewerten (Conversion & Content)
Lies **`references/conversion-content.md`** und leite die **übergeordnete Einschätzung** ab: Conversion-Hebel (Above-the-fold-Klarheit, CTA-Klarheit/-Konsistenz, Reibung, Trust, Einwände, Preis-Transparenz) und Content/Copy (Nutzen statt Funktion, Klarheit, Messaging-Hierarchie, Zielgruppen-Fit, Beweis, Scanbarkeit). Betrachte das **Zusammenspiel aller Seiten** (Funnel-Logik, Konsistenz, Seiten-Rollen, Lücken). Gewichte gemäß **Zielgruppe** (`references/audience-profiles.md`). Ergebnis: 3–6 priorisierte Conversion-Hebel + ein knapper Copy-Check je Kernseite.

### 6. Technisch auditieren (sechs Dimensionen)
Lies **`references/audit-frameworks.md`** und prüfe die Seiten über die **sechs Prüf-Dimensionen** – dieselben, die die Scope-Folie zählt:
1. **Usability** – Nielsen-Heuristiken, Flüsse, Reibung; **dazu Informationsarchitektur & Seitenstruktur** (Brille 5): Navigationsaufbau, nutzerfreundliche Link-Beschriftungen, Seitenaufbau passend zur Zielgruppe
2. **Barrierefreiheit** – WCAG 2.1 AA (Kontrast, Labels, Trefferflächen, Semantik, Fokus)
3. **Copy-Text** – Klarheit, Nutzen statt Funktion (**Features vs. echte Lösungen — pro Kernseite explizit prüfen**), Messaging-Hierarchie (aus Schritt 5)
4. **UI-Design** – visuelle Konsistenz, Hierarchie, Spacing, Zustände
5. **SEO** – `<title>`/Meta-Description, H1/Heading-Struktur, Dubletten, interne Verlinkung
6. **GEO** – Auffindbarkeit für generative KI-Suche: semantisches HTML, strukturierte Daten, eindeutige Aussagen, `llms.txt`

Mobile/Responsive wird dabei **quer über alle Dimensionen** geprüft (beide Viewports aus Schritt 4).

Kalibriere Anspruch und Wortwahl an den Beispielen in **`examples/good/`** und **`examples/bad/`** (siehe `examples/README.md`). Sind noch keine Beispiele vorhanden, halte dich strikt an das Finding-Template in `references/finding-workflow.md`.

> **Detail-Findings müssen ALLE Dimensionen abdecken – nicht nur Barrierefreiheit.** Das ist ein häufiger Fehler: das Set kippt in ein reines WCAG-Thema. Vor dem Texten prüfen: Ist je Dimension (Usability, Barrierefreiheit, Copy, UI-Design, SEO, GEO) etwas Konkretes dabei? **Ohne Deckelung** erfassen – die Capture-Caps liegen bei 600 (nicht 40). Die **Detail-Findings liegen als `findings[]` auf der `scope`-Folie** (dezentes Accordion), es gibt **keine separate Findings-Folie** mehr. Die Scope-Kacheln fassen Usability + Barrierefreiheit + Copy + UI-Design zu **einer** Kategorie zusammen, daneben **SEO** und **GEO**.

Qualität vor Quantität: Lieber 8–15 belastbare, gut belegte Findings als 40 oberflächliche. Markiere Findings, die **site-weit** auftreten, als solche – das erhöht ihre Priorität. Jedes Finding muss auf dem Screenshot **sichtbar nachvollziehbar** sein.

### 7. Pro Finding einen Screenshot erzeugen
Für jedes Finding einen fokussierten, hervorgehobenen Screenshot des betroffenen Elements:
```bash
"$SKILL/scripts/.venv/bin/python" "$SKILL/scripts/audit_capture.py" shot "<URL>" \
  --selector "<CSS-Selektor>" --viewport desktop --highlight \
  --out "audits/<domain>-<YYYY-MM-DD>/findings/f01.png"
```
`--highlight` rahmt das Element rot ein und scrollt es in den Sichtbereich. Ohne verlässlichen Selektor: `--region "x,y,w,h"` oder `--fold`. Nummeriere passend zu den Findings (`f01`, `f02`, …).

### 8. Findings dokumentieren
Schreibe `audits/<domain>-<YYYY-MM-DD>/findings.md`: zuerst die **strategische Einschätzung** (Conversion-Hebel + Copy-Check), dann die technischen Findings nach dem Template in `references/finding-workflow.md` (Titel, Brille/Heuristik, Schweregrad, Beobachtung, Wirkung, Empfehlung, Screenshot). Dazu ein Executive Summary mit den 3–5 wichtigsten Punkten, dem geprüften Seiten-Umfang (alle Seiten) und der Zielgruppe.

### 9. Ergebnis-Deck bauen (Rapid-Redesign-Stil)

> **Du schreibst kein HTML.** Das Deck entsteht aus einer `deck.json` (nur Texte und
> Bildpfade) plus fertigen Vorlagen. Struktur, CSS, Deck-Navigation und Admin-Modus
> sind bei jedem Audit identisch und werden **nicht** pro Projekt neu erfunden.

1. Lies **`references/deck-content-schema.md`** (Feldreferenz) und **`references/website-build.md`**
   (Sektions-Katalog: welche Folie wann, was gehört drauf).
2. Assets nach `audits/<domain>-<datum>/site/assets/` kopieren (Screenshots, Kundenlogo,
   `uxda.svg`, `logos/`, `gfx/`).
3. **`deck.json` schreiben** – der einzige Ort, an dem du Inhalt produzierst.
4. Bauen:
   ```bash
   "$SKILL/scripts/.venv/bin/python" "$SKILL/scripts/build_deck.py" audits/<domain>-<datum>/deck.json \
     --out audits/<domain>-<datum>/site/index.html
   ```
5. Preview-Server starten und die Folien gegenlesen (Cover-Farbe? Bilder da? Läuft eine
   Folie über?). Fehler **in der `deck.json`** beheben und neu bauen – die `index.html`
   ist ein Artefakt, kein Arbeitsdokument.

Leitplanken, die dabei gelten:
- **Folien-Deck, kein Onepager:** eine Sektion pro Ansicht. **Eine Folie = ein Gedanke** –
  lange Inhalte splitten (je Erkenntnis/Wettbewerber eine eigene Folie).
- **Cover in der Markenfarbe der auditierten Firma** (`client.farbe`/`farbe2` aus
  `survey.json → brandColor`). **`brandCandidates` nach Score gegenlesen** – ein grüner
  Consent-Button färbt die Erkennung gern falsch. Alle übrigen Folien: New-Monday-Teal.
- **Zielgruppen-Anpassung** (Schritt 2) bestimmt Reihenfolge, Wortwahl und Detailtiefe.
- **Auf die Fokus-Persona zuschneiden:** Ist die Persona-Sektion dabei, wird **vor dem Bau** die Fokus-Persona bestätigt (2–3 Personas, `audit-intake.md`). Diese Persona zieht sich sichtbar durchs Deck – Zielsatz-Divider, strategische Erkenntnisse und Redesign-Fokus argumentieren aus **ihrer** Sicht (Ziele/Frustrationen), damit erkennbar ist, dass das Projekt auf sie zugeschnitten wurde. **Nicht verwechseln:** Die *Zielgruppe* aus Intake-Frage 1 (wem wir präsentieren: Marketing/GF/…) steuert Sprache und Reihenfolge des Decks; die *Fokus-Persona* ist die Website-Zielgruppe, für die redesignt wird.
- **Persona-Varianten mitliefern (`personaVarianten`):** Für die persona-geprägten Folien (Zielsatz-Divider, `redesign-fokus`, ggf. Erkenntnis-Divider) je weiterer Persona Text-Overrides in die `deck.json` schreiben (`deck-content-schema.md`). Der Build rendert dann alle Varianten vor, und im **Admin-Modus wechseln die Texte mit**, wenn die Fokus-Persona umgeschaltet wird. Die Agentur-Folien bleiben dabei immer gleich.
- **KEINE Umsetzungs-Anweisungen auf den Folien** (außer bei Publikum Tech): Executive Summary, Erkenntnisse, „Was gut funktioniert", Roadmap und Next Steps beschreiben die **Wirkung** in der Sprache des Publikums — technische Anweisungen (`hreflang`, `for`/`id`, `301`, `44px`, Kontrast-Ratios, Finding-IDs) gehören **ausschließlich** in die aufklappbaren Detail-Findings unter „Was wir geprüft haben". Verbotsliste, Übersetzungstabelle und Selbst-Check: **`references/audience-profiles.md` → „Übersetzungspflicht"**. Für Marketing heißt das konkret: Was erlebt/übersieht/fürchtet der Besucher, und wo im Funnel kostet das Abschlüsse — Emotion und Motiv der Zielgruppe sind hier erwünschte Argumente.
- **Publikums-Varianten mitliefern (`publikumVarianten` + `publikum`):** Auch das **Publikum** (wem wir präsentieren) ist im Admin umschaltbar. Top-level `"publikum": {aktiv, optionen}` mit **allen vier Zielgruppen** setzen (`marketing`, `gf`, `tech`, `design`; `aktiv` = Intake-Wahl) und für publikums-geprägte Folien — **Executive Summary, Erkenntnisse, „Was gut funktioniert", Roadmap, Next Steps** — je weiterem Publikum Overrides schreiben. Der Admin bekommt dann automatisch den Schalter „Publikum:" in der Toolbar, mit dem sich das ganze Deck umstellen lässt. Nie mit `personaVarianten` auf derselben Folie kombinieren.
- **Detail-Findings decken alle sechs Dimensionen ab** (Schritt 6) – nicht nur Barrierefreiheit.
- **Jede Zahl auf der Scope-Folie ist belegt — der Build zählt sie.** Nie eine Summe hinschreiben, die sich nicht nachweisen lässt. Die Scope-Folie bekommt `kategorien` (key/label/sub); jeder Befund in `findings` trägt `kategorie` + `beleg` (der Messwert, der ihn trägt). Der Build zählt die Befunde je Kategorie und zeigt die Belege direkt an der Zahl und noch einmal gesammelt im Detail-Bereich. **Auch qualitative Befunde zählen** (z. B. „Dokumentation ohne Suche — 22 Kapitel nur durchklickbar"): Was auf einer Erkenntnis-Folie steht, **muss** als Befund in `findings` auftauchen, sonst behauptet die Scope-Folie eine Zahl, die die Erkenntnisse nicht abbildet.
- **Mindestens ZWEI Wireframes** („Unser Vorschlag"), typischerweise Startseite + wichtigste Unterseite. Jeder Wireframe nennt in `ausrichtung`, **worauf er ausgerichtet ist** (Fokus-Persona), und begründet in `notizen`, was besser wird. Beides ist variantenfähig: `personaVarianten` für die Ausrichtung, `publikumVarianten` für die Notizen — der Build rendert die Kombination, beide Admin-Schalter wirken unabhängig.
- **Figma-Frame 1:1 übernehmen — immer mit Subagent-Abgleich:** Gibt der Nutzer einen Figma-Link für eine Folie/Sektion, nicht nur das iframe-Embed nutzen, sondern die Folie **nativ nachbauen** (Design-Tokens aus `site-styles.css`) und die **Texte auf das aktuelle Projekt anpassen** (Platzhalter/fremde Firmennamen raus). Danach **einen Prüf-Subagenten starten** (Agent-Tool), der den Figma-Screenshot (`get_screenshot` des Nodes) mit einem Browser-Screenshot der gebauten Folie vergleicht — Layout, Abstände, Ausrichtungen, Farben, Typo-Hierarchie — und Abweichungen konkret meldet; beheben und erneut prüfen lassen, bis es 1:1 sitzt. Im Admin sitzt der Figma-Import als Eintrag **„Figma-Frame (1:1-Import)" im „＋ Abschnitt"-Katalog** — die eingefügte Folie ist ein normaler Abschnitt (verschieb-/löschbar, Übersicht-Drag). Mit **Figma-Token** (einmalig abgefragt, lokal gespeichert) importiert er den Frame **1:1 als Bild-Folie** über die offizielle Figma-Render-API (pixelgenau, ohne Figma-UI, als data-URL eingebacken → exportfest; Frame-Footer auf Nachfrage abgeschnitten, damit die Folie zu den übrigen passt). Ohne Token fällt er auf die randlose **Embed-Folie** zurück (`.figma-slide`, Figma-UI weggecroppt). Ein echter **nativer HTML-Nachbau** geht browserseitig technisch nicht (kein Zugriff auf die Figma-Designdaten) und läuft deshalb immer über den Skill.
- Alle Sektionen des vollen Programms bauen (außer der Nutzer hat welche abbestellt), in RR-Reihenfolge, mit Teal-Divider-Bändern
  zwischen den Gruppen.

Zum Schluss dem Nutzer den Pfad `audits/<domain>-<date>/site/index.html` nennen.

## Wichtige Prinzipien
- **Beleg statt Behauptung:** Jede Aussage stützt sich auf einen Screenshot oder eine Kennzahl aus `survey.json`.
- **Nie erfundene Zahlen.** Nutze nur, was gemessen wurde (Kontrast-Ratio, Tap-Target-Größe, Anzahl fehlender Alt-Texte). Keine erfundenen Conversion- oder Traffic-Zahlen – Conversion-Hebel als qualitative Richtung („senkt Reibung"), nicht als erfundene Prozente.
- **Wirkung übersetzen:** Immer erklären, *warum* etwas ein Problem für echte Nutzer:innen ist.
- **Respektvoll:** Es sind Verbesserungschancen, keine Anklagen.
- **Zielgruppengerecht:** Fakten bleiben vollständig, aber Schwerpunkt/Sprache passen sich der Zielgruppe an (nie Findings verschweigen).
- **Barrierefrei bauen:** Wir prüfen Barrierefreiheit – die eigene Ergebnis-Website muss selbst sauber sein (Kontrast, Semantik, Alt-Texte, Fokus).

## Dateien
| Datei | Wann lesen |
|-------|------------|
| `references/conversion-content.md` | Schritt 5 – strategische Ebene: Conversion-Hebel & Copy-Check |
| `references/audit-frameworks.md` | Schritt 6 – die fünf technischen Prüfraster mit Checklisten |
| `references/finding-workflow.md` | Schritt 6–8 – Schweregrade + Finding-Template |
| `references/audit-intake.md` | Schritt 2 – geführtes Intake (Zielgruppe + Sektionsauswahl), der „Chatbot" |
| `references/audience-profiles.md` | Schritt 2, 5, 9 – Zielgruppen-Schwerpunkt (Marketing/Tech/Entscheider/Design) |
| **`references/deck-content-schema.md`** | **Schritt 9 – Feldreferenz für die `deck.json`. Die einzige Datei, die du zum Texten des Decks brauchst.** |
| `references/website-build.md` | Schritt 9 – Sektions-Katalog: welche Folie wann, was gehört drauf |
| `references/design-system-newmonday.md` | Hintergrund – offizielle New-Monday-Tokens (Farben, Fonts, Spacing) |
| `examples/README.md` | Konvention für Good/Bad-Beispiele |
| `scripts/audit_capture.py --help` | Alle Capture-Optionen (`survey`, `crawl`, `shot`) |

### Bausteine des Decks (nicht von Hand anfassen)
Diese Dateien setzt `build_deck.py` automatisch ein. Sie sind der Grund, warum jedes
Audit gleich aussieht – ändere sie nur, wenn du das **Aussehen aller künftigen Decks**
ändern willst (danach Referenz-Deck neu bauen, siehe `website-build.md`).

| Datei | Rolle |
|-------|-------|
| `templates/slides/<type>.html` | Vorlage je Folientyp |
| `templates/deck.head.html` / `deck.tail.html` | Kopf (Fonts, `<style>`, Mini-Nav) / Deck-Navigation + Skript |
| `references/site-styles.css` | **kanonisches Stylesheet** – wird unverändert eingesetzt |
| `references/admin-mode-snippet.html` | Admin-/Edit-Modus |
| `scripts/deck_render.py` | Template-Engine (mustache-lite) |
| `scripts/deck_content.py` | abgeleitete Felder (Persona-Anzahl, Severity-Label) |
| `scripts/check_slide.py` | prüft eine Vorlage gegen eine Referenz-Folie |
| `audits/worksdone.de-2026-07-16/deck.json` | **Referenz-Deck** – erzeugt exakt die freigegebene Präsentation; bestes Beispiel für eine gefüllte `deck.json` |
