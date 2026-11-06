#!/usr/bin/env python3
"""Figma-Seiten fuer das Entwickler-Layout (layout: entwickler).

    python3 scripts/figma_entwickler.py cv.json "<pdf>" arbeit/ \\
            --stufen arbeit/stufen.json [--seite 12:34] [--unter 12:56]

Schreibt arbeit/figma_entwickler_bau.js (der Bau, ein use_figma-Aufruf) und
arbeit/figma_entwickler_bild.js (setzt hochgeladenes Foto und Logos ein und prueft).
SVG-Logos werden dafuer nach arbeit/figma_bilder/ als PNG gerastert.
Gebaut wird aus Instanzen der Master-Bibliothek, wie die freigegebene Vorlage
(Figma „Portfolio - CV Master“, Seite Archive, Sektion Tech-CV, 03.11.2026):
Kopfzeile, Profilkopf, Abschnittstitel, Listenpunkt, Gruppentitel,
Bildungseintrag, Kurzprofil, Verweis und Fuss. Die Seiten selbst sind Rahmen
mit zwei Spalten - CV/Seite hat nur einen 428pt breiten Slot.

Die Seitenaufteilung wird nicht geschaetzt, sondern aus dem PDF gelesen: jeder
Block der Hauptspalte (Rubrik, Stationskopf, jede einzelne Aufgabe, Eintrag)
traegt eine Textmarke und kommt auf die Seite, auf der sie im PDF steht - so
bricht eine Station in Figma an derselben Aufgabe um wie im PDF. Die
Seitenspalte steht immer auf Seite 1. Masse und Abstaende kommen aus
tokens.json, die Stufe der Seitenspalte aus stufen.json.

--seite   Zielseite in Figma (ohne: neue Seite „CV — Vorname Nachname“)
--unter   ID der ersten Seite der vollstaendigen Fassung - die anonyme Reihe
          kommt darunter
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokens  # noqa: E402
from figma_plan import finde, norm, seitentexte  # noqa: E402
from render_cv import (  # noqa: E402
    BESCHRIFTUNG, VERWEISTEXT, bildung_aufbereiten, entwickler_aufbereiten,
    layout_von, logo_groessen, logo_masse, logoliste, seitenverhaeltnis, zeitraeume_setzen,
)
from logo_lib import suche as logo_datei  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LAUFZEIT = Path(__file__).resolve().parent / "figma_entwickler.js"
T = tokens.laden()
KATALOG = json.loads((ROOT / "assets" / "master-bibliothek.json").read_text(encoding="utf-8"))
SKRIPT_GRENZE = 45000

# Bibliotheksvariablen der Farben (Design System, wie im UX-Weg).
VARIABLEN = {"text": "0a2567e1db12d0c528461890f7c1d8f51e4cfb00",      # base/black
             "grau": "df575b6bf75ad866ab3a5fd2ac275898f277f374",      # neutral/80
             "marke": "e4b628b739230dc39ab1a37ae07a304d6487476d"}     # brand/primary
KOMPONENTEN = ("kopfzeile", "profilkopf", "abschnittstitel", "listenpunkt", "gruppentitel",
               "bildungseintrag", "kurzprofil", "verweis", "fuss")


def stil(name):
    s = tokens.stil(name)
    return {"familie": s["schrift"], "schnitt": s["figma_schnitt"], "groesse": s["groesse"],
            "zeile": s["zeile"], "laufweite": s["laufweite"], "farbe": s["farbe"]}


def farbe01(hexwert):
    h = hexwert.lstrip("#")
    return {k: round(int(h[i:i + 2], 16) / 255, 4) for k, i in (("r", 0), ("g", 2), ("b", 4))}


def marke_von(text, woerter=6):
    """Die ersten Woerter eines Textes - lang genug, um eindeutig zu sein, kurz
    genug, dass ein Zeilenumbruch im PDF-Text nicht dazwischenfaellt."""
    return " ".join(norm(text).split()[:woerter])


def hauptbloecke(daten, ew, labels):
    """Die Bloecke der Hauptspalte in Lesereihenfolge, je mit Abstand und Marke."""
    en, a = T["entwickler"], T["abstand"]
    dn = T["verdichtung"]["deckblatt"]["normal"]
    b = []

    def dazu(art, marke, oben, **rest):
        b.append({"art": art, "marke": marke_von(marke), "oben": oben, **rest})

    erster = [True]

    def rubrik(titel):
        dazu("rubrik", titel, 0 if erster[0] else en["abschnitte"], text=titel)
        erster[0] = False

    def kopf(titel, zeilen, oben, **rest):
        dazu("kopf", titel, oben, titel=titel, zeilen=zeilen, **rest)

    # Firmenlogos klein links im Stationskopf (seit 06.11.2026): Hat eine
    # Station ein Logo, ruecken alle Stationskoepfe gleich ein - wie im PDF.
    groesse = logo_groessen(daten)[0]
    spalte = T["entwickler"]["logo_spalte"]
    mit_logos = any(logoliste(s.get("logo")) for s in daten.get("stationen") or [])

    def logos(s):
        return [{"datei": str(logo_datei(d) or ROOT / "assets" / "logos" / d),
                 "breite": b, "hoehe": h, "verhaeltnis": round(seitenverhaeltnis(d), 4)}
                for d in logoliste(s.get("logo")) for b, h in [logo_masse(d, groesse, spalte)]]

    def aufgaben(liste, art="aufgabe"):
        for n, x in enumerate(liste):
            dazu(art, x["text"], en["kopf_aufgaben"] if n == 0 else en["aufgaben"],
                 text=x["text"], technik=x.get("technik", ""))

    person = daten.get("person") or {}
    if person.get("kurzprofil"):
        rubrik(labels["kurzprofil"])
        dazu("kurzprofil", person["kurzprofil"], dn["rubrik_inhalt"], text=norm(person["kurzprofil"]))
    if daten.get("stationen"):
        rubrik(labels["berufserfahrung"])
        for n, s in enumerate(daten["stationen"]):
            zeilen = []
            if s.get("firma"):
                zeilen.append({"text": norm(s["firma"]), "stil": "firma", "oben": a["titel_firma"]})
            if s.get("zeitraum"):
                zeilen.append({"text": norm(s["zeitraum"]), "stil": "zeitraum", "oben": a["firma_zeitraum"]})
            for feld in ("zusammenfassung", "beschreibung"):
                if s.get(feld):
                    zeilen.append({"text": norm(s[feld]), "stil": "fliesstext", "oben": a["zeitraum_text"]})
            kopf(norm(s["titel"]), zeilen, dn["rubrik_inhalt"] if n == 0 else en["station"],
                 **({"logos": logos(s)} if mit_logos else {}))
            aufgaben(s.get("aufgaben_ew") or [])
            if s.get("technik"):
                dazu("technik", s["technik"], en["aufgaben"], text=s["technik"])
            for p in s.get("projekte") or []:
                z = ([{"text": norm(p["zeitraum"]), "stil": "zeitraum", "oben": a["kunde_zeitraum"]}]
                     if p.get("zeitraum") else [])
                if p.get("beschreibung"):
                    z.append({"text": norm(p["beschreibung"]), "stil": "fliesstext", "oben": a["projekt_text"]})
                kopf(norm(p["kunde"]), z, en["projekt"])
                aufgaben(p.get("aufgaben_ew") or [])
    if ew["eigene_projekte"]:
        rubrik(labels["projekte"])
        for n, p in enumerate(ew["eigene_projekte"]):
            z = [{"text": p["beschreibung"], "stil": "firma", "oben": a["titel_firma"]}] if p["beschreibung"] else []
            if p["zeitraum"]:
                z.append({"text": p["zeitraum"], "stil": "zeitraum", "oben": a["firma_zeitraum"]})
            kopf(p["titel"], z, dn["rubrik_inhalt"] if n == 0 else en["station"])
            aufgaben(p["aufgaben_ew"])
            if p.get("link"):
                dazu("verweis", p["link"]["anzeige"], en["aufgaben"], text=p["link"]["anzeige"],
                     url=p["link"]["url"])
    bildung = bildung_aufbereiten(daten)[0]
    if bildung:
        rubrik(labels["ausbildung"])
        for n, e in enumerate(bildung):
            dazu("bildung", e.get("abschluss"), dn["rubrik_inhalt"] if n == 0 else dn["gruppen"],
                 abschluss=norm(e.get("abschluss")), einrichtung=norm(e.get("institution")),
                 zeitraum=norm(e.get("zeitraum")))
    if ew["sprachen"]:
        rubrik(labels["sprachen"])
        for n, s in enumerate(ew["sprachen"]):
            dazu("eintrag", s, dn["rubrik_inhalt"] if n == 0 else 0, text=s)
    return b


def seitenbloecke(ew, labels, stufe):
    """Die Seitenspalte (nur Seite 1): IT-Kompetenzen, Weiterbildung."""
    w = T["verdichtung"]["entwickler"][stufe]
    b, erster = [], True
    if ew["it_kompetenzen"]:
        b.append({"art": "rubrik", "text": labels["it_kompetenzen"], "oben": 0})
        erster = False
        for n, g in enumerate(ew["it_kompetenzen"]):
            b.append({"art": "gruppe", "titel": g["titel"], "text": ", ".join(g["eintraege"]),
                      "oben": w["rubrik_inhalt"] if n == 0 else w["gruppen"], "liste_oben": w["gruppe_liste"]})
    if ew["weiterbildung"]:
        b.append({"art": "rubrik", "text": labels["weiterbildung"], "oben": 0 if erster else w["abschnitte"]})
        for n, e in enumerate(ew["weiterbildung"]):
            b.append({"art": "bildung", "abschluss": e["titel"], "einrichtung": e["aussteller"],
                      "zeitraum": e["zeit"], "oben": w["rubrik_inhalt"] if n == 0 else w["gruppen"]})
    return b


def seiten_verteilen(bloecke, texte):
    """Jeder Block auf die Seite, auf der seine Marke im PDF steht - nie zurueck."""
    seiten, aktuell, hinweise = [[]], 1, []
    for b in bloecke:
        nr = finde(b.pop("marke"), texte, aktuell)
        if nr is None:
            hinweise.append(f"Im PDF nicht wiedergefunden, bleibt auf Seite {aktuell}: "
                            f"{b.get('text') or b.get('titel') or b.get('abschluss')}")
            nr = aktuell
        while len(seiten) < nr:
            seiten.append([])
        if nr > aktuell:
            b["oben"] = 0                     # erster Block einer Seite: kein Abstand oben
            aktuell = nr
        seiten[nr - 1].append(b)
    return seiten, hinweise


def logos_rastern(plan, ordner):
    """SVG-Logos als PNG fuer die Bildfuellung (wie im UX-Bibliotheksweg)."""
    from figma_bibliothek import png_aus_svg
    hinweise = []
    for s in plan["seiten"]:
        for b in s["haupt"]:
            for l in b.get("logos") or []:
                if not l["datei"].lower().endswith(".svg"):
                    continue
                d = Path(l["datei"])
                png = png_aus_svg(d, Path(ordner).resolve() / "figma_bilder" / (d.stem + ".png"),
                                  l["breite"], l["hoehe"])
                if png is None:
                    hinweise.append(f"{d.name}: SVG ohne PyMuPDF/WeasyPrint nicht in PNG gewandelt.")
                else:
                    l["datei"] = str(png)
    return hinweise


def plan_bauen(daten, pdf, stufen, seite=None, unter=None):
    zeitraeume_setzen(daten)
    if layout_von(daten) != "entwickler":
        raise SystemExit("Die cv.json traegt nicht layout: entwickler - fuer das UX-Layout gilt figma_plan.py.")
    sprache = daten.get("sprache", "de")
    labels = BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"])
    ew, _ = entwickler_aufbereiten(daten)
    texte = seitentexte(pdf)
    haupt, hinweise = seiten_verteilen(hauptbloecke(daten, ew, labels), texte)
    if len(haupt) < len(texte):
        haupt += [[] for _ in range(len(texte) - len(haupt))]
    stufe = (stufen or {}).get("deckblatt", "normal")
    person = daten.get("person") or {}
    anonym = "silhouette" in Path(str(person.get("foto") or "")).name
    verweise = []
    vt = VERWEISTEXT.get(sprache, VERWEISTEXT["de"])
    for l in person.get("links") or []:
        titel = str(l.get("titel") or "").strip()
        verweise.append({"text": l.get("text") or vt.get(titel.lower()) or titel, "url": l.get("url")})
    foto = None if anonym or not person.get("foto") else str(Path(person["foto"]).expanduser().resolve())
    s, r = T["seite"], T["raster"]
    komp = KATALOG["komponenten"]
    return {
        "name": f"Lebenslauf{' (anonym)' if anonym else ''} — {norm(person.get('name'))}",
        "seitenname": f"CV — {norm(person.get('name'))}",
        "seite": seite, "unter": unter, "fassung": "anonym" if anonym else "vollständig",
        "variablen": VARIABLEN, "farben": {k: farbe01(T["farben"][k]) for k in VARIABLEN},
        "komponenten": {n: [komp[n]["key"], komp[n]["typ"] == "COMPONENT_SET"] for n in KOMPONENTEN},
        "stile": {n: stil(n) for n in ("titel", "firma", "zeitraum", "fliesstext", "technik", "it_liste")},
        "seite_w": s["breite"], "seite_h": s["hoehe"], "rand_oben": s["rand_oben"],
        "rand_links": s["rand_links"], "rand_unten": s["rand_unten"],
        "intro_y": s["rand_oben"] + r["kopflogo_hoehe"] + T["abstand"]["kopf_intro"],
        "intro_inhalt": T["abstand"]["intro_inhalt"],
        "haupt": T["abgeleitet"]["entwickler_haupt"], "seite_breite": T["entwickler"]["seite_breite"],
        "spaltenabstand": r["spaltenabstand"], "frameabstand": 100, "reihenabstand": 120,
        "logo_spalte": T["entwickler"]["logo_spalte"], "logo_abstand": T["entwickler"]["logo_abstand"],
        "logo_oben": r["logo_oben"], "logo_stapel": T["entwickler"]["aufgaben"],
        "profil": {"name": norm(person.get("name")), "rolle": norm(person.get("rolle")),
                   "erfahrung": norm(person.get("erfahrung")), "verweise": verweise, "foto": foto},
        "seiten": [{"haupt": h, "seite": seitenbloecke(ew, labels, stufe) if nr == 0 else []}
                   for nr, h in enumerate(haupt)],
    }, hinweise


BILD = r"""
// Setzt das hochgeladene Foto aus dem Traeger in die Ebene „Foto“ des
// Profilkopfs, loescht den Traeger und prueft die gebauten Seiten.
const S = __SEITE__, NAMEN = __NAMEN__, VERBOTEN = __VERBOTEN__;
if (S === "__SEITE__") throw new Error("Seiten-ID fehlt: den Wert `seite` aus dem Bau-Ergebnis statt \"__SEITE__\" eintragen");
let seite = await figma.getNodeByIdAsync(S); await figma.setCurrentPageAsync(seite);
const befunde = [];
for (const t of seite.children.filter(n => /^_Bild (FILL|FIT) → /.test(n.name))) {
  const bild = (t.fills || []).find(f => f.type === "IMAGE");
  const ziel = await figma.getNodeByIdAsync(t.name.split("→ ")[1]);
  if (!bild || !ziel) { befunde.push(`Träger ${t.name} ohne Bild oder Ziel`); continue; }
  const modus = t.name.startsWith("_Bild FIT") ? "FIT" : "FILL";   // FIT: Logos, nie beschnitten
  ziel.fills = [{ type: "IMAGE", imageHash: bild.imageHash, scaleMode: modus }];
  t.remove();
}
const PLATZHALTER = /^(Vorname Nachname|Rolle|Abschnittstitel|Gruppentitel|Aufgabe|Hochschule|Abschluss|Zeitraum|X\+ Jahre Erfahrung)$/;
for (const name of NAMEN) {
  // Gleichnamige Frames eines frueheren Laufs: der zuletzt angelegte gilt.
  const F = seite.children.filter(n => n.name === name).pop();
  if (!F) { befunde.push(`Seite ${name} fehlt`); continue; }
  const sichtbar = n => { for (let p = n; p && p !== F; p = p.parent) if (p.visible === false) return false; return true; };
  for (const t of F.findAll(n => n.type === "TEXT" && sichtbar(n))) {
    if (PLATZHALTER.test(t.characters.trim())) befunde.push(`${name}: Platzhalter „${t.characters}“`);
    for (const v of VERBOTEN) if (v && t.characters.includes(v)) befunde.push(`${name}: Name „${v}“ in „${t.characters.slice(0, 40)}“`);
  }
}
return { befunde };
"""


def main():
    args = sys.argv[1:]

    def option(name):
        if name in args:
            i = args.index(name)
            wert = args[i + 1]
            del args[i:i + 2]
            return wert
        return None

    stufen_datei, seite, unter = option("--stufen"), option("--seite"), option("--unter")
    verboten = option("--verboten")
    if len(args) < 3:
        raise SystemExit(__doc__)
    daten = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    stufen = json.loads(Path(stufen_datei).read_text(encoding="utf-8")) if stufen_datei else None
    plan, hinweise = plan_bauen(daten, Path(args[1]), stufen, seite, unter)
    ordner = Path(args[2])
    ordner.mkdir(parents=True, exist_ok=True)
    hinweise += logos_rastern(plan, ordner)
    bau = "const P = " + json.dumps(plan, ensure_ascii=False) + ";\n" + LAUFZEIT.read_text(encoding="utf-8")
    if len(bau) > SKRIPT_GRENZE:
        hinweise.append(f"figma_entwickler_bau.js hat {len(bau)} Zeichen – über der Grenze von "
                        f"{SKRIPT_GRENZE}; use_figma nimmt es womöglich nicht.")
    (ordner / "figma_entwickler_bau.js").write_text(bau, encoding="utf-8")
    namen = [f"{plan['name']} – Seite {n + 1}" for n in range(len(plan["seiten"]))]
    # Nur die Zuweisung ersetzen - die Pruefzeile vergleicht weiter mit dem
    # Platzhalter (sonst stuende dort ""0:1"" und das Skript liefe nicht).
    bild = (BILD.replace("const S = __SEITE__", "const S = " + json.dumps(seite or "__SEITE__"))
            .replace("__NAMEN__", json.dumps(namen, ensure_ascii=False))
            .replace("__VERBOTEN__", json.dumps([t for t in norm(verboten).split() if len(t) > 2]
                                                if verboten else [], ensure_ascii=False)))
    (ordner / "figma_entwickler_bild.js").write_text(bild, encoding="utf-8")
    print(f"{len(plan['seiten'])} Seiten geplant ({plan['fassung']}), Seitenspalte "
          f"{(stufen or {}).get('deckblatt', 'normal')} -> {ordner / 'figma_entwickler_bau.js'}, "
          f"{ordner / 'figma_entwickler_bild.js'}")
    if not seite:
        hinweise.append("Ohne --seite legt der Bau eine neue Seite an – deren ID (`seite` im Ergebnis) "
                        "in figma_entwickler_bild.js für \"__SEITE__\" einsetzen.")
    for h in hinweise:
        print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
