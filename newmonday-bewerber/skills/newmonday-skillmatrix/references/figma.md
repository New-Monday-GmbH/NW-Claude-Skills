# Figma-Referenz — Weg B: aus dem Bauplan zeichnen

Wie aus den Bauplänen bearbeitbare Frames werden. Es gibt **zwei Fassungen, und
beide kommen nach Figma**:

- **lang**: `arbeit/figma_plan.json` → ein Frame 1444 breit, in einer **fremden**
  Datei — einer, in der es die New-Monday-Komponenten nicht gibt. Für die
  Masterdatei gilt dafür `references/figma-vorlage.md` (Weg A).
- **A4**: `arbeit/figma_plan_a4.json` → je PDF-Seite ein Frame 595 × 842,
  rechts neben dem langen. Immer aus dem Plan, in jeder Datei – auch in der
  Masterdatei gibt es für sie keine Vorlage. Abschnitt „Die A4-Seiten“ unten.

**Vor dem ersten `use_figma`-Aufruf den Skill `figma-use` laden** — dort stehen
die Fallstricke des Plugin-API im Einzelnen, und `skillNames: "figma-use"` gehört
an jeden Aufruf.

Der Plan kommt aus `scripts/figma_plan.py` und trägt jeden Wert fertig: Farben,
Abstände, Radien, Konturen, Schatten und Textstile stammen aus
`assets/tokens.json`, derselben Quelle wie das PDF. Hier wird nichts umgerechnet,
nichts geschätzt und nichts nachgeschlagen — was im Plan steht, wird gesetzt.
Der Plan bildet den Aufbau der Figma-Vorlage nach: Auto-Layout mit Abständen,
Konturen innen, Schatten als Effekte, das Kartenraster als GRID-Layout. Die
Zertifikatssektion plant er mit `scripts/zertifikate.py` – dieselbe
Qualifikationskarte, Reihenfolge, Bündelung und Bildgröße wie im PDF –, und
die Kategorien stehen wie dort: mit `anfrage` in der Reihenfolge der JSON,
ohne die KI-Kategorie zuerst.

## Der Link

```
https://www.figma.com/design/<fileKey>/<Name>?node-id=1-32
```

`fileKey` ist der Teil nach `/design/`, `node-id` wird von `1-32` auf `1:32`
gedreht. **Nur `/design/`.** `/board/` ist FigJam, `/slides/` sind Slides, `/make/`
und `/proto/` können gar nicht beschrieben werden — dann nicht probieren, sondern
sagen, dass eine Design-Datei gebraucht wird. Die PDFs sind da längst fertig.

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

Steht unverändert am Anfang **jedes** Bau-Aufrufs, für beide Pläne. Oben kommen
vier Werte hinein, alles andere ist fest.

```js
const SEITE_ID  = "<ID der Zielseite>";
const ELTERN_ID = null;   // Rahmen-Schritt: null. Danach die ID aus `ids` eines früheren Schritts.
const POSITION  = null;   // Rahmen-Schritt: {x, y} (A4-Seiten, siehe unten) oder null = rechts neben allem
const KNOTEN    = {};     // Ausgabe von: python3 figma_plan.py --schritt <nr> arbeit/figma_plan[_a4].json

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
      // Umbrechende Reihe (Tags der Qualifikationskarte): Zeilen mit demselben
      // Abstand wie die Tags nebeneinander.
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
  // Nach so vielen Zeilen mit "…" enden - wie line-clamp im PDF. ERST nach
  // groesse(): textAutoResize = "HEIGHT" setzt die Kuerzung sonst zurueck.
  if (n.typ === "text" && n.max_zeilen) { k.textTruncation = "ENDING"; k.maxLines = n.max_zeilen; }
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
if (!ELTERN_ID) {                                   // Rahmen-Schritt: Stelle, Arbeitsanzeige an
  if (POSITION) { neu.x = POSITION.x; neu.y = POSITION.y; }
  else {
    const andere = seite.children.filter(c => c.id !== neu.id);
    neu.x = andere.length ? Math.max(...andere.map(c => c.x + c.width)) + 100 : 0;
    neu.y = 0;
  }
  neu.placeholder = true;
}
return { ids, knoten: neu.id, hoehe: neu.height };
```

Zu den Stellen, die still danebengehen, wenn man sie anders macht:

- **Konturen liegen innen** und zählen im Auto-Layout mit (`strokesIncludedInLayout`)
  — so rechnet die Vorlage. Einzige Ausnahme ist die Linie unter der Fußfrage
  (`im_layout: false`): Sie liegt auf den untersten 1pt des Abstands.
- **Einseitige Konturen** (Linie über dem Rumpf, unter dem Kategorielabel und der
  Fußfrage) sind `strokeTopWeight` … `strokeLeftWeight`, kein Ersatzrechteck.
- **Das Kartenraster ist ein GRID**: drei Spalten, Zeilen erst nach den Karten auf
  `HUG`, dann der Rahmen auf `HUG`. Die Karten stehen auf `FILL`/`FILL` — nur so
  sind Karten einer Zeile gleich hoch, ohne feste Höhe. Ein `HUG`-Rahmen mit
  `FLEX`-Zeilen ist ungültig; deshalb die Reihenfolge.
- **Die Fotokarte hat kein Auto-Layout**: Foto und Verlauf liegen frei darin, der
  Verlauf wird erst nach seinen Texten unten bündig gesetzt. Die Kontur der Karte
  liegt in Figma über den Kindern — wie in der Komponente.
- **Leere Punkte sind Ringe**: Rechteck in der Größe der vollen (lang 8 × 8,
  Radius 4; A4 6 × 6, Radius 3), Füllung weiß, Kontur 1,5 innen in
  `roh/punkt-rahmen` (`#6b7b7e`, in Figma an keine Variable gebunden). Im Plan
  trägt jeder leere Punkt seine `kontur`, der Baukasten setzt sie wie jede
  andere; volle Punkte haben keine. Nicht als Ellipse und nicht mit
  `strokeAlign = "CENTER"` – dann wäre der Ring größer als der volle Punkt.
- **Schatten sind Effekte** mit den Werten aus `tokens.json` (`Shadows/shadow-xs`
  an den Skill-Karten und Zertifikatskacheln). Die Qualifikationskarte hat
  keinen, nur die Kontur.
- **Die Tag-Reihe bricht um** (`layoutWrap = "WRAP"`), mit 8 Padding oben und 8
  Abstand in beide Richtungen – wie die Komponente „Zertifikate Erklärung“.
  Gesetzt wird das Umbrechen beim Anlegen, wirksam wird es, sobald die Reihe
  nach `appendChild` auf `FILL` steht. Satz und Tags werden nicht gekürzt.
- **Zertifikatsbilder haben schon ihr Format.** Jedes Rechteck `Zertifikat n` ist
  so groß wie das eingepasste Bild – Seitenverhältnis der Datei – und bekommt es
  mit `scaleMode: "FIT"` (siehe unten). Mit FILL oder einem anderen Rechteck
  würde beschnitten oder verzerrt.
- **Feste Höhen in den Kacheln** (Textfeld 73, Bühne 140) und `maxLines` an Titel
  und „Aussteller · Jahr“ halten die Sektion bei 924 – auch wenn Figma eine Zeile
  anders umbricht. Die Qualifikationskarte huggt; der Plan rechnet ihre Tags so
  um, wie das PDF umbricht, Figma kommt höchstens auf so viele Zeilen.

## Die Bauschritte

`python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py skillmatrix.json arbeit/ --pdf "<pdf>" --pdf-a4 "<A4-pdf>"`
schreibt beide Pläne und listet ihre Schritte. Je Schritt ein `use_figma`-Aufruf: Baukasten, `KNOTEN` aus

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --schritt <nr> arbeit/figma_plan.json
```

und `ELTERN_ID` aus den `ids` der Schritte davor:

| Schritt | Eltern | liefert in `ids` |
|---|---|---|
| 1 Rahmen mit Kopf, Hero, leerem Rumpf, Fuß | Seite (`null`) | Rahmen, `Rumpf`, `Foto` |
| Zertifikate (falls belegt) – Überschrift, Qualifikationskarte, Kacheln | `Rumpf` | `Zertifikat 1` … (nur Einträge mit Bild) |
| Kernkompetenzen: Überschrift, leere Liste | `Rumpf` | `Kategorien` |
| je Kategorie einer | `Kategorien` | — |
| Tools (falls welche in der JSON stehen) | `Rumpf` | — |

Die Reihenfolge der Schritte ist die Reihenfolge im Rumpf — mit
`"zertifikate_position": "ende"` stehen die Zertifikate hinten, der Plan hat das
schon sortiert.

Vor dem Bauen die Ausgabe des Planskripts lesen: `plan.zertifikate` nennt
Kacheln, Karte (Höhe, Tags, Tag-Zeilen), Bündel und die Höhe der Sektion –
geplant und im Plan nachgerechnet (`hoehe_geplant`, `hoehe_plan`, beide
höchstens `grenze` 924) –,
`plan.rahmen.hoehe_geschaetzt` die nachgerechnete Rahmenhöhe. Die Hinweise
(Bündelung, gekürzte Aussteller, KI-Kategorie nach vorn bzw. die Reihenfolge
zur Anfrage) sind dieselben wie beim Rendern. Nach jedem Schritt `get_screenshot` auf den Rahmen; stimmt etwas
nicht, erst reparieren, dann weiterbauen.

`use_figma` ist atomar: Ein Skript, das wirft, hat nichts geschrieben. Nach einem
Fehler also nicht blind wiederholen, sondern die Meldung lesen, das Skript
reparieren, erneut senden.

## Bilder: Foto und Zertifikate

Die Platzhalter (`typ: "bild"`) sind leere Rechtecke in Zielgröße; `plan.uploads`
sagt, welche Datei auf welchen gehört. Je Bild:

1. `upload_assets` mit `fileKey`, `nodeId` (aus `ids`), `count: 1` und dem
   `scaleMode` aus `plan.uploads`: **FILL fürs Foto** – es ist schon im
   Kartenformat zugeschnitten, mit dem Kopf in der Mitte (`kopf_ausschnitt.py`) –,
   **FIT für Zertifikate**: Ihr Rechteck hat das Seitenverhältnis der Datei, FIT
   zeigt das Bild ganz, unbeschnitten und unverzerrt, wie `contain` im PDF.
2. Die zurückgegebene URL an `figma_assets.py` weiterreichen:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --paare arbeit/uploads.json
   ```

`nodeId` geht nur bei `count: 1` — mehrere Bilder heißen mehrere Aufrufe. (Wer
`nodeIds` mit mehreren Zielen nutzt: Ein Aufruf trägt nur einen `scaleMode`,
Foto und Zertifikate also getrennt hochladen.) **Nie
`upload_assets` ohne `nodeId`**: Ohne Zielknoten landen neue Frames irgendwo auf
der Seite. `figma.createImageAsync` ist gesperrt, `figma.createImage` bräuchte die
Bytes im Code — bei einem 160-KB-Foto sprengt das den Cap.

## Abschluss

Ein letzter Aufruf: `placeholder = false` am Rahmen, dann `F.height` gegen
`plan.rahmen.hoehe_pdf` halten. **±20pt sind normal** (Figma und WeasyPrint brechen
Zeilen minimal anders um), mehr ist ein Hinweis, dass ein Block nicht sitzt.
Dazu die Höhe des Rahmens `Zertifikate` im Rumpf zurückgeben: **höchstens 924**
und nahe `plan.zertifikate.hoehe_plan`. Darüber stimmt etwas am Bau, nicht an den
Daten – nichts von Hand stauchen, den Schritt prüfen. Dann ein `get_screenshot`
über den ganzen Rahmen.

## Die A4-Seiten

Derselbe Baukasten, derselbe Ablauf, mit `arbeit/figma_plan_a4.json`. Der Plan
bildet den abgenommenen Vorschlag nach (Frames `2347:48` ff. in Florians Datei,
Maße in `references/layout.md`, „Die A4-Fassung“) und nimmt jeden Wert aus dem
Block `a4` in `tokens.json`.

**Die Seitenaufteilung kommt aus dem PDF**, wie beim Lebenslauf:
`render_skillmatrix.py` legt beim Rendern in der Dokumentinfo des A4-PDFs ab,
welcher Block auf welcher Seite steht, und `figma_plan.py` baut genau diese
Seiten (und meldet, wenn ein Kategorielabel nicht auf seiner Seite im Text
steht). Ohne A4-PDF gibt es keinen A4-Plan – geraten wird nicht.

| Schritt | Eltern | liefert in `ids` |
|---|---|---|
| je Seite: Rahmen mit Kopfzeile, leerem Inhalt – Seite 1 mit Hero, die letzte mit Fuß | Seite (`null`), `POSITION` siehe unten | Rahmen, `Inhalt — Seite n`, auf Seite 1 `Foto` |
| Zertifikate auf Seite n: Überschrift, Karte, leere Kacheln (je Seite, auf der etwas davon steht) | `Inhalt — Seite n` | `Kacheln — Seite n` |
| je Kachelreihe einer | `Kacheln — Seite n` | `Zertifikat 1` … (nur Einträge mit Bild) |
| Kernkompetenzen: Überschrift und leere Liste – auf Folgeseiten nur die Liste („Fortsetzung“) | `Inhalt — Seite n` | `Kategorien — Seite n` |
| je Kategorie einer | `Kategorien — Seite n` | — |
| Tools | `Inhalt — Seite n` | — |

**Wohin.** Seite 1 steht rechts neben dem langen Frame (L), oben bündig, jede
weitere 100 rechts daneben:

```js
const POSITION = { x: L.x + L.width + 100 + (n - 1) * (595 + 100), y: L.y };
```

`L` ist der lange Frame aus Schritt 1 des langen Plans (`knoten` in dessen
Rückgabe). Liegt in dieser Reihe schon etwas (ein früherer Lauf), rückt die
ganze Reihe rechts neben alles, was auf der Seite steht – überschrieben und
verschoben wird nichts.

Drei Stellen, die sonst still danebengehen:

- **Einträge einer Zeile gleich hoch**: Die Zeile huggt, die Einträge stehen
  senkrecht auf `FILL` – Figma nimmt den höchsten als Maß. Ab der zweiten Zeile
  trägt jeder Eintrag die Haarlinie als Kontur oben (`strokeTopWeight` 0,5,
  innen, im Layout).
- **Der Fuß sitzt unten**, weil der Inhalt der letzten Seite die Höhe füllt
  (`hoehe: "FILL"`) – keine feste Luft, kein Abstandsrahmen wie im Vorschlag.
- **Die Kopfzeile ist 13,5 hoch**, das Badge auf Seite 1 20: Es ragt oben und
  unten gleich weit hinaus, wie im PDF. Nicht auf HUG stellen.

**Bilder:** `plan.uploads` nennt `Foto` (der A4-Zuschnitt `foto-<name>-a4.png`,
**FILL** – er hat schon das Format 108 : 99, Kopf mit Luft über dem Haar) und die
Zertifikate (**FIT**). Wie oben, getrennt nach `scaleMode`.

**Abschluss:** `placeholder = false` an jeder Seite. Je Seite zurückgeben, wo der
Inhalt endet – höchstens bei 810, auf der letzten Seite über dem Fuß, und nahe
`plan.rahmen.inhalt_geschaetzt` (+ 60) – und dass der Fuß bei 745–810 steht.
Dann ein `get_screenshot` je Seite und neben die PDF-Seiten legen: nichts
abgeschnitten, das Porträt mit Luft über dem Haar, Bilder unverzerrt.

## Was in einer fremden Datei nicht passiert

- **Keine Text-Styles, keine Variablen, keine Komponenten.** Der Frame trägt rohe
  Werte. Eine Datei, in die jemand seine Skillmatrix legt, soll danach nicht neue
  Styles in jeder Auswahlliste haben.
- **Nichts umbenennen, nichts löschen, nichts verschieben**, was schon da war.
- **Nichts überschreiben.** Steht dort schon ein Frame gleichen Namens, kommt der
  neue daneben.

## Wenn es schiefgeht

Alles hier ist Zugabe. Die PDFs sind fertig und gehen so oder so raus — mit einem
Satz dazu, was an Figma nicht ging:

| Symptom | Was dahintersteckt |
|---|---|
| Werkzeug nicht vorhanden | Figma-MCP nicht verbunden |
| „you don't have edit access“, 401/403 | angemeldetes Konto hat keine Bearbeitungsrechte — `whoami` |
| `fileKey` wird abgelehnt | Link zeigt auf `/board/`, `/slides/`, `/make/` oder `/proto/` |
| `unloaded font` | Schnittname anders geschrieben als in `plan.schriften` |
| `HUG`/`FILL` wird abgelehnt | vor `appendChild` gesetzt, oder `FILL` ohne Auto-Layout-Eltern |
| Textknoten auf Nullbreite | `FILL` ohne vorher `textAutoResize = "HEIGHT"` |
| Zertifikatsbild beschnitten oder leer gerändert | mit `scaleMode: "FILL"` hochgeladen statt FIT, oder Rechteck nicht aus dem Plan |
| Zertifikatssektion höher als 924 | `maxLines` fehlt an einem Titel, eine feste Höhe (Textfeld 73, Bühne 140) wurde zu HUG, oder die Tag-Reihe bricht nicht um (`layoutWrap` fehlt, Reihe nicht auf FILL) |
| Karten einer Zeile ungleich hoch | Kartenraster nicht als GRID gebaut oder Zeilen nicht auf `HUG` |
| Upload hängt oder bricht ab | im Browser-Chat blockt der Proxy fremde Domains |
| „keine Seitenaufteilung im PDF“ | A4-PDF nicht mit `render_skillmatrix.py` gerendert oder nachträglich neu gespeichert – neu rendern |
| A4-Seite unten abgeschnitten | Inhalt der Seite höher als 750 (letzte: über dem Fuß) – das PDF bricht dort anders; Plan neu aus dem aktuellen PDF erzeugen |
| Einträge einer Zeile ungleich hoch | Eintrag nicht auf `FILL` gesetzt oder Zeile nicht auf `HUG` |
