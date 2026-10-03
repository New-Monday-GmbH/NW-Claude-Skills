#!/usr/bin/env python3
"""Baut aus cv.json und dem fertigen PDF den Bauplan fuer den Figma-Frame.

    python3 scripts/figma_plan.py cv.json "ausgabe/New-Monday - ... - CV.pdf" arbeit/

Schreibt arbeit/figma_plan.json: je PDF-Seite ein Frame, darin die Bloecke in
Lesereihenfolge — alle Werte fertig ausgerechnet (Schriftfamilie, Figma-Schnitt,
Groesse, Zeilenhoehe, Laufweite, Farbe, Einzug, Logomasse in pt). Das
use_figma-Skript setzt nur noch, was hier steht; Layoutwerte werden dort nicht
mehr gerechnet. Die Werte kommen aus assets/tokens.json — derselben Quelle wie
cv.css —, die Logomathematik aus render_cv.py. Nichts davon wird hier ein
zweites Mal festgelegt, deshalb koennen Frame und PDF nicht auseinanderlaufen.

Die Seitenaufteilung wird nicht geschaetzt, sondern aus dem gerenderten PDF
gelesen: jeder Block bekommt eine unterscheidbare Textmarke, gesucht wird sie im
Text der Seiten. Dieselbe Technik wie deckblatt_seiten() in render_cv.py. Ohne
pypdf geht das nicht — dann bricht das Skript ab, statt zu raten.

Optionen:
  --stufen <datei>                 stufen.json aus `render_cv.py --stufen-json`
  --deckblatt normal|kompakt|eng   Stufe von Hand setzen (schlaegt --stufen)
  --stationen normal|kompakt|eng   dito

Zertifikate stehen immer als Tags, nur mit dem Titel (Vorgabe vom 03.10.2026);
ein --zertifikate aus aelteren Aufrufen und "zertifikate" in einer aelteren
stufen.json werden ignoriert.

Logos werden nie verzerrt: Jeder Logoeintrag traegt das Seitenverhaeltnis
seiner Datei (verhaeltnis), und das Skript prueft, dass Breite und Hoehe im
Plan dazu passen (Toleranz logo_toleranz, 1 %). Dieselbe Toleranz prueft der
Figma-Schritt am fertigen Knoten nach, siehe references/figma.md.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokens  # noqa: E402  — erst nach sys.path.insert moeglich
from render_cv import (  # noqa: E402
    BESCHRIFTUNG, KONTAKT_VORGABE, VERWEISTEXT, bildung_aufbereiten, dateiname,
    logo_groessen, logo_masse, logoliste, seitenverhaeltnis, skillset_gruppen,
    zertifikate_aufbereiten,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
T = tokens.laden()

# Wie weit Breite/Hoehe eines Logos vom Seitenverhaeltnis seiner Datei
# abweichen duerfen, im Plan wie am fertigen Figma-Knoten: 1 %. Mehr ist keine
# Rundung mehr, sondern ein gestauchtes oder gestrecktes Logo.
LOGO_TOLERANZ = 0.01


def norm(text):
    """Whitespace vereinheitlichen — im PDF-Text traegt ein umbrochener
    Eintrag ein \\n, das sonst jeden Vergleich scheitern laesst."""
    return " ".join(str(text or "").split())


def typo(name):
    """Ein fertiger Textstil aus tokens.json, so wie Figma ihn braucht.

    zeile ist die Zeilenhoehe in pt und wird in Figma als PIXELS gesetzt, nicht
    als Prozent: Figma rundet Prozentwerte auf ganze Punkt, der feste Wert ist
    genau das, was dabei herauskommt — und genau das, was das PDF setzt.
    """
    s = tokens.stil(name)
    stil = {"familie": s["schrift"], "schnitt": s["figma_schnitt"],
            "groesse": s["groesse"], "zeile": s["zeile"],
            "laufweite": s["laufweite"], "farbe": s["farbe_hex"]}
    if s.get("versalien"):
        stil["versalien"] = True
    return stil


def logo_eintrag(datei, groesse):
    """Absoluter Pfad, nicht relativ: Die Logos liegen im Skill-Ordner, das Foto
    im Arbeitsverzeichnis des Nutzers. Relativ liesse sich im Plan nicht mehr
    unterscheiden, worauf sich welcher Pfad bezieht.

    verhaeltnis ist Breite/Hoehe der Datei selbst. Der Figma-Schritt prueft
    daran den fertigen Knoten: ein Logo, das dort anders proportioniert ist als
    seine Datei, ist verzerrt.
    """
    breite, hoehe = logo_masse(datei, groesse)
    return {"datei": str(ASSETS / "logos" / datei),
            "typ": "svg" if datei.lower().endswith(".svg") else "raster",
            "breite": breite, "hoehe": hoehe,
            "verhaeltnis": round(seitenverhaeltnis(datei), 4)}


def nm_logo(breite, hoehe):
    return {"datei": str(ASSETS / "logos" / "nm-logo.svg"), "typ": "svg",
            "breite": breite, "hoehe": hoehe,
            "verhaeltnis": round(seitenverhaeltnis("nm-logo.svg"), 4)}


def block(art, abstand_oben=0, marke=None, einzug=0, **rest):
    b = {"art": art, "abstand_oben": abstand_oben, "einzug": einzug}
    if marke:
        b["marke"] = norm(marke)
    b.update(rest)
    return b


# --- Bloecke ----------------------------------------------------------------

def bloecke_bauen(daten, deckblatt, stationen):
    """Das ganze Dokument als flache Liste in Lesereihenfolge.

    Flach, nicht verschachtelt: Ein Projekt kann im PDF auf einer anderen Seite
    stehen als seine Station, eine Bulletliste sogar auf beiden. Verschachtelt
    liesse sich das nicht auf Frames verteilen.
    """
    d = T["verdichtung"]["deckblatt"][deckblatt]
    s = T["verdichtung"]["stationen"][stationen]
    a, r, ab, farben = T["abstand"], T["raster"], T["abgeleitet"], T["farben"]
    sprache = daten.get("sprache", "de")
    labels = BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"])
    person = daten.get("person") or {}
    bloecke = []

    # Kopfzeile — nur die Wortmarke.
    bloecke.append(block(
        "kopfzeile", anker="erste",
        logo=nm_logo(r["kopflogo_breite"], r["kopflogo_hoehe"])))

    # Profilkopf: Foto links, rechts Name, Rolle, Erfahrung, Verweise.
    zeilen = [dict(text=norm(person.get(f)), **typo("rolle"))
              for f in ("rolle", "erfahrung") if person.get(f)]
    for i, z in enumerate(zeilen):
        z["abstand_oben"] = a["rolle_erfahrung"] if i else 0
    verweistexte = VERWEISTEXT.get(sprache, VERWEISTEXT["de"])
    verweise = []
    for l in person.get("links") or []:
        titel = norm(l.get("titel"))
        verweise.append({
            "text": l.get("text") or verweistexte.get(titel.lower()) or titel,
            "url": l.get("url") or None,
            # Die Linie in der Markenfarbe ist das einzige Signal, dass ein
            # Verweis anklickbar ist. Ein Portfolio, das nur als PDF vorliegt,
            # hat keine Adresse und steht deshalb ohne.
            "unterstrichen": bool(l.get("url")),
        })
    bloecke.append(block(
        "intro", abstand_oben=a["kopf_intro"], anker="erste",
        fotospalte=r["fotospalte"], fotoabstand=r["fotoabstand"],
        infospalte=ab["inhaltsspalte"],
        # Die anonyme Fassung setzt statt des Fotos die Silhouette, und die ist
        # ein SVG. In Figma fuehren die beiden zu verschiedenen Wegen — Markup
        # im Code gegen Upload aufs Rechteck —, also steht der Typ hier im Plan,
        # genau wie bei den Logos. Entschieden wird er nicht hier.
        foto=({"datei": str(Path(person["foto"]).expanduser().resolve()),
               "typ": ("svg" if str(person["foto"]).lower().endswith(".svg")
                       else "raster"),
               "breite": r["foto_breite"], "hoehe": r["foto_hoehe"],
               "oben": r["foto_oben"]}
              if person.get("foto") else None),
        name=dict(text=norm(person.get("name")), abstand_unten=a["name_rolle"],
                  **typo("name")),
        zeilen=zeilen,
        verweise=(dict(abstand_oben=a["erfahrung_verweise"], abstand=a["verweise"],
                       zeilenabstand=a["verweise_zeilen"],
                       linie={"staerke": r["verweislinie"], "farbe": farben["marke"]},
                       eintraege=verweise, **typo("verweis"))
                  if verweise else None)))

    # --- Deckblatt: Bildung und Skillset, beide auf Seite 1 ---
    # Abschluesse ohne Studieninhalte (dieselbe Aufbereitung wie im PDF), die
    # Zertifikate als eigener Block darunter, je Titel ein Tag.
    bildung = bildung_aufbereiten(daten)[0]
    zertifikate = zertifikate_aufbereiten(daten)[0]
    erste_rubrik = True
    if bildung or zertifikate:
        bloecke.append(block("rubrik", abstand_oben=a["intro_inhalt"],
                             marke=labels["bildung"], text=labels["bildung"],
                             **typo("rubrik")))
        erste_rubrik = False
    if bildung:
        eintraege = []
        for b in bildung:
            eintraege.append({
                "abschluss": dict(text=norm(b.get("abschluss")), **typo("abschluss")),
                "zeilen": [dict(text=norm(b[f]), abstand_oben=0, **typo("bildung"))
                           for f in ("institution", "zeitraum") if b.get(f)],
            })
        bloecke.append(block(
            "bildung", abstand_oben=d["rubrik_inhalt"],
            marke=bildung[0].get("abschluss"),
            spaltenbreite=ab["halbe_spalte"], spaltenabstand=r["spaltenabstand"],
            reihenabstand=d["bildung_reihen"], eintraege=eintraege))
    if zertifikate:
        bloecke.append(zertifikatsblock(
            zertifikate, labels["zertifikate"], d,
            d["zert_abstand"] if bildung else d["rubrik_inhalt"]))
    if bildung or zertifikate:
        bloecke.append(block("trennlinie", abstand_oben=d["vor_linie"],
                             farbe=farben["text"], staerke=r["linie"]))

    # Das Skillset gibt es immer, mit den vier festen Gruppen 2 x 2 — dieselbe
    # Aufbereitung wie im PDF (render_cv.skillset_gruppen), nicht die Rohdaten.
    skillset = skillset_gruppen(daten)[0]
    if skillset["links"] or skillset["rechts"]:
        bloecke.append(block(
            "rubrik", abstand_oben=a["intro_inhalt"] if erste_rubrik else d["nach_linie"],
            marke=labels["skillset"], text=labels["skillset"], **typo("rubrik")))

        def gruppen(spalte):
            return [{
                "titel": dict(text=norm(g["titel"]), abstand_unten=d["gruppe_liste"],
                              **typo("gruppe")),
                "eintraege": [norm(e) for e in g["eintraege"]],
            } for g in spalte]

        erste = (skillset["links"] or skillset["rechts"])[0]
        bloecke.append(block(
            "skillset", abstand_oben=d["rubrik_inhalt"], marke=erste["titel"],
            spaltenbreite=ab["halbe_spalte"], spaltenabstand=r["spaltenabstand"],
            gruppenabstand=d["gruppen"],
            liste=dict(einzug=r["listeneinzug"], abstand=0, **typo("liste")),
            spalten=[gruppen(skillset["links"]), gruppen(skillset["rechts"])]))

    # --- Ab hier die Stationen, im PDF auf einer neuen Seite ---
    naechster_abstand = 0
    if person.get("kurzprofil"):
        bloecke.append(block("rubrik", abstand_oben=0, seitenanfang=True,
                             marke=labels["kurzprofil"], text=labels["kurzprofil"],
                             **typo("rubrik")))
        bloecke.append(block("profil", abstand_oben=s["profil_rubrik"],
                             marke=" ".join(norm(person["kurzprofil"]).split()[:8]),
                             text=norm(person["kurzprofil"]), **typo("profil")))
        bloecke.append(block("trennlinie", abstand_oben=s["profil_linie"],
                             farbe=farben["text"], staerke=r["linie"]))
        naechster_abstand = s["profil_stationen"]

    st_groesse, pr_groesse = logo_groessen(daten)
    for nr, station in enumerate(daten.get("stationen") or []):
        if nr:
            naechster_abstand = s["station"]
        # Der Kopf wie in Figma: Titel, Firma, Zeitraum als eigene Zeile. Die
        # Schlagwortzeile steht zusaetzlich darunter (im Skill bewusst behalten).
        bloecke.append(block(
            "station", abstand_oben=naechster_abstand,
            seitenanfang=(nr == 0 and not person.get("kurzprofil")),
            marke=station.get("titel"),
            rail={"breite": r["logospalte"], "oben": r["logo_oben"], "abstand": r["logo_stapel"],
                  "logos": [logo_eintrag(f, st_groesse)
                            for f in logoliste(station.get("logo"))]},
            spaltenabstand=r["logoabstand"], koerperbreite=ab["inhaltsspalte"],
            titel=dict(text=norm(station.get("titel")), **typo("titel")),
            firma=(dict(text=norm(station["firma"]), abstand_oben=a["titel_firma"],
                        **typo("firma")) if station.get("firma") else None),
            zeitraum=(dict(text=norm(station["zeitraum"]), abstand_oben=a["firma_zeitraum"],
                           **typo("zeitraum")) if station.get("zeitraum") else None),
            absaetze=[dict(text=norm(station[f]), abstand_oben=a["zeitraum_text"],
                           **typo("fliesstext"))
                      for f in ("zusammenfassung", "beschreibung") if station.get(f)]))
        if station.get("aufgaben"):
            bloecke.append(aufgabenblock(station["aufgaben"], s["kopf_aufgaben"]))
        for projekt in station.get("projekte") or []:
            # Die Marke ist Kunde, Zeitraum und Textanfang in der Reihenfolge, in
            # der sie im PDF stehen. Der Kunde allein reicht nicht: Steht
            # "Deutsche Bank" dreimal im Dokument, fand die Suche immer das
            # erste Vorkommen, und das Projekt landete auf der falschen Seite.
            marke = " ".join(filter(None, [
                norm(projekt.get("kunde")), norm(projekt.get("zeitraum")),
                " ".join(norm(projekt.get("beschreibung")).split()[:3])]))
            bloecke.append(block(
                "projekt", abstand_oben=s["projekt"], einzug=ab["einzug"],
                marke=marke, breite=ab["inhaltsspalte"],
                # Nebeneinander, auf der Mitte zueinander, linksbuendig an der
                # Kundenzeile; bricht um, wenn die Reihe breiter als die Spalte
                # wird — wie .project__logos in cv.css. Im Frame also eine
                # HORIZONTAL-Autolayout-Reihe mit Umbruch, nicht VERTICAL.
                logos=dict(abstand_unten=a["projektlogo_kunde"], richtung="nebeneinander",
                           abstand=r["projektlogo_reihe"], zeilenabstand=r["projektlogo_reihe"],
                           ausrichtung="mitte", breite=ab["inhaltsspalte"],
                           eintraege=[logo_eintrag(f, pr_groesse)
                                      for f in logoliste(projekt.get("logo"))]),
                kunde=dict(text=norm(projekt.get("kunde")), **typo("kunde")),
                zeitraum=(dict(text=norm(projekt["zeitraum"]), abstand_oben=a["kunde_zeitraum"],
                               **typo("zeitraum")) if projekt.get("zeitraum") else None),
                absaetze=[dict(text=norm(projekt["beschreibung"]), abstand_oben=a["projekt_text"],
                               **typo("fliesstext"))]
                if projekt.get("beschreibung") else []))
            if projekt.get("aufgaben"):
                bloecke.append(aufgabenblock(projekt["aufgaben"], a["projekt_text"]))

    # Footer — immer am unteren Rand der letzten Seite, breiter als der
    # Satzspiegel: von der linken bis zur gespiegelten rechten Randlinie.
    kontakt = daten.get("kontakt") or KONTAKT_VORGABE

    def wert(*zeilen):
        """Ein Textblock im Footer; jede Zeile mit ihrem Stil."""
        return [{"text": norm(text), "stil": stil} for text, stil in zeilen if text]

    bloecke.append(block(
        "footer", anker="letzte", breite=r["fuss_breite"],
        trennlinie={"farbe": farben["text"], "staerke": r["linie"]},
        abstand_zur_reihe=a["fuss_linie_reihe"],
        logo=nm_logo(r["fusslogo_breite"], r["fusslogo_hoehe"]),
        spaltenblock={"breite": r["fuss_block"], "spaltenbreite": ab["fuss_spalte"],
                      "spaltenabstand": r["fuss_spaltenabstand"]},
        label=typo("fuss_label"), wert_abstand=a["fuss_label_wert"],
        werte_abstand=a["fuss_werte"],
        stile={"fuss_name": typo("fuss_name"), "fuss_wert": typo("fuss_wert")},
        spalten=[
            {"label": labels["ansprechpartner"],
             "werte": [wert((kontakt.get("name"), "fuss_name"),
                            (kontakt.get("rolle"), "fuss_wert"))]},
            {"label": labels["kontakt"],
             "werte": [wert((kontakt.get("mail"), "fuss_wert")),
                       wert((kontakt.get("telefon"), "fuss_wert"))]},
            {"label": labels["adresse"],
             "werte": [wert((kontakt.get("firma"), "fuss_wert"),
                            (kontakt.get("strasse"), "fuss_wert"),
                            (kontakt.get("ort"), "fuss_wert"))]},
        ]))
    return bloecke


def zertifikatsblock(titel_liste, titel, d, abstand_oben):
    """Der Zertifikatsblock unter den Abschluessen: Titel, darunter die Tags.

    Wie .zert__tags in cv.css: eine Reihe ueber die volle Breite, die
    umbricht — im Frame ein HORIZONTAL-Autolayout mit WRAP, abstand als
    itemSpacing, zeilenabstand als counterAxisSpacing. Je Eintrag ein Tag mit
    Innenabstand, Rand und Radius aus tag; der Text bricht nicht um, ausser er
    ist breiter als die ganze Reihe (siehe references/figma.md).
    """
    r, ab, farben = T["raster"], T["abgeleitet"], T["farben"]
    return block(
        "zertifikate", abstand_oben=abstand_oben, marke=titel_liste[0],
        titel=dict(text=titel, abstand_unten=d["gruppe_liste"], **typo("gruppe")),
        breite=ab["inhaltsbreite"], abstand=r["zert_tag_abstand"],
        zeilenabstand=r["zert_tag_reihen"],
        tag=dict(innen_x=r["zert_tag_innen_x"], innen_y=r["zert_tag_innen_y"],
                 radius=r["zert_tag_radius"],
                 rahmen={"staerke": r["zert_tag_linie"], "farbe": farben["rahmen"]},
                 **typo("zert_tag")),
        # Die Titel wie aus render_cv.py, nicht noch einmal durch norm():
        # das naehme ein geschuetztes Leerzeichen (U+00A0) wieder heraus.
        eintraege=list(titel_liste))


def aufgabenblock(aufgaben, abstand_oben):
    """Bulletliste einer Station oder eines Projekts.

    Eigener Block, nicht Teil der Station: Im PDF darf eine Liste ueber den
    Seitenumbruch laufen, und dann steht ein Teil davon auf dem naechsten Frame.
    Geteilt wird spaeter in bulletlisten_teilen(). abstand ist der
    Listenabstand zwischen den Punkten — 0, wie in Figma.
    """
    return block("aufgaben", abstand_oben=abstand_oben, einzug=T["abgeleitet"]["einzug"],
                 marke=aufgaben[0], breite=T["abgeleitet"]["inhaltsspalte"],
                 einzug_liste=T["raster"]["listeneinzug"], abstand=0,
                 eintraege=[norm(a) for a in aufgaben], **typo("aufgabe"))


# --- Seiten zuordnen --------------------------------------------------------

def seitentexte(pdf):
    """Der Text jeder PDF-Seite, Whitespace vereinheitlicht."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise SystemExit(
            "pypdf fehlt — ohne es laesst sich die Seitenaufteilung nicht aus "
            "dem PDF lesen, und geraten wird sie nicht.\n"
            "  pip install pypdf --break-system-packages")
    return [norm(seite.extract_text() or "") for seite in PdfReader(str(pdf)).pages]


def finde(marke, texte, ab):
    """Erste Seite ab `ab`, deren Text die Marke traegt. None, wenn nirgends.

    Gesucht wird ab der zuletzt belegten Seite: Ein Jobtitel wiederholt sich
    gern als Rolle im Profilkopf, und der steht immer auf Seite 1.
    """
    kurz = marke[:60]
    for nummer in range(ab, len(texte) + 1):
        if kurz and kurz in texte[nummer - 1]:
            return nummer
    return None


def seiten_zuordnen(bloecke, texte):
    """Jedem Block seine Seite. Gibt die Marken zurueck, die nicht auffindbar waren."""
    letzte, ungefunden = 1, []
    for b in bloecke:
        if b.get("anker") == "erste":
            b["seite"] = 1
            continue
        if b.get("anker") == "letzte":
            b["seite"] = len(texte)
            continue
        gefunden = finde(b["marke"], texte, letzte) if b.get("marke") else None
        # Ohne Treffer bleibt der Block, wo der vorige stand — die Reihenfolge
        # im Dokument steht fest, nur die Seitenkante ist dann geraten.
        if gefunden is None:
            if b.get("marke"):
                ungefunden.append(b["marke"])
            b["seite"] = letzte
        else:
            b["seite"] = gefunden
            letzte = gefunden
    return ungefunden


def tagreihen(pdf, bloecke):
    """Traegt an den Zertifikatsblock ein, wie die Tags im PDF auf Reihen
    stehen: reihen = [[Titel, ...], ...]. Gibt die Titel zurueck, die sich
    nicht wiederfinden liessen.

    Gelesen, nicht gerechnet: WeasyPrint schreibt jede Reihe Tags als eine
    Textzeile ("Claude 101Introduction to Agent Skills"). Gesucht wird unter
    der Blockueberschrift, Titel fuer Titel in der Reihenfolge des Plans; ein
    ueberlanger Titel, der in sich umbricht, zaehlt zu der Reihe, in der er
    beginnt. Der Figma-Schritt prueft daran, ob sein Auto-Layout genauso
    umbricht wie das PDF (references/figma.md, "Die Zertifikats-Tags").
    """
    import re
    from pypdf import PdfReader
    block = next((b for b in bloecke if b["art"] == "zertifikate"), None)
    if block is None:
        return []
    zeilen = {}

    def besucher(text, cm, tm, schrift, groesse):
        if text.strip():
            y = round(tm[4] * cm[1] + tm[5] * cm[3] + cm[5], 1)
            zeilen.setdefault(y, []).append((tm[4] * cm[0] + cm[4], text))

    PdfReader(str(pdf)).pages[block["seite"] - 1].extract_text(visitor_text=besucher)
    # Von oben nach unten (im PDF waechst y nach oben), je Zeile von links.
    texte = [norm("".join(t for _, t in sorted(stuecke)))
             for _, stuecke in sorted(zeilen.items(), reverse=True)]
    titel = block["titel"]["text"]
    if titel not in texte:
        return list(block["eintraege"])
    rest = "\n".join(texte[texte.index(titel) + 1:])
    pos, reihen, letzte = 0, [], None
    for eintrag in block["eintraege"]:
        # Zwischen zwei Woertern darf ein Umbruch stehen oder - wo zwei Tags
        # in einer Zeile aneinanderstossen - gar nichts.
        muster = r"\s*".join(re.escape(w) for w in norm(eintrag).split())
        fund = re.compile(muster).search(rest, pos)
        if not fund:
            return [e for e in block["eintraege"]
                    if not any(e in r for r in reihen)]
        reihe = rest.count("\n", 0, fund.start())
        if reihe != letzte:
            reihen.append([])
            letzte = reihe
        reihen[-1].append(eintrag)
        pos = fund.end()
    block["reihen"] = reihen
    return []


def bulletlisten_teilen(bloecke, texte):
    """Laeuft eine Bulletliste im PDF ueber einen Seitenumbruch, wird sie hier
    aufgetrennt — sonst haengt der Rest unten aus dem Frame heraus."""
    ergebnis = []
    for b in bloecke:
        if b["art"] != "aufgaben" or len(b["eintraege"]) < 2:
            ergebnis.append(b)
            continue
        seiten, letzte = [], b["seite"]
        for eintrag in b["eintraege"]:
            treffer = finde(eintrag, texte, letzte) or letzte
            letzte = treffer
            seiten.append(treffer)
        if len(set(seiten)) == 1:
            ergebnis.append(b)
            continue
        teil, aktuell = [], seiten[0]
        for eintrag, seite in zip(b["eintraege"], seiten):
            if seite != aktuell:
                ergebnis.append(dict(b, eintraege=teil, seite=aktuell))
                # Der zweite Teil beginnt oben auf der neuen Seite, also ohne
                # den Abstand, der ihn sonst vom Absatz darueber trennt.
                teil, aktuell, b = [], seite, dict(b, abstand_oben=0, seitenanfang=True)
            teil.append(eintrag)
        ergebnis.append(dict(b, eintraege=teil, seite=aktuell))
    return ergebnis


# --- Aufruf -----------------------------------------------------------------

def stufen_lesen(argv):
    """--stufen liest die Sidecar-Datei, --deckblatt/--stationen schlagen sie.
    --zertifikate gibt es nicht mehr; ein alter Aufruf wird samt Wert
    ignoriert und gemeldet."""
    deckblatt = stationen = "normal"
    rest, hinweise = [], []
    argv = list(argv)
    hand = {}
    while argv:
        a = argv.pop(0)
        if a == "--zertifikate":
            wert = argv.pop(0) if argv else "(ohne Wert)"
            hinweise.append(f"--zertifikate {wert} ignoriert — Zertifikate stehen "
                            "immer als Tags, nur mit dem Titel.")
            continue
        if a in ("--stufen", "--deckblatt", "--stationen"):
            if not argv:
                raise SystemExit(f"{a} braucht einen Wert")
            wert = argv.pop(0)
            if a == "--stufen":
                gelesen = json.loads(Path(wert).read_text(encoding="utf-8"))
                deckblatt = gelesen.get("deckblatt", "normal")
                stationen = gelesen.get("stationen", "normal")
            else:
                hand[a] = wert
            continue
        rest.append(a)
    # Von Hand Gesetztes schlaegt die Sidecar-Datei, egal in welcher Reihenfolge.
    deckblatt = hand.get("--deckblatt", deckblatt)
    stationen = hand.get("--stationen", stationen)
    stufen = T["verdichtung"]["deckblatt"]
    for name, wert in (("--deckblatt", deckblatt), ("--stationen", stationen)):
        if wert not in stufen:
            raise SystemExit(f"{name}: {', '.join(stufen)} — nicht {wert!r}")
    return deckblatt, stationen, rest, hinweise


def main():
    deckblatt, stationen, args, vorab = stufen_lesen(sys.argv[1:])
    if len(args) < 3:
        raise SystemExit(__doc__)
    daten = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    pdf = Path(args[1])
    if not pdf.exists():
        raise SystemExit(f"PDF nicht gefunden: {pdf}")
    ordner = Path(args[2])
    ordner.mkdir(parents=True, exist_ok=True)

    texte = seitentexte(pdf)
    bloecke = bloecke_bauen(daten, deckblatt, stationen)
    ungefunden = seiten_zuordnen(bloecke, texte)
    bloecke = bulletlisten_teilen(bloecke, texte)
    ohne_reihe = tagreihen(pdf, bloecke)

    name = norm((daten.get("person") or {}).get("name")) or "Lebenslauf"
    frames = []
    for nummer in range(1, len(texte) + 1):
        eigene = [{k: v for k, v in b.items() if k not in ("seite", "marke", "anker")}
                  for b in bloecke if b["seite"] == nummer]
        # Oben auf einer Folgeseite hat der erste Block keinen Abstand: Bricht
        # die Seite zwischen zwei Bloecken um, verwirft das PDF den Rand davor.
        # Ohne das stuende eine Station, die eine Seite eroeffnet, im Frame 32pt
        # tiefer als im PDF.
        if nummer > 1 and eigene and eigene[0]["art"] != "footer":
            eigene[0]["abstand_oben"] = 0
        frames.append({"nr": nummer, "name": f"CV — {name} — Seite {nummer}",
                       "bloecke": eigene})

    seite = T["seite"]
    schriften = {}
    for n in T["text"]:
        stil = typo(n)
        schriften.setdefault(stil["familie"], set()).add(stil["schnitt"])
    plan = {
        "pdf": str(pdf), "datei": dateiname(daten),
        "sprache": daten.get("sprache", "de"),
        "person": {"name": name, "rolle": norm((daten.get("person") or {}).get("rolle"))},
        "stufen": {"deckblatt": deckblatt, "stationen": stationen},
        # Seitenverhaeltnis jeder Logodatei, zum Gegenpruefen der fertigen
        # Knoten in Figma (references/figma.md, "Logos werden nie verzerrt").
        "logo_toleranz": LOGO_TOLERANZ,
        "logo_verhaeltnisse": {Path(l["datei"]).name: l["verhaeltnis"]
                               for f in frames for l in logos_im_frame(f)},
        "quelle": T["quelle"],
        "rahmen": {"breite": seite["breite"], "hoehe": seite["hoehe"],
                   "oben": seite["rand_oben"], "rechts": seite["rand_rechts"],
                   "unten": seite["rand_unten"], "links": seite["rand_links"],
                   "inhalt": T["abgeleitet"]["inhaltsbreite"]},
        "farben": {k: v for k, v in T["farben"].items()},
        # Je Familie die Schnitte in Figma-Schreibweise — fuer den Vorflug.
        "schrift": {familie: sorted(schnitte) for familie, schnitte in schriften.items()},
        "frames": frames,
    }
    ziel = ordner / "figma_plan.json"
    ziel.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"{ziel} geschrieben ({len(frames)} Frames, "
          f"{sum(len(f['bloecke']) for f in frames)} Bloecke)")

    hinweise = list(vorab)
    if ungefunden:
        hinweise.append(
            "Im PDF-Text nicht wiedergefunden, die Seitenkante ist dort geraten: "
            + "; ".join(m[:60] for m in ungefunden))
    if ohne_reihe:
        hinweise.append(
            "Zertifikats-Tags im PDF nicht wiedergefunden, ohne reihen im Plan — "
            "im Frame die Reihen mit dem PDF vergleichen: " + "; ".join(ohne_reihe))
    fehlend = sorted({b["datei"] for f in frames for b in logos_im_frame(f)
                      if not Path(b["datei"]).exists()})
    if fehlend:
        hinweise.append("Logodatei fehlt: " + ", ".join(fehlend))
    hinweise += logos_verzerrt(frames)
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


def logos_verzerrt(frames):
    """Hinweise fuer jedes Logo, dessen Masse im Plan nicht zu seiner Datei
    passen. Gerechnet wird beides aus der Datei, also darf das nie anschlagen —
    tut es das doch, ist eine Kappe in logo_masse() oder ein Mass in
    tokens.json falsch, und der Frame wuerde das Logo verzerren."""
    hinweise = []
    for f in frames:
        for l in logos_im_frame(f):
            soll = l.get("verhaeltnis")
            if not soll or not l.get("hoehe"):
                continue
            ist = l["breite"] / l["hoehe"]
            if abs(ist / soll - 1) > LOGO_TOLERANZ:
                hinweise.append(
                    f"Logo verzerrt im Plan: {Path(l['datei']).name} soll "
                    f"{soll:.3f}:1 sein, steht als {l['breite']} x {l['hoehe']} "
                    f"({ist:.3f}:1) — Abweichung {abs(ist / soll - 1):.1%}")
    return hinweise


def logos_im_frame(frame):
    """Alle Logoeintraege eines Frames, egal auf welcher Ebene sie haengen."""
    for b in frame["bloecke"]:
        if isinstance(b.get("logo"), dict):
            yield b["logo"]
        for l in (b.get("rail") or {}).get("logos") or []:
            yield l
        for l in (b.get("logos") or {}).get("eintraege") or []:
            yield l


if __name__ == "__main__":
    main()
