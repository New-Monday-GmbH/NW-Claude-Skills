#!/usr/bin/env python3
"""Baut aus skillmatrix.json die Figma-Plaene beider Fassungen.

    python3 scripts/figma_plan.py skillmatrix.json arbeit/ \
            --pdf "ausgabe/… - Skillmatrix.pdf" --pdf-a4 "ausgabe/… - Skillmatrix A4.pdf"
    python3 scripts/figma_plan.py --skript vorflug|lang|a4 arbeit/ --seite 1:147 \
            [--bilder arbeit/bilder.json]
    python3 scripts/figma_plan.py --schritt 3 arbeit/figma_plan.json

Standard ist der Bibliotheksweg (references/figma.md): Die Frames entstehen aus
Instanzen der veroeffentlichten Master-Bibliothek ("Portfolio - CV Master",
Keys in assets/master-bibliothek.json) und werden ueber Component-Properties,
exponierte Instanzen und Bild-Overrides befuellt. Dafuer schreibt die erste
Form arbeit/figma_bibliothek.json (je Fassung der Befuellungsplan und die
hochzuladenden Bilder), und --skript gibt den fertigen use_figma-Code aus:
"vorflug" (Seiten, Schriften, ein Import per Key), "lang" (ein 1444er
Seitenrahmen aus Kopfzeile, Hero, Rumpf, Fuss) und "a4" (je Seite eine
Instanz "Skillmatrix A4/Seite"). --bilder ist die Ausgabe von
figma_assets.py --bilder (Datei -> imageHash).

Rueckfall, wenn die Bibliothek nicht erreichbar ist (Vorflug) oder eine
Fassung die Mengen der Komponenten sprengt: der rohe Weg aus den Bauplaenen
(figma_plan.json, figma_plan_a4.json, Schritte per --schritt).

Die rohen Plaene, einer je Fassung:

  - arbeit/figma_plan.json: die lange Fassung, ein Frame 1444 breit.
  - arbeit/figma_plan_a4.json: die A4-Fassung, je PDF-Seite ein Frame
    595 x 842.

Die Seitenaufteilung der A4-Fassung kommt in beiden Wegen aus dem A4-PDF
(Dokumentinfo /NewMondaySeiten, von render_skillmatrix.py beim Rendern
abgelegt) und wird gegen den Seitentext gehalten. Ohne A4-PDF entsteht kein
A4-Plan - geraten wird die Aufteilung nicht. Fehlt --pdf-a4, sucht das Skript
das A4-PDF neben dem langen (--pdf).

Jeder rohe Plan traegt

  - schritte: die Bauschritte, je einer ein use_figma-Aufruf. Jeder Schritt
    traegt einen fertigen Knotenbaum und nennt den Elternknoten, in den er
    gehaengt wird ("SEITE" oder der Name eines zuvor gemerkten Knotens).
  - uploads:  welche Rasterbilder (Foto, Zertifikate) auf welchen Platzhalter
    gehoeren.

Der lange Knotenbaum bildet den Aufbau der Figma-Vorlage nach — Auto-Layout mit
Abstaenden, Konturen innen, Schatten als Effekte, das Kartenraster als
GRID-Layout; der A4-Baum den abgenommenen A4-Vorschlag (Zeilen ohne Karten,
Eintraege einer Zeile gleich hoch, der Fuss unten auf der letzten Seite). Jeder Wert kommt aus assets/tokens.json, derselben Quelle wie das
PDF; hier wird nichts erfunden. Das use_figma-Skript aus references/figma.md
setzt nur, was im Plan steht.

`--pdf` traegt die Seitenhoehe der langen Fassung als Sollwert ein, gegen die
der fertige Frame gehalten wird.

Wie render_skillmatrix.py ordnet der Plan die Kategorien (mit "anfrage" in der
JSON bleibt deren Reihenfolge, ohne steht die KI-Kategorie zuerst), zeichnet
leere Bewertungspunkte als Ringe und plant die Zertifikatskacheln mit
scripts/zertifikate.py (Buendel, Bildgroessen) — PDF und Frame zeigen
dasselbe. Zum Gegenpruefen rechnet
planhoehe() die Hoehen des Plans nach den Auto-Layout-Regeln aus (Texte
geschaetzt) und meldet Zertifikatssektion und Gesamthoehe; planhoehe_a4() je
A4-Seite die Hoehe des Inhalts.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert
import figma_bibliothek  # noqa: E402
import zertifikate  # noqa: E402
from render_skillmatrix import (  # noqa: E402
    KONTAKT_VORGABE, beschriftung, dateiname, foto_a4, kompetenzen_ordnen, seiten_lesen, zert_a4)

ASSETS = design_system.ASSETS
DS = design_system.laden()
KOMP = DS["komponenten"]
DS4 = design_system.fassung(DS, "a4")       # A4-Fassung: eigene Texte und Komponenten
K4 = DS4["komponenten"]

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


def _typo(s):
    zeile = ({"einheit": "PIXELS", "wert": s["zeilenhoehe_pt"]} if s.get("zeilenhoehe_pt")
             else {"einheit": "PERCENT", "wert": round(s["zeilenhoehe"] * 100, 3)})
    lauf = ({"einheit": "PERCENT", "wert": s["laufweite_prozent"]} if s.get("laufweite_prozent")
            else {"einheit": "PIXELS", "wert": s.get("laufweite", 0)})
    return {"familie": s["familie"], "schnitt": s["figma_schnitt"],
            "groesse": s["groesse"], "zeilenhoehe": zeile, "laufweite": lauf,
            "versalien": s["versalien"]}


def text(name, inhalt, verwendung, breite="HUG", mehrzeilig=False, max_zeilen=None, ds=None):
    """max_zeilen: nach so vielen Zeilen mit Auslassungszeichen kuerzen
    (textTruncation ENDING) — wie line-clamp im PDF. ds: die Fassung, deren
    Textstile gelten (Vorgabe: die lange)."""
    s = design_system.textstil(ds or DS, verwendung)
    inhalt = str(inhalt or "")
    if not mehrzeilig:
        inhalt = " ".join(inhalt.split())
    k = {"typ": "text", "name": name, "text": inhalt, "breite": breite,
         "stil": s["stilname"], "farbe": s["farbe"], "verwendung": verwendung,
         "typo": _typo(s)}
    if max_zeilen:
        k["max_zeilen"] = max_zeilen
    return k


def svg(name, datei, breite, hoehe):
    """SVG direkt als Markup — createNodeFromSvg braucht kein Netz. XML-Prolog,
    Kommentare und Zeilenumbrueche fliegen raus, damit der Code klein bleibt."""
    markup = (ASSETS / datei).read_text(encoding="utf-8")
    markup = re.sub(r"<\?xml.*?\?>|<!--.*?-->", "", markup, flags=re.S)
    markup = re.sub(r">\s+<", "><", markup).strip()
    return {"typ": "svg", "name": name, "svg": markup, "breite": breite, "hoehe": hoehe}


def bild(name, wert, breite, hoehe, deckkraft=None, absolut=None, skalierung="FILL"):
    """Platzhalter fuers Rasterbild; die Bytes kommen spaeter per upload_assets
    mit scaleMode = skalierung (Foto FILL, Zertifikate FIT)."""
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
         "skalierung": skalierung, "merken": True}
    if deckkraft is not None:
        k["deckkraft"] = deckkraft
    if absolut:
        k["absolut"] = absolut
    return k


def form(typ, name, breite, hoehe, fuellung, radius=0, kontur=None):
    k = {"typ": typ, "name": name, "breite": breite, "hoehe": hoehe, "fuellung": fuellung}
    if radius:
        k["radius"] = radius
    if kontur:
        k["kontur"] = kontur
    return k


def punkt(p, nr, voll):
    """Ein Bewertungspunkt (p: tokens punkte der Fassung). Voll: gefuellt in
    p["voll"]. Leer: ein Ring - Fuellung p["leer"], Kontur innen aus
    p["leer-rahmen"], gleiche Groesse und gleicher Radius wie der volle."""
    return form("rechteck", f"Punkt {nr}", p["groesse"], p["groesse"],
                f(p["voll"] if voll else p["leer"]), radius=p["radius"],
                kontur=None if voll else kontur(p["leer-rahmen"]))


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


def zertbild(e):
    """Bild eingepasst — ein Rechteck mit dem Seitenverhaeltnis der Datei,
    scaleMode FIT, nie verzerrt — oder das Platzhalterfeld mit Icon bzw. "+3"."""
    zb = KOMP["zertbild"]
    if e.get("bild"):
        k = bild(f"Zertifikat {e['nr']}", e["bild"], e["breite"], e["hoehe"], skalierung="FIT")
        k.update(radius=zb["radius"], kontur=kontur(zb["rahmen"]))
        return k
    inhalt = (text("Anzahl", f"+{e['anzahl']}", "zert-anzahl") if e["art"] == "buendel"
              else svg("Icon", "icon-zertifikat.svg", zb["icon"], zb["icon"]))
    return rahmen(f"Platzhalter {e['nr']}", "HORIZONTAL", [inhalt], breite=e["breite"],
                  hoehe=e["hoehe"], haupt="CENTER", quer="CENTER",
                  fuellung=f(zb["platz-hintergrund"]), kontur=kontur(zb["rahmen"]),
                  radius=zb["radius"])


def zerttext(e, g):
    """Titel und "Aussteller · Jahr", gekuerzt nach der geplanten Zeilenzahl.
    Das Textfeld ist fest hoch, damit die Kachel auch in Figma 259 bleibt."""
    kinder = [text("Titel", e["titel"], "karte-titel", breite="FILL", max_zeilen=e["titel_max"])]
    if e["meta"]:
        kinder.append(text("Aussteller und Jahr", e["meta"], "zert-aussteller", breite="FILL",
                           max_zeilen=e["meta_max"]))
    return rahmen("Text", "VERTICAL", kinder, abstand=g["text_abstand"], breite="FILL",
                  hoehe=g["text_hoehe"])


def buehne(e, g):
    b = KOMP["zertbuehne"]
    return rahmen("Buehne", "HORIZONTAL", [zertbild(e)], padding=m(b["padding"]), breite="FILL",
                  hoehe=g["buehne"][1], haupt="CENTER", quer="CENTER",
                  fuellung=f(b["hintergrund"]), radius=m(b["radius"]))


def qualikarte(karte, labels):
    """Erworbene Qualifikationen: Titel, darunter Satz und umbrechende
    Tag-Reihe. Wie die Komponente "Zertifikate Erklaerung" - volle Breite,
    Kontur innen, kein Schatten. Nichts wird gekuerzt."""
    q, qt, qg = KOMP["qualikarte"], KOMP["qualitag"], KOMP["qualitags"]
    block = []
    if karte["text"]:
        block.append(text("Text", karte["text"], "quali-text", breite="FILL"))
    if karte["tags"]:
        # Abstand oben als Padding der Reihe, wie in der Komponente; Zeilen
        # brechen mit demselben Abstand um.
        block.append(rahmen("Tags", "HORIZONTAL", [
            rahmen("Tag", "HORIZONTAL", [text("Tag", t, "quali-tag")],
                   padding=(m(qt["padding-y"]), m(qt["padding-x"])),
                   fuellung=f(qt["hintergrund"]), kontur=kontur(qt["rahmen"]),
                   radius=m(qt["radius"]))
            for t in karte["tags"]],
            abstand=m(qg["abstand"]), padding=(m(qg["abstand"]), 0, 0, 0), breite="FILL",
            umbruch=m(qg["abstand"])))
    return rahmen("Erworbene Qualifikationen", "VERTICAL", [
        text("Titel", labels["qualifikationen"], "quali-titel", breite="FILL"),
        rahmen("Block", "VERTICAL", block, abstand=m(q["gruppen-abstand"]), breite="FILL")],
        abstand=m(q["abstand"]), padding=m(q["padding"]), breite="FILL",
        radius=m(q["radius"]), fuellung=f(q["hintergrund"]), kontur=kontur(q["rahmen"]))


def sektion_zertifikate(zp, labels):
    """Ueberschrift, Qualifikationskarte (falls belegt), vier Kacheln je Reihe -
    gebaut wie die Skill Card."""
    if not zp:
        return None
    g, t = zp["geometrie"], KOMP["zertkachel"]
    eintraege = zp["eintraege"]
    zeilen = [rahmen(f"Zeile {nr}", "HORIZONTAL", [
        rahmen("Kachel", "VERTICAL", [buehne(e, g), zerttext(e, g)],
               abstand=m(t["abstand"]), padding=m(t["padding"]), breite=g["breite"],
               radius=m(t["radius"]), fuellung=f(t["hintergrund"]), kontur=kontur(t["rahmen"]),
               schatten=schatten(t["schatten"]))
        for e in eintraege[i:i + g["spalten"]]], abstand=g["spaltenabstand"])
        for nr, i in enumerate(range(0, len(eintraege), g["spalten"]), start=1)]
    kinder = [sektionstitel("icon-zertifikat.svg", labels["zertifikate"])]
    if zp.get("karte"):
        kinder.append(qualikarte(zp["karte"], labels))
    kinder.append(rahmen("Kacheln", "VERTICAL", zeilen, abstand=g["zeilenabstand"], breite="FILL"))
    return rahmen("Zertifikate", "VERTICAL", kinder,
                  abstand=m(KOMP["zertifikate"]["titel-abstand"]), breite="FILL")


def skillkarte(s):
    sk, p = KOMP["skillkarte"], KOMP["punkte"]
    punkte = s.get("punkte") if isinstance(s.get("punkte"), int) else 0
    reihe = rahmen("Punkte", "HORIZONTAL", [punkt(p, i + 1, i < punkte) for i in range(p["anzahl"])],
                   abstand=m(p["abstand"]))
    # Titel fuellt, die Punkte huggen.
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
        yield {"knoten": knoten["name"], "datei": knoten["datei"],
               "scaleMode": knoten.get("skalierung", "FILL")}
    for kind in knoten.get("kinder", []):
        yield from _bilder(kind)


def plan_bauen(daten, pdf=None):
    sprache = daten.get("sprache", "de")
    labels = beschriftung(daten)
    # Wie im PDF: Reihenfolge der Kategorien (mit Anfrage die der JSON, ohne
    # die KI-Kategorie zuerst), Zertifikate geplant und gebuendelt.
    daten, reihenfolge_hinweis = kompetenzen_ordnen(daten)
    if reihenfolge_hinweis:
        hinweise.append(reihenfolge_hinweis)
    zplan, zert_hinweise = zertifikate.planen(daten, DS, labels)
    hinweise.extend(zert_hinweise)
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
    zert = sektion_zertifikate(zplan, labels)
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
    if zplan:
        plan["zertifikate"] = {
            "kacheln": len(zplan["eintraege"]),
            "karte": ({"hoehe": zplan["karte"]["hoehe"], "tags": len(zplan["karte"]["tags"]),
                       "tag_reihen": zplan["karte"]["tag_reihen"]} if zplan.get("karte") else None),
            "gebuendelt": [{"aussteller": e["aussteller"] or "Sammelkachel", "anzahl": e["anzahl"]}
                           for e in zplan["eintraege"] if e["art"] == "buendel"],
            "hoehe_geplant": zplan["hoehe"], "grenze": zplan["grenze"]}
        if zplan["hoehe"] > zplan["grenze"]:
            hinweise.append(f"Zertifikatssektion im Plan {zplan['hoehe']:g}pt — ueber der "
                            f"Grenze von {zplan['grenze']}pt.")
    if pdf:
        hoehe = pdf_hoehe(pdf)
        if hoehe:
            # Sollwert zum Gegenpruefen. Der Frame selbst huggt.
            plan["rahmen"]["hoehe_pdf"] = hoehe
    return plan


# --- A4-Fassung ------------------------------------------------------------
#
# Je PDF-Seite ein Frame 595 x 842, aufgebaut wie der abgenommene Vorschlag
# (Frames 2347:48 ff.): Kopfzeile, Inhalt (35,5 oben, Bloecke 32 auseinander),
# auf der letzten Seite der Fuss. Der Inhalt der letzten Seite fuellt die Hoehe
# (FILL), so sitzt der Fuss unten - in Figma die Entsprechung der gemessenen
# Fussluft im PDF. Alle Werte aus tokens.json, Block "a4".

def t4(name, inhalt, verwendung, breite="HUG", **rest):
    return text(name, inhalt, verwendung, breite, ds=DS4, **rest)


def a4_kopfzeile(person, labels, erste):
    k, b = K4["kopf"], K4["badge"]
    kinder = [svg("Logo", "nm-logo.svg", k["logo-breite"], k["logo-hoehe"])]
    if erste:
        kinder.append(rahmen("Badge", "HORIZONTAL", [
            form("ellipse", "Punkt", b["punkt"], b["punkt"], f(b["punkt-farbe"])),
            t4("Verfuegbarkeit",
               f"{labels['verfuegbar']} {person.get('verfuegbar_ab', '')}".strip(), "badge"),
        ], abstand=m(b["abstand"]), padding=(m(b["padding-y"]), m(b["padding-x"])), quer="CENTER",
            fuellung=f(b["hintergrund"]), kontur=kontur(b["rahmen"]), radius=m(b["radius"])))
    # Feste Hoehe 13,5: das Badge (20) ragt oben und unten gleich weit hinaus.
    return rahmen("Kopfzeile", "HORIZONTAL", kinder, haupt="SPACE_BETWEEN" if erste else "MIN",
                  quer="CENTER", breite="FILL", hoehe=k["hoehe"])


def a4_hero(person, foto):
    h, sp, fk = K4["hero"], K4["schwerpunkt"], K4["fotokarte"]
    textspalte = [rahmen("Name und Rolle", "VERTICAL", [
        t4("Name", person.get("name"), "hero-name", "FILL"),
        t4("Rolle", person.get("rolle"), "hero-rolle", "FILL"),
    ], abstand=m(h["name-unten"]), breite="FILL")]
    if person.get("schwerpunkte"):
        textspalte.append(rahmen("Schwerpunkte", "HORIZONTAL", [
            rahmen("Schwerpunkt", "HORIZONTAL", [t4("Schwerpunkt", s, "schwerpunkt")],
                   padding=(m(sp["padding-y"]), m(sp["padding-x"])), fuellung=f(sp["hintergrund"]),
                   kontur=kontur(sp["rahmen"]), radius=m(sp["radius"]))
            for s in person["schwerpunkte"]],
            abstand=m(K4["schwerpunkte"]["abstand"]), breite="FILL",
            umbruch=m(K4["schwerpunkte"]["abstand"])))
        textspalte[-1]["umbruch_gap"] = True          # wie im A4-PDF (gap)
    if not foto:
        hinweise.append("A4: Kein Foto — die Fotokarte bleibt leer.")
    # Fotokarte ohne Verlauf: das Foto fuellt sie, die Kontur liegt obenauf.
    fotokarte = rahmen("Fotokarte", None, [
        bild("Foto", foto, fk["bild-breite"], fk["bild-hoehe"], deckkraft=fk["bild-deckkraft"])],
        breite=fk["breite"], hoehe=fk["hoehe"], radius=m(fk["radius"]), clip=True,
        fuellung=f(fk["hintergrund"]), kontur=kontur(fk["rahmen"]))
    profil = rahmen("Profil", "HORIZONTAL", [
        rahmen("Text", "VERTICAL", textspalte, abstand=m(h["abstand-schwerpunkte"]), breite="FILL"),
        fotokarte], abstand=m(h["spaltenabstand"]), breite="FILL")
    return rahmen("Hero", "VERTICAL", [
        profil, t4("Beschreibung", person.get("beschreibung"), "hero-beschreibung", "FILL")],
        abstand=m(h["abstand-beschreibung"]), breite="FILL")


def a4_ueberschrift(icon, titel):
    st = K4["sektionstitel"]
    return rahmen("Ueberschrift", "HORIZONTAL", [
        svg("Icon", icon, st["icon"], st["icon"]), t4("Titel", titel, "sektion-titel")],
        abstand=m(st["abstand"]), quer="CENTER")


def a4_zertbild(e):
    zb = K4["zertbild"]
    if e.get("bild"):
        k = bild(f"Zertifikat {e['nr']}", e["bild"], e["a4_breite"], e["a4_hoehe"], skalierung="FIT")
        k.update(radius=zb["radius"], kontur=kontur(zb["rahmen"]))
        return k
    inhalt = (t4("Anzahl", f"+{e['anzahl']}", "zert-anzahl") if e["art"] == "buendel"
              else svg("Icon", "icon-zertifikat.svg", zb["icon"], zb["icon"]))
    return rahmen(f"Platzhalter {e['nr']}", "HORIZONTAL", [inhalt], breite=e["a4_breite"],
                  hoehe=e["a4_hoehe"], haupt="CENTER", quer="CENTER",
                  fuellung=f(zb["platz-hintergrund"]), kontur=kontur(zb["rahmen"]),
                  radius=zb["radius"])


def a4_kachelzeile(nr, eintraege):
    t, b = K4["zertkachel"], K4["zertbuehne"]
    kacheln = []
    for e in eintraege:
        texte = [t4("Titel", e["titel"], "zert-titel", "FILL", max_zeilen=t["titel-zeilen"])]
        if e.get("meta"):
            texte.append(t4("Aussteller und Jahr", e["meta"], "zert-aussteller", "FILL",
                            max_zeilen=t["meta-zeilen"]))
        kacheln.append(rahmen("Kachel", "VERTICAL", [
            rahmen("Buehne", "HORIZONTAL", [a4_zertbild(e)], padding=m(b["padding"]), breite="FILL",
                   hoehe=t["buehne-hoehe"], haupt="CENTER", quer="CENTER",
                   fuellung=f(b["hintergrund"]), radius=m(b["radius"])),
            rahmen("Text", "VERTICAL", texte, abstand=t["text-abstand"], breite="FILL"),
        ], abstand=m(t["abstand"]), breite=t["breite"]))
    return rahmen(f"Zeile {nr}", "HORIZONTAL", kacheln, abstand=m(t["spaltenabstand"]), breite="FILL")


def a4_qualikarte(karte, labels):
    q, qt, qg = K4["qualikarte"], K4["qualitag"], K4["qualitags"]
    block = []
    if karte["text"]:
        block.append(t4("Satz", karte["text"], "quali-text", "FILL"))
    if karte["tags"]:
        block.append(rahmen("Tags", "HORIZONTAL", [
            rahmen("Tag", "HORIZONTAL", [t4("Tag", tag, "quali-tag")],
                   padding=(m(qt["padding-y"]), m(qt["padding-x"])), kontur=kontur(qt["rahmen"]),
                   radius=m(qt["radius"]))
            for tag in karte["tags"]],
            abstand=m(qg["abstand"]), breite="FILL", umbruch=m(qg["abstand"])))
        block[-1]["umbruch_gap"] = True               # wie im A4-PDF (gap)
    return rahmen("Qualifikationskarte", "VERTICAL", [
        t4("Titel", labels["qualifikationen"], "quali-titel", "FILL"),
        rahmen("Satz und Tags", "VERTICAL", block, abstand=m(q["gruppen-abstand"]), breite="FILL")],
        abstand=m(q["abstand"]), padding=m(q["padding"]), breite="FILL", radius=m(q["radius"]),
        fuellung=f(q["hintergrund"]), kontur=kontur(q["rahmen"]))


def a4_zertifikate(za4, labels, auf_seite, nr, fortsetzung):
    """Was von der Zertifikatssektion auf Seite nr steht: Ueberschrift, Karte
    und ein leerer Rahmen "Kacheln — Seite nr" fuer die Reihen (je Reihe ein
    eigener Bauschritt, damit kein Aufruf zu gross wird). auf_seite: die
    data-block-Namen dieser Seite. Gibt (knoten, reihen) zurueck."""
    kinder = []
    if "zert-titel" in auf_seite:
        kinder.append(a4_ueberschrift("icon-zertifikat.svg", labels["zertifikate"]))
    if za4.get("karte") and "zert-karte" in auf_seite:
        kinder.append(a4_qualikarte(za4["karte"], labels))
    spalten = K4["zertkachel"]["spalten"]
    reihen = [a4_kachelzeile(z, za4["eintraege"][i:i + spalten])
              for z, i in enumerate(range(0, len(za4["eintraege"]), spalten), start=1)
              if f"zert-zeile-{z}" in auf_seite]
    if reihen:
        kinder.append(rahmen(f"Kacheln — Seite {nr}", "VERTICAL", [],
                             abstand=m(K4["zertkachel"]["zeilenabstand"]), breite="FILL", merken=True))
    name = "Zertifikate (Fortsetzung)" if fortsetzung else "Zertifikate"
    return (rahmen(name, "VERTICAL", kinder, abstand=m(K4["sektionstitel"]["unten"]), breite="FILL"),
            reihen)


def a4_zeilen(skills):
    """Kernkompetenzen und Tools als Zeilen ohne Karten: zwei Spalten, Eintraege
    einer Zeile gleich hoch (Zeile huggt, Eintraege fuellen), ab der zweiten
    Zeile mit Haarlinie oben."""
    e, p = K4["eintraege"], K4["punkte"]
    zeilen = []
    for nr, i in enumerate(range(0, len(skills), e["spalten"]), start=1):
        eintraege = []
        for s in skills[i:i + e["spalten"]]:
            punkte = s.get("punkte") if isinstance(s.get("punkte"), int) else 0
            reihe = rahmen("Punkte", "HORIZONTAL", [punkt(p, j + 1, j < punkte)
                                                    for j in range(p["anzahl"])],
                           abstand=m(p["abstand"]), padding=(m(p["oben"]), 0, 0, 0))
            eintraege.append(rahmen("Eintrag", "VERTICAL", [
                rahmen("Kopf", "HORIZONTAL", [t4("Titel", s.get("name"), "eintrag-titel", "FILL"), reihe],
                       abstand=m(e["titel-abstand"]), breite="FILL"),
                t4("Beschreibung", s.get("beschreibung"), "eintrag-beschreibung", "FILL"),
            ], abstand=e["abstand"], padding=(e["padding-y"], 0, e["padding-y"], 0), breite=e["breite"],
                hoehe="FILL", kontur=kontur(e["linie"], seiten=[1, 0, 0, 0]) if nr > 1 else None))
        zeilen.append(rahmen(f"Zeile {nr}", "HORIZONTAL", eintraege,
                             abstand=m(e["spaltenabstand"]), breite="FILL"))
    return zeilen


def a4_kategorie(k):
    ka = K4["kategorie"]
    label = rahmen("Label", "VERTICAL", [t4("Kategorie", k.get("kategorie"), "kategorie")],
                   padding=(0, 0, m(ka["text-unten"]), 0), breite="FILL",
                   kontur=kontur(ka["linie"], seiten=[0, 0, 1, 0]))
    return rahmen(f"Kategorie — {k.get('kategorie')}", "VERTICAL", [
        label, rahmen("Zeilen", "VERTICAL", a4_zeilen(k.get("skills") or []), breite="FILL")],
        breite="FILL")


def a4_tools(tools, labels):
    return rahmen("Tools", "VERTICAL", [
        a4_ueberschrift("icon-tools.svg", labels["tools"]),
        rahmen("Eintraege", "VERTICAL", a4_zeilen(tools), breite="FILL",
               kontur=kontur(K4["tools"]["linie"], seiten=[1, 0, 0, 0]))],
        abstand=m(K4["sektionstitel"]["unten"]), breite="FILL")


def a4_fuss(daten, labels):
    """Wie der Fuss des Lebenslaufs: Linie, darunter Logo und drei Spalten."""
    fu = K4["fuss"]
    k = dict(KONTAKT_VORGABE)
    k.update(daten.get("kontakt") or {})
    spalte_b = round((fu["block"] - 2 * fu["spaltenabstand"]) / 3, 2)

    def spalte(name, werte):
        return rahmen(name, "VERTICAL", [
            t4("Label", labels[name.lower()], "fuss-label"),
            rahmen("Werte", "VERTICAL", werte, abstand=fu["werte-abstand"],
                   padding=(fu["label-abstand"], 0, 0, 0))], breite=spalte_b)

    return rahmen("Fuss", "VERTICAL", [
        form("rechteck", "Trennlinie", fu["breite"], fu["linie"]["breite"], f(fu["linie"]["farbe"])),
        rahmen("Fuss-Reihe", "HORIZONTAL", [
            svg("Logo", "nm-logo.svg", fu["logo-breite"], fu["logo-hoehe"]),
            rahmen("Spalten", "HORIZONTAL", [
                spalte("Ansprechpartner", [rahmen("Name und Rolle", "VERTICAL", [
                    t4("Name", k["name"], "fuss-name"), t4("Rolle", k["rolle"], "fuss-wert")])]),
                spalte("Kontakt", [t4("Mail", k["mail"], "fuss-wert"),
                                   t4("Telefon", k["telefon"], "fuss-wert")]),
                spalte("Adresse", [t4("Adresse", f"{k['firma']}\n{k['strasse']}\n{k['ort']}",
                                      "fuss-wert", mehrzeilig=True)]),
            ], abstand=fu["spaltenabstand"]),
        ], haupt="SPACE_BETWEEN", padding=(fu["abstand"], 0, 0, 0), breite=fu["breite"]),
    ], breite=fu["breite"])


def a4_seiten_aus_pdf(pdf, daten, labels):
    """Seitenaufteilung aus dem A4-PDF: {block: seite} und die Seitenzahl.
    Gegengeprueft am Seitentext (Kategorielabels stehen auf ihrer Seite)."""
    info = seiten_lesen(pdf)
    if not info:
        raise SystemExit(
            f"{pdf}: keine Seitenaufteilung im PDF (/NewMondaySeiten). Das A4-PDF mit "
            "render_skillmatrix.py neu rendern - geraten wird die Aufteilung nicht.")
    from pypdf import PdfReader
    texte = [" ".join((seite.extract_text() or "").split()).casefold()
             for seite in PdfReader(str(pdf)).pages]
    if len(texte) != info["seiten"]:
        hinweise.append(f"A4: Das PDF hat {len(texte)} Seiten, abgelegt sind {info['seiten']} — "
                        "neu rendern.")
    for nr, k in enumerate(daten.get("kompetenzen") or [], start=1):
        seite = info["bloecke"].get(f"kategorie-{nr}")
        label = " ".join(str(k.get("kategorie") or "").split()).casefold()
        if seite and label and seite <= len(texte) and label not in texte[seite - 1]:
            hinweise.append(f"A4: Kategorie „{k.get('kategorie')}“ steht laut PDF auf Seite {seite}, "
                            "ihr Label ist dort aber nicht zu finden — PDF und JSON passen nicht "
                            "zusammen, neu rendern.")
    return info["bloecke"], info["seiten"]


def plan_bauen_a4(daten, pdf_a4):
    """Der Bauplan der A4-Fassung: je Seite ein Rahmen-Schritt, dann die Bloecke
    der Seite in ihren Inhalt."""
    labels = beschriftung(daten)
    daten, _ = kompetenzen_ordnen(daten)              # gemeldet schon im langen Plan
    zplan, _ = zertifikate.planen(daten, DS, labels)
    za4 = zert_a4(zplan, DS4)
    person = daten.get("person") or {}
    name = " ".join(str(person.get("name") or "Skillmatrix").split())
    foto, foto_hinweise = foto_a4(daten)
    hinweise.extend(f"A4: {h}" for h in foto_hinweise)
    bloecke, seiten = a4_seiten_aus_pdf(pdf_a4, daten, labels)
    S, ik = K4["seite"], K4["inhalt"]

    def auf(nr):
        return {b for b, s in bloecke.items() if s == nr}

    schritte, inhalt_von = [], {}
    for nr in range(1, seiten + 1):
        letzte = nr == seiten
        inhalt = rahmen(f"Inhalt — Seite {nr}", "VERTICAL",
                        [a4_hero(person, foto)] if "hero" in auf(nr) else [],
                        abstand=m(ik["sektionsabstand"]),
                        padding=(K4["kopf"]["abstand-inhalt"], 0, 0, 0), breite="FILL",
                        hoehe="FILL" if letzte else "HUG", merken=True)
        inhalt_von[nr] = inhalt["name"]
        kinder = [a4_kopfzeile(person, labels, nr == 1), inhalt]
        if letzte:
            kinder.append(a4_fuss(daten, labels))
        seite = rahmen(f"Skillmatrix A4 — {name} — Seite {nr}", "VERTICAL", kinder,
                       padding=(S["rand-oben"], S["rand-rechts"], S["rand-unten"], S["rand-links"]),
                       breite=S["breite"], hoehe=S["hoehe"], fuellung=f(S["hintergrund"]),
                       clip=True, merken=True)
        schritte.append({"was": f"Seite {nr}: Rahmen mit Kopfzeile"
                                + (", Hero" if "hero" in auf(nr) else "")
                                + ", leerem Inhalt" + (" und Fuss" if letzte else ""),
                         "eltern": "SEITE", "seite": nr, "knoten": seite})

    # Die Bloecke in Dokumentreihenfolge, je Seite in deren Inhalt.
    zert_seiten = sorted({s for b, s in bloecke.items() if b.startswith("zert-")})
    zert_schritte = []
    for nr in (zert_seiten if za4 else []):
        knoten, reihen = a4_zertifikate(za4, labels, auf(nr), nr, nr != zert_seiten[0])
        zert_schritte.append({"was": f"Zertifikate auf Seite {nr}: Ueberschrift, Karte, leere Kacheln",
                              "eltern": inhalt_von[nr], "seite": nr, "knoten": knoten})
        zert_schritte += [{"was": f"Kachelreihe {r['name'].split()[-1]}",
                           "eltern": f"Kacheln — Seite {nr}", "seite": nr, "knoten": r}
                          for r in reihen]
    kompetenz_schritte = []
    kat_seiten = {}
    for nr, k in enumerate(daten.get("kompetenzen") or [], start=1):
        kat_seiten.setdefault(bloecke.get(f"kategorie-{nr}", 1), []).append((nr, k))
    for seite_nr in sorted(kat_seiten):
        erste = "kompetenzen-titel" in auf(seite_nr)
        liste = f"Kategorien — Seite {seite_nr}"
        kinder = [rahmen(liste, "VERTICAL", [], abstand=m(K4["kompetenzen"]["kategorie-abstand"]),
                         breite="FILL", merken=True)]
        if erste:
            knoten = rahmen("Kernkompetenzen", "VERTICAL",
                            [a4_ueberschrift("icon-kernkompetenzen.svg", labels["kernkompetenzen"])]
                            + kinder, abstand=m(K4["sektionstitel"]["unten"]), breite="FILL")
        else:
            knoten = kinder[0]
            knoten["name"] = liste
        kompetenz_schritte.append({
            "was": ("Kernkompetenzen: Ueberschrift und leere Kategorienliste" if erste
                    else "Kernkompetenzen (Fortsetzung): leere Kategorienliste") + f", Seite {seite_nr}",
            "eltern": inhalt_von[seite_nr], "seite": seite_nr, "knoten": knoten})
        for nr, k in kat_seiten[seite_nr]:
            kompetenz_schritte.append({"was": f"Kategorie {k.get('kategorie')}", "eltern": liste,
                                       "seite": seite_nr, "knoten": a4_kategorie(k)})
    if daten.get("tools"):
        nr = bloecke.get("tools", seiten)
        kompetenz_schritte.append({"was": "Tools", "eltern": inhalt_von[nr], "seite": nr,
                                   "knoten": a4_tools(daten["tools"], labels)})
    if daten.get("zertifikate_position") == "ende":
        schritte += kompetenz_schritte + zert_schritte
    else:
        schritte += zert_schritte + kompetenz_schritte

    schriften = {}
    for familie, schnitte in DS4["figma_schnitte"].items():
        if not familie.startswith("_"):
            schriften[familie] = sorted(set(schnitte.values()))
    return {
        "fassung": "a4", "pdf": str(pdf_a4), "datei": dateiname(daten, "a4"),
        "rahmen": {"name": f"Skillmatrix A4 — {name} — Seite n", "breite": S["breite"],
                   "hoehe": S["hoehe"], "seiten": seiten},
        "anordnung": {"neben": f"Skillmatrix — {name}", "abstand": 100,
                      "_regel": "Seite 1 rechts neben dem langen Frame, 100 Abstand, oben buendig; "
                                "jede weitere Seite 100 rechts daneben (references/figma.md)."},
        "sprache": daten.get("sprache", "de"),
        "schriften": schriften,
        "schritte": [{"nr": i + 1, **s} for i, s in enumerate(schritte)],
        "uploads": [b for s in schritte for b in _bilder(s["knoten"])],
    }


def planhoehe_a4(plan):
    """Rechnet je Seite die Hoehe von Kopfzeile und Inhalt nach (Texte
    geschaetzt) und meldet, wo sie den Satzspiegel ueberschreitet - im Frame
    wuerde dort abgeschnitten."""
    import copy
    schaetzer = zertifikate.Schaetzer(DS4, sicherheit=1.0)
    S = K4["seite"]
    rahmen_je_seite, gemerkt = {}, {}

    def merken(k):
        if k.get("merken") and k.get("typ") == "rahmen":
            gemerkt[k["name"]] = k
        for kind in k.get("kinder", []):
            merken(kind)
    for schritt in plan["schritte"]:
        knoten = copy.deepcopy(schritt["knoten"])
        if schritt["eltern"] == "SEITE":
            rahmen_je_seite[schritt["seite"]] = knoten
        else:
            gemerkt[schritt["eltern"]]["kinder"].append(knoten)
        merken(knoten)
    hoehen = {}
    for nr, seite in rahmen_je_seite.items():
        innen = S["breite"] - S["rand-links"] - S["rand-rechts"]
        kopf, inhalt = seite["kinder"][0], dict(seite["kinder"][1], hoehe="HUG")
        belegt = masse(kopf, innen, schaetzer)[1] + masse(inhalt, innen, schaetzer)[1]
        frei = S["hoehe"] - S["rand-oben"] - S["rand-unten"]
        if len(seite["kinder"]) > 2:
            frei -= masse(seite["kinder"][2], innen, schaetzer)[1]
        hoehen[nr] = round(belegt, 1)
        if belegt > frei + 1:
            hinweise.append(f"A4: Seite {nr} nachgerechnet {belegt:.0f}pt hoch, Platz ist {frei:.0f}pt "
                            "— im Frame koennte unten etwas abgeschnitten werden. Nach dem Bau "
                            "ansehen.")
    plan["rahmen"]["inhalt_geschaetzt"] = hoehen


# --- Hoehen nachrechnen -----------------------------------------------------

def _zeile_pt(typo):
    z = typo["zeilenhoehe"]
    return z["wert"] if z["einheit"] == "PIXELS" else z["wert"] / 100 * typo["groesse"]


def _konturen(k):
    """[oben, rechts, unten, links] der Kontur, soweit sie im Layout zaehlt —
    wie strokesIncludedInLayout im Baukasten (nur Auto-Layout-Rahmen)."""
    ko = k.get("kontur")
    if not ko or not ko.get("im_layout", True) or k.get("layout") not in ("VERTICAL", "HORIZONTAL"):
        return [0, 0, 0, 0]
    return list(ko["seiten"]) if ko.get("seiten") else [ko["breite"]] * 4


def masse(k, verfuegbar, schaetzer):
    """(breite, hoehe) eines Planknotens nach den Auto-Layout-Regeln, die der
    Baukasten setzt. verfuegbar: Breite fuer ein FILL-Kind. Texte werden mit
    zertifikate.Schaetzer umbrochen — eine Gegenrechnung, Figma rechnet beim
    Bauen selbst. Breiten von HUG-Texten bleiben 0 (fuer Hoehen unerheblich)."""
    typ = k["typ"]
    if typ in ("bild", "rechteck", "ellipse", "svg"):
        return k["breite"], k["hoehe"]
    if typ == "text":
        zeile = _zeile_pt(k["typo"])
        b = k["breite"] if isinstance(k["breite"], (int, float)) else (
            verfuegbar if k["breite"] == "FILL" else None)
        if b is None:
            return 0, (k["text"].count("\n") + 1) * zeile
        n = sum(max(schaetzer.zeilen([(z, k["verwendung"])], b), 1)
                for z in k["text"].split("\n"))
        if k.get("max_zeilen"):
            n = min(n, k["max_zeilen"])
        return b, n * zeile
    pad = k.get("padding") or [0, 0, 0, 0]
    ko = _konturen(k)
    oben, rechts, unten, links = (pad[i] + ko[i] for i in range(4))
    breite = k["breite"] if isinstance(k["breite"], (int, float)) else (
        verfuegbar if k["breite"] == "FILL" else None)
    layout = k.get("layout")
    kinder = [c for c in k.get("kinder", []) if not c.get("absolut")]
    innen = breite - links - rechts if breite is not None else None
    abstand = k.get("abstand", 0) * max(len(kinder) - 1, 0)
    if layout == "VERTICAL":
        groessen = [masse(c, innen, schaetzer) for c in kinder]
        h, b = sum(g[1] for g in groessen) + abstand, max([g[0] for g in groessen] or [0])
    elif layout == "HORIZONTAL" and k.get("umbruch"):
        # Umbrechende Reihe (Tags): Zeilen wie das PDF umbricht - lange
        # Fassung mit Rand je Tag (zertifikate.tag_reihen), A4 mit gap.
        breiten = [_hug_breite(c, schaetzer) for c in kinder]
        if k.get("umbruch_gap"):
            reihen = _reihen_gap(breiten, innen, k.get("abstand", 0))
        else:
            reihen = zertifikate.tag_reihen(breiten, innen, k.get("abstand", 0))
        zeile = max([masse(c, None, schaetzer)[1] for c in kinder] or [0])
        h, b = reihen * zeile + max(reihen - 1, 0) * k["umbruch"], innen or 0
    elif layout == "HORIZONTAL":
        fest = [None if c.get("breite") == "FILL" else masse(c, None, schaetzer) for c in kinder]
        fuellen = fest.count(None)
        rest = None
        if fuellen and innen is not None:
            rest = (innen - sum(g[0] for g in fest if g) - abstand) / fuellen
        groessen = [g or masse(c, rest, schaetzer) for g, c in zip(fest, kinder)]
        h, b = max([g[1] for g in groessen] or [0]), sum(g[0] or 0 for g in groessen) + abstand
    elif layout == "GRID":
        r = k["raster"]
        zelle = (innen - (r["spalten"] - 1) * r["spaltenabstand"]) / r["spalten"]
        groessen = [masse(c, zelle, schaetzer) for c in kinder]
        reihen = [max(g[1] for g in groessen[i:i + r["spalten"]])
                  for i in range(0, len(groessen), r["spalten"])]
        h, b = sum(reihen) + r["zeilenabstand"] * max(len(reihen) - 1, 0), innen or 0
    else:
        h, b = 0, 0
    hoehe = k["hoehe"] if isinstance(k["hoehe"], (int, float)) else h + oben + unten
    if k.get("min_hoehe"):
        hoehe = max(hoehe, k["min_hoehe"])
    return (breite if breite is not None else b + links + rechts), hoehe


def _reihen_gap(breiten, innen, abstand):
    """Zeilen einer umbrechenden Reihe mit Abstand nur zwischen den Elementen
    (CSS gap, Figma itemSpacing) - so bricht die A4-Fassung um."""
    reihen, x = (1 if breiten else 0), 0.0
    for b in breiten:
        if x and x + abstand + b > innen:
            reihen, x = reihen + 1, b
        else:
            x += (abstand if x else 0) + b
    return reihen


def _hug_breite(k, schaetzer):
    """Breite eines Knotens, der seinen Inhalt huggt (Tag): Texte geschaetzt."""
    if k["typ"] == "text":
        return schaetzer.breite(k["text"], k["verwendung"])
    if isinstance(k.get("breite"), (int, float)):
        return k["breite"]
    pad, ko = k.get("padding") or [0, 0, 0, 0], _konturen(k)
    kinder = [_hug_breite(c, schaetzer) for c in k.get("kinder", [])]
    if k.get("layout") == "HORIZONTAL":
        innen = sum(kinder) + k.get("abstand", 0) * max(len(kinder) - 1, 0)
    else:
        innen = max(kinder or [0])
    return innen + pad[1] + pad[3] + ko[1] + ko[3]


def gesamtbaum(plan):
    """Alle Bauschritte zu einem Baum zusammengesetzt, wie er in Figma steht."""
    import copy
    wurzel = copy.deepcopy(plan["schritte"][0]["knoten"])
    gemerkt = {}

    def merken(k):
        if k.get("merken") and k.get("typ") == "rahmen":
            gemerkt[k["name"]] = k
        for kind in k.get("kinder", []):
            merken(kind)
    merken(wurzel)
    for schritt in plan["schritte"][1:]:
        knoten = copy.deepcopy(schritt["knoten"])
        gemerkt[schritt["eltern"]]["kinder"].append(knoten)
        merken(knoten)
    return wurzel


def planhoehe(plan):
    """Traegt die nachgerechneten Hoehen in den Plan ein: Rahmen gesamt und
    Zertifikatssektion. Der Rahmen wird knapp geschaetzt - er wird gegen das
    fertige PDF gehalten -, die Zertifikatssektion so grosszuegig wie in
    zertifikate.py, gegen deren Planung sie gehalten wird."""
    schaetzer = zertifikate.Schaetzer(DS)
    plan["rahmen"]["hoehe_geschaetzt"] = round(
        masse(gesamtbaum(plan), KOMP["seite"]["breite"],
              zertifikate.Schaetzer(DS, sicherheit=1.0))[1], 1)
    for schritt in plan["schritte"]:
        if schritt["was"] == "Zertifikate":
            hoehe = round(masse(schritt["knoten"], KOMP["seite"]["inhalt"], schaetzer)[1], 2)
            plan["zertifikate"]["hoehe_plan"] = hoehe
            if hoehe > plan["zertifikate"]["grenze"]:
                hinweise.append(f"Zertifikatssektion im Plan nachgerechnet {hoehe:g}pt — ueber "
                                f"der Grenze von {plan['zertifikate']['grenze']}pt.")
            if abs(hoehe - plan["zertifikate"]["hoehe_geplant"]) > 1:
                hinweise.append(f"Zertifikatssektion: Plan {hoehe:g}pt, geplant "
                                f"{plan['zertifikate']['hoehe_geplant']:g}pt — Bauplan und "
                                "zertifikate.py rechnen verschieden, bitte melden.")
    soll = plan["rahmen"].get("hoehe_pdf")
    if soll and abs(plan["rahmen"]["hoehe_geschaetzt"] - soll) > 20:
        hinweise.append(f"Rahmenhoehe nachgerechnet {plan['rahmen']['hoehe_geschaetzt']:g}pt, "
                        f"PDF {soll:g}pt — mehr als 20pt Unterschied.")


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


def _arg(args, name):
    """Wert einer Option (--pdf <pfad>) und die Argumente ohne sie."""
    if name not in args:
        return None, args
    i = args.index(name)
    if i + 1 >= len(args):
        raise SystemExit(f"{name} braucht einen Pfad")
    return args[i + 1], args[:i] + args[i + 2:]


# --- Bibliotheksweg ---------------------------------------------------------

def bibliothek_plaene(daten, pdf_a4=None):
    """Die Befuellungsplaene beider Fassungen fuer den Bibliotheksweg
    (figma_bibliothek.py) - dieselbe Ordnung, dieselben Kacheln und dieselbe
    Seitenaufteilung wie PDF und rohe Plaene."""
    labels = beschriftung(daten)
    daten, _ = kompetenzen_ordnen(daten)              # gemeldet schon im rohen Plan
    zplan, _ = zertifikate.planen(daten, DS, labels)
    kontakt = dict(KONTAKT_VORGABE)
    kontakt.update(daten.get("kontakt") or {})
    eigene = []
    lang = figma_bibliothek.plan_lang(daten, labels, zplan, kontakt, eigene)
    a4 = None
    if pdf_a4 and Path(pdf_a4).exists():
        info = seiten_lesen(pdf_a4)
        if info:
            foto, _ = foto_a4(daten)
            a4 = figma_bibliothek.plan_a4(daten, labels, zert_a4(zplan, DS4), kontakt, foto,
                                          info["bloecke"], info["seiten"], eigene)
    r = KOMP["rumpf"]
    rumpf = {"padding": [m(r["padding-oben"]), m(r["padding-x"]), m(r["padding-unten"]), m(r["padding-x"])],
             "abstand": m(r["sektionsabstand"]), "fuellung": f(r["hintergrund"]),
             "linie": {"breite": r["linie-oben"]["breite"], "farbe": f(r["linie-oben"]["farbe"])}}
    dateien = figma_bibliothek.bilder(lang) + [d for d in (figma_bibliothek.bilder(a4) if a4 else [])
                                               if d not in figma_bibliothek.bilder(lang)]
    hinweise.extend(eigene)
    return {"lang": lang, "a4": a4, "rumpf": rumpf, "uploads": dateien, "hinweise": eigene}


def skript_ausgeben(args):
    """--skript vorflug|lang|a4 <arbeit> [--seite ID] [--bilder bilder.json]"""
    seite, args = _arg(args, "--seite")
    bilder_datei, args = _arg(args, "--bilder")
    if len(args) != 3:
        raise SystemExit(__doc__)
    was, ordner = args[1], Path(args[2])
    if was == "vorflug":
        print(figma_bibliothek.vorflug_skript(seite))
        return
    if not seite:
        raise SystemExit("--seite <ID der Zielseite> fehlt (aus dem Link, 1-147 -> 1:147).")
    bib = json.loads((ordner / "figma_bibliothek.json").read_text(encoding="utf-8"))
    plan = bib.get(was)
    if not plan:
        raise SystemExit(f"Kein Plan „{was}“ in {ordner / 'figma_bibliothek.json'}"
                         + (" — ohne A4-PDF entsteht keiner." if was == "a4" else "."))
    if plan.get("zu_viel"):
        raise SystemExit(f"Fassung {was}: mehr Eintraege, als die Komponenten tragen (Hinweise beim "
                         "Planen) — diese Fassung roh bauen (figma_plan.json bzw. figma_plan_a4.json).")
    hashes = json.loads(Path(bilder_datei).read_text(encoding="utf-8")) if bilder_datei else {}
    fehlen = [d for d in figma_bibliothek.bilder(plan) if d not in hashes]
    if fehlen:
        print(f"// ACHTUNG: {len(fehlen)} Bild(er) ohne Upload - die Ebenen werden ausgeblendet: "
              + ", ".join(Path(d).name for d in fehlen), file=sys.stderr)
    # Temporaere Upload-Rahmen raeumt der letzte Bauaufruf weg; lang nur die,
    # die A4 nicht mehr braucht.
    a4_dateien = figma_bibliothek.bilder(bib["a4"]) if bib.get("a4") else []
    entfernen = (bib["uploads"] if was == "a4" or not bib.get("a4")
                 else [d for d in bib["uploads"] if d not in a4_dateien])
    code = figma_bibliothek.skript(plan, seite, hashes, entfernen, bib["uploads"],
                                   bib["rumpf"] if was == "lang" else None)
    if len(code) > 50000:
        raise SystemExit(f"Skript {len(code)} Zeichen — ueber der Grenze von use_figma (50000).")
    print(code)


def main():
    args = sys.argv[1:]
    if args[:1] == ["--skript"]:
        skript_ausgeben(args)
        return
    if args[:1] == ["--schritt"] and len(args) == 3:
        plan = json.loads(Path(args[2]).read_text(encoding="utf-8"))
        schritt = next((s for s in plan["schritte"] if str(s["nr"]) == args[1]), None)
        if not schritt:
            raise SystemExit(f"Keinen Schritt {args[1]} im Plan.")
        print(json.dumps(schritt["knoten"], ensure_ascii=False, separators=(",", ":")))
        return
    pdf, args = _arg(args, "--pdf")
    pdf_a4, args = _arg(args, "--pdf-a4")
    if len(args) < 2:
        raise SystemExit(__doc__)

    daten = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    ziel = Path(args[1])
    if ziel.suffix.lower() == ".json":
        ziel = ziel.parent
    ziel.mkdir(parents=True, exist_ok=True)

    plan = plan_bauen(daten, pdf)
    planhoehe(plan)
    datei = ziel / "figma_plan.json"
    datei.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{datei} geschrieben — {len(plan['schritte'])} Bauschritte, "
          f"{len(plan['uploads'])} Bilder zum Hochladen")
    for s in plan["schritte"]:
        groesse = len(json.dumps(s["knoten"], ensure_ascii=False, separators=(",", ":")))
        print(f"  {s['nr']:2}. {s['was']}  (in: {s['eltern']}, {groesse / 1000:.0f} KB)")
    if plan.get("zertifikate"):
        z = plan["zertifikate"]
        print(f"Zertifikate: {z['kacheln']} Kacheln, Sektion {z['hoehe_plan']:g}pt "
              f"(geplant {z['hoehe_geplant']:g}, Grenze {z['grenze']})")
    print(f"Rahmenhoehe nachgerechnet (Texte geschaetzt): {plan['rahmen']['hoehe_geschaetzt']:g}pt")
    if plan["rahmen"].get("hoehe_pdf"):
        print(f"Sollhoehe aus dem PDF: {plan['rahmen']['hoehe_pdf']}pt")

    # A4: die Seitenaufteilung kommt aus dem A4-PDF. Ohne --pdf-a4 liegt es
    # neben dem langen PDF.
    if not pdf_a4 and pdf:
        kandidat = Path(pdf).with_name(dateiname(kompetenzen_ordnen(daten)[0], "a4"))
        pdf_a4 = str(kandidat) if kandidat.exists() else None
    plan4 = None
    if pdf_a4 and Path(pdf_a4).exists():
        try:
            plan4 = plan_bauen_a4(daten, pdf_a4)
        except ImportError:
            hinweise.append("A4-Plan nicht geschrieben: pypdf fehlt — ohne es laesst sich die "
                            "Seitenaufteilung nicht aus dem PDF lesen (pip3 install pypdf).")
    if plan4:
        planhoehe_a4(plan4)
        datei4 = ziel / "figma_plan_a4.json"
        datei4.write_text(json.dumps(plan4, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n{datei4} geschrieben — {plan4['rahmen']['seiten']} Seiten, "
              f"{len(plan4['schritte'])} Bauschritte, {len(plan4['uploads'])} Bilder zum Hochladen")
        for s in plan4["schritte"]:
            groesse = len(json.dumps(s["knoten"], ensure_ascii=False, separators=(",", ":")))
            print(f"  {s['nr']:2}. {s['was']}  (in: {s['eltern']}, {groesse / 1000:.0f} KB)")
        print("Inhalt je Seite nachgerechnet (Texte geschaetzt): " + ", ".join(
            f"Seite {n} {h:g}pt" for n, h in plan4["rahmen"]["inhalt_geschaetzt"].items()))
    elif not (pdf_a4 and Path(pdf_a4).exists()):
        hinweise.append("A4-Plan nicht geschrieben: --pdf-a4 \"<… - Skillmatrix A4.pdf>\" angeben "
                        "(die Seitenaufteilung kommt aus dem A4-PDF)."
                        + (f" Nicht gefunden: {pdf_a4}" if pdf_a4 else ""))

    bib = bibliothek_plaene(daten, pdf_a4 if plan4 else None)
    datei_b = ziel / "figma_bibliothek.json"
    datei_b.write_text(json.dumps(bib, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{datei_b} geschrieben — Bibliotheksweg: lang"
          + (f" und A4 ({len(bib['a4']['instanzen'])} Seiten)" if bib["a4"] else "")
          + f", {len(bib['uploads'])} Bilder zum Hochladen"
          + "".join(f"; {f} sprengt die Komponenten — roh bauen" for f in ("lang", "a4")
                    if bib.get(f) and bib[f]["zu_viel"]))
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
