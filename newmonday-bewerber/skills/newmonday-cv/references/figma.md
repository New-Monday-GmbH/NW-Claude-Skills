# Figma-Referenz

Wie aus `arbeit/figma_plan.json` ein bearbeitbarer Frame wird. Der Plan kommt aus
`scripts/figma_plan.py`, geschrieben wird mit dem Figma-MCP-Werkzeug `use_figma`.

**Vor dem ersten `use_figma`-Aufruf den Skill `figma-use` laden** — dort stehen die
Fallstricke des Plugin-API im Einzelnen, und `skillNames: "figma-use"` gehört an
jeden Aufruf.

Der Plan trägt alle Werte fertig ausgerechnet. Hier wird nichts mehr umgerechnet,
nichts geschätzt und nichts aus `layout.md` nachgeschlagen: Was im Plan steht, wird
gesetzt.

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
return { seiten, inter, editor: figma.editorType };
```

Daraus folgt:

- **Zielseite.** Trägt der Link eine `node-id`, gehört der Frame auf deren Seite.
  Ohne `node-id` eine neue Seite `figma.createPage()` mit dem Namen
  `CV — Vorname Nachname`. **Nie ungefragt in eine bestehende Seite schreiben**, zu
  der nichts hinführt — in fremden Dateien liegt dort Arbeit anderer Leute.
- **Freie Stelle.** Neue Frames stehen rechts vom rechtesten vorhandenen Knoten
  (`max(x + width)` über `figma.currentPage.children`, plus 100pt Luft). Knoten, die
  direkt an die Seite gehängt werden, landen sonst auf (0,0) — mitten in dem, was
  schon da ist.
- **Schnitte.** Fehlt einer der vier, bricht der Bau ab, bevor er anfängt.

## Die vier Schnitte heißen mit Leerzeichen

| Gewicht im Layout | Figma-Schnitt |
|---|---|
| 400 | `Regular` |
| 600 | `Semi Bold` |
| 700 | `Bold` |
| 800 | `Extra Bold` |

`SemiBold` und `ExtraBold` ohne Leerzeichen sind der häufigste Fehler am ganzen
Plugin-API. `loadFontAsync` wirft dann, und mit ihm fällt jeder Textknoten des
Frames aus. Der Plan schreibt die Schnitte schon in der Figma-Schreibweise — sie
werden übernommen, nicht gebildet.

## Werkzeuge, die im Plan stecken

Diese drei Helfer stehen am Anfang jedes Bau-Aufrufs. Alles Weitere ist ihre
Anwendung.

```js
const hex = h => ({ r: parseInt(h.slice(1,3),16)/255,
                    g: parseInt(h.slice(3,5),16)/255,
                    b: parseInt(h.slice(5,7),16)/255 });

// Ein Textknoten nach der kanonischen Reihenfolge: Schrift laden, dann setzen,
// dann Zeichen. Andersherum wirft Figma "unloaded font".
async function txt(inhalt, t, breite, farben) {
  const n = figma.createText();
  await figma.loadFontAsync({ family: "Inter", style: t.schnitt });
  n.fontName = { family: "Inter", style: t.schnitt };
  n.characters = inhalt;
  n.fontSize = t.groesse;
  // zeilenhoehe null heißt AUTO — das Gegenstück zu `line-height: normal`.
  n.lineHeight = t.zeilenhoehe ? { unit: "PERCENT", value: t.zeilenhoehe * 100 }
                               : { unit: "AUTO" };
  n.letterSpacing = { unit: "PIXELS", value: t.laufweite };
  n.fills = [{ type: "SOLID", color: hex(farben[t.farbe]) }];
  // Erst resize, dann HEIGHT: FILL allein lässt den Knoten auf Nullbreite
  // zusammenfallen, weil WIDTH_AND_HEIGHT die Breite überschreibt.
  n.resize(breite, n.height);
  n.textAutoResize = "HEIGHT";
  return n;
}

// Ein Block im Frame: eigener Rahmen, der seinen Abstand nach oben selbst trägt.
function huelle(b, breite, richtung = "VERTICAL") {
  const f = figma.createAutoLayout(richtung, { name: b.art, itemSpacing: 0 });
  f.paddingTop = b.abstand_oben; f.paddingLeft = b.einzug;
  f.fills = [];
  f.resize(breite, f.height);
  f.layoutSizingHorizontal = "FIXED"; f.layoutSizingVertical = "HUG";
  return f;
}
```

**Warum jeder Block seinen Abstand selbst trägt:** Auto-Layout kennt genau einen
`itemSpacing` je Rahmen, `cv.css` aber acht verschiedene Abstände. Der Frame läuft
deshalb mit `itemSpacing: 0`, und `abstand_oben` aus dem Plan wird zum
`paddingTop` des Blocks. `einzug` (0 oder 120) wird sein `paddingLeft` — so stehen
Aufgaben und Projekte an der Textkante der Station, ohne dass sie in ihr stecken
müssten.

## Der Frame

Pro Eintrag in `plan.frames` ein Rahmen, in der Reihenfolge des Plans:

```js
const f = figma.createAutoLayout("VERTICAL", { name: frame.name, itemSpacing: 0 });
f.resize(plan.rahmen.breite, plan.rahmen.hoehe);          // 595 x 842 = A4 in pt
f.layoutSizingHorizontal = "FIXED"; f.layoutSizingVertical = "FIXED";
f.paddingTop = 60; f.paddingRight = 107; f.paddingBottom = 32; f.paddingLeft = 60;
f.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
f.placeholder = true;     // und am Ende wieder false — nie stehen lassen
```

Die Frames stehen nebeneinander, 100pt auseinander, in Leserichtung.

**Der Footer** ist der einzige Block, der nicht oben anschließt: Er sitzt am unteren
Rand des letzten Frames. Dafür bekommt der Frame `primaryAxisAlignItems = "SPACE_BETWEEN"`
— alles davor sammelt sich oben, der Footer fällt nach unten. Die gemessene Fußluft
aus `render_cv.py` wird **nicht** nachgebaut; sie ist ein Kunstgriff für WeasyPrint,
in Figma erledigt das die Ausrichtung.

Zwei Dinge hängen daran, und beide gehen sonst schief:

- **Der letzte Frame hat genau zwei Kinder**: einen Rahmen mit allem Inhalt und den
  Footer. `SPACE_BETWEEN` verteilt die Luft zwischen *allen* Kindern — hängen die
  Stationen einzeln im Frame, werden sie mit auseinandergezogen.
- **Die Footerreihe steht auf `HUG`, nicht auf 428pt.** Die drei Spalten sind
  zusammen breiter als der Satzspiegel (gemessen 367pt statt 318pt); im PDF läuft
  der Footer deshalb in den rechten Seitenrand, und das ist so gewollt. Auf `FIXED`
  gesetzt schneidet der Frame die Adressspalte ab. Nur die Trennlinie darüber bleibt
  auf den 428pt des Satzspiegels.

## Die Blockarten

Jeder Block trägt `art`, `abstand_oben` und `einzug`. Was darüber hinaus drinsteht,
sagt die Art:

| `art` | Was gebaut wird |
|---|---|
| `kopfzeile` | Die Wortmarke aus `logo`, fest 133,231 × 13,5pt |
| `intro` | Horizontal: Fotospalte (`fotospalte`, `foto.oben` als `paddingTop`), `fotoabstand` als `itemSpacing`, dann die Infospalte mit `name`, `zeilen`, `verweise` |
| `rubrik` | Eine Zeile Überschrift aus `text` — 14pt Semi Bold |
| `bildung` | Zwei Spalten `spaltenbreite`, `spaltenabstand` auseinander, Umbruch nach zwei Einträgen mit `reihenabstand` dazwischen; je Eintrag `abschluss`, `zeilen`, `themen` |
| `skillset` | Zwei Spalten aus `spalten`, je Gruppe `titel` und `eintraege`, `gruppenabstand` zwischen den Gruppen |
| `profil` | Ein Absatz über die volle Inhaltsbreite |
| `trennlinie` | Eine Linie über die volle Breite, `staerke` pt, Farbe `farbe` |
| `station` | Horizontal: `rail` (fest `rail.breite`, Logos **rechtsbündig**, `rail.oben` als `paddingTop`), `spaltenabstand`, dann `titel`, `meta`, `absaetze` in `koerperbreite` |
| `aufgaben` | Eine Bulletliste, `abstand` als `paragraphSpacing` |
| `projekt` | `logos`, `kunde`, `zeitraum`, `absaetze` — untereinander in `breite` |
| `footer` | `trennlinie`, dann horizontal: Logo (`logo.breite`), `spaltenabstand`, die drei `spalten` mit `gruppenabstand` |

### Bulletlisten sind echte Listen

Nicht „• " vor den Text schreiben, sondern die Listenfunktion nutzen — sonst
verrutscht die Einrückung, sobald jemand eine Zeile ändert:

```js
const n = await txt(b.eintraege.join("\n"), b, b.breite, plan.farben);
n.setRangeListOptions(0, n.characters.length, { type: "UNORDERED" });
n.setRangeIndentation(0, n.characters.length, 1);
n.listSpacing = b.abstand;           // entspricht li { margin-bottom }
```

**`listSpacing`, nicht `paragraphSpacing`.** Sobald ein Textknoten Listenoptionen
trägt, regelt `listSpacing` den Abstand zwischen den Punkten; `paragraphSpacing`
lässt sich zwar setzen und auch wieder auslesen, bleibt aber wirkungslos. Gemessen:
vier Bullets standen mit `paragraphSpacing = 10` auf 70pt Höhe, mit
`listSpacing = 10` auf 100pt — das ist der Unterschied zwischen der lockeren
Aufgabenliste des Layouts und einer eng gesetzten. Ob eine Liste vorliegt, sagt
`getRangeListOptions(0, n.characters.length)`; einen `listOptions`-Getter am Knoten
gibt es nicht.

Figma setzt den Bullet-Einzug selbst; die 15pt aus dem CSS lassen sich nicht auf den
Punkt genau nachstellen. Das ist die einzige bewusste Abweichung vom PDF und fällt
im Dokument nicht auf.

### Die Verweise im Profilkopf

Schwarzer Text, Unterstrich in der Markenfarbe — mehr Signal braucht ein Verweis in
einem Dokument nicht, das auch gedruckt wird:

```js
const n = await txt(v.text, block.verweise, breite, plan.farben);
if (v.unterstrichen) {
  const e = n.characters.length;
  n.setRangeTextDecoration(0, e, "UNDERLINE");
  n.setRangeTextDecorationColor(0, e, { value: { type: "SOLID", color: hex(plan.farben.brand) } });
  n.setRangeTextDecorationThickness(0, e, { unit: "PIXELS", value: 0.5 });
  n.setRangeTextDecorationOffset(0, e, { unit: "PIXELS", value: 2 });
  if (v.url) n.setRangeHyperlink(0, e, { type: "URL", value: v.url });
}
```

`unterstrichen: false` heißt: ein Portfolio, das nur als PDF vorliegt. Es hat keine
Adresse, also auch keinen Unterstrich und keinen Link.

### Der senkrechte Strich in der Stationszeile

`meta.strich` ist 1 × 10pt in `--black`, zwischen Zeitraum und Firma, mit
`meta.abstand` Luft auf beiden Seiten. Ein Rechteck, keine Linie — eine `LINE`
lässt sich in Auto-Layout nicht sauber ausrichten.

## Logos und Foto

Zwei Wege, und die Trennung ist Absicht.

**Alle Pfade im Plan sind absolut.** Die Logos liegen im Skill-Ordner, das Foto im
Arbeitsverzeichnis des Nutzers — relativ ließe sich im Plan nicht mehr
unterscheiden, worauf sich welcher Pfad bezieht. Sie werden gelesen, wie sie
dastehen.

**SVG — direkt im Code.** Die Datei lesen und das Markup übergeben:

```js
const knoten = figma.createNodeFromSvg(svgMarkup);
knoten.resize(l.breite, l.hoehe);
```

Kein Upload, kein Netz, und das Ergebnis ist ein Vektorbaum, den jeder Designer
auseinandernehmen kann. Grenze ist der Code-Cap von 50 000 Zeichen je Aufruf — die
Logos in `assets/logos/` liegen zwischen 250 B und 22 KB. Praktisch heißt das: alles
unter ~5 KB direkt einsetzen, größere Dateien über den zweiten Weg. Das Markup
vorher von XML-Prolog, DOCTYPE, Kommentaren und Zeilenumbrüchen befreien.

**`rescale()`, nicht `resize()`.** `resize()` dehnt nur den Rahmen, die Pfade darin
bleiben in Originalgröße stehen. Das Seitenverhältnis stimmt schon aus
`logo_masse()`, also genügt `knoten.rescale(zielbreite / knoten.width)`.

**Raster — über `upload_assets` mit `nodeId`.** Erst das Zielrechteck in den Maßen
aus dem Plan anlegen, dann die Bytes darauf hochladen:

1. `figma.createRectangle()` auf `breite` × `hoehe`, an seinen Platz hängen, ID merken.
2. `upload_assets` mit `fileKey`, `nodeId` und `scaleMode` — `FILL` fürs Foto,
   `FIT` fürs Logo.
3. Die zurückgegebene URL an `figma_assets.py` weiterreichen:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --paare arbeit/uploads.json
   ```

Die Antwort des Uploads nennt `placedOnNodeId` — bei einem Rasterbild mit `nodeId`
ist das der Zielknoten, bei einem SVG der neu entstandene Vektorbaum. **Damit muss
auch ein SVG nicht gesucht werden**: ID merken, `rescale()`, an die Stelle des
Platzhalters hängen, Platzhalter entfernen. So gehen auch Logos jenseits des
Code-Caps sauber an ihren Platz.

**Nie `upload_assets` ohne `nodeId`.** Ohne Zielknoten legt es neue Frames
irgendwo auf der Seite ab, und sie hinterher wiederzufinden und einzusortieren ist
Raterei. `figma.createImageAsync` ist gesperrt, `figma.createImage` bräuchte die
Bytes im Code — bei einem 160-KB-Foto sprengt das den Cap.

Das Foto ist bereits in Graustufen und auf 79 × 106pt beschnitten; `extract_input.py`
hat das erledigt. In Figma wird nichts nachgefärbt.

## Schritt für Schritt, nicht auf einmal

Höchstens rund zehn Blöcke je `use_figma`-Aufruf. Der Plan liefert sie in
Reihenfolge, das Stückeln ist damit nur Abzählen. Nach jedem Aufruf die IDs
zurückgeben, nach jedem Frame ein `screenshot()` zur Kontrolle — und wenn etwas
nicht stimmt, erst reparieren, dann weiterbauen.

```js
return { createdNodeIds: [...], frame: f.id, seite: figma.currentPage.id };
```

`use_figma` ist atomar: Ein Skript, das wirft, hat nichts geschrieben. Nach einem
Fehler also nicht blind wiederholen, sondern die Meldung lesen, das Skript
reparieren, erneut senden.

## Was in einer fremden Datei nicht passiert

- **Keine Text-Styles, keine Variablen, keine Komponenten.** Der Frame trägt rohe
  Werte. Eine Datei, in die jemand seinen Lebenslauf legt, soll danach nicht neue
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
| 401/403, `whoami` zeigt nichts | nicht angemeldet, oder keine Bearbeitungsrechte auf der Datei |
| `fileKey` wird abgelehnt | Link zeigt auf `/board/`, `/slides/`, `/make/` oder `/proto/` |
| `unloaded font` | Schnittname ohne Leerzeichen |
| Upload hängt oder bricht ab | im Browser-Chat blockt der Proxy fremde Domains |

Bei Rechte- und Zugriffsfehlern sagt `whoami`, als wer man gerade angemeldet ist —
das ist der schnellste Weg zu der Antwort, ob es am Konto oder an der Datei liegt.
