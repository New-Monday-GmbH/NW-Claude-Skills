// Skillmatrix aus der Master-Bibliothek - fester Teil des use_figma-Skripts.
// Davor setzt figma_plan.py --skript: SEITE_ID, PLAN, BILDER (b1 … -> imageHash), ENTFERNEN.
// Legt Instanzen an und setzt nur Inhalte: Component-Properties, exponierte
// Instanzen, Bildfuellungen, Bildfeld-Paddings, Sichtbarkeit. Nichts wird
// geloest (detachInstance), keine Farbe, Schrift oder Groesse von Hand -
// ausser dem Rumpf-Rahmen der Variante "Zertifikate am Ende" (PLAN.rumpf).

const seite = await figma.getNodeByIdAsync(SEITE_ID);
if (!seite || seite.type !== "PAGE") throw new Error("Zielseite " + SEITE_ID + " nicht gefunden");
await figma.setCurrentPageAsync(seite);

const haupt = {};
for (const [name, key] of Object.entries(PLAN.keys)) haupt[name] = await figma.importComponentByKeyAsync(key);

const fehler = [], gesetzt = new Set(), bilderGesetzt = [];

// Breitensuche: die flachste Ebene mit diesem Namen. Exponierte Instanzen
// heissen eindeutig ("Kachel 3"), Unterebenen nur innerhalb ihrer Instanz.
function finde(wurzel, name, nurInstanz) {
  const q = [...(wurzel.children || [])];
  while (q.length) {
    const n = q.shift();
    if (n.name === name && (!nurInstanz || n.type === "INSTANCE")) return n;
    if ("children" in n) q.push(...n.children);
  }
  return null;
}

async function schriften(k) {
  const fonts = new Map();
  for (const t of k.findAllWithCriteria({ types: ["TEXT"] }))
    for (const s of t.getStyledTextSegments(["fontName"])) fonts.set(JSON.stringify(s.fontName), s.fontName);
  for (const f of fonts.values()) await figma.loadFontAsync(f);
}

// Je Schritt den Pfad neu aufloesen: setProperties erneuert die Knoten
// darunter, eine gemerkte Referenz waere danach tot.
function aufloesen(wurzel, pfad) {
  let n = wurzel;
  for (const s of pfad) { n = finde(n, s, true); if (!n) return null; }
  return n;
}

async function befuellen(wurzel, pfad, spec) {
  let k = aufloesen(wurzel, pfad);
  if (!k) { fehler.push("nicht gefunden: " + [wurzel.name, ...pfad].join(" / ")); return; }
  if (spec.sichtbar === false) { k.visible = false; return; }
  const props = spec.props || {};
  const varianten = {}, rest = {};
  for (const [n, v] of Object.entries(props)) (n.includes("#") ? rest : varianten)[n] = v;
  if (Object.keys(varianten).length) {             // Variante zuerst: sie tauscht die Ebenen
    k.setProperties(varianten);
    k = aufloesen(wurzel, pfad);
    await schriften(k);
  }
  if (Object.keys(rest).length) {
    k.setProperties(rest);
    k = aufloesen(wurzel, pfad);
  }
  for (const v of Object.values(props)) if (typeof v === "string") gesetzt.add(v);
  for (const name of spec.ausblenden || []) {
    const e = finde(k, name, false);
    if (e) e.visible = false; else fehler.push("Ebene fehlt: " + name + " in " + k.name);
  }
  if (spec.padding) {                              // Bildfeld: Bild im Seitenverhaeltnis der Datei
    const e = finde(k, spec.padding.ebene, false);
    if (e) [e.paddingTop, e.paddingRight, e.paddingBottom, e.paddingLeft] = spec.padding.werte;
    else fehler.push("Bildfeld fehlt: " + spec.padding.ebene + " in " + k.name);
  }
  if (spec.bild) {
    const e = finde(k, spec.bild.ebene, false), b = BILDER[spec.bild.datei];
    if (!e) fehler.push("Bildebene fehlt: " + spec.bild.ebene + " in " + k.name);
    else if (!b) {                                 // nie das Beispielbild der Komponente stehen lassen
      e.visible = false;
      fehler.push("kein Upload fuer Bild " + spec.bild.datei + " - Ebene ausgeblendet");
    } else {
      const bild = { type: "IMAGE", imageHash: b.hash, scaleMode: spec.bild.skalierung };
      const alt = e.fills.findIndex(f => f.type === "IMAGE");
      e.fills = alt >= 0 ? e.fills.map((f, i) => i === alt ? { ...bild, opacity: f.opacity, visible: f.visible } : f)
                         : [...e.fills, bild];
      bilderGesetzt.push(k.name + "/" + e.name);
    }
  }
  for (const kind of spec.kinder || []) await befuellen(wurzel, pfad.concat([kind.name]), kind);
}

async function instanz(spec, eltern) {
  const k = haupt[spec.k].createInstance();
  eltern.appendChild(k);
  k.name = spec.name;
  await schriften(k);
  await befuellen(k, [], spec);
  return k;
}

const hex = h => ({ r: parseInt(h.slice(1, 3), 16) / 255, g: parseInt(h.slice(3, 5), 16) / 255,
                    b: parseInt(h.slice(5, 7), 16) / 255 });
const rechts = (ausser) => {
  const andere = seite.children.filter(c => !ausser.includes(c.id));
  return andere.length ? Math.max(...andere.map(c => c.x + c.width)) + 100 : 0;
};

const ergebnis = { fassung: PLAN.fassung, knoten: [] };
if (PLAN.fassung === "lang") {
  const F = figma.createAutoLayout("VERTICAL", { name: PLAN.name, itemSpacing: 0 });
  F.fills = [];
  seite.appendChild(F);
  F.x = rechts([F.id]); F.y = 0;
  F.resize(PLAN.breite, F.height);
  F.counterAxisSizingMode = "FIXED";
  F.placeholder = true;
  for (const spec of PLAN.instanzen) {
    if (spec.rahmen === "rumpf") {                 // Variante "Zertifikate am Ende"
      const r = PLAN.rumpf, R = figma.createAutoLayout("VERTICAL", { name: "Rumpf", itemSpacing: r.abstand });
      [R.paddingTop, R.paddingRight, R.paddingBottom, R.paddingLeft] = r.padding;
      R.fills = [{ type: "SOLID", color: hex(r.fuellung) }];
      R.strokes = [{ type: "SOLID", color: hex(r.linie.farbe) }];
      R.strokeAlign = "INSIDE";
      [R.strokeTopWeight, R.strokeRightWeight, R.strokeBottomWeight, R.strokeLeftWeight] = [r.linie.breite, 0, 0, 0];
      F.appendChild(R); R.layoutSizingHorizontal = "FILL";
      for (const s of spec.kinder) { const k = await instanz(s, R); k.layoutSizingHorizontal = "FILL"; }
    } else {
      const k = await instanz(spec, F);
      k.layoutSizingHorizontal = "FILL";
    }
  }
  F.placeholder = false;
  ergebnis.knoten.push(F.id);
  ergebnis.hoehe = Math.round(F.height * 10) / 10;
  ergebnis.oben = F.children.map(c => c.type + " " + c.name);
} else {
  // A4: je Seite eine Instanz, rechts neben dem langen Frame, oben buendig.
  const anker = seite.children.filter(c => c.name === PLAN.anker).sort((a, b) => b.x - a.x)[0];
  const B = 595, H = 842, n = PLAN.instanzen.length;
  let x0 = anker ? anker.x + anker.width + 100 : rechts([]), y0 = anker ? anker.y : 0;
  const belegt = seite.children.some(c => c !== anker && c.x < x0 + n * (B + 100) && c.x + c.width > x0
                                          && c.y < y0 + H && c.y + c.height > y0);
  if (belegt) x0 = rechts([]);                     // frueherer Lauf: ganze Reihe dahinter
  for (const [i, spec] of PLAN.instanzen.entries()) {
    const k = await instanz(spec, seite);
    k.x = x0 + i * (B + 100); k.y = y0;
    ergebnis.knoten.push(k.id);
  }
}

// Nichts Fremdes stehen lassen: sichtbare Texte, die noch den Vorgabewert
// ihrer Komponente tragen und nicht gesetzt wurden.
function sichtbar(n, bis) {
  for (let p = n; p && p !== bis.parent; p = p.parent) if (p.visible === false) return false;
  return true;
}
const reste = [];
for (const id of ergebnis.knoten) {
  const wurzel = await figma.getNodeByIdAsync(id);
  const instanzen = [wurzel, ...wurzel.findAllWithCriteria({ types: ["INSTANCE"] })].filter(i => i.type === "INSTANCE");
  for (const inst of instanzen) {
    if (!sichtbar(inst, wurzel)) continue;
    const m = await inst.getMainComponentAsync();
    const eigner = m && m.parent && m.parent.type === "COMPONENT_SET" ? m.parent : m;
    if (!eigner) continue;
    const defs = eigner.componentPropertyDefinitions;
    for (const [name, p] of Object.entries(inst.componentProperties)) {
      if (p.type !== "TEXT" || !defs[name] || p.value !== defs[name].defaultValue || gesetzt.has(p.value)) continue;
      const t = inst.findOne(x => x.type === "TEXT" && x.componentPropertyReferences
                                 && x.componentPropertyReferences.characters === name);
      if (t && sichtbar(t, wurzel)) reste.push(inst.name + ": " + p.value);
    }
  }
}
for (const id of ENTFERNEN) { const n = await figma.getNodeByIdAsync(id); if (n) n.remove(); }
return { ...ergebnis, reste: [...new Set(reste)].slice(0, 30), fehler: fehler.slice(0, 30),
         bilder: bilderGesetzt.length };
