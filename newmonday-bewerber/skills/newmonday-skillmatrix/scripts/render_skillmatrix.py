#!/usr/bin/env python3
"""Rendert skillmatrix.json in beiden Fassungen zu zwei PDFs.

    python3 scripts/render_skillmatrix.py daten/skillmatrix.json ausgabe/

Es entstehen immer beide Fassungen, aus derselben JSON:

  - lang: "New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf" - eine
    einzige lange Seite, so breit wie der Figma-Frame der Vorlage (1444pt), so
    hoch wie ihr Inhalt; sie bildet eine Webseite ab. Weil CSS keine Seite "so
    hoch wie der Inhalt" kennt, wird zweimal gerendert: erst auf Vorrat hoch,
    dann mit der gemessenen Inhaltshoehe.
  - A4:   "New-Monday - Vorname Nachname - Jobtitel - Skillmatrix A4.pdf" -
    595 x 842pt, mehrseitig, im Format des Lebenslaufs (Template
    template-a4.html, Tokens im Block "a4"). Kein Block bricht in sich um; der
    Fuss sitzt unten auf der letzten Seite (Luft davor gemessen, zweiter
    Durchgang). Welcher Block auf welcher Seite steht, legt das Skript im PDF
    ab (Dokumentinfo /NewMondaySeiten) - daraus baut figma_plan.py die Seiten.

Den Dateinamen setzt das Skript selbst aus den Daten. Das zweite Argument
bestimmt nur den Ordner — ein dort angehaengter Dateiname wird ersetzt
(Ausnahme: --pfad-genau, siehe main()).

Alle Farben, Abstaende, Radien, Schatten und Schriften kommen aus
assets/tokens.json (design_system.py erzeugt daraus das CSS). WeasyPrint kennt
kein box-shadow; im ersten Durchgang werden deshalb die Karten vermessen und
ihre Schatten als Bild gezeichnet, im zweiten liegen sie hinter den Karten.
Zum Schluss wird jedes PDF gegen die Tokens seiner Fassung geprueft —
Seitenformat, Schriften, Textstile, Farben. Weicht eins ab, endet das Skript
mit Code 2.

Sucht sich die Render-Engine selbst: WeasyPrint (bevorzugt), sonst headless
Chrome, sonst wkhtmltopdf - der Ausweichweg gilt nur fuer die lange Fassung,
die A4-Fassung braucht WeasyPrint (laufende Kopfzeile, gemessener Fuss). Prueft ausserdem die Daten auf Auffaelligkeiten und
schreibt sie nach stderr — darunter jedes Attribut ausserhalb seiner
Katalog-Kategorie (verwandt: Hinweis, fachfremd: WARNUNG, Tabelle VERWANDT) und
jeder Name, der nicht der Katalogform der Dokumentsprache entspricht
(references/attribute-katalog.md). Korrigiert wird nichts — mit zwei
Ausnahmen, die
gemeldet werden und die figma_plan.py genauso anwendet: Die KI-Kategorie
rueckt an die erste Stelle der Kernkompetenzen, und die Zertifikate werden
nach Datum sortiert und, wo der Platz nicht reicht, je Aussteller gebuendelt
(scripts/zertifikate.py). Die Zertifikatssektion wird im Layout vermessen;
ueber 924pt (tokens.json) gibt es einen Hinweis mit der Ueberschreitung.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert
import zertifikate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
KATALOG = ROOT / "references" / "attribute-katalog.md"

VORRAT_HOEHE = 12000         # pt, erster Durchgang — reicht fuer jede Matrix
PT_JE_PX = 0.75              # WeasyPrint rechnet intern in CSS-px (96 dpi)

# Der Ansprechpartner im Fuss steht als Vorgabe im Skill, nicht in der JSON.
# figma_plan.py liest ihn von hier. Telefonnummer und Adresse genau wie im
# Lebenslauf (newmonday-cv, KONTAKT_VORGABE) - beide Fassungen gleich.
KONTAKT_VORGABE = {
    "name": "Manuel Klein", "rolle": "CCO",
    "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0) 155 1148 0130",
    "firma": "New Monday GmbH", "strasse": "Stresemannstr. 23", "ort": "10963 Berlin",
}

BESCHRIFTUNG = {
    "de": {
        "verfuegbar": "Verfügbar ab",
        "zertifikate": "Zertifikate",
        "qualifikationen": "Erworbene Qualifikationen",
        "kernkompetenzen": "Kernkompetenzen",
        "tools": "Tools",
        "buendel": "+ {n} weitere Kurse von {aussteller}",
        "sammel": "+ {n} weitere Zertifikate",
        "footer_frage": "Bereit für das nächste Projekt?",
        "ansprechpartner": "Ansprechpartner", "kontakt": "Kontakt", "adresse": "Adresse",
    },
    "en": {
        "verfuegbar": "Available from",
        "zertifikate": "Certificates",
        "qualifikationen": "Acquired qualifications",
        "kernkompetenzen": "Core Skills",
        "tools": "Tools",
        "buendel": "+ {n} more courses from {aussteller}",
        "sammel": "+ {n} more certificates",
        "footer_frage": "Ready for the next project?",
        "ansprechpartner": "Contact person", "kontakt": "Contact", "adresse": "Address",
    },
}


# Sprachprobe fuer die Beschreibungen. Absichtlich grob und absichtlich
# schweigsam: gewarnt wird nur, wenn die Marker der FALSCHEN Sprache die der
# richtigen ueberwiegen. Ein Text ohne jeden Marker ("Photoshop, Illustrator,
# After Effects") bleibt unbeanstandet — lieber ein uebersehener Fall als eine
# Warnung, die man sich abgewoehnt zu lesen.
_DE_MARKER = re.compile(
    r"\b(der|die|das|und|für|von|mit|zur|zum|den|dem|eine|einen|einer|auf|aus"
    r"|durch|über|bei|nach|sowie|nicht|wird|werden|ohne|zwischen|zu|bis|um"
    r"|ihre|ihrer|echten)\b|[äöüßÄÖÜ]", re.I)
# Englisch zeigt sich hier an Funktionswoertern und am Gerundium AM ANFANG
# ("Designing …", "Using …"). Ein -ing mitten im Satz zaehlt nicht: deutsche
# Beschreibungen tragen Fachbegriffe wie "Prototyping" oder "Onboarding".
_EN_MARKER = re.compile(
    r"\b(the|and|for|with|of|to|into|across|within|from|by|their|its|real"
    r"|users|based|before|through)\b", re.I)
_EN_GERUND = re.compile(r"^\s*\w+ing\b", re.I)


def _sprachprobe(text):
    """(de_treffer, en_treffer) — je hoeher, desto sicherer die Sprache."""
    text = str(text or "")
    de = len(_DE_MARKER.findall(text))
    en = len(_EN_MARKER.findall(text)) + (1 if _EN_GERUND.match(text) else 0)
    return de, en


def _sprachhinweis(text, sprache, wo):
    de, en = _sprachprobe(text)
    if sprache == "de" and en > de and en:
        return (f"{wo}: sieht englisch aus, die Matrix ist deutsch — "
                f"„{text}“")
    if sprache == "en" and de > en and de:
        return (f"{wo}: looks German, the matrix is English — "
                f"“{text}”")
    return None


def pruefe(daten):
    """Sammelt Auffaelligkeiten. Aendert nichts."""
    hinweise = []
    sprache = daten.get("sprache", "de")
    person = daten.get("person") or {}
    for feld in ("name", "rolle", "beschreibung", "erfahrung", "verfuegbar_ab"):
        if not person.get(feld):
            hinweise.append(f"person.{feld} fehlt — die Zeile bleibt im Hero leer.")
    schwerpunkte = person.get("schwerpunkte") or []
    if len(schwerpunkte) > 3:
        hinweise.append(
            f"{len(schwerpunkte)} Schwerpunkte gesetzt — die Vorlage traegt drei. "
            "Die Buttons stehen in einer Zeile; mehr als drei laufen ueber die "
            "Textspalte hinaus.")
    if not person.get("foto"):
        hinweise.append("Kein Foto — die Fotokarte zeigt nur den Farbverlauf mit dem Namen.")
    elif not str(person["foto"]).startswith(("http:", "https:", "file:")):
        foto = Path(person["foto"]).expanduser()
        if not foto.is_absolute():
            foto = Path.cwd() / foto
        if not foto.exists():
            hinweise.append(f"Foto nicht gefunden: {foto} — die Fotokarte bliebe leer. "
                            "Relative Pfade gelten ab dem Arbeitsverzeichnis.")

    # Die Hero-Beschreibung ist der einzige laengere neue Text im Dokument und
    # steht in der Ich-Perspektive — die Matrix ist kein Steckbrief ueber den
    # Kandidaten, sondern ein Dokument, in dem er selbst spricht.
    beschreibung = person.get("beschreibung")
    if beschreibung:
        hinweis = _sprachhinweis(beschreibung, sprache, "person.beschreibung")
        if hinweis:
            hinweise.append(hinweis)
        ich = (r"\b(ich|mein|meine|meinen|meiner|meinem|mich|mir)\b"
               if sprache == "de" else r"\b(I|my|me|mine)\b")
        if not re.search(ich, str(beschreibung), 0 if sprache == "en" else re.I):
            hinweise.append(
                "person.beschreibung steht nicht in der Ich-Perspektive — in der "
                "Skill Matrix spricht der Kandidat selbst („Ich gestalte …“, "
                "nicht „Gestaltet …“).")

    # Zertifikate prueft zertifikate.planen() — samt Bildern, Karte und Hoehe.
    quali = daten.get("qualifikationen")
    if isinstance(quali, dict) and quali.get("text"):
        hinweis = _sprachhinweis(quali["text"], sprache, "qualifikationen.text")
        if hinweis:
            hinweise.append(hinweis)

    tools = daten.get("tools") or []
    hoechstens = design_system.laden()["komponenten"]["tools"]["anzahl"]
    if len(tools) > hoechstens:
        hinweise.append(
            f"{len(tools)} Tools gesetzt — die Sektion traegt hoechstens {hoechstens} "
            "(zwei Reihen). Die schwaechsten weglassen.")
    gruppen = [(k.get("kategorie"), k.get("skills") or []) for k in daten.get("kompetenzen") or []]
    for kategorie, _ in gruppen:
        if re.match(r"\s*tools\b", str(kategorie or ""), re.I):
            hinweise.append(
                f"Kategorie „{kategorie}“ unter den Kernkompetenzen — Tools haben eine "
                "eigene Sektion (JSON-Feld tools); Werkzeuge gehoeren dorthin.")
    if tools:
        gruppen.append((TOOLS_SEKTION, tools))
    for kategorie, skills in gruppen:
        if not skills:
            hinweise.append(f"Kategorie ohne Skills: {kategorie}")
        for s in skills:
            p = s.get("punkte")
            if not isinstance(p, int) or not 1 <= p <= 5:
                hinweise.append(
                    f"{s.get('name')}: punkte muss eine ganze Zahl 1–5 sein, ist {p!r}.")
            elif p < 3:
                hinweise.append(
                    f"{s.get('name')} steht mit {p} Punkten in der Matrix — in den "
                    "Vorlagen ist 3 die unterste Stufe, darunter wird weggelassen.")
            if not s.get("beschreibung"):
                hinweise.append(f"{s.get('name')}: beschreibung fehlt — die Karte wirkt leer.")
            elif len(str(s.get("beschreibung"))) > 110:
                hinweise.append(
                    f"{s.get('name')}: Beschreibung ist {len(str(s['beschreibung']))} Zeichen "
                    "lang — die Karten der Vorlage tragen ein bis zwei kurze Zeilen.")
            if s.get("beschreibung"):
                hinweis = _sprachhinweis(s["beschreibung"], sprache, s.get("name"))
                if hinweis:
                    hinweise.append(hinweis)
    hinweise += _doppelte(gruppen)
    hinweise += katalog_pruefen(daten)
    if not daten.get("kompetenzen"):
        hinweise.append("Keine Kernkompetenzen — die Matrix besteht dann nur aus dem Hero.")
    return hinweise


TOOLS_SEKTION = object()      # Kennung der Tools-Sektion - eine Kategorie darf auch "Tools" heissen

MAX_KATEGORIEN = 5            # SKILL.md, Schritt 2a


def _schluessel(name):
    """Vergleichsform eines Namens: "Micro-interactions" = "Microinteractions"."""
    return re.sub(r"[^0-9a-zäöüß+#]", "", str(name or "").lower())


def katalog_laden(pfad=KATALOG):
    """(attribute, kategorien) aus references/attribute-katalog.md.
    attribute: Vergleichsform des englischen Namens und der deutschen Form ->
    {"name", "deutsch" (None, wenn der Name englisch bleibt), "kategorie"}.
    kategorien: die Kategorienamen in Katalogreihenfolge."""
    attribute, kategorien, kat = {}, [], None
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        liste = re.match(r"\d+\. \*\*(.+?)\*\* \(\d+\)$", zeile.strip())
        if liste:
            kategorien.append(liste.group(1))
            continue
        titel = re.match(r"## (.+)$", zeile)
        if titel:
            kat = titel.group(1).strip() if titel.group(1).strip() in kategorien else None
            continue
        if not kat or not zeile.startswith("|"):
            continue
        zellen = [z.strip() for z in zeile.strip().strip("|").split("|")]
        if len(zellen) < 3 or zellen[0] == "Attribut" or not zellen[0].strip("-"):
            continue
        deutsch = zellen[1] if zellen[1] and not zellen[1].startswith("*") else None
        eintrag = {"name": zellen[0], "deutsch": deutsch, "kategorie": kat}
        attribute[_schluessel(zellen[0])] = eintrag
        if deutsch:
            attribute[_schluessel(deutsch)] = eintrag
    return attribute, kategorien


# Verwandtschaft der Katalog-Kategorien, naechste zuerst: Fehlt die
# Katalog-Kategorie eines Attributs in der Matrix (oder ist sie mit sechs Skills
# voll), steht es in einer der hier genannten. Jede andere Kategorie ist
# fachfremd - "Frontend-Verstaendnis" unter Accessibility etwa.
VERWANDT = {
    "UX Strategy & Product Discovery": ["User Research & Insights", "Stakeholder Management & Facilitation",
                                        "Agile Product Delivery", "Interaction & Visual Design"],
    "User Research & Insights": ["Usability Testing & Evaluation", "UX Strategy & Product Discovery"],
    "Interaction & Visual Design": ["UI Design & Visual Systems", "Design Systems & Scaling",
                                    "UX Strategy & Product Discovery"],
    "UI Design & Visual Systems": ["Interaction & Visual Design", "Design Systems & Scaling"],
    "Design Systems & Scaling": ["UI Design & Visual Systems", "Interaction & Visual Design",
                                 "Development Collaboration"],
    "Usability Testing & Evaluation": ["User Research & Insights", "UX Strategy & Product Discovery"],
    "Accessibility & Inclusive Design": ["Interaction & Visual Design", "UI Design & Visual Systems",
                                         "Usability Testing & Evaluation"],
    "Agile Product Delivery": ["Stakeholder Management & Facilitation", "Development Collaboration",
                               "UX Strategy & Product Discovery"],
    "Stakeholder Management & Facilitation": ["UX Strategy & Product Discovery", "User Research & Insights",
                                              "Agile Product Delivery"],
    "Development Collaboration": ["Coding Skills", "Agile Product Delivery", "Design Systems & Scaling"],
    "AI & Emerging Tech": ["Interaction & Visual Design", "User Research & Insights"],
    "Coding Skills": ["Development Collaboration"],
}
# Einzelne Attribute, deren naechste Kategorie eine andere ist als die ihrer
# Katalog-Kategorie - sie gehen zuerst dorthin.
VERWANDT_ATTRIBUT = {
    "Accessibility Audits": ["Accessibility & Inclusive Design"],
}


def katalog_pruefen(daten):
    """Kategorien und Namen gegen den Katalog (SKILL.md, Schritt 2a). Ein
    Katalog-Attribut steht in seiner Katalog-Kategorie, wenn die in der Matrix
    vorkommt; sonst (oder wenn sie voll ist) in einer verwandten (Hinweis), nie in
    einer fachfremden (Warnung). Namen in der Katalogform der Dokumentsprache.
    Hoechstens fuenf Kategorien, sechs Skills je Kategorie, 24 insgesamt."""
    if not KATALOG.exists():
        return [f"Katalog nicht gefunden: {KATALOG} — Kategorien und Namen ungeprueft."]
    attribute, kategorien = katalog_laden()
    sprache = daten.get("sprache", "de")
    hinweise = []
    unbekannt = ({k for k in VERWANDT} | {v for vs in list(VERWANDT.values())
                                          + list(VERWANDT_ATTRIBUT.values()) for v in vs}) - set(kategorien)
    if unbekannt:
        hinweise.append("VERWANDT in render_skillmatrix.py nennt Kategorien, die der Katalog nicht "
                        "mehr fuehrt: " + ", ".join(sorted(unbekannt)) + " — nachziehen.")
    kompetenzen = daten.get("kompetenzen") or []
    je_kategorie = 2 * design_system.laden()["komponenten"]["skillraster"]["spalten"]
    in_matrix = {str(k.get("kategorie") or ""): len(k.get("skills") or []) for k in kompetenzen}
    if len(kompetenzen) > MAX_KATEGORIEN:
        hinweise.append(f"{len(kompetenzen)} Kategorien — hoechstens {MAX_KATEGORIEN} (SKILL.md, "
                        "Schritt 2a). Attribute der kleinsten in verwandte Kategorien setzen.")
    if sum(in_matrix.values()) > 24:
        hinweise.append("Mehr als 24 Kernkompetenzen — die Sektion traegt hoechstens 24.")

    def name_pruefen(name, wo):
        e = attribute.get(_schluessel(name))
        if not e:
            return None
        soll = e["deutsch"] if sprache == "de" and e["deutsch"] else e["name"]
        if name != soll:
            if sprache == "de" and e["deutsch"] and name == e["name"]:
                grund = "in einer deutschen Matrix die deutsche Form"
            elif sprache != "de" and name == e["deutsch"]:
                grund = "in einer englischen Matrix den englischen Namen"
            else:
                grund = "die Schreibweise des Katalogs"
            hinweise.append(f"„{name}“ ({wo}): der Katalog fuehrt {grund} — „{soll}“.")
        return e

    for k in kompetenzen:
        kategorie = str(k.get("kategorie") or "")
        skills = k.get("skills") or []
        if kategorie not in kategorien:
            hinweise.append(f"Kategorie „{kategorie}“ steht nicht im Katalog — Kategorien werden "
                            "nicht erfunden (SKILL.md, Schritt 2a): "
                            + ", ".join(kategorien) + ".")
        if len(skills) > je_kategorie:
            hinweise.append(f"Kategorie „{kategorie}“ hat {len(skills)} Skills — hoechstens "
                            f"{je_kategorie} (zwei Reihen).")
        elif len(skills) == 1:
            hinweise.append(f"Kategorie „{kategorie}“ hat nur einen Skill — eine eigene Kategorie "
                            "lohnt sich ab zwei; den Skill in die naechstverwandte Kategorie setzen.")
        for s in skills:
            name = s.get("name")
            e = name_pruefen(name, kategorie)
            if not e or e["kategorie"] == kategorie:
                continue
            soll = e["kategorie"]
            if soll == "Tools":
                hinweise.append(f"WARNUNG: „{name}“ steht unter „{kategorie}“ — im Katalog ist es "
                                "ein Tool und gehoert in die Tools-Sektion.")
                continue
            verwandt = VERWANDT_ATTRIBUT.get(e["name"], []) + VERWANDT.get(soll, [])
            if kategorie not in verwandt:
                hinweise.append(
                    f"WARNUNG: „{name}“ steht unter „{kategorie}“ — fachfremd. Der Katalog fuehrt "
                    f"es unter „{soll}“; "
                    + (f"die steht in der Matrix, dorthin setzen." if soll in in_matrix else
                       "verwandt sind " + ", ".join(f"„{v}“" for v in dict.fromkeys(verwandt))
                       + " (SKILL.md, Schritt 2a)."))
            elif soll in in_matrix and in_matrix[soll] < je_kategorie:
                hinweise.append(
                    f"WARNUNG: „{name}“ steht unter „{kategorie}“, seine Katalog-Kategorie "
                    f"„{soll}“ steht aber in der Matrix und hat Platz — dorthin setzen.")
            else:
                grund = "voll ist" if soll in in_matrix else "in der Matrix fehlt"
                hinweise.append(f"„{name}“ steht in der naechstverwandten Kategorie „{kategorie}“, "
                                f"weil „{soll}“ {grund}. In der Uebergabe nennen.")
    for t in daten.get("tools") or []:
        name_pruefen(t.get("name"), "Tools")
    return hinweise

# Eine KI-Kategorie beginnt mit "AI" oder "KI" ("AI & Emerging Tech", "KI-Tools").
KI_KATEGORIE = re.compile(r"\s*(AI|KI)\b", re.I)


def kompetenzen_ordnen(daten):
    """Die KI-Kategorie steht immer an erster Stelle der Kernkompetenzen, danach
    die Reihenfolge der JSON. Gibt (daten, hinweis) zurueck — daten ist eine
    Kopie, wenn umsortiert wurde, sonst unveraendert und hinweis None. Rufen
    render_skillmatrix.py und figma_plan.py gleich auf, damit PDF und Frame
    dieselbe Reihenfolge haben."""
    kompetenzen = list(daten.get("kompetenzen") or [])
    ki = [k for k in kompetenzen if KI_KATEGORIE.match(str(k.get("kategorie") or ""))]
    neu = ki + [k for k in kompetenzen if not any(k is x for x in ki)]
    if all(a is b for a, b in zip(neu, kompetenzen)):
        return daten, None
    namen = ", ".join(f"„{k.get('kategorie')}“" for k in ki)
    return dict(daten, kompetenzen=neu), (
        f"KI-Kategorie {namen} an die erste Stelle der Kernkompetenzen gesetzt — sie "
        "steht immer zuerst (SKILL.md, Schritt 3). In der skillmatrix.json nachziehen.")


def beschriftung(daten):
    """Rubriken in der Dokumentsprache; die Ueberschrift der Zertifikatssektion
    laesst sich ueberschreiben (ein Beispiel der Vorlage traegt
    "Zertifizierungen UX/UI")."""
    labels = dict(BESCHRIFTUNG.get(daten.get("sprache", "de"), BESCHRIFTUNG["de"]))
    if daten.get("zertifikate_titel"):
        labels["zertifikate"] = daten["zertifikate_titel"]
    return labels


def _namensteile(name):
    """'Figma / FigJam' -> {'figma', 'figjam', 'figmafigjam'}: Sammelnamen
    zaehlen auch mit jedem ihrer Teile."""
    norm = lambda s: re.sub(r"[^0-9a-z+#]", "", s.lower())      # C++ und C# bleiben verschieden
    teile = {norm(t) for t in re.split(r"\s*/\s*", str(name or ""))}
    teile.add(norm(str(name or "")))
    return {t for t in teile if t}


def _doppelte(gruppen):
    """Jeder Name steht einmal im Dokument; ein Tool nur in der Tools-Sektion."""
    hinweise, gesehen = [], []                 # (teile, name, kategorie)
    for kategorie, skills in gruppen:
        for s in skills:
            teile = _namensteile(s.get("name"))
            for teile_alt, name_alt, kat_alt in gesehen:
                if not teile & teile_alt:
                    continue
                if TOOLS_SEKTION in (kategorie, kat_alt) and kategorie != kat_alt:
                    if kategorie is TOOLS_SEKTION:
                        tool, skill, skill_kat = s.get("name"), name_alt, kat_alt
                    else:
                        tool, skill, skill_kat = name_alt, s.get("name"), kategorie
                    hinweise.append(
                        f"„{skill}“ unter „{skill_kat}“ doppelt das Tool „{tool}“ — ein Tool "
                        "steht nur in der Tools-Sektion; unter den Kernkompetenzen streichen.")
                else:
                    orte = [("Tools-Sektion" if k is TOOLS_SEKTION else k) for k in (kat_alt, kategorie)]
                    hinweise.append(
                        f"„{s.get('name')}“ steht doppelt ({orte[0]} und {orte[1]}) — "
                        "jeder Name kommt nur einmal vor.")
                break
            gesehen.append((teile, s.get("name"), kategorie))
    return hinweise


def _pfad_zu_uri(wert):
    """Relative Pfade aus der JSON beziehen sich aufs Arbeitsverzeichnis,
    gerendert wird aber aus assets/ heraus — darum absolut machen."""
    if not wert or str(wert).startswith(("file:", "http:", "https:")):
        return wert
    p = Path(wert).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists() and p not in _GEMELDET:
        _GEMELDET.add(p)
        print(f"Warnung: Datei nicht gefunden: {p}", file=sys.stderr)
    return p.as_uri()


_GEMELDET = set()


def html_bauen(daten, hoehe, design, schatten=None, zplan=None):
    """schatten: Karten-ID -> Schattenbild samt Lage, nur im zweiten
    WeasyPrint-Durchgang. Ohne sie zeichnet Chrome box-shadow selbst.
    zplan: Ergebnis von zertifikate.planen(), None ohne Zertifikate."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(ASSETS)),
        autoescape=select_autoescape(["html"]),
    )
    labels = beschriftung(daten)

    daten = dict(daten)
    person = dict(daten.get("person") or {})
    person["foto"] = _pfad_zu_uri(person.get("foto"))
    daten["person"] = person
    if zplan:
        zplan = dict(zplan, eintraege=[dict(e, src=_pfad_zu_uri(e["bild"]) if e.get("bild") else None)
                                       for e in zplan["eintraege"]])

    daten["kontakt"] = dict(KONTAKT_VORGABE, **(daten.get("kontakt") or {}))
    komponenten = design["komponenten"]
    return env.get_template("template.html").render(
        hoehe=hoehe, t=labels,
        design_css=design_system.css(design),
        seitenbreite=komponenten["seite"]["breite"],
        skill_spalten=komponenten["skillraster"]["spalten"],
        punkte_anzahl=komponenten["punkte"]["anzahl"],
        schatten=schatten or {},
        z=zplan, g=(zplan or {}).get("geometrie"),
        **{k: v for k, v in daten.items() if k not in ("zertifikate", "zertifikat_bilder")})


def chrome_pfad():
    kandidaten = [
        "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for k in kandidaten:
        p = shutil.which(k) or (k if os.path.exists(k) else None)
        if p:
            return p
    return None


def _kaesten(box):
    yield box
    for kind in getattr(box, "children", None) or []:
        yield from _kaesten(kind)


def _kasten(box):
    """Rahmenkasten eines Layout-Kastens in pt."""
    return {
        "x": box.border_box_x() * PT_JE_PX, "y": box.border_box_y() * PT_JE_PX,
        "breite": box.border_width() * PT_JE_PX, "hoehe": box.border_height() * PT_JE_PX,
        "rahmen_links": box.border_left_width * PT_JE_PX,
        "rahmen_oben": box.border_top_width * PT_JE_PX,
    }


def _elemente(wurzel):
    """Je HTML-Element sein erster (Haupt-)Kasten, in Dokumentreihenfolge."""
    gesehen = set()
    for box in _kaesten(wurzel):
        element = getattr(box, "element", None)
        if element is None or id(element) in gesehen or not hasattr(box, "border_width"):
            continue
        gesehen.add(id(element))
        yield element, box


def layout_pruefen(wurzel, design):
    """Hinweise, die erst das fertige Layout zeigt."""
    hinweise = []
    spalte = design["komponenten"]["hero"]["textspalte"]
    for element, box in _elemente(wurzel):
        if "hero__schwerpunkte" in (element.get("class") or ""):
            buttons = [_kasten(k) for k in box.children if hasattr(k, "border_width")]
            if buttons:
                breite = buttons[-1]["x"] + buttons[-1]["breite"] - buttons[0]["x"]
                if breite > spalte + 0.5:
                    hinweise.append(
                        f"Die Schwerpunkt-Buttons sind zusammen {breite:.0f}pt breit, "
                        f"die Textspalte {spalte}pt — kuerzere Begriffe waehlen.")
    return hinweise


def zertsektion_messen(wurzel):
    """Hoehe der Zertifikatssektion im Layout in pt, None ohne Sektion."""
    for element, box in _elemente(wurzel):
        if "zertsektion" in (element.get("class") or "").split():
            return round(_kasten(box)["hoehe"], 2)
    return None


def rendern_weasyprint(daten, design, ziel, zplan=None):
    """Zwei Durchgaenge. Der erste liefert Inhaltshoehe und Kartengroessen, der
    zweite rendert mit exakter Hoehe und den Schattenbildern hinter den Karten.
    Gibt (engine, hoehe_pt, anzahl_schatten, hinweise, zertsektion_pt) zurueck;
    ImportError, wenn WeasyPrint fehlt."""
    from weasyprint import HTML
    basis = ASSETS.as_uri() + "/"
    doc = HTML(string=html_bauen(daten, VORRAT_HOEHE, design, zplan=zplan),
               base_url=basis).render()
    wurzel = doc.pages[0]._page_box
    html_kasten = wurzel.children[0]
    hoehe = math.ceil((html_kasten.position_y + html_kasten.margin_height()) * PT_JE_PX)
    hinweise = layout_pruefen(wurzel, design)
    zert_hoehe = zertsektion_messen(wurzel)

    with tempfile.TemporaryDirectory() as tmp:
        cache, schatten = {}, {}
        for element, box in _elemente(wurzel):
            komponente = element.get("data-schatten")
            if not komponente:
                continue
            k = _kasten(box)
            eigenschaften = design["komponenten"][komponente]
            radius = design_system.aufloesen(design, eigenschaften["radius"])
            bild, rand = design_system.schatten_bild(
                design, eigenschaften["schatten"], k["breite"], k["hoehe"],
                min(radius, k["breite"] / 2, k["hoehe"] / 2), tmp, cache)
            schatten[element.get("id")] = {
                "src": bild.as_uri(),
                "links": round(-rand - k["rahmen_links"], 3),
                "oben": round(-rand - k["rahmen_oben"], 3),
                "breite": round(k["breite"] + 2 * rand, 3),
                "hoehe": round(k["hoehe"] + 2 * rand, 3),
            }
        HTML(string=html_bauen(daten, hoehe, design, schatten, zplan),
             base_url=basis).write_pdf(str(ziel))
    return "WeasyPrint", hoehe, len(schatten), hinweise, zert_hoehe


def rendern_ausweich(html, ziel):
    """Ohne WeasyPrint: headless Chrome, sonst wkhtmltopdf. Gibt den Namen der
    Engine zurueck. Schreibt nichts in den Skill-Ordner — die Engines bekommen
    eine Temporaerdatei mit <base>-Tag."""
    basis = ASSETS.as_uri() + "/"
    with tempfile.TemporaryDirectory() as tmp:
        seite = Path(tmp) / "matrix.html"
        seite.write_text(
            html.replace("<head>", f'<head><base href="{basis}">', 1), encoding="utf-8"
        )
        chrome = chrome_pfad()
        if chrome:
            with tempfile.TemporaryDirectory() as profil:
                subprocess.run([
                    chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    f"--user-data-dir={profil}", "--no-pdf-header-footer",
                    f"--print-to-pdf={ziel}", seite.as_uri(),
                ], check=True, capture_output=True, timeout=120)
            return "Chrome (headless) — Layout ist auf WeasyPrint abgestimmt, bitte pruefen"

        if shutil.which("wkhtmltopdf"):
            subprocess.run([
                "wkhtmltopdf", "--enable-local-file-access",
                "--margin-top", "0", "--margin-bottom", "0",
                "--margin-left", "0", "--margin-right", "0",
                str(seite), str(ziel),
            ], check=True, capture_output=True, timeout=120)
            return "wkhtmltopdf (eingeschraenktes CSS)"

    raise SystemExit(
        "Keine Render-Engine gefunden. python3 scripts/pruefe_umgebung.py "
        "zeigt, was fehlt und wie es installiert wird."
    )


def inhaltshoehe_messen(pdf):
    """Unterkante des Inhalts auf Seite 1, in pt ab Oberkante. None = nicht messbar.

    Gemessen wird am Bild, nicht am Text: Das unterste Element ist der teal
    gefuellte Footer, unter ihm ist die Vorratsseite weiss. Die letzte nicht
    weisse Pixelzeile ist also die Unterkante des Inhalts — das funktioniert
    fuer jede Engine gleich. Aufgeloest wird mit 36 dpi (0,5 px je pt), der
    Messfehler liegt damit bei 2pt und verschwindet in der Rundungsreserve.
    """
    zeile = None
    try:
        import fitz                                   # PyMuPDF, falls vorhanden
        seite = fitz.open(str(pdf))[0]
        pix = seite.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
        px, breite, hoehe = pix.samples, pix.width, pix.height
        n = pix.n
        for y in range(hoehe - 1, -1, -1):
            reihe = px[y * breite * n:(y + 1) * breite * n]
            if any(kanal < 247 for kanal in reihe):
                zeile = y
                break
        if zeile is not None:
            return (zeile + 1) / 0.5
    except ImportError:
        pass

    if not shutil.which("pdftoppm"):
        return None
    try:
        from PIL import Image
    except ImportError:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "mess"
        subprocess.run(
            ["pdftoppm", "-png", "-r", "36", "-f", "1", "-l", "1", str(pdf), str(prefix)],
            check=True, capture_output=True,
        )
        treffer = sorted(Path(tmp).glob("mess*.png"))
        if not treffer:
            return None
        bild = Image.open(treffer[0]).convert("L")
        px = bild.load()
        for y in range(bild.height - 1, -1, -1):
            if any(px[x, y] < 247 for x in range(bild.width)):
                return (y + 1) * 72 / 36
    return None


def zert_hoehe_pruefen(zplan, gemessen):
    """Meldet die gemessene Hoehe der Zertifikatssektion und jede
    Ueberschreitung der Grenze."""
    grenze, geplant = zplan["grenze"], zplan["hoehe"]
    print(f"Zertifikatssektion: {gemessen:g}pt hoch ({len(zplan['eintraege'])} Kacheln, "
          f"geplant {geplant:g}, Grenze {grenze})")
    hinweise = []
    if gemessen > grenze:
        hinweise.append(
            f"Zertifikatssektion {gemessen:g}pt hoch — {gemessen - grenze:g}pt ueber der "
            f"Grenze von {grenze}pt. Titel kuerzen oder Eintraege mit dem Nutzer streichen.")
    if abs(gemessen - geplant) > 1:
        hinweise.append(
            f"Zertifikatssektion im PDF {gemessen:g}pt, geplant {geplant:g}pt — ein Text "
            "bricht anders um als geschaetzt. Der Figma-Plan rechnet mit der geplanten "
            "Hoehe; Vorschau ansehen.")
    return hinweise


def seitenzahl(pdf):
    try:
        from pypdf import PdfReader
    except ImportError:
        return 0
    return len(PdfReader(str(pdf)).pages)


def dateiname(daten, fassung="lang"):
    """New-Monday - Vorname Nachname - Jobtitel - Skillmatrix.pdf, fuer die
    A4-Fassung "... - Skillmatrix A4.pdf".

    Der Name kommt aus den Daten, nicht aus dem Aufrufargument: so heisst jede
    Matrix beim Kunden gleich, egal wie der Zielpfad getippt war. Fehlt ein
    Feld, faellt nur sein Abschnitt weg — eine Datei entsteht trotzdem.
    """
    person = daten.get("person") or {}
    teile = ["New-Monday"]
    for feld in ("name", "rolle"):
        wert = re.sub(r'[/\\:*?"<>|]', "-", str(person.get(feld) or ""))
        wert = re.sub(r"\s+", " ", wert).strip(" .")
        if wert:
            teile.append(wert)
    teile.append("Skillmatrix" if fassung == "lang" else "Skillmatrix A4")
    return " - ".join(teile) + ".pdf"


def zielpfad(argument, daten, fassung="lang"):
    """Ordner aus dem Argument, Dateiname aus den Daten."""
    name = dateiname(daten, fassung)
    pdf_gemeint = argument.suffix.lower() == ".pdf"
    ordner = argument.parent if pdf_gemeint else argument
    if pdf_gemeint and argument.name != name and fassung == "lang":
        print(f"Dateiname gesetzt: {argument.name} -> {name}")
    return ordner / name


# --- A4-Fassung --------------------------------------------------------------

SEITEN_SCHLUESSEL = "/NewMondaySeiten"     # Dokumentinfo: Block -> Seite, fuer figma_plan.py


def a4_seitenmasse(ds_a4):
    """@page-Werte der A4-Fassung in pt, aus den Tokens: oben Rand, Kopfzeile
    und Abstand zum Inhalt; rechts nur bis zur Kante des Fusses."""
    K = ds_a4["komponenten"]
    s, k = K["seite"], K["kopf"]
    return {"breite": s["breite"], "hoehe": s["hoehe"], "inhalt": s["inhalt"],
            "oben": s["rand-oben"] + k["hoehe"] + k["abstand-inhalt"],
            "rechts": s["breite"] - s["rand-links"] - K["fuss"]["breite"],
            "unten": s["rand-unten"], "links": s["rand-links"],
            "kopf_oben": s["rand-oben"]}


def foto_a4(daten):
    """(Pfad des A4-Fotos, hinweise). Reihenfolge: person.foto_a4, sonst
    foto-<name>-a4.png neben person.foto (kopf_ausschnitt.py legt ihn dort ab),
    sonst ein Zuschnitt aus person.foto selbst - mit Hinweis, denn aus dem
    Original haette der Kopf mehr Luft."""
    person = daten.get("person") or {}
    if person.get("foto_a4"):
        return person["foto_a4"], []
    foto = person.get("foto")
    if not foto or str(foto).startswith(("http:", "https:", "file:")):
        return foto, []
    p = Path(foto).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    neben = p.with_name(f"{p.stem}-a4.png")
    if neben.exists():
        return str(neben), []
    if not p.exists():
        return foto, []                      # pruefe() meldet das fehlende Foto
    import hashlib
    import kopf_ausschnitt
    kennung = hashlib.sha1(p.read_bytes()).hexdigest()[:12]
    ordner = Path(tempfile.gettempdir()) / "newmonday-skillmatrix" / "a4-fotos" / kennung
    ausgabe, bericht = kopf_ausschnitt.zuschneiden(p, ordner, flaechen=("a4",), kontrolle=False)
    return str(ausgabe), [
        f"A4-Foto: {neben.name} fehlt neben dem Foto — aus {p.name} zugeschnitten. Besser aus "
        "dem Original: kopf_ausschnitt.py <original> arbeit/fotos/ legt beide Zuschnitte ab."
        + "".join(f" {h}" for h in bericht["hinweise"])]


def zert_a4(zplan, ds_a4):
    """Die Kacheln der langen Fassung (dieselben Eintraege, Buendel und
    Kurzformen) mit den Bildmassen der A4-Buehne. None ohne Zertifikate."""
    if not zplan:
        return None
    K = ds_a4["komponenten"]
    T, B = K["zertkachel"], K["zertbuehne"]
    bp = design_system.aufloesen(ds_a4, B["padding"])
    platz = (T["breite"] - 2 * bp, T["buehne-hoehe"] - 2 * bp)
    eintraege = []
    for e in zplan["eintraege"]:
        _, px = zertifikate._bildgroesse(e.get("bild"))
        format_ = (px[0] / px[1]) if px else K["zertbild"]["platz-format"]
        breite, hoehe = zertifikate._einpassen(format_, *platz)
        eintraege.append(dict(e, a4_breite=breite, a4_hoehe=hoehe,
                              src=_pfad_zu_uri(e["bild"]) if e.get("bild") else None))
    return dict(zplan, eintraege=eintraege)


def html_bauen_a4(daten, ds_a4, za4, fussluft):
    """Das HTML der A4-Fassung. fussluft: Hoehe der Luft vor dem Fuss in pt."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(loader=FileSystemLoader(str(ASSETS)),
                      autoescape=select_autoescape(["html"]))
    daten = dict(daten)
    person = dict(daten.get("person") or {})
    person["foto"] = _pfad_zu_uri(foto_a4(daten)[0])
    daten["person"] = person
    daten["kontakt"] = dict(KONTAKT_VORGABE, **(daten.get("kontakt") or {}))
    K = ds_a4["komponenten"]
    g = {"spalten": K["zertkachel"]["spalten"], "titel_zeilen": K["zertkachel"]["titel-zeilen"],
         "meta_zeilen": K["zertkachel"]["meta-zeilen"]}
    return env.get_template("template-a4.html").render(
        t=beschriftung(daten), design_css=design_system.css(ds_a4), p=a4_seitenmasse(ds_a4),
        spalten=K["eintraege"]["spalten"], punkte_anzahl=K["punkte"]["anzahl"],
        z=za4, g=g, fussluft=round(fussluft, 2),
        **{k: v for k, v in daten.items() if k not in ("zertifikate", "zertifikat_bilder")})


def _bloecke_je_seite(doc):
    """{block: [seiten]} aus dem Layout: jedes Element mit data-block und die
    Seiten, auf denen es steht (1-basiert)."""
    bloecke = {}
    for nr, seite in enumerate(doc.pages, start=1):
        for element, _ in _elemente(seite._page_box):
            name = element.get("data-block")
            if name and nr not in bloecke.setdefault(name, []):
                bloecke[name].append(nr)
    return bloecke


def _fuss_unterkante(doc):
    """(Seite, Unterkante des Fusses in pt) im gelayouteten Dokument."""
    for nr in range(len(doc.pages), 0, -1):
        for element, box in _elemente(doc.pages[nr - 1]._page_box):
            if "fuss" in (element.get("class") or "").split():
                k = _kasten(box)
                return nr, k["y"] + k["hoehe"]
    return None, None


def seiten_ablegen(pdf, bloecke):
    """Legt die Seitenaufteilung im PDF ab (Dokumentinfo /NewMondaySeiten):
    {"seiten": n, "bloecke": {block: seite}}. figma_plan.py liest sie dort.
    Gibt einen Hinweis zurueck, wenn pypdf fehlt, sonst None."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return ("A4: pypdf fehlt — die Seitenaufteilung steht nicht im PDF, figma_plan.py "
                "kann die A4-Seiten nicht bauen (pip3 install pypdf).")
    leser = PdfReader(str(pdf))
    schreiber = PdfWriter(clone_from=leser)
    schreiber.add_metadata({SEITEN_SCHLUESSEL: json.dumps(
        {"fassung": "a4", "seiten": len(leser.pages),
         "bloecke": {k: v[0] for k, v in bloecke.items()}}, ensure_ascii=False)})
    with tempfile.NamedTemporaryFile(suffix=".pdf", dir=str(Path(pdf).parent), delete=False) as tmp:
        schreiber.write(tmp)
    os.replace(tmp.name, pdf)
    return None


def seiten_lesen(pdf):
    """Die Seitenaufteilung aus der Dokumentinfo eines A4-PDFs, None ohne."""
    from pypdf import PdfReader
    info = PdfReader(str(pdf)).metadata or {}
    wert = info.get(SEITEN_SCHLUESSEL)
    return json.loads(str(wert)) if wert else None


def rendern_a4(daten, design, ziel, zplan):
    """A4-Fassung mit WeasyPrint: erster Durchgang mit Mindestluft vor dem Fuss,
    zweiter mit so viel Luft, dass der Fuss auf dem unteren Rand aufsitzt.
    Gibt (seiten, bloecke, hinweise) zurueck; ImportError ohne WeasyPrint."""
    from weasyprint import HTML
    ds = design_system.fassung(design, "a4")
    K = ds["komponenten"]
    basis = ASSETS.as_uri() + "/"
    za4 = zert_a4(zplan, ds)
    hinweise = list(foto_a4(daten)[1])
    luft_min = design_system.aufloesen(ds, K["fuss"]["abstand-min"])
    soll = K["seite"]["hoehe"] - K["seite"]["rand-unten"]

    erster = HTML(string=html_bauen_a4(daten, ds, za4, luft_min), base_url=basis).render()
    seite, unten = _fuss_unterkante(erster)
    doc = erster
    if unten is not None and soll - unten > 0.05:
        # Knapp unter dem Soll bleiben: fuellt die Luft die Seite auf den Punkt,
        # kippt der Fuss auf eine neue Seite.
        zweiter = HTML(string=html_bauen_a4(daten, ds, za4, luft_min + soll - unten - 0.02),
                       base_url=basis).render()
        seite2, unten2 = _fuss_unterkante(zweiter)
        if len(zweiter.pages) == len(erster.pages) and seite2 == seite:
            doc, unten = zweiter, unten2
        else:
            hinweise.append("A4: Der Fuss liess sich nicht an den unteren Rand setzen, ohne eine "
                            "Seite mehr zu brauchen — er steht mit Mindestabstand unter dem Inhalt.")
    bloecke = _bloecke_je_seite(doc)
    for name, seiten in bloecke.items():
        if len(seiten) > 1 and name != "fuss":
            hinweise.append(f"A4: Block „{name}“ bricht ueber die Seiten {seiten} — er ist hoeher "
                            "als eine Seite. Inhalt kuerzen.")
    letzte = [b for b, s in bloecke.items() if s[0] == len(doc.pages)]
    if letzte == ["fuss"] and len(doc.pages) > 1:
        hinweise.append("A4: Auf der letzten Seite steht nur der Fuss — der Inhalt endet knapp "
                        "zu tief. Ein Eintrag weniger oder eine kuerzere Beschreibung spart die Seite.")
    doc.write_pdf(str(ziel))
    hinweis = seiten_ablegen(ziel, bloecke)
    if hinweis:
        hinweise.append(hinweis)
    return len(doc.pages), bloecke, hinweise


def main():
    # --pfad-genau nimmt den Zielpfad wie angegeben — nur fuer Tests, die eine
    # bekannte Datei wieder aufmachen. Im normalen Lauf gilt der Namensaufbau.
    genau = "--pfad-genau" in sys.argv[1:]
    args = [a for a in sys.argv[1:] if a != "--pfad-genau"]
    if len(args) < 2:
        raise SystemExit(__doc__)
    quelle = Path(args[0])
    daten = json.loads(quelle.read_text(encoding="utf-8"))

    design = design_system.laden()
    fehlend = design_system.schriften_fehlen(design)
    if fehlend:
        # Ohne die Datei setzt jede Engine still eine Ersatzschrift — lieber
        # gar kein PDF als eines in der falschen Schrift.
        raise SystemExit(
            "Schriftdateien fehlen — ohne sie entstuende das PDF in einer "
            "Ersatzschrift:\n" + "\n".join(f"  {p}" for p in fehlend) +
            "\nDie Schnitte nennt assets/tokens.json unter \"schriften\" "
            "(Google Fonts, OFL).")

    daten, ki_hinweis = kompetenzen_ordnen(daten)
    hinweise = ([ki_hinweis] if ki_hinweis else []) + pruefe(daten)
    zplan, zert_hinweise = zertifikate.planen(daten, design, beschriftung(daten))
    hinweise += zert_hinweise
    ziel = Path(args[1]) if genau else zielpfad(Path(args[1]), daten)
    ziel_a4 = (ziel.with_name(ziel.stem + " A4.pdf") if genau
               else zielpfad(Path(args[1]), daten, "a4"))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    breite = design["komponenten"]["seite"]["breite"]

    try:
        engine, hoehe, schatten, layout_hinweise, zert_hoehe = rendern_weasyprint(
            daten, design, ziel, zplan)
        hinweise += layout_hinweise
        print(f"Seitenformat: {breite} x {hoehe}pt, {schatten} Kartenschatten")
        if zplan and zert_hoehe is not None:
            hinweise += zert_hoehe_pruefen(zplan, zert_hoehe)
    except ImportError:
        # Ausweichweg: Hoehe am Bild messen (letzte nicht weisse Pixelzeile).
        # Die 2pt Reserve decken den Messfehler der Rasterung — lieber eine
        # haarduenne weisse Kante als ein abgeschnittener Footer.
        engine = rendern_ausweich(html_bauen(daten, VORRAT_HOEHE, design, zplan=zplan), ziel)
        hoehe = inhaltshoehe_messen(ziel)
        if hoehe is None:
            hinweise.append(
                f"Inhaltshoehe nicht messbar (weder PyMuPDF noch pdftoppm+Pillow) — "
                f"die Seite bleibt auf Vorratshoehe {VORRAT_HOEHE}pt und traegt unten "
                "viel Weissraum. pruefe_umgebung.py zeigt, was fehlt.")
        else:
            hoehe = round(hoehe + 2)
            engine = rendern_ausweich(html_bauen(daten, hoehe, design, zplan=zplan), ziel)
            print(f"Seitenformat: {breite} x {hoehe}pt")
        if zplan:
            hinweise.append(
                f"Zertifikatssektion auf dem Ausweichweg nicht vermessen — geplant "
                f"{zplan['hoehe']:g}pt (Grenze {zplan['grenze']}). In der Vorschau pruefen.")

    seiten = seitenzahl(ziel)
    if seiten > 1:
        hinweise.append(
            f"Das PDF hat {seiten} Seiten statt einer — der Inhalt ist hoeher als "
            "die gesetzte Seitenhoehe. Das darf nicht passieren, bitte melden.")

    print(f"{ziel} geschrieben (Engine: {engine})")

    fehler, design_hinweise = design_system.pruefe_pdf(ziel, design)
    hinweise += design_hinweise

    # Die A4-Fassung aus denselben Daten: dieselbe KI-Reihenfolge, dieselben
    # Zertifikatskacheln und Buendel.
    try:
        seiten, _, a4_hinweise = rendern_a4(daten, design, ziel_a4, zplan)
        hinweise += a4_hinweise
        print(f"Seitenformat A4: 595 x 842pt, {seiten} Seite{'n' if seiten != 1 else ''}")
        print(f"{ziel_a4} geschrieben (Engine: WeasyPrint)")
        a4_fehler, a4_design = design_system.pruefe_pdf(ziel_a4, design_system.fassung(design, "a4"))
        fehler += [f"A4: {f}" for f in a4_fehler]
        hinweise += [f"A4: {h}" for h in a4_design]
    except ImportError:
        hinweise.append("A4-Fassung nicht erzeugt — sie braucht WeasyPrint (laufende Kopfzeile, "
                        "gemessener Fuss). python3 scripts/pruefe_umgebung.py zeigt die Installation.")

    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)
    if fehler:
        print("\nFEHLER — das PDF weicht vom Design System ab (assets/tokens.json). "
              "So nicht ausliefern:", file=sys.stderr)
        for f in fehler:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(2)
    print("Design System eingehalten: Seitenformat, Schriften, Textstile, Farben.")


if __name__ == "__main__":
    main()
