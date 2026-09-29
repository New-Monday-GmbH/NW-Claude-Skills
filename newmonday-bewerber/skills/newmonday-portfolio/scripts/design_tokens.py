#!/usr/bin/env python3
"""Das Design System des Portfolios — eine Quelle für Farben und Schriften.

    python3 scripts/design_tokens.py pruefe                  # Skill gegen die Tokens
    python3 scripts/design_tokens.py pruefe --pdf deck.pdf   # fertiges PDF dazu
    python3 scripts/design_tokens.py pruefe --figma dump.json  # Tokens gegen Figma
    python3 scripts/design_tokens.py css                     # erzeugtes CSS ansehen

Farben, Textstile, Schriftdateien, Linien, Kartenradius und -abstände stehen einmal, in
assets/tokens.json — gespiegelt aus dem [NM] DESIGN SYSTEM v1.3, wie es die
Figma-Seite »Portfolio« nutzt. Dieses Modul gibt sie weiter:

  - css()          @font-face, :root-Variablen und die Textklassen .t-*
  - stil()         ein Textstil in Punkt, für die Zeilenmessung im Renderskript
  - pruefe()       hält portfolio.css frei von eigenen Farb- und Schriftwerten
  - pruefe_pdf()   jede Textstelle im PDF gegen die erlaubten Schnitte und Grade
  - vergleiche_figma()  die Tokens gegen einen Auszug aus Figma

Wer einen Wert ändern will, ändert ihn in tokens.json. Ein Farbwert oder eine
Schriftgröße direkt im CSS wird beim nächsten Rendern gemeldet.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TOKENS = ASSETS / "tokens.json"
FONTS = ASSETS / "fonts"
CSS_DATEI = ASSETS / "portfolio.css"

# Die Überschriften der Arbeitsweise-Seiten dürfen kleiner gesetzt werden, wenn
# ein Titel bei 96pt mehr als drei Zeilen bräuchte (render_portfolio.kopfmass).
# Diese Grade sind deshalb im PDF erlaubt, obwohl kein eigener Stil sie führt.
H1_AUSWEICHGRADE = (84, 72, 64)

SCHNITTNAME = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}

_cache: dict | None = None


def laden() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(TOKENS.read_text(encoding="utf-8"))
    return _cache


def varname(token: str) -> str:
    """"brand/primary" -> "--brand-primary"."""
    return "--" + re.sub(r"[^a-z0-9]+", "-", token.lower()).strip("-")


def _zahl(wert) -> str:
    return f"{float(wert):g}"


def _zeilenhoehe_css(wert: str) -> str:
    wert = str(wert)
    if wert.endswith("%"):
        return _zahl(float(wert[:-1]) / 100)
    if wert.endswith("pt"):
        return f"{_zahl(wert[:-2])}pt"
    raise ValueError(f"Zeilenhöhe ohne Einheit: {wert!r}")


def _laufweite_css(wert) -> str:
    if not wert:
        return "0"
    wert = str(wert)
    if wert.endswith("%"):
        return f"{_zahl(float(wert[:-1]) / 100)}em"
    if wert.endswith("pt"):
        return f"{_zahl(wert[:-2])}pt"
    raise ValueError(f"Laufweite ohne Einheit: {wert!r}")


def stil(name: str) -> dict:
    """Ein Textstil mit fertig gerechneten Punktwerten - für die Zeilenmessung.
    `laufweite` ist der Punktwert je Zeichen (negativ = enger)."""
    s = laden()["textstile"][name]
    grad = float(s["groesse"])
    zh = str(s["zeilenhoehe"])
    zeile = grad * float(zh[:-1]) / 100 if zh.endswith("%") else float(zh[:-2])
    lw = str(s.get("laufweite") or 0)
    if lw.endswith("%"):
        lauf = grad * float(lw[:-1]) / 100
    elif lw.endswith("pt"):
        lauf = float(lw[:-2])
    else:
        lauf = float(lw)
    datei = laden()["schriftdateien"][s["familie"]][str(s["gewicht"])]["datei"]
    return {"datei": datei, "pfad": FONTS / datei, "familie": s["familie"],
            "gewicht": int(s["gewicht"]), "groesse": grad, "zeile": zeile,
            "zeilenfaktor": zeile / grad, "laufweite": lauf,
            "laufweite_anteil": lauf / grad, "versalien": bool(s.get("versalien"))}


def _linien(t: dict) -> dict[str, str]:
    """Konturen als CSS-Variablen. Figma legt eine Kontur nach innen, die Fläche
    bleibt so groß wie ohne. Im CSS ist sie ein border - damit der Inhalt dort
    bleibt, wo er in Figma steht, wird der Innenabstand um die Stärke kleiner:
    --karte-innen-gerahmt."""
    aus = {}
    for name, l in (t.get("linien") or {}).items():
        if name.startswith("_"):
            continue
        if l.get("farbe") not in t["farben"]:
            continue          # pruefe() meldet das; ohne Farbe keine Variable
        aus[f"--linie-{name}"] = f"{_zahl(l['staerke'])}pt solid var({varname(l['farbe'])})"
        aus[f"--linie-{name}-staerke"] = f"{_zahl(l['staerke'])}pt"
    karte = (t.get("linien") or {}).get("karte")
    if karte and "karte-innen" in t["masse"]:
        aus["--karte-innen-gerahmt"] = f"{_zahl(float(t['masse']['karte-innen']) - float(karte['staerke']))}pt"
    return aus


def css() -> str:
    """@font-face, :root und .t-*: das, was portfolio.css voraussetzt."""
    t = laden()
    teile = []
    for familie, schnitte in t["schriftdateien"].items():
        for gewicht, eintrag in schnitte.items():
            uri = (FONTS / eintrag["datei"]).as_uri()
            teile.append(f'@font-face {{ font-family: "{familie}"; font-weight: {gewicht}; '
                         f'src: url("{uri}"); }}')
    root = [f"  {varname(n)}: {w};" for n, w in t["farben"].items()]
    root += [f"  {varname(n)}: {_zahl(w)}pt;" for n, w in t["masse"].items()]
    root += [f"  {n}: {w};" for n, w in _linien(t).items()]
    for name, v in (t.get("verlaeufe") or {}).items():
        r, g, b = (int(v["farbe"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        root.append(f"  {varname(name)}: linear-gradient(rgba({r},{g},{b},{_zahl(v['von'])}), "
                    f"rgba({r},{g},{b},{_zahl(v['bis'])}));")
        root.append(f"  {varname(name + '-hoehe')}: {_zahl(v['hoehe'])}pt;")
    teile.append(":root {\n" + "\n".join(root) + "\n}")
    for name, s in t["textstile"].items():
        regel = (f'font-family: "{s["familie"]}"; font-weight: {s["gewicht"]}; '
                 f'font-size: {_zahl(s["groesse"])}pt; '
                 f'line-height: {_zeilenhoehe_css(s["zeilenhoehe"])}; '
                 f'letter-spacing: {_laufweite_css(s.get("laufweite"))};')
        if s.get("versalien"):
            regel += " text-transform: uppercase;"
        teile.append(f".t-{name} {{ {regel} }}")
    # Fett im Fliesstext ist der Bold-Stil des Design Systems: Inter Semi Bold.
    teile.append(f"b, strong {{ font-weight: {t['fett']}; }}")
    return "\n".join(teile) + "\n"


# ── Prüfungen ────────────────────────────────────────────────────────────

_SCHRIFT_PROPS = ("font-family", "font-size", "font-weight", "line-height", "letter-spacing")


def pruefe(css_text: str | None = None) -> list[str]:
    """Hält den Skill an seine Tokens. Liefert Befunde, ändert nichts."""
    t = laden()
    befunde = []
    for familie, schnitte in t["schriftdateien"].items():
        for gewicht, eintrag in schnitte.items():
            if not (FONTS / eintrag["datei"]).exists():
                befunde.append(f"Schriftdatei fehlt: assets/fonts/{eintrag['datei']} "
                               f"({familie} {gewicht})")
    for name, s in t["textstile"].items():
        schnitte = t["schriftdateien"].get(s["familie"], {})
        if str(s["gewicht"]) not in schnitte:
            befunde.append(f"Textstil {name}: für {s['familie']} {s['gewicht']} "
                           "ist keine Schriftdatei hinterlegt.")

    if css_text is None:
        css_text = CSS_DATEI.read_text(encoding="utf-8")
    ohne_kommentar = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
    for nr, zeile in enumerate(ohne_kommentar.splitlines(), 1):
        if re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", zeile):
            befunde.append(f"portfolio.css Zeile {nr}: Farbwert direkt im CSS – "
                           f"gehört als Token in tokens.json: {zeile.strip()}")
        ohne_var = re.sub(r"var\([^)]*\)", "", zeile)
        if re.search(r"(?<![\w-])(color|background|border[\w-]*)\s*:[^;]*\b(white|black)\b", ohne_var):
            befunde.append(f"portfolio.css Zeile {nr}: Farbname statt Token: {zeile.strip()}")
        for prop in _SCHRIFT_PROPS:
            if re.search(rf"(?<![\w-]){prop}\s*:", zeile):
                befunde.append(f"portfolio.css Zeile {nr}: {prop} direkt im CSS – "
                               f"Schrift kommt nur über die .t-*-Klassen: {zeile.strip()}")
    definiert = {varname(n) for n in t["farben"]} | {varname(n) for n in t["masse"]}
    definiert |= set(_linien(t))
    for name, l in (t.get("linien") or {}).items():
        if not name.startswith("_") and l.get("farbe") not in t["farben"]:
            befunde.append(f"tokens.json: Linie {name} nutzt die Farbe {l.get('farbe')!r}, "
                           "die unter »farben« fehlt.")
    for n in t.get("verlaeufe") or {}:
        definiert |= {varname(n), varname(n + "-hoehe")}
    for name in sorted(set(re.findall(r"var\((--[\w-]+)\)", ohne_kommentar))):
        if name not in definiert:
            befunde.append(f"portfolio.css nutzt {name}, tokens.json kennt die Variable nicht.")
    return befunde


def _schnitt_kennung(name: str) -> str:
    """PDF-Schriftname -> vergleichbare Kennung ("ABCDEF+Rethink-Sans-Semi-Bold" -> "rethinksanssemibold").
    WeasyPrint nennt den Regular-Schnitt nur beim Familiennamen ("Inter"), deshalb
    fällt "regular" auf beiden Seiten weg."""
    name = name.split("+", 1)[-1]
    return re.sub(r"[^a-z]", "", name.lower()).replace("regular", "")


def pruefe_pdf(pdf) -> list[str]:
    """Jede Textstelle im fertigen PDF muss einen Schnitt und Grad aus den
    Tokens tragen. Was davon abweicht, ist entweder ein Element ohne .t-*-Klasse
    oder ein Wert, der am Design System vorbei ins Dokument gekommen ist."""
    try:
        import fitz
    except ImportError:
        return ["PyMuPDF fehlt – die Schriftprüfung des PDFs wurde übersprungen."]
    t = laden()
    erlaubt = set()
    for name, s in t["textstile"].items():
        kennung = _schnitt_kennung(s["familie"] + SCHNITTNAME[int(s["gewicht"])])
        grade = [float(s["groesse"])]
        if name == "h1":
            grade += [float(g) for g in H1_AUSWEICHGRADE]
        for g in grade:
            erlaubt.add((kennung, round(g, 1)))
    fett = int(t["fett"])
    for name, s in t["textstile"].items():   # **fett** innerhalb eines Stils
        if int(s["gewicht"]) < fett:
            kennung = _schnitt_kennung(s["familie"] + SCHNITTNAME[fett])
            erlaubt.add((kennung, round(float(s["groesse"]), 1)))
    befunde, gesehen = [], set()
    with fitz.open(str(pdf)) as doc:
        for nr, seite in enumerate(doc, 1):
            for blk in seite.get_text("dict")["blocks"]:
                for zeile in blk.get("lines", []):
                    for sp in zeile.get("spans", []):
                        if not sp["text"].strip():
                            continue
                        paar = (_schnitt_kennung(sp["font"]), round(sp["size"], 1))
                        if paar in erlaubt or any(p[0] == paar[0] and abs(p[1] - paar[1]) <= 0.2
                                                  for p in erlaubt):
                            continue
                        if (nr, paar) in gesehen:
                            continue
                        gesehen.add((nr, paar))
                        befunde.append(f"Seite {nr}: »{sp['text'].strip()[:40]}« steht in "
                                       f"{sp['font'].split('+')[-1]} {sp['size']:.1f}pt – "
                                       "kein Textstil aus tokens.json.")
    return befunde


def vergleiche_figma(auszug: dict) -> list[str]:
    """Die Tokens gegen einen Auszug aus Figma. Der Auszug kommt aus dem
    Leseskript in references/layout.md (Abschnitt »Tokens gegen Figma prüfen«):
    {"farben": {"brand/primary": "#009193", …},
     "textstile": {"Headings/H1": {"familie": …, "gewicht": 600, "groesse": 96,
                   "zeilenhoehe": "108%", "laufweite": "-0.3%"}, …}}"""
    t = laden()
    befunde = []
    for name, wert in t["farben"].items():
        soll = (auszug.get("farben") or {}).get(name)
        if soll and soll.lower() != wert.lower():
            befunde.append(f"Farbe {name}: tokens.json {wert}, Figma {soll}")
    stile = auszug.get("textstile") or {}
    for name, s in t["textstile"].items():
        f = stile.get(s.get("figma", ""))
        if not f:
            continue
        for feld in ("familie", "gewicht", "groesse", "zeilenhoehe", "laufweite"):
            a, b = s.get(feld), f.get(feld)
            if feld in ("gewicht", "groesse"):
                gleich = b is None or abs(float(a) - float(b)) < 0.05
            elif feld == "laufweite":
                gleich = b is None or _laufweite_css(a) == _laufweite_css(b)
            else:
                gleich = b is None or str(a).lower() == str(b).lower()
            if not gleich:
                befunde.append(f"Textstil {name} ({s['figma']}): {feld} tokens.json {a!r}, Figma {b!r}")
    return befunde


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] not in ("pruefe", "css"):
        raise SystemExit(__doc__)
    if args[0] == "css":
        print(css())
        return
    befunde = pruefe()
    if "--pdf" in args:
        befunde += pruefe_pdf(args[args.index("--pdf") + 1])
    if "--figma" in args:
        auszug = json.loads(Path(args[args.index("--figma") + 1]).read_text(encoding="utf-8"))
        befunde += vergleiche_figma(auszug)
    if befunde:
        print("Abweichungen vom Design System:")
        for b in befunde:
            print(f"  - {b}")
        raise SystemExit(1)
    print("Alles aus tokens.json – keine Abweichung gefunden.")


if __name__ == "__main__":
    main()
