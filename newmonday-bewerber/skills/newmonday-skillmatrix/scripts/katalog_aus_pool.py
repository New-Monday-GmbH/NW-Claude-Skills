#!/usr/bin/env python3
"""Schreibt references/attribute-katalog.md aus dem Figma-Pool.

    python3 scripts/katalog_aus_pool.py arbeit/pool.json

Die JSON ist die Rueckgabe des Lese-Skripts aus references/figma-vorlage.md —
eine Liste [[Kategoriename, [[Attribut, Beschreibung], …]], …], gelesen aus dem
Frame `Skill Matrix Pool Refactored`.

Der Pool ist die Quelle, der Katalog die Kopie. Dieses Skript ist der einzige
Weg, sie zu erzeugen: von Hand nachgepflegt laufen die beiden nach zwei
Aenderungen wieder auseinander — genau das war der Zustand, den der Refactor
beendet hat.

Prueft beim Schreiben mit und bricht ab, wenn der Pool die Hausregeln verletzt:
Bindestriche in Attributnamen, doppelte Namen, zu lange Beschreibungen.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIEL = ROOT / "references" / "attribute-katalog.md"
MAX_BESCHREIBUNG = 90

KOPF = """# Attribut-Katalog — Skills, Kategorien und Standardbeschreibungen

Der Katalog spiegelt **1:1 den Figma-Frame `Skill Matrix Pool Refactored`** in
der Datei `Portfolio - CV Master` (Section „SKill Matrix Pool"). Er ist der
**Wortschatz** der Skillmatrix: Steht ein Attribut hier, werden Name und
Beschreibung **woertlich** uebernommen — so tragen alle Matrizen fuer denselben
Skill denselben Text, und die Dokumente bleiben ueber Kandidaten hinweg
vergleichbar. Nur was hier fehlt, wird neu formuliert, im selben Stil
(Muster am Ende).

**Der Pool ist die Quelle, diese Datei die Kopie.** Bei Abweichung gewinnt
Figma. Erzeugt wird sie mit `scripts/katalog_aus_pool.py` — nicht von Hand
nachgepflegt.

## Die harten Regeln

- **Ab drei Punkten, sonst gar nicht.** Ein Skill kommt nur in die Matrix, wenn
  die Bewertung **mindestens 3** ergibt. Alles darunter wird **nicht
  angezeigt** — nicht abgewertet, nicht in Klammern, nicht kleiner gesetzt:
  weggelassen. Eine Skillmatrix ist ein Verkaufsdokument; was schwach belegt
  ist, gehoert nicht hinein.
- **Hoechstens 24 Kernkompetenzen.** Die Sektion traegt maximal **vier
  Kategorien zu je sechs Skills**, gesetzt als **drei Karten pro Reihe, zwei
  Reihen** je Kategorie.
- **`Tools` ist eine eigene Sektion**, keine Kategorie. Sie bekommt eine eigene
  Ueberschrift mit Icon wie „Kernkompetenzen" und steht **davor**; ein
  Kategorielabel innerhalb der Sektion entfaellt. Sie zaehlt nicht gegen die
  24. `Coding Skills` ist dagegen eine gewoehnliche Kategorie innerhalb der
  Kernkompetenzen und ersetzt dann eine der vier.
- **Attributnamen sind englisch**, Beschreibungen deutsch. Eine Spalte, keine
  zweite. Fuer eine englische Matrix wird beim Bauen uebersetzt und in der
  Uebergabe gemeldet.
- **Keine Bindestriche in Attributnamen.** „Microinteractions", nicht
  „Micro-interactions"; „Data Driven Design", nicht „Data-Driven Design".
- **Produktnamen so, wie der Hersteller sie schreibt.** Belegbare
  Eigenschreibung schlaegt jede Zuruf-Variante — „Fullstory", nicht
  „FullStory"; „Hotjar", nicht „HotJar"; „UXPin", nicht „UxPin". Im Zweifel
  auf der Herstellerseite nachsehen und die Abweichung in der Uebergabe
  nennen, statt sie stillschweigend zu uebernehmen.
- **Jeder Name kommt genau einmal vor**, ueber alle Kategorien hinweg.

## Die Kategorien

"""

FUSS = """
---

## Neue Attribute formulieren

Wenn der Eingang etwas belegt, das im Katalog fehlt (eine Branche, ein Tool,
eine Spezialitaet), wird ein neues Attribut im Katalogstil angelegt:

- **Name**: englisch, kurz, wie ein Fachbegriff — kein Satz, **kein
  Bindestrich**. Produktnamen in der Eigenschreibung des Herstellers.
- **Beschreibung**: deutsch, eine Zeile, hoechstens etwa 90 Zeichen. Sachlich
  beschreiben, was die Person damit tut — kein „exzellent", „langjaehrig",
  „leidenschaftlich". Die Bewertung machen die Punkte, nicht das Adjektiv.
  Punkt am Ende.
- **Pruefen, ob es das schon gibt.** „UX Research" und „Qualitative Research"
  nebeneinander auf einer Matrix sagen zweimal dasselbe.

Beispiele fuer den Ton: „Strukturierung komplexer Informationen." /
„Produkte mit echten Nutzern testen." / „Photoshop, Illustrator und After Effects."

**Ein neues Attribut gehoert in den Figma-Pool**, nicht nur in diese Datei.
Sonst faellt es beim naechsten Lauf wieder heraus.
"""


def pruefe(daten):
    """Sammelt Regelverstoesse. Aendert nichts."""
    fehler = []
    namen = [n for _, attrs in daten for n, _ in attrs]
    for n in sorted({x for x in namen if namen.count(x) > 1}):
        fehler.append(f"Attributname doppelt: {n}")
    for kat, attrs in daten:
        for name, beschr in attrs:
            if "-" in name:
                fehler.append(f"Bindestrich im Namen: {name} ({kat})")
            if len(beschr) > MAX_BESCHREIBUNG:
                fehler.append(f"Beschreibung {len(beschr)} Zeichen: {name} ({kat})")
            if not beschr.endswith("."):
                fehler.append(f"Beschreibung ohne Punkt: {name} ({kat})")
    return fehler


def rendern(daten):
    teile = [KOPF]
    teile.append("\n".join(f"{i+1}. **{k}** ({len(a)})"
                           for i, (k, a) in enumerate(daten)))
    teile.append(
        "\n\nEine Matrix nimmt **drei bis vier** Kategorien als Kernkompetenzen "
        "— die, die das Profil belegt, die staerkste zuerst — und dazu optional "
        "`Tools`.\n\n---\n")
    for kat, attrs in daten:
        teile.append(f"\n## {kat}\n\n| Attribut | Beschreibung |\n|---|---|\n")
        for name, beschr in attrs:
            teile.append(f"| {name} | {beschr} |\n")
    teile.append(FUSS)
    return "".join(teile)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    daten = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    fehler = pruefe(daten)
    if fehler:
        print("Der Pool verletzt die Hausregeln — nichts geschrieben:",
              file=sys.stderr)
        for f in fehler:
            print(f"  - {f}", file=sys.stderr)
        raise SystemExit(1)

    ZIEL.write_text(rendern(daten), encoding="utf-8")
    print(f"{ZIEL} geschrieben — {len(daten)} Kategorien, "
          f"{sum(len(a) for _, a in daten)} Attribute")


if __name__ == "__main__":
    main()
