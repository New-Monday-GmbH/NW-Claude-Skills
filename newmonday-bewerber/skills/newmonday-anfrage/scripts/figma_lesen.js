// Liest einen Teil eines New-Monday-Frames read-only aus – für use_figma.
// Vor dem Senden die drei Konstanten ersetzen. Rückgabe ist ein String in
// reinem ASCII (Figma-MCP bricht sonst ab) und bleibt durch ANZAHL klein.
// Zeilenformat, eine Zeile je Knoten, Einrückung = Tiefe:
//   I <id> <Knotenname> | <Komponente> | prop=wert; …   Instanz mit ihren Properties
//   T <id> <Knotenname> | <Text>                         Text, der nicht schon als Property dasteht
//   B <id> <Knotenname> | <imageHash> <Breite>x<Hoehe>   Bildfüllung
//   F <id> <Knotenname> | <Breite>x<Hoehe> @ <x>,<y>     Frame/Gruppe (Folie, freie Bildgruppe)
const FRAME_ID = "__FRAME_ID__";   // z. B. "2525:1278"
const START = 0;                   // erste Zeile dieses Abschnitts
const ANZAHL = 250;                // Zeilen je Aufruf; bei Abbruch kleiner wählen

const ascii = s => String(s).replace(/[^\x20-\x7e]/g, c => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"));
const kurz = s => ascii(s).replace(/\s+/g, " ").slice(0, 400);
const zeilen = [];

async function lies(n, tiefe, werte) {
  const ein = " ".repeat(tiefe);
  const bild = Array.isArray(n.fills) && n.fills.find(f => f.type === "IMAGE" && f.visible !== false);
  if (bild) zeilen.push(`${ein}B ${n.id} ${kurz(n.name)} | ${bild.imageHash} ${Math.round(n.width)}x${Math.round(n.height)}`);
  if (n.type === "INSTANCE") {
    const haupt = await n.getMainComponentAsync();
    const name = haupt ? (haupt.parent && haupt.parent.type === "COMPONENT_SET" ? haupt.parent.name + "/" + haupt.name : haupt.name) : "?";
    const props = Object.entries(n.componentProperties || {})
      .map(([k, v]) => `${kurz(k.split("#")[0])}=${kurz(v.value)}`).join("; ");
    zeilen.push(`${ein}I ${n.id} ${kurz(n.name)} | ${kurz(name)} | ${props}`);
    werte = new Set(Object.values(n.componentProperties || {}).map(v => String(v.value)));
  } else if (n.type === "TEXT" && !werte.has(n.characters)) {
    // nur Texte, die nicht schon als Property der Instanz darüber stehen (Overrides)
    zeilen.push(`${ein}T ${n.id} ${kurz(n.name)} | ${kurz(n.characters)}`);
  } else if ((n.type === "FRAME" || n.type === "GROUP" || n.type === "SECTION") && tiefe <= 2) {
    zeilen.push(`${ein}F ${n.id} ${kurz(n.name)} | ${Math.round(n.width)}x${Math.round(n.height)} @ ${Math.round(n.x)},${Math.round(n.y)}`);
  }
  if ("children" in n && n.visible !== false) {
    for (const k of n.children) await lies(k, tiefe + 1, werte);
  }
}

const frame = await figma.getNodeByIdAsync(FRAME_ID);
if (!frame) return `FEHLT ${FRAME_ID}`;
let seite = frame;
while (seite && seite.type !== "PAGE") seite = seite.parent;
await figma.setCurrentPageAsync(seite);
await lies(frame, 0, new Set());
const teil = zeilen.slice(START, START + ANZAHL);
return `ZEILEN ${START}-${START + teil.length - 1} von ${zeilen.length}\n` + teil.join("\n");
