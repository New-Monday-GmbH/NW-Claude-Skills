#!/usr/bin/env python3
"""Schreibt aus einer cv.json die anonyme Fassung — Initialen statt Name.

    python3 scripts/anonymisieren.py cv.json cv-anonym.json
    python3 scripts/anonymisieren.py cv.json cv-anonym.json --jahre --firmen-map firmen.json

Anonymisiert wird auf den Daten, nicht im Renderer: beide Fassungen laufen
danach durch dieselbe unveraenderte Kette. render_cv.py und figma_plan.py
bekommen keine Sonderbehandlung, sie bauen weiter nur das, was in der JSON
steht. Drei Lecks erledigen sich damit von selbst, weil alle drei aus
person.name abgeleitet sind: der Dateiname des PDF, der PDF-Titel in den
Metadaten und die Frame-Namen im Figma-Plan.

Voreingestellt ist nur die Person — Name zu Initialen, Links weg, Silhouette
statt Foto, Namensnennungen im Fliesstext ersetzt. Arbeitgeber, Logos, Bildung
und Zeitraeume bleiben stehen: sie sind der Grund, warum ein Kunde das Dokument
ueberhaupt liest. Weitergehendes steht auf Schaltern, und dort nur, was sich
mechanisch entscheiden laesst:

    --jahre              streicht die Monate aus allen Zeitraeumen
    --firmen-map DATEI   Zuordnung {"Cocomore": "Digitalagentur"} auf firma,
                         kunde und Fliesstext; nimmt jeder ersetzten Firma
                         das Logo ab
    --foto-raster        silhouette.png statt silhouette.svg, fuer Engines,
                         die SVG im <img> nicht koennen (wkhtmltopdf)

Welche Hochschule wie zu verallgemeinern ist und welcher Skillset-Eintrag die
Muttersprache verraet, entscheidet dieses Skript nicht — das waere Raten. Es
bleibt Handarbeit an der cv.json, siehe SKILL.md.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_cv import MONATE, logoliste  # noqa: E402  — erst nach sys.path.insert moeglich

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Fliesstextfelder eines Stations- oder Projektknotens. Hier stehen Saetze, und
# hier greifen auch die Regeln fuer einzelne Namensteile.
FLIESSTEXT = ("zusammenfassung", "beschreibung")

# Felder, in denen ein Eigenname steht und kein Satz. Auch dort kann der Name
# der Person auftauchen — wer selbstaendig war, fuehrt "Timo Muster Freelance
# UX" als Arbeitgeber, und ohne diesen Durchgang stuende der Klarname in der
# anonymen Fassung. Gesucht wird hier nur die volle Schreibweise: ein einzelnes
# "Muster" in einem Firmennamen ist die Firma und nicht die Person.
NAMENSFELDER = ("firma", "kunde", "titel")

# Monatsnamen, an denen --jahre die Zeitraeume kuerzt. Die deutschen kommen aus
# render_cv.py, damit es nur eine Liste gibt; die englischen stehen hier, weil
# der Renderer sie nicht braucht, ein englischer Lebenslauf sie aber traegt.
MONATSWOERTER = set(MONATE) | {
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
}

# Felder, die einen Dateinamen tragen und keinen Text. Die Nachkontrolle laesst
# sie aus: der Skill liegt unter ~/.claude/skills/, und dieser Pfad traegt den
# Vornamen des Nutzers — der Fotopfad meldete sonst bei jedem Lauf einen
# Treffer, den niemand beheben kann.
PFADFELDER = ("foto", "logo")


# --- Name -------------------------------------------------------------------

def erster_buchstabe(teil):
    """Erster Buchstabe eines Namensteils. Zeichen davor werden uebersprungen."""
    for zeichen in teil:
        if zeichen.isalpha():
            return zeichen
    return ""


def initialen(name):
    """'Timo Muster' -> 'T. M.'. Leer, wenn kein Buchstabe im Namen steht.

    Ein Teil, der auf einen Punkt endet, ist ein Titel und bleibt woertlich
    stehen ('Dr. T. M.', 'Dipl.-Ing. T. M.'): er verraet niemanden und haelt die
    Zeile lesbar. Klein geschriebene Partikel entfallen, 'T. v. M.' liest sich
    wie ein Tippfehler. Ein Bindestrichname ist ein Teil und damit ein
    Buchstabe: 'Anna-Lena' wird zu 'A.', nicht zu 'A.-L.'.
    """
    teile = (name or "").split()
    namen = [t for t in teile if not t.endswith(".")]
    # "Dr." allein ist kein Name. Ohne diese Zeile kaeme "Dr." als Kuerzel
    # zurueck, der Hinweis auf den fehlenden Namen bliebe aus, und "Dr." stuende
    # im Dateinamen, im PDF-Titel und in den Figma-Frames.
    if not any(erster_buchstabe(t) for t in namen):
        return ""
    # Ist gar nichts gross geschrieben, ist der Name klein getippt und besteht
    # nicht aus lauter Partikeln — sonst bliebe von "timo muster" nichts uebrig.
    partikel_weg = any(t != t.lower() for t in namen)
    kuerzel = []
    for teil in teile:
        if teil.endswith("."):
            kuerzel.append(teil)
            continue
        if partikel_weg and teil == teil.lower():
            continue
        buchstabe = erster_buchstabe(teil)
        if buchstabe:
            kuerzel.append(buchstabe.upper() + ".")
    return " ".join(kuerzel)


def muster(form):
    """Wortgrenzengenau, Gross-/Kleinschreibung egal.

    \\b taugt an den Raendern nicht: eine Form darf auf einem Punkt enden
    ('Dipl.-Ing. Timo Muster'), und hinter einem Punkt verlangt \\b ein
    Wortzeichen — der Treffer fiele durch.
    """
    return re.compile(r"(?<!\w)" + re.escape(form) + r"(?!\w)", re.IGNORECASE)


def namensregeln(name, daten):
    """Suchmuster fuer den Fliesstext als (Form, Muster, Ersatz), laengste zuerst.

    Die Reihenfolge ist der Grund fuer die Sortierung: griffe erst die Regel fuer
    'Timo', stuende danach 'T. M. Muster' da, und die Regel fuer 'Muster' machte
    daraus 'T. M. T. M.'.

    Ein Titel wird nicht einzeln gesucht — 'Dr.' allein gehoert niemandem — und
    steht nur dort im Ersatz, wo er auch im Fund stand: aus 'Dr. Timo Muster'
    wird 'Dr. T. M.', aus dem blossen 'Timo' mitten im Satz 'T. M.'.
    """
    voll = " ".join((name or "").split())
    teile = [t for t in voll.split() if not t.endswith(".")]
    ohne_titel = " ".join(teile)
    # Partikel einzeln zu suchen hiesse, jedes "von" im Dokument zu treffen.
    echte = [t for t in teile if t != t.lower()] or teile
    # Die verkuerzten Schreibweisen sind eigene Regeln und nicht die Summe der
    # Einzelteile: steht "Timo Muster" im Satz, waehrend die cv.json "Timo von
    # Muster" oder "Timo Peter Muster" fuehrt, greifen sonst nacheinander die
    # Regeln fuer "Timo" und "Muster" — und aus einem Namen werden zwei Kuerzel.
    rufname = " ".join([echte[0], echte[-1]]) if len(echte) > 2 else ""
    mehrteilig = [voll, ohne_titel, " ".join(echte), rufname]
    einzeln, offen = [], []
    volle_muster = [muster(f) for f in dict.fromkeys(f for f in mehrteilig if f)]
    for teil in (t for t in echte if len(t) > 1):
        grund = mehrdeutig(teil, daten, volle_muster)
        (offen if grund else einzeln).append((teil, grund))

    kuerzel, kurz = initialen(voll), initialen(ohne_titel)
    def regel(form):
        return (form, muster(form), kuerzel if form == voll else kurz)
    volle = [regel(f) for f in dict.fromkeys(f for f in mehrteilig if f)]
    regeln = volle + [regel(teil) for teil, _ in einzeln]
    schluessel = lambda r: len(r[0])
    return (sorted(regeln, key=schluessel, reverse=True),
            sorted(volle, key=schluessel, reverse=True), offen)


def mehrdeutig(teil, daten, volle_muster):
    """Warum ein einzelner Namensteil im Satz nicht die Person sein muss.

    Zwei Faelle, und fuer beide liegt der Beleg vor — geraten wird hier nicht:

    - Der Teil ist ein Monatsname. "Im Mai 2024 gestartet" hat mit einer
      Kandidatin namens Mai nichts zu tun, und "Im M. N. 2024" waere ein
      zerschossener Satz im Kundendokument.
    - Der Teil steht auch in einem Arbeitgeber, Kunden oder Stationstitel
      desselben Dokuments. Deutsche Firmen tragen reihenweise Familiennamen:
      Wer bei der "Feiler GmbH" war, heisst deshalb nicht Feiler — und wer so
      heisst, hat den Firmennamen trotzdem im Text stehen.

    Gibt den Grund zurueck oder None. Was hier landet, wird gemeldet statt
    ersetzt. Ein stehen gebliebener Vorname ist ein Fehler, den der Bericht
    sichtbar macht; ein zerschossener Satz ist einer, den niemand mehr sieht.
    """
    if teil.lower() in MONATSWOERTER:
        return "ein Monatsname ist"
    for _, _, pfad, wert in namensfelder(daten):
        # Erst den vollen Namen aus dem Feld nehmen. Steht er dort selbst drin —
        # "Timo Muster Freelance UX" als Arbeitgeber —, machte er sonst seine
        # eigenen Bestandteile mehrdeutig, und keiner davon wuerde je ersetzt.
        rest = wert
        for regel in volle_muster:
            rest = regel.sub(" ", rest)
        if muster(teil).search(rest):
            return f'auch in {pfad} "{wert}" steht'
    return None


def namensteile(name):
    """Die Namensteile, nach denen zum Schluss noch einmal gesucht wird.

    Kurze Teile bleiben aussen vor: ein zweibuchstabiger Namensteil steckt in zu
    vielen deutschen Woertern, die Meldung waere nur noch Rauschen.
    """
    teile = [t for t in " ".join((name or "").split()).split() if not t.endswith(".")]
    echte = [t for t in teile if t != t.lower()] or teile
    return [t for t in echte if len(t) > 2]


# --- Wo im Dokument Text steht ----------------------------------------------

def _knotentexte(knoten, pfad):
    for feld in FLIESSTEXT:
        if isinstance(knoten.get(feld), str) and knoten[feld]:
            yield knoten, feld, f"{pfad}.{feld}"
    aufgaben = knoten.get("aufgaben") or []
    for nummer, eintrag in enumerate(aufgaben):
        if isinstance(eintrag, str) and eintrag:
            yield aufgaben, nummer, f"{pfad}.aufgaben[{nummer}]"


def namensfelder(daten):
    """(Behaelter, Schluessel, Pfad, Wert) fuer jedes Feld mit einem Eigennamen.

    person.rolle gehoert dazu, obwohl dort eine Jobbezeichnung erwartet wird:
    Aus einem PDF oder LinkedIn-Export gezogene Rollenzeilen tragen regelmaessig
    den Namen mit — und render_cv.py baut den Dateinamen aus name UND rolle. Ein
    Klarname, der dort haengen bleibt, steht im Mailanhang ganz vorn.
    """
    person = daten.get("person") or {}
    if isinstance(person.get("rolle"), str) and person["rolle"]:
        yield person, "rolle", "person.rolle", person["rolle"]
    for i, station in enumerate(daten.get("stationen") or []):
        for feld in NAMENSFELDER:
            if isinstance(station.get(feld), str) and station[feld]:
                yield station, feld, f"stationen[{i}].{feld}", station[feld]
        for j, projekt in enumerate(station.get("projekte") or []):
            for feld in NAMENSFELDER:
                if isinstance(projekt.get(feld), str) and projekt[feld]:
                    pfad = f"stationen[{i}].projekte[{j}].{feld}"
                    yield projekt, feld, pfad, projekt[feld]


def textstellen(daten):
    """Jede Fliesstextstelle als (Behaelter, Schluessel, Pfad).

    Behaelter ist das dict oder die Liste, Schluessel entsprechend Feldname oder
    Index — damit liest der Aufrufer an derselben Stelle, an der er
    zurueckschreibt, und die Struktur wird nicht ein zweites Mal nachgebaut.
    """
    person = daten.get("person") or {}
    if isinstance(person.get("kurzprofil"), str) and person["kurzprofil"]:
        yield person, "kurzprofil", "person.kurzprofil"
    for i, station in enumerate(daten.get("stationen") or []):
        yield from _knotentexte(station, f"stationen[{i}]")
        for j, projekt in enumerate(station.get("projekte") or []):
            yield from _knotentexte(projekt, f"stationen[{i}].projekte[{j}]")


def alle_texte(wert, pfad="", feld=""):
    """Jeder String im Dokument als (Pfad, Text) — fuer die Nachkontrolle.

    Umgeschrieben werden nur die Felder aus textstellen(); gesucht wird zum
    Schluss ueberall, auch in bildung und skillset. Wer den Namen dort noch
    stehen hat, soll es erfahren, statt dass es niemandem auffaellt.
    """
    if feld in PFADFELDER:
        return
    if isinstance(wert, str):
        yield pfad, wert
    elif isinstance(wert, dict):
        for schluessel, unter in wert.items():
            unterpfad = f"{pfad}.{schluessel}" if pfad else f"{schluessel}"
            yield from alle_texte(unter, unterpfad, str(schluessel))
    elif isinstance(wert, list):
        for nummer, unter in enumerate(wert):
            yield from alle_texte(unter, f"{pfad}[{nummer}]", feld)


def firmenfelder(daten):
    """(Knoten, Feldname) fuer jede Firmen- und jede Kundennennung."""
    for station in daten.get("stationen") or []:
        if station.get("firma"):
            yield station, "firma"
        for projekt in station.get("projekte") or []:
            if projekt.get("kunde"):
                yield projekt, "kunde"


def zeitraumknoten(daten):
    """Jeder Knoten, der ein zeitraum-Feld tragen kann."""
    for station in daten.get("stationen") or []:
        yield station
        for projekt in station.get("projekte") or []:
            yield projekt
    for bildung in daten.get("bildung") or []:
        yield bildung


# --- Die Eingriffe ----------------------------------------------------------

def umgebung(text, anfang, ende, rand=30):
    """Ausschnitt um eine Fundstelle — der Bericht muss nachlesbar sein."""
    links = max(0, anfang - rand)
    rechts = min(len(text), ende + rand)
    ausschnitt = " ".join(text[links:rechts].split())
    return ("..." if links else "") + ausschnitt + ("..." if rechts < len(text) else "")


def ersetze_namen(daten, regeln, volle):
    """Namensnennungen im Fliesstext durch die Initialenform ersetzen.

    Die einzige Stelle, an der dieses Skript fremden Text umschreibt. Deshalb
    geht jeder Treffer mit Feld und Umgebung in den Bericht, statt still zu
    verschwinden: der Nutzer muss nachlesen koennen, was aus seinem Satz wurde.
    """
    treffer = []
    for behaelter, schluessel, pfad in textstellen(daten):
        text = behaelter[schluessel]
        for _, regel, ersatz in regeln:

            def tauschen(fund, wert=ersatz, feldpfad=pfad):
                # Stand der Name am Satzende, treffen der Punkt der letzten
                # Initiale und der Satzpunkt aufeinander: "geleitet von T. M..".
                # Einer davon reicht.
                if wert.endswith(".") and fund.string[fund.end():fund.end() + 1] == ".":
                    wert = wert[:-1]
                treffer.append((feldpfad, fund.group(0), wert,
                                umgebung(fund.string, fund.start(), fund.end())))
                return wert

            text = regel.sub(tauschen, text)
        behaelter[schluessel] = text

    # In firma, kunde, titel und rolle steht ein Eigenname und kein Satz. Dort
    # greifen nur die mehrteiligen Regeln: "Timo Muster Freelance UX" wird zu
    # "T. M. Freelance UX", das blosse "Muster" in "Muster Logistik GmbH" bleibt
    # die Firma.
    for behaelter, schluessel, pfad, _ in namensfelder(daten):
        text = behaelter[schluessel]
        for _, regel, ersatz in volle:

            def tauschen_feld(fund, wert=ersatz, feldpfad=pfad):
                treffer.append((feldpfad, fund.group(0), wert,
                                umgebung(fund.string, fund.start(), fund.end())))
                return wert

            text = regel.sub(tauschen_feld, text)
        behaelter[schluessel] = text
    return treffer


def restnennungen(daten, teile):
    """Namensteile, die nach allen Ersetzungen noch irgendwo im Dokument stehen.

    Gesucht wird als blosse Zeichenfolge, nicht wortgrenzengenau: 'Musterhaus'
    und 'Florians' fallen durch die Wortgrenze, weil ein Umbau der Genitivform
    Raten waere. Uebersehen darf man sie trotzdem nicht — also gemeldet und von
    Hand entschieden.
    """
    offen = []
    for pfad, text in alle_texte(daten):
        klein = text.lower()
        for teil in teile:
            stelle = klein.find(teil.lower())
            if stelle >= 0:
                ausschnitt = umgebung(text, stelle, stelle + len(teil))
                offen.append(f'{pfad}: "{teil}" in: {ausschnitt}')
    return offen


def nur_jahr(zeitraum):
    """'August 2019 - Juli 2022' -> '2019 - 2022'. 'Heute' bleibt stehen.

    Monatsgenaue Daten machen den Abgleich mit einem LinkedIn-Profil trivial —
    ueber sie ist die Person in Minuten wieder benannt. Wo statt einer Jahreszahl
    'Heute' oder 'Present' steht, steht eine Aussage und kein Datum; die bleibt.
    """
    # Dieselben drei Striche wie spanne() in render_cv.py: eine cv.json traegt
    # mal den Bindestrich, mal den Halbgeviert-, mal den Geviertstrich. Als
    # Escape geschrieben, damit die Quelle ASCII bleibt.
    def monat_weg(stueck):
        # Gestrichen wird der Monat, nicht alles ausser der Jahreszahl. Sonst
        # wuerde aus "Seit 2019" ein "2019" — aus einer laufenden Station ein
        # Zeitpunkt, und das ist eine andere Aussage.
        return re.sub(
            r"(?<!\w)([^\W\d_]+)(\s+)(\d{4})(?!\d)",
            lambda f: f.group(3) if f.group(1).lower() in MONATSWOERTER
            else f.group(0),
            stueck)

    teile = re.split(r"(\s*[-\u2013\u2014]\s*)", zeitraum or "")
    # Die ungeraden Stuecke sind die Trennstriche selbst — sie kommen aus der
    # Klammer im Muster und bleiben unangetastet.
    return "".join(teil if nummer % 2 else monat_weg(teil)
                   for nummer, teil in enumerate(teile))


def jahre_kuerzen(daten):
    gekuerzt = []
    for knoten in zeitraumknoten(daten):
        alt = knoten.get("zeitraum")
        if not isinstance(alt, str) or not alt:
            continue
        neu = nur_jahr(alt)
        if neu != alt:
            knoten["zeitraum"] = neu
            gekuerzt.append(f"{alt} -> {neu}")
    return gekuerzt


def firmen_ersetzen(daten, karte):
    """Firmen durch die Oberbegriffe aus der Zuordnung ersetzen.

    Das Skript erfindet keinen Oberbegriff: was nicht in der Datei steht, bleibt
    stehen und wird als offen gemeldet. Eine geratene Branche waere schlimmer als
    ein stehen gebliebener Firmenname — sie ist womoeglich falsch und faellt dann
    niemandem mehr auf.
    """
    regeln = [(str(name), str(neu), muster(str(name))) for name, neu in karte.items()]
    ersetzt, ohne_logo, offen = [], [], []
    for knoten, feld in firmenfelder(daten):
        wert = str(knoten[feld])
        oberbegriff = next((n for _, n, regel in regeln if regel.search(wert)), None)
        if oberbegriff is None:
            offen.append(wert)
            continue
        # Ersetzt wird das ganze Feld, nicht nur der Name darin: aus "Cocomore
        # AG" wuerde sonst "Digitalagentur AG", und eine Rechtsform gehoert
        # nicht hinter einen Oberbegriff.
        knoten[feld] = oberbegriff
        ersetzt.append(f"{wert} -> {oberbegriff}")
        # Ein Logo neben "Grossbank" hebt die Anonymisierung sofort wieder auf.
        for datei in logoliste(knoten.get("logo")):
            ohne_logo.append(f"{oberbegriff}: {datei}")
        knoten.pop("logo", None)

    # Im Fliesstext bleibt der Satz stehen, nur der Name darin wechselt: "Fuer
    # Cocomore entwickelt" soll "Fuer Digitalagentur entwickelt" werden und
    # nicht auf den Oberbegriff allein zusammenfallen.
    im_text = []
    for behaelter, schluessel, pfad in textstellen(daten):
        text = behaelter[schluessel]
        for name, neu, regel in regeln:
            if regel.search(text):
                im_text.append(f"{pfad}: {name} -> {neu}")
                text = regel.sub(lambda _, wert=neu: wert, text)
        behaelter[schluessel] = text
    return ersetzt, ohne_logo, im_text, list(dict.fromkeys(offen))


def silhouette_pruefen(pfad):
    """Hinweise zur Silhouettendatei — leer, wenn sie benutzbar ist.

    Geprueft wird nicht nur, ob die Datei da ist, sondern beim SVG auch, ob sie
    sich parsen laesst: WeasyPrint laesst ein kaputtes SVG still weg und rendert
    eine leere Fotospalte, ohne dass irgendwo etwas steht. Genau dieser Fall ist
    schon einmal eingetreten — ein doppelter Bindestrich im XML-Kommentar, den
    XML dort verbietet. Lieber hier laut als spaeter unsichtbar.
    """
    if not pfad.exists():
        return [f"Silhouette nicht gefunden: {pfad} — die Fotospalte bliebe leer."]
    if pfad.suffix.lower() != ".svg":
        return []
    try:
        ET.fromstring(pfad.read_bytes())
    except ET.ParseError as fehler:
        return [f"Silhouette ist kein gueltiges XML ({pfad.name}: {fehler}). "
                "WeasyPrint laesst sie dann kommentarlos weg — bis das behoben "
                "ist, mit --foto-raster auf silhouette.png ausweichen."]
    return []


# --- Bericht ----------------------------------------------------------------

def anzahl(menge, einzahl, mehrzahl):
    """'1 Namensnennung' / '2 Namensnennungen' — der Bericht wird gelesen."""
    return f"{menge} {einzahl if menge == 1 else mehrzahl}"


def abschnitt(ueberschrift, zeilen):
    if not zeilen:
        return
    print(ueberschrift)
    for zeile in zeilen:
        print("  " + zeile)


def argumente(rohargumente):
    """Schalter von Pfaden trennen, von Hand wie in render_cv.py."""
    jahre, raster, karte, pfade = False, False, None, []
    rest = list(rohargumente)
    while rest:
        arg = rest.pop(0)
        if arg == "--jahre":
            jahre = True
        elif arg == "--foto-raster":
            raster = True
        elif arg == "--firmen-map":
            if not rest:
                raise SystemExit("--firmen-map braucht einen Dateinamen")
            karte = Path(rest.pop(0))
        elif arg.startswith("--"):
            raise SystemExit(f"Unbekannter Schalter: {arg}\n{__doc__}")
        else:
            pfade.append(arg)
    return jahre, raster, karte, pfade


def main():
    jahre, raster, karte_datei, pfade = argumente(sys.argv[1:])
    if len(pfade) < 2:
        raise SystemExit(__doc__)

    quelle, ziel = Path(pfade[0]), Path(pfade[1])
    # Eine kaputte cv.json ist der haeufigste Abbruchgrund. Ein Traceback sagt
    # zwar auch, dass etwas fehlt, aber nicht was zu tun ist — und die anderen
    # Skripte des Skills melden ihre Probleme im Klartext.
    if not quelle.exists():
        raise SystemExit(f"Quelldatei nicht gefunden: {quelle}")
    try:
        daten = json.loads(quelle.read_text(encoding="utf-8"))
    except json.JSONDecodeError as fehler:
        raise SystemExit(f"{quelle} ist kein lesbares JSON: {fehler}")
    if not isinstance(daten, dict):
        raise SystemExit(f"{quelle} enthaelt {type(daten).__name__} statt eines "
                         "Objekts — erwartet wird eine cv.json.")
    for feld, art in (("person", dict), ("stationen", list), ("bildung", list)):
        if feld in daten and daten[feld] is not None and not isinstance(daten[feld], art):
            raise SystemExit(f"{quelle}: {feld} ist {type(daten[feld]).__name__} "
                             f"statt {art.__name__} — so laesst sich daraus "
                             "keine anonyme Fassung bauen.")
    person = daten.setdefault("person", {})
    hinweise = []

    name = " ".join(str(person.get("name") or "").split())
    kuerzel = initialen(name)
    if not kuerzel:
        hinweise.append(
            "person.name fehlt oder traegt keinen Buchstaben — das Feld bleibt "
            "leer. Dateiname, PDF-Titel und Figma-Frames kommen dann ohne "
            "Namensteil, und im Fliesstext wird nichts ersetzt."
        )
    person["name"] = kuerzel

    # Der Schluessel wird entfernt und nicht auf [] gesetzt. Das Template prueft
    # auf {% if person.links %}, beides ginge — aber ein fehlender Schluessel ist
    # ehrlicher als eine leere Liste.
    entfernte = [str(l.get("titel") or l.get("url") or "?")
                 for l in (person.pop("links", None) or [])]

    # Die Silhouette kommt auch dann, wenn die Person gar kein Foto hatte: in der
    # anonymen Fassung ist eine leere Fotospalte kein Normalzustand, sondern
    # sieht nach einem Fehler aus.
    silhouette = ASSETS / ("silhouette.png" if raster else "silhouette.svg")
    hinweise += silhouette_pruefen(silhouette)
    altes_foto = person.get("foto") or "(keins)"
    person["foto"] = str(silhouette)

    # Die Firmen kommen vor den Namen an die Reihe. Andersherum haette eine
    # Namensersetzung "Feiler GmbH" schon zu "F. F. GmbH" gemacht, und die
    # Zuordnung liefe im Fliesstext ins Leere, ohne dass es jemand merkt.
    firmen, logos_weg, firmen_im_text, firmen_offen = [], [], [], []
    if karte_datei:
        if not karte_datei.exists():
            raise SystemExit(f"Firmen-Zuordnung nicht gefunden: {karte_datei}")
        firmen, logos_weg, firmen_im_text, firmen_offen = firmen_ersetzen(
            daten, json.loads(karte_datei.read_text(encoding="utf-8")))

    treffer, offen = [], []
    if kuerzel:
        regeln, volle, offen = namensregeln(name, daten)
        treffer = ersetze_namen(daten, regeln, volle)
    for teil, grund in offen:
        hinweise.append(
            f'"{teil}" wurde im Fliesstext nicht ersetzt, weil der Namensteil '
            f"{grund}. Ist an einer Stelle doch die Person gemeint, gehoert sie "
            "von Hand in die cv.json.")

    gekuerzt = jahre_kuerzen(daten) if jahre else []

    # Erst ganz zum Schluss suchen: gemeldet wird nur, was auch nach allen
    # Ersetzungen noch dasteht.
    hinweise += [f"Namensteil steht noch im Dokument — {stelle}"
                 for stelle in restnennungen(daten, namensteile(name))]

    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    print(f"Name:  {name or '(fehlt)'} -> {kuerzel or '(leer)'}")
    print(f"Foto:  {altes_foto} -> {silhouette}")
    print(f"Links: {len(entfernte)} entfernt"
          + (f" ({', '.join(entfernte)})" if entfernte else ""))
    print(f"Text:  {anzahl(len(treffer), 'Namensnennung', 'Namensnennungen')} ersetzt"
          + (f", {len(offen)} Namensteil(e) mehrdeutig stehen gelassen" if offen else ""))
    for pfad, gefunden, ersatz, stelle in treffer:
        print(f'  {pfad}: "{gefunden}" -> "{ersatz}"')
        print(f"    {stelle}")
    abschnitt(f"Zeitraeume auf Jahre gekuerzt ({len(gekuerzt)}):", gekuerzt)
    abschnitt(f"Firmen ersetzt ({len(firmen)}):", firmen)
    abschnitt("Logos entfernt — sie verrieten die ersetzte Firma sofort wieder:",
              logos_weg)
    abschnitt("Firmen auch im Fliesstext ersetzt — die Saetze bitte gegenlesen, "
              "eine Rechtsform davor oder dahinter bleibt stehen:", firmen_im_text)
    abschnitt("Offen — steht nicht in der Firmen-Zuordnung und bleibt stehen:",
              firmen_offen)
    print(f"{ziel} geschrieben")

    if hinweise:
        print("\nPruefen:", file=sys.stderr)
        for hinweis in hinweise:
            print(f"  - {hinweis}", file=sys.stderr)


if __name__ == "__main__":
    main()
