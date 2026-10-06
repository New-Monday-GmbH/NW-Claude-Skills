#!/usr/bin/env python3
"""Prüft, ob der Skill noch so rendert wie die Figma-Vorlage.

    python3 scripts/selbsttest.py

1. Tokens: portfolio.css setzt keine eigenen Farben oder Schriften
   (design_tokens.pruefe).
2. Beispiel: beispiel/portfolio.json rendert, und jede Textstelle im PDF trägt
   einen Textstil aus tokens.json (design_tokens.pruefe_pdf).
3. Figma-Abgleich: Für jede Datei in assets/figma-soll/ wird die Folie mit
   genau dem Inhalt der Vorlage gerendert und über denselben Leser, der die
   Figma-Frames baut (figma_plan.folien_lesen), mit der Vorlage verglichen –
   Flächen, Rahmen, Radien, Trennlinien, Bilder, Logos und Texte mit Schnitt,
   Grad, Zeilenhöhe, Farbe und Lage, auf 1,5 pt genau. Was in der Vorlage
   steht und im Skill fehlt, fällt hier auf, und ebenso eine Fläche, die der
   Skill zeichnet und die Vorlage nicht kennt.
4. Sprachen: Deutsch – Muttersprache und Englisch – Business Niveau stehen
   immer auf der Profilseite, auch ohne Angabe im Material.
5. Arbeitsjahre: Die Zahl auf der Karte „Arbeitserfahrung“ trägt immer ein
   „+“ – aus „10“, 10, „ 10 “ und „10 +“ wird „10+“, „25+“ bleibt, „über 10“
   und „10+ Jahre“ bleiben und werden gemeldet.
6. Screen-Stil: Mit künstlichen Screens entstehen eine Desktop-, eine Phone-
   und eine Szenenfläche. Geprüft wird, was die Figma-Vorlagen vorgeben: ein
   Raster (15° Desktop, 10° Phone, mehr Kacheln als Screens), Wortmarken-
   und Seitenzahlfeld im reinen Grund der Fläche (kein Schleier, kein Schatten),
   die schwarze Phone-Fassung, das Herauslösen von Clay-Phones und die
   Szene, die die Fläche füllt.
7. Statement: bis 124 Zeichen keine Meldung, bis 130 ein Hinweis, darüber
   eine Warnung mit der Zahl; »« und Fettmarken zählen nicht mit.
8. Logos: Das Seitenverhältnis wird aus jeder SVG-Schreibweise gelesen, jede
   Logofläche im Layout (Kundenwand als Reihe und als Raster, Kopfseite,
   Werkzeugkacheln) passt auf 1 % zu ihrer Datei, und figma_plan gibt einem
   eingepassten Bild ein Rechteck im Seitenverhältnis der Datei.
9. Graustufen: Kundenlogos stehen schwarz-weiß wie auf Folie 3 in Figma –
   der Hauptton wird #111111, das DATEV-Grün ein mittleres Grau (#8c8c8c),
   Weiß bleibt Weiß, viewBox und Pixelmaß bleiben. Auf Kundenwand und
   Projektseiten liegen nur umgerechnete Dateien (auch im Figma-Plan), die
   Werkzeuglogos der KI-Folie bleiben farbig.
10. Fläche: Ohne Flächenfarbe liegen die Screens auf neutral/15 (nicht
   abgedunkelt, Kontur neutral/20); eine `markenfarbe` ohne Quelle wird nicht
   gesetzt; markenfarbe.py findet die Produktfläche in den Screens.
11. Schwerpunkt-Folien: stehen hinter der KI-Folie und vor der Agenturseite,
   Seitenzahlen und Divider zählen weiter, höchstens vier, drei Karten; das
   Beispiel mit Schwerpunkten trägt nur Textstile aus tokens.json. Den
   Figma-Abgleich der Folie macht Punkt 3 mit assets/figma-soll/12-schwerpunkt.json –
   das Beispielmaterial kennt keine Anfrage, also trägt das Beispiel selbst
   keine Schwerpunkt-Folie.
12. Rollenzeile: statement_rolle setzt nur Umbrüche; trägt sie andere Wörter
   als rolle, steht die Rolle selbst, mit Hinweis.
13. Durchkopplung: offene Schreibweisen („UX Design“, „Usability Testing“ …)
   werden gemeldet, nie geändert; nicht bei sprache „en“, nicht bei „UX
   Designer“ oder „User Research“, und das Beispiel ist frei davon.

Schreibt nichts in den Skill-Ordner. Rückgabe 1, wenn etwas abweicht.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import design_tokens as ds  # noqa: E402
import figma_plan as fp  # noqa: E402
import render_portfolio as rp  # noqa: E402
import screens as sc  # noqa: E402

WURZEL = HIER.parent
BEISPIEL = WURZEL / "beispiel"
SOLL = WURZEL / "assets" / "figma-soll"
TOL = 1.5          # pt – Lage und Größe
TOL_ZEILE = 0.3    # pt – Zeilenhöhe
TOL_GRAD = 0.2     # pt – Schriftgrad
TOL_LINIE = 0.1    # pt – Stärke von Linien (Flächen mit einer Kante ≤ 2 pt)


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def _norm_ist(text: str) -> str:
    """Ein Umbruch hinter einem Bindestrich („Scrum-\nTeam“) ist im gerenderten
    Text ein harter Umbruch, in Figma ein weicher - dort steht „Scrum-Team“."""
    return _norm(str(text).replace("-\n", "-"))


def _abstand(a: dict, b: dict, felder=("x", "y", "w", "h")) -> float:
    return max(abs(float(a[k]) - float(b[k])) for k in felder)


def _hex(f) -> str | None:
    return f[0].lower() if f else None


def _radien(r) -> list[float]:
    if r is None:
        return [0.0] * 4
    return [float(r)] * 4 if isinstance(r, (int, float)) else [float(x) for x in r]


def _ort(e: dict) -> str:
    return f"x {e['x']:g}, y {e['y']:g}, {e['w']:g} × {e['h']:g}"


def abgleich(soll: dict, folie: fp.Folie) -> list[str]:
    """Die gerenderte Folie gegen die Sollwerte. Liefert Befunde."""
    befunde = []
    ist_r = [e for e in folie.ebenen if e["t"] == "r"]
    ist_x = [e for e in folie.ebenen if e["t"] == "x"]
    ist_b = [e for e in folie.ebenen if e["t"] in ("i", "s")]

    if folie.hintergrund.lower() != soll.get("hintergrund", "#ffffff").lower():
        befunde.append(f"Folienfarbe {folie.hintergrund}, Vorlage {soll['hintergrund']}")

    for f in soll.get("flaechen", []):
        if f.get("pruefen") is False:
            continue
        felder = f.get("nur") or ["x", "y", "w", "h"]
        kandidaten = sorted(ist_r, key=lambda e: _abstand(e, f, felder))
        if not kandidaten or _abstand(kandidaten[0], f, felder) > TOL:
            naechste = f" – am nächsten: {_ort(kandidaten[0])}" if kandidaten else ""
            befunde.append(f"Fläche »{f['name']}« ({_ort(f)}) fehlt{naechste}")
            continue
        e = kandidaten[0]
        if (f.get("fill") or None) != _hex(e.get("f")):
            befunde.append(f"Fläche »{f['name']}« ({_ort(f)}): Füllung {_hex(e.get('f'))}, "
                           f"Vorlage {f.get('fill')}")
        s = e.get("s")
        if f.get("stroke"):
            if not s:
                befunde.append(f"Fläche »{f['name']}« ({_ort(f)}): kein Rahmen, Vorlage "
                               f"{f['sw']:g} pt {f['stroke']}")
            elif s["c"].lower() != f["stroke"].lower() or abs(s["w"] - float(f["sw"])) > 0.1:
                befunde.append(f"Fläche »{f['name']}« ({_ort(f)}): Rahmen {s['w']:g} pt {s['c']}, "
                               f"Vorlage {f['sw']:g} pt {f['stroke']}")
        elif s:
            befunde.append(f"Fläche »{f['name']}« ({_ort(f)}): Rahmen {s['w']:g} pt {s['c']}, "
                           "die Vorlage hat keinen")
        # Linien (Trenner) sind Flächen mit einer Kante von 1 pt – deren Stärke
        # zählt enger als die Lage, sonst bestünde eine doppelt so dicke Linie.
        for kante in ("w", "h"):
            if float(f[kante]) <= 2 and abs(float(e[kante]) - float(f[kante])) > TOL_LINIE:
                befunde.append(f"Fläche »{f['name']}« ({_ort(f)}): Stärke {e[kante]:g} pt, "
                               f"Vorlage {float(f[kante]):g} pt")
        if any(abs(a - b) > 0.5 for a, b in zip(_radien(e.get("r")), _radien(f.get("r")))):
            befunde.append(f"Fläche »{f['name']}« ({_ort(f)}): Radius {e.get('r')}, "
                           f"Vorlage {f.get('r', 0)}")

    # Umgekehrt: jede gezeichnete Fläche muss eine Entsprechung in der Vorlage
    # haben – an derselben Stelle und in derselben Farbe. Sonst malt der Skill
    # etwas, das es dort nicht gibt: auch eine sichtbare Linie dort, wo die
    # Vorlage nur eine unsichtbare (weiß auf weiß) führt.
    def bekannt(e) -> bool:
        for f in soll.get("flaechen", []):
            if (_abstand(e, f, f.get("nur") or ("x", "y", "w", "h")) <= TOL
                    and (f.get("fill") or None) == _hex(e.get("f"))):
                return True
        return any(_abstand(e, b) <= TOL for b in soll.get("bilder", []))
    for e in ist_r:
        if not bekannt(e):
            rahmen = f", Rahmen {e['s']['c']}" if e.get("s") else ""
            befunde.append(f"Fläche »{e['n']}« ({_ort(e)}, {_hex(e.get('f'))}{rahmen}) "
                           "steht nicht in der Vorlage")

    for t in soll.get("texte", []):
        if t.get("pruefen") is False:
            continue
        # „erwartet“: Der Skill setzt aus dem Inhalt der Vorlage nach einer
        # eigenen Regel einen anderen Text (Arbeitsjahre „14“ -> „14+“). Lage,
        # Schnitt, Grad und Farbe zählen weiter wie in der Vorlage.
        text = t.get("erwartet", t["text"])
        treffer = [e for e in ist_x if _norm_ist(e["text"]) == _norm(text)]
        if not treffer:
            befunde.append(f"Text »{text[:50]}« fehlt")
            continue
        e = min(treffer, key=lambda e: abs(e["y"] - t["y"]) + abs(e["x"] - t["x"]))
        g = e["seg"][0]
        name = f"Text »{text[:40]}«"
        if (g["familie"], g["schnitt"]) != (t["familie"], t["schnitt"]):
            befunde.append(f"{name}: {g['familie']} {g['schnitt']}, "
                           f"Vorlage {t['familie']} {t['schnitt']}")
        if abs(g["grad"] - float(t["groesse"])) > TOL_GRAD:
            befunde.append(f"{name}: {g['grad']:g} pt, Vorlage {float(t['groesse']):g} pt")
        if t.get("zeile") and abs(e["zh"] - float(t["zeile"])) > TOL_ZEILE:
            befunde.append(f"{name}: Zeilenhöhe {e['zh']:g}, Vorlage {t['zeile']:g}")
        if t.get("farbe") and g["farbe"].lower() != t["farbe"].lower():
            befunde.append(f"{name}: Farbe {g['farbe']}, Vorlage {t['farbe']}")
        if t.get("unterstrichen") is not None and bool(g.get("unterstrichen")) != bool(t["unterstrichen"]):
            befunde.append(f"{name}: unterstrichen {bool(g.get('unterstrichen'))}, "
                           f"Vorlage {t['unterstrichen']}")
        if t.get("vergleich") == "mitte":
            ist = (e["x"] + e["w"] / 2, e["y"] + e["zh"] / 2)
            soll_m = (t["x"] + t["w"] / 2, t["y"] + t["h"] / 2)
        else:
            ist, soll_m = (e["x"], e["y"]), (t["x"], t["y"])
        if max(abs(ist[0] - soll_m[0]), abs(ist[1] - soll_m[1])) > TOL:
            befunde.append(f"{name}: Lage {ist[0]:g}/{ist[1]:g}, Vorlage {soll_m[0]:g}/{soll_m[1]:g}")

    for b in list(soll.get("bilder", [])) + list(soll.get("logos", [])):
        if not any(_abstand(e, b) <= TOL for e in ist_b):
            naechste = min(ist_b, key=lambda e: _abstand(e, b)) if ist_b else None
            rest = f" – am nächsten: {_ort(naechste)}" if naechste else ""
            befunde.append(f"Bild »{b['name']}« ({_ort(b)}) fehlt{rest}")
    return befunde


def figma_abgleich() -> list[str]:
    befunde = []
    grund = json.loads((BEISPIEL / "portfolio.json").read_text(encoding="utf-8"))
    for datei in sorted(SOLL.glob("*.json")):
        soll = json.loads(datei.read_text(encoding="utf-8"))
        d = copy.deepcopy(grund)
        for teil, wert in (soll.get("inhalt") or {}).items():
            d[teil] = (d.get(teil) or {}) | wert if isinstance(wert, dict) else wert
        with tempfile.TemporaryDirectory() as tmp:
            html_text, _ = rp.baue_html(d, BEISPIEL, Path(tmp))
            folien, _ = fp.folien_lesen(html_text)
        folie = folien[int(soll["folie"]) - 1]
        for b in abgleich(soll, folie):
            befunde.append(f"{datei.name}: {b}")
    return befunde


def sprachen_pruefen() -> list[str]:
    befunde = []
    soll = [{"sprache": "Deutsch", "niveau": "Muttersprache"},
            {"sprache": "Englisch", "niveau": "Business Niveau"}]
    for eingang in (None, [], [{"sprache": "Deutsch", "niveau": ""},
                               {"sprache": "Englisch", "niveau": "Fließend"}]):
        ist = rp.sprachen_mit_vorgabe(eingang, "de")[:2]
        if ist != soll:
            befunde.append(f"aus {eingang!r} wird {ist!r}, erwartet {soll!r}")
    mit = rp.sprachen_mit_vorgabe([{"sprache": "Französisch", "niveau": "Gut"}], "de")
    if [s["sprache"] for s in mit] != ["Deutsch", "Englisch", "Französisch"]:
        befunde.append(f"weitere Sprachen gehen verloren oder stehen falsch: {mit!r}")
    rp.hinweise.clear()
    return befunde


def erfahrung_pruefen() -> list[str]:
    """Die Arbeitsjahre tragen immer ein „+“ – genau eines."""
    befunde = []
    rp.hinweise.clear()
    for eingang, soll in (("10", "10+"), (10, "10+"), (" 10 ", "10+"), (10.0, "10+"),
                          ("10 +", "10+"), ("25+", "25+"), ("über 10", "über 10"),
                          ("10+ Jahre", "10+ Jahre")):
        ist = rp.erfahrung_anzeige(eingang)
        if ist != soll:
            befunde.append(f"aus {eingang!r} wird {ist!r}, erwartet {soll!r}")
    gemeldet = [h for h in rp.hinweise if "Arbeitserfahrung" in h]
    if (len(gemeldet) != 2 or not any("„über 10“" in h for h in gemeldet)
            or not any("„10+ Jahre“" in h for h in gemeldet)):
        befunde.append("nur „über 10“ und „10+ Jahre“ gehören in die Prüfhinweise, "
                       f"gemeldet: {gemeldet!r}")
    rp.hinweise.clear()
    return befunde


def statement_pruefen() -> list[str]:
    """Bis 124 Zeichen still, bis 130 ein Hinweis, darüber eine Warnung mit
    Zahl. Die »« des Layouts und Fettmarken zählen nicht mit."""
    befunde = []
    t = rp.TEXTE["de"]
    for laenge, soll in ((124, None), (127, "Hinweis"), (131, "Warnung")):
        rp.hinweise.clear()
        text = "»" + "x" * (laenge - 2) + " y«"
        d = {"person": {"statement": {"text": text, "zitat": True}, "rolle": "UX"}}
        rp.seite_statement(d, t, BEISPIEL, 4)
        meldung = [h for h in rp.hinweise if "Statement" in h]
        if rp.statement_zeichen(text) != laenge:
            befunde.append(f"gezählt {rp.statement_zeichen(text)} Zeichen, erwartet {laenge}")
        if soll is None and meldung:
            befunde.append(f"{laenge} Zeichen werden gemeldet: {meldung!r}")
        elif soll == "Hinweis" and (not meldung or "Warnung" in meldung[0]):
            befunde.append(f"{laenge} Zeichen: erwartet ein Hinweis, gemeldet {meldung!r}")
        elif soll == "Warnung" and (not meldung or not meldung[0].startswith("Warnung")
                                    or str(laenge) not in meldung[0]):
            befunde.append(f"{laenge} Zeichen: erwartet eine Warnung mit Zahl, gemeldet {meldung!r}")
    if rp.statement_zeichen("**Gut** gesagt.") != len("Gut gesagt."):
        befunde.append("Fettmarken zählen bei der Statement-Länge mit")
    rp.hinweise.clear()
    return befunde


def logos_pruefen() -> list[str]:
    """Logos nie verzerrt: Das Seitenverhältnis kommt aus der Datei, in jeder
    SVG-Schreibweise, und jede Logofläche im Layout – Kundenwand als Reihe und
    als Raster, Kopfseite, Werkzeugkacheln – passt dazu auf 1 %. In Figma
    bekommt ein eingepasstes Bild ein Rechteck im Seitenverhältnis der Datei."""
    befunde = []
    rp.hinweise.clear()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name, kopf, soll in (
                ("viewbox.svg", '<svg viewBox="0 0 300 100">', 3.0),
                ("komma.svg", '<svg viewBox="0,0,300,100">', 3.0),
                ("exponent.svg", '<svg viewBox="0 0 1e3 500">', 2.0),
                ("hoehe-zuerst.svg", '<svg height="82.4" width="300">', 300 / 82.4),
                ("einheit.svg", '<svg stroke-width="9" width="120px" height="40px">', 3.0)):
            datei = tmp / name
            datei.write_text(f'<?xml version="1.0"?>\n{kopf}<rect width="1" height="1"/></svg>')
            ist = rp.seitenverhaeltnis(datei.as_uri())
            if abs(ist - soll) > 1e-3:
                befunde.append(f"{name}: Seitenverhältnis {ist:.3f}, erwartet {soll:.3f}")

        # Figma: Fläche 100 × 100 für eine Datei 2:1 -> Rechteck 100 × 50,
        # mittig; links verankert bleibt x stehen. Gemeldet wird es auch.
        from PIL import Image
        breit = tmp / "breit.png"
        Image.new("RGBA", (200, 100)).save(breit)
        for anker, soll_x in (((0.5, 0.5), 10.0), ((0.0, 0.5), 10.0)):
            rp.hinweise.clear()
            e = {"x": 10.0, "y": 10.0, "w": 100.0, "h": 100.0}
            fp.im_verhaeltnis(e, breit, "contain", anker, 3)
            if (e["w"], e["h"], e["x"], e["y"]) != (100.0, 50.0, soll_x, 35.0):
                befunde.append(f"Figma-Rechteck für 2:1 in 100 × 100: {e}")
            if not any("breit.png" in h for h in rp.hinweise):
                befunde.append("Figma: eine Fläche außerhalb des Seitenverhältnisses wird nicht gemeldet")

        # Das Layout selbst: das Beispiel (Raster, Kopfseiten, KI-Kacheln) und
        # dieselben Daten mit fünf Kunden (eine Reihe).
        grund = json.loads((BEISPIEL / "portfolio.json").read_text(encoding="utf-8"))
        reihe = copy.deepcopy(grund)
        reihe["kunden"] = reihe["kunden"][:5]
        for fall, d in (("Raster", grund), ("Reihe", reihe)):
            rp.hinweise.clear()
            html_text, _ = rp.baue_html(d, BEISPIEL, tmp)
            folien, bilder = fp.folien_lesen(html_text)
            for e in bilder:
                if e["passung"] == "cover":
                    continue
                v = rp.seitenverhaeltnis(Path(e["quelle"]).as_uri())
                if abs((e["w"] / e["h"]) / v - 1) > rp.LOGO_VERZERRUNG_MAX:
                    befunde.append(f"{fall}: {Path(e['quelle']).name} auf Folie {e['folie']} "
                                   f"steht {e['w']:g} × {e['h']:g} pt, Datei {v:.3f}")
            if any("verzerrt" in h for h in rp.hinweise):
                befunde.append(f"{fall}: {[h for h in rp.hinweise if 'verzerrt' in h]!r}")
    rp.hinweise.clear()
    return befunde


def _kuenstliche_screens():
    """Drei Desktop-Screens, drei Phone-Screens, ein Clay-Mockup mit zwei
    Phones und eine Showcase-Szene - jeder Screen mit eigenem Aufbau, damit
    die Doublettenpruefung sie nicht zusammenlegt."""
    from PIL import Image, ImageDraw
    farben = [(230, 57, 70), (42, 157, 143), (69, 123, 157)]
    desktop, phone = [], []
    for i, f in enumerate(farben):
        d = Image.new("RGB", (1400, 900), (250, 250, 252))
        z = ImageDraw.Draw(d)
        z.rectangle((0, 0, 1400, 70), fill=f)
        z.rectangle((0, 70, 220 + i * 60, 900), fill=(236, 239, 244))
        for k in range(3 + i):
            z.rectangle((300, 140 + k * 150, 1300 - i * 200, 250 + k * 150),
                        fill=(210 - 30 * i, 215, 225))
        desktop.append((f"desktop-{i}.png", d))
        p = Image.new("RGB", (560, 1210), (248, 248, 250))
        z = ImageDraw.Draw(p)
        z.rectangle((0, 0, 560, 90 + 60 * i), fill=f)
        for k in range(2 + 2 * i):
            z.rectangle((40, 220 + k * 120, 520 - 60 * i, 300 + k * 120),
                        fill=(200 - 40 * i, 205, 215))
        z.rectangle((40, 1100, 520, 1170), fill=f)
        phone.append((f"phone-{i}.png", p))
    clay = Image.new("RGB", (1600, 1000), (229, 229, 231))
    z = ImageDraw.Draw(clay)
    for j, x in enumerate((400, 900)):
        z.rounded_rectangle((x, 180, x + 300, 820), 44, fill=(246, 246, 246))
        z.rectangle((x + 30, 260 + 200 * j, x + 270, 330 + 200 * j), fill=(120, 40, 160))
    szene = Image.new("RGB", (1920, 1200), (16, 24, 40))
    z = ImageDraw.Draw(szene)
    for x, y in ((260, 240), (700, 380), (1150, 300)):
        z.rectangle((x, y, x + 560, y + 420), fill=(240, 242, 246))
        z.rectangle((x, y, x + 560, y + 36), fill=(200, 204, 212))
    return desktop, phone, [("clay.png", clay)], [("szene.png", szene)]


def screens_pruefen() -> list[str]:
    """Die Screenflaechen gegen die Figma-Vorlagen (screens.py, Stand 11+)."""
    befunde = []
    marke = "#aa164a"
    grund = sc._farbe(marke)
    desktop, phone, clay, szene = _kuenstliche_screens()

    for name, bilder, art, winkel in (("Desktop", desktop, "desktop", 15.0),
                                      ("Phone", phone, "phone", 10.0)):
        plan, stuecke, bild = sc.planen(bilder, "panel", 0, "selbsttest")
        sc.hole_hinweise()
        if plan is None:
            befunde.append(f"{name}: keine Rasterfläche geplant")
            continue
        if plan["winkel"] != winkel:
            befunde.append(f"{name}: Kippwinkel {plan['winkel']}°, Vorlage {winkel}°")
        W, H = [v * sc.PX_JE_PUNKT for v in sc.GROESSEN["panel"]]
        sichtbar = [u for u in sc.umrisse(plan, W, H)
                    if max(x for x, _ in u) > 0 and min(x for x, _ in u) < W
                    and max(y for _, y in u) > 0 and min(y for _, y in u) < H]
        if len(sichtbar) <= len(bilder):
            befunde.append(f"{name}: {len(sichtbar)} Kacheln sichtbar – ein Raster "
                           f"wiederholt {len(bilder)} Screens bis an die Ränder")
        fertig = sc._komponieren(plan, stuecke, (W, H), grund)
        for feld_name, (x0, y0, x1, y1) in zip(("Wortmarke", "Seitenzahl"),
                                              sc._felder("panel")):
            ausschnitt = fertig.crop((int(x0), int(y0), int(x1), int(y1)))
            daten = list(ausschnitt.getdata())
            fremd = sum(1 for px in daten
                        if max(abs(a - b) for a, b in zip(px, grund)) > 10)
            if fremd / len(daten) > 0.02:
                befunde.append(f"{name}: unter der {feld_name} liegt nicht reine "
                               f"Grundfarbe ({fremd / len(daten):.0%} fremde Pixel) – "
                               "Schleier, Schatten oder eine Kachel im Feld")
        if art == "phone":
            schwarz = sum(1 for px in fertig.resize((W // 4, H // 4)).getdata()
                          if max(px) < 24) / ((W // 4) * (H // 4))
            if schwarz < 0.02:
                befunde.append(f"Phone: kaum Schwarz auf der Fläche ({schwarz:.1%}) – "
                               "die Phones stecken nicht in der Fassung")

    stuecke = sc.aufbereiten(clay, "selbsttest")
    sc.hole_hinweise()
    if [s.art for s in stuecke] != ["phone", "phone"]:
        befunde.append(f"Clay-Mockup: {[s.art for s in stuecke]} statt zweier "
                       "herausgelöster Phone-Screens")

    plan, stuecke, bild = sc.planen(szene, "panel", 0, "selbsttest")
    sc.hole_hinweise()
    if bild is None:
        befunde.append("Szene: wurde nicht als Szene erkannt und nicht als Ganzes gezeigt")
    return befunde


def _svg(tmp: Path, name: str, inhalt: str, vb: str = "0 0 100 50") -> Path:
    datei = tmp / name
    datei.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{inhalt}</svg>')
    return datei


def _grau(hexwert: str) -> int | None:
    """Grauwert einer Hex-Farbe, None wenn sie bunt ist."""
    h = hexwert.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return r if r == g == b else None


def graustufen_pruefen() -> list[str]:
    """Kundenlogos schwarz-weiß nach der Regel aus Folie 3 (logo_grau.py)."""
    import re

    import logo_grau as lg
    from PIL import Image
    befunde = []
    rp.hinweise.clear()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # DATEV wie in der Bibliothek: grüne Fläche, Petrol-Schrift darunter.
        datev = _svg(tmp, "datev.svg", '<rect width="100" height="34" fill="#90d033"/>'
                     '<path d="M0 38h100v12H0z" style="fill:#039a9a"/>')
        text = lg.umrechnen(datev, tmp / "c").read_text()
        farben = {f.lower() for f in re.findall(r"#[0-9a-fA-F]{6}", text)}
        if 'viewBox="0 0 100 50"' not in text:
            befunde.append("die viewBox des Logos hat sich verändert")
        if any(_grau(f) is None for f in farben):
            befunde.append(f"farbige Werte im umgerechneten SVG: {sorted(farben)}")
        if "#111111" not in farben:
            befunde.append(f"DATEV-Schrift nicht base/black: {sorted(farben)}")
        mitte = [_grau(f) for f in farben if _grau(f) not in (None, 17)]
        if not mitte or abs(mitte[0] - 0x8c) > 6:
            befunde.append(f"DATEV-Grün nicht als mittleres Grau (#8c8c8c): {sorted(farben)}")
        # Eine dunkle Marke allein wird base/black, Weiß bleibt, Elemente ohne
        # Füllung erben #111111 vom Wurzelelement.
        union = _svg(tmp, "union.svg", '<path d="M0 0h60v50H0z" fill="#00358E"/>'
                     '<path d="M70 0h30v50H70z"/><circle cx="30" cy="25" r="5" fill="#fff"/>')
        text = lg.umrechnen(union, tmp / "c").read_text()
        if "#00358E" in text or 'fill="#111111"' not in text or "#ffffff" not in text:
            befunde.append("dunkle Marke nicht auf #111111 oder Weiß nicht erhalten")
        # Rasterlogo: Maß und Alpha bleiben, nur Grau.
        bild = Image.new("RGBA", (200, 80), (0, 0, 0, 0))
        bild.paste((0, 40, 91, 255), (20, 20, 180, 60))
        bild.save(tmp / "tollwerk.png")
        with Image.open(lg.umrechnen(tmp / "tollwerk.png", tmp / "c")) as im:
            mit = im.convert("RGBA")
        if mit.size != (200, 80) or mit.getpixel((0, 0))[3] != 0 \
                or mit.getpixel((100, 40))[:3] != (17, 17, 17):
            befunde.append(f"Rasterlogo: {mit.size}, Ecke {mit.getpixel((0, 0))}, "
                           f"Mitte {mit.getpixel((100, 40))}")
        lg.hole_hinweise()

        # Im Layout: Kundenwand und Projektseiten nur mit umgerechneten
        # Dateien - dieselben liest der Figma-Plan -, die KI-Folie farbig.
        d = json.loads((BEISPIEL / "portfolio.json").read_text(encoding="utf-8"))
        html_text, _ = rp.baue_html(d, BEISPIEL, tmp)
        _, bilder = fp.folien_lesen(html_text)
        name = lambda e: Path(e["quelle"]).name
        wand = [name(e) for e in bilder if e["folie"] == 3 and not name(e).startswith("nm-logo")]
        if not wand or any(not n.startswith("logo-grau-") for n in wand):
            befunde.append(f"Kundenwand mit Originaldateien: {wand}")
        kopf = [name(e) for e in bilder if "apobank" in name(e).lower()]
        if len(kopf) < 3 or any(not n.startswith("logo-grau-") for n in kopf):
            befunde.append(f"Projektseiten mit farbigem Kundenlogo: {kopf}")
        ki = [name(e) for e in bilder if e["folie"] == 10]
        if not ki or any(n.startswith("logo-grau-") for n in ki):
            befunde.append(f"KI-Folie: Werkzeuglogos nicht im Original: {ki}")
        for e in bilder:
            q = Path(e["quelle"])
            if q.name.startswith("logo-grau-") and q.suffix == ".svg":
                bunt = [f for f in re.findall(r"#[0-9a-fA-F]{6}", q.read_text())
                        if _grau(f) is None]
                if bunt:
                    befunde.append(f"{q.name}: noch farbig {bunt[:3]}")
    rp.hinweise.clear()
    return befunde


def flaeche_pruefen() -> list[str]:
    """Standard neutral, Farbe nur mit Quelle, Vorschlag aus den Screens."""
    import markenfarbe as mf
    from PIL import Image, ImageDraw
    befunde = []
    neutral = ds.laden()["farben"]["neutral/15"]
    grund = sc._grundton(sc._farbe(None))
    if "#%02x%02x%02x" % grund != neutral:
        befunde.append(f"ohne Farbe liegt der Grund auf {grund}, erwartet {neutral}")
    if sc._konturfarbe(grund) == (255, 255, 255):
        befunde.append("auf der neutralen Fläche tragen die Karten eine weiße Kontur")
    if "#%02x%02x%02x" % sc._grundton(sc._farbe("#ffffff")) != neutral:
        befunde.append("reines Weiß wird nicht zur neutralen Fläche")
    if sc._grundton(sc._farbe("#247488")) != (36, 116, 136):
        befunde.append("eine Produktfarbe (#247488) wird verändert")
    rp.hinweise.clear()
    if rp.flaechenfarbe({"kunde": "X", "markenfarbe": "#00358e"}) is not None \
            or not any("markenfarbe_quelle" in h for h in rp.hinweise):
        befunde.append("markenfarbe ohne Quelle wird gesetzt oder nicht gemeldet")
    if rp.flaechenfarbe({"kunde": "X", "markenfarbe": "#247488",
                         "markenfarbe_quelle": "Kopfleiste der Anwendung"}) != "#247488":
        befunde.append("markenfarbe mit Quelle wird nicht gesetzt")
    rp.hinweise.clear()
    with tempfile.TemporaryDirectory() as tmp:
        dateien = []
        for i in range(2):
            b = Image.new("RGB", (1200, 800), (250, 250, 250))
            z = ImageDraw.Draw(b)
            z.rectangle((0, 0, 1200, 120), fill=(36, 116, 136))
            z.rectangle((0, 120, 220, 800), fill=(36, 116, 136))
            z.rectangle((400, 300 + i * 40, 520, 340 + i * 40), fill=(230, 57, 70))
            b.save(Path(tmp) / f"s{i}.png")
            dateien.append(Path(tmp) / f"s{i}.png")
        v = mf.vorschlaege(dateien)
        if not v or v[0]["farbe"] != "#247488" or not v[0]["flaechig"]:
            befunde.append(f"markenfarbe.py findet die Produktfläche nicht: {v[:1]}")
        if any(x["flaechig"] for x in v[1:]):
            befunde.append(f"ein Akzent gilt als Fläche: {v[1:]}")
    if hasattr(mf, "farbe"):
        befunde.append("markenfarbe.py liest noch Farben aus dem Logo (farbe())")
    return befunde


def schwerpunkte_pruefen() -> list[str]:
    """Lage, Zählung und Grenzen der Schwerpunkt-Folien."""
    import re
    befunde = []
    grund = json.loads((BEISPIEL / "portfolio.json").read_text(encoding="utf-8"))
    drei = json.loads((SOLL / "12-schwerpunkt.json").read_text(
        encoding="utf-8"))["inhalt"]["schwerpunkte"]

    # Ein Zwischenspeicher fuer alle Laeufe: die Screenflaechen sind bei
    # jedem Lauf dieselben, nur die Folienfolge aendert sich.
    lager = tempfile.TemporaryDirectory()

    def folge(d) -> tuple[list[str], list[int]]:
        """Seitenarten in Reihenfolge und die gesetzten Seitenzahlen."""
        rp.hinweise.clear()
        html_text, _ = rp.baue_html(copy.deepcopy(d), BEISPIEL, Path(lager.name))
        # Die letzte Klasse benennt die Seite: "seite--arbeitsweise seite--ki" ist die KI-Folie.
        arten = [k.split()[-1].replace("seite--", "")
                 for k in re.findall(r'<section class="seite ([^"]+)"', html_text)]
        nummern = [int(n) for n in re.findall(
            r'class="seitenzahl t-seitenzahl[^"]*">(\d+)<', html_text)]
        return arten, nummern

    ohne, _ = folge(grund)
    mit_d = copy.deepcopy(grund)
    mit_d["schwerpunkte"] = drei[:2]
    mit, nummern = folge(mit_d)
    if "schwerpunkt" in ohne:
        befunde.append("ohne „schwerpunkte“ entsteht trotzdem eine Schwerpunkt-Folie")
    if len(mit) != len(ohne) + 2:
        befunde.append(f"zwei Schwerpunkte ergeben {len(mit) - len(ohne)} Folien mehr")
    if "schwerpunkt" in mit:
        i = mit.index("schwerpunkt")
        if mit[i - 1] != "ki" or mit[i + 2] != "agentur":
            befunde.append(f"Reihenfolge: {mit[i - 1:i + 3]}")
    if mit.count("divider") != 3:
        befunde.append(f"{mit.count('divider')} Divider statt 3")
    # Jede Folie mit Seitenzahl traegt ihre Blattnummer, ohne Luecke.
    blatt = [k + 1 for k, art in enumerate(mit) if art not in ("cover", "divider")]
    if nummern != blatt:
        befunde.append(f"Seitenzahlen {nummern}, erwartet {blatt}")
    # Ohne KI-Folie stehen sie direkt hinter den Arbeitsweise-Seiten.
    ohne_ki = copy.deepcopy(mit_d)
    ohne_ki["person"]["ki"] = {}
    arten, _ = folge(ohne_ki)
    k = arten.index("schwerpunkt") if "schwerpunkt" in arten else 0
    if arten[k - 1] != "arbeitsweise" or arten[k + 2] != "agentur":
        befunde.append(f"ohne KI-Folie: {arten[k - 1:k + 3]}")
    # Hoechstens vier Folien, drei Karten - beides mit Hinweis.
    viel = copy.deepcopy(grund)
    viel["schwerpunkte"] = drei + drei
    arten, _ = folge(viel)
    if arten.count("schwerpunkt") != 4 or not any("ersten 4" in h for h in rp.hinweise):
        befunde.append(f"sechs Schwerpunkte: {arten.count('schwerpunkt')} Folien, "
                       "erwartet 4 mit Hinweis")
    zwei = copy.deepcopy(grund)
    zwei["schwerpunkte"] = [dict(drei[0], karten=drei[0]["karten"][:2])]
    folge(zwei)
    if not any("2 Karte(n)" in h for h in rp.hinweise):
        befunde.append("zwei Karten werden nicht gemeldet")
    lager.cleanup()
    rp.hinweise.clear()
    return befunde


def rollenzeile_pruefen() -> list[str]:
    """Folie 4: statement_rolle setzt nur Umbrueche, die Woerter sind die Rolle."""
    befunde = []
    for umbruch, rolle, soll, meldung in (
            ("UX & AI\nDesigner", "UX & AI Designer", "UX & AI\nDesigner", False),
            ("Konzept-\nentwickler", "Konzeptentwickler", "Konzept-\nentwickler", False),
            ("UX-\nDesigner", "UX-Designer", "UX-\nDesigner", False),
            ("User Experience\nDesigner", "UX & AI Designer", "UX & AI Designer", True),
            ("", "UX & AI Designer", "UX & AI Designer", False)):
        rp.hinweise.clear()
        ist = rp.statement_rolle({"rolle": rolle, "statement_rolle": umbruch})
        gemeldet = any("statement_rolle" in h for h in rp.hinweise)
        if ist != soll or gemeldet != meldung:
            befunde.append(f"„{umbruch}“ / „{rolle}“: gesetzt „{ist}“, Hinweis {gemeldet}")
    rp.hinweise.clear()
    return befunde


def durchkopplung_pruefen() -> list[str]:
    """Offene Schreibweisen werden gemeldet, nie geaendert - nur im Deutschen."""
    befunde = []
    grund = json.loads((BEISPIEL / "portfolio.json").read_text(encoding="utf-8"))
    offen_im_beispiel = rp.durchkopplung_pruefen(grund)
    if offen_im_beispiel:
        befunde.append(f"das Beispiel trägt offene Schreibweisen: {offen_im_beispiel}")
    d = copy.deepcopy(grund)
    d["person"]["kenntnisse"][0] = "UX Design und Usability Testing"
    d["projekte"][0]["rolle"] = ["Stakeholder Management", "Senior UX Designer"]
    d["projekte"][0]["projekt"] += " Ein User Centered Design-Ansatz mit User Research."
    d["schwerpunkte"] = [{"titel": "UX Konzeption", "text": "", "karten": []}]
    vorher = json.dumps(d, sort_keys=True)
    meldungen = rp.durchkopplung_pruefen(d)
    for offen in ("UX Design", "Usability Testing", "Stakeholder Management",
                  "User Centered Design", "UX Konzeption"):
        if not any(f"„{offen}“" in m for m in meldungen):
            befunde.append(f"kein Hinweis auf „{offen}“")
    if len(meldungen) != 5:
        befunde.append(f"{len(meldungen)} Hinweise statt 5 („UX Designer“ und „User "
                       f"Research“ bleiben): {meldungen}")
    if json.dumps(d, sort_keys=True) != vorher:
        befunde.append("die Prüfung hat den Text geändert statt nur zu melden")
    d["sprache"] = "en"
    if rp.durchkopplung_pruefen(d):
        befunde.append("Hinweise auch im englischen Portfolio")
    return befunde


def main() -> None:
    fehler = []
    fehler += [f"Tokens: {b}" for b in ds.pruefe()]

    with tempfile.TemporaryDirectory() as tmp:
        quelle = BEISPIEL / "portfolio.json"
        d = json.loads(quelle.read_text(encoding="utf-8"))
        ziel = Path(tmp) / "beispiel.pdf"
        html_text, _ = rp.baue_html(d, BEISPIEL, Path(tmp))
        rp.rendere(html_text, ziel)
        fehler += [f"Beispiel-PDF: {b}" for b in ds.pruefe_pdf(ziel)]
        # Dasselbe Beispiel mit den drei Schwerpunkt-Folien aus Florians Deck:
        # auch deren Texte muessen Textstile aus tokens.json tragen.
        d["schwerpunkte"] = json.loads((SOLL / "12-schwerpunkt.json").read_text(
            encoding="utf-8"))["inhalt"]["schwerpunkte"]
        ziel = Path(tmp) / "beispiel-schwerpunkte.pdf"
        html_text, _ = rp.baue_html(d, BEISPIEL, Path(tmp))
        rp.rendere(html_text, ziel)
        fehler += [f"Beispiel mit Schwerpunkten: {b}" for b in ds.pruefe_pdf(ziel)]

    fehler += [f"Figma-Abgleich {b}" for b in figma_abgleich()]
    fehler += [f"Sprachen: {b}" for b in sprachen_pruefen()]
    fehler += [f"Arbeitsjahre: {b}" for b in erfahrung_pruefen()]
    fehler += [f"Screen-Stil: {b}" for b in screens_pruefen()]
    fehler += [f"Statement: {b}" for b in statement_pruefen()]
    fehler += [f"Logos: {b}" for b in logos_pruefen()]
    fehler += [f"Graustufen: {b}" for b in graustufen_pruefen()]
    fehler += [f"Fläche: {b}" for b in flaeche_pruefen()]
    fehler += [f"Schwerpunkte: {b}" for b in schwerpunkte_pruefen()]
    fehler += [f"Rollenzeile: {b}" for b in rollenzeile_pruefen()]
    fehler += [f"Durchkopplung: {b}" for b in durchkopplung_pruefen()]

    if fehler:
        print(f"Selbsttest: {len(fehler)} Abweichung(en)")
        for f in fehler:
            print(f"  - {f}")
        raise SystemExit(1)
    print("Selbsttest bestanden: Tokens, Beispiel-PDF, Figma-Abgleich "
          f"({len(list(SOLL.glob('*.json')))} Vorlage(n)), Sprachen, Arbeitsjahre, "
          "Screen-Stil, Statement-Länge, Logo-Proportionen, Graustufen, Fläche, "
          "Schwerpunkte, Rollenzeile und Durchkopplung ohne Abweichung.")


if __name__ == "__main__":
    main()
