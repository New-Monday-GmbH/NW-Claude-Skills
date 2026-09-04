#!/usr/bin/env python3
"""Ergaenzt alle fehlenden Logos einer portfolio.json in einem Durchgang.

    python3 scripts/logos_ergaenzen.py portfolio.json
    python3 scripts/logos_ergaenzen.py portfolio.json --domains domains.json

Betroffen sind drei Stellen: die Logowand "Meine Kunden", das Kundenlogo ueber
jedem Projektblock und die Werkzeugreihe der KI-Folie (person.ki.tools). Je
Firma zuerst die gemeinsame Bibliothek (kostet nichts und ist schon geprueft),
dann die Quellenkette aus fetch_logo.py.

In person.ki.tools duerfen blosse Werkzeugnamen stehen ("ChatGPT", "Claude",
"Midjourney") - sie werden hier gegen echte SVGs aufgeloest und durch den
Dateinamen ersetzt. Die Werkzeugreihe zeigt immer das Originallogo in
Originalfarben: Simple Icons fuehrt praktisch jedes KI-Werkzeug, liefert aber
grundsaetzlich einfarbig Schwarz - das genuegt nur fuer Marken, die selbst
schwarz auftreten; fuer farbige Marken (Claude, Gemini, Perplexity ...)
gehoert die farbige Original-Variante in die Bibliothek, bevor gerendert
wird. Werkzeuglogos werden nie selbst gezeichnet: selbst gebaute SVGs sassen
sichtbar verschoben in den Kacheln der KI-Folie.

Das Feld "logo" eines Projekts darf eine Liste sein (mehrere Auftraggeber).
Listen pflegt der Mensch: Dieses Skript befuellt nur Einzelwerte und meldet
Mehrmarken-Kunden als offen, statt still ein einzelnes Logo zu setzen.

domains.json ist optional und ordnet Firmennamen Domains zu - Brandfetch,
logo.dev und der Favicon-Dienst brauchen eine Domain, Wikimedia nicht:

    { "Yareto": "yareto.de", "apoBank": "apobank.de" }

Am Ende steht ein Bericht. Offene Logos sind kein Fehler: Die Wand rueckt
zusammen und die Projektseite rendert ohne - aber sie gehoeren in die Uebergabe,
damit jemand sie nachliefern kann.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_logo import ZIEL, als_bild, als_svg, bibliothek_bereit, slugify  # noqa: E402
import fetch_logo  # noqa: E402

RECHTSFORMEN = ("gmbh & co. kg", "gmbh", "ag", "eg", "se", "kg", "ohg", "plc",
                "inc", "ltd", "mbh", "e.v.", "ug")


def slugs(firma):
    """Kandidaten fuer den Dateinamen, vom Genauen zum Groben."""
    name = firma.split(",")[0].strip()
    grund = re.sub(r"[^\w\s&-]", "", name.lower())
    ohne_form = grund
    for form in RECHTSFORMEN:
        ohne_form = re.sub(rf"\b{re.escape(form)}\b", "", ohne_form)
    ergebnis = []
    for k in (grund, ohne_form.strip(), ohne_form.split("&")[0].strip()):
        s = slugify(k)
        if s and s not in ergebnis:
            ergebnis.append(s)
    return ergebnis


def aus_bibliothek(firma):
    aliase = ZIEL / "aliase.json"
    if aliase.exists():
        karte = json.loads(aliase.read_text(encoding="utf-8"))
        for schluessel, datei in karte.items():
            if schluessel.lower() in firma.lower() and (ZIEL / datei).exists():
                return datei
    vorhanden = {p.stem: p.name for p in ZIEL.iterdir()
                 if p.suffix in (".svg", ".png")}
    for s in slugs(firma):
        if s in vorhanden:
            return vorhanden[s]
        for stem, datei in vorhanden.items():      # "team" trifft "team-gmbh"
            if stem.startswith(s + "-") or s.startswith(stem + "-"):
                return datei
    return None


def suchen(firma, domain):
    name = slugs(firma)[-1] or slugs(firma)[0]
    tmp = ZIEL / f".suche-{name}"
    for quelle in fetch_logo.QUELLEN:
        try:
            ergebnis = quelle(firma, domain)
        except Exception:
            continue
        if not ergebnis:
            continue
        daten, endung, woher = ergebnis
        tmp.write_bytes(daten)
        try:
            ziel = als_svg(tmp, name) if endung == "svg" else als_bild(tmp, name)
            return ziel.name, woher
        except Exception:
            continue
        finally:
            tmp.unlink(missing_ok=True)
    tmp.unlink(missing_ok=True)
    return None, None


def eintraege(daten):
    """Alle Stellen, die ein Logo tragen koennen, als (Knoten, Namensfeld)."""
    for k in daten.get("kunden", []):
        if isinstance(k, dict) and k.get("name"):
            yield k, "name"
    for p in daten.get("projekte", []):
        if p.get("kunde"):
            yield p, "kunde"


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pfad = Path(sys.argv[1])
    domains = {}
    if "--domains" in sys.argv:
        domains = json.loads(Path(sys.argv[sys.argv.index("--domains") + 1])
                             .read_text(encoding="utf-8"))
    bibliothek_bereit()
    daten = json.loads(pfad.read_text(encoding="utf-8"))

    aus_lib, neu, offen = [], [], []
    for knoten, feld in eintraege(daten):
        logo = knoten.get("logo")
        if isinstance(logo, list):
            # Listen (mehrere Auftraggeber) pflegt der Mensch: teilbefuellte
            # nie ueberschreiben, leere melden statt still zu befuellen.
            if not any(logo):
                offen.append(f"{knoten[feld]} (Logo-Liste leer - Marken einzeln nachtragen)")
            continue
        if logo:
            continue
        firma = knoten[feld]
        if feld == "kunde" and re.search(r", | und | & ", firma):
            offen.append(f"{firma} (mehrere Marken - logo als Liste von Hand pflegen)")
            continue
        treffer = aus_bibliothek(firma)
        if treffer:
            knoten["logo"] = treffer
            aus_lib.append(f"{firma} -> {treffer}")
            continue
        datei, woher = suchen(firma, domains.get(firma))
        if datei:
            knoten["logo"] = datei
            neu.append(f"{firma} -> {datei} ({woher})")
        else:
            offen.append(firma)

    # Die Werkzeugreihe der KI-Folie: Eintraege ohne Dateiendung sind
    # Werkzeugnamen und werden wie Firmen aufgeloest. Eintraege mit Endung
    # bleiben stehen - sie sind schon Dateinamen.
    werkzeuge = ((daten.get("person") or {}).get("ki") or {}).get("tools") or []
    for i, werkzeug in enumerate(werkzeuge):
        if not isinstance(werkzeug, str) or werkzeug.lower().endswith(
                (".svg", ".png", ".jpg", ".jpeg")):
            continue
        treffer = aus_bibliothek(werkzeug)
        if treffer:
            werkzeuge[i] = treffer
            aus_lib.append(f"KI-Werkzeug {werkzeug} -> {treffer}")
            continue
        datei, woher = suchen(werkzeug, domains.get(werkzeug))
        if datei:
            werkzeuge[i] = datei
            neu.append(f"KI-Werkzeug {werkzeug} -> {datei} ({woher})")
        else:
            offen.append(f"KI-Werkzeug {werkzeug}")

    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    if aus_lib:
        print("Aus der Bibliothek:")
        for z in aus_lib:
            print("  " + z)
    if neu:
        print("Neu gefunden (bitte ansehen — die Suche trifft manchmal daneben):")
        for z in neu:
            print("  " + z)
    if offen:
        print("Offen — erst selbst im Netz suchen (Presse-/Markenbereich der Firma),")
        print("dann add_logo.py mit Datei oder URL aufrufen:")
        for z in offen:
            print("  " + z)
    print(f"\nBibliothek: {ZIEL}")


if __name__ == "__main__":
    main()
