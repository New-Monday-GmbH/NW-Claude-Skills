# Figma-Referenz

Wie aus `arbeit/figma_plan.json` ein bearbeitbarer Frame wird. Der Plan kommt aus
`scripts/figma_plan.py`, geschrieben wird mit dem Figma-MCP-Werkzeug `use_figma`.

**Vor dem ersten `use_figma`-Aufruf den Skill `figma-use` laden** — dort stehen die
Fallstricke des Plugin-API im Einzelnen, und `skillNames: "figma-use"` gehört an
jeden Aufruf.

Der Plan trägt alle Werte fertig ausgerechnet. Hier wird nichts mehr umgerechnet,
nichts geschätzt und nichts aus `layout.md` nachgeschlagen: Was im Plan steht, wird
gesetzt.

Die Matrix ist **eine einzige lange Seite** und wird **ein einziger Frame** —
1440pt breit, Höhe nach Inhalt. Es gibt hier keine Seitenaufteilung wie im
CV-Skill, dafür vier Bänder untereinander: Kopf, Hero, Rumpf, Fuß. Die Vorlage
war selbst ein Figma-Frame; dieser Schritt bringt das Dokument dorthin zurück.

## Der Link

```
https://www.figma.com/design/<fileKey>/<Name>?node-id=1-32
```

`fileKey` ist der Teil nach `/design/` (22–128 Zeichen, alphanumerisch), `node-id`
wird von `1-32` auf `1:32` gedreht. Beides geht als `fileKey` bzw. `nodeId` in die
Werkzeugaufrufe.

**Nur `/design/`.** `/board/` ist FigJam, `/slides/` sind Slides, `/make/` und
`/proto/` können gar nicht beschrieben werden. In allen vier Fällen nicht
probieren, sondern sagen, dass eine Design-Datei gebraucht wird — das PDF ist da
längst fertig.

## Vorflug

Ein lesender Aufruf, bevor irgendetwas entsteht:

```js
const seiten = figma.root.children.map(p => ({ id: p.id, name: p.name }));
const inter = (await figma.listAvailableFontsAsync())
  .filter(f => f.fontName.family === "Inter")
  .map(f => f.fontName.style);
const kinder = figma.currentPage.children.map(n => ({ x: n.x, w: n.width }));
return { editor: figma.editorType, seiten, inter,
         rechts: kinder.length ? Math.max(...kinder.map(n => n.x + n.w)) : 0 };
```

Daraus folgt:

- **Zielseite.** Trägt der Link eine `node-id`, gehört der Frame auf deren Seite.
  Ohne `node-id` eine neue Seite `figma.createPage()` mit dem Namen
  `Skillmatrix — Vorname Nachname`. **Nie ungefragt in eine bestehende Seite
  schreiben**, zu der nichts hinführt — in fremden Dateien liegt dort Arbeit
  anderer Leute.
- **Freie Stelle.** Der Frame steht rechts vom rechtesten vorhandenen Knoten
  (`max(x + width)`, plus 100pt Luft). Knoten, die direkt an die Seite gehängt
  werden, landen sonst auf (0,0) — mitten in dem, was schon da ist.
- **Schnitte.** Fehlt einer der drei, bricht der Bau ab, bevor er anfängt.

Scheitert schon der Vorflug an Rechten, ist das die Antwort auf die Frage, ob es
am Konto oder an der Datei liegt — `whoami` sagt, als wer man angemeldet ist.

## Die Schnitte heißen mit Leerzeichen

| Gewicht im Layout | Figma-Schnitt |
|---|---|
| 400 | `Regular` |
| 600 | `Semi Bold` |
| 700 | `Bold` |

`SemiBold` ohne Leerzeichen ist der häufigste Fehler am ganzen Plugin-API.
`loadFontAsync` wirft dann, und mit ihm fällt jeder Textknoten des Frames aus.
Der Plan schreibt die Schnitte schon in der Figma-Schreibweise — sie werden
übernommen, nicht gebildet. `Extra Bold` steht der Vollständigkeit halber in
`plan.schnitte`, die Skillmatrix benutzt es nicht.

## Werkzeuge, die in jedem Aufruf stehen

Diese vier Helfer stehen am Anfang jedes Bau-Aufrufs. Alles Weitere ist ihre
Anwendung.

```js
const hex = h => ({ r: parseInt(h.slice(1,3),16)/255,
                    g: parseInt(h.slice(3,5),16)/255,
                    b: parseInt(h.slice(5,7),16)/255 });
// Farbwerte im Plan sind Tokennamen ("brand") oder rohe Hexwerte — beides geht.
const farbe = (n, d = 1) => ({ type: "SOLID", color: hex(P.farben[n] || n), opacity: d });

// Ein Textknoten nach der kanonischen Reihenfolge: Schrift laden, dann setzen,
// dann Zeichen. Andersherum wirft Figma "unloaded font".
async function txt(t) {
  const n = figma.createText();
  await figma.loadFontAsync({ family: "Inter", style: t.typo.schnitt });
  n.fontName = { family: "Inter", style: t.typo.schnitt };
  n.characters = t.text;
  n.fontSize = t.typo.groesse;
  // zeilenhoehe null heißt AUTO — das Gegenstück zu `line-height: normal`.
  n.lineHeight = t.typo.zeilenhoehe ? { unit: "PERCENT", value: t.typo.zeilenhoehe * 100 }
                                    : { unit: "AUTO" };
  n.letterSpacing = { unit: "PIXELS", value: t.typo.laufweite };
  if (t.typo.versalien) n.textCase = "UPPER";
  n.fills = [farbe(t.typo.farbe, t.typo.deckkraft)];
  // Erst resize, dann HEIGHT: FILL allein lässt den Knoten auf Nullbreite
  // zusammenfallen, weil WIDTH_AND_HEIGHT die Breite überschreibt.
  if (t.breite) { n.resize(t.breite, n.height); n.textAutoResize = "HEIGHT"; }
  return n;
}

// Ein Band im Frame: volle Breite, eigener Hintergrund, Inhalt auf 1232
// zentriert. paddingLeft/Right = rand erledigt die Zentrierung — .container
// hat kein Gegenstück in Auto-Layout.
function band(b) {
  const f = figma.createAutoLayout("VERTICAL", { name: b.art, itemSpacing: 0 });
  f.paddingTop = b.oben; f.paddingBottom = b.unten;
  f.paddingLeft = P.rahmen.rand; f.paddingRight = P.rahmen.rand;
  f.fills = [farbe(b.hintergrund)];
  return f;                    // FILL erst nach appendChild setzen
}

// Ein Block, der seinen Abstand nach oben selbst trägt.
function huelle(name, abstand, richtung = "VERTICAL") {
  const f = figma.createAutoLayout(richtung, { name, itemSpacing: 0 });
  f.paddingTop = abstand || 0;
  f.fills = [];
  return f;
}
```

**Warum jeder Block seinen Abstand selbst trägt:** Auto-Layout kennt genau einen
`itemSpacing` je Rahmen, `skillmatrix.css` aber ein Dutzend verschiedener
Abstände. Alle Rahmen laufen deshalb mit `itemSpacing: 0`, und `abstand_oben`
aus dem Plan wird zum `paddingTop` des Blocks.

## Der Rahmen

```js
const F = figma.createAutoLayout("VERTICAL", { name: P.rahmen.name, itemSpacing: 0 });
F.resize(P.rahmen.breite, 1000);                    // 1440 breit
F.layoutSizingHorizontal = "FIXED";
F.layoutSizingVertical = "HUG";                     // Höhe nach Inhalt
F.fills = [farbe(P.rahmen.hintergrund)];
F.x = rechts + 100; F.y = 0;
F.placeholder = true;          // und am Ende wieder false — nie stehen lassen
```

**Der Frame hugt, er bekommt keine feste Höhe.** `plan.rahmen.hoehe_pdf` ist ein
Sollwert zum Gegenprüfen, kein Wert zum Setzen: Eine feste Höhe wäre beim ersten
Textwechsel falsch, und genau dafür ist der Frame ja da. Am Ende `F.height` gegen
`hoehe_pdf` halten — **±20pt sind normal** (Figma und WeasyPrint brechen Zeilen
minimal anders um), mehr ist ein Hinweis, dass ein Block nicht sitzt.

Jedes Band wird angehängt und **danach** auf volle Breite gesetzt:

```js
F.appendChild(b); b.layoutSizingHorizontal = "FILL"; b.layoutSizingVertical = "HUG";
```

Die Reihenfolge ist nicht verhandelbar — `FILL` vor `appendChild` wirft.

## Die vier Bänder

### `kopf`

Kein Auto-Layout: Die Wortmarke sitzt bei 44/33 und damit **nicht** auf der
Containerkante — so steht sie in der Vorlage. Ein Rahmen fester Höhe mit einem
absolut gesetzten Kind.

```js
const k = figma.createFrame();
k.resize(P.rahmen.breite, b.hoehe);      // 1440 x 88
k.fills = [farbe(b.hintergrund)]; k.clipsContent = true;
const l = figma.createNodeFromSvg(svgMarkup);
l.rescale(b.logo.breite / l.width);
k.appendChild(l); l.x = b.logo.links; l.y = b.logo.oben;
```

Angehängt wird der Kopf mit `layoutSizingVertical = "FIXED"` — er ist das einzige
Band mit gesetzter Höhe.

### `hero`

Eine horizontale Zeile, oben ausgerichtet (`counterAxisAlignItems = "MIN"`),
`primaryAxisAlignItems = "SPACE_BETWEEN"`: links die Textspalte auf
`textspalte` (700), rechts die Fotokarte.

Die Textspalte von oben nach unten: `badge`, `name`, `rolle`, `beschreibung`,
`schwerpunkte`. Jeder Block trägt sein `abstand_oben`.

**Das Badge** ist ein horizontales Auto-Layout mit `counterAxisAlignItems =
"CENTER"`: eine 8pt-Ellipse in `gruen`, dann der Text. `cornerRadius`,
`padding` (oben/rechts/unten/links) und `strokeWeight` stehen im Plan. Es hugt in
beide Richtungen — sonst zieht es sich über die 700pt der Spalte.

**Die Schwerpunkt-Buttons** sind eine horizontale Reihe mit `itemSpacing:
abstand` (20), jeder Button ein hugendes Auto-Layout mit `strokes` in `brand`,
`strokeWeight: 2` und `cornerRadius: 14`. Drei passen nebeneinander in die
Textspalte; ein vierter bricht um, deshalb warnt schon `render_skillmatrix.py`
darüber.

**Die Fotokarte** ist der einzige Ort mit übereinanderliegenden Ebenen — hier
also ein `figma.createFrame()` mit `clipsContent = true`, keine Auto-Layout-Hülle:

```js
const c = figma.createFrame();
c.resize(k.breite, k.hoehe);                       // 433 x 390
c.cornerRadius = k.radius; c.clipsContent = true;
c.fills = [farbe(k.hintergrund)];

const bild = figma.createRectangle();              // Ziel fürs Foto
bild.resize(k.breite, k.hoehe); c.appendChild(bild); bild.x = 0; bild.y = 0;

const v = figma.createRectangle();                 // der Verlauf darüber
v.resize(k.breite, k.verlauf.hoehe);
c.appendChild(v); v.x = 0; v.y = k.hoehe - k.verlauf.hoehe;
v.fills = [{ type: "GRADIENT_LINEAR",
             // Oben nach unten. Die Einheitsmatrix liefe links nach rechts.
             gradientTransform: [[0, 1, 0], [-1, 0, 1]],
             gradientStops: k.verlauf.stopps.map(s => ({
               position: s.position,
               color: { ...hex(P.farben[k.verlauf.farbe]), a: s.deckkraft } })) }];
```

`gradientStops` ist die eine Stelle im ganzen API, an der die Farbe ein
`a`-Feld trägt — bei `SOLID` gehört die Deckkraft an den Paint, hier an den Stopp.

Name und Erfahrung stehen absolut bei `textlinks` von links und `textunten` vom
unteren Rand, mit `zeilenabstand` dazwischen. Erst setzen, wenn beide Texthöhen
feststehen, sonst stimmt die Unterkante nicht.

Das Foto ist bereits in Graustufen und auf 433 × 390pt beschnitten;
`extract_input.py` hat das erledigt. In Figma wird nichts nachgefärbt.

### `rumpf`

Hintergrund `flaeche`, Padding 80 oben / 56 unten, darin die Sektionen mit
`sektionsabstand` (64) dazwischen — als `paddingTop` der zweiten und jeder
weiteren Sektion, nicht als `itemSpacing`.

**Die Sektionsüberschrift** ist eine horizontale Reihe mit
`counterAxisAlignItems = "CENTER"` und `itemSpacing: icon.abstand` (14): das
26pt-Icon als SVG, dann der Titel in 24pt/Bold. Das CSS setzt das Icon mit
`vertical-align: -4pt` leicht tiefer; in Figma richtet die Mittelachse aus. Das
ist eine bewusste Abweichung und fällt nicht auf.

#### `zertifikate`

Je Karte ein vertikales Auto-Layout auf `breite` (1232) mit `cornerRadius`,
`padding` und weißer Füllung. `paddingLeft` ist `kante + padding[3]`, also 33 —
die 5pt-Teal-Kante links ist **kein Stroke**, sondern ein absolut gesetztes
Rechteck über die volle Kartenhöhe. Einseitige Rahmen kennt Figma nicht.

**Die Reihenfolge entscheidet:**

```js
karte.appendChild(kante);
kante.layoutPositioning = "ABSOLUTE";      // ZUERST
kante.resize(5, karte.height);
kante.x = karte.x; kante.y = karte.y;
kante.constraints = { horizontal:"MIN", vertical:"STRETCH" };
```

Wer `x`/`y` vor `layoutPositioning` setzt, bekommt einen kurzen Teal-Strich am
unteren Kartenrand: Solange der Knoten Flusskind ist, ignoriert Auto-Layout
seine Koordinaten und sortiert ihn hinter die Chips. `ABSOLUTE` danach friert
ihn an genau dieser falschen Stelle ein — der Fehler sieht aus wie ein
Rechenfehler, ist aber einer der Aufrufreihenfolge. `STRETCH` sorgt dafür, dass
die Kante mitwächst, wenn später jemand eine Zeile in die Karte schreibt.

Kopfzeile der Karte: horizontal, `SPACE_BETWEEN`, links der Titel, rechts das
Jahres-Badge (hugendes Auto-Layout, `jahr_bg`, Radius 6).

Die Tags sind ein horizontales Auto-Layout mit **`layoutWrap = "WRAP"`**,
`itemSpacing: abstand_x`, `counterAxisSpacing: abstand_y`. Wrap verlangt
`layoutSizingHorizontal = "FIXED"` — ohne feste Breite weiß Figma nicht, wo
umzubrechen ist, und alle Chips stehen in einer Zeile.

Das **Bilderraster**: je Zeile ein horizontales Auto-Layout mit
`itemSpacing: abstand` (24), das **hugt**. Drei Kacheln zu 395 plus zwei Abstände
sind 1233pt und stehen damit 1pt über dem Container — im PDF ist das genauso.
Auf 1232 festgenagelt schnitte Figma die dritte Kachel an.

#### `kompetenzen`

Je Kategorie: das Versalien-Label, darunter mit `label_unten` (14) Abstand die
Hairline (Rechteck 1232 × 1pt in `linie`), darunter die Kartenzeilen mit
`zeilenabstand` (20) und `kartenabstand` (20.5) zwischen den Karten.

Eine **Skillkarte** ist ein vertikales Auto-Layout, 397 breit, Radius 14,
Padding 24/26/22/26:

```js
const kopf = figma.createAutoLayout("HORIZONTAL", { itemSpacing: 0 });
kopf.primaryAxisAlignItems = "SPACE_BETWEEN";
kopf.counterAxisAlignItems = "MIN";
// Titel links (feste Breite aus dem Plan), Punktereihe rechts.
const reihe = figma.createAutoLayout("HORIZONTAL", { itemSpacing: p.abstand });
reihe.paddingTop = p.oben;                       // 4pt, wie .punkte
for (let i = 0; i < p.anzahl; i++) {
  const e = figma.createEllipse();
  e.resize(p.groesse, p.groesse);
  e.fills = [farbe(i < p.voll ? p.voll_farbe : p.leer_farbe)];
  reihe.appendChild(e);
}
```

Die Reihe misst 5 × 10 + 4 × 3,5 = 64pt. Im CSS trägt jeder Punkt
`margin-left: 3.5pt`, macht 67,5 — in Figma sitzt der Abstand zwischen den
Punkten. Die 3,5pt Differenz sind die einzige bewusste Abweichung an dieser
Karte, und der Plan hat die Titelbreite bereits danach gerechnet.

Der leichte Schatten der Karten (`0 1pt 4pt rgba(15,23,42,.06)`) wird
**nicht** nachgebaut. Er ist im PDF kaum zu sehen, und ein Effekt je Karte
bläht bei 21 Karten die Datei auf, ohne dass jemand den Unterschied bemerkt.

### `fuss`

Hintergrund `brand`, Padding 64/56. Die Frage in 28pt/Bold weiß, darunter mit
`abstand_oben` (40) die Trennlinie — ein Rechteck 1232 × 1pt in Weiß mit
`opacity: 0.25` am Paint, nicht am Knoten.

Darunter die Zeile: das 140pt-Logo, `abstand_rechts` (96) Luft, dann die drei
Spalten zu 240pt mit `spaltenabstand` (48). Je Spalte ein Label (11pt, Versalien,
Weiß auf 75 %) und ein mehrzeiliger Wert (14pt, Zeilenabstand 1,5).

**Die Zeilenumbrüche im Wert sind echte `\n` im Textknoten** — der Plan hat sie
absichtlich nicht wegnormalisiert. Nicht in drei Textknoten aufteilen.

## Logos, Icons, Fotos

Zwei Wege, und die Trennung ist Absicht.

**Alle Pfade im Plan sind absolut.** Logos und Icons liegen im Skill-Ordner, Foto
und Zertifikatsbilder im Arbeitsverzeichnis des Nutzers — relativ ließe sich im
Plan nicht mehr unterscheiden, worauf sich welcher Pfad bezieht. Sie werden
gelesen, wie sie dastehen.

**SVG — direkt im Code.** Die Datei lesen und das Markup übergeben:

```js
const knoten = figma.createNodeFromSvg(svgMarkup);
knoten.rescale(l.breite / knoten.width);
```

Kein Upload, kein Netz, und das Ergebnis ist ein Vektorbaum, den jeder Designer
auseinandernehmen kann. Die vier SVGs dieses Skills liegen zwischen 508 B und
4,2 KB und passen alle in den Code-Cap von 50 000 Zeichen je Aufruf. Das Markup
vorher von XML-Prolog, DOCTYPE, Kommentaren und Zeilenumbrüchen befreien.

**`rescale()`, nicht `resize()`.** `resize()` dehnt nur den Rahmen, die Pfade
darin bleiben in Originalgröße stehen. Das Seitenverhältnis stimmt schon aus
`svg_masse()`, also genügt der eine Faktor.

**Raster — über `upload_assets` mit `nodeId`.** Erst das Zielrechteck in den
Maßen aus dem Plan anlegen, dann die Bytes darauf hochladen:

1. `figma.createRectangle()` auf `breite` × `hoehe`, an seinen Platz hängen, ID merken.
2. `upload_assets` mit `fileKey`, `nodeId` und `scaleMode: "FILL"` — Foto wie
   Zertifikatskachel sind beide auf ihr Zielformat vorbeschnitten.
3. Die zurückgegebene URL an `figma_assets.py` weiterreichen:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --paare arbeit/uploads.json
   ```

`upload_assets` gibt je Aufruf `count` Upload-URLs zurück; für die sechs Kacheln
eines vollen Rasters also **ein** Aufruf mit `count: 6`. Aber: `nodeId` geht nur
bei `count: 1`. Mehrere Kacheln heißen darum mehrere Aufrufe — je Kachel einer,
mit ihrer `nodeId`.

**Nie `upload_assets` ohne `nodeId`.** Ohne Zielknoten legt es neue Frames
irgendwo auf der Seite ab, und sie hinterher wiederzufinden und einzusortieren
ist Raterei. `figma.createImageAsync` ist gesperrt, `figma.createImage` bräuchte
die Bytes im Code — bei einem 160-KB-Foto sprengt das den Cap.

## Schritt für Schritt, nicht auf einmal

Höchstens rund zehn logische Operationen je `use_figma`-Aufruf. Für eine
Matrix mit vier Kategorien sind das etwa zehn Aufrufe:

| # | Was |
|---|---|
| 1 | Vorflug (nur lesen) |
| 2 | Rahmen, Kopf, Hero-Textspalte |
| 3 | Fotokarte anlegen, dann Foto hochladen |
| 4 | Rumpf, Zertifikatssektion mit Karten und Tags |
| 5 | Rasterkacheln anlegen, dann Bilder hochladen (je Kachel ein Upload) |
| 6…n | **Je Kategorie ein Aufruf** — Label, Hairline, Kartenzeilen |
| n+1 | Fuß, `placeholder = false`, Kontrollbild |

Nach jedem Aufruf die IDs zurückgeben, nach jedem Band ein `screenshot()` zur
Kontrolle — und wenn etwas nicht stimmt, erst reparieren, dann weiterbauen.

```js
return { createdNodeIds: [...], frame: F.id, seite: figma.currentPage.id };
```

`use_figma` ist atomar: Ein Skript, das wirft, hat nichts geschrieben. Nach einem
Fehler also nicht blind wiederholen, sondern die Meldung lesen, das Skript
reparieren, erneut senden.

## Was in einer fremden Datei nicht passiert

- **Keine Text-Styles, keine Variablen, keine Komponenten.** Der Frame trägt rohe
  Werte. Eine Datei, in die jemand seine Skillmatrix legt, soll danach nicht neue
  Styles in jeder Auswahlliste haben.
- **Nichts umbenennen, nichts löschen, nichts verschieben**, was schon da war.
- **Nichts überschreiben.** Steht dort schon ein Frame gleichen Namens, kommt der
  neue daneben.

## Wenn es schiefgeht

Alles hier ist Zugabe. Das PDF ist zu diesem Zeitpunkt fertig und geht so oder so
raus — mit einem Satz dazu, was an Figma nicht ging:

| Symptom | Was dahintersteckt |
|---|---|
| Werkzeug nicht vorhanden | Figma-MCP nicht verbunden |
| „you don't have edit access“, 401/403 | angemeldetes Konto hat keine Bearbeitungsrechte — `whoami` zeigt, welches Konto das ist |
| `fileKey` wird abgelehnt | Link zeigt auf `/board/`, `/slides/`, `/make/` oder `/proto/` |
| `unloaded font` | Schnittname ohne Leerzeichen |
| `HUG`/`FILL` wird abgelehnt | vor `appendChild` gesetzt |
| Textknoten auf Nullbreite | `textAutoResize` gesetzt, ohne vorher zu `resize()` |
| Chips stehen alle in einer Zeile | `layoutWrap = "WRAP"` ohne feste Breite am Rahmen |
| Teal-Kante als kurzer Strich unten | `x`/`y` vor `layoutPositioning = "ABSOLUTE"` gesetzt |
| Upload hängt oder bricht ab | im Browser-Chat blockt der Proxy fremde Domains |

Bei Rechte- und Zugriffsfehlern sagt `whoami`, als wer man gerade angemeldet ist —
das ist der schnellste Weg zu der Antwort, ob es am Konto oder an der Datei liegt.
