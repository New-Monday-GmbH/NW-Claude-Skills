#!/usr/bin/env python3
"""Prüft die Dateien eines Gesamtlaufs von newmonday-bewerbermappe.

    python3 pruefe_lauf.py <laufordner>
    python3 pruefe_lauf.py <laufordner> --ohne-dateien   # Materialpfade nicht prüfen

Geprüft werden auftrag.json, jede <skill>/fragen.json und jede
<skill>/uebergabe.md, die es gibt – außer bei einem Skill, dessen vorbereiten
bzw. bauen auf fehler oder ausgelassen steht: dann nur eine Warnung. Rückgabe 1,
wenn etwas nicht stimmt – die Ausgabe nennt jede Stelle, in fester Reihenfolge.
Warnungen halten nichts auf. Nur Standardbibliothek.
"""
from __future__ import annotations

import json
import os
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
QUELLEN = ("lebenslauf", "portfolio", "linkedin_export")  # Reihe nach vorrang
ANWEISUNG = "Anweisung:"  # Antwort über Other, die eine Anweisung an den Skill ist
LEER = {"", "-", "–", "—"}  # kein Wert: eine Quelle, die schweigt, fehlt in werte
STRICH = re.compile(r"\s*[-‐‑‒–—−]\s*")
UEBERSPRINGEN = {"fehler", "ausgelassen"}  # Phase so: deren Datei nur mit Warnung
UEBERGABE = ["## Dateien", "## Zur Freigabe", "## Quellen weichen ab",
             "## Hinweise", "## Ohne Rückfrage entschieden", "## Fehlt noch"]
EMPFOHLEN = "(Empfohlen)"
ID = re.compile(r"^[a-z][a-z0-9_]*$")
FIGMA_LINK = re.compile(
    r"^https://www\.figma\.com/design/(?P<key>[A-Za-z0-9]+)/[^?]*\?(?:.*&)?"
    r"node-id=(?P<a>\d+)-(?P<b>\d+)")
SEITE = re.compile(r"^\d+:\d+$")
_FEHLT = object()  # Rückgabe von _lade für eine nicht ladbare Datei (JSON null ist None)


def _text(wert) -> bool:
    return isinstance(wert, str) and bool(wert.strip())


def _vergleichsform(wert: str) -> str:
    """Ein Wert, wie er für „alle gleich“ zählt: Groß- und Kleinschreibung,
    Leerraum und Strichart („2017 - 2024“, „2017 – 2024“) machen keinen
    Widerspruch."""
    return " ".join(STRICH.sub("-", wert.strip()).split()).casefold()


def pruefe_abweichungen(abw) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für abweichungen in einer fragen.json."""
    f: list[str] = []
    w: list[str] = []
    if not isinstance(abw, list):
        return ["abweichungen: muss eine Liste sein"], w
    for i, a in enumerate(abw):
        o = f"abweichungen[{i}]"
        if not isinstance(a, dict):
            f.append(f"{o}: muss ein Objekt sein")
            continue
        if not _text(a.get("feld")):
            f.append(f"{o}.feld: fehlt")
        werte = a.get("werte")
        if not isinstance(werte, dict):
            f.append(f"{o}.werte: muss ein Objekt sein")
            werte = None
        else:
            if len(werte) < 2:
                f.append(f"{o}.werte: {len(werte)} Quelle(n) statt mindestens 2")
            for k, v in werte.items():
                if k not in QUELLEN:
                    f.append(f"{o}.werte.{k}: unbekannte Quelle – erlaubt sind {list(QUELLEN)}")
                elif not isinstance(v, str):
                    f.append(f"{o}.werte.{k}: muss ein String sein")
                elif v.strip() in LEER:
                    f.append(f"{o}.werte.{k}: leer – eine Quelle ohne Angabe gehört "
                             "nicht in werte")
            gefuellt = [v for k, v in werte.items()
                        if k in QUELLEN and isinstance(v, str) and v.strip() not in LEER]
            if len(gefuellt) >= 2 and len({_vergleichsform(v) for v in gefuellt}) == 1:
                f.append(f"{o}.werte: alle gleich – keine Abweichung")
        if "neuer" in a:
            neuer = a["neuer"]
            if not isinstance(neuer, str):
                f.append(f"{o}.neuer: muss ein String sein")
            elif neuer not in (werte if werte is not None else QUELLEN):
                f.append(f"{o}.neuer: {neuer!r} ist keine Quelle aus werte")
    return f, w


def pruefe_fragen(d: dict) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für den Inhalt einer fragen.json."""
    f: list[str] = []
    w: list[str] = []
    if not isinstance(d, dict):
        return ["oberste Ebene muss ein JSON-Objekt sein"], w
    skill = d.get("skill")
    if not isinstance(skill, str):
        f.append("skill: muss ein String sein")
    elif skill not in SKILLS:
        f.append(f"skill: {skill!r} ist keiner von {sorted(SKILLS)}")
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
    fa, wa = pruefe_abweichungen(d.get("abweichungen", []))
    f += fa
    w += wa
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
    if isinstance(fig, dict) and "neues_file" in fig and not isinstance(fig["neues_file"], bool):
        f.append("figma.neues_file: muss true oder false sein")
    if isinstance(fig, dict) and "bibliothek" in fig and not isinstance(fig["bibliothek"], bool):
        f.append("figma.bibliothek: muss true oder false sein")
    if not isinstance(fig, dict) or not isinstance(fig.get("aktiv"), bool):
        f.append("figma.aktiv: muss true oder false sein")
    elif fig["aktiv"]:
        m = FIGMA_LINK.match(str(fig.get("link") or ""))
        if not m:
            f.append("figma.link: kein figma.com/design-Link mit node-id der Zielseite")
        elif fig.get("file_key") != m.group("key"):
            w.append(f"figma.file_key: {fig.get('file_key')!r} passt nicht zum Link "
                     f"({m.group('key')!r})")
        seite = str(fig.get("seite_id") or "")
        if not SEITE.match(seite):
            f.append("figma.seite_id: fehlt (Form 12:34)")
        elif m and seite != f"{m.group('a')}:{m.group('b')}":
            f.append("figma.seite_id: passt nicht zur node-id im Link")
    mat = d.get("material", {})
    if not isinstance(mat, dict):
        f.append("material: muss ein Objekt sein")
        mat = {}
    for k, v in mat.items():
        if k not in MATERIAL:
            f.append(f"material.{k}: unbekannt")
        elif v is not None and not isinstance(v, str):
            f.append(f"material.{k}: muss ein String oder null sein")
    if not (mat.get("lebenslauf") or mat.get("linkedin_export")):
        f.append("material: weder lebenslauf noch linkedin_export – ohne eins von beiden kein Lauf")
    ohne = d.get("ohne", [])
    if not isinstance(ohne, list):
        f.append("ohne: muss eine Liste sein")
    else:
        for i, k in enumerate(ohne):
            if not isinstance(k, str):
                f.append(f"ohne[{i}]: muss ein String sein")
            elif k not in MATERIAL:
                w.append(f"ohne: {k!r} ist kein Materialschlüssel – richtig nur für eine "
                         "Lücke ohne Schlüssel (references/formate.md)")
            elif mat.get(k):
                w.append(f"ohne: {k!r} steht auch unter material")
    if "vorrang" in d:
        v = d["vorrang"]
        if isinstance(v, str) and v.startswith(ANWEISUNG):
            if not _text(v[len(ANWEISUNG):]):
                f.append("vorrang: Anweisung ohne Text")
        elif v is not None and not (isinstance(v, str) and v in QUELLEN):
            f.append(f"vorrang: {v!r} ist keiner von {list(QUELLEN)}, nicht null und "
                     f"beginnt nicht mit {ANWEISUNG!r}")
    entscheidungen = d.get("entscheidungen", {})
    if not isinstance(entscheidungen, dict):
        f.append("entscheidungen: muss ein Objekt sein")
    else:
        for s, antworten in entscheidungen.items():
            if s not in SKILLS:
                f.append(f"entscheidungen.{s}: unbekannter Skill")
            elif not isinstance(antworten, dict):
                f.append(f"entscheidungen.{s}: muss ein Objekt sein")
            else:
                for qid, antwort in antworten.items():
                    if not isinstance(antwort, str):
                        f.append(f"entscheidungen.{s}.{qid}: muss ein String sein, "
                                 "auch bei mehreren Haken")
    status = d.get("status", {})
    if not isinstance(status, dict):
        return f + ["status: muss ein Objekt sein"], w
    for s in reihe:
        st = status.get(s)
        if st is None:
            f.append(f"status.{s}: fehlt")
            continue
        if not isinstance(st, dict):
            f.append(f"status.{s}: muss ein Objekt sein")
            continue
        for phase in ("vorbereiten", "bauen"):
            wert = st.get(phase)
            if not isinstance(wert, str) or wert not in STATUS:
                f.append(f"status.{s}.{phase}: {wert!r} ist keiner von {sorted(STATUS)}")
        if st.get("fehler") is not None and not isinstance(st.get("fehler"), str):
            f.append(f"status.{s}.fehler: muss ein String oder null sein")
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


def _lade(datei: Path, name: str, f: list[str]):
    """Inhalt einer JSON-Datei. Ist sie nicht ladbar: _FEHLT und eine FEHLER-Zeile
    mit dem Pfad relativ zum Laufordner. Der Inhalt null kommt als None zurück."""
    try:
        return json.loads(datei.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as e:
        f.append(f"{name}: nicht lesbar – {e}")
        return _FEHLT


def _phase(auftrag, skill: str, phase: str):
    """status.<skill>.<phase> aus auftrag.json, sonst None."""
    status = auftrag.get("status") if isinstance(auftrag, dict) else None
    st = status.get(skill) if isinstance(status, dict) else None
    return st.get(phase) if isinstance(st, dict) else None


def _gleicher_ordner(pfad: str, lauf: Path) -> bool:
    try:
        return os.path.samefile(pfad, lauf)
    except (OSError, ValueError):
        return False


def _unbekannte_antworten(auftrag, skill: str, kurz: str, fragen) -> list[str]:
    """Antwort-ids in entscheidungen.<skill>, zu denen <kurz>/fragen.json keine Frage hat."""
    alle = auftrag.get("entscheidungen") if isinstance(auftrag, dict) else None
    antworten = alle.get(skill) if isinstance(alle, dict) else None
    liste = fragen.get("fragen", []) if isinstance(fragen, dict) else None
    if not isinstance(antworten, dict) or not isinstance(liste, list):
        return []
    ids = {q.get("id") for q in liste if isinstance(q, dict) and isinstance(q.get("id"), str)}
    return [f"auftrag.json: entscheidungen.{skill}.{qid}: keine Frage mit dieser id "
            f"in {kurz}/fragen.json" for qid in antworten if qid not in ids]


def pruefe_ordner(lauf: Path, dateien: bool = True) -> tuple[list[str], list[str]]:
    """Fehler und Warnungen für einen ganzen Laufordner."""
    f: list[str] = []
    w: list[str] = []
    datei = lauf / "auftrag.json"
    if not datei.exists():
        return [f"{datei}: fehlt"], w
    auftrag = _lade(datei, "auftrag.json", f)
    if auftrag is not _FEHLT:
        fa, wa = pruefe_auftrag(auftrag)
        f += [f"auftrag.json: {x}" for x in fa]
        w += [f"auftrag.json: {x}" for x in wa]
    if isinstance(auftrag, dict):
        lf = auftrag.get("laufordner")
        if isinstance(lf, str) and lf.startswith("/") and not _gleicher_ordner(lf, lauf):
            w.append(f"auftrag.json: laufordner {lf!r} ist nicht der geprüfte Ordner {str(lauf)!r}")
        mat = auftrag.get("material", {})
        if dateien and isinstance(mat, dict):
            for k in sorted(PFADE):
                v = mat.get(k)
                if _text(v) and not (lauf / v).exists():
                    f.append(f"auftrag.json: material.{k}: {v} gibt es im Laufordner nicht")
    for skill, kurz in SKILLS.items():
        fr = lauf / kurz / "fragen.json"
        vorbereiten = _phase(auftrag, skill, "vorbereiten")
        if fr.exists() and isinstance(vorbereiten, str) and vorbereiten in UEBERSPRINGEN:
            w.append(f"{kurz}/fragen.json: nicht geprüft – status.{skill}.vorbereiten "
                     f"ist {vorbereiten!r}")
        elif fr.exists():
            d = _lade(fr, f"{kurz}/fragen.json", f)
            if d is not _FEHLT:
                ff, ww = pruefe_fragen(d)
                gemeldet = d.get("skill") if isinstance(d, dict) else None
                if isinstance(gemeldet, str) and gemeldet in SKILLS and gemeldet != skill:
                    ff.append(f"skill: {gemeldet!r}, erwartet {skill!r}")
                f += [f"{kurz}/fragen.json: {x}" for x in ff]
                w += [f"{kurz}/fragen.json: {x}" for x in ww]
                f += _unbekannte_antworten(auftrag, skill, kurz, d)
        ue = lauf / kurz / "uebergabe.md"
        bauen = _phase(auftrag, skill, "bauen")
        if ue.exists() and isinstance(bauen, str) and bauen in UEBERSPRINGEN:
            w.append(f"{kurz}/uebergabe.md: nicht geprüft – status.{skill}.bauen ist {bauen!r}")
        elif ue.exists():
            try:
                text = ue.read_text(encoding="utf-8")
                f += [f"{kurz}/uebergabe.md: {x}"
                      for x in pruefe_uebergabe("\n" + text + "\n")]
            except (OSError, UnicodeDecodeError) as e:
                f.append(f"{kurz}/uebergabe.md: nicht lesbar – {e}")
    ff, ww = pruefe_tools(lauf, auftrag)
    return f + ff, w + ww


def _tools(datei: Path, lesen):
    """Toolnamen aus cv.json (skillset.tools) bzw. skillmatrix.json (tools[].name),
    oder None, wenn die Datei fehlt oder keine Liste traegt."""
    if not datei.exists():
        return None
    try:
        return lesen(json.loads(datei.read_text(encoding="utf-8")))
    except (OSError, ValueError, AttributeError, KeyError, TypeError):
        return None


def pruefe_tools(lauf: Path, auftrag) -> tuple[list[str], list[str]]:
    """Lebenslauf und Skill Matrix fuehren dieselben Tools – gleiche Eintraege,
    gleiche Schreibweise; die Reihenfolge darf abweichen (Liste im Lebenslauf,
    Raster in der Skill Matrix). Massgeblich ist die Skill Matrix. Fehler erst, wenn
    beide gebaut sind; vorher eine Warnung, damit ein laufender Bau nicht an
    einem Dokument scheitert, das noch nicht dran war."""
    cv = _tools(lauf / "cv" / "cv.json",
                lambda d: [str(t) for t in d["skillset"]["tools"]])
    sm = _tools(lauf / "skillmatrix" / "skillmatrix.json",
                lambda d: [str(t["name"]) for t in d["tools"]])
    if cv is None or sm is None or sorted(cv) == sorted(sm):
        return [], []
    text = (f"Tools weichen ab – Skill Matrix {sm}, Lebenslauf {cv}. Der Lebenslauf "
            "übernimmt die Tools der Skill Matrix wörtlich (skillset.tools).")
    gebaut = all(_phase(auftrag, s, "bauen") == "fertig"
                 for s in ("newmonday-cv", "newmonday-skillmatrix"))
    return ([text], []) if gebaut else ([], [text])


def main(args: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")  # kein Absturz an einem Zeichen
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
