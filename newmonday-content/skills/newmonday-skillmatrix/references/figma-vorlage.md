# Figma-Referenz — Weg über die Vorlage

Der zweite Weg in Figma, und für die New-Monday-Masterdatei der **richtige**:
Die Skillmatrix wird nicht aus rohen Knoten gezeichnet, sondern aus der
bestehenden Vorlage geklont und befüllt.

`references/figma.md` beschreibt den anderen Weg — Aufbau aus
`arbeit/figma_plan.json` in eine fremde, leere Datei. Der bleibt gültig für
Kundendateien, in denen es keine New-Monday-Komponenten gibt. **Sobald die
Masterdatei im Spiel ist, gilt dieses Dokument.**

## Warum klonen und nicht zeichnen

Gezeichnet wird jedes Element aus Maßen — und jedes Element, für das keine Maße
vorliegen, wird geraten. Genau dort entstehen erfundene Icons, Schatten,
Verläufe und Bildinhalte. Die Vorlage trägt all das bereits korrekt; ein Klon
kann es nicht falsch machen, weil er es nicht neu erfindet.

Zweiter Grund: Der Klon bleibt an die Komponenten der Datei gebunden. Ändert
jemand später die Komponente `Skill Card`, ziehen alle Matrizen mit. Ein
gezeichneter Frame tut das nie.

**Der Frame ist 1444pt breit, nicht 1440.** Die Zahl aus `layout.md` stammt aus
dem PDF-Nachbau; die Masterdatei misst 1444. Wer hier 1440 setzt, baut am
Original vorbei.

## Die Masterdatei

| | |
|---|---|
| Datei | `Portfolio - CV Master`, fileKey `oezbaw261xDwxthPuX3ZpS` |
| Vorlagenframe | `Nachbau`, Knoten `4008:13506` — die vollständige Skillmatrix |
| Komponentenseite | `Components` (`0:1`) |

Die Vorlage trägt Wissem Kordis Inhalte. Sie ist Vorlage, nicht Beispiel:
**wird nie verändert**, immer nur geklont.

## Die Komponenten

Alle auf Seite `Components`. Keine trägt Component-Properties — Texte werden
direkt auf den Layern der Instanz überschrieben. Einzige Ausnahme ist `Dots`.

| Komponente | Knoten | Was drinsteckt |
|---|---|---|
| `Header` | `4001:11603` | Teal-Balken mit Wortmarke, 1444 × 65 |
| `Hero` | `4007:12611` | Badge, Name, Rolle, Beschreibung, drei Tags, Fotokarte |
| `Zertifikate Section` | `4007:12765` | Überschrift, Zertifikatskarte mit Chips, Bilderraster |
| `Text` (Set) | `4006:12163` | Sektionsüberschriften, Variante `Variante` |
| `Skill Section` | `4008:13204` | Kategorielabel + **sechs** Skill Cards |
| `Skill Card` | in `Skill Section` | Titel, `Dots`, Beschreibung, 380 × 108 |
| `Dots` (Set) | `4006:12292` | Bewertung, Variante `Filled` = `5`…`1` |
| `Footer` | `4006:12178` | Frage, Wortmarke, drei Kontaktspalten |

## Der Ablauf

### 1. Klonen und umhängen

```js
const vorlage = await figma.getNodeByIdAsync("4008:13506");
const ziel    = await figma.getNodeByIdAsync("<Zielseite>");
const klon = vorlage.clone();
klon.name = "Skillmatrix — Vorname Nachname";
ziel.appendChild(klon);
klon.x = 0; klon.y = 0;
klon.placeholder = true;        // am Ende wieder false
```

Der ganze Baum läuft auf Auto-Layout (`VERTICAL`, Höhe `HUG`). Entfernte
Blöcke fließen deshalb sauber nach, und der Frame schrumpft von selbst.

### 2. Sektionen ohne Beleg entfernen

Die Zertifikatssektion ist ein direktes Kind von `Frame 83` und **kein**
Instanz-Unterlayer — sie lässt sich also wirklich entfernen:

```js
const f83 = klon.children[0].children[1].children[1];
const zert = f83.children.find(c => c.name === "Zertifikate Section");
if (zert) zert.remove();
```

**Das ist der wichtigste Handgriff des ganzen Dokuments.** Bringt der Eingang
keine Zertifikate mit, bleiben sonst die Bilder aus der Vorlage stehen — und
behaupten Qualifikationen, die der Kandidat nie erworben hat. Eine Matrix ohne
Zertifikatssektion ist vollständig; eine mit fremden Zertifikaten ist eine
Falschaussage.

Dieselbe Regel gilt für jeden anderen Block, für den das Material nichts
hergibt: entfernen, nicht mit Vorlageninhalt stehen lassen.

### 3. Texte überschreiben

Die Layernamen sind die alten Texte der Vorlage und teils mehrfach vergeben
(alle drei Hero-Tags heißen `Agentic Coding`). **Gematcht wird deshalb über
`characters`, nicht über den Namen.**

```js
async function setzeText(n, neu){
  // Die Schrift des Knotens laden, wie er sie gerade traegt — nicht raten.
  for (const s of n.getStyledTextSegments(["fontName"])) await figma.loadFontAsync(s.fontName);
  n.characters = neu;
}
```

`getStyledTextSegments(["fontName"])` statt `n.fontName`: Trägt ein Knoten
gemischte Schnitte, ist `n.fontName` `figma.mixed` und `loadFontAsync` wirft.

Der Hero braucht diese Ersetzungen — die linke Spalte sind die Vorlagentexte:

| Vorlage | Wird zu |
|---|---|
| `VERFÜGBAR AB JULI 2026` | Verfügbarkeit aus Schritt 0 |
| `Wissem Kordi` (2 Knoten: 60pt und Fotokarte) | Name |
| `Senior UX/UI Designer` | Rolle |
| `Spezialisiert darauf, …` | Hero-Beschreibung, Ich-Perspektive |
| `Agentic Coding` / `AI Design System Automation` / `Vibe Coding` | die drei Schwerpunkte |
| `12+ Jahre Erfahrung` | Erfahrung |

Am Ende prüfen, dass **nichts** übrig bleibt:

```js
klon.findAllWithCriteria({types:["TEXT"]})
    .filter(t => /Wissem|Anthropic|Kordi/i.test(t.characters));   // muss leer sein
```

### 4. Die Bewertungspunkte

`Dots` ist ein Variantenset, kein Haufen Kreise:

```js
const dots = karte.findOne(n => n.type === "INSTANCE" && n.name === "Dots");
dots.setProperties({ Filled: String(punkte) });      // "5" … "1"
```

Nie die Füllfarben der einzelnen `Background`-Rechtecke anfassen — das bricht
die Bindung an die Komponente und überlebt keine Änderung am Design System.

### 5. Die Falle mit den gelöschten Kartenslots

`Skill Section` bringt **sechs** Skill Cards mit. In der Vorlage sind in zwei
der vier Sektionen Karten per Override gelöscht — dort kommen nur fünf an.
Eine Schleife über die vorhandenen Karten füllt dann stillschweigend nur fünf
Einträge, und der sechste verschwindet, ohne dass irgendwas meldet.

**Vor dem Befüllen die Overrides zurücksetzen:**

```js
sektion.resetOverrides();     // holt die sechste Karte zurueck
```

Danach befüllen. Und die Schleife muss den Überhang melden, statt ihn zu
schlucken:

```js
if (karten.length > cards.length)
  bericht.push(`ACHTUNG: ${karten.length - cards.length} Eintrag/Eintraege ohne Slot`);
```

Weniger als sechs Einträge: übrige Karten auf `visible = false`.

**Und damit wird die Sektion beim nächsten Lauf wieder zur Falle.** Eine so
ausgeblendete Karte ist bei der nächsten Lesung nicht mehr da — die Sektion
meldet dann vier Slots statt sechs, und ein fünfter Eintrag verschwindet
wortlos. Gemessen: eine Tools-Sektion mit vier gefüllten und zwei versteckten
Karten kam beim zweiten Anfassen mit `findAll` auf genau vier Treffer.

Daraus folgt die Regel: **vor jedem Befüllen `resetOverrides()`**, nicht nur
beim ersten Mal. Der Aufruf kostet nichts und stellt immer sechs Slots her.
Wer stattdessen prüft, ob genug Slots da sind, prüft zu spät — die Schleife
läuft dann schon über eine zu kurze Liste.

### 6. Die Tools-Sektion

`Tools` bekommt einen **eigenen Block nach dem Muster der Kernkompetenzen**,
nicht eine fünfte Kategorie in deren Frame. Der Weg ist ein Klon:

```js
const toolsBlock = f82.clone();                 // Frame 82 = Kernkompetenzen
toolsBlock.name = "Frame 82 Tools";
f83.insertChild(0, toolsBlock);                 // vor die Kernkompetenzen
// Ueberschrift: Instanz "Text", Variante "Headline Section"
await setzeText(toolsBlock.children[0].findAllWithCriteria({types:["TEXT"]})[0], "Tools");
// im Klon bleibt genau eine Skill Section stehen
const f81 = toolsBlock.children[1];
for (let i = f81.children.length - 2; i >= 0; i--) f81.children[i].remove();
f81.children[0].children[0].visible = false;    // Kategorielabel doppelt zur Ueberschrift
```

Und aus dem Kernkompetenzen-Frame fliegt die Tools-Kategorie heraus, sonst
steht sie zweimal im Dokument. Reihenfolge im Rumpf danach:
**Tools → Kernkompetenzen** (→ Zertifikate, falls belegt).

### 7. Das Foto

`upload_assets` nimmt als `nodeId` nur die Form `123:456`. Der Photo-Knoten
liegt aber in einer Instanz und heißt `I4039:51;4007:12587;4007:12409` — das
Muster wird abgelehnt. Der Weg geht deshalb über den Hash:

1. `upload_assets` **ohne** `nodeId`, `count: 1`.
2. Bytes per `scripts/figma_assets.py` an die `submitUrl` posten. Die Antwort
   nennt `imageHash` und `placedOnNodeId`.
3. Den Hash auf den Zielknoten legen und den Hilfsrahmen wegräumen:

Zielknoten ist der Rahmen **`imageArea`** in der Komponente
`Zertifikate/Profilbild` — **433 × 433, quadratisch**, `clipsContent`. Nicht
mehr der frühere `Photo`-Knoten mit 386 × 511; die Komponente wurde umgebaut,
damit ein voller Bildausschnitt zur Verfügung steht.

**Das Bild wird nicht vorher beschnitten.** Hochgeladen wird das Original, den
Ausschnitt macht Figma:

```js
// 1. mit FILL einsetzen — so laeuft es von Hand auch
area.fills = [{ type: "IMAGE", imageHash: HASH, scaleMode: "FILL" }];
// 2. als Profilbild zuschneiden
area.fills = [{ type: "IMAGE", imageHash: HASH, scaleMode: "CROP",
                imageTransform: [[fw, 0, tx], [0, fh, ty]] }];
const temp = await figma.getNodeByIdAsync(PLACED_ON);
if (temp) temp.remove();          // sonst liegt er auf einer fremden Seite herum
```

`imageTransform` ist der Ausschnitt in Anteilen des **Quellbildes**: `fw`/`fh`
die Kantenlängen, `tx`/`ty` die linke obere Ecke.

**Die Regel gegen Verzerrung:** Der Ausschnitt muss im Quellbild dasselbe
Seitenverhältnis haben wie `imageArea` — und die ist quadratisch. Also

```
fw · Breite(Quelle)  ==  fh · Höhe(Quelle)
```

Bei quadratischer Quelle heißt das schlicht `fw == fh`. Wer den Transform des
Masters blind kopiert, verzerrt: dort steht `fw = 0,6274`, `fh = 0,4183` —
das ergibt nur bei einem 2:3-Hochformat einen quadratischen Ausschnitt.

**Der Master-Ausschnitt als Maßstab.** Damit alle Profilbilder gleich wirken,
wird nicht frei gewählt, sondern nachgemessen: Im Master sitzt der Haaransatz
bei **5 %** der Rahmenhöhe, das Kinn bei rund **70 %** — der Kopf füllt also
etwa 65 % des Rahmens, die Schultern laufen unten in den Verlauf.

```python
kopf  = kinn_y - haar_y            # im Quellbild gemessen
seite = round(kopf / 0.65)         # quadratisch
top   = round(haar_y - 0.05*seite)
left  = round(gesicht_mitte_x - seite/2)
# -> imageTransform = [[seite/W, 0, left/W], [0, seite/H, top/H]]
```

Haaransatz, Schulteransatz und Gesichtsmitte lassen sich am Bild messen: Der
Hintergrund solcher Porträts ist hell und gleichmäßig, alles unter etwa
`Hintergrund − 28` gehört zum Motiv. **Den Ausschnitt vor dem Hochladen einmal
lokal rendern und ansehen** — das ist billiger als ein zweiter Figma-Durchlauf.

Auflösung: Der Ausschnitt landet auf 433pt. Unter ~600px Kantenlänge im
Ausschnitt wird das Bild weich — dann melden, nicht stillschweigend einsetzen.

**Und vorher ansehen.** `pdfimages` fördert aus einem Lebenslauf regelmäßig
mehr Porträts zutage als das eine, das im Dokument sichtbar ist — Reste aus
Vorlagen, Bilder anderer Personen. Jedes automatisch gefundene Foto wird
angesehen, bevor es in ein Kundendokument geht.

## Was nach dem Bau geprüft wird

```js
return {
  instanzen: klon.findAll(n => n.type === "INSTANCE").length,   // nichts detached
  reste: klon.findAllWithCriteria({types:["TEXT"]})
             .filter(t => /Wissem|Kordi|Anthropic/i.test(t.characters)).length,  // 0
  textstyles: (await figma.getLocalTextStylesAsync()).length,   // unveraendert
  vorlage: (await figma.getNodeByIdAsync("4008:13506")).height, // 3454, unberuehrt
};
```

Dazu ein `get_screenshot` über den ganzen Frame. Worauf zu achten ist: steht
das Gesicht frei vom Verlauf, brechen die drei Schwerpunkt-Buttons einzeilig,
läuft kein Kartentitel in die Punkte, ist keine Kategorie halb leer.

## Was nicht passiert

- **Keine Instanz wird detached.** Wer `detachInstance()` ruft, kappt die
  Verbindung zum Design System — genau das, wofür die Datei existiert.
- **Keine neuen Styles, Variablen oder Komponenten.** Der Klon nutzt, was da
  ist.
- **Die Vorlage `Nachbau` wird nicht angefasst.** Nach jedem Lauf steht sie
  unverändert auf 3454pt.
- **Keine Vorlageninhalte als Platzhalter stehen lassen.** Was nicht befüllt
  werden kann, wird entfernt oder ausgeblendet — nie mit fremdem Inhalt
  ausgeliefert.
