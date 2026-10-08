#!/usr/bin/env python3
"""Der Bibliotheksweg: aus figma_plan.json die use_figma-Skripte, die den
Lebenslauf aus Instanzen der veroeffentlichten Master-Bibliothek bauen.

Wird von figma_plan.py aufgerufen (Standard), laesst sich aber auch allein
starten, etwa um die Skripte mit den IDs der vollstaendigen Reihe neu zu
schreiben:

    python3 scripts/figma_bibliothek.py arbeit/figma_plan.json arbeit/ \\
            [--seite 0:1] [--unter 12:34] [--frame-ids 12:34,12:56]

Schreibt in den Ordner:
  figma_vorflug.js    lesend: Bibliothek erreichbar? Schriften da?
  figma_bau.js        baut alle Seiten (oder figma_bau_1.js, _2.js, ... wenn
                      ein Skript sonst zu gross wuerde)
  figma_pruefung.js   lesend: alles Instanzen der Bibliothek, nichts geloest,
                      Logos unverzerrt und hochgeladen, anonym ohne Namen
  figma_bilder/       SVG-Logos als PNG - eine Bildfuellung braucht Rasterdaten

Woher die Komponenten kommen: assets/master-bibliothek.json. Wie gesetzt wird:
scripts/figma_bau.js. Die Zahlen bleiben in tokens.json; hier wird nur
gegengeprueft, dass Plan und Bibliothek dieselben Abstaende meinen.

Mengengrenzen der Komponenten (Eintraege je Skillset-Gruppe, Logos je
Station, ...) werden geprueft. Aufgabenlisten und Zertifikate werden auf
mehrere Instanzen verteilt; alles andere, was nicht hineinpasst, wird
gemeldet, und dann entsteht kein Bauskript - der rohe Weg bleibt (Rueckfall),
abgeschnitten wird nichts.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokens  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
KATALOG = ASSETS / "master-bibliothek.json"
LAUFZEIT = Path(__file__).resolve().parent / "figma_bau.js"
T = tokens.laden()

# Ein use_figma-Skript darf 50 000 Zeichen haben; mit Luft fuer die Laufzeit.
SKRIPT_GRENZE = 45000
FRAMEABSTAND = 100
REIHENABSTAND = 120
# Breite der PNG je pt Logobreite: scharf auch bei 400 % Zoom.
PNG_JE_PT = 12

GRUPPEN_NAMEN = {"faehigkeiten": "Fähigkeiten", "branchen": "Branchen",
                 "tools": "Tools", "sprachen": "Sprachen"}


def katalog():
    return json.loads(KATALOG.read_text(encoding="utf-8"))


class Grenze(Exception):
    pass


def png_aus_svg(svg, ziel, breite_pt, hoehe_pt):
    """SVG-Logo als PNG fuer die Bildfuellung - gesetzt von WeasyPrint, also
    vom selben Renderer wie das PDF (Illustrator-SVGs faerben ueber <style>,
    das PyMuPDF allein nicht kennt und schwarz malt), gerastert von PyMuPDF.
    Die Seite hat genau die Masse aus dem Plan, das Seitenverhaeltnis bleibt
    also das der Datei. Ohne eins der beiden Pakete: None."""
    try:
        import fitz  # PyMuPDF
        import weasyprint
    except ImportError:
        return None
    html = (f"<style>@page{{size:{breite_pt}pt {hoehe_pt}pt;margin:0}}html,body{{margin:0}}"
            f"img{{display:block;width:{breite_pt}pt;height:{hoehe_pt}pt}}</style>"
            f'<img src="{Path(svg).resolve().as_uri()}">')
    dok = fitz.open(stream=weasyprint.HTML(string=html).write_pdf(), filetype="pdf")
    seite = dok[0]
    faktor = breite_pt * PNG_JE_PT / seite.rect.width
    pix = seite.get_pixmap(matrix=fitz.Matrix(faktor, faktor), alpha=True)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(ziel))
    return ziel


class Uebersetzer:
    def __init__(self, plan, ordner):
        self.plan = plan
        self.ordner = Path(ordner).resolve()
        self.kat = katalog()
        self.grenzen = self.kat["komponenten"]
        self.hinweise = []
        self.ueberlauf = []
        self.gebraucht = {"seite", "abstand"}
        foto = None
        for f in plan["frames"]:
            for b in f["bloecke"]:
                if b["art"] == "intro":
                    foto = b.get("foto")
        self.fassung = plan.get("fassung") or (
            "anonym" if foto and Path(foto["datei"]).name.startswith("silhouette") else "vollständig")

    def grenze(self, schluessel, art):
        return self.grenzen[schluessel]["grenzen"][art]

    def melden(self, was, anzahl, grenze, wo):
        self.ueberlauf.append(f"{wo}: {anzahl} {was}, die Komponente fasst {grenze}")

    # --- Abstaende -------------------------------------------------------

    def abstand(self, b, stufen, deckblatt):
        token = b.get("token")
        if not b.get("abstand_oben") or not token:
            return []
        varianten = self.kat["komponenten"]["abstand"]["varianten"]
        if token not in varianten:
            self.hinweise.append(f"Abstand {token} ({b['abstand_oben']}pt) hat keine Variante in "
                                 "CV/Abstand - steht ohne Abstand im Frame")
            return []
        # Gegenprobe: meint die Bibliothek im Modus dieser Seite dieselbe Zahl?
        bereich = "deckblatt" if deckblatt else "stationen"
        stufe = stufen[bereich]
        soll = (T["verdichtung"][bereich].get(stufe, {}).get(token)
                if token in T["verdichtung"][bereich].get(stufe, {})
                else T["abstand"].get(token))
        if soll is not None and abs(soll - b["abstand_oben"]) > 0.01:
            self.hinweise.append(f"Abstand {token}: Plan {b['abstand_oben']}pt, Bibliothek im Modus "
                                 f"{stufe} {soll}pt")
        return [{"k": "abstand", "variante": token, "name": f"Abstand · {token}"}]

    # --- Bilder -------------------------------------------------------------

    def logo_bild(self, l, ebene):
        datei = Path(l["datei"])
        if l["typ"] == "svg":
            png = png_aus_svg(datei, self.ordner / "figma_bilder" / (datei.stem + ".png"),
                              l["breite"], l["hoehe"])
            if png is None:
                self.hinweise.append(f"{datei.name}: SVG ohne PyMuPDF/WeasyPrint nicht in PNG "
                                     "umzusetzen - pip install pymupdf --break-system-packages; "
                                     "bis dahin bleibt das Vorgabebild der Komponente stehen")
                png = datei
            datei = png
        return {"ebene": ebene, "datei": str(datei), "scaleMode": "FIT", "art": "logo",
                "breite": l["breite"], "hoehe": l["hoehe"], "verhaeltnis": l["verhaeltnis"]}

    # --- Bloecke --------------------------------------------------------------

    def intro(self, b):
        k = {"k": "profilkopf", "variante": self.fassung, "name": "Profilkopf"}
        p = {"Name": b["name"]["text"]}
        zeilen = {z.get("feld"): z["text"] for z in b.get("zeilen") or []}
        p.update({"Rolle": zeilen["rolle"]} if "rolle" in zeilen else {"Rolle anzeigen": False})
        p.update({"Erfahrung": zeilen["erfahrung"]} if "erfahrung" in zeilen
                 else {"Erfahrung anzeigen": False})
        k["p"] = p
        if self.fassung == "anonym":
            return [k]
        foto = b.get("foto")
        p["Foto anzeigen"] = bool(foto)
        if foto:
            k["bilder"] = [{"ebene": "Foto", "datei": foto["datei"], "scaleMode": "FILL", "art": "foto"}]
            if foto["typ"] == "svg":
                self.hinweise.append("Foto ist ein SVG - in der vollständigen Fassung wird ein Rasterbild erwartet")
        verweise = (b.get("verweise") or {}).get("eintraege") or []
        if len(verweise) > self.grenze("profilkopf", "verweise"):
            self.melden("Verweise", len(verweise), self.grenze("profilkopf", "verweise"), "Profilkopf")
        p["Verweise anzeigen"] = bool(verweise)
        for n in range(2, 5):
            p[f"Verweis {n}"] = len(verweise) >= n
        kinder = {}
        for n, v in enumerate(verweise[:4], 1):
            kind = {"p": {"Label": v["text"], "Linie anzeigen": bool(v.get("unterstrichen"))}}
            if v.get("url"):
                kind["link"] = {"ebene": "Label", "url": v["url"]}
            kinder[f"Verweis {n}"] = kind
        if kinder:
            k["kinder"] = kinder
        return [k]

    def rubrik(self, b):
        return [{"k": "abschnittstitel", "name": f"Rubrik {b['text']}",
                 "p": {"Titel": b["text"], "Icon anzeigen": False}}]

    def bildung(self, b):
        eintraege = b["eintraege"]
        g = self.grenze("bildung", "eintraege")
        if len(eintraege) > g:
            self.melden("Bildungseinträge", len(eintraege), g, "Bildung")
        p = {f"Eintrag {n}": len(eintraege) >= n for n in range(2, g + 1)}
        kinder = {}
        for n, e in enumerate(eintraege[:g], 1):
            zeilen = {z.get("feld"): z["text"] for z in e["zeilen"]}
            einr, zeit = zeilen.get("institution"), zeilen.get("zeitraum")
            q = {"Abschluss": e["abschluss"]["text"]}
            q.update({"Einrichtung": einr} if einr else {"Einrichtung anzeigen": False})
            q.update({"Zeitraum": zeit} if zeit else {"Zeitraum anzeigen": False})
            kinder[f"Eintrag {n}"] = {"p": q}
        self.gebraucht.add("bildung")
        return [{"k": "bildung", "name": "Bildung", "p": p, "kinder": kinder}]

    def zertifikate(self, b):
        g = self.grenze("zertifikate", "eintraege")
        titel = b["eintraege"]
        teile = [titel[i:i + g] for i in range(0, len(titel), g)]
        if len(teile) > 1:
            self.hinweise.append(f"Zertifikate: {len(titel)} Tags, verteilt auf {len(teile)} Instanzen "
                                 f"CV/Zertifikate zu höchstens {g} - die Reihen können vom PDF abweichen")
        aus = []
        for i, teil in enumerate(teile):
            if i:
                aus.append({"k": "abstand", "variante": "zert_reihen", "name": "Abstand · zert_reihen"})
            p = {f"Zertifikat {n}": len(teil) >= n for n in range(2, g + 1)}
            p["Titel anzeigen"] = i == 0
            kinder = {f"Zertifikat {n}": {"p": {"Text": t}} for n, t in enumerate(teil, 1)}
            if i == 0:
                kinder["Titel"] = {"p": {"Titel": b["titel"]["text"]}}
            aus.append({"k": "zertifikate", "name": "Zertifikate", "p": p, "kinder": kinder})
        return aus

    def skillset(self, b):
        g = self.grenze("skillset_gruppe", "eintraege")
        da = {}
        for spalte in b["spalten"]:
            for gruppe in spalte:
                da[gruppe["schluessel"]] = gruppe
        p = {f"{GRUPPEN_NAMEN[s]} anzeigen": s in da for s in GRUPPEN_NAMEN}
        kinder = {}
        for s, gruppe in da.items():
            eintraege = gruppe["eintraege"]
            if len(eintraege) > g:
                self.melden("Einträge", len(eintraege), g, f"Skillset-Gruppe {gruppe['titel']['text']}")
            q = {f"Eintrag {n}": len(eintraege) >= n for n in range(2, g + 1)}
            sub = {"Titel": {"p": {"Titel": gruppe["titel"]["text"]}}}
            sub.update({f"Eintrag {n}": {"p": {"Text": t}} for n, t in enumerate(eintraege[:g], 1)})
            kinder[GRUPPEN_NAMEN[s]] = {"p": q, "kinder": sub}
        return [{"k": "skillset", "name": "Skillset", "p": p, "kinder": kinder}]

    def profil(self, b):
        return [{"k": "kurzprofil", "name": "Kurzprofil", "p": {"Text": b["text"]}}]

    def trennlinie(self, b):
        return [{"k": "trennlinie", "name": "Trennlinie"}]

    def station(self, b):
        logos = b["rail"]["logos"]
        nm = [l for l in logos if Path(l["datei"]).name == "nm-logo.svg"]
        fremd = [l for l in logos if l not in nm]
        g = self.grenze("station", "logos")
        firma = (b.get("firma") or {}).get("text") or ""
        if len(fremd) > g:
            self.melden("Logos", len(fremd), g, f"Station {firma or b['titel']['text']}")
        p = {"Titel": b["titel"]["text"], "New-Monday-Logo anzeigen": bool(nm)}
        p.update({"Firma": firma} if firma else {"Firma anzeigen": False})
        p.update({"Zeitraum": b["zeitraum"]["text"]} if b.get("zeitraum") else {"Zeitraum anzeigen": False})
        felder = {a.get("feld"): a["text"] for a in b.get("absaetze") or []}
        for feld, name in (("zusammenfassung", "Zusammenfassung"), ("beschreibung", "Beschreibung")):
            p.update({name: felder[feld], f"{name} anzeigen": True} if feld in felder
                     else {f"{name} anzeigen": False})
        for n in range(1, g + 1):
            p[f"Logo {n}"] = len(fremd) >= n
        return [{"k": "station", "name": f"Station {firma}".strip(), "p": p,
                 "bilder": [self.logo_bild(l, f"Logo {n}") for n, l in enumerate(fremd[:g], 1)]}]

    def aufgaben(self, b):
        g = self.grenze("aufgabenliste", "eintraege")
        teile = [b["eintraege"][i:i + g] for i in range(0, len(b["eintraege"]), g)]
        aus = []
        for teil in teile:
            p = {f"Punkt {n}": len(teil) >= n for n in range(2, g + 1)}
            kinder = {f"Punkt {n}": {"p": {"Text": t}} for n, t in enumerate(teil, 1)}
            aus.append({"k": "aufgabenliste", "name": "Aufgaben", "p": p, "kinder": kinder})
        return aus

    def projekt(self, b):
        logos = b["logos"]["eintraege"]
        g = self.grenze("projekt", "logos")
        if len(logos) > g:
            self.melden("Logos", len(logos), g, f"Projekt {b['kunde']['text']}")
        p = {"Kunde": b["kunde"]["text"], "Logos anzeigen": bool(logos)}
        p.update({"Zeitraum": b["zeitraum"]["text"]} if b.get("zeitraum") else {"Zeitraum anzeigen": False})
        absaetze = b.get("absaetze") or []
        p.update({"Beschreibung": absaetze[0]["text"]} if absaetze else {"Beschreibung anzeigen": False})
        for n in range(1, g + 1):
            p[f"Logo {n}"] = len(logos) >= n
        return [{"k": "projekt", "name": f"Projekt {b['kunde']['text']}", "p": p,
                 "bilder": [self.logo_bild(l, f"Logo {n}") for n, l in enumerate(logos[:g], 1)]}]

    def fuss(self, b):
        """Nur wenn der Kontakt von der Vorgabe abweicht - sonst gilt, was im
        Master steht, und eine Aenderung dort kommt per Update an."""
        if not self.plan.get("kontakt_abweichend"):
            return None
        sp = b["spalten"]

        def zeilen(werte):
            return ["\n".join(z["text"] for z in w) for w in werte]

        an, ko, ad = zeilen(sp[0]["werte"]), zeilen(sp[1]["werte"]), zeilen(sp[2]["werte"])
        name_rolle = sp[0]["werte"][0] if sp[0]["werte"] else []
        return {
            "Ansprechpartner": {"p": {"Label": sp[0]["label"],
                                      "Name": name_rolle[0]["text"] if name_rolle else "",
                                      "Wert 1": name_rolle[1]["text"] if len(name_rolle) > 1 else ""}},
            "Kontakt": {"p": {"Label": sp[1]["label"], "Wert 1": ko[0] if ko else "",
                              "Wert 2": ko[1] if len(ko) > 1 else "",
                              "Wert 2 anzeigen": len(ko) > 1}},
            "Adresse": {"p": {"Label": sp[2]["label"], "Wert 1": ad[0] if ad else ""}},
        }

    # --- Ganzes -----------------------------------------------------------------

    def frames(self):
        stufen = self.plan["stufen"]
        frames, fuss = [], None
        for f in self.plan["frames"]:
            deckblatt = f["nr"] == 1
            inhalt, kopf, hat_fuss = [], False, False
            for b in f["bloecke"]:
                art = b["art"]
                if art == "kopfzeile":
                    kopf = True
                    continue
                if art == "footer":
                    hat_fuss = True
                    fuss = self.fuss(b)
                    continue
                inhalt += self.abstand(b, stufen, deckblatt)
                inhalt += getattr(self, art)(b)
            frames.append({"name": f["name"], "stufe": stufen["deckblatt" if deckblatt else "stationen"],
                           "kopfzeile": kopf, "fuss": hat_fuss, "inhalt": inhalt})
        for f in frames:
            for e in f["inhalt"]:
                self.gebraucht.add(e["k"])
        return frames, fuss


def skripte(plan, ordner, seite=None, unter=None, frame_ids=None):
    """Schreibt Vorflug, Bau und Pruefung. Gibt (geschriebene Dateien,
    Hinweise, Ueberlauf) zurueck; bei Ueberlauf entsteht kein Bauskript."""
    ordner = Path(ordner)
    u = Uebersetzer(plan, ordner)
    frames, fuss = u.frames()
    laufzeit = LAUFZEIT.read_text(encoding="utf-8")
    kat = u.kat["komponenten"]
    komponenten = {s: {"key": kat[s]["key"], "typ": kat[s]["typ"], "name": kat[s]["name"]}
                   for s in sorted(u.gebraucht)}
    basis = {"seite": seite, "seitenname": f"CV — {plan['person']['name']}",
             "komponenten": komponenten, "schrift": plan["schrift"],
             "frameabstand": FRAMEABSTAND, "reihenabstand": REIHENABSTAND,
             "logo_toleranz": plan["logo_toleranz"], "fassung": u.fassung}
    geschrieben = []

    def schreibe(name, bau):
        pfad = ordner / name
        pfad.write_text("const BAU = " + json.dumps(bau, ensure_ascii=False) + ";\n" + laufzeit,
                        encoding="utf-8")
        geschrieben.append(pfad)
        return pfad

    for alt in list(ordner.glob("figma_bau*.js")):
        alt.unlink()
    schreibe("figma_vorflug.js", dict(basis, modus="vorflug",
                                      komponenten={"seite": komponenten["seite"]}))
    verboten = plan.get("verboten") or []
    # Die Pruefung braucht je Element nur Komponente und Bilder, keine Texte.
    knapp = [dict(f, inhalt=[{k: v for k, v in e.items() if k not in ("p", "kinder")}
                             for e in f["inhalt"]]) for f in frames]
    schreibe("figma_pruefung.js", dict(basis, modus="pruefen", frames=knapp, frame_ids=frame_ids,
                                       verboten=verboten))
    if u.ueberlauf:
        return geschrieben, u.hinweise, u.ueberlauf

    bau = dict(basis, modus="bauen", gebraucht=sorted(u.gebraucht), unter=unter,
               fuss=fuss, frames=frames)
    text = json.dumps(bau, ensure_ascii=False)
    if len(text) + len(laufzeit) + 20 <= SKRIPT_GRENZE:
        schreibe("figma_bau.js", bau)
    else:
        # Je Frame ein Skript; ab dem zweiten setzt es neben den vorigen Frame.
        for i, f in enumerate(frames):
            teil = dict(bau, frames=[f], fuss=fuss if f["fuss"] else None)
            if i:
                teil["unter"] = None
                teil["neben"] = frames[i - 1]["name"]
            schreibe(f"figma_bau_{i + 1}.js", teil)
    return geschrieben, u.hinweise, u.ueberlauf


def main():
    args = sys.argv[1:]
    opt = {}
    rest = []
    while args:
        a = args.pop(0)
        if a in ("--seite", "--unter", "--frame-ids"):
            opt[a] = args.pop(0)
        else:
            rest.append(a)
    if len(rest) < 2:
        raise SystemExit(__doc__)
    plan = json.loads(Path(rest[0]).read_text(encoding="utf-8"))
    ids = opt.get("--frame-ids")
    dateien, hinweise, ueberlauf = skripte(plan, rest[1], opt.get("--seite"), opt.get("--unter"),
                                           ids.split(",") if ids else None)
    for d in dateien:
        print(d)
    for h in hinweise:
        print(f"  - {h}", file=sys.stderr)
    if ueberlauf:
        print("Bibliotheksweg nicht moeglich, roher Weg (references/figma.md, Rueckfall):",
              file=sys.stderr)
        for h in ueberlauf:
            print(f"  - {h}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
