#!/usr/bin/env python3
"""Marktbild: was der Markt gerade sucht – aus den Anfrage-Läufen.

    marktbild.py offen
        Anfrage-Ordner, für die noch keine anforderungen/<ordner>.json existiert,
        und Begriffe in anforderungen/, die in begriffe.json fehlen.
    marktbild.py auswerten [--stichtag JJJJ-MM-TT]
        Zählt je Rollenfamilie, was in den letzten 6 Monaten gefordert war
        (gefragt = in mindestens 2 Ausschreibungen), prüft die PDFs in Originale/
        auf Lücken und schreibt <markt>/stand-<datum>/ mit marktbild.xlsx,
        bericht.md, marktbild.json, luecken.json. Gibt zuletzt drei Zeilen für die
        Mitteilung aus.
    marktbild.py luecken --kandidat "Vorname Nachname"
        Lücken des Kandidaten aus dem neuesten Stand als JSON.
    marktbild.py antwort --kandidat "…" --begriff "…" --antwort ja|ja_projekt|nein|weiss_nicht [--projekt "…"]
        Technik-Antwort des Nutzers ablegen (antworten/<Kandidat>.json).

Konfiguration: ~/.newmonday/marktbild.json (Vorlage marktbild.config.beispiel.json).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

KONFIG = Path(os.environ.get("MARKTBILD_KONFIG", Path.home() / ".newmonday" / "marktbild.json"))
FENSTER_TAGE = 183          # 6 Monate
MINDESTENS = 2              # gefragt ab so vielen Ausschreibungen
GEWICHT = {"muss": 2, "kann": 1}
SELBST = {"methode"}                                   # darf der Skill ableiten
FRAGEN = {"tool", "technik", "norm", "domaene"}        # nur mit Ja des Nutzers
ARTEN = SELBST | FRAGEN | {"sprache", "erfahrung", "sonstiges"}   # Rest: nur Marktbild
ANTWORTEN = {"ja", "ja_projekt", "nein", "weiss_nicht"}


# ---------- Daten laden ----------

def konfig() -> dict:
    if not KONFIG.exists():
        sys.exit(f"Konfiguration fehlt: {KONFIG} (Vorlage: marktbild.config.beispiel.json)")
    k = json.loads(KONFIG.read_text())
    for schluessel in ("ausschreibungen", "originale", "markt"):
        k[schluessel] = Path(k[schluessel]).expanduser()
    return k


def lies(pfad: Path, leer):
    return json.loads(pfad.read_text()) if pfad.exists() else leer


def anforderungen(markt: Path) -> list[dict]:
    return [json.loads(p.read_text()) | {"_datei": p.stem}
            for p in sorted((markt / "anforderungen").glob("*.json"))]


def pruefe_daten(anf: list[dict], begriffe: dict, vorgaben=()) -> list[str]:
    fehler = []
    for b, info in begriffe.items():
        if info.get("art") not in ARTEN:
            fehler.append(f"begriffe.json: „{b}“ hat unbekannte art {info.get('art')!r}")
    for v in vorgaben:
        if v.get("begriff") not in begriffe:
            fehler.append(f"vorgaben.json: „{v.get('begriff')}“ fehlt in begriffe.json")
    for a in anf:
        for feld in ("anfrage", "datum", "rollenfamilie", "anforderungen"):
            if feld not in a:
                fehler.append(f"anforderungen/{a['_datei']}.json: Feld {feld} fehlt")
        for r in a.get("anforderungen", []):
            if r.get("begriff") not in begriffe:
                fehler.append(f"anforderungen/{a['_datei']}.json: „{r.get('begriff')}“ fehlt in begriffe.json")
            if r.get("stufe") not in GEWICHT:
                fehler.append(f"anforderungen/{a['_datei']}.json: „{r.get('begriff')}“ stufe muss muss|kann sein")
        for name, liste in a.get("ergaenzt", {}).items():
            for b in liste:
                if b not in begriffe:
                    fehler.append(f"anforderungen/{a['_datei']}.json: ergaenzt {name}: „{b}“ fehlt in begriffe.json")
    return fehler


# ---------- Auswerten ----------

def marktbild(anf: list[dict], begriffe: dict, stichtag: dt.date, vorgaben=()) -> dict:
    """{rollenfamilie: {begriff: zeile}} für Ausschreibungen im Fenster.
    vorgaben: [{"begriff", "rollenfamilien"?}] – vom Nutzer gesetzt, gelten
    immer als gefragt (ohne rollenfamilien: in jeder Familie des Marktbilds)."""
    ab = stichtag - dt.timedelta(days=FENSTER_TAGE)
    bild: dict = {}
    for a in anf:
        datum = dt.date.fromisoformat(a["datum"])
        if not ab <= datum <= stichtag:
            continue
        familie = bild.setdefault(a["rollenfamilie"], {})
        ergaenzt = {b for liste in a.get("ergaenzt", {}).values() for b in liste}
        for r in a["anforderungen"]:
            z = familie.setdefault(r["begriff"], {
                "begriff": r["begriff"], "art": begriffe[r["begriff"]]["art"],
                "quellen": [], "muss": 0, "kann": 0, "punkte": 0, "ergaenzt": 0, "letzte": ""})
            if a["anfrage"] in z["quellen"]:
                continue                            # pro Ausschreibung nur einmal zählen
            z["quellen"].append(a["anfrage"])
            z[r["stufe"]] += 1
            z["punkte"] += GEWICHT[r["stufe"]]
            z["ergaenzt"] += r["begriff"] in ergaenzt
            z["letzte"] = max(z["letzte"], a["datum"])
    for familie in bild.values():
        for z in familie.values():
            z["gefragt"] = len(z["quellen"]) >= MINDESTENS
            z["vorgabe"] = False
    for v in vorgaben:
        for f in v.get("rollenfamilien") or list(bild):
            z = bild.setdefault(f, {}).setdefault(v["begriff"], {
                "begriff": v["begriff"], "art": begriffe[v["begriff"]]["art"],
                "quellen": [], "muss": 0, "kann": 0, "punkte": 0, "ergaenzt": 0, "letzte": ""})
            z["gefragt"] = z["vorgabe"] = True
    return bild


def normal(text: str) -> str:
    """PDF-Text vergleichbar machen: geschützte Zeichen aus dem Layout zurück."""
    text = text.replace(" ", " ").replace("‑", "-").replace("⁠", "").replace("­", "")
    return re.sub(r"\s+", " ", text).casefold()


def kommt_vor(begriff: str, info: dict, text: str) -> bool:
    for wort in [begriff, *info.get("synonyme", [])]:
        if re.search(r"(?<!\w)" + re.escape(normal(wort)) + r"(?!\w)", text):
            return True
    return False


def kandidatentext(ordner: Path) -> str:
    teile = []
    for p in sorted(ordner.glob("*.pdf")):
        teile.append(subprocess.run(["pdftotext", "-q", str(p), "-"], capture_output=True, text=True).stdout)
    for p in sorted(ordner.glob("*.txt")):     # nur für selbsttest.py
        teile.append(p.read_text())
    return normal(" ".join(teile))


def luecken(bild: dict, begriffe: dict, kandidaten: dict, originale: Path, markt: Path) -> tuple[dict, list[str]]:
    ergebnis, hinweise = {}, []
    for name, k in kandidaten.items():
        ordner = originale / k["ordner"]
        text = kandidatentext(ordner) if ordner.is_dir() else ""
        if not text.strip():
            hinweise.append(f"{name}: keine lesbaren PDFs in {ordner}")
            continue
        antworten = lies(markt / "antworten" / f"{name}.json", {})
        offen = {}
        for familie in k["rollenfamilien"]:
            for z in bild.get(familie, {}).values():
                if not z["gefragt"] or z["art"] not in SELBST | FRAGEN:
                    continue
                if kommt_vor(z["begriff"], begriffe[z["begriff"]], text):
                    continue
                antwort = antworten.get(z["begriff"], {}).get("antwort")
                if antwort == "nein":
                    continue
                if antwort in ("ja", "ja_projekt"):
                    tun = "bejaht – einspeisen"
                elif z["art"] in SELBST:
                    tun = "selbst ergänzen"
                elif antwort == "weiss_nicht":
                    tun = "weiß nicht – Kandidat fragen"
                else:
                    tun = "Nutzer fragen"
                alt = offen.get(z["begriff"])
                if alt is None or z["punkte"] > alt["punkte"]:
                    offen[z["begriff"]] = {"begriff": z["begriff"], "art": z["art"], "rollenfamilie": familie,
                                           "punkte": z["punkte"], "tun": tun,
                                           "projekt": antworten.get(z["begriff"], {}).get("projekt", "")}
        ergebnis[name] = sorted(offen.values(), key=lambda x: (-x["punkte"], x["begriff"]))
    return ergebnis, hinweise


def veraenderungen(alt: dict, neu: dict) -> list[str]:
    """Was seit dem letzten Stand dazukam oder herausfiel (nur gefragte Begriffe)."""
    zeilen = []
    for familie in neu.keys() | alt.keys():
        vorher = {b for b, z in alt.get(familie, {}).items() if z["gefragt"]}
        jetzt = {b: z for b, z in neu.get(familie, {}).items() if z["gefragt"]}
        for b in set(jetzt) - vorher:
            # Ergänzbares (Methoden, Tools …) zuerst – Sprache/Erfahrung kann keine Mappe nachholen
            zeilen.append(((jetzt[b]["art"] not in SELBST | FRAGEN, -jetzt[b]["punkte"], b, familie),
                           f"Neu gefragt ({familie}): {b} – {len(jetzt[b]['quellen'])} Ausschreibungen"))
        for b in vorher - set(jetzt):
            zeilen.append(((True, 0, b, familie), f"Nicht mehr gefragt ({familie}): {b}"))
    return [text for _, text in sorted(zeilen)]


def top(bild: dict, familie: str, n: int = 3) -> list[dict]:
    return sorted((z for z in bild.get(familie, {}).values() if z["gefragt"]),
                  key=lambda z: (-z["punkte"], z["begriff"]))[:n]


# ---------- Schreiben ----------

def xlsx(pfad: Path, blaetter: list[tuple[str, list[list]]]) -> None:
    """Minimale .xlsx ohne Fremdpaket: Inline-Strings, Zahlen, Filter, Kopfzeile fixiert."""
    def spalte(i: int) -> str:
        s = ""
        i += 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s

    def zelle(ref: str, wert) -> str:
        if isinstance(wert, (int, float)) and not isinstance(wert, bool):
            return f'<c r="{ref}"><v>{wert}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(str(wert))}</t></is></c>'

    def blatt(zeilen: list[list]) -> str:
        breite = max((len(z) for z in zeilen), default=1)
        cols = "".join(
            f'<col min="{i + 1}" max="{i + 1}" width="{min(60, max(10, max(len(str(z[i])) if i < len(z) else 0 for z in zeilen) + 2))}" customWidth="1"/>'
            for i in range(breite))
        rows = "".join(
            f'<row r="{r + 1}">' + "".join(zelle(f"{spalte(c)}{r + 1}", w) for c, w in enumerate(z)) + "</row>"
            for r, z in enumerate(zeilen))
        filt = f'<autoFilter ref="A1:{spalte(breite - 1)}{len(zeilen)}"/>' if len(zeilen) > 1 else ""
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
                f'<cols>{cols}</cols><sheetData>{rows}</sheetData>{filt}</worksheet>')

    ns = "http://schemas.openxmlformats.org"
    with zipfile.ZipFile(pfad, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="{ns}/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(len(blaetter))) + "</Types>")
        z.writestr("_rels/.rels",
                   f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}/package/2006/relationships">'
                   f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml",
                   f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{ns}/spreadsheetml/2006/main" '
                   f'xmlns:r="{ns}/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(n[:31])}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, (n, _) in enumerate(blaetter))
                   + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" Type="{ns}/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>'
                             for i in range(len(blaetter))) + "</Relationships>")
        for i, (_, zeilen) in enumerate(blaetter):
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", blatt(zeilen))


def bericht(stichtag, bild, luecken_, aend, hinweise, quellen) -> str:
    z = [f"# Marktbild – Stand {stichtag:%d.%m.%Y}", "",
         f"Fenster: Ausschreibungen seit {stichtag - dt.timedelta(days=FENSTER_TAGE):%d.%m.%Y}, "
         f"gefragt ab {MINDESTENS} Ausschreibungen, Muss zählt {GEWICHT['muss']}, Kann {GEWICHT['kann']}. "
         f"Quellen: {len(quellen)} Ausschreibungen.", ""]
    z += ["## Was sich verändert hat", ""] + ([f"- {x}" for x in aend] or ["- Nichts gegenüber dem letzten Stand."]) + [""]
    for familie in sorted(bild):
        gefragt = sorted((x for x in bild[familie].values() if x["gefragt"]), key=lambda x: (-x["punkte"], x["begriff"]))
        n = sum(1 for q in quellen if q[3] == familie)
        z += [f"## {familie} ({n} Ausschreibungen)", ""]
        if not gefragt:
            z += [f"Noch nichts in {MINDESTENS}+ Ausschreibungen.", ""]
            continue
        z += ["| Begriff | Art | Ausschreibungen | Muss | Kann | bei uns ergänzt |", "|---|---|---|---|---|---|"]
        z += [f"| {x['begriff']}{' (Vorgabe)' if x.get('vorgabe') else ''} | {x['art']} | {len(x['quellen'])} | {x['muss']} | {x['kann']} | {x['ergaenzt']} |" for x in gefragt]
        z.append("")
    z += ["## Lücken je Kandidat", ""]
    for name, liste in luecken_.items():
        if not liste:
            z.append(f"- **{name}:** keine Lücken.")
            continue
        gruppen: dict = {}
        for l in liste:
            gruppen.setdefault(l["tun"], []).append(l["begriff"])
        z.append(f"- **{name}:** " + "; ".join(f"{tun}: {', '.join(b)}" for tun, b in gruppen.items()))
    if hinweise:
        z += ["", "## Hinweise", ""] + [f"- {h}" for h in hinweise]
    return "\n".join(z) + "\n"


def auswerten(k: dict, stichtag: dt.date) -> Path:
    markt = k["markt"]
    begriffe = lies(markt / "begriffe.json", {})
    kandidaten = lies(markt / "kandidaten.json", {})
    anf = anforderungen(markt)
    vorgaben = lies(markt / "vorgaben.json", [])
    fehler = pruefe_daten(anf, begriffe, vorgaben)
    if fehler:
        sys.exit("Daten unvollständig:\n" + "\n".join(fehler))
    bild = marktbild(anf, begriffe, stichtag, vorgaben)
    luecken_, hinweise = luecken(bild, begriffe, kandidaten, k["originale"], markt)
    for ordner in sorted(p.name for p in k["originale"].iterdir() if p.is_dir()):
        if ordner not in {v["ordner"] for v in kandidaten.values()}:
            hinweise.append(f"Originale/{ordner} steht nicht in kandidaten.json – keine Lückenprüfung")

    staende = sorted(p for p in markt.glob("stand-*") if p.is_dir() and p.name != f"stand-{stichtag}")
    alt = lies(staende[-1] / "marktbild.json", {}) if staende else {}
    aend = veraenderungen(alt, bild)

    ziel = markt / f"stand-{stichtag}"
    ziel.mkdir(parents=True, exist_ok=True)
    ab = stichtag - dt.timedelta(days=FENSTER_TAGE)
    quellen = [(a["anfrage"], a["datum"], a.get("rolle", ""), a["rollenfamilie"], len(a["anforderungen"]))
               for a in anf if ab <= dt.date.fromisoformat(a["datum"]) <= stichtag]
    kopf = ["Rollenfamilie", "Begriff", "Art", "Gefragt", "Ausschreibungen", "Muss", "Kann", "Punkte",
            "Bei uns ergänzt", "Letzte Nennung", "Quellen"]
    zeilen = [kopf] + [[f, z["begriff"], z["art"], ("ja (Vorgabe)" if z.get("vorgabe") else "ja") if z["gefragt"] else "nein", len(z["quellen"]), z["muss"],
                        z["kann"], z["punkte"], z["ergaenzt"], z["letzte"], " · ".join(z["quellen"])]
                       for f in sorted(bild) for z in sorted(bild[f].values(), key=lambda z: (-z["punkte"], z["begriff"]))]
    lz = [["Kandidat", "Begriff", "Art", "Rollenfamilie", "Punkte", "Was tun", "Projekt (Nutzerangabe)"]]
    lz += [[n, l["begriff"], l["art"], l["rollenfamilie"], l["punkte"], l["tun"], l["projekt"]]
           for n, liste in luecken_.items() for l in liste]
    qz = [["Anfrage", "Datum", "Rolle", "Rollenfamilie", "Anforderungen"]] + [list(q) for q in quellen]
    xlsx(ziel / "marktbild.xlsx", [("Marktbild", zeilen), ("Lücken", lz), ("Quellen", qz)])
    (ziel / "marktbild.json").write_text(json.dumps(bild, ensure_ascii=False, indent=1))
    (ziel / "luecken.json").write_text(json.dumps(luecken_, ensure_ascii=False, indent=1))
    (ziel / "bericht.md").write_text(bericht(stichtag, bild, luecken_, aend, hinweise, quellen))

    mitteilung = aend[:3] or [f"{f}: " + ", ".join(z["begriff"] for z in top(bild, f)) for f in sorted(bild) if top(bild, f)][:3]
    print(ziel)
    print("\n".join(mitteilung or ["Marktbild aktualisiert, keine gefragten Begriffe."]))
    return ziel


# ---------- Kommandos ----------

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("offen")
    a = sub.add_parser("auswerten")
    a.add_argument("--stichtag", type=dt.date.fromisoformat, default=dt.date.today())
    l = sub.add_parser("luecken")
    l.add_argument("--kandidat", required=True)
    w = sub.add_parser("antwort")
    w.add_argument("--kandidat", required=True)
    w.add_argument("--begriff", required=True)
    w.add_argument("--antwort", required=True, choices=sorted(ANTWORTEN))
    w.add_argument("--projekt", default="")
    args = ap.parse_args(argv)
    k = konfig()
    markt = k["markt"]

    if args.cmd == "offen":
        fertig = {p.stem for p in (markt / "anforderungen").glob("*.json")}
        for p in sorted(k["ausschreibungen"].iterdir()):
            if p.is_dir() and (p / "ausschreibung.md").exists() and p.name not in fertig:
                print(f"OFFEN\t{p}")
        for f in pruefe_daten(anforderungen(markt), lies(markt / "begriffe.json", {}), lies(markt / "vorgaben.json", [])):
            print(f"FEHLER\t{f}")
    elif args.cmd == "auswerten":
        auswerten(k, args.stichtag)
    elif args.cmd == "luecken":
        staende = sorted(p for p in markt.glob("stand-*") if p.is_dir())
        if not staende:
            sys.exit("Noch kein Stand – erst auswerten.")
        print(json.dumps(lies(staende[-1] / "luecken.json", {}).get(args.kandidat, []), ensure_ascii=False, indent=1))
    elif args.cmd == "antwort":
        pfad = markt / "antworten" / f"{args.kandidat}.json"
        pfad.parent.mkdir(parents=True, exist_ok=True)
        daten = lies(pfad, {})
        daten[args.begriff] = {"antwort": args.antwort, "projekt": args.projekt, "datum": dt.date.today().isoformat()}
        pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=1))
        print(pfad)


if __name__ == "__main__":
    main()
