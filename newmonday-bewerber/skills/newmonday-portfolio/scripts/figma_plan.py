#!/usr/bin/env python3
"""Baut aus portfolio.json die Figma-Frames des Portfolios – als fertige
use_figma-Skripte, gerechnet aus demselben Layout wie das PDF.

    python3 scripts/figma_plan.py portfolio.json arbeit/figma/ [--knoten 12-34] [--folien 2,5]
    python3 scripts/figma_plan.py --einsetzen arbeit/figma/ --seite 12:3 --rahmen 12:40

Erster Aufruf schreibt nach arbeit/figma/:
    plan.json        alle Folien mit ihren Ebenen in Punkt (zur Kontrolle)
    00-start.js      Zielseite und Sammelrahmen anlegen - der erste use_figma-Aufruf
    01-folien.js …   je Paket einige Folien, bereit für use_figma
    99-bilder.js     sammelt am Ende die Bildflächen in Upload-Reihenfolge ein
    bilder/          die Rasterbilder, auf ihren sichtbaren Ausschnitt beschnitten
    bilder.json      je Bildfläche: Nummer, Datei, Füllmodus

Der zweite Aufruf (--einsetzen) trägt die IDs aus 00-start.js in die
Folien-Skripte ein. Wie es danach weitergeht, steht in references/figma.md.

--folien baut nur die genannten Folien – für ein Deck, das in Figma schon
steht: Mit den IDs seines Sammelrahmens eingesetzt, ersetzt jedes Paket die
gleichnamige Folie ("02") an derselben Stelle. 99-bilder.js sammelt nur
Bildflächen ein, die noch leer sind.

Warum aus dem Layout und nicht aus eigenen Maßen: Das Renderskript baut das
HTML, WeasyPrint rechnet daraus jede Position, jede Zeile, jeden Umbruch. Genau
diese Rechnung wird hier ausgelesen - dieselbe, aus der das PDF entsteht. Der
Figma-Frame kann dem PDF deshalb nicht davonlaufen: Es gibt keine zweite
Maßtabelle, die jemand vergessen könnte nachzuziehen.
"""
from __future__ import annotations

import io
import json
import math
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_tokens as ds  # noqa: E402
import render_portfolio as rp  # noqa: E402

PT = 0.75                      # WeasyPrint rechnet in CSS-px, Figma hier in pt
CODE_GRENZE = 44000            # use_figma nimmt 50 000 Zeichen je Aufruf
SVG_INLINE_MAX = 12000         # größere SVGs gehen als Rasterbild hinein
SVG_FOLIE_MAX = 26000          # Summe der Vektorlogos je Folie
BILD_FAKTOR = 2                # Rasterbilder mit 2 px je pt, wie die Screenflächen


def _p(wert: float) -> float:
    return round(wert * PT, 2)


def _farbe(c) -> tuple[str, float] | None:
    """tinycss2-Farbe -> ("#rrggbb", Deckkraft) oder None, wenn unsichtbar."""
    if c is None or getattr(c, "alpha", 0) == 0:
        return None
    r, g, b = c.to("srgb").coordinates
    klemme = lambda v: max(0, min(255, round(v * 255)))
    return "#%02x%02x%02x" % (klemme(r), klemme(g), klemme(b)), round(float(c.alpha), 3)


def _radius(style) -> list[float]:
    ecken = []
    for name in ("top_left", "top_right", "bottom_right", "bottom_left"):
        wert = style[f"border_{name}_radius"][0]
        ecken.append(_p(wert.value) if wert.unit == "px" else 0.0)
    return ecken


def _linien(box) -> tuple[dict | None, list[dict]]:
    """CSS-Rahmen einer Box. Rundum gleich -> Figma-Kontur (innen, wie in der
    Vorlage: die Fläche bleibt so groß wie die Border-Box). Nur einzelne Seiten
    (Trennlinie über einer Kenntnis) -> je Seite ein flaches Rechteck."""
    st = box.style
    seiten = {}
    for seite in ("top", "right", "bottom", "left"):
        breite = getattr(box, f"border_{seite}_width", 0) or 0
        if breite <= 0 or st[f"border_{seite}_style"] in ("none", "hidden"):
            continue
        if st[f"border_{seite}_style"] != "solid":
            rp.merke(f"Figma: Rahmen »{_name(box)}« ist {st[f'border_{seite}_style']} – "
                     "in Figma wird er durchgezogen.")
        c = st[f"border_{seite}_color"]
        farbe = _farbe(st["color"] if isinstance(c, str) else c)
        if farbe:
            seiten[seite] = (breite, farbe)
    if not seiten:
        return None, []
    werte = set(seiten.values())
    if len(seiten) == 4 and len(werte) == 1:
        breite, farbe = werte.pop()
        return {"c": farbe[0], "a": farbe[1], "w": _p(breite)}, []
    if any(_radius(st)):
        rp.merke(f"Figma: Rahmen »{_name(box)}« ist nicht rundum gleich, hat aber "
                 "Radien – in Figma werden daraus gerade Linien ohne Rundung.")
    x, y = box.border_box_x(), box.border_box_y()
    w, h = box.border_width(), box.border_height()
    flaechen = []
    for seite, (breite, farbe) in seiten.items():
        rx, ry, rw, rh = {"top": (x, y, w, breite), "bottom": (x, y + h - breite, w, breite),
                          "left": (x, y, breite, h), "right": (x + w - breite, y, breite, h)}[seite]
        flaechen.append({"t": "r", "n": f"{_name(box)}-linie", "x": _p(rx), "y": _p(ry),
                         "w": _p(rw), "h": _p(rh), "f": farbe, "g": None, "r": [0.0] * 4})
    return None, flaechen


def _verlauf(style) -> list | None:
    """Der einzige Verlauf der Folien (.bildschatten) läuft von oben nach unten."""
    for art, bild in style["background_image"]:
        if art != "linear-gradient" or bild is None:
            continue
        farben = [_farbe(c) or ("#000000", 0.0) for c in bild.colors]
        n = len(farben)
        return [{"pos": i / max(1, n - 1), "farbe": f[0], "a": f[1]} for i, f in enumerate(farben)]
    return None


def _datei(src: str | None) -> Path | None:
    if not src:
        return None
    if src.startswith("file:"):
        return Path(url2pathname(urlparse(src).path))
    return Path(src)


def _schnitt(familie: str, gewicht: int) -> str:
    """Der Figma-Stilname aus tokens.json: Inter schreibt „Semi Bold", Rethink
    Sans „SemiBold" - geraten wäre einer von beiden falsch."""
    schnitte = ds.laden()["schriftdateien"].get(familie, {})
    eintrag = schnitte.get(str(gewicht))
    if eintrag:
        return eintrag["figma"]
    naechster = min(schnitte, key=lambda g: abs(int(g) - gewicht)) if schnitte else None
    return schnitte[naechster]["figma"] if naechster else "Regular"


def _name(box) -> str:
    el = getattr(box, "element", None)
    if el is None:
        return "Ebene"
    klassen = [k for k in (el.get("class") or "").split() if not k.startswith("t-")]
    return klassen[0] if klassen else el.tag


# ── Layoutbaum lesen ─────────────────────────────────────────────────────

class Folie:
    def __init__(self, nr: int):
        self.nr = nr
        self.ebenen: list[dict] = []
        self.hintergrund = "#ffffff"


def _textsegmente(box, segmente: list):
    """TextBoxen einer Zeile einsammeln, auch durch <b> und <a> hindurch."""
    for kind in getattr(box, "children", []) or []:
        art = type(kind).__name__
        if art == "TextBox":
            st = kind.style
            farbe = _farbe(st["color"]) or ("#000000", 1.0)
            lauf = st["letter_spacing"]
            link = None
            el = getattr(kind, "element", None)
            if el is not None and el.tag == "a":
                link = el.get("href")
            segmente.append({
                "text": kind.text,
                "familie": st["font_family"][0],
                "schnitt": _schnitt(st["font_family"][0], int(st["font_weight"])),
                "grad": _p(st["font_size"]),
                "farbe": farbe[0], "a": farbe[1],
                "lauf": 0.0 if lauf == "normal" else _p(lauf),
                "link": link,
                "unterstrichen": "underline" in (st["text_decoration_line"] or ()),
            })
        elif art in ("InlineBox",):
            _textsegmente(kind, segmente)


def _zeilen_als_text(behaelter, zeilen, folie: Folie):
    """Ein Blockbehälter mit Zeilen wird ein Textknoten: gleiche Breite, gleiche
    Zeilenhöhe, dieselben Umbrüche (als harte Umbrüche übernommen - so bricht
    Figma nicht anders um als WeasyPrint)."""
    text_teile, bereiche, pos = [], [], 0
    for i, zeile in enumerate(zeilen):
        segmente: list = []
        _textsegmente(zeile, segmente)
        if i and text_teile:
            text_teile.append("\n")
            pos += 1
        zeilentext = "".join(s["text"] for s in segmente).rstrip()
        rest = len(zeilentext)
        for s in segmente:
            t = s["text"][:rest] if rest < len(s["text"]) else s["text"]
            rest -= len(t)
            if not t:
                continue
            bereiche.append({k: v for k, v in s.items() if k != "text"} | {"von": pos, "bis": pos + len(t)})
            pos += len(t)
            text_teile.append(t)
    text = "".join(text_teile)
    if not text.strip():
        return
    st = behaelter.style
    ausrichtung = {"center": "CENTER", "right": "RIGHT", "end": "RIGHT"}.get(
        str(st["text_align_all"]), "LEFT")
    x, breite = _p(behaelter.content_box_x()), _p(behaelter.width)
    # Zwei Punkt Luft, damit Figma eine randvolle Zeile nicht doch umbricht.
    if ausrichtung == "LEFT":
        breite += 2
    elif ausrichtung == "RIGHT":
        x, breite = x - 2, breite + 2
    else:
        x, breite = x - 1, breite + 2
    folie.ebenen.append({
        "t": "x", "n": _name(behaelter), "x": x, "y": _p(zeilen[0].position_y),
        "w": breite, "zh": _p(zeilen[0].height), "al": ausrichtung,
        "text": text, "seg": bereiche,
    })


def _bild(box, folie: Folie, bilder: list):
    el = box.element
    datei = _datei(el.get("src") if el is not None else None)
    if not datei or not datei.exists():
        return
    x, y = _p(box.content_box_x()), _p(box.content_box_y())
    w, h = _p(box.width), _p(box.height)
    if w < 1 or h < 1:
        return
    st = box.style
    passung = st["object_fit"] or "fill"
    position = st["object_position"]
    folie.ebenen.append({"t": "i", "n": _name(box), "x": x, "y": y, "w": w, "h": h,
                         "quelle": str(datei), "passung": passung,
                         "oben": _oben_verankert(position),
                         "anker": _verankerung(position), "folie": folie.nr})
    bilder.append(folie.ebenen[-1])


def _oben_verankert(position) -> bool:
    try:
        return position[0][2][0] in ("top",) or position[0][3].value == 0
    except Exception:
        return False


def _verankerung(position) -> tuple[float, float]:
    """object-position als Anteil (0 links/oben, 1 rechts/unten). Das
    Kundenlogo der Projektseiten steht links, alles andere mittig."""
    try:
        ox, lx, oy, ly = position[0]
        anteil = lambda ursprung, laenge, fern: (
            (laenge.value / 100 if laenge.unit == "%" else 0.0) if ursprung != fern
            else 1 - (laenge.value / 100 if laenge.unit == "%" else 0.0))
        return anteil(ox, lx, "right"), anteil(oy, ly, "bottom")
    except Exception:
        return 0.5, 0.5


VERZERRUNG_MAX = rp.LOGO_VERZERRUNG_MAX


def im_verhaeltnis(e: dict, quelle: Path, passung: str, anker, folie: int) -> None:
    """Ein Bild, das eingepasst statt beschnitten wird (Logos), bekommt in
    Figma ein Rechteck im Seitenverhaeltnis seiner Datei, gesetzt wie
    object-position im PDF. Dann passt FIT ohne Rand - und wer in Figma den
    Fuellmodus wechselt, verzerrt trotzdem nichts. Weicht die Flaeche aus dem
    Layout mehr als 1 % ab, wird das gemeldet: bei object-fit fill steht das
    Bild dann schon im PDF verzerrt. Eine gestauchte Datei findet diese
    Pruefung nicht - die faellt nur beim Ansehen gegen die Quelle auf."""
    v = rp.seitenverhaeltnis(quelle.as_uri())
    w, h = e["w"], e["h"]
    if abs((w / h) / v - 1) > VERZERRUNG_MAX:
        folge = ("steht im PDF verzerrt" if passung == "fill"
                 else "das Rechteck wird auf die Datei eingepasst")
        rp.merke(f"Figma: Bildfläche {quelle.name} auf Folie {folie:02d} ist "
                 f"{w:g} × {h:g} pt ({w / h:.2f}), die Datei {v:.2f} – {folge}.")
    neu_w, neu_h = (h * v, h) if w / h > v else (w, w / v)
    e["x"] = round(e["x"] + (w - neu_w) * anker[0], 2)
    e["y"] = round(e["y"] + (h - neu_h) * anker[1], 2)
    e["w"], e["h"] = round(neu_w, 2), round(neu_h, 2)


def _gehe(box, folie: Folie, bilder: list):
    innen = getattr(box, "_box", box)
    art = type(innen).__name__
    if art in ("InlineReplacedBox", "BlockReplacedBox"):
        _bild(innen, folie, bilder)
        return
    st = getattr(innen, "style", None)
    if st is not None and art not in ("LineBox", "TextBox", "InlineBox", "PageBox"):
        farbe = _farbe(st["background_color"])
        verlauf = _verlauf(st)
        kontur, linien = _linien(innen)
        if (farbe or verlauf or kontur) and innen.border_width() > 0 and innen.border_height() > 0:
            el = getattr(innen, "element", None)
            if el is not None and "seite" in (el.get("class") or "").split() and farbe:
                folie.hintergrund = farbe[0]
            else:
                eintrag = {
                    "t": "r", "n": _name(innen),
                    "x": _p(innen.border_box_x()), "y": _p(innen.border_box_y()),
                    "w": _p(innen.border_width()), "h": _p(innen.border_height()),
                    "f": farbe, "g": verlauf, "r": _radius(st)}
                if kontur:
                    eintrag["s"] = kontur
                folie.ebenen.append(eintrag)
        folie.ebenen.extend(linien)
    kinder = getattr(innen, "children", []) or []
    zeilen = [k for k in kinder if type(k).__name__ == "LineBox"]
    if zeilen:
        _zeilen_als_text(innen, zeilen, folie)
        for zeile in zeilen:                  # Bilder im Zeilenfluss (Foto, Logos)
            for kind in _inline_bilder(zeile):
                _bild(kind, folie, bilder)
    for kind in kinder:
        if type(kind).__name__ != "LineBox":
            _gehe(kind, folie, bilder)
    # Absolut positionierte Kinder hängen in WeasyPrint an den Zeilen.
    for zeile in zeilen:
        for kind in zeile.children or []:
            if type(kind).__name__ == "AbsolutePlaceholder":
                _gehe(kind, folie, bilder)


def _inline_bilder(box):
    for kind in getattr(box, "children", []) or []:
        art = type(kind).__name__
        if art == "InlineReplacedBox":
            yield kind
        elif art == "InlineBox":
            yield from _inline_bilder(kind)


def folien_lesen(html_text: str) -> tuple[list[Folie], list[dict]]:
    from weasyprint import HTML
    tmp = Path(tempfile.mkdtemp()) / "portfolio.html"
    tmp.write_text(html_text, encoding="utf-8")
    doc = HTML(filename=str(tmp)).render()
    folien, bilder = [], []
    for nr, seite in enumerate(doc.pages, 1):
        f = Folie(nr)
        _gehe(seite._page_box, f, bilder)
        folien.append(f)
    return folien, bilder


# ── Bilder vorbereiten ───────────────────────────────────────────────────

def _svg_budget(folien: list[Folie]) -> set[int]:
    """Welche SVG-Ebenen als Rasterbild gehen: alle über SVG_INLINE_MAX und, je
    Folie, die größten, bis die Folie unter SVG_FOLIE_MAX bleibt - eine
    Kundenwand aus zwölf Vektorlogos sprengt sonst allein den Code-Deckel."""
    raster = set()
    for f in folien:
        kandidaten = []
        for e in f.ebenen:
            q = e.get("quelle")
            if e["t"] == "i" and q and q.lower().endswith(".svg"):
                groesse = len(_svg_bereinigen(Path(q).read_text(encoding="utf-8", errors="replace")))
                if groesse > SVG_INLINE_MAX:
                    raster.add(id(e))
                else:
                    kandidaten.append((groesse, e))
        summe = sum(g for g, _ in {q_: (g, e) for g, e in kandidaten
                                    for q_ in [e["quelle"]]}.values())
        for groesse, e in sorted(kandidaten, key=lambda k: -k[0]):
            if summe <= SVG_FOLIE_MAX:
                break
            raster.add(id(e))
            summe -= groesse
    return raster


def bilder_vorbereiten(bilder: list[dict], ordner: Path, folien: list[Folie]) -> list[dict]:
    """Rasterbilder auf ihren sichtbaren Ausschnitt bringen (object-fit: cover
    mit derselben Verankerung wie im CSS), auf 2 px je pt begrenzen und einmal
    je Inhalt ablegen. Kleine SVGs bleiben Vektor und gehen direkt in den Code."""
    from PIL import Image
    ordner.mkdir(parents=True, exist_ok=True)
    liste, gesehen = [], {}
    als_raster = _svg_budget(folien)
    for e in bilder:
        raster = id(e) in als_raster
        quelle = Path(e.pop("quelle"))
        passung = e.pop("passung")
        oben = e.pop("oben")
        anker, folie = e.pop("anker"), e.pop("folie")
        if passung != "cover":
            im_verhaeltnis(e, quelle, passung, anker, folie)
        if quelle.suffix.lower() == ".svg":
            svg = _svg_bereinigen(quelle.read_text(encoding="utf-8", errors="replace"))
            if not raster:
                e["t"], e["svg"] = "s", svg
                continue
            bild = _svg_raster(quelle, e["w"], e["h"])
            passung = "contain"
        else:
            bild = Image.open(quelle)
            bild.load()
        schluessel = (str(quelle), passung, oben, round(e["w"]), round(e["h"]))
        if schluessel in gesehen:
            e["bild"] = gesehen[schluessel]
            continue
        ziel_b, ziel_h = e["w"] * BILD_FAKTOR, e["h"] * BILD_FAKTOR
        if passung == "cover":
            verh = e["w"] / e["h"]
            b, h = bild.size
            if b / h > verh:
                neu = round(h * verh)
                links = (b - neu) // 2
                bild = bild.crop((links, 0, links + neu, h))
            else:
                neu = round(b / verh)
                oben_px = 0 if oben else (h - neu) // 2
                bild = bild.crop((0, oben_px, b, oben_px + neu))
            modus = "FILL"
        else:
            modus = "FIT"
        faktor = min(1.0, ziel_b / bild.width, ziel_h / bild.height) if passung == "cover" \
            else min(1.0, max(ziel_b / bild.width, ziel_h / bild.height))
        if faktor < 1.0:
            bild = bild.resize((max(1, round(bild.width * faktor)),
                                max(1, round(bild.height * faktor))), Image.LANCZOS)
        nr = len(liste) + 1
        alpha = bild.mode in ("RGBA", "LA", "P")
        datei = ordner / (f"{nr:02d}.png" if alpha else f"{nr:02d}.jpg")
        if alpha:
            bild.convert("RGBA").save(datei)
        else:
            bild.convert("RGB").save(datei, quality=90)
        liste.append({"nr": nr, "datei": str(datei), "modus": modus, "quelle": str(quelle)})
        gesehen[schluessel] = nr
        e["bild"] = nr
    return liste


def _svg_bereinigen(svg: str) -> str:
    svg = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>|<!--.*?-->", "", svg, flags=re.S)
    return re.sub(r">\s+<", "><", svg).strip()


def _svg_raster(pfad: Path, w: float, h: float):
    """SVGs, die als Rasterbild gehen (zu groß für den Code-Deckel von
    use_figma), rendert WeasyPrint - derselbe Renderer wie im PDF. Der
    SVG-Leser von PyMuPDF zeichnete manche Logos falsch (HostEurope als
    schwarze Fläche, congstar ohne Pille); über WeasyPrint sieht das Bild in
    Figma so aus wie im PDF."""
    import fitz
    from PIL import Image
    from weasyprint import HTML
    html = (f'<html><head><style>@page{{size:{w}pt {h}pt;margin:0}}body{{margin:0}}'
            f'img{{display:block;width:{w}pt;height:{h}pt;object-fit:contain}}</style></head>'
            f'<body><img src="{pfad.resolve().as_uri()}"></body></html>')
    pdf = HTML(string=html).write_pdf()
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(BILD_FAKTOR, BILD_FAKTOR), alpha=True)
        return Image.open(io.BytesIO(pix.tobytes("png")))


# ── use_figma-Skripte schreiben ──────────────────────────────────────────

BAUER = r"""
const RAHMEN = await figma.getNodeByIdAsync("__RAHMEN__");
const SEITE = await figma.getNodeByIdAsync("__SEITE__");
if (!RAHMEN || !SEITE) throw new Error("IDs fehlen: erst figma_plan.py --einsetzen laufen lassen");
await figma.setCurrentPageAsync(SEITE);
const hx = h => ({ r: parseInt(h.slice(1, 3), 16) / 255, g: parseInt(h.slice(3, 5), 16) / 255, b: parseInt(h.slice(5, 7), 16) / 255 });
const fl = (h, a) => ({ type: "SOLID", color: hx(h), opacity: a == null ? 1 : a });
for (const f of P.schriften) await figma.loadFontAsync({ family: f[0], style: f[1] });
const angelegt = [];
for (const s of P.folien) {
  const F = figma.createFrame();
  F.name = s.name; F.resize(1920, 1080); F.clipsContent = true; F.fills = [fl(s.bg)];
  // Steht die Folie im Sammelrahmen schon (Neubau einzelner Folien, --folien),
  // kommt die neue an ihre Stelle, die alte geht.
  const alt = RAHMEN.children.find(c => c.name === s.name);
  if (alt) { RAHMEN.insertChild(RAHMEN.children.indexOf(alt), F); alt.remove(); }
  else RAHMEN.appendChild(F);
  angelegt.push(F.id);
  for (const e of s.e) {
    if (e.t === "r" || e.t === "i") {
      const r = figma.createRectangle();
      F.appendChild(r); r.name = e.t === "i" ? "bild:" + e.bild + " " + e.n : e.n;
      r.x = e.x; r.y = e.y; r.resize(Math.max(e.w, 0.01), Math.max(e.h, 0.01));
      if (e.t === "i") r.fills = [fl("#ebf2f5")];
      else if (e.g) r.fills = [{ type: "GRADIENT_LINEAR", gradientTransform: [[0, 1, 0], [-1, 0, 1]],
        gradientStops: e.g.map(g => ({ position: g.pos, color: { ...hx(g.farbe), a: g.a } })) }];
      else r.fills = e.f ? [fl(e.f[0], e.f[1])] : [];
      if (e.r) { r.topLeftRadius = e.r[0]; r.topRightRadius = e.r[1]; r.bottomRightRadius = e.r[2]; r.bottomLeftRadius = e.r[3]; }
      if (e.s) { r.strokes = [fl(e.s.c, e.s.a)]; r.strokeWeight = e.s.w; r.strokeAlign = "INSIDE"; }
    } else if (e.t === "s") {
      const n = figma.createNodeFromSvg(P.svg[e.svg]);
      F.appendChild(n); n.name = e.n;
      n.rescale(Math.min(e.w / n.width, e.h / n.height));
      n.x = e.x + (e.w - n.width) / 2; n.y = e.y + (e.h - n.height) / 2;
    } else if (e.t === "x") {
      const n = figma.createText();
      F.appendChild(n); n.name = e.n;
      const s0 = e.seg[0];
      n.fontName = { family: s0.familie, style: s0.schnitt };
      n.characters = e.text;
      n.lineHeight = { unit: "PIXELS", value: e.zh };
      for (const g of e.seg) {
        n.setRangeFontName(g.von, g.bis, { family: g.familie, style: g.schnitt });
        n.setRangeFontSize(g.von, g.bis, g.grad);
        n.setRangeFills(g.von, g.bis, [fl(g.farbe, g.a)]);
        n.setRangeLetterSpacing(g.von, g.bis, { unit: "PIXELS", value: g.lauf });
        if (g.link) n.setRangeHyperlink(g.von, g.bis, { type: "URL", value: g.link });
        if (g.unterstrichen) n.setRangeTextDecoration(g.von, g.bis, "UNDERLINE");
      }
      // Die Umbrüche sind harte Umbrüche aus dem PDF - Figma muss nie selbst
      // umbrechen. Mit fester Breite brach es trotzdem, wo es einen Hauch
      // breiter misst als WeasyPrint (Telefonnummer auf der Kontaktseite).
      n.textAlignHorizontal = e.al;
      n.textAutoResize = "WIDTH_AND_HEIGHT";
      n.x = e.al === "CENTER" ? e.x + (e.w - n.width) / 2 : e.al === "RIGHT" ? e.x + e.w - n.width : e.x;
      n.y = e.y;
    }
  }
}
return { folien: angelegt, rahmen: RAHMEN.id };
"""

START = r"""
// Zielseite: Knoten aus dem Link (node-id) -> dessen Seite; sonst neue Seite.
const KNOTEN = "__KNOTEN__";
let seite = null;
if (KNOTEN && !KNOTEN.startsWith("__")) {
  let n = await figma.getNodeByIdAsync(KNOTEN);
  while (n && n.type !== "PAGE") n = n.parent;
  seite = n;
}
if (!seite) { seite = figma.createPage(); seite.name = __NAME__; }
await figma.setCurrentPageAsync(seite);
const inter = (await figma.listAvailableFontsAsync()).map(f => f.fontName.family + "/" + f.fontName.style);
const fehlt = __SCHRIFTEN__.filter(f => !inter.includes(f[0] + "/" + f[1])).map(f => f.join(" "));
if (fehlt.length) throw new Error("Schriften fehlen in Figma: " + fehlt.join(", "));
const rechts = seite.children.length ? Math.max(...seite.children.map(n => n.x + n.width)) : 0;
const R = figma.createAutoLayout("VERTICAL", { name: __NAME__, itemSpacing: 300 });
R.fills = [];
// Sofort volle Breite - der nächste Rahmen misst sonst an einem leeren. resize()
// setzt beide Achsen auf FIXED; die Höhe muss danach wieder mitwachsen, sonst
// schneidet der Rahmen seine Folien auf 10 px ab.
R.resize(1920, 10); R.counterAxisSizingMode = "FIXED"; R.primaryAxisSizingMode = "AUTO";
R.clipsContent = false;
seite.appendChild(R);
R.x = seite.children.length > 1 ? rechts + 300 : 0; R.y = 0;
return { seite: seite.id, rahmen: R.id };
"""

EINSAMMELN = r"""
const MODUS = __MODUS__;   // Bildnummer -> FILL | FIT, aus bilder.json
const R = await figma.getNodeByIdAsync("__RAHMEN__");
const SEITE = await figma.getNodeByIdAsync("__SEITE__");
await figma.setCurrentPageAsync(SEITE);
// Nur Flächen, die noch den Platzhalter tragen - schon gefüllte (frühere Läufe,
// unveränderte Folien) bleiben, wie sie sind.
const flaechen = R.findAll(n => n.type === "RECTANGLE" && n.name.startsWith("bild:")
  && n.fills.length && n.fills[0].type === "SOLID");
const je = { FILL: [], FIT: [] };
for (const n of flaechen) { const nr = parseInt(n.name.slice(5)); je[MODUS[nr] || "FILL"].push([n.id, nr]); }
return je;   // als arbeit/figma/knoten.json speichern - Reihenfolge = Upload-Reihenfolge
"""


def skripte_schreiben(folien: list[Folie], name: str, ordner: Path) -> list[Path]:
    schriften = sorted({(g["familie"], g["schnitt"]) for f in folien for e in f.ebenen
                        if e["t"] == "x" for g in e["seg"]})
    (ordner / "00-start.js").write_text(
        START.replace("__NAME__", json.dumps(f"Portfolio — {name}"))
             .replace("__SCHRIFTEN__", json.dumps([list(s) for s in schriften])),
        encoding="utf-8")
    modus = {}
    liste_pfad = ordner / "bilder.json"
    if liste_pfad.exists():
        modus = {b["nr"]: b["modus"] for b in json.loads(liste_pfad.read_text(encoding="utf-8"))}
    (ordner / "99-bilder.js").write_text(EINSAMMELN.replace("__MODUS__", json.dumps(modus)),
                                        encoding="utf-8")

    # Pakete eines früheren Laufs im selben Ordner gehen weg: Mit --folien
    # ersetzt jedes Paket gleichnamige Folien, ein liegengebliebenes würde
    # Folien überschreiben, die gar nicht neu gebaut werden sollten.
    for alt in ordner.glob("[0-9][0-9]-folien.js"):
        alt.unlink()

    pakete, paket, svgs, groesse = [], [], {}, len(BAUER)
    def abschliessen():
        if paket:
            pakete.append((list(paket), dict(svgs)))
    for f in folien:
        eigene = {}
        ebenen = []
        for e in f.ebenen:
            e = dict(e)
            if e["t"] == "s":
                schl = f"s{abs(hash(e['svg'])) % 10**8}"
                eigene[schl] = e.pop("svg")
                e["svg"] = schl
            ebenen.append(e)
        eintrag = {"name": f"{f.nr:02d}", "bg": f.hintergrund, "e": ebenen}
        neu = len(json.dumps(eintrag, ensure_ascii=False, separators=(",", ":"))) + sum(
            len(v) for k, v in eigene.items() if k not in svgs)
        if paket and (groesse + neu > CODE_GRENZE or len(paket) >= 4):
            abschliessen()
            paket.clear(); svgs.clear(); groesse = len(BAUER)
        paket.append(eintrag)
        svgs.update(eigene)
        groesse += neu
    abschliessen()

    dateien = []
    for i, (liste, svg) in enumerate(pakete, 1):
        daten = {"schriften": [list(s) for s in schriften], "folien": liste, "svg": svg}
        code = "const P = " + json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + ";\n" + BAUER
        if len(code) > 50000:
            rp.merke(f"Figma-Paket {i} ist {len(code)} Zeichen lang – über dem Deckel von use_figma.")
        datei = ordner / f"{i:02d}-folien.js"
        datei.write_text(code, encoding="utf-8")
        dateien.append(datei)
    return dateien


def einsetzen(ordner: Path, seite: str, rahmen: str) -> None:
    for datei in sorted(ordner.glob("*.js")):
        if datei.name == "00-start.js":
            continue
        text = datei.read_text(encoding="utf-8")
        text = text.replace("__SEITE__", seite).replace("__RAHMEN__", rahmen)
        datei.write_text(text, encoding="utf-8")
    print(f"IDs eingesetzt: Seite {seite}, Rahmen {rahmen}")


def main() -> None:
    args = sys.argv[1:]
    if args[:1] == ["--einsetzen"]:
        ordner = Path(args[1])
        seite = args[args.index("--seite") + 1]
        rahmen = args[args.index("--rahmen") + 1]
        einsetzen(ordner, seite, rahmen)
        return
    if len(args) < 2:
        raise SystemExit(__doc__)
    knoten = args[args.index("--knoten") + 1].replace("-", ":") if "--knoten" in args else ""
    nur = None
    if "--folien" in args:
        i = args.index("--folien") + 1
        teile = [t.strip() for t in (args[i] if i < len(args) else "").split(",") if t.strip()]
        if not teile or not all(t.isdigit() and int(t) > 0 for t in teile):
            raise SystemExit("--folien erwartet Foliennummern mit Komma, z. B. --folien 2 "
                             "oder --folien 2,5")
        nur = {int(t) for t in teile}
    # Absolut: bilder.json nennt Dateipfade, die figma_assets.py von überall liest.
    quelle, ordner = Path(args[0]).resolve(), Path(args[1]).resolve()
    ordner.mkdir(parents=True, exist_ok=True)
    d = json.loads(quelle.read_text(encoding="utf-8"))
    html_text, _ = rp.baue_html(d, quelle.parent, rp.zwischenlager(quelle))
    folien, bilder = folien_lesen(html_text)
    # Vor dem ersten Schreiben: eine Foliennummer, die es nicht gibt, soll
    # keinen halben Plan im Ordner hinterlassen.
    auswahl = [f for f in folien if nur is None or f.nr in nur]
    if nur is not None and len(auswahl) != len(nur):
        raise SystemExit(f"--folien: das Deck hat {len(folien)} Folien – "
                         f"{sorted(nur - {f.nr for f in folien})} gibt es nicht.")
    liste = bilder_vorbereiten(bilder, ordner / "bilder", folien)
    name = (d.get("person") or {}).get("name") or "Portfolio"
    (ordner / "plan.json").write_text(json.dumps(
        [{"nr": f.nr, "hintergrund": f.hintergrund, "ebenen": f.ebenen} for f in folien],
        ensure_ascii=False, indent=1), encoding="utf-8")
    (ordner / "bilder.json").write_text(json.dumps(liste, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    dateien = skripte_schreiben(auswahl, name, ordner)
    if knoten:
        start = ordner / "00-start.js"
        start.write_text(start.read_text(encoding="utf-8").replace("__KNOTEN__", knoten),
                         encoding="utf-8")
    texte = sum(1 for f in auswahl for e in f.ebenen if e["t"] == "x")
    umfang = f"{len(auswahl)} von {len(folien)} Folien" if nur is not None else f"{len(folien)} Folien"
    print(f"{umfang}, {texte} Textknoten, {len(liste)} Rasterbilder, "
          f"{sum(1 for f in auswahl for e in f.ebenen if e['t'] == 's')} SVG-Knoten "
          f"-> {len(dateien)} Pakete in {ordner}")
    for h in dict.fromkeys(rp.hinweise):
        if "Figma" in h:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
