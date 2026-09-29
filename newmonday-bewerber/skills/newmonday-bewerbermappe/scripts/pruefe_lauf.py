#!/usr/bin/env python3
"""Prüft die Dateien eines Gesamtlaufs von newmonday-bewerbermappe.

    python3 pruefe_lauf.py <laufordner>
    python3 pruefe_lauf.py <laufordner> --ohne-dateien   # Materialpfade nicht prüfen

Geprüft werden auftrag.json, jede <skill>/fragen.json und jede
<skill>/uebergabe.md, die es gibt. Rückgabe 1, wenn etwas nicht stimmt – die
Ausgabe nennt jede Stelle. Warnungen halten nichts auf. Nur Standardbibliothek.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Skill -> Unterordner im Laufordner, in Bau-Reihenfolge
SKILLS = {
    "newmonday-cv": "cv",
    "newmonday-skillmatrix": "skillmatrix",
    "newmonday-portfolio": "portfolio",
}
MATERIAL = {"lebenslauf", "linkedin_export", "linkedin_url", "xing_url",
            "portfolio_url", "portfolio_pdf", "foto", "logos", "screens",
            "zertifikate", "kundentexte"}
PFADE = {"lebenslauf", "linkedin_export", "portfolio_pdf", "foto", "logos",
         "screens", "zertifikate"}
STATUS = {"offen", "fertig", "fehler", "ausgelassen"}
UEBERGABE = ["## Dateien", "## Zur Freigabe", "## Quellen weichen ab",
             "## Hinweise", "## Ohne Rückfrage entschieden", "## Fehlt noch"]
EMPFOHLEN = "(Empfohlen)"
ID = re.compile(r"^[a-z][a-z0-9_]*$")
FIGMA_LINK = re.compile(
    r"^https://www\.figma\.com/design/[A-Za-z0-9]+/[^?]*\?(?:.*&)?node-id=(\d+)-(\d+)")
SEITE = re.compile(r"^\d+:\d+$")


def _text(wert) -> bool:
    return isinstance(wert, str) and bool(wert.strip())


def pruefe_fragen(d: dict) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für den Inhalt einer fragen.json."""
    f: list[str] = []
    w: list[str] = []
    if not isinstance(d, dict):
        return ["oberste Ebene muss ein JSON-Objekt sein"], w
    if d.get("skill") not in SKILLS:
        f.append(f"skill: {d.get('skill')!r} ist keiner von {sorted(SKILLS)}")
    if not _text(d.get("kandidat")):
        f.append("kandidat: fehlt")
    texte = d.get("texte", [])
    if not isinstance(texte, list) or not all(isinstance(t, str) for t in texte):
        f.append("texte: muss eine Liste von Strings sein")
    luecken = d.get("luecken", [])
    if not isinstance(luecken, list):
        f.append("luecken: muss eine Liste sein")
        luecken = []
    for i, l in enumerate(luecken):
        for k in ("was", "folge", "form"):
            if not _text(l.get(k) if isinstance(l, dict) else None):
                f.append(f"luecken[{i}].{k}: fehlt")
    fragen = d.get("fragen", [])
    if not isinstance(fragen, list):
        return f + ["fragen: muss eine Liste sein"], w
    if len(fragen) > 4:
        f.append(f"fragen: {len(fragen)} statt höchstens 4")
    ids: set = set()
    fragetexte: set = set()
    for i, q in enumerate(fragen):
        o = f"fragen[{i}]"
        if not isinstance(q, dict):
            f.append(f"{o}: muss ein Objekt sein")
            continue
        qid = str(q.get("id", ""))
        if not ID.match(qid):
            f.append(f"{o}.id: {qid!r} ist kein snake_case")
        elif qid in ids:
            f.append(f"{o}.id: {qid!r} doppelt")
        ids.add(qid)
        text = q.get("question")
        if not _text(text) or not text.strip().endswith("?"):
            f.append(f"{o}.question: muss mit '?' enden")
        elif isinstance(text, str) and text in fragetexte:
            f.append(f"{o}.question: doppelt – Antworten kommen nach Fragetext zurück")
        if isinstance(text, str):
            fragetexte.add(text)
        header = q.get("header")
        if not _text(header):
            f.append(f"{o}.header: fehlt")
        elif len(header) > 12:
            w.append(f"{o}.header: {header!r} hat {len(header)} Zeichen, "
                     "AskUserQuestion zeigt 12")
        if not isinstance(q.get("multiSelect"), bool):
            f.append(f"{o}.multiSelect: muss true oder false sein")
        opts = q.get("options")
        if not isinstance(opts, list) or not 2 <= len(opts) <= 4:
            anzahl = len(opts) if isinstance(opts, list) else "keine"
            f.append(f"{o}.options: {anzahl} statt 2–4")
            continue
        labels = []
        for j, p in enumerate(opts):
            if not isinstance(p, dict):
                f.append(f"{o}.options[{j}]: muss ein Objekt sein")
                labels.append("")
                continue
            if not _text(p.get("label")):
                f.append(f"{o}.options[{j}].label: fehlt")
            if not isinstance(p.get("description"), str):
                f.append(f"{o}.options[{j}].description: fehlt")
            if "text_noetig" in p and not isinstance(p["text_noetig"], bool):
                f.append(f"{o}.options[{j}].text_noetig: muss true oder false sein")
            labels.append(str(p.get("label", "")))
        if len(set(labels)) != len(labels):
            f.append(f"{o}.options: Labels doppelt")
        empf = [j for j, l in enumerate(labels) if EMPFOHLEN in l]
        if len(empf) > 1:
            f.append(f"{o}.options: mehr als eine Option {EMPFOHLEN}")
        elif empf and empf[0] != 0:
            f.append(f"{o}.options: {EMPFOHLEN} muss die erste Option sein")
    return f, w


def pruefe_auftrag(d: dict) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für den Inhalt einer auftrag.json."""
    f: list[str] = []
    w: list[str] = []
    if not isinstance(d, dict):
        return ["oberste Ebene muss ein JSON-Objekt sein"], w
    if d.get("version") != 1:
        f.append(f"version: {d.get('version')!r} statt 1")
    if not str(d.get("laufordner", "")).startswith("/"):
        f.append("laufordner: muss ein absoluter Pfad sein")
    if not _text(d.get("kandidat")):
        f.append("kandidat: fehlt")
    if d.get("sprache") not in ("de", "en"):
        f.append(f"sprache: {d.get('sprache')!r} statt 'de' oder 'en'")
    reihe = d.get("reihenfolge")
    if not isinstance(reihe, list) or not reihe or reihe != [s for s in SKILLS if s in reihe]:
        f.append(f"reihenfolge: {reihe!r} – erlaubt sind {list(SKILLS)} in dieser Reihenfolge")
        reihe = []
    fig = d.get("figma", {})
    if not isinstance(fig, dict) or not isinstance(fig.get("aktiv"), bool):
        f.append("figma.aktiv: muss true oder false sein")
    elif fig["aktiv"]:
        m = FIGMA_LINK.match(str(fig.get("link") or ""))
        if not m:
            f.append("figma.link: kein figma.com/design-Link mit node-id der Zielseite")
        seite = str(fig.get("seite_id") or "")
        if not SEITE.match(seite):
            f.append("figma.seite_id: fehlt (Form 12:34)")
        elif m and seite != f"{m.group(1)}:{m.group(2)}":
            f.append("figma.seite_id: passt nicht zur node-id im Link")
    mat = d.get("material", {})
    if not isinstance(mat, dict):
        f.append("material: muss ein Objekt sein")
        mat = {}
    for k in mat:
        if k not in MATERIAL:
            f.append(f"material.{k}: unbekannt")
    if not (mat.get("lebenslauf") or mat.get("linkedin_export")):
        f.append("material: weder lebenslauf noch linkedin_export – ohne eins von beiden kein Lauf")
    ohne = d.get("ohne", [])
    if not isinstance(ohne, list):
        f.append("ohne: muss eine Liste sein")
    else:
        for k in ohne:
            if k not in MATERIAL:
                f.append(f"ohne: {k!r} ist kein Materialposten")
            elif mat.get(k):
                w.append(f"ohne: {k!r} steht auch unter material")
    entscheidungen = d.get("entscheidungen", {})
    if not isinstance(entscheidungen, dict):
        f.append("entscheidungen: muss ein Objekt sein")
    else:
        for s in entscheidungen:
            if s not in SKILLS:
                f.append(f"entscheidungen.{s}: unbekannter Skill")
    status = d.get("status", {})
    for s in reihe:
        st = status.get(s) if isinstance(status, dict) else None
        if not isinstance(st, dict):
            f.append(f"status.{s}: fehlt")
            continue
        for phase in ("vorbereiten", "bauen"):
            if st.get(phase) not in STATUS:
                f.append(f"status.{s}.{phase}: {st.get(phase)!r} ist keiner von {sorted(STATUS)}")
        if st.get("bauen") == "fertig" and st.get("vorbereiten") != "fertig":
            f.append(f"status.{s}: gebaut, aber nicht vorbereitet")
    return f, w


def pruefe_uebergabe(text: str) -> list[str]:
    """Fehler für eine uebergabe.md: alle Abschnitte da, in dieser Reihenfolge."""
    stellen = [text.find("\n" + h + "\n") for h in UEBERGABE]
    fehlen = [h for h, s in zip(UEBERGABE, stellen) if s < 0]
    if fehlen:
        return [f"Abschnitt fehlt: {h}" for h in fehlen]
    if stellen != sorted(stellen):
        return ["Abschnitte nicht in der Reihenfolge " + " · ".join(UEBERGABE)]
    return []


def _lade(datei: Path, f: list[str]):
    try:
        return json.loads(datei.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
        f.append(f"{datei.name}: nicht lesbar – {e}")
        return None


def pruefe_ordner(lauf: Path, dateien: bool = True) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für einen ganzen Laufordner."""
    f: list[str] = []
    w: list[str] = []
    datei = lauf / "auftrag.json"
    if not datei.exists():
        return [f"{datei}: fehlt"], w
    auftrag = _lade(datei, f)
    if auftrag is not None:
        fa, wa = pruefe_auftrag(auftrag)
        f += [f"auftrag.json: {x}" for x in fa]
        w += [f"auftrag.json: {x}" for x in wa]
        if dateien and isinstance(auftrag, dict):
            mat = auftrag.get("material", {})
            if isinstance(mat, dict):
                for k in PFADE:
                    v = mat.get(k)
                    if _text(v) and not (lauf / v).exists():
                        f.append(f"auftrag.json: material.{k}: {v} gibt es im Laufordner nicht")
    for skill, kurz in SKILLS.items():
        fr = lauf / kurz / "fragen.json"
        if fr.exists():
            d = _lade(fr, f)
            if d is not None:
                ff, ww = pruefe_fragen(d)
                if isinstance(d, dict) and d.get("skill") in SKILLS and d.get("skill") != skill:
                    ff.append(f"skill: {d.get('skill')!r}, erwartet {skill!r}")
                f += [f"{kurz}/fragen.json: {x}" for x in ff]
                w += [f"{kurz}/fragen.json: {x}" for x in ww]
        ue = lauf / kurz / "uebergabe.md"
        if ue.exists():
            try:
                text = ue.read_text(encoding="utf-8")
                f += [f"{kurz}/uebergabe.md: {x}"
                      for x in pruefe_uebergabe("\n" + text + "\n")]
            except (OSError, UnicodeDecodeError) as e:
                f.append(f"{kurz}/uebergabe.md: nicht lesbar – {e}")
    return f, w


def main(args: list[str]) -> int:
    pfade = [a for a in args if not a.startswith("--")]
    if len(pfade) != 1:
        print(__doc__)
        return 2
    fehler, warnungen = pruefe_ordner(Path(pfade[0]), dateien="--ohne-dateien" not in args)
    for x in warnungen:
        print(f"Warnung: {x}")
    for x in fehler:
        print(f"FEHLER: {x}")
    if fehler:
        print(f"FEHLER — {len(fehler)} Stelle(n)")
        return 1
    print("Lauf in Ordnung")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))