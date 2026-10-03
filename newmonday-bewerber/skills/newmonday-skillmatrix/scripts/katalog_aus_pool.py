#!/usr/bin/env python3
"""Schreibt references/attribute-katalog.md aus dem Figma-Pool.

    python3 scripts/katalog_aus_pool.py arbeit/pool.json

Die JSON liefert ein lesender use_figma-Aufruf ueber den Frame
`Skill Matrix Pool Refactored` der Masterdatei: je Kategorie-Abschnitt der Titel,
je Skill Card Titel und Beschreibung - als Liste
[[Kategoriename, [[Attribut, Beschreibung], …]], …], in Pool-Reihenfolge.

Der Pool ist die Quelle, der Katalog die Kopie. Dieses Skript ist der einzige
Weg, sie zu erzeugen: von Hand nachgepflegt laufen die beiden nach zwei
Aenderungen wieder auseinander — genau das war der Zustand, den der Refactor
beendet hat.

Die Spalte "deutsch" kommt nicht aus dem Pool, sondern aus DEUTSCH und
GRENZFAELLE unten: die Namen, die eine deutsche Matrix traegt, wenn der
englische Name kein eingefuehrter Fachbegriff ist (SKILL.md, Schritt 0,
Namensregel). Wer dort etwas aendert, laesst das Skript neu laufen.

Prueft beim Schreiben mit und bricht ab, wenn der Pool die Hausregeln verletzt:
Bindestriche in englischen Attributnamen, doppelte Namen, zu lange
Beschreibungen, deutsche Formen zu Attributen, die es im Pool nicht gibt.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIEL = ROOT / "references" / "attribute-katalog.md"
MAX_BESCHREIBUNG = 90

# Deutsche Form je Attribut, wo der englische Name nur eine Uebersetzung ist.
# Fehlt ein Attribut hier, bleibt es auch in einer deutschen Matrix englisch:
# eingefuehrte Fachbegriffe (Journey Mapping, Design Systems), Methoden,
# Rollen, Produkt- und Technologienamen - und alle KI-Begriffe (AI Prototyping,
# AI in Research): So stehen sie in der Branche und in der Vorschau, die der
# Nutzer am 2026-10-03 gewaehlt hat.
DEUTSCH = {
    "UX Strategy": "UX-Strategie",
    "UX Principles & Guidelines": "UX-Prinzipien & Guidelines",
    "Persona Creation": "Persona-Erstellung",
    "Pain Point Analysis": "Pain-Point-Analyse",
    "Competitive Analysis": "Wettbewerbsanalyse",
    "Behavioral Analysis": "Verhaltensanalyse",
    "Research Synthesis": "Research-Synthese",
    "Conversion Optimization": "Conversion-Optimierung",
    "Scalable UI Concepts": "Skalierbare UI-Konzepte",
    "Consistent Interfaces": "Konsistente Interfaces",
    "Component Based Design": "Komponentenbasiertes Design",
    "Figma Component Systems": "Figma-Komponentensysteme",
    "UI Quality Assurance": "UI-Qualitätssicherung",
    "Component Standards": "Komponentenstandards",
    "Documentation": "Dokumentation",
    "Cross Platform Consistency": "Plattformübergreifende Konsistenz",
    "UX/UI Scaling": "UX/UI-Skalierung",
    "Test Planning": "Testplanung",
    "Test Moderation": "Testmoderation",
    "Prototype Validation": "Prototyp-Validierung",
    "Heuristic Evaluation": "Heuristische Evaluation",
    "Regulatory Compliance": "Regulatorische Anforderungen",
    "Agile UX Collaboration": "Zusammenarbeit in agilen Teams",
    "Sprint Support": "Sprint-Begleitung",
    "Iterative Improvement": "Iterative Verbesserung",
    "Design Presentation": "Designpräsentation",
    "Cross Team Alignment": "Teamübergreifende Abstimmung",
    "Conflict Resolution": "Konfliktlösung",
    "Dev Collaboration": "Zusammenarbeit mit Entwicklern",
    "UX Specifications": "UX-Spezifikationen",
    "Frontend Understanding": "Frontend-Verständnis",
    "Feasibility Assessment": "Machbarkeitsprüfung",
}

# Grenzfaelle: Der englische Name bleibt, die deutsche Alternative steht als
# Vermerk in der Tabelle - zum Nachschauen, falls jemand anders entscheidet.
GRENZFAELLE = {
    "User Centered Design": "Nutzerzentriertes Design",
    "Experience Vision": "Zielbild für das Nutzererlebnis",
    "Business to UX Translation": "Anforderungen in UX übersetzen",
    "Data Driven Design": "Datengetriebenes Design",
    "Microinteractions": "Mikrointeraktionen",
    "Product Systemization": "Systematisierung im Produkt",
    "Insight Reporting": "Aufbereitung von Testergebnissen",
    "Accessible Design": "Barrierefreies Design",
    "MVP Delivery": "MVP-Entwicklung",
    "Teamlead": "Teamleitung",
    "Decision Facilitation": "Entscheidungen begleiten",
    "Consulting": "Beratung",
}

KOPF = """# Attribut-Katalog — Skills, Kategorien und Standardbeschreibungen

Der Katalog spiegelt **1:1 den Figma-Frame `Skill Matrix Pool Refactored`** in
der Datei `Portfolio - CV Master` (Section „SKill Matrix Pool"). Er ist der
**Wortschatz** der Skillmatrix: Steht ein Attribut hier, werden Name,
Beschreibung und Kategorie **woertlich** uebernommen — so tragen alle Matrizen
fuer denselben Skill denselben Text am selben Ort, und die Dokumente bleiben
ueber Kandidaten hinweg vergleichbar. Nur was hier fehlt, wird neu formuliert,
im selben Stil (Muster am Ende).

**Der Pool ist die Quelle, diese Datei die Kopie.** Bei Abweichung gewinnt
Figma. Erzeugt wird sie mit `scripts/katalog_aus_pool.py` — nicht von Hand
nachgepflegt. Einzige Zutat des Skills ist die Spalte „deutsch“: Sie steht im
Skript (`DEUTSCH`, `GRENZFAELLE`), nicht im Pool.

## Die harten Regeln

- **Ab drei Punkten, sonst gar nicht.** Ein Skill kommt nur in die Matrix, wenn
  die Bewertung **mindestens 3** ergibt. Alles darunter wird **nicht
  angezeigt** — nicht abgewertet, nicht in Klammern, nicht kleiner gesetzt:
  weggelassen. Eine Skillmatrix ist ein Verkaufsdokument; was schwach belegt
  ist, gehoert nicht hinein.
- **Hoechstens 24 Kernkompetenzen.** Die Sektion traegt hoechstens **sechs
  Skills je Kategorie**, gesetzt als **drei Karten pro Reihe, zwei Reihen**,
  und hoechstens **fuenf Kategorien**, ueblich sind drei bis vier.
- **`Tools` ist eine eigene Sektion**, keine Kategorie. Sie bekommt eine eigene
  Ueberschrift mit Tools-Icon wie „Kernkompetenzen" und steht **danach**; ein
  Kategorielabel innerhalb der Sektion entfaellt. Sie traegt hoechstens sechs
  Tools, die der Eingang nennt, und zaehlt nicht gegen die 24. Nennt der
  Eingang keine, fragt der Skill in der Freigabe, ob rollentypische Tools
  ergaenzt werden sollen. Ein Tool steht nur dort und nicht noch einmal
  als Skill in den Kernkompetenzen. `Coding Skills` ist dagegen eine
  gewoehnliche Kategorie innerhalb der Kernkompetenzen.
- **Namen: Fachbegriffe englisch, Uebersetzungen deutsch.** Kategorienamen
  sind immer englisch. Ein Attributname bleibt in einer deutschen Matrix nur
  englisch, wenn er ein eingefuehrter Fachbegriff ist, den man im deutschen
  UX-Alltag so sagt (Wireframing & Prototyping, Design Systems, Information
  Architecture, Journey Mapping, alle KI-Begriffe wie AI Prototyping). Ist der
  englische Name nur eine Uebersetzung,
  traegt die deutsche Matrix die Form aus der Spalte „deutsch“ („Frontend
  Understanding“ → „Frontend-Verständnis“). Leer heisst: bleibt englisch.
  *Grenzfall* heisst: bleibt englisch, die deutsche Alternative steht daneben.
  Eine englische Matrix traegt immer die englischen Namen. Beschreibungen sind
  deutsch; fuer eine englische Matrix wird beim Bauen uebersetzt und in der
  Uebergabe gemeldet.
- **Keine Bindestriche in englischen Attributnamen.** „Microinteractions",
  nicht „Micro-interactions"; „Data Driven Design", nicht „Data-Driven Design".
  Deutsche Formen folgen der deutschen Rechtschreibung und koppeln englische
  Teile mit Bindestrich („Pain-Point-Analyse“).
- **Produktnamen so, wie der Hersteller sie schreibt.** Belegbare
  Eigenschreibung schlaegt jede Zuruf-Variante — „Fullstory", nicht
  „FullStory"; „Hotjar", nicht „HotJar"; „UXPin", nicht „UxPin". Im Zweifel
  auf der Herstellerseite nachsehen und die Abweichung in der Uebergabe
  nennen, statt sie stillschweigend zu uebernehmen.
- **Jeder Name kommt genau einmal vor**, ueber alle Kategorien hinweg.
- **Ein Attribut steht in seiner Kategorie.** In der Matrix steht jedes
  Attribut unter der Kategorie, unter der es hier gefuehrt wird, wenn die in
  der Matrix vorkommt — auch wenn eine alte Matrix des Kandidaten es anderswo
  einsortiert hatte. Fehlt sie, steht es in der inhaltlich naechsten Kategorie
  der Matrix (Tabelle `VERWANDT` in `scripts/render_skillmatrix.py`), nie in
  einer fachfremden. Das Renderskript meldet beides.

## Die Kategorien

"""

FUSS = """
---

## Neue Attribute formulieren

Wenn der Eingang etwas belegt, das im Katalog fehlt (eine Branche, ein Tool,
eine Spezialitaet), wird ein neues Attribut im Katalogstil angelegt:

- **Name**: englisch, kurz, wie ein Fachbegriff — kein Satz, **kein
  Bindestrich**. Produktnamen in der Eigenschreibung des Herstellers. Ist der
  englische Name kein eingefuehrter Fachbegriff, bekommt er dazu eine deutsche
  Form fuer deutsche Matrizen (`DEUTSCH` in `scripts/katalog_aus_pool.py`).
- **Kategorie**: die Katalog-Kategorie, zu der es inhaltlich gehoert — keine
  neue.
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
    for n in sorted((set(DEUTSCH) | set(GRENZFAELLE)) - set(namen)):
        fehler.append(f"Deutsche Form zu einem Attribut, das der Pool nicht fuehrt: {n} "
                      "— umbenannt oder entfernt? DEUTSCH/GRENZFAELLE nachziehen.")
    for n in sorted(set(DEUTSCH) & set(GRENZFAELLE)):
        fehler.append(f"{n} steht in DEUTSCH und in GRENZFAELLE — nur eins von beiden.")
    alle = namen + list(DEUTSCH.values())
    for n in sorted({x for x in alle if alle.count(x) > 1}):
        fehler.append(f"Name doppelt (englisch oder deutsch): {n}")
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
        "\n\nEine Matrix nimmt **drei bis vier** Kategorien als Kernkompetenzen, "
        "hoechstens fuenf — die, die das Profil belegt, eine KI-Kategorie zuerst, "
        "danach die staerkste — und dazu optional `Tools`.\n\n---\n")
    for kat, attrs in daten:
        teile.append(f"\n## {kat}\n\n| Attribut | deutsch | Beschreibung |\n|---|---|---|\n")
        for name, beschr in attrs:
            if name in DEUTSCH:
                deutsch = DEUTSCH[name]
            elif name in GRENZFAELLE:
                deutsch = f"*Grenzfall, bleibt englisch (dt. „{GRENZFAELLE[name]}“)*"
            else:
                deutsch = ""
            teile.append(f"| {name} | {deutsch} | {beschr} |\n")
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
