# Abgleich mit dem Figma-Design-System

Wann: Das Design-System, die Komponenten oder die Seite "CV" im Master wurden
geändert, oder jemand fragt, ob der Skill noch zur Vorlage passt. Ziel ist, dass
`assets/tokens.json` wieder genau das enthält, was Figma zeigt — CSS, Plan und Test
folgen daraus von selbst –, und dass `assets/master-bibliothek.json` die
veröffentlichten Komponenten richtig beschreibt.

**In Figma wird dabei nur gelesen.** Kein Schreibzugriff auf die Vorlage, auch
nicht „nur kurz zum Messen".

**Ohne Figma-Zugriff** (Werkzeug nicht verbunden, keine Rechte) darf ein Wert,
den der Nutzer ausdrücklich nennt, trotzdem in `tokens.json` — er ist eine
Anweisung. `quelle.stand` bleibt dann aber stehen, denn es datiert den letzten
echten Abgleich; in die Übergabe gehört, dass die Figma-Gegenprobe noch aussteht.

## Master und tokens.json gehören zusammen

Seit Oktober 2026 baut der Skill die Figma-Fassung aus den Komponenten des
Masters („Portfolio - CV Master“, Seiten „Components – CV“ und „Components –
Skillmatrix kompakt“), das PDF aber weiter aus `tokens.json`. **Beide werden
gemeinsam gepflegt**: Eine Änderung im Master – Abstand, Schriftgrad, Farbe –
wird veröffentlicht *und* in `tokens.json` nachgezogen; eine Änderung, die in
`tokens.json` beginnt, gehört ebenso in den Master. Sonst stimmt die
Figma-Fassung, und das PDF weicht ab, oder umgekehrt. Die Abstände der
Verdichtung stehen doppelt: als Modi der Collection „CV – Verdichtung“ im
Master und unter `verdichtung` in `tokens.json` – Wert für Wert gleich.
`figma_plan.py` meldet es, wenn Plan und Bibliothek für einen Abstand
verschiedene Zahlen meinen.

**Die Bibliothek neu auslesen**, wenn im Master Komponenten dazukommen, Keys
sich ändern (neu veröffentlicht nach Löschen) oder eine Property umbenannt
wurde: je Komponentenseite ein lesender `use_figma`-Aufruf, der je Komponente
bzw. Komponentenset `key`, `componentPropertyDefinitions` (Namen samt
`#`-Suffix, nie aus einer Variante lesen), exponierte Instanzen und die Namen
der Bildebenen zurückgibt – Rückgabe unter 20 KB halten, also in zwei Hälften
lesen. Das Ergebnis nach `assets/master-bibliothek.json`, `quelle.stand` auf
heute. Property-Namen im Master nach der Veröffentlichung nicht mehr ändern:
Der Bau löst sie zwar über den Namen vor dem `#` auf, aber jede Umbenennung
bricht die Overrides in allen Kandidatendateien. Wie die Komponenten befüllt
werden, zeigen die Testbefüllungen auf der Seite „CV“ (IDs in
`master-bibliothek.json` unter `quelle`).

## Werte abgleichen

Wird ein `normal`-Wert unter `verdichtung` kleiner, müssen `kompakt` und `eng`
mitziehen — der Selbsttest meldet es, wenn eine Notstufe mehr Abstand setzt als
die Stufe davor.

## Ablauf

1. **Skill `figma-use` laden**, dann die Seite auslesen: je Seiten-Frame ein
   `use_figma`-Aufruf mit dem Skript unten, alle vier in derselben Nachricht (sie
   laufen parallel). Datei, Seite und Frame-IDs stehen in `tokens.json` unter
   `quelle`. Wurde die Seite neu aufgebaut, zuerst `get_metadata` auf den
   Seitenknoten — die Frame-IDs können sich geändert haben.
2. **Zuordnen und vergleichen**, Wert für Wert nach der Tabelle unten. Dabei die
   drei Umrechnungen aus `layout.md` („Wo Figma anders rechnet als CSS") anwenden:
   Zeilenhöhen auf ganze Punkt runden, Listen mit 25 % + Listenabstand in den
   13pt-Takt umrechnen, sichtbare Abstände dort messen, wo Figma mit „Space
   Between" verteilt.
3. **Bewusste Abweichungen stehen lassen.** Die Tabelle in `layout.md`
   („Bewusste Abweichungen von der Figma-Vorlage") zählt sie auf — Logofarben,
   Schlagwortzeile, Footer-Inhalt, Logoplatzierung. Die gleicht niemand an, ohne
   dass der Nutzer es ausdrücklich will.
4. **`tokens.json` ändern**, nichts sonst; `quelle.stand` auf das heutige Datum.
   Ändert sich `raster.foto_breite`/`foto_hoehe` oder kommt ein neues
   Platzhalterbild (`assets/silhouette-vorlage.svg`), danach
   `python3 ${CLAUDE_SKILL_DIR}/scripts/silhouette.py` — es setzt die Vorlage in den
   Fotoplatz ein und schreibt `assets/silhouette.svg` und `.png`.
   Neue Schrift oder neuer Schnitt: Datei nach `assets/fonts/` (statischer
   Schnitt, bei variablen Fonts mit `fontTools.varLib.instancer` erzeugen),
   Lizenz daneben, Eintrag unter `schriften` samt `figma`-Schnittname und
   Ober-/Unterlänge (`hhea` der Datei ÷ unitsPerEm). Ändert sich eine Herleitung,
   auch `layout.md` nachziehen.
5. **Selbsttest**: `python3 ${CLAUDE_SKILL_DIR}/scripts/selbsttest.py`. Er prüft das
   PDF gegen die neuen Tokens.
6. **Gegenprobe am Bild**: die Texte des Figma-Musters in eine `cv.json` in einem
   temporären Ordner übernehmen (nicht in den Skill — es sind die Daten eines
   echten Menschen), rendern, die Seiten mit `get_screenshot` der Figma-Frames
   übereinanderlegen und die Schriftlinien vergleichen. Soll-Schriftlinie eines
   Textknotens = Oberkante + `tokens.grundlinie(stil)`. Seite 1 und 2 standen beim
   letzten Abgleich auf 0,00pt genau.

## Auslesen (nur lesend)

```js
const FRAME_ID = "4158:5572";                 // je Aufruf ein Frame aus quelle.frames
const page = await figma.getNodeByIdAsync("4158:3773");
await figma.setCurrentPageAsync(page);
const root = await figma.getNodeByIdAsync(FRAME_ID);
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
const r2 = v => typeof v === 'number' ? Math.round(v * 100) / 100 : v;
const varName = async id => { const v = await figma.variables.getVariableByIdAsync(id); return v ? v.name : id; };
async function farben(ps) {
  if (!Array.isArray(ps) || !ps.length) return null;
  const out = [];
  for (const p of ps) {
    let s = p.type === 'SOLID' ? hex(p.color) + (p.opacity < 1 ? '@' + r2(p.opacity) : '') : p.type;
    if (p.type === 'SOLID' && p.boundVariables && p.boundVariables.color) s += '{' + await varName(p.boundVariables.color.id) + '}';
    if (p.type === 'IMAGE' && p.filters && Object.values(p.filters).some(Boolean)) s += JSON.stringify(p.filters);
    out.push((p.visible === false ? '(aus)' : '') + s);
  }
  return out.join(',');
}
const zeilen = [];
async function lauf(n, tiefe) {
  const t = [`${'  '.repeat(tiefe)}${n.type} "${n.name}" #${n.id} ${r2(n.x)},${r2(n.y)} ${r2(n.width)}x${r2(n.height)}`];
  if (n.visible === false) t.push('VERSTECKT');
  if (n.layoutMode && n.layoutMode !== 'NONE')
    t.push(`AL=${n.layoutMode} gap=${n.itemSpacing} pad=${n.paddingTop},${n.paddingRight},${n.paddingBottom},${n.paddingLeft} haupt=${n.primaryAxisAlignItems}`);
  if ('cornerRadius' in n && n.cornerRadius) t.push('rundung=' + String(n.cornerRadius));
  if (n.type !== 'TEXT' && 'fills' in n) { const f = await farben(n.fills); if (f) t.push('fill=' + f); }
  if ('strokes' in n && n.strokes.length) t.push(`stroke=${await farben(n.strokes)} ${n.strokeAlign}`);
  if ('effects' in n && n.effects.length) t.push('effekte=' + JSON.stringify(n.effects));
  if (n.type === 'TEXT') {
    for (const s of n.getStyledTextSegments(['fontName', 'fontSize', 'lineHeight', 'letterSpacing', 'fills', 'textCase', 'listOptions', 'listSpacing', 'textStyleId'])) {
      const lh = s.lineHeight.unit === 'AUTO' ? 'auto' : r2(s.lineHeight.value) + (s.lineHeight.unit === 'PERCENT' ? '%' : 'pt');
      const ls = r2(s.letterSpacing.value) + (s.letterSpacing.unit === 'PERCENT' ? '%' : 'pt');
      t.push(`\n${'  '.repeat(tiefe + 1)}» "${s.characters.slice(0, 40)}" ${s.fontName.family} ${s.fontName.style} ${s.fontSize} zeile=${lh} laufweite=${ls} farbe=${await farben(s.fills)}`
        + (s.textCase !== 'ORIGINAL' ? ' ' + s.textCase : '')
        + (s.listOptions.type !== 'NONE' ? ` liste listSpacing=${s.listSpacing}` : ''));
    }
  }
  zeilen.push(t.join(' '));
  if ('children' in n && n.type !== 'INSTANCE' && !/logo/i.test(n.name))
    for (const c of n.children) await lauf(c, tiefe + 1);
}
await lauf(root, 0);
return zeilen.join('\n');
```

Schatten stehen unter `effekte`, Rundungen unter `rundung` — beim letzten Abgleich
gab es keine.

## Wo steht welcher Token in Figma

Knotennamen vom Stand 2026-09-28. Die Frames heißen „Erste Seite" bis „Vierte
Seite".

| Token | Figma |
|---|---|
| `seite.*` | Seiten-Frame: Größe, Padding |
| `farben.text`, `.grau`, `.marke` | Variablen `base/black`, `neutral/80`, `brand/primary` |
| `text.name` | Erste Seite › Person › Name + Experience › Name (Text-Style `Headings/H6`) |
| `text.rolle` | Title + Experience, beide Zeilen |
| `abstand.name_rolle`, `.rolle_erfahrung` | itemSpacing von Name + Experience bzw. Title + Experience |
| `abstand.erfahrung_verweise` | itemSpacing von Person |
| `text.verweis`, `raster.verweislinie` | Links › Frame 91/92: Text; Unterkante (Stroke) in `brand/primary` |
| `abstand.verweise` | sichtbar: x des zweiten Verweises − Breite des ersten (Frame 90 verteilt mit Space Between) |
| `abstand.kopf_intro`, `.intro_inhalt` | itemSpacing von Body bzw. Content |
| `raster.fotospalte`, `.fotoabstand`, `.foto_*` | Introduction (itemSpacing), Col (Breite, paddingTop), Photo |
| `raster.kopflogo_*`, `.fusslogo_*` | Instanz `nm-logo-2025` im Header bzw. Footer |
| `text.rubrik` | „Bildung", „Skillset", „Kurzprofil" |
| `verdichtung.deckblatt.normal.rubrik_inhalt` | itemSpacing von Education bzw. Skillset |
| `….vor_linie`, `….nach_linie` | itemSpacing von Experience (um die Trennlinie) |
| `text.abschluss`, `text.bildung` | Education-Text: erste Zeile bzw. übrige |
| `raster.spaltenabstand` | itemSpacing von Skillset-Grid |
| `text.gruppe` | Gruppentitel („p") |
| `text.liste`, `….gruppe_liste`, `….gruppen` | „sub-p" (25 % + listSpacing), itemSpacing der Gruppe und von Left/Right — **umgerechnet**, siehe layout.md |
| `verdichtung.stationen.normal.profil_rubrik` | itemSpacing von Short profile |
| `….profil_linie`, `….profil_stationen` | itemSpacing der Zweiten Seite |
| `….station` | itemSpacing der Stationsliste (Frame 82/83) |
| `….kopf_aufgaben` | itemSpacing einer Station (Frame 79/80) |
| `raster.logospalte`, `.logoabstand`, `.logo_oben` | Row is-segment: Breite des Logo-Rahmens, itemSpacing; paddingTop des Logo-Rahmens |
| `text.titel`, `.firma`, `.zeitraum` | Job Title + Date (Titel, Firma), Job Description (Zeitraum) |
| `abstand.titel_firma`, `.firma_zeitraum` | itemSpacing von Job Title + Date bzw. Job Description |
| `text.aufgabe`, `raster.listeneinzug` | Aufgabenliste in Col (paddingLeft = Einzug der Station) |
| `raster.fuss_*`, `abstand.fuss_*`, `text.fuss_*` | Footer, Frame 72 (Reihe), Frame 78 (Spalten), Frame 66–69 (Label, Werte) |

Nicht in der Vorlage und deshalb frei gewählt: Projekte unter einer Station, der
Zeilenabstand umbrechender Verweise, der Reihenabstand bei mehr als zwei
Bildungseinträgen, die Zertifikats-Tags (`text.zert_tag`, `raster.zert_tag_*`,
`farben.rahmen`, `verdichtung.deckblatt.*.zert_abstand`, Vorgabe vom
03.10.2026, abgeleitet aus den Tags der Skill Matrix, Herleitung in
`layout.md`) und alle Stufen außer `normal` unter `verdichtung`. Die
Studieninhalte unter den Abschlüssen („sub-p“ in Education) übernimmt der Skill
seit dem 03.10.2026 nicht mehr – ein Abgleich zieht sie nicht nach.
