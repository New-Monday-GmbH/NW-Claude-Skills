// Laufzeit fuer den Bibliotheksweg. figma_plan.py setzt davor eine Zeile
//   const BAU = {...};
// und schickt das Ganze als use_figma-Skript. Hier steht keine Zahl und kein
// Text des Lebenslaufs - nur, wie aus BAU Instanzen der Master-Bibliothek
// werden. Drei Modi: "vorflug" (erreichbar? Schriften?), "bauen", "pruefen".
// Instanzen werden nie geloest (kein detachInstance), nichts Lokales angelegt
// ausser den Seiteninstanzen selbst. Siehe references/figma.md.

const K = BAU.komponenten;              // Schluessel -> {key, typ}
const geladen = {};                     // Schluessel -> COMPONENT oder COMPONENT_SET
const warnungen = [];

async function importiere(schluessel) {
  if (geladen[schluessel]) return geladen[schluessel];
  const k = K[schluessel];
  if (!k) throw new Error(`Komponente ${schluessel} nicht in BAU.komponenten`);
  geladen[schluessel] = k.typ === "COMPONENT_SET"
    ? await figma.importComponentSetByKeyAsync(k.key)
    : await figma.importComponentByKeyAsync(k.key);
  return geladen[schluessel];
}

function variante(set, wert) {
  if (set.type !== "COMPONENT_SET") return set;
  const v = set.children.find(c => Object.values(c.variantProperties || {}).includes(wert));
  if (!v) throw new Error(`${set.name}: Variante ${wert} fehlt`);
  return v;
}

async function schriftenLaden() {
  const gesehen = new Set();
  for (const k of Object.values(geladen)) {
    for (const t of k.findAllWithCriteria({ types: ["TEXT"] })) {
      if (!t.characters.length) continue;
      for (const f of t.getRangeAllFontNames(0, t.characters.length)) {
        const id = f.family + "|" + f.style;
        if (gesehen.has(id)) continue;
        gesehen.add(id);
        await figma.loadFontAsync(f);
      }
    }
  }
  return [...gesehen];
}

// Properties ueber den Namen vor dem # setzen. Der volle Name (mit Suffix)
// steht in master-bibliothek.json; aufgeloest wird an der Instanz selbst,
// damit ein neu vergebener Suffix nach einem Bibliotheks-Update nicht bricht.
function setze(inst, props) {
  if (!props) return;
  const vorhanden = Object.keys(inst.componentProperties);
  const neu = {};
  for (const [name, wert] of Object.entries(props)) {
    const voll = vorhanden.find(v => v === name) || vorhanden.find(v => v.split("#")[0] === name.split("#")[0]);
    if (!voll) { warnungen.push(`${inst.name}: Property „${name}“ fehlt`); continue; }
    // Was schon so in der Komponente steht, wird nicht gesetzt: kein Override,
    // und eine spaetere Aenderung des Standards im Master kommt hier an.
    if (inst.componentProperties[voll].value === wert) continue;
    neu[voll] = wert;
  }
  if (Object.keys(neu).length) inst.setProperties(neu);
}

function kind(wurzel, name, typ) {
  return wurzel.findOne(n => n.name === name && (!typ || n.type === typ));
}

// Bilder: upload_assets nimmt als Ziel nur Knoten mit einfacher ID, keine
// Ebenen in Instanzen (I12:3;45:6). Deshalb bekommt jedes Bild einen
// Traeger - ein Rechteck auf der Seite, Name "_Bild FIT → <Ziel-ID>". Der Upload
// fuellt den Traeger; der Pruefaufruf setzt die Fuellung in die Ebene der
// Instanz und loescht den Traeger.
const bilder = [];
const traeger = [];
const TRAEGER = /^_Bild (FIT|FILL) → (.+)$/;
function befuellen(inst, e, pfad) {
  setze(inst, e.p);
  for (const [name, sub] of Object.entries(e.kinder || {})) {
    const k = kind(inst, name, "INSTANCE");
    if (!k) { warnungen.push(`${pfad}: exponierte Instanz „${name}“ fehlt`); continue; }
    befuellen(k, sub, pfad + " › " + name);
  }
  if (e.link) {
    const t = kind(inst, e.link.ebene, "TEXT");
    if (t) t.hyperlink = { type: "URL", value: e.link.url };
    else warnungen.push(`${pfad}: Textebene ${e.link.ebene} fuer den Link fehlt`);
  }
  for (const b of e.bilder || []) {
    const n = kind(inst, b.ebene);
    if (!n) { warnungen.push(`${pfad}: Bildebene ${b.ebene} fehlt`); continue; }
    // Logos: Groesse ueber den Innenabstand, wie im Master angelegt
    // (_Größe über Innenabstand) - die Masse kommen aus dem Plan, also aus
    // dem Seitenverhaeltnis der Datei. Nie resize() an der Ebene.
    if (b.breite && "paddingLeft" in n) { n.paddingLeft = b.breite; n.paddingTop = b.hoehe; }
    const r = figma.createRectangle();
    r.name = `_Bild ${b.scaleMode} → ${n.id}`;
    r.resize(Math.max(1, b.breite || n.width), Math.max(1, b.hoehe || n.height));
    r.fills = [];
    traeger.push(r);
    bilder.push({ nodeId: r.id, ziel: n.id, datei: b.datei, scaleMode: b.scaleMode, art: b.art,
                  ebene: pfad + " › " + b.ebene });
  }
}

async function instanz(e) {
  const komp = await importiere(e.k);
  const inst = variante(komp, e.variante).createInstance();
  if (e.name) inst.name = e.name;
  return inst;
}

async function verdichtung() {
  // Die Collection haengt an der Hoehe von CV/Abstand{station}; ueber diese
  // Bindung wird sie in der Zieldatei gefunden, ohne Variablen-Keys.
  const anker = variante(await importiere("abstand"), "station");
  const b = anker.boundVariables && anker.boundVariables.height;
  if (b) {
    const v = await figma.variables.getVariableByIdAsync(b.id);
    if (v) return await figma.variables.getVariableCollectionByIdAsync(v.variableCollectionId);
  }
  warnungen.push("Collection CV – Verdichtung nicht gefunden - Seiten bleiben im Modus normal");
  return null;
}

async function zielseite() {
  if (BAU.seite) {
    const s = await figma.getNodeByIdAsync(BAU.seite);
    if (!s || s.type !== "PAGE") throw new Error(`Seite ${BAU.seite} nicht gefunden`);
    await figma.setCurrentPageAsync(s);
    return s;
  }
  const s = figma.createPage();
  s.name = BAU.seitenname;
  await figma.setCurrentPageAsync(s);
  return s;
}

if (BAU.modus === "vorflug") {
  const ergebnis = { erreichbar: false, editor: figma.editorType,
                     seiten: figma.root.children.map(p => ({ id: p.id, name: p.name })) };
  try {
    const s = await importiere("seite");
    ergebnis.erreichbar = true;
    ergebnis.komponente = { name: s.name, remote: s.remote, key: s.key };
  } catch (fehler) {
    ergebnis.fehler = String(fehler && fehler.message || fehler);
  }
  if (BAU.seite) {
    const s = await figma.getNodeByIdAsync(BAU.seite);
    ergebnis.zielseite = s && s.type === "PAGE" ? { id: s.id, name: s.name } : "nicht gefunden";
    if (s && s.type === "PAGE") {
      await figma.setCurrentPageAsync(s);
      ergebnis.zielseite.knoten = s.children.length;
    }
  }
  const da = await figma.listAvailableFontsAsync();
  ergebnis.fehlen = [];
  for (const [familie, schnitte] of Object.entries(BAU.schrift))
    for (const s of schnitte)
      if (!da.some(f => f.fontName.family === familie && f.fontName.style === s))
        ergebnis.fehlen.push(`${familie} ${s}`);
  return ergebnis;
}

if (BAU.modus === "bauen") {
  const seite = await zielseite();
  // Erst alles importieren, dann Schriften laden, dann bauen.
  for (const s of BAU.gebraucht) await importiere(s);
  await schriftenLaden();
  const coll = await verdichtung();

  let x0, y0;
  const schonDa = seite.children.slice();
  if (BAU.neben) {
    // Zweites und folgende Teilskripte: rechts neben den zuletzt gebauten Frame.
    const u = seite.children.filter(n => n.name === BAU.neben).pop();
    if (!u) throw new Error(`Frame ${BAU.neben} nicht gefunden - Teilskripte der Reihe nach senden`);
    x0 = u.x + u.width + BAU.frameabstand; y0 = u.y;
  } else if (BAU.unter) {
    const u = await figma.getNodeByIdAsync(BAU.unter);
    if (!u) throw new Error(`Knoten ${BAU.unter} (vollstaendige Reihe) nicht gefunden`);
    x0 = u.x; y0 = u.y + u.height + BAU.reihenabstand;
  } else {
    x0 = schonDa.length ? Math.max(...schonDa.map(n => n.x + n.width)) + BAU.frameabstand : 0;
    y0 = schonDa.length ? Math.min(...schonDa.map(n => n.y)) : 0;
  }

  const frames = [];
  let zahl = 0;
  for (const [i, f] of BAU.frames.entries()) {
    const s = (await importiere("seite")).createInstance();
    seite.appendChild(s);
    s.name = f.name;
    s.x = x0 + i * (s.width + BAU.frameabstand); s.y = y0;
    if (coll) {
      const m = coll.modes.find(m => m.name === f.stufe);
      if (m) s.setExplicitVariableModeForCollection(coll, m.modeId);
      else warnungen.push(`${f.name}: Modus ${f.stufe} fehlt in ${coll.name}`);
    }
    setze(s, { "Kopfzeile anzeigen": f.kopfzeile, "Fuß anzeigen": f.fuss });
    if (f.fuss && BAU.fuss) befuellen(s, { kinder: { "Fuß": { kinder: BAU.fuss } } }, f.name);
    const slot = s.findOne(n => n.type === "SLOT" && n.name === "Inhalt");
    if (!slot) throw new Error(`${f.name}: Slot Inhalt fehlt in CV/Seite`);
    for (const e of f.inhalt) {
      const inst = await instanz(e);
      slot.appendChild(inst);
      befuellen(inst, e, f.name + " › " + inst.name);
      zahl++;
    }
    frames.push({ id: s.id, name: s.name, hoehe_inhalt: Math.round(slot.children.reduce((a, c) => a + c.height, 0) * 10) / 10,
                  platz: Math.round(slot.height * 10) / 10 });
  }
  // Traeger unter die Reihe, nebeneinander - bis der Pruefaufruf sie abraeumt.
  let tx = x0;
  for (const r of traeger) {
    seite.appendChild(r);
    r.x = tx; r.y = y0 + 842 + 40;
    tx += r.width + 20;
  }
  for (const f of frames)
    if (f.hoehe_inhalt > f.platz + 0.5)
      warnungen.push(`${f.name}: Inhalt ${f.hoehe_inhalt} hoch, Platz ${f.platz} - laeuft ueber`);
  return { seite: seite.id, frames, instanzen: zahl,
           bilder_fill: bilder.filter(b => b.scaleMode === "FILL"),
           bilder_fit: bilder.filter(b => b.scaleMode === "FIT"),
           warnungen };
}

if (BAU.modus === "pruefen") {
  // Je Frame: Seiteninstanz der Bibliothek, im Slot genau die geplanten
  // Instanzen in Reihenfolge, nichts geloest, alles remote; Logos im
  // Seitenverhaeltnis ihrer Datei mit FIT und hochgeladen; Foto hochgeladen;
  // in der anonymen Fassung kein Name.
  const seite = BAU.seite ? await figma.getNodeByIdAsync(BAU.seite) : null;
  if (seite) await figma.setCurrentPageAsync(seite);
  const befunde = [];
  let instanzen = 0, logos = 0, eingesetzt = 0;
  // Erst die hochgeladenen Bilder aus den Traegern in die Instanzen setzen.
  for (const r of figma.currentPage.children.filter(n => TRAEGER.test(n.name))) {
    const [, modus, ziel] = r.name.match(TRAEGER);
    const bild = (r.fills || []).find(p => p.type === "IMAGE");
    const z = await figma.getNodeByIdAsync(ziel);
    if (!z) { befunde.push(`${r.name}: Ziel fehlt - Traeger bleibt stehen`); continue; }
    if (!bild) { befunde.push(`${r.name}: noch kein Bild hochgeladen - Traeger bleibt stehen`); continue; }
    z.fills = [{ type: "IMAGE", imageHash: bild.imageHash, scaleMode: modus }];
    r.remove();
    eingesetzt++;
  }
  const ids = BAU.frame_ids || [];
  for (const [i, f] of BAU.frames.entries()) {
    let s = ids[i] ? await figma.getNodeByIdAsync(ids[i]) : null;
    if (!s) s = figma.currentPage.children.filter(n => n.name === f.name).pop();
    if (!s) { befunde.push(`${f.name}: nicht gefunden`); continue; }
    if (s.type !== "INSTANCE") { befunde.push(`${f.name}: ist ${s.type}, keine Instanz - geloest?`); continue; }
    const ms = await s.getMainComponentAsync();
    if (!ms || ms.key !== K.seite.key) befunde.push(`${f.name}: Seite ist keine Instanz von CV/Seite`);
    else if (!ms.remote) befunde.push(`${f.name}: CV/Seite ist lokal, nicht aus der Bibliothek`);
    for (const n of s.findAllWithCriteria({ types: ["INSTANCE"] })) {
      instanzen++;
      const m = await n.getMainComponentAsync();
      if (!m) befunde.push(`${f.name} › ${n.name}: Hauptkomponente fehlt`);
      else if (!m.remote) befunde.push(`${f.name} › ${n.name}: ${m.name} ist lokal`);
    }
    const slot = s.findOne(n => n.type === "SLOT" && n.name === "Inhalt");
    const kinder = slot ? slot.children : [];
    if (kinder.length !== f.inhalt.length)
      befunde.push(`${f.name}: ${kinder.length} Elemente im Slot statt ${f.inhalt.length}`);
    for (const [j, e] of f.inhalt.entries()) {
      const n = kinder[j];
      if (!n) break;
      if (n.type !== "INSTANCE") { befunde.push(`${f.name} › ${n.name}: ${n.type} im Slot - geloest?`); continue; }
      const m = await n.getMainComponentAsync();
      const owner = m && m.parent && m.parent.type === "COMPONENT_SET" ? m.parent : m;
      if (!owner || owner.key !== K[e.k].key) befunde.push(`${f.name} › ${n.name}: nicht ${K[e.k].name}`);
      for (const b of e.bilder || []) {
        const z = kind(n, b.ebene);
        const zm = m && kind(m, b.ebene);
        if (!z) { befunde.push(`${f.name} › ${n.name} › ${b.ebene}: fehlt`); continue; }
        const fill = (z.fills || []).find(p => p.type === "IMAGE");
        const vorgabe = zm && (zm.fills || []).find(p => p.type === "IMAGE");
        if (!fill) { befunde.push(`${f.name} › ${n.name} › ${b.ebene}: kein Bild`); continue; }
        if (vorgabe && fill.imageHash === vorgabe.imageHash) befunde.push(`${f.name} › ${n.name} › ${b.ebene}: Bild nicht hochgeladen (${b.datei.split("/").pop()})`);
        if (b.art === "logo") {
          logos++;
          if (fill.scaleMode !== "FIT") befunde.push(`${f.name} › ${n.name} › ${b.ebene}: scaleMode ${fill.scaleMode} statt FIT`);
          const ist = z.width / z.height;
          if (Math.abs(ist / b.verhaeltnis - 1) > BAU.logo_toleranz)
            befunde.push(`${f.name} › ${n.name} › ${b.ebene}: verzerrt ${ist.toFixed(3)}:1 statt ${b.verhaeltnis.toFixed(3)}:1`);
        }
      }
    }
    if (BAU.verboten && BAU.verboten.length) {
      const muster = new RegExp(BAU.verboten.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"));
      for (const t of s.findAllWithCriteria({ types: ["TEXT"] }))
        if (t.visible && muster.test(t.characters)) befunde.push(`${f.name}: Name steht noch in „${t.characters.slice(0, 60)}“`);
    }
  }
  return { geprueft: BAU.frames.length, eingesetzt, instanzen, logos, befunde };
}
