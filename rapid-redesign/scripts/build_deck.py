#!/usr/bin/env python3
"""Baut das Audit-Deck (index.html) aus einer deck.json.

    scripts/.venv/bin/python scripts/build_deck.py <deck.json> --out <site/index.html>

Zusammensetzung:
    templates/deck.head.html          Kopf: Titel, Fonts, <style>, Logo-Sprite, Mini-Nav
    + references/site-styles.css      kanonisches Stylesheet (unveraendert eingesetzt)
    + templates/slides/<typ>.html     je Eintrag in deck.json -> "slides"
    + templates/deck.tail.html        Deck-Navigation + Folien-Skript
    + references/admin-mode-snippet.html   Admin-/Edit-Modus (eine zentrale Quelle)

Das Skript erfindet nichts: Fehlt ein Platzhalter-Wert in der deck.json, bricht es
mit einer klaren Meldung ab, statt eine Luecke ins Deck zu rendern.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck_render import render, TemplateError  # noqa: E402
from deck_content import enrich, ContentError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"
REF = ROOT / "references"


def fail(msg):
    print(f"FEHLER: {msg}", file=sys.stderr)
    sys.exit(1)


_SECTION_RE = re.compile(r"^(<section\b[^>]*>)(.*)(</section>)$", re.S)


def _merge(basis, overrides):
    """Tiefe Mischung fuer Varianten-Overrides.

    Verschachtelte Objekte werden feldweise gemischt (Listen ganz ersetzt).
    Flach gemischt wuerde eine Variante, die nur `quick_wins.punkte` aendert,
    das Geschwisterfeld `quick_wins.titel` verlieren -- und die Vorlage bricht.
    """
    out = dict(basis)
    for k, v in (overrides or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _varianten_section(varianten):
    """[(attrs, inner_html), ...] -> eine <section> mit einem Wrapper je Variante."""
    outer = None
    teile = []
    for attrs, html in varianten:
        m = _SECTION_RE.match(html)
        if not m:
            raise ContentError("Varianten: Vorlage rendert keine einzelne <section>")
        if outer is None:
            outer = (m.group(1), m.group(3))
        teile.append(f"<div {attrs}>{m.group(2)}</div>")
    return outer[0] + "\n" + "\n".join(teile) + "\n" + outer[1]


def render_folie(slide, ctx_global, tpl_text, n_personas, publikum):
    """Rendert eine Folie.

    "personaVarianten": {"1": {...}, "2": {...}} -> Folie je PERSONA einmal
    rendern (Variante 0 = Basisfelder) und in EINE <section> packen: je Variante
    ein <div class="pv" data-persona-variant="i">, Nicht-Fokus hidden.

    "publikumVarianten": {"<key>": {...}} -> dasselbe je PUBLIKUM (wem wir
    praesentieren; deck.json braucht dann "publikum": {aktiv, optionen}).
    Wrapper: <div class="av" data-audience-variant="key" data-audience-label>.

    Die Admin-Schalter toggeln nur diese Sichtbarkeit -- so wechseln die TEXTE
    mit, ohne dass im Browser Markup erzeugt werden muss. Beides auf EINER
    Folie ist nicht erlaubt (Kombinatorik waere nicht pflegbar)."""
    pv = slide.get("personaVarianten")
    av = slide.get("publikumVarianten")
    base = {k: v for k, v in slide.items() if k not in ("personaVarianten", "publikumVarianten")}

    # BEIDE Achsen (z. B. Wireframes: Notizen je Publikum, Ausrichtung je Persona)
    # -> geschachtelt rendern: aussen Publikum, innen Persona. Beide Admin-Schalter
    # toggeln ihre Ebene unabhaengig; sichtbar ist nur, was auf BEIDEN Ebenen passt.
    if pv and av:
        if n_personas < 2:
            raise ContentError("personaVarianten gesetzt, aber keine persona-Folie mit >=2 Personas im Deck")
        if not publikum or "aktiv" not in publikum or len(publikum.get("optionen", [])) < 2:
            raise ContentError('publikumVarianten gesetzt, aber kein "publikum" im Deck')
        aktiv = publikum["aktiv"]
        outer = None
        aussen = []
        for opt in publikum["optionen"]:
            key, label = opt["key"], opt["label"]
            a_basis = base if key == aktiv else _merge(base, av.get(key))
            innen = []
            for i in range(n_personas):
                merged = _merge(a_basis, pv.get(str(i)))
                html = render(tpl_text, {**ctx_global, **enrich(merged)}).strip()
                m = _SECTION_RE.match(html)
                if not m:
                    raise ContentError("Varianten: Vorlage rendert keine einzelne <section>")
                if outer is None:
                    outer = (m.group(1), m.group(3))
                p_hid = "" if i == 0 else " hidden"
                innen.append(f'<div class="pv" data-persona-variant="{i}"{p_hid}>{m.group(2)}</div>')
            a_hid = "" if key == aktiv else " hidden"
            aussen.append(
                f'<div class="av" data-audience-variant="{key}" data-audience-label="{label}"{a_hid}>'
                + "\n".join(innen) + "</div>")
        return outer[0] + "\n" + "\n".join(aussen) + "\n" + outer[1]

    if pv:
        if n_personas < 2:
            raise ContentError("personaVarianten gesetzt, aber keine persona-Folie mit >=2 Personas im Deck")
        varianten = []
        for i in range(n_personas):
            merged = _merge(base, pv.get(str(i)))
            html = render(tpl_text, {**ctx_global, **enrich(merged)}).strip()
            hid = "" if i == 0 else " hidden"
            varianten.append((f'class="pv" data-persona-variant="{i}"{hid}', html))
        return _varianten_section(varianten)

    if av:
        if not publikum or "aktiv" not in publikum or len(publikum.get("optionen", [])) < 2:
            raise ContentError('publikumVarianten gesetzt, aber kein "publikum" '
                               '({aktiv, optionen:[{key,label},...]}) im Deck')
        aktiv = publikum["aktiv"]
        varianten = []
        for opt in publikum["optionen"]:
            key, label = opt["key"], opt["label"]
            merged = base if key == aktiv else _merge(base, av.get(key))
            html = render(tpl_text, {**ctx_global, **enrich(merged)}).strip()
            hid = "" if key == aktiv else " hidden"
            varianten.append(
                (f'class="av" data-audience-variant="{key}" data-audience-label="{label}"{hid}', html))
        return _varianten_section(varianten)

    return render(tpl_text, {**ctx_global, **enrich(base)})


def build(deck_path, out_path):
    deck_path = Path(deck_path)
    if not deck_path.exists():
        fail(f"{deck_path} nicht gefunden")

    try:
        deck = json.loads(deck_path.read_text())
    except json.JSONDecodeError as e:
        fail(f"{deck_path} ist kein gueltiges JSON: {e}")

    for key in ("client", "slides"):
        if key not in deck:
            fail(f'"{key}" fehlt in {deck_path.name}')
    for key in ("domain", "farbe", "farbe2", "ink"):
        if key not in deck["client"]:
            fail(f'"client.{key}" fehlt in {deck_path.name}')

    styles = (REF / "site-styles.css").read_text().strip()
    admin = (REF / "admin-mode-snippet.html").read_text().strip()

    ctx_global = {k: v for k, v in deck.items() if k != "slides"}

    # --- Kopf ---
    head_tpl = (TPL / "deck.head.html").read_text()
    try:
        parts = [render(head_tpl, {**ctx_global, "STYLES": styles})]
    except TemplateError as e:
        fail(f"deck.head.html: {e}")

    # Persona-Anzahl fuer personaVarianten (aus der persona-Folie abgeleitet)
    n_personas = 0
    for s in deck["slides"]:
        if s.get("type") == "persona" and isinstance(s.get("personas"), list):
            n_personas = len(s["personas"])
            break

    # --- Folien ---
    for n, slide in enumerate(deck["slides"], 1):
        if "type" not in slide:
            fail(f'Folie {n}: "type" fehlt')
        typ = slide["type"]
        tpl_file = TPL / "slides" / f"{typ}.html"
        if not tpl_file.exists():
            vorhanden = sorted(p.stem for p in (TPL / "slides").glob("*.html"))
            fail(f'Folie {n}: unbekannter type "{typ}".\n  Verfuegbar: {", ".join(vorhanden)}')

        try:
            html = render_folie(slide, ctx_global, tpl_file.read_text(), n_personas,
                                deck.get("publikum"))
        except (TemplateError, ContentError) as e:
            fail(f'Folie {n} (type "{typ}"): {e}')

        parts.append(f"\n<!-- {n} {typ.upper()} -->\n{html.strip()}\n")

    # --- Fuss ---
    # Build-Kennung: der Admin-Modus verwirft gespeicherte Aenderungen, die zu
    # einem aelteren Build gehoeren -- sonst ueberschreibt der localStorage-Stand
    # die frisch gebauten Folien.
    stempel = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()[:12]
    parts.append(f'\n<script>window.NM_BUILD="{stempel}";</script>\n')
    parts.append("\n" + (TPL / "deck.tail.html").read_text().strip() + "\n")
    parts.append("\n" + baue_katalog() + "\n")
    parts.append("\n" + admin + "\n")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(parts))

    n_assets = kopiere_agentur_assets(out_path.parent / "assets")

    print(f"✓ {out_path}  ({len(deck['slides'])} Folien, {out_path.stat().st_size // 1024} KB, "
          f"{n_assets} Agentur-Assets)")


def nur_vorschau(html):
    """Bedienelemente aus einer Katalog-Miniatur entfernen.

    Zwei Gruende, beide zwingend:
    1. Der Katalog-Eintrag ist selbst ein <button>. Ein <button> darin waere
       verschachtelt = ungueltiges HTML -- der Parser loest ihn heraus, die
       Kachel verliert ihr Label und ein Streu-Button landet im Menue.
       (Genau das passierte mit "Alle aufklappen" auf der Vorgehen-Folie.)
    2. Eine Vorschau soll den Aufbau zeigen, nicht bedienbar sein.
    """
    return re.sub(r"<button\b[^>]*>.*?</button>", "", html, flags=re.S | re.I)


def baue_katalog():
    """Abschnitts-Katalog fuer den Admin-Modus einbacken.

    Der Admin laeuft im Browser und kann templates/slides/ nicht lesen. Damit
    "Abschnitt hinzufuegen" echte, fertig gestylte Folien anbietet statt drei
    generischer Bloecke, rendert der Build jeden Typ mit Platzhalter-Inhalt
    (templates/catalog.json) und legt das Ergebnis als window.NM_SECTION_CATALOG ab.
    """
    kat_file = TPL / "catalog.json"
    if not kat_file.exists():
        return ""
    kat = json.loads(kat_file.read_text())

    eintraege = []
    for typ, cfg in kat.items():
        if typ.startswith("_"):
            continue
        tpl_file = TPL / "slides" / f"{typ}.html"
        if not tpl_file.exists():
            print(f"  ⚠ Katalog: keine Vorlage fuer '{typ}' – uebersprungen", file=sys.stderr)
            continue
        try:
            html = render(tpl_file.read_text(), enrich({"type": typ, **cfg.get("content", {})}))
        except (TemplateError, ContentError) as e:
            print(f"  ⚠ Katalog: '{typ}' nicht renderbar ({e}) – uebersprungen", file=sys.stderr)
            continue
        eintraege.append({"typ": typ, "label": cfg.get("label", typ),
                          "html": nur_vorschau(html.strip())})

    if not eintraege:
        return ""
    return ("<script>window.NM_SECTION_CATALOG="
            + json.dumps(eintraege, ensure_ascii=False)
            + ";</script>")


def kopiere_agentur_assets(ziel):
    """Bilder/Logos/Grafiken der FIXEN Agentur-Folien bereitstellen.

    Die gehoeren zur Vorlage, nicht zum Projekt -- deshalb kopiert der Build sie
    selbst, statt sich darauf zu verlassen, dass jemand daran denkt. Vorhandene
    Dateien werden ueberschrieben, damit eine Korrektur an der Quelle (z. B. ein
    entzerrtes Logo) in jedem neuen Build ankommt.
    """
    quelle = REF / "assets"
    if not quelle.is_dir():
        return 0
    n = 0
    for src in quelle.rglob("*"):
        if src.is_dir():
            continue
        dst = ziel / src.relative_to(quelle)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="Audit-Deck aus deck.json bauen")
    ap.add_argument("deck", help="Pfad zur deck.json")
    ap.add_argument("--out", required=True, help="Ziel, z. B. audits/<domain>-<datum>/site/index.html")
    a = ap.parse_args()
    build(a.deck, a.out)


if __name__ == "__main__":
    main()
