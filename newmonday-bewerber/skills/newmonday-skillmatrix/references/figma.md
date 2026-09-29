# Figma-Referenz — Weg B: aus dem Bauplan zeichnen

Wie aus `arbeit/figma_plan.json` ein bearbeitbarer Frame in einer **fremden**
Datei wird — einer, in der es die New-Monday-Komponenten nicht gibt. Für die
Masterdatei gilt `references/figma-vorlage.md` (Weg A).

**Vor dem ersten `use_figma`-Aufruf den Skill `figma-use` laden** — dort stehen
die Fallstricke des Plugin-API im Einzelnen, und `skillNames: "figma-use"` gehört
an jeden Aufruf.

Der Plan kommt aus `scripts/figma_plan.py` und trägt jeden Wert fertig: Farben,
Abstände, Radien, Konturen, Schatten und Textstile stammen aus
`assets/tokens.json`, derselben Quelle wie das PDF. Hier wird nichts umgerechnet,
nichts geschätzt und nichts nachgeschlagen — was im Plan steht, wird gesetzt.
Der Plan bildet den Aufbau der Figma-Vorlage nach: Auto-Layout mit Abständen,
Konturen innen, Schatten als Effekte, das Kartenraster als GRID-Layout.

## Der Link

```
https://www.figma.com/design/<fileKey>/<Name>?node-id=1-32
```

`fileKey` ist der Teil nach `/design/`, `node-id` wird von `1-32` auf `1:32`
gedreht. **Nur `/design/`.** `/board/` ist FigJam, `/slides/` sind Slides, `/make/`
und `/proto/` können gar nicht beschrieben werden — dann nicht probieren, sondern
sagen, dass eine Design-Datei gebraucht wird. Das PDF ist da längst fertig.

## Vorflug

Ein lesender Aufruf, bevor irgendetwas entsteht:

```js
const seiten = figma.root.children.map(p => ({ id: p.id, name: p.name }));
const alle = await figma.listAvailableFontsAsync();
const schnitte = fam => alle.filter(f => f.fontName.family === fam).map(f => f.fontName.style);
return { editor: figma.editorType, seiten,
         inter: schnitte("Inter"), rethink: schnitte("Rethink Sans") };
```

Daraus folgt:

- **Zielseite.** Trägt der Link eine `node-id`, gehört der Frame auf deren Seite.
  Ohne `node-id` eine neue Seite `figma.createPage()` mit dem Namen
  `Skillmatrix — Vorname Nachname`. **Nie ungefragt in eine bestehende Seite
  schreiben**, zu der nichts hinführt — in fremden Dateien liegt dort Arbeit
  anderer Leute.
- **Schnitte.** Jeder Schnitt aus `plan.schriften` muss in der Liste stehen. Fehlt
  einer, bricht der Bau ab, bevor er anfängt.

Scheitert schon der Vorflug an Rechten, sagt `whoami`, als wer man angemeldet
ist — der schnellste Weg zur Antwort, ob es am Konto oder an der Datei liegt.

## Die Schnitte heißen je Familie anders

| Familie | Schnitte im Plan |
|---|---|
| Inter | `Regular`, `Medium`, `Semi Bold`, `Bold` |
| Rethink Sans | `SemiBold` |

Inter schreibt `Semi Bold` **mit** Leerzeichen, Rethink Sans `SemiBold` **ohne**.
Der Plan trägt die Schreibweise je Familie aus `tokens.json` (`figma_schnitte`) —
übernehmen, nicht bilden. Ein falscher Name lässt `loadFontAsync` werfen, und mit
ihm fällt jeder Textknoten des Aufrufs aus.

## Der Baukasten

Steht unverändert am Anfang **jedes** Bau-Aufrufs. Oben kommen drei Werte hinein,
alles andere ist fest.

```js
const SEITE_ID  = "<ID der Zielseite>";
const ELTERN_ID = null;   // Schritt 1: null. Danach die ID aus `ids` eines früheren Schritts.
const KNOTEN    = {};     // Ausgabe von: python3 figma_plan.py --schritt <nr> arbeit/figma_plan.json

const hex = h => ({ r: parseInt(h.slice(1, 3), 16) / 255,
                    g: parseInt(h.slice(3, 5), 16) / 255,
                    b: parseInt(h.slice(5, 7), 16) / 255 });
const solid = h => ({ type: "SOLID", color: hex(h) });
// Verlauf der Fotokarte: oben transparent, ab voll_anteil satt. Die Matrix
// [[0,1,0],[-1,0,1]] laeuft von oben nach unten; die Einheitsmatrix liefe von
// links nach rechts. In gradientStops traegt die Farbe ein a-Feld — die einzige
// Stelle im API, an der das so ist.
function fuellung(v) {
  if (!v) return [];
  if (typeof v === "string") return [solid(v)];
  const c = hex(v.verlauf.farbe);
  return [{ type: "GRADIENT_LINEAR", gradientTransform: [[0, 1, 0], [-1, 0, 1]],
            gradientStops: [{ position: 0, color: { ...c, a: 0 } },
                            { position: v.verlauf.voll_anteil, color: { ...c, a: 1 } },
                            { position: 1, color: { ...c, a: 1 } }] }];
}
const imAutoLayout = k => k.parent && k.parent.type !== "PAGE"
                          && k.parent.layoutMode && k.parent.layoutMode !== "NONE";
const ids = {};

// Groessen erst nach appendChild — HUG/FILL vorher wirft. Texte: erst Breite
// (fest oder FILL), dann HEIGHT; FILL allein faellt auf Nullbreite zusammen.
function groesse(k, n) {
  if (n.typ === "svg") return;                      // schon per rescale() gesetzt
  const w = n.breite, h = n.hoehe;
  if (k.type === "TEXT") {
    if (typeof w === "number") { k.resize(w, k.height); k.textAutoResize = "HEIGHT"; }
    else if (w === "FILL") { k.textAutoResize = "HEIGHT"; k.layoutSizingHorizontal = "FILL"; }
    return;
  }
  if (typeof w === "number" || typeof h === "number")
    k.resize(typeof w === "number" ? w : k.width, typeof h === "number" ? h : k.height);
  const flex = k.type === "FRAME" && (k.layoutMode === "VERTICAL" || k.layoutMode === "HORIZONTAL");
  if (w === "FILL" && imAutoLayout(k)) k.layoutSizingHorizontal = "FILL";
  if (h === "FILL" && imAutoLayout(k)) k.layoutSizingVertical = "FILL";
  if (w === "HUG" && flex) k.layoutSizingHorizontal = "HUG";
  if (h === "HUG" && flex) k.layoutSizingVertical = "HUG";
}

async function bau(n, eltern) {
  let k;
  if (n.typ === "text") {
    const font = { family: n.typo.familie, style: n.typo.schnitt };
    await figma.loadFontAsync(font);                // laden, dann setzen, dann Zeichen
    k = figma.createText();
    k.fontName = font;
    k.characters = n.text;
    k.fontSize = n.typo.groesse;
    k.lineHeight = { unit: n.typo.zeilenhoehe.einheit, value: n.typo.zeilenhoehe.wert };
    k.letterSpacing = { unit: n.typo.laufweite.einheit, value: n.typo.laufweite.wert };
    if (n.typo.versalien) k.textCase = "UPPER";
    k.fills = [solid(n.farbe)];
  } else if (n.typ === "svg") {
    k = figma.createNodeFromSvg(n.svg);
    k.rescale(n.breite / k.width);                  // rescale, nicht resize
    // Das Logo-SVG ist 21 hoch, die Marke darin 20,16: den Rahmen auf die
    // Tokenhoehe kuerzen, ohne die Vektoren zu skalieren - sonst sitzt das
    // Logo im Kopf 0,4 hoeher als im PDF.
    if (n.hoehe && Math.abs(k.height - n.hoehe) > 0.01) {
      k.resizeWithoutConstraints(k.width, n.hoehe); k.clipsContent = true; }
  } else if (n.typ === "ellipse") {
    k = figma.createEllipse(); k.resize(n.breite, n.hoehe);
  } else if (n.typ === "rechteck" || n.typ === "bild") {
    k = figma.createRectangle(); k.resize(n.breite, n.hoehe);
    if (n.radius) k.cornerRadius = n.radius;
  } else if (n.layout === "GRID") {
    k = figma.createFrame();
    k.layoutMode = "GRID";
    k.gridColumnCount = n.raster.spalten;
    k.gridAutoTracks = "ROWS";                      // Zeilen entstehen mit den Karten
    k.gridRowGap = n.raster.zeilenabstand;
    k.gridColumnGap = n.raster.spaltenabstand;
  } else {
    k = n.layout ? figma.createAutoLayout(n.layout) : figma.createFrame();
    if (n.layout) {
      k.itemSpacing = n.abstand;
      [k.paddingTop, k.paddingRight, k.paddingBottom, k.paddingLeft] = n.padding;
      k.primaryAxisAlignItems = n.haupt;
      k.counterAxisAlignItems = n.quer;
      if (n.umbruch) { k.layoutWrap = "WRAP"; k.counterAxisSpacing = n.umbruch; }
    }
  }
  k.name = n.name;
  if (n.typ !== "text" && n.typ !== "svg") k.fills = fuellung(n.fuellung);
  if (n.typ === "rahmen") {
    k.clipsContent = !!n.clip;
    if (n.radius) k.cornerRadius = n.radius;
  }
  if (n.kontur) {
    k.strokes = [solid(n.kontur.farbe)];
    k.strokeAlign = "INSIDE";
    if (n.kontur.seiten)                            // einseitig: Figma kann das direkt
      [k.strokeTopWeight, k.strokeRightWeight, k.strokeBottomWeight, k.strokeLeftWeight] = n.kontur.seiten;
    else k.strokeWeight = n.kontur.breite;
    if (n.layout === "VERTICAL" || n.layout === "HORIZONTAL")
      k.strokesIncludedInLayout = n.kontur.im_layout;
  }
  if (n.schatten)
    k.effects = n.schatten.map(e => ({ type: "DROP_SHADOW", visible: true, blendMode: "NORMAL",
      color: { ...hex(e.farbe), a: e.deckkraft }, offset: { x: e.x, y: e.y },
      radius: e.blur, spread: e.spread, showShadowBehindNode: true }));
  if (n.deckkraft !== undefined) k.opacity = n.deckkraft;

  eltern.appendChild(k);
  groesse(k, n);
  if (n.min_hoehe) k.minHeight = n.min_hoehe;       // Skill Card: nie niedriger als in der Vorlage
  if (n.absolut) {
    if (imAutoLayout(k)) k.layoutPositioning = "ABSOLUTE";   // ZUERST, dann x/y
    k.x = n.absolut.x;
    if (n.absolut.y !== undefined) k.y = n.absolut.y;
  }
  if (n.merken) ids[n.name] = k.id;

  for (const kind of n.kinder || []) await bau(kind, k);

  if (n.layout === "GRID") {                        // erst wenn alle Karten drin sind
    for (const zeile of k.gridRowSizes) zeile.type = "HUG";
    k.layoutSizingVertical = "HUG";
  }
  if (n.absolut && n.absolut.unten !== undefined) { // unten buendig braucht die fertige Hoehe
    k.y = eltern.height - k.height - n.absolut.unten;
    k.constraints = { horizontal: "CENTER", vertical: "MAX" };
  }
  return k;
}

const seite = await figma.getNodeByIdAsync(SEITE_ID);
await figma.setCurrentPageAsync(seite);
const eltern = ELTERN_ID ? await figma.getNodeByIdAsync(ELTERN_ID) : seite;
const neu = await bau(KNOTEN, eltern);
if (!ELTERN_ID) {                                   // Schritt 1: freie Stelle, Arbeitsanzeige an
  const andere = seite.children.filter(c => c.id !== neu.id);
  neu.x = andere.length ? Math.max(...andere.map(c => c.x + c.width)) + 100 : 0;
  neu.y = 0;
  neu.placeholder = true;
}
return { ids, knoten: neu.id, hoehe: neu.height };
```

Zu den Stellen, die still danebengehen, wenn man sie anders macht:

- **Konturen liegen innen** und zählen im Auto-Layout mit (`strokesIncludedInLayout`)
  — so rechnet die Vorlage. Einzige Ausnahme ist die Linie unter der Fußfrage
  (`im_layout: false`): Sie liegt auf den untersten 1pt des Abstands.
- **Einseitige Konturen** (Zertifikatskante links, Linie über dem Rumpf, unter dem
  Kategorielabel und der Fußfrage) sind `strokeTopWeight` … `strokeLeftWeight`,
  kein Ersatzrechteck.
- **Das Kartenraster ist ein GRID**: drei Spalten, Zeilen erst nach den Karten auf
  `HUG`, dann der Rahmen auf `HUG`. Die Karten stehen auf `FILL`/`FILL` — nur so
  sind Karten einer Zeile gleich hoch, ohne feste Höhe. Ein `HUG`-Rahmen mit
  `FLEX`-Zeilen ist ungültig; deshalb die Reihenfolge.
- **Die Fotokarte hat kein Auto-Layout**: Foto und Verlauf liegen frei darin, der
  Verlauf wird erst nach seinen Texten unten bündig gesetzt. Die Kontur der Karte
  liegt in Figma über den Kindern — wie in der Komponente.
- **Schatten sind Effekte** mit den Werten aus `tokens.json` (`Shadows/shadow-xs`
  an den Skill-Karten, `Shadows/shadow-md` an der Zertifikatskarte).

## Die Bauschritte

`python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py skillmatrix.json arbeit/ --pdf "<pdf>"`
listet die Schritte. Je Schritt ein `use_figma`-Aufruf: Baukasten, `KNOTEN` aus

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --schritt <nr> arbeit/figma_plan.json
```

und `ELTERN_ID` aus den `ids` der Schritte davor:

| Schritt | Eltern | liefert in `ids` |
|---|---|---|
| 1 Rahmen mit Kopf, Hero, leerem Rumpf, Fuß | Seite (`null`) | Rahmen, `Rumpf`, `Foto` |
| Zertifikate (falls belegt) | `Rumpf` | `Zertifikat 1` … |
| Kernkompetenzen: Überschrift, leere Liste | `Rumpf` | `Kategorien` |
| je Kategorie einer | `Kategorien` | — |
| Tools (falls welche in der JSON stehen) | `Rumpf` | — |

Die Reihenfolge der Schritte ist die Reihenfolge im Rumpf — mit
`"zertifikate_position": "ende"` stehen die Zertifikate hinten, der Plan hat das
schon sortiert. Nach jedem Schritt `get_screenshot` auf den Rahmen; stimmt etwas
nicht, erst reparieren, dann weiterbauen.

`use_figma` ist atomar: Ein Skript, das wirft, hat nichts geschrieben. Nach einem
Fehler also nicht blind wiederholen, sondern die Meldung lesen, das Skript
reparieren, erneut senden.

## Bilder: Foto und Zertifikate

Die Platzhalter (`typ: "bild"`) sind leere Rechtecke in Zielgröße; `plan.uploads`
sagt, welche Datei auf welchen gehört. Je Bild:

1. `upload_assets` mit `fileKey`, `nodeId` (aus `ids`), `count: 1` und
   `scaleMode: "FILL"`. Das Foto ist schon im Kartenformat zugeschnitten, mit dem
   Kopf in der Mitte (`kopf_ausschnitt.py`); Zertifikatsbilder füllt FILL mittig,
   wie `cover` im PDF.
2. Die zurückgegebene URL an `figma_assets.py` weiterreichen:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --paare arbeit/uploads.json
   ```

`nodeId` geht nur bei `count: 1` — mehrere Bilder heißen mehrere Aufrufe. **Nie
`upload_assets` ohne `nodeId`**: Ohne Zielknoten landen neue Frames irgendwo auf
der Seite. `figma.createImageAsync` ist gesperrt, `figma.createImage` bräuchte die
Bytes im Code — bei einem 160-KB-Foto sprengt das den Cap.

## Abschluss

Ein letzter Aufruf: `placeholder = false` am Rahmen, dann `F.height` gegen
`plan.rahmen.hoehe_pdf` halten. **±20pt sind normal** (Figma und WeasyPrint brechen
Zeilen minimal anders um), mehr ist ein Hinweis, dass ein Block nicht sitzt. Dazu
ein `get_screenshot` über den ganzen Rahmen.

## Was in einer fremden Datei nicht passiert

- **Keine Text-Styles, keine Variablen, keine Komponenten.** Der Frame trägt rohe
  Werte. Eine Datei, in die jemand seine Skillmatrix legt, soll danach nicht neue
  Styles in jeder Auswahlliste haben.
- **Nichts umbenennen, nichts löschen, nichts verschieben**, was schon da war.
- **Nichts überschreiben.** Steht dort schon ein Frame gleichen Namens, kommt der
  neue daneben.

## Wenn es schiefgeht

Alles hier ist Zugabe. Das PDF ist fertig und geht so oder so raus — mit einem
Satz dazu, was an Figma nicht ging:

| Symptom | Was dahintersteckt |
|---|---|
| Werkzeug nicht vorhanden | Figma-MCP nicht verbunden |
| „you don't have edit access“, 401/403 | angemeldetes Konto hat keine Bearbeitungsrechte — `whoami` |
| `fileKey` wird abgelehnt | Link zeigt auf `/board/`, `/slides/`, `/make/` oder `/proto/` |
| `unloaded font` | Schnittname anders geschrieben als in `plan.schriften` |
| `HUG`/`FILL` wird abgelehnt | vor `appendChild` gesetzt, oder `FILL` ohne Auto-Layout-Eltern |
| Textknoten auf Nullbreite | `FILL` ohne vorher `textAutoResize = "HEIGHT"` |
| Chips stehen alle in einer Zeile | `layoutWrap = "WRAP"` ohne feste Breite am Rahmen |
| Karten einer Zeile ungleich hoch | Kartenraster nicht als GRID gebaut oder Zeilen nicht auf `HUG` |
| Upload hängt oder bricht ab | im Browser-Chat blockt der Proxy fremde Domains |
