# Figma-Referenz — Weg A: die Vorlage klonen

Der Weg für die New-Monday-Masterdatei und jede Datei mit ihren Komponenten: Die
Skillmatrix wird nicht aus rohen Knoten gezeichnet, sondern aus der bestehenden
Vorlage geklont und befüllt.

`references/figma.md` beschreibt den anderen Weg — Aufbau aus
`arbeit/figma_plan.json` in eine fremde, leere Datei. Der bleibt gültig für
Kundendateien ohne New-Monday-Komponenten. **Sobald die Masterdatei im Spiel ist,
gilt dieses Dokument** – für den langen Frame. Die A4-Seiten der zweiten Fassung
haben keine Vorlage und kommen auch hier aus dem Bauplan
(`arbeit/figma_plan_a4.json`, `references/figma.md`, „Die A4-Seiten“), rechts
neben den geklonten Frame.

## Warum klonen und nicht zeichnen

Gezeichnet wird jedes Element aus Maßen — und jedes Element, für das keine Maße
vorliegen, wird geraten. Die Vorlage trägt Icons, Schatten, Verläufe und
Bildrahmen bereits korrekt; ein Klon kann es nicht falsch machen, weil er es nicht
neu erfindet.

Vor allem bleibt der Klon ans Design System gebunden: Farben, Abstände, Radien,
Schatten und Textstile der Komponenten hängen an den Variablen und Styles der
Library. Ändert jemand später die Komponente `Skill Card` oder einen Token, ziehen
alle Matrizen mit. Ein gezeichneter Frame tut das nie.

**Deshalb wird im Klon kein Wert von Hand gesetzt** — keine Füllung, keine
Schrift, kein Abstand, kein Radius, kein Schatten. Überschrieben werden nur
Inhalte: Texte (`characters`), die Bewertung (Variante von `Dots`), das Foto
(`imageHash`), das Ein- und Ausblenden von Karten. Jede andere Überschreibung
kappt die Bindung an das Design System genau dort, wo sie gesetzt wird.

**Der Frame ist 1444pt breit** — genau wie das PDF.

## Die Masterdatei

| | |
|---|---|
| Datei | `Portfolio - CV Master`, fileKey `oezbaw261xDwxthPuX3ZpS` |
| Vorlagenframe | `Skillmatrix`, Knoten `4158:4223`, auf Seite `Skillmatrix` (`4158:3774`) — 1444 × 3776,55 |
| Komponentenseite | `Components / Masterfile` (`0:1`) |

Die Vorlage trägt Wissem Kordis Inhalte. Sie ist Vorlage, nicht Beispiel: **wird
nie verändert**, immer nur geklont. (Der frühere Vorlagenframe `Nachbau`,
`4008:13506`, existiert nicht mehr.)

Ob eine Datei die Komponenten führt, zeigt der Vorflug: Gibt es eine Seite, deren
Name mit `Components` beginnt, und findet `figma.getNodeByIdAsync("4158:4223")`
die Vorlage, gilt Weg A.

## Die Komponenten

Alle auf der Komponentenseite. Texte werden direkt auf den Layern der Instanz
überschrieben — Text-Properties gibt es nicht. Varianten tragen nur die Sets
`Text`, `Zertifikate-Icon` und `Dots`; umgeschaltet wird ausschließlich `Dots`
(Schritt 4).

| Komponente | Knoten | Was drinsteckt |
|---|---|---|
| `Header` | `4001:11603` | Teal-Balken mit `Logo`, 65,16 hoch |
| `Hero` | `4007:12611` | `Badge`, Name, Rolle, Beschreibung, `Tag Reihe`, `Zertifikate/Profilbild` |
| `Zertifikate/Profilbild` | `4007:12416` | Fotokarte 437,33 × 435,34, darin `imageArea` und der Verlauf |
| `Zertifikate Section` | `4007:12765` | Überschrift, `Zertifikate Erklärung` (Karte mit Chips), Bilderraster – alter Aufbau, wird immer entfernt (Schritt 2) |
| `Text` (Set) | `4006:12163` | Überschriften, Variante `Variante` |
| `Zertifikate-Icon` (Set) | `4005:12142` | Sektions-Icons 24 × 24, Variante `Icon` = `Zertifikate`, `Kernkompetenzen`, `Tools` (`4158:10710`) |
| `Skill Section` | `4008:13204` | Kategorielabel + **sechs** Skill Cards im GRID |
| `Skill Card` | `4006:12352` | Titel, `Dots`, Beschreibung |
| `Dots` (Set) | `4006:12292` | Bewertung, Variante `Filled` = `5`…`1` |
| `Footer` | `4006:12178` | Frage, `Logo`, drei Kontaktspalten |

## Der Ablauf

### 1. Klonen und umhängen

```js
const vorlage = await figma.getNodeByIdAsync("4158:4223");
const ziel    = await figma.getNodeByIdAsync("<Zielseite>");
const klon = vorlage.clone();
klon.name = "Skillmatrix — Vorname Nachname";
ziel.appendChild(klon);
klon.x = 0; klon.y = 0;          // bzw. freie Stelle rechts neben dem Vorhandenen
klon.placeholder = true;        // am Ende wieder false
```

Der ganze Baum läuft auf Auto-Layout (`VERTICAL`, Höhe `HUG`). Entfernte Blöcke
fließen deshalb sauber nach, und der Frame schrumpft von selbst.

### 2. Sektionen ohne Beleg entfernen

Die Zertifikatssektion ist ein direktes Kind von `Frame 83` und **kein**
Instanz-Unterlayer — sie lässt sich also wirklich entfernen:

```js
const f83 = klon.children[0].children[1].children[1];   // Frame 86 > Frame 84 > Frame 83
const zert = f83.children.find(c => c.name === "Zertifikate Section");
if (zert) zert.remove();
```

**Das ist der wichtigste Handgriff des ganzen Dokuments.** Bringt der Eingang
keine Zertifikate mit, bleiben sonst die Bilder aus der Vorlage stehen — und
behaupten Qualifikationen, die der Kandidat nie erworben hat. Eine Matrix ohne
Zertifikatssektion ist vollständig; eine mit fremden Zertifikaten ist eine
Falschaussage.

**Mit Zertifikaten wird die Sektion genauso entfernt.** Sie zeigt noch die alte
Karte mit Kante und Chips über dem Bilderraster; Kacheln und die Karte „Erworbene
Qualifikationen“ (SKILL.md, Schritt 3) haben im Master noch keine Komponente –
die Karte gibt es bisher nur in Florians Datei (`Zertifikate Erklärung`,
`2284:964`). An ihre Stelle kommt der Schritt „Zertifikate“ aus dem Bauplan
(`figma_plan.py`, gebaut mit dem Baukasten aus `references/figma.md`, Eltern
`Frame 83`), danach an den Anfang
von `Frame 83` gerückt (`f83.insertChild(0, zertifikate)`; mit
`"zertifikate_position": "ende"` bleibt er hinten). Das ist die einzige Stelle
des Klons mit rohen Werten – aus denselben Tokens wie das PDF. Bilder kommen
mit `scaleMode: "FIT"` auf die Rechtecke `Zertifikat n` (`references/figma.md`,
„Bilder“).

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
gemischte Schnitte, ist `n.fontName` `figma.mixed` und `loadFontAsync` wirft. Name
und Rolle stehen in **Rethink Sans**, alles andere in Inter — auch deshalb wird die
Schrift des Knotens gelesen und nicht angenommen.

Der Hero braucht diese Ersetzungen — die linke Spalte sind die Vorlagentexte:

| Vorlage | Wird zu |
|---|---|
| `VERFÜGBAR AB JULI 2026` | Verfügbarkeit aus Schritt 0, in Versalien |
| `Wissem Kordi` (2 Knoten: 60pt und Fotokarte) | Name |
| `Senior UX/UI Designer` | Rolle |
| `Spezialisiert darauf, …` | Hero-Beschreibung, Ich-Perspektive |
| `Agentic Coding` / `AI Design System Automation` / `Vibe Coding` | die drei Schwerpunkte |
| `12+ Jahre Erfahrung` | Erfahrung |

**Lange Namen oder Rollen umbrechen lassen.** Name und Rolle stehen in der Vorlage
auf „Hug“ und laufen bei Überlänge nach rechts in die Fotokarte (etwa „Senior
UX/UI Product Designer“ bei 60pt). Ist ein 60pt-Text breiter als die Textspalte,
ihn samt Eltern auf `FILL` und den Text auf `textAutoResize = "HEIGHT"` stellen —
er bricht dann wie im PDF in zwei Zeilen:

```js
const spalte = hero.children[0];
for (const t of hero.findAllWithCriteria({types:["TEXT"]}).filter(t => t.fontSize === 60))
  if (t.width > spalte.width + 0.5) {
    const inst = t.parent; inst.parent.layoutSizingHorizontal = "FILL";
    inst.layoutSizingHorizontal = "FILL"; t.textAutoResize = "HEIGHT"; t.layoutSizingHorizontal = "FILL";
  }
```

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

Nie die Füllfarben der einzelnen `Background`-Rechtecke anfassen — das bricht die
Bindung an die Komponente und überlebt keine Änderung am Design System. (Leere
Punkte sind in der Komponente flächig `neutral/10`, Stand 2026-09-28. Seit
2026-10-06 sind sie im Skill Ringe – weiß, Rahmen 1,5 innen in
`roh/punkt-rahmen`, `references/layout.md`. Das gehört in die Komponente `Dots`
der Masterdatei, nicht in den Klon: Bis sie nachgezogen ist, zeigt Weg A die
alten Punkte, und das steht in der Übergabe.)

### 5. Die Kategorien: vollständige Sektion klonen, nicht zurücksetzen

`Skill Section` bringt **sechs** Skill Cards mit. In der Vorlage sind in zwei der
vier Sektionen Karten per Override gelöscht — dort kommen nur fünf an. Eine
Schleife über die vorhandenen Karten füllt dann stillschweigend nur fünf Einträge,
und der sechste verschwindet, ohne dass irgendwas meldet.

**Nicht `resetOverrides()` nehmen.** Das holt zwar die sechste Karte zurück, setzt
aber auch das Raster auf die Master-Komponente zurück — und die weicht von der
Seite „Skillmatrix" ab: Abstände 16 statt 24, und die Karten füllen ihre Spalte,
statt 380 breit zu sein (in der 1188 breiten Vorlage 385,33; der Master selbst ist
1324,33 breit, seine Karten 430,78). Die Label-Linie ist im Master an `base/white`
gebunden statt an `neutral/80` (gemessen 2026-09-28). Die Matrix sähe danach anders
aus als die Vorlage.

Stattdessen je Kategorie **die erste Sektion mit sechs Slots klonen** — der Klon
trägt die Overrides der Vorlage mit, also genau deren Abstände und Breiten — und
die ursprünglichen Sektionen danach entfernen. Gibt es Tools, wird **ein Klon mehr**
angelegt und gleich in den Tools-Block gesetzt, solange das Muster noch da ist
(Schritt 6 findet ihn dort wieder — Variablen überleben einen `use_figma`-Aufruf
nicht):

```js
const f83 = klon.children[0].children[1].children[1];            // wie in Schritt 2
const f82 = f83.children.find(c => c.name === "Frame 82");         // Kernkompetenzen
const f81 = f82.children[1];                     // Frame 82 > Frame 81
const vorhandene = f81.children.filter(c => c.type === "INSTANCE" && c.name === "Skill Section");
const raster = s => s.children.find(c => c.layoutMode === "GRID");       // Frame 78
const karten = s => raster(s).children.filter(c => c.type === "INSTANCE" && c.name === "Skill Card");
const muster = vorhandene.find(s => karten(s).length === 6);
const sektionen = kompetenzen.map(() => {
  const s = muster.clone(); f81.appendChild(s); s.layoutSizingHorizontal = "FILL"; return s; });
const toolsBlock = f83.children.find(c => c.name === "Frame 82 Tools");
if (tools.length) {                                 // Tools-Sektion gegen einen Muster-Klon tauschen
  const tf81 = toolsBlock.children[1];              // Frame 82 Tools > Frame 81
  const alt = tf81.children[0];                     // Skill Section mit dem Master-Raster
  const t = muster.clone(); tf81.appendChild(t); t.layoutSizingHorizontal = "FILL";
  alt.remove();
  t.children.find(c => c.name === "Frame 80").visible = false;   // kein Label unter "Tools"
}
for (const s of vorhandene) s.remove();
```

Danach befüllen — Label, Titel, Beschreibung, `Dots` —, übrige Karten auf
`visible = false`, und die Schleife meldet einen Überhang, statt ihn zu schlucken.
**Die Karten dabei jedes Mal frisch abfragen** (`karten(s)[j]`, nicht eine vorher
gemerkte Liste): `setProperties` auf `Dots` und `visible = false` erneuern die
Knoten im Raster, eine alte Referenz wirft „node does not exist“, und
ausgeblendete Knoten fallen aus `children` heraus – deshalb Raster und Label
nie über die Position (`children[1]`) suchen, sondern über Layout und Namen: Nach
dem Ausblenden von `Frame 80` steht das Raster an Index 0. Erst alle Einträge befüllen,
dann die überzähligen ausblenden:

```js
if (eintraege.length > karten(s).length)
  bericht.push(`ACHTUNG: ${eintraege.length - karten(s).length} Eintrag/Eintraege ohne Slot`);
```

**Dann die Kartenhöhen je Zeile angleichen.** Die Skill Card ist in der Komponente
fest hoch; das Raster wächst nicht von selbst mit dem Text. Ohne Abgleich behält
eine Zeile die Höhe aus der Vorlage (in Sektion 1 sind das 108 und 129), und eine
dreizeilige Beschreibung würde abgeschnitten. Je Dreierreihe die Inhaltshöhe
rechnen, mindestens `skillkarte.mindesthoehe` (108, wie im PDF):

```js
const MIN = 108;
const sichtbar = karten(s).filter(k => k.visible);
for (let r = 0; r < sichtbar.length; r += 3) {
  const zeile = sichtbar.slice(r, r + 3);
  const h = Math.max(MIN, ...zeile.map(k => k.paddingTop + k.paddingBottom + 2   // 2 = Kontur oben und unten
                                          + k.children[0].height + k.itemSpacing + k.children[1].height));
  for (const k of zeile) { k.resize(k.width, h); k.layoutSizingHorizontal = "FILL"; }
}
```

Das ist eine Größe, kein Design-Wert: Abstände, Farben und Schriften bleiben
unangetastet.

### 6. Die Tools-Sektion

Die Vorlage hat einen eigenen Block **`Frame 82 Tools`** in `Frame 83`, **nach**
den Kernkompetenzen: Überschrift „Tools" mit dem Icon `Icon=Tools`
(Zertifikate-Icon-Set), 24 Abstand, darunter eine `Skill Section` ohne
Kategorielabel. Befüllt wird er wie eine Kategorie, mit drei Besonderheiten:

- **Ohne Tools fliegt der ganze Block raus** — wie die Zertifikatssektion. Kein
  Vorlagen-Tool bleibt stehen.
- **Raster wie bei den Kernkompetenzen.** Die `Skill Section` im Tools-Block trägt
  das Raster der Master-Komponente (Abstände 16, Karten 385,33). Festgelegt ist 24
  und 380 wie bei den Kernkompetenzen. Deshalb hat Schritt 5 sie schon durch
  einen Klon des Musters ersetzt und dessen Kategorielabel (`Frame 80`)
  ausgeblendet.
- **Höchstens sechs Tools**, eine Sektion mit zwei Reihen.

```js
const f83 = klon.children[0].children[1].children[1];            // wie in Schritt 2
const toolsBlock = f83.children.find(c => c.name === "Frame 82 Tools");
if (!tools.length) toolsBlock.remove();
else {
  const s = toolsBlock.children[1].children[0];     // der Muster-Klon aus Schritt 5
  // befüllen wie in Schritt 5: Karten frisch abfragen, Überzählige ausblenden,
  // Höhen je Reihe angleichen
}
```

Reihenfolge im Rumpf danach: **Zertifikate → Kernkompetenzen → Tools**. Mit
`"zertifikate_position": "ende"` die Zertifikatssektion ans Ende hängen
(`f83.appendChild(zert)`). Die Kategorien kommen in der Reihenfolge des Plans
(SKILL.md, Schritt 2a): mit `anfrage` wie in der JSON, ohne **eine
KI-Kategorie zuerst**, auch wenn die JSON sie weiter hinten führt.

### 7. Das Foto

`upload_assets` nimmt als `nodeId` nur die Form `123:456`. Der Bildknoten liegt
aber in einer Instanz (`I…;…`) — das Muster wird abgelehnt. Der Weg geht deshalb
über den Hash:

1. `upload_assets` **ohne** `nodeId`, `count: 1`.
2. Bytes per `scripts/figma_assets.py` an die `submitUrl` posten. Die Antwort
   nennt `imageHash` und `placedOnNodeId`.
3. Den Hash auf den Zielknoten legen und den Hilfsrahmen wegräumen.

Zielknoten ist der Rahmen **`imageArea`** in `Zertifikate/Profilbild` —
**435,33 × 433,34**, also fast quadratisch, mit `clipsContent` und 90 % Deckkraft
(die Deckkraft gehört zur Komponente, nicht anfassen).

**Hochgeladen wird das fertig zugeschnittene Foto** – dieselbe Datei wie im PDF
(`person.foto` aus der JSON, erzeugt von `kopf_ausschnitt.py`, SKILL.md
Schritt 1a) –, mit `scaleMode: "FILL"`. Sie hat schon das Seitenverhältnis von
`imageArea` und den Kopf in der Mitte; FILL zeigt sie deshalb genau so wie im
PDF, ohne Verzerrung und ohne zweiten Ausschnitt:

```js
area.fills = [{ type: "IMAGE", imageHash: HASH, scaleMode: "FILL" }];
const temp = await figma.getNodeByIdAsync(PLACED_ON);
if (temp) temp.remove();          // sonst liegt er auf einer fremden Seite herum
```

**Nicht das Original hochladen und in Figma per `imageTransform` zuschneiden.**
Dann gäbe es zwei Ausschnitte – den des Skripts im PDF und einen von Hand
gemessenen im Frame –, und die laufen auseinander. Der Master-Ausschnitt
(Kopf waagerecht mittig, Haaransatz bei 5 %, Kinn bei 70 % der Rahmenhöhe)
steht als `kopf-oben-anteil` / `kinn-anteil` in `tokens.json` und wird nur vom
Skript umgesetzt. (Wer den Transform des Masters kopiert, verzerrt obendrein:
dort steht `fw = 0,6274`, `fh = 0,4183` – das passt nur bei einem
2:3-Hochformat.)

Auflösung: Meldet das Skript unter 100 dpi, das in der Übergabe sagen, nicht
stillschweigend einsetzen.

**Und vorher ansehen.** `pdfimages` fördert aus einem Lebenslauf regelmäßig mehr
Porträts zutage als das eine, das im Dokument sichtbar ist — Reste aus Vorlagen,
Bilder anderer Personen. Jedes automatisch gefundene Foto wird angesehen, bevor
es in ein Kundendokument geht.

## Was nach dem Bau geprüft wird

```js
return {
  instanzen: klon.findAll(n => n.type === "INSTANCE").length,   // nichts detached
  // "Anthropic" stand frueher mit drin - es kam nur aus der Zertifikatskarte der
  // Vorlage, die jetzt immer entfernt wird; echte Anthropic-Zertifikate des
  // Kandidaten sind kein Rest.
  reste: klon.findAllWithCriteria({types:["TEXT"]})
             .filter(t => /Wissem|Kordi/i.test(t.characters)).length,  // 0
  textstyles: (await figma.getLocalTextStylesAsync()).length,   // unveraendert
  vorlage: (await figma.getNodeByIdAsync("4158:4223")).height,  // 3776,55, unberuehrt
};
```

Dazu ein `get_screenshot` über den ganzen Frame. Worauf zu achten ist: steht das
Gesicht frei vom Verlauf, stehen die drei Schwerpunkt-Buttons in einer Zeile,
läuft kein Kartentitel in die Punkte, ist keine Kategorie halb leer.

## Bekannte Unstimmigkeiten der Vorlage (Stand 2026-09-28)

Fünf Stellen der Masterdatei weichen vom System ab. Sie werden **im Master**
behoben, nicht im Klon — ein Klon erbt die ersten beiden bis dahin, das PDF setzt
sie systemkonform um:

- **Kategorielinie zu lang:** In `Skill Section` ist `Frame 80` fest 1259 breit
  statt `FILL`; die Linie unter dem Kategorielabel läuft 61pt über die Karten
  hinaus. Im PDF endet sie 10pt vor der rechten Kante (wie links).
- **Erste Kachelreihe zu hoch:** In `Zertifikate Section` ist die mittlere Kachel
  der ersten Reihe ein loses Rechteck (300 hoch) statt einer `Zertifikate`-Instanz;
  die Reihe ist dadurch 300 statt 278,05 hoch. Seit 2026-10-03 ohne Folgen – die
  Sektion wird im Klon immer ersetzt.
- **Master-Komponente `Skill Section` mit anderem Raster:** Die Komponente hat
  Kartenabstände von 16, ihre Karten füllen die Spalte (im Master 430,78, in der
  Vorlagenbreite 385,33), die Label-Linie ist an `base/white` gebunden; die
  Instanzen auf der Seite „Skillmatrix" überschreiben das auf 24, 380 und
  `neutral/80`. Deshalb klont Schritt 5 eine Sektion der Vorlage, statt
  `resetOverrides()` zu rufen.
- **Master-Komponente `Zertifikate Section` mit anderen Abständen:** Im Master
  stehen die Blöcke 40 auseinander (`spacing-5xl`, an der Wurzel und in
  `Frame 77`), die Kacheln sind 400,67 × 293,17 bei 1250 Breite. Die Instanz der
  Vorlage überschreibt das auf 24 und 32 (`spacing-3xl` / `spacing-4xl`) bei 1188.
  Weg A behält die Instanz; wer sie neu aus dem Master zieht oder
  `resetOverrides()` ruft, bekommt die Master-Werte.

- **Tools-Block mit Master-Raster:** Die `Skill Section` in `Frame 82 Tools` hat
  Abstände 16 und Karten 385,33 statt 24/380 wie die Kernkompetenzen. Festgelegt
  ist 24/380; Schritt 5 ersetzt sie deshalb gleich mit durch einen Klon des Musters.

Ist das im Master korrigiert, diesen Abschnitt streichen.

## Was nicht passiert

- **Keine Instanz wird detached.** Wer `detachInstance()` ruft, kappt die
  Verbindung zum Design System — genau das, wofür die Datei existiert.
- **Keine Werte von Hand.** Farben, Abstände, Radien, Schatten und Schriften
  kommen aus den Komponenten; überschrieben werden nur Inhalte.
- **Keine neuen Styles, Variablen oder Komponenten.** Der Klon nutzt, was da ist.
- **Die Vorlage `Skillmatrix` (`4158:4223`) wird nicht angefasst.** Nach jedem
  Lauf steht sie unverändert auf 3776,55pt.
- **Keine Vorlageninhalte als Platzhalter stehen lassen.** Was nicht befüllt
  werden kann, wird entfernt oder ausgeblendet — nie mit fremdem Inhalt
  ausgeliefert.
