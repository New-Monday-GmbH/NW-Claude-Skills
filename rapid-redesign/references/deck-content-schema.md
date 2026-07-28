# deck.json – der einzige Ort, an dem ein Audit Inhalt schreibt

Das Deck wird **nicht mehr von Hand als HTML geschrieben.** Du schreibst eine
`deck.json` (Texte + Bildpfade), das Build-Skript setzt daraus die `index.html`
zusammen:

```bash
scripts/.venv/bin/python scripts/build_deck.py audits/<domain>-<datum>/deck.json \
  --out audits/<domain>-<datum>/site/index.html
```

Damit sind CSS, Layout, Deck-Navigation und Admin-Modus **kein Thema mehr** – sie
kommen aus `references/site-styles.css`, `templates/` und
`references/admin-mode-snippet.html`. Jedes Audit sieht dadurch gleich aus.

> **Fehlt ein Pflichtwert, bricht der Build ab** – mit Angabe von Folie und Key.
> Das ist Absicht: lieber ein Fehler als eine stille Lücke im Kunden-Deck.

### Was du NICHT schreibst

Diese Werte leitet `scripts/deck_content.py` ab. Von Hand gepflegt wären sie eine
stille Fehlerquelle – schreib sie nicht in die `deck.json`:

| Feld | wird abgeleitet aus |
|---|---|
| `persona.anzahl` (`data-count`) | Länge von `personas` – eine falsche Zahl würde das Grid brechen, ohne dass der Build meckert |
| `findings[].stufe_text` („Kritisch"…) | `findings[].stufe` (`crit`/`high`/`mid`/`low`) |

## Grundgerüst

```json
{
  "client": {
    "name":   "worksdone",
    "domain": "worksdone.de",
    "farbe":  "#512ffc",
    "farbe2": "#2a17b0",
    "ink":    "#fff"
  },
  "datum": "Juli 2026",
  "nav": [
    {"ziel": "ueber-nm", "titel": "Über uns"},
    {"ziel": "findings", "titel": "Findings"}
  ],
  "slides": [
    {"type": "cover", "...": "..."},
    {"type": "agenda", "...": "..."}
  ]
}
```

- **`client.farbe` / `farbe2`** – Primärfarbe der auditierten Firma (aus
  `survey.json → brandColor`; `brandCandidates` nach Score gegenprüfen, der
  Consent-Banner färbt die Erkennung gern falsch). `farbe2` ist die dunklere
  Variante für den Verlauf. **Das sind die einzigen Farben, die ein Audit setzt.**
- **`client.ink`** – `#fff` oder `#0b1416`, je nachdem was auf der Kundenfarbe
  ≥ 4.5:1 erreicht.
- **`nav`** – Mini-Nav oben. `ziel` = `id` einer Folie.
- **`slides`** – Reihenfolge = Foliennfolge. Jeder Eintrag braucht `type`.

## Werte dürfen Inline-HTML enthalten

Alle Texte werden **roh** eingesetzt. `<b>`, `<i>`, `<code>`, `<br>` sind erlaubt
und erwünscht – so entstehen die Hervorhebungen im Deck:

```json
"text": "Das Tracking ist auf <b>21 von 28 Seiten</b> defekt (<code>net::ERR_FAILED</code>)."
```

Kaufmanns-Und im Fließtext als `&amp;` schreiben.

## Folientypen

Legende: `#key` = Liste, `.` = Listeneintrag ist ein einfacher String.
Alles ohne `?` ist Pflicht.

| type | Keys | Anmerkung |
|---|---|---|
| `cover` | `bild`, `alt`, `titel`, `domain`, `datum` | `bild` = Kundenlogo (`assets/client-logo.*`). Wird per CSS weiß eingefärbt. `titel` ist immer „Rapid Redesign". |
| `agenda` | `#punkte` (Strings) | **In der Regel weglassen.** Ein Deck mit Deck-Navigation braucht kein Inhaltsverzeichnis. Nur auf Wunsch. |
| `ueber-nm` | — | **Fix.** `{"type":"ueber-nm"}` genügt. |
| `credibility` | — | **Fix** (Kundenlogo-Wand). |
| `ueber-projekt` | `titel`, `absatz1`, `absatz2`, `#punkte` | `titel` = Domain. Der teal Kernsatz ist **fix** im Template („Im Rapid Redesign analysieren wir die Webseite ganzheitlich mit Blick auf die Zielgruppenausrichtung.") — kein `statement`-Feld mehr. |
| `redesign-fokus` | `kicker`, `titel`, `#ziele`, `wirkung` | |
| `vorgehen` | — | **Fix** (6 Schritte als Kacheln, Inhalt direkt sichtbar — kein Aufklappen). |
| `summary` | `kicker`, `titel`, `lead`, `#punkte{titel,text}` | **Knapp halten: ein fetter Titel + EIN Satz je Punkt.** Bullets stehen 1-spaltig **untereinander** (keine Grafik). Das Detail steht in den Findings — hier in 20 Sekunden erfassbar. |
| `staerken` | `kicker`, `titel`, `untertitel`, `#punkte{label,text}` | **In der Regel weglassen** — die Stärken kommen als `gut` („Was gut funktioniert") mit Belegen ohnehin nochmal. |
| `scope` | `kicker`, `titel`, `zahlen_hinweis?`, `#kategorien{key,label,sub}`, `#findings{...,kategorie,beleg}` | **Die Zahlen werden GEZAEHLT, nicht geschrieben.** `kategorien` definiert die Kacheln; jeder Befund traegt `kategorie` (muss ein `key` sein - sonst Build-Fehler) und `beleg` (der Messwert, der ihn traegt). Der Build setzt `zahl` = Anzahl der Befunde je Kategorie und zeigt die Belege an der Kachel UND gesammelt im Detail-Bereich - damit ist jede Zahl nachweisbar. Die Detail-Findings liegen als Accordion auf derselben Folie - **keine separate `findings`-Folie**. |
| `divider` | `id?`, `kicker`, `titel`, `text` | Teal-Band. `titel` im Format „‹Ziel› durch ‹Mittel›". |
| `persona` | `kicker`, `titel`, `#personas{...}` | **Standard: 2–3 Personas.** **JEDE Persona braucht die vollen Felder** `bild,alt,name,rolle,zitat,#ziele,#beduerfnisse,#motivation,#frustrationen` **UND** `kurz` (Einzeiler) – denn jede kann Fokus werden. Die **erste** ist die Fokus-Persona (voll ausgeklappt, „Unser Fokus"), die übrigen erscheinen als Karten. Der Build rendert **alle** vor (Fokus- **und** Karten-Form) und blendet per `hidden` nur die Auswahl ein → im **Admin-Modus** lässt sich die Fokus-Persona per Klick umschalten. Fokus im Intake wählen (`audit-intake.md`). |
| `jtbd` | `titel`, `#funktional`, `#emotional` | **Direkt nach der `persona`-Folie.** 1:1 nach RR-Figma (`3856-860`): zwei Karten „Funktionale Jobs" / „Emotionale Jobs", je **genau 3 Aussagen** (kurze Sätze mit Punkt). Kein `kicker` — die Folie führt mit dem großen Titel. **Jobs aus der Fokus-Persona ableiten**, nie Beispieltexte übernehmen; `personaVarianten` empfohlen. |
| `positionierung` | `kicker`, `titel`, `claim`, `#aspekte{titel,text}` | Drei Aspekt-Kacheln **links gestapelt**, Grafik (`aspekte.svg`) **rechts**. Nummerierung kommt automatisch. |
| `erkenntnis` | `id`, `nummer`, `bereich`, `titel`, `#absaetze`, **entweder** `console{#fehler,#warnungen?,cap}` **oder** `browser{url,bild,alt}` | Eine Folie je Erkenntnis. Genau **einen** Beleg-Typ setzen. `warnungen` ist eine Liste (0, 1 oder mehrere). |
| `gut` | `kicker`, `titel`, `#punkte`, `browser{url,bild,alt}` | Max. 3 Punkte – sonst zweite Folie. |
| `wettbewerber` | `id`, `nummer`, `titel`, `url`, `bild`, `alt`, `#gut`, `#schlecht` | Eine Folie je Wettbewerber. „Macht gut" + „Macht schlechter" stehen **untereinander links**, der Screenshot **rechts**. |
| `inspiration` | `id`, `nummer`, `quelle`, `titel`, `text`, `#shots{bild,alt,bildtext}` | **Eine Quelle pro Folie, max. 3 Folien.** Von dieser einen Seite 3 Sektionen abfotografieren (Hero + 2 weitere). Die **Bilder stehen im Vordergrund** - gross, ohne Browser-Rahmen; der Text ordnet nur ein. **Quellen IMMER frisch aus Branche/Kontext des auditierten Produkts recherchieren** - die Beispiele des Demo-Decks (Linear, Pitch) sind Platzhalter und duerfen NICHT reflexhaft uebernommen werden; sie sind nur zulaessig, wenn sie fuer genau dieses Produkt nachweislich die beste Referenz sind (Begruendung im Text). |
| `findings[]` (in `scope`) | `stufe,ueberschrift,brille,beobachtung,wirkung,empfehlung, console{#zeilen,cap} \| shot{bild,alt,portrait?}` | **Keine eigene Folie mehr** — die Detail-Findings liegen als `findings[]` **auf der `scope`-Folie** (dezentes Accordion). `stufe` = `crit`/`high`/`mid`/`low` – das Label („Kritisch"/„Hoch"/…) wird **daraus abgeleitet**, nicht mitgeschrieben. `portrait: true` für Hochkant-Screenshots. Die eigenständige `findings`-Folie (mit `kicker,titel,zweispaltig?`) existiert noch im Katalog, wird aber standardmäßig nicht mehr gebaut. |
| `roadmap` | `kicker`, `titel`, `quick_wins{titel,untertitel,#punkte}`, `massnahmen{titel,untertitel,#punkte}` | |
| `wireframe` | `id`, `titel`, `skizze`, `ausrichtung?`, `#notizen` | **Mindestens ZWEI Wireframe-Folien je Deck** (Startseite + wichtigste Unterseite). `ausrichtung` = ein Satz, worauf der Entwurf ausgerichtet ist (Fokus-Persona) - sinnvollerweise ueber `personaVarianten`. `notizen` = was besser wird, in der Sprache des Publikums - ueber `publikumVarianten`. **Beide Achsen duerfen hier gleichzeitig gesetzt sein**: der Build rendert die Kombination (aussen Publikum, innen Persona), beide Admin-Schalter wirken unabhaengig. `skizze` = roher HTML-Block (siehe unten). |
| `nextsteps` | `kicker`, `titel`, `#ziele`, `#ergebnisse`, `#eckdaten{label,wert}`, `fussnote` | **`eckdaten` sind GENAU zwei Karten: „Dauer" + „Investition (Richtwert)".** Keine weiteren Karten erfinden (kein „Ihr Aufwand", kein „Start", kein „Team") — alles andere gehört, wenn überhaupt, in `ziele`/`ergebnisse` oder die `fussnote`. |
| `projektablauf` | `#phasen{phase,woche,ziel,#punkte}` | **3 Phasen** (Figma-Layout): Titel „Projektablauf", teal Label „Geschätzter Zeitraum"; je Phase Name (teal, über der Achse), „Woche X–Y", Ziel + Bullet-Liste. Achse mit Ticks am Spaltenanfang + Pfeil rechts. |
| `closing` | — | **Fix** (Danke + Footer). |

### Per-Persona-Textvarianten (`personaVarianten`)

**Jede** Folie kann zusätzlich `"personaVarianten": {"1": {…}, "2": {…}}` tragen
(Schlüssel = Persona-Index aus der `persona`-Folie; die Basisfelder der Folie
sind Variante 0 = Fokus-Persona des Builds). Die Overrides ersetzen nur die
genannten Felder (z. B. `titel`, `text`, `#ziele`, `wirkung`). Der Build rendert
die Folie dann **je Persona einmal** und packt alle Varianten in **eine**
`<section>` (`div.pv[data-persona-variant]`, Nicht-Fokus `hidden`) – der
Fokus-Persona-Schalter im Admin-Modus wechselt so **die Texte gleich mit**.
Empfohlen für die persona-geprägten Folien: Zielsatz-Divider, `redesign-fokus`,
Erkenntnis-Divider. **Nicht** für Agentur-Folien und die Publikums-Ansprache
(die hängen an der Zielgruppe der Präsentation, nicht an der Persona).

### Per-Publikum-Textvarianten (`publikumVarianten`)

Dasselbe Muster für das **Publikum** (wem wir präsentieren — nicht die
Website-Persona!): Top-level im Deck steht
`"publikum": {"aktiv": "<key>", "optionen": [{"key","label"}, …]}` (aktiv =
die im Intake gewählte Zielgruppe). Eine Folie kann dann
`"publikumVarianten": {"<key>": {…Overrides…}}` tragen; die Basisfelder sind
die Fassung fürs aktive Publikum. Wrapper: `div.av[data-audience-variant]`
mit `data-audience-label` — der **Publikum:-Schalter** in der Admin-Toolbar
liest Optionen und Zustand direkt aus dem DOM und wechselt die Texte um.
Empfohlen für publikums-geprägte Folien: `summary`, ggf. `nextsteps`.
**Beide Achsen auf derselben Folie** sind seit dem Wireframe-Umbau erlaubt: der Build
rendert dann die Kombination (außen Publikum, innen Persona), beide Admin-Schalter wirken
unabhängig. Sparsam einsetzen — die Zahl der Renders ist das Produkt beider Achsen.

### Wireframe-Vokabular (`skizze`)

Der einzige Ort, an dem ein Audit rohes HTML schreibt – weil die Skizze echt
projektspezifisch ist. Nutze **nur** diese Klassen (sie sind im kanonischen
Stylesheet definiert), erfinde keine neuen:

```html
<div class="hero">
  <div>
    <div class="h-title w1"></div><div class="h-title w2"></div>
    <div class="h-sub"></div>
    <div class="primary"></div>
    <div class="trust"><i></i><i></i><i></i></div>
  </div>
  <div class="mock">Beschriftung, was hier steht</div>
</div>
<div class="consent">
  Consent als schmales Band am unteren Rand
  <div class="btns"><span class="b1">Akzeptieren</span><span class="b2">Essenzielle</span></div>
</div>
```

Die Kopfzeile (`.wf-nav` mit Logo/Nav/CTA) setzt die Vorlage selbst – nicht in
die `skizze` schreiben.

## Vorlagen ändern

Alle Folien-Vorlagen liegen in `templates/slides/<type>.html`, Kopf und Fuß in
`templates/deck.head.html` / `templates/deck.tail.html`. Eine Änderung dort wirkt
auf **jedes künftige Deck**. Syntax der Vorlagen: siehe Kopf von
`scripts/deck_render.py` (mustache-lite: `{{key}}`, `{{key?}}`, `{{#liste}}`,
`{{^liste}}`, `{{@index2}}`).

Nach einer Vorlagen-Änderung prüfen, dass das Referenz-Deck noch reproduziert wird:

```bash
scripts/.venv/bin/python scripts/build_deck.py audits/worksdone.de-2026-07-16/deck.json --out /tmp/probe.html
```

`audits/worksdone.de-2026-07-16/deck.json` ist das **Referenz-Deck**: Es erzeugt
exakt die freigegebene Präsentation und ist zugleich das beste Beispiel dafür,
wie eine gefüllte `deck.json` aussieht.
