#!/usr/bin/env python3
"""Rendert cv.json ueber das New-Monday-Template zu einem PDF.

    python3 scripts/render_cv.py daten/cv.json ausgabe/
    python3 scripts/render_cv.py daten/cv.json ausgabe/ --stufen-json arbeit/stufen.json

Den Dateinamen setzt das Skript selbst aus den Daten:
"New-Monday - Vorname Nachname - Jobtitel - CV.pdf". Das zweite Argument
bestimmt nur den Ordner — ein dort angehaengter Dateiname wird ersetzt
(Ausnahme: --pfad-genau, siehe main()).

Sucht sich die Render-Engine selbst: WeasyPrint (bevorzugt, ueberall per pip),
sonst headless Chrome, sonst wkhtmltopdf. Prueft ausserdem die Zeitraeume auf
Unstimmigkeiten und schreibt sie nach stderr — korrigiert wird nichts.
"""
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokens  # noqa: E402  — erst nach sys.path.insert moeglich

BESCHRIFTUNG = {
    "de": {
        "bildung": "Bildung", "skillset": "Skillset", "links": "Weiterführende Links",
        "kurzprofil": "Kurzprofil", "zertifikate": "Zertifikate",
        "ansprechpartner": "Ansprechpartner", "kontakt": "Kontakt", "adresse": "Adresse",
        "faehigkeiten": "Fähigkeiten", "branchen": "Branchen", "tools": "Tools",
        "sprachen": "Sprachen",
    },
    "en": {
        "bildung": "Education", "skillset": "Skillset", "links": "Further links",
        "kurzprofil": "Profile", "zertifikate": "Certificates",
        "ansprechpartner": "Contact person", "kontakt": "Contact", "adresse": "Address",
        "faehigkeiten": "Skills", "branchen": "Industries", "tools": "Tools",
        "sprachen": "Languages",
    },
}

# Zertifikate und Weiterbildungen stehen seit dem 03.10.2026 nicht mehr als
# Bildungseintraege, sondern als eigener Block unter den Abschluessen: je
# Zertifikat ein Tag mit dem Titel, nebeneinander (Entscheidung des Nutzers vom
# selben Tag; die drei Darstellungen davor - zeilen, spalten, aussteller - sind
# entfallen). Aussteller und Datum bleiben in der cv.json, fuer die Uebergabe
# und spaetere Zwecke; ins Dokument kommt nur der Titel.
#
# Ausgeschriebene Monatsnamen, nur zum Lesen eines Zertifikatsdatums wie
# "September 2026" (zert_datum) - gesetzt wird kein Datum mehr.
MONATSNAMEN = {
    "de": ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
           "September", "Oktober", "November", "Dezember"),
    "en": ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"),
}

# Das Skillset hat in jedem Lebenslauf dieselben vier Gruppen in derselben
# Anordnung, 2 x 2: links Faehigkeiten und Branchen, rechts Tools und Sprachen
# (Vorgabe vom 29.09.2026 — vorher trug jeder Lebenslauf andere Gruppen). Die
# Titel kommen aus BESCHRIFTUNG, nicht aus der cv.json; dort stehen nur die
# Eintraege unter den vier festen Schluesseln.
SKILLSET_SPALTEN = (("faehigkeiten", "branchen"), ("tools", "sprachen"))
SKILLSET_GRUPPEN = tuple(k for spalte in SKILLSET_SPALTEN for k in spalte)

# Aeltere cv.json-Dateien fuehren frei benannte Gruppen unter links/rechts. Nur
# eindeutige Titel werden einer festen Gruppe zugeordnet; alles andere faellt
# aus dem Skillset und wird gemeldet — geraten wird nicht.
ALTE_GRUPPENTITEL = {
    "faehigkeiten": ("fähigkeiten", "faehigkeiten", "skills", "kompetenzen",
                     "kernkompetenzen", "schwerpunkte", "arbeitsweise", "methoden"),
    "branchen": ("branchen", "branchenerfahrung", "industries", "industry experience"),
    "tools": ("tools", "software", "werkzeuge"),
    "sprachen": ("sprachen", "languages"),
}

# Deutsch und Englisch stehen in jedem Lebenslauf, mit festem Niveau — auch wenn
# das Material keine Sprachen oder andere Niveaus nennt (Vorgabe vom 29.09.2026,
# gleich wie im Portfolio-Skill). Weitere Sprachen kommen aus dem Material, mit
# ihrem eigenen Niveau.
SPRACH_VORGABE = {
    "de": ((("deutsch", "german"), "Deutsch", "Muttersprache"),
           (("englisch", "english"), "Englisch", "Business Niveau")),
    "en": ((("deutsch", "german"), "German", "Native speaker"),
           (("englisch", "english"), "English", "Business level")),
}
SPRACH_TRENNER = " – "

# Die Verweise im Profilkopf werden benannt, nicht als Adresse gesetzt: "zum
# LinkedIn Profil" statt "linkedin.com/in/timo-muster". In einem Dokument, das
# auch gedruckt wird, liest sich der Satz besser als eine nackte URL — und
# ausserhalb des Browsers ist eine URL ohnehin nur Zeichensalat.
# Was hier nicht steht, faellt auf den Titel aus der cv.json zurueck; ein
# eigenes "text" in der cv.json schlaegt beides.
VERWEISTEXT = {
    "de": {
        "linkedin": "zum LinkedIn Profil",
        "xing": "zum Xing Profil",
        "portfolio": "zum Portfolio",
        "website": "zur Website",
    },
    "en": {
        "linkedin": "to the LinkedIn profile",
        "xing": "to the Xing profile",
        "portfolio": "to the portfolio",
        "website": "to the website",
    },
}

# Der Ansprechpartner im Footer steht als Vorgabe im Skill, nicht in der
# cv.json. figma_plan.py liest ihn von hier, damit Frame und PDF gleich bleiben.
# Die Strasse genau so geschrieben, in allen drei Dokumenten gleich (Vorgabe
# vom 03.10.2026; vorher stand hier eine falsche Hausnummer).
KONTAKT_VORGABE = {
    "name": "Manuel Klein", "rolle": "CCO",
    "mail": "manuel.klein@newmonday.co", "telefon": "+49 (0) 155 1148 0130",
    "firma": "New Monday GmbH", "strasse": "Stresemannstr. 23", "ort": "10963 Berlin",
}

# Optische Groesse in pt: die Kantenlaenge, die ein quadratisches Logo bekommt.
# Jedes Logo wird auf dieselbe Flaeche gebracht (Breite x Hoehe = Groesse^2),
# nicht auf dieselbe Hoehe. Ueber die Hoehe gesetzt wirkt eine kompakte
# Bildmarke doppelt so schwer wie ein breiter Schriftzug: 3pc auf 58pt Hoehe
# deckt 88 x 48pt, Cocomore in derselben Zeile nur 88 x 15pt.
# Stationslogos: gestaffelt nach Anzahl der Marken — sie stehen in der
# Logospalte untereinander, und je mehr es sind, desto kleiner, damit die
# Logoreihe nicht laenger wird als der Text daneben. Entschieden wird einmal
# fuers ganze Dokument, nicht je Station: sonst steht dieselbe Marke —
# Deutsche Bank etwa, einmal allein und einmal neben Postbank, FYRST und
# Norisbank — an der einen Stelle doppelt so gross wie an der anderen.
LOGO_GROESSE = {1: 42, 2: 37, 3: 33}
LOGO_GROESSE_AB_4 = 29
# Projektlogos: immer dieselbe Groesse, egal wie viele an einem Projekt stehen.
# Sie stehen nebeneinander ueber dem Kundennamen (Design-Feedback 2026-09-28),
# eine Reihe wird also nicht hoeher, wenn eine Marke dazukommt — der Grund fuer
# die Staffelung faellt weg. Frueher standen sie untereinander und wurden ab
# zwei Marken auf 19pt verkleinert.
LOGO_PROJEKT_GROESSE = 26

# Die Logospalte aus tokens.json. Die Spaltenbreite ist die harte Grenze: ein
# Schriftzug, der breiter waere, erreicht seine Sollflaeche nicht und wird
# stattdessen auf volle Spaltenbreite gesetzt.
RAIL_BREITE = tokens.laden()["raster"]["logospalte"]
# Hochformatige Marken duerfen nicht beliebig hoch werden, sonst schiebt sich
# die Logospalte ueber den Stationskopf hinaus.
LOGO_HOCH_FAKTOR = 1.4

MONATE = {
    "januar": 1, "februar": 2, "maerz": 3, "märz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}
LAUFEND = ("heute", "aktuell", "jetzt", "laufend")


def parse_monat(text):
    """'Juni 2025' -> (2025, 6). None, wenn nicht lesbar oder laufend."""
    t = text.strip().lower()
    if any(w in t for w in LAUFEND):
        return "laufend"
    m = re.search(r"([a-zäöü]+)\s+(\d{4})", t)
    if not m:
        j = re.search(r"\b(\d{4})\b", t)
        return (int(j.group(1)), 1) if j else None
    monat = MONATE.get(m.group(1))
    return (int(m.group(2)), monat) if monat else None


def spanne(zeitraum):
    teile = re.split(r"\s*[-–—]\s*", zeitraum or "", maxsplit=1)
    if len(teile) != 2:
        return None, None
    return parse_monat(teile[0]), parse_monat(teile[1])


def logoliste(wert):
    """logo nimmt einen Dateinamen oder eine Liste davon — hier immer Liste."""
    if not wert:
        return []
    return [wert] if isinstance(wert, str) else list(wert)


def _sprache_zerlegen(eintrag):
    """(Sprachteil, Niveau) aus einem Sprach-Eintrag, so wie er in der cv.json steht.

    Angenommen werden "Deutsch – Muttersprache", "Englisch (fließend)",
    "Französisch: B2", {"sprache": "Französisch", "niveau": "B2"} und "Deutsch".
    """
    if isinstance(eintrag, dict):
        return (" ".join(str(eintrag.get("sprache") or "").split()),
                " ".join(str(eintrag.get("niveau") or "").split()))
    text = " ".join(str(eintrag or "").split())
    klammer = re.match(r"^(.*?)\s*\((.*)\)\s*$", text)
    if klammer:
        return klammer.group(1).strip(), klammer.group(2).strip()
    teile = re.split(r"\s+[–—-]\s+|:\s*", text, maxsplit=1)
    return teile[0].strip(), (teile[1].strip() if len(teile) > 1 else "")


def _sprachnamen(teil):
    """"Deutsch, Italienisch" -> {"deutsch", "italienisch"}."""
    return {t.strip().lower() for t in re.split(r",|/|&|\bund\b|\band\b", teil) if t.strip()}


def sprachen_mit_vorgabe(eintraege, sprache="de"):
    """Die Sprachen fuers Skillset: Deutsch und Englisch immer, mit festem Niveau.

    Gibt (Eintraege als Text, Hinweise) zurueck. Deutsch und Englisch stehen
    vorn — ergaenzt, wenn das Material sie nicht nennt, und mit dem Niveau der
    Vorgabe, wenn es ein anderes nennt ("fließend", "C1"). Beides wird gemeldet,
    damit es in der Uebergabe steht. Eine zusammengefasste Zeile ("Deutsch,
    Italienisch – Muttersprache") traegt die Sprache schon und bleibt, wie sie
    ist. Alle weiteren Sprachen bleiben mit ihrem eigenen Niveau stehen.
    """
    rest = [(e, *_sprache_zerlegen(e)) for e in eintraege or []]
    rest = [r for r in rest if r[1]]

    def anzeige(r):
        eintrag, teil, niveau = r
        if isinstance(eintrag, dict):
            return f"{teil}{SPRACH_TRENNER}{niveau}" if niveau else teil
        return " ".join(str(eintrag).split())

    kopf, hinweise = [], []
    for namen, name, niveau in SPRACH_VORGABE.get(sprache, SPRACH_VORGABE["de"]):
        einzeln = [r for r in rest if _sprachnamen(r[1]) <= set(namen)]
        gruppe = [r for r in rest if len(_sprachnamen(r[1])) > 1
                  and _sprachnamen(r[1]) & set(namen)]
        if gruppe:
            kopf.append(anzeige(gruppe[0]))
            rest = [r for r in rest if r is not gruppe[0] and r not in einzeln]
            continue
        alt = einzeln[0][2] if einzeln else None
        if alt is None:
            hinweise.append(f"Sprachen: „{name}{SPRACH_TRENNER}{niveau}“ ergänzt — "
                            "Vorgabe, im Material nicht genannt.")
        elif alt.lower() != niveau.lower():
            hinweise.append(f"Sprachen: {name} steht als „{niveau}“ (Vorgabe) — im "
                            f"Material stand {f'„{alt}“' if alt else 'kein Niveau'}.")
        kopf.append(f"{name}{SPRACH_TRENNER}{niveau}")
        rest = [r for r in rest if r not in einzeln]
    return kopf + [anzeige(r) for r in rest], hinweise


def skillset_gruppen(daten):
    """Das Skillset als zwei Spalten mit den vier festen Gruppen.

    Gibt ({"links": [...], "rechts": [...]}, Hinweise) zurueck; jede Gruppe als
    {"schluessel", "titel", "eintraege"}. Template, Figma-Plan und Selbsttest
    lesen alle von hier — die Anordnung steht nur in SKILLSET_SPALTEN.

    Eine leere Gruppe faellt weg und wird gemeldet: Faehigkeiten, Branchen und
    Tools leitet der Skill aus den Stationen ab, wenn das Material nichts sagt
    (SKILL.md, Schritt 2) — bleibt eine trotzdem leer, ist das eine Luecke fuer
    die Uebergabe. Sprachen sind nie leer.
    """
    sprache = daten.get("sprache", "de")
    labels = BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"])
    roh = daten.get("skillset") or {}
    hinweise = []
    gruppen = {k: [] for k in SKILLSET_GRUPPEN}
    if "links" in roh or "rechts" in roh:
        hinweise.append("Skillset im alten Format (links/rechts mit freien Titeln) — "
                        "bitte auf die vier festen Gruppen umstellen, SKILL.md Schritt 2.")
        for g in (roh.get("links") or []) + (roh.get("rechts") or []):
            titel = " ".join(str(g.get("titel") or "").split())
            ziel = next((k for k, titel_liste in ALTE_GRUPPENTITEL.items()
                         if titel.lower() in titel_liste), None)
            if ziel:
                gruppen[ziel] += list(g.get("eintraege") or [])
            else:
                hinweise.append(f"Skillset: Gruppe „{titel}“ passt in keine der vier "
                                "festen Gruppen und steht nicht im Dokument.")
    else:
        for k, wert in roh.items():
            if k in gruppen:
                gruppen[k] = list(wert or [])
            else:
                hinweise.append(f"Skillset: „{k}“ ist keine der vier Gruppen "
                                f"({', '.join(SKILLSET_GRUPPEN)}) und steht nicht im Dokument.")

    for k in ("faehigkeiten", "branchen", "tools"):
        gesehen, eindeutig = set(), []
        for e in gruppen[k]:
            text = " ".join(str(e).split())
            if not text:
                continue
            if text.lower() in gesehen:
                hinweise.append(f"Skillset: „{text}“ stand doppelt unter {labels[k]} — "
                                "einmal gestrichen.")
                continue
            gesehen.add(text.lower())
            eindeutig.append(text)
        gruppen[k] = eindeutig
    gruppen["sprachen"], sprach_hinweise = sprachen_mit_vorgabe(gruppen["sprachen"], sprache)
    hinweise += sprach_hinweise

    spalten = {}
    for seite, schluessel in zip(("links", "rechts"), SKILLSET_SPALTEN):
        spalten[seite] = []
        for k in schluessel:
            if gruppen[k]:
                spalten[seite].append({"schluessel": k, "titel": labels[k],
                                       "eintraege": gruppen[k]})
            else:
                hinweise.append(f"Skillset: {labels[k]} ist leer und fehlt im Dokument — "
                                "aus Stationen und Projekten ableiten und in der Übergabe "
                                "zur Freigabe nennen (SKILL.md, Schritt 2).")
    return spalten, hinweise


# Woran ein Bildungseintrag als Zertifikat zu erkennen ist. Nur fuer einen
# Hinweis — umgezogen wird nichts, das waere Raten.
ZERT_MUSTER = re.compile(r"zertifi|certifi|certified", re.IGNORECASE)


def bildung_aufbereiten(daten):
    """Die Abschluesse fuers Dokument — ohne Studieninhalte.

    Gibt (Eintraege, Hinweise) zurueck. Was jemand an einer Einrichtung gelernt
    hat (frueher "themen"), steht seit dem 03.10.2026 nicht mehr im Lebenslauf.
    Aeltere cv.json-Dateien tragen das Feld noch: es wird ignoriert und
    gemeldet, nicht still verschluckt. Ebenso ein Zertifikat, das noch als
    Bildungseintrag steht — es bleibt dort stehen, wird aber genannt, weil es
    jetzt unter "zertifikate" gehoert.
    """
    eintraege, hinweise = [], []
    for nummer, b in enumerate(daten.get("bildung") or []):
        if not isinstance(b, dict):
            continue
        eintrag = {k: v for k, v in b.items() if k != "themen"}
        name = " ".join(str(b.get("abschluss") or b.get("institution") or "").split())
        if b.get("themen"):
            themen = ", ".join(" ".join(str(t).split()) for t in b["themen"])
            hinweise.append(f"bildung[{nummer}] („{name}“): themen ignoriert — "
                            "Studieninhalte stehen nicht mehr im Lebenslauf "
                            f"(Vorgabe vom 03.10.2026). Waren: {themen}")
        if ZERT_MUSTER.search(name):
            hinweise.append(f"bildung[{nummer}] „{name}“ sieht nach einem Zertifikat "
                            "aus — Zertifikate stehen jetzt unter zertifikate "
                            "(SKILL.md, Schritt 2). Im Dokument steht er weiter "
                            "als Abschluss.")
        eintraege.append(eintrag)
    return eintraege, hinweise


def zert_datum(text):
    """'09/2026' -> (2026, 9), '2021' -> (2021, None). None, wenn nicht lesbar.

    Erwartet wird MM/JJJJ oder JJJJ. Ein ausgeschriebener Monat ('September
    2026') wird auch gelesen — der Eingang schreibt Daten selten so, wie das
    Schema es will.
    """
    t = " ".join(str(text or "").split()).lower()
    m = re.fullmatch(r"(\d{1,2})\s*[/.]\s*(\d{4})", t)
    if m and 1 <= int(m.group(1)) <= 12:
        return int(m.group(2)), int(m.group(1))
    if re.fullmatch(r"\d{4}", t):
        return int(t), None
    m = re.fullmatch(r"([a-zäöü]+)\.?\s+(\d{4})", t)
    if m:
        namen = {n.lower(): i for namen in MONATSNAMEN.values()
                 for i, n in enumerate(namen, start=1)}
        monat = MONATE.get(m.group(1)) or namen.get(m.group(1))
        if monat:
            return int(m.group(2)), monat
    return None


def leerraum(text):
    """Fasst Leerraum zusammen, laesst aber das geschuetzte Leerzeichen (U+00A0)
    stehen - str.split() wuerde auch daran trennen, und dann bricht etwa
    „e. V.“ zwischen „e.“ und „V.“ um."""
    return re.sub(r"[ \t\r\n\f\v]+", " ", str(text or "")).strip()


def zertifikate_aufbereiten(daten):
    """Die Zertifikate fuers Dokument: die Titel, fertig fuer Template und Plan.

    Gibt (Titel, Hinweise) zurueck; ohne Zertifikate ist die Liste leer. Jedes
    Zertifikat wird ein Tag, und ein Tag traegt nur den Titel. Aussteller und
    Datum bleiben in der cv.json — sie werden hier trotzdem geprueft, weil die
    Uebergabe nennt, was davon fehlt, und weil die Reihenfolge der Tags am
    Datum haengt: neueste zuerst ist Sache der Daten, steht ein aelteres vor
    einem neueren, wird das gemeldet, nicht umsortiert.

    "zertifikate_darstellung" aus einer aelteren cv.json (zeilen, spalten,
    aussteller) wird ignoriert und gemeldet.
    """
    hinweise = []
    if daten.get("zertifikate_darstellung"):
        hinweise.append(f"zertifikate_darstellung „{daten['zertifikate_darstellung']}“ "
                        "wird ignoriert — Zertifikate stehen seit dem 03.10.2026 immer "
                        "als Tags, nur mit dem Titel. Der Schlüssel kann aus der cv.json.")

    gelesen = []
    for nummer, z in enumerate(daten.get("zertifikate") or []):
        if not isinstance(z, dict):
            hinweise.append(f"zertifikate[{nummer}] ist kein Objekt und fehlt im Dokument.")
            continue
        titel = leerraum(z.get("titel"))
        if not titel:
            hinweise.append(f"zertifikate[{nummer}] hat keinen titel und fehlt im Dokument.")
            continue
        roh = " ".join(str(z.get("datum") or "").split())
        datum = zert_datum(roh) if roh else None
        if roh and datum is None:
            hinweise.append(f"zertifikate[{nummer}] („{titel}“): Datum „{roh}“ nicht "
                            "lesbar — erwartet MM/JJJJ oder JJJJ.")
        if not leerraum(z.get("aussteller")):
            hinweise.append(f"zertifikate[{nummer}] („{titel}“) ohne Aussteller.")
        if not roh:
            hinweise.append(f"zertifikate[{nummer}] („{titel}“) ohne Datum.")
        gelesen.append({"titel": titel, "roh": roh, "datum": datum})

    # Neueste zuerst. Gemeldet wird nur, was eindeutig falsch steht: ein Jahr
    # ohne Monat ist innerhalb seines Jahres weder aelter noch neuer.
    for vorher, nachher in zip(gelesen, gelesen[1:]):
        a, b = vorher["datum"], nachher["datum"]
        if a and b and (a[0] < b[0] or (a[0] == b[0] and a[1] and b[1] and a[1] < b[1])):
            hinweise.append(f"Zertifikate nicht neueste zuerst: „{vorher['titel']}“ "
                            f"({vorher['roh']}) steht vor „{nachher['titel']}“ "
                            f"({nachher['roh']}).")
    return [z["titel"] for z in gelesen], hinweise


# Eine Zahl, wie sie in SVG-Attributen steht: "593.2", ".5", "1e3", "-0.25".
# Das fruehere Muster [\d.]+ las "1e3" zwar, nahm aber auch "1.2.3" als eine
# Zahl, und \bwidth traf "stroke-width" — gleich gehalten mit dem
# Portfolio-Skill, der dort adidas und Nestle als quadratisch gelesen hatte.
SVG_ZAHL = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def svg_masse(rohdaten):
    """(Verhaeltnis der viewBox, Verhaeltnis aus width/height) des
    Wurzelelements, je None, wenn nicht lesbar. width/height in jeder
    Reihenfolge, ohne Einheit oder in px/pt; Prozentangaben sind kein Mass."""
    if isinstance(rohdaten, str):
        rohdaten = rohdaten.encode("utf-8")
    kopf = re.search(rb"<svg\b[^>]*>", rohdaten, re.S)
    if not kopf:
        return None, None
    tag = kopf.group(0).decode("utf-8", "replace")

    box_verhaeltnis = None
    box = re.search(r'(?<![-\w])viewBox\s*=\s*["\']([^"\']+)["\']', tag)
    if box:
        werte = [float(z) for z in re.findall(SVG_ZAHL, box.group(1))]
        if len(werte) == 4 and werte[2] > 0 and werte[3] > 0:
            box_verhaeltnis = werte[2] / werte[3]

    masse = [re.search(rf'(?<![-\w]){attribut}\s*=\s*["\']\s*({SVG_ZAHL})\s*(?:px|pt)?\s*["\']', tag)
             for attribut in ("width", "height")]
    breit_hoch = None
    if all(masse) and float(masse[0].group(1)) > 0 and float(masse[1].group(1)) > 0:
        breit_hoch = float(masse[0].group(1)) / float(masse[1].group(1))
    return box_verhaeltnis, breit_hoch


def _svg_verhaeltnis(rohdaten):
    """Erst die viewBox, ohne sie width/height."""
    box, breit_hoch = svg_masse(rohdaten)
    return box or breit_hoch


def _bitmap_verhaeltnis(rohdaten):
    if rohdaten[:8] == b"\x89PNG\r\n\x1a\n":
        breite, hoehe = struct.unpack(">II", rohdaten[16:24])
        return breite / hoehe if hoehe else None
    if rohdaten[:6] in (b"GIF87a", b"GIF89a"):
        breite, hoehe = struct.unpack("<HH", rohdaten[6:10])
        return breite / hoehe if hoehe else None
    if rohdaten[:2] == b"\xff\xd8":                     # JPEG: SOF-Marker suchen
        i = 2
        while i + 9 < len(rohdaten):
            if rohdaten[i] != 0xFF:
                i += 1
                continue
            marker, laenge = rohdaten[i + 1], struct.unpack(">H", rohdaten[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                hoehe, breite = struct.unpack(">HH", rohdaten[i + 5:i + 9])
                return breite / hoehe if hoehe else None
            i += 2 + laenge
    return None


def verhaeltnis_der_datei(pfad):
    """Breite/Hoehe einer Bilddatei, gelesen aus der Datei selbst. None, wenn
    sie fehlt oder sich nicht lesen laesst. SVG bringt das Verhaeltnis in der
    viewBox mit, PNG/GIF/JPEG im Dateikopf. add_logo.py misst damit, was es
    abgelegt hat — dieselbe Rechnung wie beim Setzen."""
    pfad = Path(pfad)
    try:
        rohdaten = pfad.read_bytes()
    except OSError:
        return None
    try:
        return (_svg_verhaeltnis(rohdaten) if pfad.suffix.lower() == ".svg"
                else _bitmap_verhaeltnis(rohdaten)) or None
    except (ValueError, struct.error):
        return None


def seitenverhaeltnis(datei):
    """Breite/Hoehe einer Logodatei. 1.0, wenn sie sich nicht lesen laesst.

    Quelle ist die Datei selbst, nicht die Angabe in der cv.json: nur so laesst
    sich die Flaeche jedes Logos gleich setzen — und nur so wird kein Logo
    verzerrt. Breite und Hoehe kommen immer aus diesem einen Verhaeltnis.
    """
    pfad = ASSETS / "logos" / datei
    if not pfad.exists():
        return 1.0
    verhaeltnis = verhaeltnis_der_datei(pfad)
    if not verhaeltnis:
        print(f"Warnung: Seitenverhaeltnis von {datei} nicht lesbar, nehme 1:1",
              file=sys.stderr)
        return 1.0
    return verhaeltnis


def logo_masse(datei, groesse):
    """(Breite, Hoehe) in pt fuer ein Logo bei gegebener optischer Groesse."""
    return masse_aus_verhaeltnis(seitenverhaeltnis(datei), groesse)


def masse_aus_verhaeltnis(verhaeltnis, groesse):
    """(Breite, Hoehe) in pt aus Seitenverhaeltnis und optischer Groesse.

    Gleiche Flaeche fuer alle: Breite = Groesse * sqrt(Verhaeltnis), Hoehe =
    Groesse / sqrt(Verhaeltnis). Ein Quadrat bekommt damit genau Groesse x
    Groesse, ein 4:1-Schriftzug dieselbe Flaeche in flacher Form. Beide Kappen
    unten rechnen die andere Seite aus dem Verhaeltnis nach — gestaucht wird
    nie.
    """
    wurzel = math.sqrt(verhaeltnis)
    breite, hoehe = groesse * wurzel, groesse / wurzel
    if breite > RAIL_BREITE:                  # breiter als die Spalte: kappen
        breite, hoehe = RAIL_BREITE, RAIL_BREITE / verhaeltnis
    hoch = groesse * LOGO_HOCH_FAKTOR
    if hoehe > hoch:                          # hochformatig: Hoehe deckeln
        breite, hoehe = hoch * verhaeltnis, hoch
    return round(breite, 2), round(hoehe, 2)


def logo_groessen(daten):
    """(Stationsgroesse, Projektgroesse) in pt — einmal fuer das ganze Dokument.

    Fuer die Stationen ist die groesste Markenzahl massgeblich, die irgendwo
    auftritt. Damit ist jedes Logo an jeder Stelle gleich gross, auch wenn es
    einmal allein und einmal in einer Markenreihe steht. Projektlogos stehen
    nebeneinander und haben deshalb immer dieselbe Groesse.
    """
    stationen = daten.get("stationen", [])
    st = max([len(logoliste(s.get("logo"))) for s in stationen] or [0])
    return LOGO_GROESSE.get(max(st, 1), LOGO_GROESSE_AB_4), LOGO_PROJEKT_GROESSE


def pruefe(daten):
    """Sammelt Auffaelligkeiten in den Zeitraeumen. Aendert nichts."""
    hinweise = []
    for s in daten.get("stationen", []):
        start, ende = spanne(s.get("zeitraum", ""))
        if start and ende and ende != "laufend" and start != "laufend" and ende < start:
            hinweise.append(f"{s.get('firma') or s.get('titel')}: Ende liegt vor dem Anfang ({s['zeitraum']})")
        for p in s.get("projekte", []):
            ps, pe = spanne(p.get("zeitraum", ""))
            if ps and pe and pe != "laufend" and ps != "laufend" and pe < ps:
                hinweise.append(f"{p.get('kunde')}: Ende liegt vor dem Anfang ({p['zeitraum']})")
            if ps and start and ps != "laufend" and start != "laufend" and ps < start:
                hinweise.append(
                    f"{p.get('kunde')}: startet vor der Anstellung bei {s.get('firma')} "
                    f"({p.get('zeitraum')} vs. {s.get('zeitraum')})"
                )
    def fehlende(wert, wer):
        return [f"Logo fehlt in assets/logos/: {d} ({wer})"
                for d in logoliste(wert) if not (ASSETS / "logos" / d).exists()]

    im_rail, im_projekt = set(), set()
    for s in daten.get("stationen", []):
        hinweise += fehlende(s.get("logo"), s.get("firma"))
        im_rail.update(logoliste(s.get("logo")))
        for p in s.get("projekte", []):
            hinweise += fehlende(p.get("logo"), p.get("kunde"))
            im_projekt.update(logoliste(p.get("logo")))

    # Innerhalb einer Ebene ist jedes Logo gleich gross. Ueber beide Ebenen
    # hinweg nicht: das Projektlogo ist bewusst die kleinere Stufe.
    for d in sorted(im_rail & im_projekt):
        hinweise.append(
            f"{d} steht als Stationslogo und als Projektlogo im Dokument — "
            "Projektlogos sind die kleinere Stufe, die beiden Groessen weichen "
            "deshalb ab."
        )
    return hinweise


def html_bauen(daten, stufe="normal", fuss_abstand=0, stationen_kompakt=False):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(ASSETS)),
        autoescape=select_autoescape(["html"]),
    )
    # cv.css holt sich jeden Designwert ueber diese Namen aus tokens.json.
    env.globals.update(tokens.jinja_globals())
    sprache = daten.get("sprache", "de")
    labels = BESCHRIFTUNG.get(sprache, BESCHRIFTUNG["de"])
    # Angezeigt wird der benannte Verweis, nicht die Adresse — verlinkt bleibt
    # die volle URL. Das Template setzt nur noch, was hier steht.
    verweise = VERWEISTEXT.get(sprache, VERWEISTEXT["de"])
    for l in daten.get("person", {}).get("links") or []:
        titel = str(l.get("titel") or "").strip()
        l["anzeige"] = l.get("text") or verweise.get(titel.lower()) or titel
    daten.setdefault("kontakt", dict(KONTAKT_VORGABE))
    # Jedes Logo bekommt sein eigenes Mass, ausgerechnet aus dem
    # Seitenverhaeltnis der Datei. Das Template setzt nur noch, was hier steht.
    groesse, projekt_groesse = logo_groessen(daten)
    for s in daten.get("stationen", []):
        s.setdefault("projekte", [])
        s["logos"] = [dict(zip(("datei", "breite", "hoehe"),
                               (d, *logo_masse(d, groesse))))
                      for d in logoliste(s.get("logo"))]
        for p in s["projekte"]:
            p["logos"] = [dict(zip(("datei", "breite", "hoehe"),
                                   (d, *logo_masse(d, projekt_groesse))))
                          for d in logoliste(p.get("logo"))]

    # Das Template wird aus assets/ heraus gerendert; ein Fotopfad aus der JSON
    # bezieht sich aber auf das Arbeitsverzeichnis. Darum hier absolut machen.
    foto = daten.get("person", {}).get("foto")
    if foto and not str(foto).startswith("file:"):   # zweiter Lauf: schon umgewandelt
        p = Path(foto).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            print(f"Warnung: Foto nicht gefunden: {p}", file=sys.stderr)
        daten["person"]["foto"] = p.as_uri()

    # Das Skillset geht als die zwei festen Spalten ins Template, nicht so, wie
    # es in der cv.json steht. Ueber eine Kopie: html_bauen laeuft je Dokument
    # mehrmals, und die Rohdaten muessen fuer den naechsten Durchgang bleiben.
    kontext = dict(daten)
    kontext["skillset"] = skillset_gruppen(daten)[0]
    # Abschluesse ohne Studieninhalte, Zertifikate als Liste ihrer Titel — je
    # Titel ein Tag. Beides fertig aufbereitet, wie es gesetzt wird.
    kontext["bildung"] = bildung_aufbereiten(daten)[0]
    kontext["zertifikate"] = zertifikate_aufbereiten(daten)[0]
    return env.get_template("template.html").render(
        stufe=stufe, fuss_abstand=fuss_abstand,
        stationen_kompakt=stationen_kompakt, t=labels, **kontext
    )


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


def rendern(html, ziel):
    """Erste verfuegbare Engine gewinnt. Gibt ihren Namen zurueck.

    Schreibt nichts in den Skill-Ordner: WeasyPrint bekommt die Basis-URL direkt,
    die anderen Engines eine Temporaerdatei mit <base>-Tag. In Claude Code liegt
    der Skill unter ~/.claude/skills/ und darf nicht vollgeschrieben werden.
    """
    basis = ASSETS.as_uri() + "/"
    try:
        from weasyprint import HTML
        HTML(string=html, base_url=basis).write_pdf(str(ziel))
        return "WeasyPrint"
    except ImportError:
        pass

    with tempfile.TemporaryDirectory() as tmp:
        seite = Path(tmp) / "cv.html"
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
                "--page-size", "A4", "--margin-top", "0", "--margin-bottom", "0",
                str(seite), str(ziel),
            ], check=True, capture_output=True, timeout=120)
            return "wkhtmltopdf (eingeschraenktes CSS)"

    raise SystemExit(
        "Keine Render-Engine gefunden. python3 scripts/pruefe_umgebung.py "
        "zeigt, was fehlt und wie es installiert wird."
    )


def spalten_pruefen(daten):
    """Laeuft Seite 1 ueber: wo sich Hoehe gewinnen laesst.

    Die vier Gruppen und ihre Anordnung stehen fest, verschieben geht nicht
    mehr. Der Block ist so hoch wie seine laengere Spalte — gekuerzt wird also
    in der laengsten Gruppe der laengeren Spalte, durch Weglassen der
    schwaechsten Eintraege, nie durch Umformulieren.
    """
    spalten = skillset_gruppen(daten)[0]

    def zeilen(spalte):                       # Ueberschrift plus Eintraege
        return sum(1 + len(g["eintraege"]) for g in spalte)
    seite = max(spalten, key=lambda s: zeilen(spalten[s]))
    if not spalten[seite]:
        return []
    laengste = max(spalten[seite], key=lambda g: len(g["eintraege"]))
    return [
        f"Die {'linke' if seite == 'links' else 'rechte'} Skillset-Spalte ist die "
        f"laengere ({zeilen(spalten[seite])} Zeilen). Dort zuerst in "
        f"{laengste['titel']} ({len(laengste['eintraege'])} Eintraege) die schwaechsten "
        "Eintraege weglassen — Gruppen und Anordnung stehen fest."
    ]


# Wo die unterste Zeile des Footers stehen soll, in pt ueber der Blattunterkante:
# so wie in Figma, wo der Footer mit seiner letzten Zeile auf dem unteren
# Seitenrand aufsitzt. Gemessen wird die Schriftlinie, und die sitzt um die
# Unterlaenge der Zeile ueber dem Rand. Fuellt die Fussluft die Restseite auf
# den Punkt aus, kippt der Footer auf eine neue Seite — deshalb probiert
# render_cv.py kleine Reserven durch, bevor es groessere nimmt.
FUSS_ZIEL = round(tokens.laden()["seite"]["rand_unten"]
                  + tokens.stil("fuss_wert")["zeile"] - tokens.grundlinie("fuss_wert"), 2)
# Mindestabstand, wenn die Seite nicht mehr hergibt. Lieber eng als eine
# zusaetzliche Seite, auf der nichts ausser dem Footer steht.
FUSS_MIN = 12


def seitenzahl(ziel):
    """Seiten im fertigen PDF. 0, wenn pypdf fehlt — dann wird nicht gemessen."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return 0
    return len(PdfReader(str(ziel)).pages)


def footer_allein(ziel, daten):
    """Steht auf der letzten Seite nur noch der Footer?

    Dann ist die Seite reine Verschwendung — es lohnt der Versuch, die Stationen
    enger zu setzen, damit er auf die Seite davor rutscht. Gemessen wird, was
    nach Abzug der Footer-Texte an Text uebrig bleibt: ueber die Stationen ginge
    es nicht, "New Monday GmbH" steht als Firma und als Adresse im Dokument.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return False
    letzte = " ".join((PdfReader(str(ziel)).pages[-1].extract_text() or "").split()).lower()
    labels = BESCHRIFTUNG.get(daten.get("sprache", "de"), BESCHRIFTUNG["de"])
    teile = [labels[k] for k in ("ansprechpartner", "kontakt", "adresse")]
    teile += [str(w) for w in (daten.get("kontakt") or {}).values()]
    for stueck in teile:
        letzte = letzte.replace(" ".join(str(stueck).split()).lower(), " ", 1)
    return len(letzte.split()) < 4


def text_tiefe(ziel, seite=-1):
    """Wie weit ueber der Blattunterkante endet der Text einer Seite?

    In pt, gemessen an der untersten Schriftlinie. None, wenn nicht messbar.
    Die Textmatrix allein reicht dafuer nicht: WeasyPrint setzt eine gedrehte
    und skalierte Grundmatrix, erst beide zusammen ergeben die Seitenkoordinate.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    hoehen = []

    def besucher(text, cm, tm, schrift, groesse):
        if text.strip():
            hoehen.append(tm[4] * cm[1] + tm[5] * cm[3] + cm[5])

    PdfReader(str(ziel)).pages[seite].extract_text(visitor_text=besucher)
    return min(hoehen) if hoehen else None


def _schlussmarken(daten):
    """Texte, die ganz am Ende des Deckblatts stehen — je Skillset-Spalte einer.

    Nicht am Anfang der Stationen messen: deren erster Titel ist oft derselbe
    Text wie die Rolle im Profilkopf ("Softwareentwickler") und wird dann schon
    auf Seite 1 gefunden, obwohl das Skillset laengst ueberlaeuft.

    Die Verweise taugen dafuer nicht: sie stehen im Profilkopf, also immer weit
    oben auf Seite 1, egal wie weit das Skillset darunter ueberlaeuft.
    """
    marken = []
    spalten = skillset_gruppen(daten)[0]
    for spalte in (spalten["links"], spalten["rechts"]):
        if spalte:
            letzte = spalte[-1]
            eintraege = letzte.get("eintraege") or []
            marken.append(eintraege[-1] if eintraege else letzte.get("titel"))
    if not marken:
        # Ohne Skillset ist das Letzte im Block ein Zertifikats-Tag oder, ohne
        # die, der letzte Abschluss. Studieninhalte gibt es nicht mehr.
        zert = zertifikate_aufbereiten(daten)[0]
        marken += zert[-1:]
        for b in ([] if zert else bildung_aufbereiten(daten)[0][-1:]):
            marken.append(b.get("zeitraum") or b.get("institution") or b.get("abschluss"))
    return [" ".join(str(m).split()) for m in marken if m]


def deckblatt_seiten(ziel, daten):
    """Wie viele Seiten belegen Profilkopf, Bildung und Skillset zusammen?

    Gemessen am jeweils ersten Vorkommen der Schlussmarken — der Block steht vor
    den Stationen, ein spaeterer Treffer im Stationstext zaehlt also nicht.
    0 heisst: gibt hier nichts zu pruefen (kein pypdf, kein Bildung/Skillset).
    -1 heisst: geprueft, aber keine Marke wiedergefunden. Ein Skillset gibt es
    immer — mindestens die Sprachen stehen darin —, geprueft wird also immer.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return 0

    marken = _schlussmarken(daten)
    if not marken:
        return 0
    # Normalisiert, weil ein umgebrochener Eintrag im PDF-Text ein \n traegt.
    seiten = [" ".join((s.extract_text() or "").split())
              for s in PdfReader(str(ziel)).pages]
    letzte = 0
    for marke in marken:
        for nummer, text in enumerate(seiten, start=1):
            if marke in text:
                letzte = max(letzte, nummer)
                break
    return letzte or -1


def dateiname(daten):
    """New-Monday - Vorname Nachname - Jobtitel - CV.pdf

    Der Name kommt aus den Daten, nicht aus dem Aufrufargument: so heisst jeder
    Lebenslauf beim Kunden gleich, egal wie der Zielpfad getippt war. Fehlt ein
    Feld, faellt nur sein Abschnitt weg — eine Datei entsteht trotzdem.
    """
    person = daten.get("person") or {}
    teile = ["New-Monday"]
    for feld in ("name", "rolle"):
        wert = re.sub(r'[/\\:*?"<>|]', "-", str(person.get(feld) or ""))
        # Nur Leerzeichen weg, Punkte bleiben: die anonyme Fassung traegt
        # Initialen im Namensfeld, und "F. F" statt "F. F." saehe nach Panne
        # aus. Ein Punkt am Ende des ganzen Dateinamens kann dadurch nicht
        # entstehen — der ist immer ".pdf".
        wert = re.sub(r"\s+", " ", wert).strip()
        if wert:
            teile.append(wert)
    teile.append("CV")
    return " - ".join(teile) + ".pdf"


def zielpfad(argument, daten):
    """Ordner aus dem Argument, Dateiname aus den Daten."""
    name = dateiname(daten)
    pdf_gemeint = argument.suffix.lower() == ".pdf"
    ordner = argument.parent if pdf_gemeint else argument
    if pdf_gemeint and argument.name != name:
        print(f"Dateiname gesetzt: {argument.name} -> {name}")
    return ordner / name


def main():
    # --pfad-genau nimmt den Zielpfad wie angegeben — nur fuer Tests, die eine
    # bekannte Datei wieder aufmachen. Im normalen Lauf gilt der Namensaufbau.
    genau = "--pfad-genau" in sys.argv[1:]
    # --stufen-json schreibt nebenbei mit, welche Verdichtungsstufen gegriffen
    # haben. Das braucht figma_plan.py: der Figma-Frame muss dieselben Abstaende
    # setzen wie das PDF, sonst laeuft er ueber. Aus der Ausgabe unten laesst es
    # sich nicht ablesen — die Deckblattstufe wird nur gemeldet, wenn sie am Ende
    # auch gereicht hat. Ohne die Option aendert sich nichts.
    stufen_datei = None
    # --zertifikate (zeilen|spalten|aussteller) gibt es seit dem 03.10.2026
    # nicht mehr: Zertifikate stehen immer als Tags. Ein alter Aufruf bricht
    # nicht ab, der Schalter wird samt Wert ignoriert und gemeldet.
    vorab = []
    args = []
    rest = list(sys.argv[1:])
    while rest:
        a = rest.pop(0)
        if a == "--pfad-genau":
            continue
        if a == "--zertifikate":
            wert = rest.pop(0) if rest else "(ohne Wert)"
            vorab.append(f"--zertifikate {wert} ignoriert — Zertifikate stehen immer "
                         "als Tags, nur mit dem Titel.")
            continue
        if a == "--stufen-json":
            if not rest:
                raise SystemExit(f"{a} braucht einen Wert")
            stufen_datei = Path(rest.pop(0))
            continue
        args.append(a)
    if len(args) < 2:
        raise SystemExit(__doc__)
    quelle = Path(args[0])
    daten = json.loads(quelle.read_text(encoding="utf-8"))

    hinweise = vorab + pruefe(daten)
    # Was am Skillset gesetzt, ergaenzt oder weggelassen wurde (Sprachvorgabe,
    # leere Gruppen, altes Format) — gehoert in die Uebergabe.
    hinweise += skillset_gruppen(daten)[1]
    # Dasselbe fuer Bildung und Zertifikate: ignorierte Studieninhalte und
    # Darstellungsschluessel aus aelteren cv.json, Zertifikate im alten
    # Bildungsplatz, fehlende Aussteller und Daten, die Reihenfolge.
    hinweise += bildung_aufbereiten(daten)[1]
    zertifikate, zert_hinweise = zertifikate_aufbereiten(daten)
    hinweise += zert_hinweise
    person = daten.get("person") or {}
    for feld in ("name", "rolle"):
        if not person.get(feld):
            hinweise.append(f"person.{feld} fehlt — der Dateiname bleibt ohne diesen Teil.")
    ziel = Path(args[1]) if genau else zielpfad(Path(args[1]), daten)
    ziel.parent.mkdir(parents=True, exist_ok=True)

    # Deckblatt = Profilkopf, Bildung und Skillset auf Seite 1. Passt es nicht,
    # werden die Abstaende gestaffelt enger gesetzt, bevor irgendwer Eintraege
    # streicht. Erst wenn auch die engste Stufe nicht reicht, kommt der Hinweis.
    stufe = "normal"
    engine = rendern(html_bauen(daten), ziel)
    for naechste in ("kompakt", "eng"):
        if deckblatt_seiten(ziel, daten) <= 1:
            break
        stufe = naechste
        engine = rendern(html_bauen(daten, stufe=stufe), ziel)

    kompakt = False

    def setzen(**abstaende):
        return rendern(html_bauen(daten, stufe=stufe, stationen_kompakt=kompakt,
                                  **abstaende), ziel)

    # Der Footer schliesst die letzte Seite unten ab. Sein Abstand wird nicht
    # geraten, sondern gemessen: erst die Ist-Hoehe der untersten Zeile, dann
    # bekommt die Luft davor genau die Differenz. Unter der Schriftlinie sitzt
    # aber noch Zeilenrest, und der Umbruch braucht Reserve — wie viel, haengt
    # am Dokument, deshalb mehrere Zielhoehen von knapp bis gelassen. Was die
    # Seite sprengt, faellt durch.
    ZIELE = tuple(FUSS_ZIEL + reserve for reserve in (0.5, 2, 6, 20, 45, 75))

    # Eine letzte Seite, auf der nur der Footer steht, ist verschenktes Papier.
    # Dann werden die Abstaende zwischen Stationen, Projekten und Bullets enger
    # gesetzt — bringt das die Seite zurueck, bleibt es dabei. Gemessen wird mit
    # minimaler Fussluft: nur so zeigt sich, ob der Footer ueberhaupt noch auf
    # die Seite davor passt.
    engine = setzen(fuss_abstand=FUSS_MIN)
    if footer_allein(ziel, daten):
        vorher = seitenzahl(ziel)
        for enger in ("kompakt", "eng"):
            kompakt = enger
            engine = setzen(fuss_abstand=FUSS_MIN)
            if seitenzahl(ziel) < vorher:
                break
        else:
            kompakt = False
            engine = setzen(fuss_abstand=FUSS_MIN)

    # Jetzt steht fest, mit wie wenig Seiten das Dokument auskommt. Der Footer
    # rueckt so weit nach unten, wie es diese Seitenzahl zulaesst — reicht es
    # nur fuer den Mindestabstand, ist das immer noch besser als eine Seite,
    # auf der nichts als der Footer steht.
    minimal = seitenzahl(ziel)
    tiefe = text_tiefe(ziel)
    for ziel_hoehe in ZIELE if tiefe else ():
        abstand = round(tiefe - ziel_hoehe + FUSS_MIN, 1)
        if abstand <= FUSS_MIN:
            break
        engine = setzen(fuss_abstand=abstand)
        if seitenzahl(ziel) <= minimal:
            break
        engine = setzen(fuss_abstand=FUSS_MIN)

    seiten = deckblatt_seiten(ziel, daten)
    if seiten > 1:
        hinweise.append(
            f"Bildung/Skillset passen nicht neben den Profilkopf auf Seite 1, sie "
            f"laufen ueber {seiten} Seiten. Zusammenfassen: Gruppen zusammenlegen, "
            "je Gruppe die aussagekraeftigsten Eintraege behalten."
        )
        hinweise += spalten_pruefen(daten)
        # Der Zertifikatsblock steht mit auf Seite 1, gekuerzt wird aber im
        # Skillset: Zertifikate werden nur nach Rueckfrage gestrichen.
        if zertifikate:
            hinweise.append(
                f"Zertifikate stehen mit {len(zertifikate)} Tags auf Seite 1 — "
                "gestrichen wird dort nur nach Rueckfrage.")
    elif seiten < 0:
        hinweise.append(
            "Die Seitenaufteilung liess sich nicht pruefen: die erste Station "
            "steht nicht im auslesbaren Text des PDF. Bitte im PDF nachsehen, ob "
            "Bildung und Skillset zusammen auf Seite 1 stehen."
        )
    elif stufe != "normal":
        print(f"Bildung/Skillset {stufe} gesetzt, damit sie auf Seite 1 passen.")
    if zertifikate:
        print(f"Zertifikate: {len(zertifikate)} als Tags.")
    if kompakt:
        print(f"Stationen {kompakt} gesetzt, damit der Footer nicht allein auf "
              "einer Seite steht.")

    if stufen_datei:
        stufen_datei.parent.mkdir(parents=True, exist_ok=True)
        stufen_datei.write_text(json.dumps({
            "deckblatt": stufe,
            "stationen": kompakt or "normal",
            "seiten": seitenzahl(ziel),
            "engine": engine,
            "pdf": str(ziel),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{stufen_datei} geschrieben")

    print(f"{ziel} geschrieben (Engine: {engine})")
    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for h in hinweise:
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
