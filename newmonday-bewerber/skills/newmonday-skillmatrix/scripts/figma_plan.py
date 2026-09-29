#!/usr/bin/env python3
"""Baut aus skillmatrix.json den Bauplan fuer den Figma-Frame (Weg B).

    python3 scripts/figma_plan.py skillmatrix.json arbeit/
    python3 scripts/figma_plan.py skillmatrix.json arbeit/ --pdf "ausgabe/… .pdf"
    python3 scripts/figma_plan.py --schritt 3 arbeit/figma_plan.json

Die dritte Form gibt den Knotenbaum eines Bauschritts kompakt aus — genau so,
wie er als KNOTEN in den use_figma-Aufruf gehoert.

Schreibt arbeit/figma_plan.json mit

  - schritte: die Bauschritte, je einer ein use_figma-Aufruf. Jeder Schritt
    traegt einen fertigen Knotenbaum und nennt den Elternknoten, in den er
    gehaengt wird ("SEITE" oder der Name eines zuvor gemerkten Knotens).
  - uploads:  welche Rasterbilder (Foto, Zertifikate) auf welchen Platzhalter
    gehoeren.

Der Knotenbaum bildet den Aufbau der Figma-Vorlage nach — Auto-Layout mit
Abstaenden, Konturen innen, Schatten als Effekte, das Kartenraster als
GRID-Layout. Jeder Wert kommt aus assets/tokens.json, derselben Quelle wie das
PDF; hier wird nichts erfunden. Das use_figma-Skript aus references/figma.md
setzt nur, was im Plan steht.

`--pdf` ist optional und traegt nur die Seitenhoehe als Sollwert ein, gegen die
der fertige Frame gehalten wird.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert
from render_skillmatrix import BESCHRIFTUNG  # noqa: E402

ASSETS = design_system.ASSETS
DS = design_system.laden()
KOMP = DS["komponenten"]

# Muss der Vorgabe in render_skillmatrix.html_bauen() entsprechen — der
# Ansprechpartner steht als Vorgabe im Skill, nicht in der skillmatrix.json.
KONTAKT_VORGABE = {
    "name": "Manuel Klein", "rolle": "CCO",
    "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0)155 1148 0130",
    "firma": "New Monday GmbH", "strasse": "Stresemannstraße 32",
    "ort": "10963 Berlin",
}

hinweise = []


# --- Werte aus den Tokens ---------------------------------------------------

def m(ref):
    """Mass in pt (Tokenname oder Zahl)."""
    return design_system.aufloesen(DS, ref)


def f(ref):
    return design_system.farbe(DS, ref)


def kontur(rahmen, seiten=None, im_layout=True):
    """Kontur innen. seiten = [oben, rechts, unten, links] (1 = Kontur, 0 =
    keine) fuer einseitige Konturen — Figma kann das (strokeTopWeight …), ein
    Ersatzrechteck braucht es nicht."""
    k = {"farbe": f(rahmen["farbe"]), "im_layout": im_layout}
    if seiten:
        k["seiten"] = [rahmen["breite"] if s else 0 for s in seiten]
    else:
        k["breite"] = rahmen["breite"]
    return k


def schatten(ref):
    return [{s: v for s, v in e.items() if not s.startswith("_")}
            for e in design_system.schatten_ebenen(DS, ref)]


def _padding(p):
    if isinstance(p, (int, float)):
        return [p, p, p, p]
    if len(p) == 2:
        return [p[0], p[1], p[0], p[1]]
    return list(p)


# --- Knoten -----------------------------------------------------------------

def rahmen(name, layout, kinder=(), *, abstand=0, padding=0, breite="HUG",
           hoehe="HUG", haupt="MIN", quer="MIN", fuellung=None, kontur=None,
           radius=0, schatten=None, clip=False, absolut=None, umbruch=None,
           raster=None, merken=False):
    """layout: "VERTICAL", "HORIZONTAL", "GRID" oder None (freie Kinder).
    breite/hoehe: Zahl (fest), "HUG" oder "FILL"."""
    k = {"typ": "rahmen", "name": name, "layout": layout,
         "breite": breite, "hoehe": hoehe, "fuellung": fuellung, "clip": clip}
    if layout in ("VERTICAL", "HORIZONTAL"):
        k.update(abstand=abstand, padding=_padding(padding), haupt=haupt, quer=quer)
    if raster:
        k["raster"] = raster
    for schluessel, wert in (("kontur", kontur), ("radius", radius), ("schatten", schatten),
                             ("absolut", absolut), ("umbruch", umbruch)):
        if wert:
            k[schluessel] = wert
    if merken:
        k["merken"] = True
    k["kinder"] = list(kinder)
    return k


def text(name, inhalt, verwendung, breite="HUG", mehrzeilig=False):
    s = design_system.textstil(DS, verwendung)
    inhalt = str(inhalt or "")
    if not mehrzeilig:
        inhalt = " ".join(inhalt.split())
    zeile = ({"einheit": "PIXELS", "wert": s["zeilenhoehe_pt"]} if s.get("zeilenhoehe_pt")
             else {"einheit": "PERCENT", "wert": round(s["zeilenhoehe"] * 100, 3)})
    lauf = ({"einheit": "PERCENT", "wert": s["laufweite_prozent"]} if s.get("laufweite_prozent")
            else {"einheit": "PIXELS", "wert": s.get("laufweite", 0)})
    return {"typ": "text", "name": name, "text": inhalt, "breite": breite,
            "stil": s["stilname"], "farbe": s["farbe"],
            "typo": {"familie": s["familie"], "schnitt": s["figma_schnitt"],
                     "groesse": s["groesse"], "zeilenhoehe": zeile, "laufweite": lauf,
                     "versalien": s["versalien"]}}


def svg(name, datei, breite, hoehe):
    """SVG direkt als Markup — createNodeFromSvg braucht kein Netz. XML-Prolog,
    Kommentare und Zeilenumbrueche fliegen raus, damit der Code klein bleibt."""
    markup = (ASSETS / datei).read_text(encoding="utf-8")
    markup = re.sub(r"<\?xml.*?\?>|<!--.*?-->", "", markup, flags=re.S)
    markup = re.sub(r">\s+<", "><", markup).strip()
    return {"typ": "svg", "name": name, "svg": markup, "breite": breite, "hoehe": hoehe}


def bild(name, wert, breite, hoehe, deckkraft=None, absolut=None):
    """Platzhalter fuers Rasterbild; die Bytes kommen spaeter per upload_assets."""
    datei = None
    if wert:
        p = Path(str(wert)).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        if p.exists():
            datei = str(p)
        else:
            hinweise.append(f"{name}: Datei nicht gefunden — {wert}")
    k = {"typ": "bild", "name": name, "datei": datei, "breite": breite, "hoehe": hoehe,
         "merken": True}
    if deckkraft is not None:
        k["deckkraft"] = deckkraft
    if absolut:
        k["absolut"] = absolut
    return k


def form(typ, name, breite, hoehe, fuellung, radius=0):
    k = {"typ": typ, "name": name, "breite": breite, "hoehe": hoehe, "fuellung": fuellung}
    if radius:
        k["radius"] = radius
    return k


# --- Baender ----------------------------------------------------------------

def kopf():
    k = KOMP["kopf"]
    return rahmen("Kopf", "HORIZONTAL",
                  [svg("Logo", "nm-logo-weiss.svg", k["logo-breite"], k["logo-hoehe"])],
                  padding=(m(k["padding-y"]), m(k["padding-x"])), quer="CENTER",
                  breite="FILL", hoehe=k["hoehe"], fuellung=f(k["hintergrund"]))


def hero(person, labels):
    h, b, sp, fk = KOMP["hero"], KOMP["badge"], KOMP["schwerpunkt"], KOMP["fotokarte"]

    def unten_luft(name, kind):
        # Die Text-Instanzen der Vorlage tragen 8pt Abstand unter dem Text.
        return rahmen(name, "VERTICAL", [kind], padding=(0, 0, m(h["text-unten"]), 0),
                      breite="FILL")

    badge = rahmen("Badge", "HORIZONTAL", [
        form("ellipse", "Punkt", b["punkt"], b["punkt"], f(b["punkt-farbe"])),
        text("Verfuegbarkeit",
             f"{labels['verfuegbar']} {person.get('verfuegbar_ab', '')}".strip(), "badge"),
    ], abstand=m(b["abstand"]), padding=(m(b["padding-y"]), m(b["padding-x"])), quer="CENTER",
        fuellung=f(b["hintergrund"]), kontur=kontur(b["rahmen"]), radius=m(b["radius"]))

    titel = rahmen("Name und Rolle", "VERTICAL", [
        unten_luft("Name", text("Name", person.get("name"), "hero-name", breite="FILL")),
        unten_luft("Rolle", text("Rolle", person.get("rolle"), "hero-rolle", breite="FILL")),
    ], breite="FILL")
    beschreibung = unten_luft("Beschreibung", text(
        "Beschreibung", person.get("beschreibung"), "hero-beschreibung", breite="FILL"))
    textblock = rahmen("Titel und Text", "VERTICAL", [titel, beschreibung],
                       abstand=m(h["abstand-text"]), breite="FILL")

    tags = [rahmen("Schwerpunkt", "HORIZONTAL", [text("Schwerpunkt", s, "schwerpunkt")],
                   abstand=m(sp["abstand"]),
                   padding=(m(sp["padding-y"]), m(sp["padding-x"])), hoehe=sp["hoehe"],
                   quer="CENTER", fuellung=f(sp["hintergrund"]), kontur=kontur(sp["rahmen"]),
                   radius=m(sp["radius"]))
            for s in person.get("schwerpunkte") or []]
    inhalt = [textblock]
    if tags:
        inhalt.append(rahmen("Schwerpunkte", "HORIZONTAL", tags,
                             abstand=m(KOMP["schwerpunkte"]["abstand"]), quer="CENTER"))
    spalte = rahmen("Text", "VERTICAL", [
        badge,
        rahmen("Inhalt", "VERTICAL", inhalt, abstand=m(h["abstand-schwerpunkte"]), breite="FILL"),
    ], abstand=m(h["abstand-badge"]), breite=h["textspalte"])

    # Fotokarte wie die Komponente: freie Kinder, Foto um die Konturbreite
    # eingerueckt, Verlauf unten ueber die volle Breite, Kontur obenauf.
    rb = fk["rahmen"]["breite"]
    if not person.get("foto"):
        hinweise.append("Kein Foto — die Fotokarte im Frame zeigt nur den Verlauf.")
    fotokarte = rahmen("Fotokarte", None, [
        bild("Foto", person.get("foto"), fk["bild-breite"], fk["bild-hoehe"],
             deckkraft=fk["bild-deckkraft"], absolut={"x": rb, "y": rb}),
        rahmen("Verlauf", "VERTICAL", [
            text("Name", person.get("name"), "foto-name", breite="FILL"),
            text("Erfahrung", person.get("erfahrung"), "foto-erfahrung", breite="FILL"),
        ], padding=m(fk["verlauf-padding"]), breite=fk["breite"], radius=m(fk["verlauf-radius"]),
            fuellung={"verlauf": {"farbe": f(fk["verlauf"]["farbe"]),
                                  "voll_anteil": fk["verlauf"]["voll-anteil"]}},
            absolut={"x": 0, "unten": 0}),
    ], breite=fk["breite"], hoehe=fk["hoehe"], radius=m(fk["radius"]), clip=True,
        fuellung=f(fk["hintergrund"]), kontur=kontur(fk["rahmen"]))

    return rahmen("Hero", "HORIZONTAL", [spalte, fotokarte],
                  padding=(m(h["padding-y"]), m(h["padding-x"])), haupt="SPACE_BETWEEN",
                  breite="FILL", fuellung=f(h["hintergrund"]))


def sektionstitel(icon, titel):
    st = KOMP["sektionstitel"]
    return rahmen("Ueberschrift", "HORIZONTAL", [
        svg("Icon", icon, st["icon"], st["icon"]), text("Titel", titel, "sektion-titel")],
        abstand=m(st["abstand"]), quer="CENTER")


def zertkarte(z, labels):
    zk, jahr, zt, tag = KOMP["zertkarte"], KOMP["jahr"], KOMP["zert-tags"], KOMP["zert-tag"]
    innen = KOMP["seite"]["inhalt"] - zk["kante"]["breite"] - 2 * m(zk["padding"])
    # Titel fuellt, das Jahr huggt: So steht das Jahr rechtsbuendig, und ein
    # langer Titel bricht um, statt ins Jahr zu laufen.
    titelzeile = [text("Titel", z.get("titel"), "zert-titel", breite="FILL")]
    if z.get("jahr"):
        titelzeile.append(rahmen("Jahr", "HORIZONTAL", [text("Jahr", z["jahr"], "zert-jahr")],
                                 padding=(m(jahr["padding-y"]), m(jahr["padding-x"])),
                                 quer="CENTER", fuellung=f(jahr["hintergrund"]),
                                 kontur=kontur(jahr["rahmen"]), radius=m(jahr["radius"])))
    kopfgruppe = [rahmen("Titelzeile", "HORIZONTAL", titelzeile,
                         abstand=m(zk["jahr-abstand-min"]), breite="FILL")]
    if z.get("aussteller"):
        kopfgruppe.append(text("Aussteller", f"{labels['aussteller']} {z['aussteller']}",
                               "zert-aussteller", breite="FILL"))
    teile = [rahmen("Kopf", "VERTICAL", kopfgruppe, abstand=m(zk["gruppen-abstand"]),
                    breite="FILL")]
    unten = []
    if z.get("beschreibung"):
        unten.append(text("Beschreibung", z["beschreibung"], "zert-beschreibung", breite="FILL"))
    if z.get("tags"):
        # Umbruch braucht eine feste Breite, sonst weiss Figma nicht, wo.
        unten.append(rahmen("Tags", "HORIZONTAL", [
            rahmen("Tag", "HORIZONTAL", [text("Tag", t, "zert-tag")],
                   padding=(m(tag["padding-y"]), m(tag["padding-x"])), quer="CENTER",
                   fuellung=f(tag["hintergrund"]), kontur=kontur(tag["rahmen"]),
                   radius=m(tag["radius"]))
            for t in z["tags"]],
            abstand=m(zt["abstand"]), padding=(m(zt["abstand-oben"]), 0, 0, 0),
            breite=innen, umbruch=m(zt["abstand"])))
    if unten:
        teile.append(rahmen("Inhalt", "VERTICAL", unten, abstand=m(zk["gruppen-abstand"]),
                            breite="FILL"))
    return rahmen("Zertifikatskarte", "VERTICAL", teile, abstand=m(zk["abstand"]),
                  padding=m(zk["padding"]), breite="FILL", radius=m(zk["radius"]),
                  fuellung=f(zk["hintergrund"]),
                  kontur=kontur(zk["kante"], seiten=[0, 0, 0, 1]),
                  schatten=schatten(zk["schatten"]))


def sektion_zertifikate(daten, labels):
    za, ra = KOMP["zertifikate"], KOMP["raster"]
    karten = [zertkarte(z, labels) for z in daten.get("zertifikate") or []]
    bilder = list(daten.get("zertifikat_bilder") or [])
    if not karten and not bilder:
        return None
    oben = [sektionstitel("icon-zertifikat.svg", labels["zertifikate"])]
    if karten:
        oben.append(rahmen("Zertifikatskarten", "VERTICAL", karten,
                           abstand=m(za["karten-abstand"]), breite="FILL"))
    teile = [rahmen("Zertifikate oben", "VERTICAL", oben, abstand=m(za["titel-abstand"]),
                    breite="FILL")]
    if bilder:
        zeilen = []
        for i in range(0, len(bilder), ra["spalten"]):
            zeilen.append(rahmen(f"Zeile {len(zeilen) + 1}", "HORIZONTAL", [
                bild(f"Zertifikat {nr}", b, ra["kachel-breite"], ra["kachel-hoehe"])
                for nr, b in enumerate(bilder[i:i + ra["spalten"]], start=i + 1)],
                abstand=m(ra["abstand"])))
        teile.append(rahmen("Raster", "VERTICAL", zeilen, abstand=m(ra["abstand"]),
                            breite="FILL"))
    return rahmen("Zertifikate", "VERTICAL", teile, abstand=m(za["abstand"]), breite="FILL")


def skillkarte(s):
    sk, p = KOMP["skillkarte"], KOMP["punkte"]
    punkte = s.get("punkte") if isinstance(s.get("punkte"), int) else 0
    reihe = rahmen("Punkte", "HORIZONTAL", [
        form("rechteck", f"Punkt {i + 1}", p["groesse"], p["groesse"],
             f(p["voll"] if i < punkte else p["leer"]), radius=p["radius"])
        for i in range(p["anzahl"])], abstand=m(p["abstand"]))
    # Titel fuellt, die Punkte huggen — wie beim Zertifikatstitel.
    karte = rahmen("Skill Card", "VERTICAL", [
        rahmen("Kopf", "HORIZONTAL", [text("Titel", s.get("name"), "karte-titel", breite="FILL"),
                                      reihe],
               abstand=m(sk["titel-abstand-min"]), breite="FILL"),
        text("Beschreibung", s.get("beschreibung"), "karte-beschreibung", breite="FILL"),
    ], abstand=m(sk["abstand"]), padding=m(sk["padding"]), breite="FILL", hoehe="FILL",
        radius=m(sk["radius"]), fuellung=f(sk["hintergrund"]), kontur=kontur(sk["rahmen"]),
        schatten=schatten(sk["schatten"]), clip=True)
    karte["min_hoehe"] = sk["mindesthoehe"]       # wie im PDF: min-height
    return karte


def kategorie(k):
    ka, sr, kp = KOMP["kategorie"], KOMP["skillraster"], KOMP["kompetenzen"]
    label = rahmen("Label", "VERTICAL", [
        rahmen("Label mit Linie", "VERTICAL",
               [text("Kategorie", k.get("kategorie"), "kategorie")],
               padding=(0, 0, m(ka["text-unten"]), 0), breite="FILL",
               kontur=kontur(ka["linie"], seiten=[0, 0, 1, 0]))],
        padding=m(ka["padding"]), breite="FILL")
    # Wie die Vorlage: GRID mit drei gleich breiten Spalten, Zeilen huggen, die
    # Karten fuellen ihre Zelle — so sind Karten einer Zeile gleich hoch.
    karten = rahmen("Karten", "GRID", [skillkarte(s) for s in k.get("skills") or []],
                    raster={"spalten": sr["spalten"], "zeilenabstand": m(sr["zeilenabstand"]),
                            "spaltenabstand": m(sr["spaltenabstand"])},
                    breite="FILL")
    return rahmen(f"Kategorie — {k.get('kategorie')}", "VERTICAL", [label, karten],
                  abstand=m(kp["raster-abstand"]), breite="FILL")


def sektion_tools(tools, labels):
    """Eigene Sektion nach den Kernkompetenzen: Ueberschrift mit Tools-Icon, dann
    direkt das Kartenraster — ohne Kategorielabel, sonst wie eine Kategorie."""
    if len(tools) > KOMP["tools"]["anzahl"]:
        hinweise.append(f"{len(tools)} Tools gesetzt — die Sektion traegt hoechstens "
                        f"{KOMP['tools']['anzahl']} (zwei Reihen).")
    sr = KOMP["skillraster"]
    karten = rahmen("Karten", "GRID", [skillkarte(s) for s in tools],
                    raster={"spalten": sr["spalten"], "zeilenabstand": m(sr["zeilenabstand"]),
                            "spaltenabstand": m(sr["spaltenabstand"])},
                    breite="FILL")
    return rahmen("Tools", "VERTICAL", [sektionstitel("icon-tools.svg", labels["tools"]), karten],
                  abstand=m(KOMP["tools"]["titel-abstand"]), breite="FILL")


def fuss(daten, labels):
    fu = KOMP["fuss"]
    k = dict(KONTAKT_VORGABE)
    k.update(daten.get("kontakt") or {})

    def spalte(name, kinder):
        return rahmen(name, "VERTICAL", kinder, abstand=fu["label-abstand"])

    return rahmen("Fuss", "VERTICAL", [
        # Die Linie zaehlt wie in der Vorlage nicht zum Layout (im_layout False):
        # Block 36 + 32 = 68, Linie auf den untersten 1pt.
        rahmen("Frage", "VERTICAL",
               [text("Frage", labels["footer_frage"], "fuss-frage", breite=fu["frage-breite"])],
               padding=(0, 0, m(fu["frage-unten"]), 0), breite="FILL",
               kontur=kontur(fu["linie"], seiten=[0, 0, 1, 0], im_layout=False)),
        rahmen("Kontakt", "HORIZONTAL", [
            svg("Logo", "nm-logo-weiss.svg", fu["logo-breite"], fu["logo-hoehe"]),
            spalte("Ansprechpartner", [
                text("Label", labels["ansprechpartner"], "fuss-label"),
                text("Wert", f"{k['name']}\n{k['rolle']}", "fuss-wert", mehrzeilig=True)]),
            spalte("Kontakt", [
                text("Label", labels["kontakt"], "fuss-label"),
                rahmen("Werte", "VERTICAL", [text("Mail", k["mail"], "fuss-wert"),
                                             text("Telefon", k["telefon"], "fuss-wert")],
                       abstand=fu["kontakt-zeilenabstand"])]),
            spalte("Adresse", [
                text("Label", labels["adresse"], "fuss-label"),
                text("Wert", f"{k['firma']}\n{k['strasse']}\n{k['ort']}", "fuss-wert",
                     mehrzeilig=True)]),
        ], abstand=m(fu["spaltenabstand"])),
    ], abstand=m(fu["abstand"]), padding=(fu["padding-y"], fu["padding-x"]), breite="FILL",
        fuellung=f(fu["hintergrund"]))


def _bilder(knoten):
    if knoten.get("typ") == "bild" and knoten.get("datei"):
        yield {"knoten": knoten["name"], "datei": knoten["datei"]}
    for kind in knoten.get("kinder", []):
        yield from _bilder(kind)


def plan_bauen(daten, pdf=None):
    sprache = daten.get("sprache", "de")
    labels = dict(BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"]))
    if daten.get("zertifikate_titel"):
        labels["zertifikate"] = daten["zertifikate_titel"]
    person = daten.get("person") or {}
    name = " ".join(str(person.get("name") or "Skillmatrix").split())
    r = KOMP["rumpf"]

    rumpf = rahmen("Rumpf", "VERTICAL", [], abstand=m(r["sektionsabstand"]),
                   padding=(m(r["padding-oben"]), m(r["padding-x"]), m(r["padding-unten"]),
                            m(r["padding-x"])),
                   breite="FILL", fuellung=f(r["hintergrund"]),
                   kontur=kontur(r["linie-oben"], seiten=[1, 0, 0, 0]), merken=True)
    wurzel = rahmen(f"Skillmatrix — {name}", "VERTICAL", [
        # Der graue Rumpf reicht bis an den Fuss — kein weisser Streifen dazwischen.
        rahmen("Inhalt", "VERTICAL", [kopf(), hero(person, labels), rumpf],
               breite="FILL", clip=True),
        fuss(daten, labels),
    ], breite=KOMP["seite"]["breite"], fuellung=f(KOMP["seite"]["hintergrund"]), merken=True)

    schritte = [{"was": "Rahmen mit Kopf, Hero, leerem Rumpf und Fuss",
                 "eltern": "SEITE", "knoten": wurzel}]
    zert = sektion_zertifikate(daten, labels)
    zert_schritt = [{"was": "Zertifikate", "eltern": "Rumpf", "knoten": zert}] if zert else []
    kompetenzen = []
    if daten.get("kompetenzen"):
        kp = KOMP["kompetenzen"]
        kompetenzen.append({
            "was": "Kernkompetenzen: Ueberschrift und leere Kategorienliste",
            "eltern": "Rumpf",
            "knoten": rahmen("Kernkompetenzen", "VERTICAL", [
                sektionstitel("icon-kernkompetenzen.svg", labels["kernkompetenzen"]),
                rahmen("Kategorien", "VERTICAL", [], abstand=m(kp["kategorie-abstand"]),
                       breite="FILL", merken=True),
            ], abstand=m(kp["titel-abstand"]), breite="FILL")})
        for k in daten["kompetenzen"]:
            kompetenzen.append({"was": f"Kategorie {k.get('kategorie')}",
                                "eltern": "Kategorien", "knoten": kategorie(k)})
    if daten.get("tools"):
        kompetenzen.append({"was": "Tools", "eltern": "Rumpf",
                            "knoten": sektion_tools(daten["tools"], labels)})
    if daten.get("zertifikate_position") == "ende":
        schritte += kompetenzen + zert_schritt
    else:
        schritte += zert_schritt + kompetenzen

    schriften = {}
    for familie, schnitte in DS["figma_schnitte"].items():
        if not familie.startswith("_"):
            schriften[familie] = sorted(set(schnitte.values()))
    plan = {
        "rahmen": {"name": wurzel["name"], "breite": KOMP["seite"]["breite"]},
        "sprache": sprache,
        "schriften": schriften,
        "schritte": [{"nr": i + 1, **s} for i, s in enumerate(schritte)],
        "uploads": [b for s in schritte for b in _bilder(s["knoten"])],
    }
    if pdf:
        hoehe = pdf_hoehe(pdf)
        if hoehe:
            # Sollwert zum Gegenpruefen. Der Frame selbst huggt.
            plan["rahmen"]["hoehe_pdf"] = hoehe
    return plan


def pdf_hoehe(pfad):
    try:
        from pypdf import PdfReader
    except ImportError:
        hinweise.append("pypdf fehlt — die PDF-Hoehe kommt nicht in den Plan.")
        return None
    try:
        kasten = PdfReader(str(pfad)).pages[0].mediabox
        return round(float(kasten.height), 1)
    except Exception as fehler:                       # noqa: BLE001
        hinweise.append(f"PDF-Hoehe nicht lesbar: {fehler}")
        return None


def main():
    args = sys.argv[1:]
    if args[:1] == ["--schritt"] and len(args) == 3:
        plan = json.loads(Path(args[2]).read_text(encoding="utf-8"))
        schritt = next((s for s in plan["schritte"] if str(s["nr"]) == args[1]), None)
        if not schritt:
            raise SystemExit(f"Keinen Schritt {args[1]} im Plan.")
        print(json.dumps(schritt["knoten"], ensure_ascii=False, separators=(",", ":")))
        return
    pdf = None
    if "--pdf" in args:
        i = args.index("--pdf")
        if i + 1 >= len(args):
            raise SystemExit("--pdf braucht einen Pfad")
        pdf = args[i + 1]
        args = args[:i] + args[i + 2:]
    if len(args) < 2:
        raise SystemExit(__doc__)

    daten = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    ziel = Path(args[1])
    if ziel.suffix.lower() != ".json":
        ziel = ziel / "figma_plan.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)

    plan = plan_bauen(daten, pdf)
    ziel.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{ziel} geschrieben — {len(plan['schritte'])} Bauschritte, "
          f"{len(plan['uploads'])} Bilder zum Hochladen")
    for s in plan["schritte"]:
        groesse = len(json.dumps(s["knoten"], ensure_ascii=False, separators=(",", ":")))
        print(f"  {s['nr']:2}. {s['was']}  (in: {s['eltern']}, {groesse / 1000:.0f} KB)")
    if plan["rahmen"].get("hoehe_pdf"):
        print(f"Sollhoehe aus dem PDF: {plan['rahmen']['hoehe_pdf']}pt")
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
