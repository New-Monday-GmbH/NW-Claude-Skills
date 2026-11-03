// Laufzeit fuer das Entwickler-Layout in Figma - figma_entwickler.py setzt den
// Plan als `const P = …` davor. Gebaut wird aus Instanzen der Master-Bibliothek
// „Portfolio - CV Master“ (Kopfzeile, Profilkopf, Abschnittstitel, Listenpunkt,
// Gruppentitel, Bildungseintrag, Kurzprofil, Fuss); Seiten und Spalten sind
// Rahmen mit Auto-Layout, weil CV/Seite nur einen 428pt breiten Slot hat.
// Alle Masse stehen im Plan (aus tokens.json), hier wird nichts gerechnet.

let seite = null;
if (P.seite) { let n = await figma.getNodeByIdAsync(P.seite); while (n && n.type !== "PAGE") n = n.parent; seite = n; }
if (!seite) { seite = figma.createPage(); seite.name = P.seitenname; }
await figma.setCurrentPageAsync(seite);

for (const [f, s] of [["Inter", "Regular"], ["Inter", "Bold"], ["Rethink Sans", "SemiBold"]])
  await figma.loadFontAsync({ family: f, style: s });
const V = {};
for (const [n, k] of Object.entries(P.variablen)) V[n] = await figma.variables.importVariableByKeyAsync(k);
const K = {};
for (const [n, [k, set]] of Object.entries(P.komponenten))
  K[n] = set ? await figma.importComponentSetByKeyAsync(k) : await figma.importComponentByKeyAsync(k);
const variante = (set, name) => set.children.find(c => c.name === name) || set.defaultVariant;

const farbe = (name) => figma.variables.setBoundVariableForPaint(
  { type: "SOLID", color: P.farben[name] }, "color", V[name]);
const warnungen = [];
function eig(i, n) { return Object.keys(i.componentProperties).find(k => k.split("#")[0] === n); }
function setz(i, o) {
  const p = {};
  for (const [n, v] of Object.entries(o)) { const k = eig(i, n); if (k) p[k] = v; else warnungen.push(`Property ${n} fehlt an ${i.name}`); }
  if (Object.keys(p).length) i.setProperties(p);
}
function text(s, st, breite) {
  const t = figma.createText();
  t.fontName = { family: st.familie, style: st.schnitt }; t.fontSize = st.groesse;
  t.lineHeight = { unit: "PIXELS", value: st.zeile }; t.letterSpacing = { unit: "PIXELS", value: st.laufweite };
  t.characters = s; t.fills = [farbe(st.farbe)];
  if (breite) { t.resize(breite, t.height); t.textAutoResize = "HEIGHT"; }
  return t;
}
function spalte(name, breite, gap = 0) {
  const f = figma.createAutoLayout("VERTICAL", { name, itemSpacing: gap }); f.fills = [];
  f.resize(breite, 10); f.counterAxisSizingMode = "FIXED"; f.primaryAxisSizingMode = "AUTO";
  return f;
}
function abstand(p, h) { if (!h) return; const f = figma.createFrame(); f.name = "Abstand " + h; f.resize(1, h); f.fills = []; p.appendChild(f); }
function voll(p, n) { p.appendChild(n); n.layoutSizingHorizontal = "FILL"; return n; }

function punkt(p, a, art) {
  const i = variante(K.listenpunkt, "Art=" + art).createInstance(); voll(p, i);
  const ganz = a.technik ? a.text + " " + a.technik : a.text;
  setz(i, { "Text": ganz });
  if (a.technik) {
    const t = i.findOne(n => n.type === "TEXT" && n.name === "Text");
    t.setRangeFills(ganz.length - a.technik.length, ganz.length, [farbe("marke")]);
  }
}
function rubrik(p, titel) { const i = K.abschnittstitel.createInstance(); setz(i, { "Titel": titel, "Icon anzeigen": false }); p.appendChild(i); }
function kopf(p, b) {
  const k = voll(p, spalte("Kopf – " + b.titel, P.haupt));
  voll(k, text(b.titel, P.stile.titel, P.haupt));
  for (const z of b.zeilen) { abstand(k, z.oben); voll(k, text(z.text, P.stile[z.stil], P.haupt)); }
}
function bildung(p, b) {
  const i = K.bildungseintrag.createInstance(); voll(p, i);
  const q = { "Abschluss": b.abschluss };
  Object.assign(q, b.einrichtung ? { "Einrichtung": b.einrichtung } : { "Einrichtung anzeigen": false });
  Object.assign(q, b.zeitraum ? { "Zeitraum": b.zeitraum } : { "Zeitraum anzeigen": false });
  setz(i, q);
}
function block(p, b) {
  abstand(p, b.oben);
  if (b.art === "rubrik") rubrik(p, b.text);
  else if (b.art === "kurzprofil") { const i = K.kurzprofil.createInstance(); voll(p, i); setz(i, { "Text": b.text }); }
  else if (b.art === "kopf") kopf(p, b);
  else if (b.art === "aufgabe") punkt(p, b, "Aufgabe");
  else if (b.art === "eintrag") punkt(p, { text: b.text, technik: "" }, "Eintrag");
  else if (b.art === "technik") voll(p, text(b.text, P.stile.technik, P.haupt));
  else if (b.art === "verweis") {
    const i = K.verweis.createInstance(); p.appendChild(i); setz(i, { "Label": b.text });
    const t = i.findOne(n => n.type === "TEXT" && n.name === "Label");
    if (t && b.url) t.setRangeHyperlink(0, t.characters.length, { type: "URL", value: b.url });
  }
  else if (b.art === "bildung") bildung(p, b);
  else if (b.art === "gruppe") {
    const g = K.gruppentitel.createInstance(); voll(p, g); setz(g, { "Titel": b.titel });
    abstand(p, b.liste_oben); voll(p, text(b.text, P.stile.it_liste, P.seite_breite));
  }
}

// Lage: rechts neben allem, was auf der Seite steht - oder unter einer Reihe.
let x0 = 0, y0 = 0;
if (P.unter) {
  const u = await figma.getNodeByIdAsync(P.unter);
  if (u) { x0 = u.x; y0 = u.y + u.height + P.reihenabstand; }
} else if (seite.children.length) {
  x0 = Math.max(...seite.children.map(n => n.x + n.width)) + 200;
}

const frames = [], bilder_fill = [];
P.seiten.forEach((s, nr) => {
  const F = figma.createFrame(); F.name = `${P.name} – Seite ${nr + 1}`; F.resize(P.seite_w, P.seite_h);
  F.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
  seite.appendChild(F); F.x = x0 + nr * (P.seite_w + P.frameabstand); F.y = y0;
  let oben = P.rand_oben;
  if (nr === 0) {
    const k = K.kopfzeile.createInstance(); F.appendChild(k); k.x = P.rand_links; k.y = P.rand_oben;
    const pk = variante(K.profilkopf, "Fassung=" + P.fassung).createInstance(); F.appendChild(pk);
    pk.x = P.rand_links; pk.y = P.intro_y;
    const q = { "Name": P.profil.name };
    Object.assign(q, P.profil.rolle ? { "Rolle": P.profil.rolle } : { "Rolle anzeigen": false });
    Object.assign(q, P.profil.erfahrung ? { "Erfahrung": P.profil.erfahrung } : { "Erfahrung anzeigen": false });
    if (P.fassung !== "anonym") {
      const v = P.profil.verweise;
      q["Verweise anzeigen"] = v.length > 0;
      for (let n = 2; n <= 4; n++) q[`Verweis ${n}`] = v.length >= n;
      q["Foto anzeigen"] = !!P.profil.foto;
      setz(pk, q);
      v.slice(0, 4).forEach((w, i) => {
        const e = pk.exposedInstances.find(x => x.name === `Verweis ${i + 1}`);
        if (!e) return;
        setz(e, { "Label": w.text, "Linie anzeigen": !!w.url });
        const t = e.findOne(n => n.type === "TEXT" && n.name === "Label");
        if (t && w.url) t.setRangeHyperlink(0, t.characters.length, { type: "URL", value: w.url });
      });
      if (P.profil.foto) {
        const ziel = pk.findOne(n => n.name === "Foto" && "fills" in n);
        const r = figma.createRectangle(); r.name = `_Bild FILL → ${ziel.id}`; r.resize(40, 40);
        seite.appendChild(r); r.x = F.x; r.y = F.y + P.seite_h + 40;
        bilder_fill.push({ nodeId: r.id, datei: P.profil.foto, ziel: ziel.id });
      }
    } else setz(pk, q);
    oben = P.intro_y + pk.height + P.intro_inhalt;
  }
  const sp = figma.createAutoLayout("HORIZONTAL", { name: "Spalten", itemSpacing: P.spaltenabstand });
  sp.fills = []; F.appendChild(sp); sp.x = P.rand_links; sp.y = oben;
  const haupt = spalte("Hauptspalte (2/3)", P.haupt); sp.appendChild(haupt);
  const seitensp = spalte("Seitenspalte (1/3)", P.seite_breite); sp.appendChild(seitensp);
  for (const b of s.haupt) block(haupt, b);
  for (const b of s.seite) block(seitensp, b);
  let grenze = P.seite_h - P.rand_unten;
  if (nr === P.seiten.length - 1) {
    const fu = K.fuss.createInstance(); F.appendChild(fu); fu.x = P.rand_links; fu.y = P.seite_h - P.rand_unten - fu.height;
    grenze = fu.y;
  }
  for (const c of [haupt, seitensp])
    if (oben + c.height > grenze + 0.5)
      warnungen.push(`${F.name}: ${c.name} endet bei ${Math.round(oben + c.height)}pt, Platz bis ${Math.round(grenze)}pt`);
  frames.push({ id: F.id, name: F.name });
});
return { seite: seite.id, frames, bilder_fill, bilder_fit: [], warnungen };
