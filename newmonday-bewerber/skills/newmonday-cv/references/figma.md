# Figma-Referenz

Wie aus `arbeit/figma_plan.json` ein bearbeitbarer Frame wird. Der Plan kommt aus
`scripts/figma_plan.py`, geschrieben wird mit dem Figma-MCP-Werkzeug `use_figma`.

**Vor dem ersten `use_figma`-Aufruf den Skill `figma-use` laden** — dort stehen die
Fallstricke des Plugin-API im Einzelnen, und `skillNames: "figma-use"` gehört an
jeden Aufruf.

Der Plan trägt alle Werte fertig ausgerechnet — aus `assets/tokens.json`, derselben
Quelle, aus der das PDF gesetzt wird. Hier wird nichts mehr umgerechnet, nichts
geschätzt und nichts aus `layout.md` nachgeschlagen: Was im Plan steht, wird
gesetzt. Eine Zahl, die hier im Rezept stünde statt im Plan, wäre die Stelle, an
der Frame und PDF auseinanderlaufen.

## Der Link

```
https://www.figma.com/design/<fileKey>/<Name>?node-id=1-32
```

`fileKey` ist der Teil nach `/design/` (22–128 Zeichen, alphanumerisch), `node-id`
wird von `1-32` auf `1:32` gedreht. Beides geht als `fileKey` bzw. `nodeId` in die
Werkzeugaufrufe.

**Nur `/design/`.** `/board/` ist FigJam, `/slides/` sind Slides, `/make/` und
`/proto/` können gar nicht beschrieben werden. In allen vier Fällen nicht
probieren, sondern sagen, dass eine Design-Datei gebraucht wird — die PDFs sind
da längst fertig.

### Kein Link

Figma ist kein Wenn mehr, nur noch ein Wohin. Kommt kein Link, wird also nicht
zurückgefragt, sondern angelegt. **Vorher den Skill `figma-create-new-file`
laden**, so wie `figma-use` vor `use_figma`.

1. `whoami`. Die Antwort nennt die Pläne des angemeldeten Kontos. Bei genau einem
   gilt dessen `key`, bei mehreren wird gefragt, welches Team oder welche
   Organisation es sein soll — geraten wird das nicht: In der falschen
   Organisation angelegt, findet die Datei später niemand wieder.
2. `create_new_file` mit `fileName: New Monday CV — Vorname Nachname`,
   `editorType: design` und diesem `planKey`. Ohne `projectId` landet sie in den
   Entwürfen des Kontos. Zurück kommen `fileKey` und Link, und ab da geht es
   weiter wie bei einem übergebenen Link.

Der Vorflug unten gilt weiter, fällt aber kürzer aus: In der frischen Datei ist
die erste Seite leer und gehört uns, eine zweite `figma.createPage()` braucht es
nicht, und die Suche nach der freien Stelle findet nichts — die obere Reihe
beginnt bei (0,0).

**Der Link auf die neue Datei gehört in die Übergabe.** Sonst liegt sie in den
Entwürfen eines Kontos, und niemand weiß von ihr.

Eine Warnung gehört dazu: Die Datei trägt beide Fassungen, den vollen Namen also
im Dateinamen wie in der oberen Reihe. **Anonym ist das PDF, nicht das
Figma-File.** Wer den Link weitergibt, gibt die vollständige Fassung mit.

Scheitert das Anlegen, hält es die PDFs nicht auf — es gilt, was unter
*Wenn es schiefgeht* steht.

## Vorflug

Ein lesender Aufruf, bevor irgendetwas entsteht:

```js
const seiten = figma.root.children.map(p => ({ id: p.id, name: p.name }));
const gebraucht = PLAN_SCHRIFT;   // plan.schrift, z. B. {"Inter": ["Bold","Regular"], "Rethink Sans": ["SemiBold"]}
const da = await figma.listAvailableFontsAsync();
const fehlen = [];
for (const [familie, schnitte] of Object.entries(gebraucht))
  for (const s of schnitte)
    if (!da.some(f => f.fontName.family === familie && f.fontName.style === s))
      fehlen.push(`${familie} ${s}`);
return { seiten, fehlen, editor: figma.editorType };
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
- **Schnitte.** Ist `fehlen` nicht leer, bricht der Bau ab, bevor er anfängt.

## Die Schnitte heißen je Familie anders

| Stil | Familie | Figma-Schnitt |
|---|---|---|
| Name | `Rethink Sans` | `SemiBold` — **ohne** Leerzeichen |
| alles übrige, normal | `Inter` | `Regular` |
| alles übrige, fett | `Inter` | `Bold` |

Die Schreibweise ist nicht einheitlich: Inter heißt in Figma „Semi Bold" mit
Leerzeichen, Rethink Sans „SemiBold" ohne. Falsch geschrieben wirft
`loadFontAsync`, und mit ihm fällt jeder Textknoten des Frames aus. Der Plan
schreibt Familie und Schnitt schon in der Figma-Schreibweise an jeden Stil
(`familie`, `schnitt`) — sie werden übernommen, nicht gebildet.

## Werkzeuge, die im Plan stecken

Diese drei Helfer stehen am Anfang jedes Bau-Aufrufs. Alles Weitere ist ihre
Anwendung.

```js
const hex = h => ({ r: parseInt(h.slice(1,3),16)/255,
                    g: parseInt(h.slice(3,5),16)/255,
                    b: parseInt(h.slice(5,7),16)/255 });

// Ein Textknoten nach der kanonischen Reihenfolge: Schrift laden, dann setzen,
// dann Zeichen. Andersherum wirft Figma "unloaded font".
// breite null heißt: so breit wie der Text, kein Umbruch (Verweise, Footer).
async function txt(inhalt, t, breite) {
  const n = figma.createText();
  const schrift = { family: t.familie, style: t.schnitt };
  await figma.loadFontAsync(schrift);
  n.fontName = schrift;
  n.characters = inhalt;
  n.fontSize = t.groesse;
  // zeile ist die Zeilenhöhe in pt, fest gesetzt: Figma rundet Prozentwerte
  // ohnehin auf ganze Punkt, und genau dieser Wert steht auch im PDF.
  n.lineHeight = { unit: "PIXELS", value: t.zeile };
  n.letterSpacing = { unit: "PIXELS", value: t.laufweite };
  if (t.versalien) n.textCase = "UPPER";
  n.fills = [{ type: "SOLID", color: hex(t.farbe) }];
  if (breite === null) { n.textAutoResize = "WIDTH_AND_HEIGHT"; return n; }
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
`itemSpacing` je Rahmen, das Dokument aber viele verschiedene Abstände. Der Frame
läuft deshalb mit `itemSpacing: 0`, und `abstand_oben` aus dem Plan wird zum
`paddingTop` des Blocks. `einzug` (0 oder 120) wird sein `paddingLeft` — so stehen
Aufgaben und Projekte an der Textkante der Station, ohne dass sie in ihr stecken
müssten. Dasselbe gilt innerhalb eines Blocks: Ein Element mit `abstand_oben`
(Firma, Zeitraum, Absätze im Stationskopf) bekommt einen eigenen Rahmen mit
diesem `paddingTop`.

## Der Frame

Pro Eintrag in `plan.frames` ein Rahmen, in der Reihenfolge des Plans:

```js
const R = plan.rahmen;                                    // aus tokens.json
const f = figma.createAutoLayout("VERTICAL", { name: frame.name, itemSpacing: 0 });
f.resize(R.breite, R.hoehe);                              // 595 x 842 = A4 in pt
f.layoutSizingHorizontal = "FIXED"; f.layoutSizingVertical = "FIXED";
f.paddingTop = R.oben; f.paddingRight = R.rechts; f.paddingBottom = R.unten; f.paddingLeft = R.links;
f.fills = [{ type: "SOLID", color: hex(plan.farben.papier) }];
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
- **Der Footer ist breiter als der Satzspiegel**: `block.breite` (475pt), fest,
  von der linken bis zur gespiegelten rechten Randlinie — er ragt damit über das
  rechte Padding des Frames hinaus, und das ist so gewollt. Darin, alles `FIXED`
  auf die Planwerte: die Trennlinie über die volle Breite, dann nach
  `abstand_zur_reihe` die Reihe (horizontal, `SPACE_BETWEEN`) mit dem Logo links
  und dem `spaltenblock` rechts (horizontal, `spaltenabstand`, drei Spalten zu
  `spaltenbreite`). Je Spalte das Label, darunter nach `wert_abstand` die `werte`
  — jeder Wert ein Textknoten, mehrere untereinander mit `werte_abstand`. Die
  Zeilen eines Werts tragen ihren Stil aus `stile` (der Name fett, per
  `setRangeFontName`); Werte werden nicht umbrochen (`txt(…, null)`) — die
  Mailadresse ist breiter als ihre Spalte und ragt in den Zwischenraum, wie in
  Figma.

## Zwei Varianten in einer Datei

Der Skill baut zwei Fassungen, die vollständige und die anonyme. Sie kommen aus
zwei cv.json und damit aus **zwei Plänen**; `figma_plan.py` weiß von der jeweils
anderen nichts und muss es auch nicht.

Beide gehören auf **dieselbe Seite**, nicht auf zwei. Sie unterscheiden sich in
drei Kleinigkeiten — Foto, Name, Verweise —, und wer das prüfen soll, soll dafür
nicht die Seite wechseln.

- **Oben die vollständige Reihe**, wie gehabt nebeneinander, 100pt auseinander.
- **Darunter die anonyme**, beginnend bei `y = oberste_reihe_unterkante + 120`.
  Der senkrechte Abstand ist mit Absicht größer als die 100pt zwischen den
  Frames: Steht er gleich, liest das Auge Spalten statt Reihen, und Seite 1
  vollständig bildet mit Seite 1 anonym scheinbar einen Block.

Nur die obere Reihe sucht sich ihre freie Stelle nach der Regel aus dem Vorflug.
Die untere übernimmt deren linkes `x` und rechnet nur das `y` neu — fragte sie
den Vorflug ein zweites Mal, stünde sie neben der oberen statt unter ihr.

Umbenannt werden muss dabei nichts. Die Frames heißen ohnehin verschieden,
`CV — Timo Muster — Seite 1` gegen `CV — T. M. — Seite 1`, weil beide Namen aus
der jeweiligen cv.json kommen.

**Erst vollständig, dann anonym.** Bricht der zweite Lauf ab, steht wenigstens
die vollständige Fassung. Andersherum bliebe die Datei mit der halben Lieferung
zurück, und die halbe ist die, die niemand allein verschicken kann.

### Die anonyme Reihe wird geklont, nicht neu gebaut

Vergleicht man die beiden Pläne, unterscheiden sie sich nur an drei Stellen, und
alle drei liegen auf Seite 1: Name, Foto und die Verweiszeile. **Die Seiten 2 bis
n sind bis auf den Frame-Namen identisch.** Sie ein zweites Mal aus dem Plan zu
bauen kostet doppelt so lange und lässt zu, dass die Reihen auseinanderlaufen —
ein Tippfehler in einem der beiden Läufe fällt niemandem auf.

Deshalb: die fertigen Frames klonen, `y` auf die untere Reihe setzen, umbenennen,
und nur in der Kopie von Seite 1 nacharbeiten — Namenstext kürzen, den Rahmen
`Verweise` entfernen, den Fotoknoten gegen die Silhouette tauschen.

**Textknoten nicht über `query('TEXT[characters=…]')` suchen.** Der Selektor
greift bei Werten mit Leerzeichen nicht, und er wirft dabei nicht, sondern findet
schlicht nichts: Der Name bleibt stehen, der Bau meldet Erfolg. Stattdessen
`findAllWithCriteria({types:["TEXT"]})` und im Ergebnis auf `characters` prüfen.

### Zum Schluss gegenlesen

Nach der anonymen Reihe einmal über alle ihre Frames laufen und prüfen, dass
weder Vor- noch Nachname noch irgendwo in einem Textknoten stehen:

```js
const rest = [];
for (const id of anonymeFrames){
  const frame = await figma.getNodeByIdAsync(id);
  for (const t of frame.findAllWithCriteria({types:["TEXT"]}))
    if (/Vorname|Nachname/.test(t.characters))
      rest.push({frame: frame.name, id: t.id, text: t.characters.slice(0,60)});
}
return {restnennungen: rest};
```

Kommt die Liste nicht leer zurück, ist die Reihe nicht anonym — und das sieht am
Bildschirm niemand, weil eine Namenszeile genau dort steht, wo man eine erwartet.
Der Befund gehört in die Übergabe, nicht in einen stillen zweiten Versuch.

## Die Blockarten

Jeder Block trägt `art`, `abstand_oben` und `einzug`. Was darüber hinaus drinsteht,
sagt die Art:

| `art` | Was gebaut wird |
|---|---|
| `kopfzeile` | Die Wortmarke aus `logo` in `logo.breite` × `logo.hoehe` |
| `intro` | Horizontal: Fotospalte (`fotospalte`, `foto.oben` als `paddingTop`), `fotoabstand` als `itemSpacing`, dann die Infospalte mit `name` (`abstand_unten`), `zeilen`, `verweise` |
| `rubrik` | Eine Zeile Überschrift aus `text` im Stil des Blocks |
| `bildung` | Zwei Spalten `spaltenbreite`, `spaltenabstand` auseinander, Umbruch nach zwei Einträgen mit `reihenabstand` dazwischen; je Eintrag `abschluss`, `zeilen`, `themen` |
| `skillset` | Zwei Spalten aus `spalten`, je Gruppe `titel` (`abstand_unten`) und `eintraege` im Stil `liste`, `gruppenabstand` zwischen den Gruppen |
| `profil` | Ein Absatz über die volle Inhaltsbreite |
| `trennlinie` | Eine Linie über die volle Breite, `staerke` pt, Farbe `farbe` (Hex) |
| `station` | Horizontal: `rail` (fest `rail.breite`, Logos **rechtsbündig**, `rail.oben` als `paddingTop`, `rail.abstand` zwischen gestapelten Logos), `spaltenabstand`, dann in `koerperbreite` untereinander `titel`, `firma`, `zeitraum`, `absaetze` — jedes mit seinem `abstand_oben` |
| `aufgaben` | Eine Bulletliste, `abstand` als `listSpacing` (0: ohne Zwischenraum) |
| `projekt` | `logos`, `kunde`, `zeitraum`, `absaetze` — untereinander in `breite`. Die Logos **nebeneinander**, siehe „Projektlogos in einer Reihe" |
| `footer` | fest `breite`: `trennlinie`, dann die Reihe mit Logo und `spaltenblock`, siehe oben |

### Bulletlisten sind echte Listen

Nicht „• " vor den Text schreiben, sondern die Listenfunktion nutzen — sonst
verrutscht die Einrückung, sobald jemand eine Zeile ändert:

```js
const n = await txt(b.eintraege.join("\n"), b, b.breite);
n.setRangeListOptions(0, n.characters.length, { type: "UNORDERED" });
n.setRangeIndentation(0, n.characters.length, 1);
n.listSpacing = b.abstand;           // 0 — die Punkte laufen ohne Zwischenraum
```

**`listSpacing`, nicht `paragraphSpacing`.** Sobald ein Textknoten Listenoptionen
trägt, regelt `listSpacing` den Abstand zwischen den Punkten; `paragraphSpacing`
lässt sich zwar setzen und auch wieder auslesen, bleibt aber wirkungslos. Ob eine
Liste vorliegt, sagt `getRangeListOptions(0, n.characters.length)`; einen
`listOptions`-Getter am Knoten gibt es nicht.

**Die Skillset-Listen nicht nach der Designvorlage nachbauen.** Dort stehen sie auf
25 % Zeilenhöhe plus 10pt Listenabstand; umbricht ein Eintrag, laufen seine Zeilen
3pt auseinander ineinander. Der Plan setzt 13pt Zeilenhöhe und `listSpacing` 0 —
dasselbe Bild, ohne die Falle. Warum die Abstände zu Titel und nächster Gruppe
deshalb 11 und 15pt sind statt 16 und 20: `references/layout.md`.

Figma setzt den Bullet-Einzug selbst; die 15pt aus dem CSS lassen sich nicht auf den
Punkt genau nachstellen. Das ist die einzige bewusste Abweichung vom PDF und fällt
im Dokument nicht auf.

### Die Verweise im Profilkopf

Schwarzer Text, darunter eine Linie in der Markenfarbe — mehr Signal braucht ein
Verweis in einem Dokument nicht, das auch gedruckt wird. Wie in der Designvorlage
ist die Linie keine Unterstreichung, sondern die Unterkante eines Rahmens um den
Text; die Verweise stehen in einer Reihe mit `verweise.abstand` dazwischen
(`layoutWrap = "WRAP"`, `counterAxisSpacing = verweise.zeilenabstand`):

```js
const V = block.verweise;
const rahmen = figma.createAutoLayout("HORIZONTAL", { name: "Verweis", itemSpacing: 0 });
rahmen.fills = [];
const n = await txt(v.text, V, null);
rahmen.appendChild(n);
if (v.unterstrichen) {
  rahmen.strokes = [{ type: "SOLID", color: hex(V.linie.farbe) }];
  rahmen.strokeTopWeight = 0; rahmen.strokeRightWeight = 0; rahmen.strokeLeftWeight = 0;
  rahmen.strokeBottomWeight = V.linie.staerke;
  rahmen.strokeAlign = "INSIDE";
  rahmen.strokesIncludedInLayout = true;   // Linie unter der Zeile, nicht darin
  if (v.url) n.setRangeHyperlink(0, n.characters.length, { type: "URL", value: v.url });
}
```

`unterstrichen: false` heißt: ein Portfolio, das nur als PDF vorliegt. Es hat keine
Adresse, also auch keine Linie und keinen Link.

### Projektlogos in einer Reihe

Mehrere Kunden an einem Projekt: ihre Logos stehen **nebeneinander** über dem
Kundennamen, nicht untereinander wie in der Logospalte der Station. Der Plan sagt
das an `logos.richtung: "nebeneinander"`, dazu `abstand` (16pt zwischen den
Logos), `zeilenabstand` (16pt, falls die Reihe umbricht), `ausrichtung: "mitte"`
und `breite` (die Textspalte, 308pt). Unter der Reihe folgt der Kundenname mit
`abstand_unten`. **`logos` steht an jedem Projekt, auch ohne Logo** — dann mit
leerer `eintraege`-Liste: keine Reihe bauen, und der Kundenname steht ohne
Abstand oben im Projekt, wie im PDF.

```js
// projekt: der Rahmen des Projektblocks (huelle), block: der Planeintrag
const L = block.logos;
const mitLogo = L.eintraege.length > 0;
if (mitLogo) {
  const reihe = figma.createAutoLayout("HORIZONTAL", { name: "Logos", itemSpacing: L.abstand });
  reihe.fills = [];
  reihe.resize(L.breite, reihe.height);        // Umbruch braucht eine feste Breite
  reihe.primaryAxisSizingMode = "FIXED";
  reihe.counterAxisSizingMode = "AUTO";        // so hoch wie das höchste Logo
  reihe.layoutWrap = "WRAP";
  reihe.counterAxisSpacing = L.zeilenabstand;
  reihe.counterAxisAlignItems = "CENTER";      // auf der Mitte zueinander
  // Jedes Logo auf einem der beiden Wege aus „Logos und Foto": SVG direkt
  // (createNodeFromSvg + rescale), Raster als Platzhalter-Rechteck in
  // l.breite × l.hoehe, das später per upload_assets gefüllt wird.
  for (const l of L.eintraege) reihe.appendChild(logoKnoten(l));
  projekt.appendChild(reihe);
}
const kunde = figma.createAutoLayout("VERTICAL", { name: "Kunde", itemSpacing: 0 });
kunde.fills = [];
kunde.paddingTop = mitLogo ? L.abstand_unten : 0;
kunde.appendChild(await txt(block.kunde.text, block.kunde, block.breite));
projekt.appendChild(kunde);
```

`logoKnoten(l)` ist kein Figma-Befehl, sondern steht für die beiden Wege aus
„Logos und Foto" unten — dieselben wie in der Logospalte der Station.

Jedes Projektlogo ist 26pt groß (gleiche Fläche), allein wie in der Reihe — die
Maße stehen fertig am Eintrag.

### Der Stationskopf

Titel, darunter die Firma, darunter der Zeitraum als eigene Zeile, danach die
Absätze (Schlagwortzeile, Beschreibung) — jeder Teil ein eigener Textknoten mit
seinem `abstand_oben`. Einen senkrechten Strich zwischen Zeitraum und Firma gibt
es nicht mehr. Fehlt `firma` oder `zeitraum`, steht dort `null`: Dann entfällt der
Knoten, der Abstand des nächsten bleibt.

## Logos und Foto

Zwei Wege, und die Trennung ist Absicht.

**Alle Pfade im Plan sind absolut.** Die Logos liegen im Skill-Ordner, das Foto im
Arbeitsverzeichnis des Nutzers — relativ ließe sich im Plan nicht mehr
unterscheiden, worauf sich welcher Pfad bezieht. Sie werden gelesen, wie sie
dastehen.

**Welcher der beiden Wege gilt, sagt `typ`** — an jedem Logoeintrag und ebenso am
Foto: `svg` oder `raster`. Entschieden hat das der Plan, hier wird es nicht noch
einmal am Dateinamen aufgerollt.

**SVG — direkt im Code.** Die Datei lesen und das Markup übergeben:

```js
const knoten = figma.createNodeFromSvg(svgMarkup);
knoten.rescale(l.breite / knoten.width);   // nicht resize(), siehe unten
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

**Das Foto kann auch ein SVG sein.** Die anonyme Fassung setzt statt des Porträts
das Platzhalterbild aus `assets/silhouette.svg`; `plan.foto.typ` steht dann auf
`svg`, und es gilt der obere Weg — `createNodeFromSvg` und `rescale()` —, nicht
der Upload. Der Code-Cap ist dabei kein Thema: Von XML-Prolog und Kommentaren
befreit sind es rund 1 400 Zeichen. Das Bild ist der „user-pict-placeholder" aus
dem Design, von `scripts/silhouette.py` über die viewBox in dieselben 79 × 106pt
eingesetzt wie das Foto; der Profilkopf sitzt in beiden Fassungen also gleich. Ein
Frame, der eine graue Figur mit rundem Kopf zeigt, stammt aus einer älteren
Fassung.

Zwei Dinge hängen daran:

- **`clipsContent` auf dem entstandenen Rahmen setzen**, nicht auf die Vorgabe
  vertrauen. Die Vorlage ist 80 × 110 und wird oben und unten um je rund 1,3pt
  beschnitten; ohne Beschnitt ragen Hintergrund und Schultern über den
  Fotoplatz hinaus, und der Profilkopf steht schief.
- **`--foto-raster` dreht den Weg um.** Für Engines, die SVG im `<img>` nicht
  können, legt `anonymisieren.py` die PNG-Silhouette ein; dann steht im Plan
  `raster`, und es gilt der Upload-Weg. Anonym heißt also nicht automatisch
  SVG — gefragt wird `typ`, nicht die Fassung.

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

Die Frames gehören zum Regellauf, aber sie sind nicht der Ausgang. Die PDFs sind
zu diesem Zeitpunkt fertig und gehen so oder so raus — mit einem Satz dazu, was
an Figma nicht ging:

| Symptom | Was dahintersteckt |
|---|---|
| Werkzeug nicht vorhanden | Figma-MCP nicht verbunden |
| 401/403, `whoami` zeigt nichts | nicht angemeldet, oder keine Bearbeitungsrechte auf der Datei |
| `fileKey` wird abgelehnt | Link zeigt auf `/board/`, `/slides/`, `/make/` oder `/proto/` |
| `unloaded font` | Schnittname falsch geschrieben — Inter „Semi Bold" mit, Rethink Sans „SemiBold" ohne Leerzeichen; oder `loadFontAsync` vergessen |
| Upload hängt oder bricht ab | im Browser-Chat blockt der Proxy fremde Domains |

Bei Rechte- und Zugriffsfehlern sagt `whoami`, als wer man gerade angemeldet ist —
das ist der schnellste Weg zu der Antwort, ob es am Konto oder an der Datei liegt.
