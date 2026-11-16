#!/usr/bin/env python3
"""Selbsttest für marktbild.py – ohne echte Daten: python3 selbsttest.py"""
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SKRIPT = Path(__file__).with_name("marktbild.py")


def schreib(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(daten if isinstance(daten, str) else json.dumps(daten, ensure_ascii=False))


def lauf(env, *args) -> str:
    r = subprocess.run([sys.executable, str(SKRIPT), *args], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    return r.stdout


with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    aus, orig, markt = t / "Ausschreibungen", t / "Originale", t / "Markt"
    schreib(t / "konfig.json", {"ausschreibungen": str(aus), "originale": str(orig), "markt": str(markt)})
    env = dict(os.environ, MARKTBILD_KONFIG=str(t / "konfig.json"))
    for name in ("A1 UX", "A2 UX", "A3 alt", "A4 neu"):
        schreib(aus / name / "ausschreibung.md", "x")
    schreib(markt / "begriffe.json", {
        "Jira": {"art": "tool", "synonyme": []},
        "Confluence": {"art": "tool"},
        "Scrum": {"art": "methode"},
        "Barrierefreiheit": {"art": "methode", "synonyme": ["Accessibility", "WCAG"]},
        "Figma": {"art": "tool"},
        "Deutsch fließend": {"art": "sprache"},
    })
    schreib(markt / "anforderungen" / "A1 UX.json", {
        "anfrage": "A1 UX", "datum": "2026-10-01", "rollenfamilie": "UX/UI",
        "anforderungen": [{"begriff": "Jira", "stufe": "muss"}, {"begriff": "Scrum", "stufe": "muss"},
                          {"begriff": "Confluence", "stufe": "kann"}, {"begriff": "Deutsch fließend", "stufe": "muss"},
                          {"begriff": "Barrierefreiheit", "stufe": "kann"}],
        "ergaenzt": {"Anna Test": ["Scrum"]}})
    schreib(markt / "anforderungen" / "A2 UX.json", {
        "anfrage": "A2 UX", "datum": "2026-11-01", "rollenfamilie": "UX/UI",
        "anforderungen": [{"begriff": "Jira", "stufe": "kann"}, {"begriff": "Scrum", "stufe": "muss"},
                          {"begriff": "Scrum", "stufe": "muss"},          # doppelt: zählt einmal
                          {"begriff": "Confluence", "stufe": "muss"}, {"begriff": "Deutsch fließend", "stufe": "muss"},
                          {"begriff": "Barrierefreiheit", "stufe": "muss"}]})
    schreib(markt / "anforderungen" / "A3 alt.json", {     # außerhalb des Fensters
        "anfrage": "A3 alt", "datum": "2026-03-01", "rollenfamilie": "UX/UI",
        "anforderungen": [{"begriff": "Figma", "stufe": "muss"}]})
    schreib(markt / "kandidaten.json", {"Anna Test": {"ordner": "anna", "rollenfamilien": ["UX/UI"]},
                                        "Ben Visual": {"ordner": "ben", "rollenfamilien": ["Visual"]}})
    # Anna: Jira belegt, WCAG als Synonym (mit geschütztem Leerzeichen aus dem Layout)
    schreib(orig / "anna" / "cv.txt", "Tools: JIRA, Figma und WCAG 2.2")
    schreib(orig / "ben" / "cv.txt", "Illustration")
    (orig / "unbekannt").mkdir(parents=True)

    offen = lauf(env, "offen")
    assert "A4 neu" in offen and "A1 UX" not in offen and "FEHLER" not in offen, offen

    lauf(env, "antwort", "--kandidat", "Anna Test", "--begriff", "Confluence", "--antwort", "nein")
    out = lauf(env, "auswerten", "--stichtag", "2026-11-16").splitlines()
    ziel = Path(out[0])
    assert out[1:] == ["Neu gefragt (UX/UI): Scrum – 2 Ausschreibungen",
                       "Neu gefragt (UX/UI): Barrierefreiheit – 2 Ausschreibungen",
                       "Neu gefragt (UX/UI): Confluence – 2 Ausschreibungen"], out

    bild = json.loads((ziel / "marktbild.json").read_text())["UX/UI"]
    assert "Figma" not in bild, "A3 liegt außerhalb des Fensters"
    assert bild["Scrum"]["quellen"] == ["A1 UX", "A2 UX"] and bild["Scrum"]["punkte"] == 4, bild["Scrum"]
    assert bild["Jira"]["muss"] == 1 and bild["Jira"]["kann"] == 1 and bild["Jira"]["gefragt"]
    assert bild["Scrum"]["ergaenzt"] == 1

    luecken = json.loads((ziel / "luecken.json").read_text())
    anna = {l["begriff"]: l["tun"] for l in luecken["Anna Test"]}
    assert anna == {"Scrum": "selbst ergänzen"}, anna      # Jira belegt, Barrierefreiheit via WCAG, Confluence verneint
    assert luecken["Ben Visual"] == []

    lauf(env, "antwort", "--kandidat", "Anna Test", "--begriff", "Confluence", "--antwort", "ja", "--projekt", "P1")
    lauf(env, "auswerten", "--stichtag", "2026-11-16")
    anna = {l["begriff"]: (l["tun"], l["projekt"]) for l in json.loads(lauf(env, "luecken", "--kandidat", "Anna Test"))}
    assert anna["Confluence"] == ("bejaht – einspeisen", "P1"), anna

    with zipfile.ZipFile(ziel / "marktbild.xlsx") as z:
        assert z.testzip() is None
        blatt = z.read("xl/worksheets/sheet1.xml").decode()
        assert "Barrierefreiheit" in blatt and "<autoFilter" in blatt
    text = (ziel / "bericht.md").read_text()
    assert "Originale/unbekannt" in text and "## UX/UI (2 Ausschreibungen)" in text, text

    # unbekannter Begriff wird gemeldet, nicht still gezählt
    schreib(markt / "anforderungen" / "A4 neu.json", {"anfrage": "A4 neu", "datum": "2026-11-10",
            "rollenfamilie": "UX/UI", "anforderungen": [{"begriff": "Kubernetes", "stufe": "muss"}]})
    assert "Kubernetes" in lauf(env, "offen")
    r = subprocess.run([sys.executable, str(SKRIPT), "auswerten"], capture_output=True, text=True, env=env)
    assert r.returncode != 0 and "Kubernetes" in r.stderr

print("selbsttest ok")
