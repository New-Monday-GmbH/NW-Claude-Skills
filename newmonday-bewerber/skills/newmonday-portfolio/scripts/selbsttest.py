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
5. Screen-Stil: Mit künstlichen Screens entstehen eine Desktop-, eine Phone-
   und eine Szenenfläche. Geprüft wird, was die Figma-Vorlagen vorgeben: ein
   Raster (15° Desktop, 10° Phone, mehr Kacheln als Screens), Wortmarken-
   und Seitenzahlfeld in reiner Markenfarbe (kein Schleier, kein Schatten),
   die schwarze Phone-Fassung, das Herauslösen von Clay-Phones und die
   Szene, die die Fläche füllt.

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
        treffer = [e for e in ist_x if _norm(e["text"]) == _norm(t["text"])]
        if not treffer:
            befunde.append(f"Text »{t['text'][:50]}« fehlt")
            continue
        e = min(treffer, key=lambda e: abs(e["y"] - t["y"]) + abs(e["x"] - t["x"]))
        g = e["seg"][0]
        name = f"Text »{t['text'][:40]}«"
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
                               f"Markenfarbe ({fremd / len(daten):.0%} fremde Pixel) – "
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

    fehler += [f"Figma-Abgleich {b}" for b in figma_abgleich()]
    fehler += [f"Sprachen: {b}" for b in sprachen_pruefen()]
    fehler += [f"Screen-Stil: {b}" for b in screens_pruefen()]

    if fehler:
        print(f"Selbsttest: {len(fehler)} Abweichung(en)")
        for f in fehler:
            print(f"  - {f}")
        raise SystemExit(1)
    print("Selbsttest bestanden: Tokens, Beispiel-PDF, Figma-Abgleich "
          f"({len(list(SOLL.glob('*.json')))} Vorlage(n)), Sprachen und "
          "Screen-Stil ohne Abweichung.")


if __name__ == "__main__":
    main()
