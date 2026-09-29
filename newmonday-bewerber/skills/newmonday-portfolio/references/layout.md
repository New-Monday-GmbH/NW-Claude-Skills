# Layout-Referenz

Seit September 2026 ist die Referenz die Figma-Seite **»Portfolio«** in der
Datei `Portfolio - CV Master` (fileKey `oezbaw261xDwxthPuX3ZpS`, Frame
`Portfolio`, Knoten `4158:7019`): 29 Folien im [NM] DESIGN SYSTEM v1.3. Alle
Positionen hier sind dort gemessen – per `use_figma`, nicht am Bildschirm
geschätzt. Wo der Skill bewusst von Figma abweicht, steht es dabei.

Ältere Maße aus den Referenzportfolios (Rolfes, Gottscheck, Hecker, Reis,
Schwertfeger) gelten nur noch dort, wo Figma den Fall nicht zeigt: die
einzelne Logoreihe bis fünf Logos, die KI-Folie mit ihrer Werkzeugreihe und
die Screenflächen.

## Design System: eine Quelle, eine Prüfung

**Farben, Textstile, Schriftdateien, Linien, Kartenradius und -abstände stehen
einmal, in `assets/tokens.json`.** Daraus erzeugt `scripts/design_tokens.py` beim
Rendern das CSS, das `portfolio.css` voraussetzt:

- `@font-face` für jeden Schnitt aus `schriftdateien`,
- `:root`-Variablen für Farben (`--brand-primary`, `--neutral-80` …), Maße
  (`--karte-radius` …), den Bildverlauf (`--bildschatten`) und die Linien
  (`--linie-karte`, `--linie-trenner` – je Stärke und Farbe als fertiger
  `border`-Wert; dazu `--karte-innen-gerahmt`, der um die Linie verkleinerte
  Innenabstand: Figma legt Konturen nach innen, die Karte wird nicht größer),
- je Textstil eine Klasse `.t-<name>` mit Familie, Schnitt, Grad,
  Zeilenhöhe und Laufweite.

`portfolio.css` enthält danach nur noch Layout. Jede Textstelle bekommt im
Renderskript ihre `.t-*`-Klasse. Zwei Prüfungen halten das dicht, beide laufen
bei jedem Rendern mit und melden sich unter „Design System:":

1. **`pruefe()`** liest `portfolio.css`: kein Hex-Wert, kein `rgb()`, keine
   Farbnamen, kein `font-family`/`font-size`/`font-weight`/`line-height`/
   `letter-spacing`, keine Variable, die `tokens.json` nicht kennt.
2. **`pruefe_pdf()`** liest das fertige PDF: Jede Textstelle muss einen
   Schnitt und Grad aus den Textstilen tragen (erlaubt sind außerdem die
   Ausweichgrade 84/72/64 der Arbeitsweise-Überschrift und `**fett**` in
   Inter Semi Bold). Ein Element ohne `.t-*`-Klasse fällt hier auf.

### Tokens gegen Figma prüfen

Ändert sich das Design System, wird die Figma-Seite ausgelesen und gegen die
Tokens gehalten. Das Leseskript (rein lesend, `use_figma`) sammelt die
Farbvariablen und Textstile der Seite:

```js
const seite = await figma.getNodeByIdAsync("4158:3775");      // Seite »Portfolio«
await figma.setCurrentPageAsync(seite);
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');
const farben = {}, textstile = {};
for (const n of seite.findAll(() => true)) {
  const farbflaechen = [].concat('fills' in n && Array.isArray(n.fills) ? n.fills : [],
                                 'strokes' in n && Array.isArray(n.strokes) ? n.strokes : []);
  for (const f of farbflaechen)
    if (f.boundVariables && f.boundVariables.color) {
      const v = await figma.variables.getVariableByIdAsync(f.boundVariables.color.id);
      if (v) farben[v.name] = hex(f.color);
    }
  if (n.type === 'TEXT') for (const s of n.getStyledTextSegments(['textStyleId'])) {
    if (!s.textStyleId || textstile[s.textStyleId]) continue;
    const st = await figma.getStyleByIdAsync(s.textStyleId);
    if (!st) continue;
    const lh = st.lineHeight.unit === 'PERCENT' ? Math.round(st.lineHeight.value) + '%' : st.lineHeight.value + 'pt';
    const ls = st.letterSpacing.unit === 'PERCENT' ? Math.round(st.letterSpacing.value * 100) / 100 + '%' : st.letterSpacing.value + 'pt';
    const gewicht = { Regular: 400, Medium: 500, 'Semi Bold': 600, SemiBold: 600, Bold: 700 }[st.fontName.style];
    textstile[st.id] = { name: st.name, familie: st.fontName.family, gewicht, groesse: st.fontSize, zeilenhoehe: lh, laufweite: ls };
  }
}
const stile = {}; for (const s of Object.values(textstile)) stile[s.name] = s;
return { farben, textstile: stile };
```

Das Ergebnis als `auszug.json` speichern, dann:

```bash
python3 scripts/design_tokens.py pruefe --figma auszug.json
```

Gemeldet wird jede Farbe und jeder Textstil (über das Feld `figma` in
`tokens.json` zugeordnet), der von Figma abweicht. Angepasst wird dann
`tokens.json` – und nur sie.

### Selbsttest gegen Figma

Die Tokens sagen, *welche* Werte es gibt – nicht, *wo* sie stehen. Ob eine
Karte eine Kontur hat, ob zwischen zwei Kenntnissen eine Linie läuft, welcher
Stil einen Kartentitel setzt: Das prüft der Selbsttest gegen die Vorlage.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/selbsttest.py
```

Für jede Datei in `assets/figma-soll/` rendert er die Folie mit **genau dem
Inhalt der Vorlage** (`inhalt` in der Datei, der Rest aus
`beispiel/portfolio.json`) und liest sie mit demselben Leser, der die
Figma-Frames baut (`figma_plan.folien_lesen`). Verglichen wird auf 1,5 pt:
jede Fläche mit Füllung, Kontur und Radius, jede Trennlinie, jedes Bild und
Logo, jeder Text mit Schnitt, Grad, Zeilenhöhe, Farbe und Lage – und
umgekehrt jede Fläche, die der Skill zeichnet und die Vorlage nicht kennt.
Linien (eine Kante ≤ 2 pt) werden in ihrer Stärke auf 0,1 pt verglichen.
Markierungen in der Soll-Datei, jeweils mit `grund`:

| Markierung | Wirkung | heute an |
|---|---|---|
| `"pruefen": false` | Eintrag wird nicht verglichen | Connect-Texte „LinkedIn Profil“/„Anzeigen“, unsichtbare weiße Linie in der Sprachen-Karte |
| `"nur": ["x", "y", "w"]` | nur diese Maße zählen | Connect-Karte (niedriger, weil Pfeil-Links) |
| `"vergleich": "mitte"` | verglichen wird die Mitte statt der linken oberen Ecke – für zentrierte Texte in einem größeren Kasten | Seitenzahl (setzt das Leseskript selbst) |

Die ersten beiden sind gewollte Abweichungen und werden nach dem Neulesen von
Hand wieder gesetzt; `vergleich` setzt das Leseskript bei zentrierten Texten.

Dazu prüft er die Tokens (`pruefe()`) und rendert das Beispiel-Deck
(`pruefe_pdf()`). Nach jeder Änderung an Layout, Tokens oder
`figma_plan.py` laufen lassen; er schreibt nichts in den Skill-Ordner.

**Wird eine Vorlage in Figma geändert**, die Sollwerte neu lesen – rein
lesend, Frame-ID anpassen:

```js
const FRAME = "4158:7033";                                   // 02 NM Portfolio - Profile V2
const root = await figma.getNodeByIdAsync(FRAME);
let pg = root; while (pg && pg.type !== "PAGE") pg = pg.parent;
await figma.setCurrentPageAsync(pg);
const ox = root.absoluteTransform[0][2], oy = root.absoluteTransform[1][2];
const hex = c => "#" + [c.r, c.g, c.b].map(x => Math.round(x * 255).toString(16).padStart(2, "0")).join("");
const r1 = v => Math.round(v * 10) / 10;
const sichtbar = ps => (ps && ps !== figma.mixed ? ps : []).filter(p => p.visible !== false && (p.opacity === undefined || p.opacity > 0));
const flaechen = [], texte = [], bilder = [], logos = [];
function lauf(n, grund) {
  if (n.visible === false) return;
  const t = n.absoluteTransform, x = r1(t[0][2] - ox), y = r1(t[1][2] - oy), w = r1(n.width), h = r1(n.height);
  if (n.type === "INSTANCE" && /Logo/i.test(n.name)) { logos.push({ name: n.name, x, y, w, h }); return; }
  if (n.type === "TEXT") {
    const s = n.getStyledTextSegments(["fontName", "fontSize", "lineHeight", "fills", "textDecoration"])[0];
    const f = sichtbar(s.fills)[0];
    const lh = s.lineHeight.unit === "PERCENT" ? s.fontSize * s.lineHeight.value / 100 : s.lineHeight.unit === "PIXELS" ? s.lineHeight.value : null;
    texte.push({ text: n.characters.replace(/\s+/g, " ").trim(), x, y, w, h, familie: s.fontName.family, schnitt: s.fontName.style,
      groesse: s.fontSize, zeile: lh === null ? null : r1(lh), farbe: f && f.type === "SOLID" ? hex(f.color) : null,
      unterstrichen: s.textDecoration === "UNDERLINE" || undefined,
      vergleich: n.textAlignHorizontal === "CENTER" ? "mitte" : undefined });
    return;
  }
  const fills = "fills" in n ? sichtbar(n.fills) : [], strokes = "strokes" in n ? sichtbar(n.strokes) : [];
  let eigen = grund;
  if (n !== root && !["VECTOR", "BOOLEAN_OPERATION", "GROUP"].includes(n.type)) {
    const bild = fills.find(p => p.type === "IMAGE"), solid = fills.find(p => p.type === "SOLID");
    if (bild) bilder.push({ name: n.name, x, y, w, h });
    else if (solid || strokes.length) {
      const e = { name: n.name, x, y, w, h, fill: solid ? hex(solid.color) : null };
      if (strokes.length) { e.stroke = hex(strokes[0].color); e.sw = n.strokeWeight; e.sa = n.strokeAlign; }
      const cr = "cornerRadius" in n ? (n.cornerRadius === figma.mixed ? [n.topLeftRadius, n.topRightRadius, n.bottomRightRadius, n.bottomLeftRadius] : n.cornerRadius) : 0;
      if (cr) e.r = cr;
      if (solid && !strokes.length && (h <= 2 || w <= 2) && hex(solid.color) === grund) { e.pruefen = false; e.grund = "unsichtbare Linie (Farbe = Kartengrund)"; }
      flaechen.push(e);
    }
    if (solid) eigen = hex(solid.color);
  }
  if ("children" in n) for (const c of n.children) lauf(c, eigen);
}
lauf(root, "#ffffff");
return { hintergrund: "#ffffff", flaechen, texte, bilder, logos };
```

Das Ergebnis ersetzt `flaechen`, `texte`, `bilder` und `logos` in der
Soll-Datei; `inhalt` muss zu den Texten der Vorlage passen, `folie` ist die
Foliennummer im Deck. Gewollte Abweichungen (`pruefen`, `nur`) danach wieder
markieren. Eine neue
Vorlage (andere Folie) bekommt eine eigene Datei – der Test nimmt jede auf.

## Einheiten

Die Folien sind **1920 × 1080 pt** – Querformat 16:9, kein A4. Figma-px und
PDF-pt sind 1:1. Im CSS deshalb durchgehend `pt`. Wer die Werte als `px`
übernimmt, baut das Dokument um ein Viertel zu klein.

## Seitenraster

| Wert | |
|---|---|
| Seite | 1920 × 1080 pt |
| Linker Randstreifen | 0 – 72 pt, volle Höhe |
| Linke Textkante | 193 pt |
| Cover und Divider | 160 pt |
| Kontaktseite | 240 pt |
| Wortmarke oben rechts | x 1712 – 1860, y 60 – 75 (148 × 15 pt) |
| Wortmarke auf dem Cover | x 160, y 160, 335,5 pt breit |
| Seitenzahl | Feld 66 × 43 pt bei x 1832 / y 1003, Zahl mittig (Komponente `slideNumber`) |

**Der Streifen ist die Sektionsmarke.** Petrol heißt „hier beginnt etwas" – die
erste Seite eines Abschnitts (Prozess) und jede Projekt-Kopfseite. Nebelblau
(`neutral/15`) heißt „das läuft weiter". Die Abschlussseite eines Projekts hat
keinen: Sie ist randlos, und ein Streifen darauf wäre ein Rand.

**Cover und Divider tragen keine Seitenzahl.** Die Zahl ist die tatsächliche
Blattnummer, nicht eine eigene Zählung: Seite 12 zeigt „12".

### Wo die Bildkante liegt

| Seitentyp | Bild beginnt bei | Figma |
|---|---|---|
| Arbeitsweise und KI-Einsatz | 1122 pt | Folien 7–9: Bild 798 pt breit |
| Summary (Foto der Firmenzentrale) | 932 pt | `image-wrapper` 988 pt breit |
| Lösung (Markenfläche) | 932 pt | `image-wrapper` 988 pt breit |
| Statement (Fläche, kein Bild) | 798 pt | 798 |
| Projekt-Kopfseite | kein Bild | – |
| Abschlussseite | randlos, 0 pt | – |

Die Bildbreiten stehen in `render_portfolio.py` als `FLAECHENBREITE` und
dienen zugleich der Auflösungsprüfung; `screens.py` rechnet die Lösungsfläche
auf dieselben 988 pt (`GROESSEN["panel"]`).

## Farben

Alle aus `Foundation – Colors` des [NM] DESIGN SYSTEM v1.3, als Token in
`tokens.json`:

| Token | Wert | Einsatz |
|---|---|---|
| `brand/primary` | `#009193` | Cover, Divider, Panels, Balken, Links, große Zahlen |
| `brand/primary-100` | `#004142` | Eyebrow über Prozess und Arbeitsweise |
| `base/black` | `#111111` | Überschriften, Labels, Kartentexte, Seitenzahl |
| `base/white` | `#ffffff` | Seiten, Karten, Schrift auf Petrol |
| `neutral/80` | `#48575a` | Fließtext |
| `neutral/15` | `#ebf2f5` | Streifen, Kontaktband, Statementfläche, Platzhalter |
| `neutral/20` | `#c9cfd1` | Kontur der Karten links auf der Profilseite, Trennlinien zwischen den Kenntnissen |

Nicht mehr im Einsatz: `#265d60` (Eyebrow alt), `#485758` (Fließtext alt, ein
Blauwert neben `neutral/80`), `#dedede` (Kartenrahmen alt – heute
`neutral/20`), `#f4ece8` (Fläche hinter dem Foto), `#fafafa`
(Cover-Schrift).

Die Markenfarben der Projekte kommen aus dem Kundenlogo und gehören nicht in
diese Liste – siehe `scripts/markenfarbe.py`.

## Typografie

Überschriften in **Rethink Sans**, Text in **Inter** – die Textstile des
Design Systems, in `tokens.json` unter `textstile`:

| Stil (`.t-…`) | Figma | Schrift | Grad / Zeile / Laufweite |
|---|---|---|---|
| `h1` | Headings/H1 | Rethink Sans SemiBold | 96 / 108 % / −0,3 % |
| `h2` | Headings/H2 | Rethink Sans SemiBold | 72 / 110 % / −0,3 % |
| `h2-regular` | Headings/H2 - Regular | Rethink Sans Regular | 72 / 110 % / −0,3 % |
| `h4` | Headings/H4 | Rethink Sans SemiBold | 48 / 110 % / −0,25 % |
| `h4-regular` | Headings/H4 - Regular | Rethink Sans Regular | 48 / 110 % / −0,25 % |
| `h5` | Headings/H5 | Rethink Sans SemiBold | 36 / 110 % / −0,25 % |
| `h6-regular` | Headings/H6 - Regular | Rethink Sans Regular | 32 / 112 % / −0,25 % |
| `subheadline-1-bold` | Text/Subheadline 1 - Bold | Inter Semi Bold | 28 / 115 % |
| `subheadline-2-regular` | Text/Subheadline 2 - Regular | Inter Regular | 24 / 125 % |
| `subheadline-2-bold` | Text/Subheadline 2 - Bold | Inter Semi Bold | 24 / 125 % |
| `body-1-regular` | Text/Body 1 - Regular | Inter Regular | 20 / 150 % |
| `body-1-bold` | Text/Body 1 - Bold | Inter Semi Bold | 20 / 150 % |
| `eyebrow` | H3 (Stil der Datei) | Inter Semi Bold, Versalien | 20 / 130 % |

Dazu sieben Stile ohne Figma-Textstil, so wie die Elemente dort gesetzt sind:
`karten-titel` (Inter Bold 24 / 150 % – Titel der Karten links auf der
Profilseite), `cover-jahr` (Inter 48, Zeile 56,3 pt), `seitenzahl` (Inter Bold 21,8),
`badge-text` (Rethink Sans SemiBold 18), `person-name`/`person-rolle` (Inter
Bold 24 / Regular 20, Zeile 140 %) und `hinweis` (Inter 15 – NDA-Hinweis und
Platzhalter, in Figma nicht vertreten).

**Rethink Sans hat einen hohen Schriftkasten** (Ober- plus Unterlänge 1,3 des
Grades) bei 108–112 % Zeilenhöhe: Die Glyphenbox einer 96-pt-Zeile beginnt
10,6 pt über ihrer Zeile. Die oberen Kanten der Überlaufzonen liegen deshalb
gut 10 pt über den Überschriften, sonst meldet `pruefe_ueberlauf()` Text der
eigenen Seite als Übertrag der Vorseite.

Absätze stehen in Figma als Leerzeile im Textknoten: Der Abstand ist eine
Zeile – bei Subheadline 2 wie bei Body 1 genau 30 pt.

## Maße einzelner Seiten

**Cover** (Figma Folie 1). Wortmarke x 160 / y 160, 335,5 pt breit. Titel
(`h1`) ab y 371, darunter mit 96 pt Abstand der Name (`h2`), 40 pt darunter
die Rolle (`h4-regular`) – ein Auto-Layout: Ein zweizeiliger Titel schiebt
Name und Rolle nach unten. Jahr fest auf y 903.

**Profilseite** (Folie 2, „Profile V2"). Foto 320 × 429 pt bei x 120 / y 120,
Graustufen, `cover`. Inhalt ab x 501 / y 120, 832 pt breit: Name (`h2`), 8 pt
darunter die Rolle (`h4-regular`), 32 pt darunter die Karten, 32 pt zwischen
ihnen. Die Karten sind weiß, Radius 16, **Kontur 1 pt `neutral/20` innen**
(`--linie-karte`) – die Karte bleibt 832 pt breit, der Inhalt steht 24 pt vom
Rand. Titel `karten-titel` (Inter Bold 24 / 150 %), 24 pt darunter der Inhalt:
Top-Kenntnisse in `body-1-regular`, mit „ • “ verbunden, **in einer Zeile**;
die Kenntnisse in `body-1-regular`, dazwischen je eine **Trennlinie 1 pt
`neutral/20`** mit 16 pt Luft darüber und darunter (`--linie-trenner`,
`trenner-luft`) – 63-pt-Takt. Mit acht einzeiligen Kenntnissen endet die
Kenntnisse-Karte bei y 1041 wie in Figma; mehr passt nicht, und
`profil_linke_spalte()` meldet, wenn die Spalte darüber hinausläuft.
Rechtes Petrol-Panel x 1393, 527 breit; darin der Kartenstapel
x 1453, 407 breit, ab y 229, 32 pt zwischen den Karten, jede Karte hugt ihren
Inhalt. Sprachen stehen im 93-pt-Takt (zwei Zeilen plus 33 pt Luft).

Die Connect-Karte führt ihre Einträge **als petrolfarbene Pfeil-Links**
(„LinkedIn Profil →“) – ohne schwarzen Titel, ohne „Anzeigen“-Link, ohne
Trennlinie zwischen den Einträgen. So steht es in der Referenz (Paul, S. 2).
Figma V2 zeigt die frühere Form („LinkedIn Profil“ fett, „Anzeigen“
darunter); sie kam im August 2026 als Abweichung zurück, und die Pfeil-Links
bleiben (Entscheidung September 2026). Die Linktitel sind **sprechende
Labels** („Portfolio“, „LinkedIn Profil“), nie die nackte Domain –
„paulhecker.com →“ kam als Fehler zurück. Gleiches Prinzip bei den Sprachen:
Niveau im Klartext („Business Niveau“, „Muttersprache“), nicht als Kürzel wie
„C2“.

**Meine Kunden** (Folie 3). Überschrift (`h1`) x 193 / y 160. Die Wand ist
ein Band ab x 196 / y 471, 1579 × 420 pt – siehe „Logos".

**Statement** (Folie 4). Nebelblaue Fläche ab x 798. Rollenzeile (`h1`) x 193 /
y 332, 520 pt breit. Das Zitat (`h2-regular`, `neutral/80`) x 964 / y 285,
790 pt breit – oben verankert wie in Figma, nicht mehr vertikal mittig. In
72 pt trägt die Fläche höchstens neun Zeilen, rund 20 Wörter.

**Divider** (Folien 5, 10, 16). Überschrift (`h1`, weiß) x 160 / y 353,
einzeilig – der frühere Umbruch „Mein Design / Prozess" entfällt.

**Design-Prozess** (Folie 6). Eyebrow (`eyebrow`, `brand/primary-100`) x 193 /
y 120. **Drei oder vier Spalten** zu 350 pt im 414-pt-Takt ab x 193 (64 pt
Luft), Balken 350 × 12 pt bei y 434, 16 pt darunter der Titel (`h4`), 24 pt
darunter der Text (`body-1-regular`). Figma zeigt vier Spalten; der Skill
setzt drei oder vier, je nach Material (Entscheidung September 2026).
„KI-Einsatz" ist nie eine davon – eine frühere Fassung hängte ihn als Spalte
an, und genau das kam zurück (August 2026): KI läuft in allen Phasen mit und
ist kein Schritt nach der Umsetzung.

**Arbeitsweise** (Folien 7–9). Eyebrow „Arbeitsweise" (`h6-regular`,
`brand/primary-100`, in normaler Schreibung) x 193 / y 120. Überschrift (`h1`)
x 193 / y 181, 807 pt breit. Der Text (`subheadline-2-regular`, 626 pt breit)
beginnt 80 pt unter der letzten Zeile der Überschrift – bei einer Zeile ab
y 365, bei zweien ab y 469. Die Zeilenzahl rechnet `kopfzeilen()` aus der
Schriftdatei des Stils `h1`; geschätzt wäre sie irgendwann um eine Zeile
daneben und der Text stünde in der Überschrift. Braucht ein Titel bei 96 pt
mehr als drei Zeilen, setzt `kopfmass()` ihn mit 84, 72 oder 64 pt und meldet
das: Kürzen hieße Inhalt wegwerfen.

Schrittleiste unten: drei Balken 323 × 12 pt bei x 193 / 678 / 1162, y 955,
Beschriftung (`body-1-bold`) 16 pt darunter. Erledigte und aktuelle Schritte
sind Petrol, **kommende weiß** – auf der weißen Seite also unsichtbar, auf dem
Bild sichtbar (so in Figma). Der dritte Balken liegt auf dem Bild; ein
Verlauf über die unteren 298 pt (Schwarz bis 20 %, Token `bildschatten`) hält
die weiße Schrift lesbar.

Figma zeigt auf den Arbeitsweise-Folien keine Wortmarke. Der Skill setzt sie
weiter oben rechts aufs Bild, hell oder dunkel nach dem Motiv – offen, ob
das so bleiben soll.

Wortmarke und Seitenzahl richten sich hier nach dem Motiv, nicht nach einer
festen Farbe: `arbeitsweise-3.jpg` ist unten rechts fast schwarz, eine dunkle
Seitenzahl verschwände darin spurlos.

**KI-Einsatz.** Nicht in Figma; dieselbe Seite wie die Arbeitsweise, mit zwei
Unterschieden. Unter dem Text stehen die Werkzeuglogos: Kacheln zu 80 × 80 pt
im 102,4-pt-Takt ab x 193, Grund `neutral/15`, das Logo darin freigestellt,
Unterkante 826 pt. Die Kacheln messen **immer 80 pt**, egal wie viele es sind
– eine frühere Fassung ließ ein bis drei Kacheln wachsen, und genau das kam
als „verrutscht" zurück. Mehr als sechs zeigt die Seite nicht, und das Skript
sagt, welche es weggelassen hat. Der Fließtext steht durchgehend mager:
`**fett**` wird vom Renderskript entfernt, nicht gesetzt. Die Seite trägt
**keine Schrittleiste**.

**Agenturseite** (Folie 15). Überschrift (`h1`) x 193 / y 120, 1015 pt breit,
zweizeilig. Subline (`subheadline-2-regular`) 40 pt darunter auf y 368.
Kundenwand-Bild x 193 / y 497, 700 pt breit. Badge x 1120 / y 707 (110 pt),
Badge-Text (`badge-text`, Petrol) y 891. Statuskarten im Panel ab y 278,
407 × 206 pt, 32 pt Abstand: Titel `subheadline-2-bold`, Zahl `h1` in Petrol.

**Projekt-Kopfseite** (Folien 11_1 ff.). Kundenlogo im 91 pt hohen Feld ab
x 193 / y 120, flächengleich skaliert (`LOGO_PROJEKT_MASS` 105, Deckel 80 pt
Höhe / 420 pt Breite). Überschrift (`h1`) 32 pt unter dem Feld auf y 243,
1300 pt breit. Zwei Spalten zu 570 pt bei x 193 und x 923 (160 pt Luft), ihre
Oberkante 80 pt unter der letzten Zeile der Überschrift – bricht der
Projektname um, rücken beide Spalten mit. Label (`subheadline-1-bold`), 24 pt
darunter der Text (`subheadline-2-regular`, `neutral/80`). **„Meine Rolle"
folgt dem Textfluss der linken Spalte** – 48 pt unter dem Projekttext, dann
Label und Stichpunkte. Die frühere Fassung ließ den Block von der Blattkante
nach oben wachsen; bei kurzen Texten klebte er sichtbar allein am unteren
Rand – genau das kam als Rückmeldung zurück (August 2026). Mehr als drei
Stichpunkte sieht die Vorlage nicht vor: Unter „Meine Rolle" stehen
Rollenbezeichnungen, keine Aufgabenlisten – das Renderskript meldet Überzahl.
Der Überlauf läuft über die normale Zonenprüfung (Unterkante 1010 pt).

**Summary** (Folien 11_2 ff.). Rechts ab 932 pt über die volle Höhe das Foto
der Firmenzentrale, `cover`. Links Kundenlogo im 80-pt-Feld ab y 120,
Überschrift „Summary" (`h1`) auf y 232, Text (`subheadline-2-regular`) ab
y 384, 565 pt breit.

**Lösungsseite** (Folien 11_3 ff.). Rechts ab 932 pt die Markenfläche mit den
Screens. Links Kundenlogo, dann ab y 240 (40 pt unter dem Logofeld) `titel` als
Einleitungszeile (`subheadline-2-bold`), eine Leerzeile darunter der Inhalt
(`body-1-regular`), 565 pt breit. Figma setzt die Einleitung mal in
Subheadline 2 Bold (GPE), mal in fettem Body 1 (Union Investment); der Skill
nimmt den Design-System-Stil.

Die Einleitungszeile ersetzt das feste Label „Die Lösung", sie schafft es nicht
ab: Ohne `titel` steht das Label wieder dort. Der Platz ist derselbe, einzeilig
wie zweizeilig – der Text darunter fließt nach.

**Abschlussseite.** Die Markenfläche randlos über die ganze Folie, kein
Streifen, kein Text. Es bleiben Wortmarke, Seitenzahl und der NDA-Hinweis
(gemessen y 1016–1034).

**Kontaktseite** (Folie 17). Nebelblaues Band ab y 413. Adresse
(`subheadline-2-regular`) x 240 / y 98, Mail und Web in Petrol, nicht
unterstrichen. Aufruf x 752 / y 98, 800 pt breit: Überschrift `h5`, 24 pt
darunter der Text (`subheadline-2-regular`). Weiße Box x 240 / y 653, 657 pt
breit, Radius 16, Innenabstand 24: Frage (`subheadline-1-bold`), darunter
E-Mail und Telefon mit 38 pt Spaltenabstand (Label `body-1-bold`, Wert
`body-1-regular` in Petrol) – der frühere Satz zum Ansprechpartner steht dort
nicht mehr. Person x 1360 / y 516, Foto 320 × 320, darunter der Petrol-Block
mit 40 pt Luft oben und unten, unten mit 24 pt gerundet. Figma zeigt dort
„Business Developer" und ein Farbfoto; der Skill setzt Titel und Foto aus
`ANSPRECHPARTNER` in `render_portfolio.py`.

## Absolut positioniert — und was WeasyPrint dabei anstellt

Die Seiten sind mit `position: absolute` gebaut, nicht im Textfluss. Das ist bei
einem Foliendokument richtig: Jede Fläche hat eine feste Stelle, und es gibt
keine Umbrüche, die zu erhalten wären. Diese Fallen gehören dazu:

- **Jedes absolut positionierte Textelement braucht eine gesetzte Breite.**
  Ohne `width` greift Shrink-to-fit viel zu eng, und „UI/UX Design Portfolio"
  bricht mitten im Titel um. Wer ein neues Textelement anlegt, setzt die Breite
  mit.
- **`nth-of-type` zählt alle Geschwister desselben Tags**, nicht die mit der
  Klasse. Streifen, Eyebrow, Logo und Seitenzahl sind alles `div`, also trifft
  `.prozess-spalte:nth-of-type(1)` daneben. Die Spalten- und Schrittpositionen
  setzt deshalb das Renderskript direkt als `style="left:…"`.
- **Flex-Umbruch reagiert auf Zehntelpunkte.** Vier Kacheln zu 401,8 pt sind
  1607,2 pt und brechen in einem 1607 pt breiten Kasten auf drei je Zeile um.
  Die Zellbreite wird deshalb abgerundet.
- **`justify-content` wirkt nicht.** Ein Logo, das per Flex in seiner Kachel
  zentriert werden soll, hängt in WeasyPrint linksbündig – so kamen die
  Kundenwand und die Werkzeugkacheln der KI-Folie als „verschoben" zurück
  (August 2026). Zentriert wird deshalb über gerechnetes Padding aus dem
  Renderskript; `align-items` und der Zeilenfluss von `flex-wrap`
  funktionieren dagegen.
- **Der Rest eines zu hohen Blocks steht auf der Folgeseite.** Ein absolut
  positionierter Kasten wächst über die Blattkante hinaus, statt abgeschnitten
  zu werden; WeasyPrint bricht ihn um und legt den Rest in die Textebene der
  nächsten Seite. Zu sehen ist er dort nicht – die Folie ist gegen ihn
  beschnitten –, im PDF steht er trotzdem, und auf der eigentlichen Folie fehlen
  die Sätze. Genau deshalb misst `pruefe_ueberlauf()` das fertige PDF nach,
  statt sich auf das Layout zu verlassen.
- **Kein `box-shadow`, kein `filter`.** WeasyPrint übergeht beides
  stillschweigend. Das alte CSS setzte das Profilfoto per
  `filter: grayscale(1)` grau – im PDF stand es farbig, sobald es nicht durch
  `extract_input.py` gelaufen war. Das Renderskript entfärbt es deshalb selbst
  (`graues_foto()`, Zwischenspeicher neben der `portfolio.json`). Schatten
  gibt es auf den Folien ohnehin keine.
- **CSS-Variablen gehen, auch in Kurzschreibweisen** (`padding`, `border`,
  `background` mit Verlauf) – darauf baut das Token-CSS.

## Die Markenflächen sind vorgerenderte Bilder

Auf Lösungs- und Abschlussseite liegen die Screens schräg und laufen über die
Kanten hinaus. Im Browser wäre das eine Handvoll `transform` – **WeasyPrint
setzt Transformationen nicht brauchbar um**. Deshalb baut `scripts/screens.py`
die Fläche als Bild, bevor gerendert wird, und das Template setzt nur noch ein
`<img>` ein. Zwei Größen, doppelt aufgelöst gegen die Punktmaße der Folie:
`panel` 1976 × 2160 px für die rechte Fläche (988 × 1080 pt, Bildkante 932 wie
in Figma), `voll` 3840 × 2160 px für die ganze Folie. Gesichert wird als JPEG:
Die Fläche ist ein Foto aus Fotos, und PNG speichert davon vor allem Rauschen.
Ohne `markenfarbe` steht das New-Monday-Petrol `brand/primary` (siehe unten).

**Die Anordnung ist die gestalterische Entscheidung des Skills** (seit
August 2026, seit September 2026 nach den Figma-Vorlagen unten): Das
Kandidatenmaterial liefert die Screens, nicht ihre Lage.
Fest bleiben nur die Grundfläche selbst und die HQ-Fotos der Summary-Seiten.
Sieben Vorgänger sind bewusst verworfen – die Zufallsstreuung mit Perspektive
(„unscharf und komisch überlappt“), das per PyMuPDF aus Pauls Portfolio 2026
vermessene 15-Grad-Raster, ein flaches Editorial- und ein Showcase-Raster
(alle: „sieht immer noch komisch aus“), die **Bühne** aus Stand 7
(Markenverlauf mit Lichtschein, Fassungen, Überlapp-Paar – Screens klein und
mittig auf leerer Fläche) sowie die **Kachelwand** aus Stand 8: viele kleine
Kacheln in Versatz-Spalten auf einer zu 88 % Richtung Weiß aufgehellten
Markenfläche. Im fertigen Deck (Enrico Meermeier, August 2026) wirkten diese
Flächen „random rumfliegend“ – dunkle Karten schwebten auf fahlem Grau,
und keine der vier Referenzen zeigt eine Wand aus kleinen Kacheln.

Auch die **diagonale Kaskade** aus Stand 9/10 ist verworfen (September
2026): wenige große Screens auf einer abgedunkelten Markenfarbe, mit weichem
Schatten und einem dunklen Verlaufsschleier unter Wortmarke und Seitenzahl.
Bei Paul (S. 25–27) und Enrico (S. 24–26) kam sie als „sieht schlecht aus“
zurück; Enricos Phone-Mockups lagen dabei mitsamt ihrem hellgrauen Grund als
graue Karten auf dunklem Petrol.

Seit `LAYOUT_STAND` 11 ist die Fläche ein **gekipptes Raster**, vermessen an
sieben Figma-Folien, die der Nutzer als Vorbild vorgegeben hat (Wissem Kordi
S. 14/19, Carolin Reis S. 13/14/21, Daniel Fallack S. 13/14):

| Wert | Desktop | Phone | Quelle |
|---|---|---|---|
| Kachelbreite | 560 pt | 276 pt | Carolin S. 14 / Wissem S. 14 |
| Abstand | 36 pt | 30 pt | ebenda |
| Kippwinkel | 15° | 10° | ebenda (Figma-Rotation) |
| Versatz je Spalte | 0,70 Takt | 0,30 Takt | ebenda, gemessen am Spaltenstart |
| Ecke / Kontur | 2,8 % der Breite, 1,45 pt weiß | Gehäuse 14,7 %, Screen 12,6 % | Karte 560 × 396, r 15,5 / Container 276 × 598, r 40,6 |
| Fassung | – | schwarz, Rand 3,25 %, Dynamic Island 35 × 8,8 % der Breite | Wissem S. 14 |

- **Satte Markenfarbe, nichts darüber.** Der Grund ist die Markenfarbe, wie
  sie ist – in den Referenzen #275fb4, #aa164a, #f07d00, nie abgedunkelt.
  Nur fast weiße Töne (Luminanz > 0,80) werden Richtung Schwarz gezogen.
  Ohne `markenfarbe` steht `brand/primary` aus den Tokens (#009193) – die
  RTL-Folie der Referenz macht es so. Kein Schleier, kein Schatten: Keine
  Referenz trägt einen Effekt auf den Screens.
- **Raster statt einzelner Kacheln.** Gleich breite Screens stehen in
  Spalten, jede Spalte gegen die vorige versetzt, von oben bis unten
  gefüllt und gemeinsam gekippt – das Raster füllt die ganze Fläche und wird
  an allen Kanten angeschnitten. Sind es weniger Screens als Plätze, kommen
  sie reihum wieder (Carolin S. 14 zeigt einen Screen dreimal); Nachbarn in
  einer Reihe zeigen verschiedene Screens. Karten zeigen den Screen in
  ganzer Breite, höchstens 1,25-mal so hoch wie breit (lange Seiten von
  oben).
- **Wortmarke, Seitenzahl und NDA-Hinweis liegen auf Markenfarbe.** Kacheln,
  die in ihre Felder ragen, entfallen – die Spalte beginnt dort später, wie
  die rechte Phone-Spalte in Wissem S. 14. Unter 48 Verschiebungen des
  Rasters gewinnt die, bei der dafür am wenigsten Screen wegfällt. Auf den
  Screenflächen setzt der Renderer Wortmarke und Seitenzahl weiß, solange
  die Fläche unter Luminanz 0,40 bleibt (`MARKE_TINTENWECHSEL`) – so stehen
  sie in allen Referenzen, auch auf Orange.
- **Phones in Fassung.** Hochformate im Displayformat (Verhältnis 1,7–2,45,
  höchstens 1 400 px breit) stecken in einer schwarzen Fassung mit Dynamic
  Island; die Fassung passt sich dem Displayformat an (1,75–2,3). Sind die
  meisten Screens einer Fläche Phones, liegt das Phone-Raster, sonst das
  Desktop-Raster – Hochformate zwischen Desktop-Screens werden dort Karten.
- **Die volle Abschlussseite:** Desktop-Screens gerade in drei Spalten von
  502 pt mit 40 pt Abstand ab x 67, versetzt gestartet (Carolin S. 21);
  rechts ab x 1 653 bleibt Markenfarbe für Wortmarke und Seitenzahl. Phones
  liegen auch dort als gekipptes Raster (300 pt, 32 pt Abstand, 10°).
- **Ein einzelner Screen** liegt groß und gekippt allein: Desktop 92 % der
  Panelbreite (62 % der Folie), Phone 86 % der Höhe.
- **Szenen.** Eine fertig gestaltete Showcase-Szene – überlappende Fenster
  auf eigenem dunklem oder farbigem Grund, rundum freier Saum, nach dem
  Freistellen noch über 30 % Grund – wird nicht in Karten zerlegt. Sie
  füllt die Fläche als Ganzes (cover), quer auf ihren Inhalt ausgerichtet,
  wie das Laptop-Foto in Daniel S. 14. Szenen, deren Fenster bis an den
  Bildrand reichen, sind davon nicht zu unterscheiden und laufen als Karte
  im Raster mit. Heller, unbunter Grund (Luminanz > 0,7) ist nie eine Szene,
  sondern die Unterlage eines Screen-Exports.

**Material aufbereiten**, bevor das Raster gelegt wird:

- **Geräte-Mockups.** Helle Clay-Phones auf hellem, ruhigem Grund geben ihre
  Screens her: Das Gehäuse ist heller als der Grund (≥ 8 Stufen), sein
  Umriss ein Hochformat-Rechteck (1,85–2,35, ≥ 150 px breit); innen, um den
  Gehäuserand (3,4 %) eingerückt, liegt der Screen – er kommt in die eigene
  Fassung.
- **Komposit-Zerleger.** Ein Quellbild mit mehreren getrennten, rechteckigen
  Screens auf einheitlichem Grund zerfällt in einzelne Screens; ein
  einzelner Screen auf viel Grund wird auf den Inhalt beschnitten
  (Farbabstands-Maske statt Kantendetektor – Punktmuster im Grund täuschen
  den Kantendetektor). Echte Screenshots tragen Inhalt bis an die Kanten und
  passieren unverändert; zerlegt wird nur, wenn rundum freier Saum liegt
  (≥ 2,5 % je Seite) und die Teile groß genug bleiben (≥ 500/900 px).
- **Mockup-Rand** (Kantendetektor) und **Doubletten** (gleiche Maße, gleiche
  8 × 8-Mittelwerte) wie bisher.

Schärfe misst `screens.py` gegen die tatsächlich platzierte Breite in
Pixeln (2 px je Punkt): Eine Desktop-Kachel liegt 1 120 px breit (voll
1 004 px), ein Phone-Screen 516 px. Liegt der schwächste Screen unter 0,75
davon, wird das ganze Raster bis auf 80 % kleiner, damit die Kacheln gleich
breit bleiben; was dann noch weich ist, wird hochgerechnet und je Datei
gemeldet. Unter 0,40 fliegt ein Screen raus. Szenen füllen die Fläche als
Foto – dort genügt ein Pixel je Punkt. Bleibt nichts übrig, schreibt
`screens.py` die reine Grundfläche und meldet es; die Übergabe bittet dann
um Originalexporte.

## Logos

**Gleiche Fläche statt gleicher Höhe.** Über die Höhe skaliert wirkt eine
kompakte Bildmarke doppelt so schwer wie ein breiter Schriftzug. Das
Renderskript liest das Seitenverhältnis aus der Datei (SVG: `viewBox`, sonst
Dateikopf) und rechnet:

```
Breite = Größe × √Verhältnis      Höhe = Größe / √Verhältnis
```

**Die Kundenwand folgt Folie 3 der Figma-Seite.** Die Logos stehen in ihren
**Originalfarben** – Figma zeigt sie einfarbig schwarz, der Skill bleibt bei
den Farben (Entscheidung September 2026); Raster und Abstände kommen aus Figma:

- **Das Raster (ab 6 Logos)**: ein Band ab x 196 / y 471, 1579 × 420 pt.
  Zeilen zu 100 pt mit 60 pt Luft, je Zeile bis zu sieben Logos, das erste an
  der linken, das letzte an der rechten Kante, die Luft dazwischen gleich
  (SPACE_BETWEEN in Figma). Die vorderen Zeilen tragen bei ungerader Menge
  eines mehr – 19 Logos stehen 7 / 6 / 6 wie in Figma. Ein bis zwei Zeilen
  stehen mittig im Band; über 21 Logos werden es vier Zeilen zu 80 pt mit
  33 pt Luft. Die Größen: `LOGO_MASS_MAX` 100, `LOGO_HOEHE_MAX` 80,
  `LOGO_BREITE_MAX` 350 – damit entstehen genau die Maße aus Figma (Union
  Investment 142 × 64, Porsche 348 × 23, SCA 61 × 80). Passt eine Zeile nicht
  mit 40 pt Mindestluft, schrumpfen ihre Logos gleichmäßig.
- **Eine Reihe (bis 5 Logos)** zeigt Figma nicht; sie steht weiter exakt im
  Referenzmaß von p-03 (Paul Hecker): `LOGO_MASS_REIHE` 160 pt,
  `LOGO_HOEHE_REIHE` 128 pt, Zellfaktor 0,46, Reihenmitte ~717 pt
  (`REIHE_OBEN` 397 pt bei 640 pt Wandhöhe). Die Rückmeldung „Größe und
  Position wie bei Paul" (August 2026) bezog sich genau auf diesen Fall. Bis
  fünf Logos stehen nebeneinander, weil eine Restzeile mit einem einzelnen Logo
  nach Versehen aussieht.

Der Höhendeckel ist jeweils nötig, weil der Flächendeckel über die Fläche
wirkt – eine quadratische Bildmarke wüchse sonst auf das volle Maß.

## Wortmarke und Seitenzahl wechseln die Farbe

Auf Projektseiten reicht das Bild bis in die rechte obere und untere Ecke. Ob
Wortmarke und Seitenzahl dort weiß oder schwarz stehen, hängt am Motiv – in den
Vorlagen wechselt es von Seite zu Seite. Das ist kein Schönheitsdetail: Auf
einem dunklen Screenshot ist eine schwarze Wortmarke unsichtbar.

`ecke_dunkel()` misst nicht die ganze Bildecke, sondern nur `MOEBELFELD` – die
Stelle, an der Wortmarke und Seitenzahl tatsächlich liegen. Eine ganze Ecke
mittelt Himmel und Fassade zusammen und entscheidet dann für einen Punkt, an dem
nichts steht. Gemessen wird außerdem der Ausschnitt, der auf der Folie zu sehen
ist: Die Flächen sind `object-fit: cover` und rechtsbündig, ein abgeschnittener
Dateirand darf nicht mitentscheiden. Wo der Verlauf aus `.bildschatten` liegt,
wird er mitgerechnet (`SCHATTEN_HOCH`, `SCHATTEN_TIEF`) – er macht die untere
Ecke dunkel, egal wie hell das Foto ist. Die Schwelle ist `TINTENWECHSEL`.

Bei den Markenflächen misst `marken_moebel()` zuerst genauso die fertige, schon
zusammengesetzte Fläche; `hell(markenfarbe)` ist nur der Rückfall, wenn nichts
zu messen ist. Umgekehrt wäre es falsch: Ein Screen, der bis in die Ecke reicht,
entscheidet dort über die Lesbarkeit, nicht die Farbe darunter. `screens.py`
hält diese Ecken über `SPERRE_OBEN` und `SPERRE_UNTEN` frei – in der Referenz
bleibt dort immer Markenfarbe stehen.

Ein Fall bleibt, den keine Tinte löst: Liegt das Möbelfeld halb auf Hellem und
halb auf Dunklem, verschwindet ein Stück Wortmarke, egal wie entschieden wird.
`ecke_dunkel()` zählt deshalb die widersprechenden Pixel und meldet ab
`FELD_UNRUHE`, dass das Motiv zu wechseln ist.

## Was aus den Vorlagen bewusst nicht übernommen wurde

- **Freias Variante** ohne Aufmacherbild auf der Kopfseite ist inzwischen der
  Normalfall: Die Kopfseite hat gar kein Bild mehr, beide Textspalten sind gleich
  breit.
- **Reis' Projektseiten** mit „Der Kunde" statt „Projekt / Kunde / Meine Rolle"
  sind eine ältere Fassung und nicht nachgebaut.
- **Freias Gründungsjahr 2019** ist ein Fehler; drei von vier Vorlagen und der
  Satz „Seit 2018 verlängern 100 %…" sagen 2018.
- **Freias Vollbildseiten** mit Fließtext über einer Bildcollage kommen nur bei
  ihr vor und sind nicht Teil des Standards.
