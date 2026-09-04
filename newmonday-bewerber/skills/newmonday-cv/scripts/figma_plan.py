#!/usr/bin/env python3
"""Baut aus cv.json und dem fertigen PDF den Bauplan fuer den Figma-Frame.

    python3 scripts/figma_plan.py cv.json "ausgabe/New-Monday - ... - CV.pdf" arbeit/

Schreibt arbeit/figma_plan.json: je PDF-Seite ein Frame, darin die Bloecke in
Lesereihenfolge — alle Werte fertig ausgerechnet (Schriftgroesse, Figma-Schnitt,
Zeilenhoehe, Laufweite, Farbe, Einzug, Logomasse in pt). Das use_figma-Skript
setzt nur noch, was hier steht; Layoutwerte werden dort nicht mehr gerechnet.
Die Werte stammen aus assets/cv.css und references/layout.md, die Logomathematik
aus render_cv.py — nichts davon wird hier ein zweites Mal erfunden.

Die Seitenaufteilung wird nicht geschaetzt, sondern aus dem gerenderten PDF
gelesen: jeder Block bekommt eine unterscheidbare Textmarke, gesucht wird sie im
Text der Seiten. Dieselbe Technik wie deckblatt_seiten() in render_cv.py. Ohne
pypdf geht das nicht — dann bricht das Skript ab, statt zu raten.

Optionen:
  --stufen <datei>                 stufen.json aus `render_cv.py --stufen-json`
  --deckblatt normal|kompakt|eng   Stufe von Hand setzen (schlaegt --stufen)
  --stationen normal|kompakt|eng   dito
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_cv import (  # noqa: E402  — erst nach sys.path.insert moeglich
    BESCHRIFTUNG, VERWEISTEXT, dateiname, logo_groessen, logo_masse,
    logoliste, seitenverhaeltnis,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# --- Feste Masse, 1:1 aus assets/cv.css -------------------------------------
# A4 in Punkt. In Figma gilt 1px = 1pt, die Zahlen wandern also unveraendert
# in den Frame.
RAHMEN = {"breite": 595, "hoehe": 842,
          "oben": 60, "rechts": 107, "unten": 32, "links": 60, "inhalt": 428}
RASTER = {"logospalte": 88, "abstand": 32, "inhaltsspalte": 308, "einzug": 120,
          "fotospalte": 78, "fotoabstand": 40,
          "spalte_halb": 198.5, "spalte_abstand": 31}
FARBEN = {"black": "#111111", "muted": "#485758", "brand": "#009193"}

# Inter heisst in Figma "Semi Bold" und "Extra Bold" — mit Leerzeichen. Ohne
# Leerzeichen wirft loadFontAsync, und jeder Textknoten des Frames faellt aus.
SCHNITT = {400: "Regular", 600: "Semi Bold", 700: "Bold", 800: "Extra Bold"}

# Die Kopfzeilen-Wortmarke steht im CSS fest, nicht ueber logo_masse().
KOPF_LOGO = {"breite": 133.231, "hoehe": 13.5}
FUSS_LOGO_BREITE = 79

# Verdichtungsstufen. render_cv.py setzt Deckblatt und Stationen enger, bevor
# irgendwer Eintraege streicht; der Frame muss dieselben Abstaende bekommen,
# sonst laeuft er ueber. Werte aus .deckblatt--* und .stationen--* in cv.css.
DECKBLATT = {
    "normal":  {"section": 31, "h2": 31, "h3": 17, "stack": 31, "reihe": 31,
                "divider": 31, "edu_liste": 17},
    "kompakt": {"section": 20, "h2": 20, "h3": 12, "stack": 20, "reihe": 20,
                "divider": 20, "edu_liste": 17},
    "eng":     {"section": 14, "h2": 12, "h3":  8, "stack": 14, "reihe": 14,
                "divider": 14, "edu_liste":  8},
}
STATIONEN = {
    "normal":  {"station": 32, "projekt": 32, "bullet": 10,
                "profil_unten": 31, "profil_divider": 20, "profil_h2": 12},
    "kompakt": {"station": 24, "projekt": 24, "bullet":  8,
                "profil_unten": 24, "profil_divider": 16, "profil_h2": 12},
    "eng":     {"station": 20, "projekt": 20, "bullet":  6,
                "profil_unten": 20, "profil_divider": 14, "profil_h2": 10},
}

# Muss dem Vorgabewert in render_cv.html_bauen() entsprechen — der
# Ansprechpartner im Footer steht als Vorgabe im Skill, nicht in der cv.json.
KONTAKT_VORGABE = {
    "name": "Manuel Klein", "rolle": "CCO",
    "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0) 155 1148 0130",
    "firma": "New Monday GmbH", "strasse": "Stresemannstraße 32",
    "ort": "10963 Berlin",
}


def norm(text):
    """Whitespace vereinheitlichen — im PDF-Text traegt ein umbrochener
    Eintrag ein \\n, das sonst jeden Vergleich scheitern laesst."""
    return " ".join(str(text or "").split())


def typo(groesse, gewicht, zeilenhoehe=None, laufweite=0, farbe="black"):
    """Ein fertiger Textstil. zeilenhoehe None heisst in Figma AUTO — das ist
    das Gegenstueck zu `line-height: normal` im CSS."""
    return {"groesse": groesse, "schnitt": SCHNITT[gewicht],
            "zeilenhoehe": zeilenhoehe, "laufweite": laufweite, "farbe": farbe}


def logo_eintrag(datei, groesse):
    """Absoluter Pfad, nicht relativ: Die Logos liegen im Skill-Ordner, das Foto
    im Arbeitsverzeichnis des Nutzers. Relativ liesse sich im Plan nicht mehr
    unterscheiden, worauf sich welcher Pfad bezieht."""
    breite, hoehe = logo_masse(datei, groesse)
    return {"datei": str(ASSETS / "logos" / datei),
            "typ": "svg" if datei.lower().endswith(".svg") else "raster",
            "breite": breite, "hoehe": hoehe}


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
    d = DECKBLATT[deckblatt]
    s = STATIONEN[stationen]
    sprache = daten.get("sprache", "de")
    labels = BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"])
    person = daten.get("person") or {}
    bloecke = []

    # Kopfzeile — nur die Wortmarke.
    bloecke.append(block(
        "kopfzeile", anker="erste",
        logo={"datei": str(ASSETS / "logos" / "nm-logo.svg"), "typ": "svg",
              **KOPF_LOGO}))

    # Profilkopf: Foto links, rechts Name, Rolle, Erfahrung, Verweise.
    zeilen = [dict(text=norm(person.get(f)), **typo(10, 400))
              for f in ("rolle", "erfahrung") if person.get(f)]
    for i, z in enumerate(zeilen):
        z["abstand_oben"] = 4 if i else 0
    verweistexte = VERWEISTEXT.get(sprache, VERWEISTEXT["de"])
    verweise = []
    for l in person.get("links") or []:
        titel = norm(l.get("titel"))
        verweise.append({
            "text": l.get("text") or verweistexte.get(titel.lower()) or titel,
            "url": l.get("url") or None,
            # Der Unterstrich in der Markenfarbe ist das einzige Signal, dass
            # ein Verweis anklickbar ist. Ein Portfolio, das nur als PDF
            # vorliegt, hat keine Adresse und steht deshalb ohne.
            "unterstrichen": bool(l.get("url")),
        })
    bloecke.append(block(
        "intro", abstand_oben=35.5, anker="erste",
        fotospalte=RASTER["fotospalte"], fotoabstand=RASTER["fotoabstand"],
        infospalte=RASTER["inhaltsspalte"],
        foto=({"datei": str(Path(person["foto"]).expanduser().resolve()),
               "breite": 79, "hoehe": 106, "oben": 7}
              if person.get("foto") else None),
        name=dict(text=norm(person.get("name")), abstand_unten=8,
                  **typo(24, 800, 1.35, -1.08)),
        zeilen=zeilen,
        verweise=(dict(abstand_oben=10, abstand_rechts=16, eintraege=verweise,
                       **typo(9, 400)) if verweise else None)))

    # --- Deckblatt: Bildung und Skillset, beide auf Seite 1 ---
    erste_rubrik = True
    if daten.get("bildung"):
        bloecke.append(block("rubrik", abstand_oben=32, marke=labels["bildung"],
                             text=labels["bildung"], **typo(14, 600)))
        erste_rubrik = False
        eintraege = []
        for b in daten["bildung"]:
            eintraege.append({
                "abschluss": dict(text=norm(b.get("abschluss")), **typo(10, 600)),
                "zeilen": [dict(text=norm(b[f]), abstand_oben=2, **typo(10, 400))
                           for f in ("institution", "zeitraum") if b.get(f)],
                "themen": (dict(abstand_oben=d["edu_liste"], einzug=15, abstand=2,
                                eintraege=[norm(t) for t in b["themen"]],
                                **typo(10, 400)) if b.get("themen") else None),
            })
        bloecke.append(block(
            "bildung", abstand_oben=d["h2"],
            marke=(daten["bildung"][0] or {}).get("abschluss"),
            spaltenbreite=RASTER["spalte_halb"],
            spaltenabstand=RASTER["spalte_abstand"], reihenabstand=d["reihe"],
            eintraege=eintraege))
        bloecke.append(block("trennlinie", abstand_oben=d["divider"],
                             farbe="black", staerke=1))

    if daten.get("skillset"):
        bloecke.append(block(
            "rubrik", abstand_oben=32 if erste_rubrik else d["section"],
            marke=labels["skillset"], text=labels["skillset"], **typo(14, 600)))
        skillset = daten["skillset"]

        def gruppen(spalte):
            return [{
                "titel": dict(text=norm(g.get("titel")), abstand_unten=d["h3"],
                              **typo(10, 600)),
                "eintraege": [norm(e) for e in g.get("eintraege") or []],
            } for g in spalte or []]

        erste = (skillset.get("links") or skillset.get("rechts") or [{}])[0]
        bloecke.append(block(
            "skillset", abstand_oben=d["h2"], marke=erste.get("titel"),
            spaltenbreite=RASTER["spalte_halb"],
            spaltenabstand=RASTER["spalte_abstand"], gruppenabstand=d["stack"],
            liste=dict(einzug=15, abstand=2, **typo(10, 400)),
            spalten=[gruppen(skillset.get("links")),
                     gruppen(skillset.get("rechts"))]))

    # --- Ab hier die Stationen, im PDF auf einer neuen Seite ---
    naechster_abstand = 0
    if person.get("kurzprofil"):
        bloecke.append(block("rubrik", abstand_oben=0, seitenanfang=True,
                             marke=labels["kurzprofil"], text=labels["kurzprofil"],
                             **typo(14, 600)))
        bloecke.append(block("profil", abstand_oben=s["profil_h2"],
                             marke=" ".join(norm(person["kurzprofil"]).split()[:8]),
                             text=norm(person["kurzprofil"]),
                             **typo(10, 400, 1.35, -0.05)))
        bloecke.append(block("trennlinie", abstand_oben=s["profil_divider"],
                             farbe="black", staerke=1))
        naechster_abstand = s["profil_unten"]

    st_groesse, pr_groesse = logo_groessen(daten)
    for nr, station in enumerate(daten.get("stationen") or []):
        if nr:
            naechster_abstand = s["station"]
        bloecke.append(block(
            "station", abstand_oben=naechster_abstand,
            seitenanfang=(nr == 0 and not person.get("kurzprofil")),
            marke=station.get("titel"),
            rail={"breite": RASTER["logospalte"], "oben": 3, "abstand": 10,
                  "logos": [logo_eintrag(f, st_groesse)
                            for f in logoliste(station.get("logo"))]},
            spaltenabstand=RASTER["abstand"], koerperbreite=RASTER["inhaltsspalte"],
            titel=dict(text=norm(station.get("titel")), **typo(12, 700)),
            meta=dict(abstand_oben=4, abstand=8, strich={"breite": 1, "hoehe": 10},
                      zeitraum=norm(station.get("zeitraum")),
                      firma=norm(station.get("firma")) or None, **typo(8, 400)),
            absaetze=[dict(text=norm(station[f]), abstand_oben=8, **typo(10, 400, 1.35))
                      for f in ("zusammenfassung", "beschreibung") if station.get(f)]))
        if station.get("aufgaben"):
            bloecke.append(aufgabenblock(station["aufgaben"], 8, s["bullet"]))
        for projekt in station.get("projekte") or []:
            bloecke.append(block(
                "projekt", abstand_oben=s["projekt"], einzug=RASTER["einzug"],
                marke=projekt.get("kunde"), breite=RASTER["inhaltsspalte"],
                logos=dict(abstand_unten=8, abstand=8,
                           eintraege=[logo_eintrag(f, pr_groesse)
                                      for f in logoliste(projekt.get("logo"))]),
                kunde=dict(text=norm(projekt.get("kunde")), **typo(10, 700)),
                zeitraum=(dict(text=norm(projekt["zeitraum"]), abstand_oben=4,
                               **typo(8, 400)) if projekt.get("zeitraum") else None),
                absaetze=[dict(text=norm(projekt["beschreibung"]), abstand_oben=8,
                               **typo(10, 400, 1.35))]
                if projekt.get("beschreibung") else []))
            if projekt.get("aufgaben"):
                bloecke.append(aufgabenblock(projekt["aufgaben"], 8, s["bullet"]))

    # Footer — immer am unteren Rand der letzten Seite.
    kontakt = daten.get("kontakt") or KONTAKT_VORGABE
    fuss_hoehe = round(FUSS_LOGO_BREITE / seitenverhaeltnis(ASSETS / "logos" / "nm-logo.svg"), 2)
    bloecke.append(block(
        "footer", anker="letzte",
        trennlinie={"abstand_oben": 16, "farbe": "black", "staerke": 1},
        abstand_zur_reihe=17, spaltenabstand=31, gruppenabstand=48,
        logo={"datei": str(ASSETS / "logos" / "nm-logo.svg"), "typ": "svg",
              "breite": FUSS_LOGO_BREITE, "hoehe": fuss_hoehe},
        label=typo(7, 600, None, 0.4), wert=dict(abstand_oben=8, **typo(8, 400)),
        versalien=True,
        spalten=[
            {"label": labels["ansprechpartner"],
             "zeilen": [kontakt.get("name"), kontakt.get("rolle")]},
            {"label": labels["kontakt"],
             "zeilen": [kontakt.get("mail"), kontakt.get("telefon")]},
            {"label": labels["adresse"],
             "zeilen": [kontakt.get("firma"), kontakt.get("strasse"), kontakt.get("ort")]},
        ]))
    return bloecke


def aufgabenblock(aufgaben, abstand_oben, abstand):
    """Bulletliste einer Station oder eines Projekts.

    Eigener Block, nicht Teil der Station: Im PDF darf eine Liste ueber den
    Seitenumbruch laufen, und dann steht ein Teil davon auf dem naechsten Frame.
    Geteilt wird spaeter in bulletlisten_teilen().
    """
    return block("aufgaben", abstand_oben=abstand_oben, einzug=RASTER["einzug"],
                 marke=aufgaben[0], breite=RASTER["inhaltsspalte"], einzug_liste=15,
                 abstand=abstand, eintraege=[norm(a) for a in aufgaben],
                 **typo(10, 400, 1.35, -0.05, "muted"))


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
    """--stufen liest die Sidecar-Datei, --deckblatt/--stationen schlagen sie."""
    deckblatt = stationen = "normal"
    rest = []
    argv = list(argv)
    while argv:
        a = argv.pop(0)
        if a in ("--stufen", "--deckblatt", "--stationen"):
            if not argv:
                raise SystemExit(f"{a} braucht einen Wert")
            wert = argv.pop(0)
            if a == "--stufen":
                gelesen = json.loads(Path(wert).read_text(encoding="utf-8"))
                deckblatt = gelesen.get("deckblatt", "normal")
                stationen = gelesen.get("stationen", "normal")
            elif a == "--deckblatt":
                deckblatt = wert
            else:
                stationen = wert
            continue
        rest.append(a)
    for name, wert in (("--deckblatt", deckblatt), ("--stationen", stationen)):
        if wert not in DECKBLATT:
            raise SystemExit(f"{name}: normal, kompakt oder eng — nicht {wert!r}")
    return deckblatt, stationen, rest


def main():
    deckblatt, stationen, args = stufen_lesen(sys.argv[1:])
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

    name = norm((daten.get("person") or {}).get("name")) or "Lebenslauf"
    frames = []
    for nummer in range(1, len(texte) + 1):
        eigene = [{k: v for k, v in b.items() if k not in ("seite", "marke", "anker")}
                  for b in bloecke if b["seite"] == nummer]
        frames.append({"nr": nummer, "name": f"CV — {name} — Seite {nummer}",
                       "bloecke": eigene})

    plan = {
        "pdf": str(pdf), "datei": dateiname(daten),
        "sprache": daten.get("sprache", "de"),
        "person": {"name": name, "rolle": norm((daten.get("person") or {}).get("rolle"))},
        "stufen": {"deckblatt": deckblatt, "stationen": stationen},
        "rahmen": RAHMEN, "raster": RASTER, "farben": FARBEN,
        "schrift": {"familie": "Inter", "schnitte": sorted(set(SCHNITT.values()))},
        "frames": frames,
    }
    ziel = ordner / "figma_plan.json"
    ziel.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"{ziel} geschrieben ({len(frames)} Frames, "
          f"{sum(len(f['bloecke']) for f in frames)} Bloecke)")

    hinweise = []
    if ungefunden:
        hinweise.append(
            "Im PDF-Text nicht wiedergefunden, die Seitenkante ist dort geraten: "
            + "; ".join(m[:60] for m in ungefunden))
    fehlend = sorted({b["datei"] for f in frames for b in logos_im_frame(f)
                      if not Path(b["datei"]).exists()})
    if fehlend:
        hinweise.append("Logodatei fehlt: " + ", ".join(fehlend))
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


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
