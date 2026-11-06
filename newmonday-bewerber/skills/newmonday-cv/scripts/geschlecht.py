#!/usr/bin/env python3
"""Berufsbezeichnungen der Person: gemischte Formen finden, neutral setzen.

Zwei Nutzer, eine Liste:

- render_cv.py meldet in der vollstaendigen Fassung, wenn dieselbe Person
  einmal "Designerin" und einmal "Designer" heisst (mischung). Die cv.json
  steht in der Form der Person, einheitlich - Quellen liefern oft gemischt
  (LinkedIn "UX/UI-Designer", der Lebenslauf "Designerin").
- anonymisieren.py setzt in der anonymen Fassung die Doppelpunkt-Form
  (neutralisieren) und meldet, was danach noch auf ein Geschlecht deutet
  (restmeldungen). Nur Deutsch; englische Titel sind neutral, dort wird nur
  gemeldet.

Die Person bezeichnet eine Rolle in person.rolle, ein Stationstitel und eine
Wendung wie "Als UX-Designerin habe ich ..." oder "Rolle: Entwicklerin". Nur
dort wird die maskuline Grundform angefasst - sonst meint "Entwickler" oft
andere ("Schulungen fuer Entwickler"). Feminine Formen werden ueberall in den
Texten der Person neutralisiert. Gebeugte Formen ("des UI-Designers"),
Plurale mit :innen/*innen und Firmennamen bleiben unberuehrt.
"""
import re

# Grundformen, deren Femininum auf -in endet. Gross-/Kleinschreibung egal,
# auch als Wortende: "Softwareentwickler", "UX/UI-Designerin", "Projektleiter".
STAEMME = (
    "designer", "entwickler", "berater", "leiter", "architekt", "analyst",
    "spezialist", "werkstudent", "praktikant", "referent", "mitarbeiter",
    "manager", "gestalter", "programmierer", "ingenieur", "informatiker",
    "gruender", "gründer", "inhaber", "geschäftsführer", "koordinator",
    "redakteur", "texter", "trainer", "dozent", "student", "assistent",
    "absolvent", "freelancer", "moderator", "mentor", "researcher",
    "developer", "engineer", "consultant", "owner",
)
# Englische Titel ohne deutsches Femininum im Alltag ("Frontend Developer"
# steht auch bei Frauen oft so) - sie zaehlen fuer die Mischung nur gegen
# ihre eigene feminine Form.
ENGLISCH = {"researcher", "developer", "engineer", "consultant", "owner"}

# Ein Wort, das auf einen Stamm endet, optional mit -in. Danach kein
# Wortzeichen und kein Gender-Zeichen: "Designers", "Entwicklerinnen",
# "Designer:innen", "Entwickler-Team" und "Designer/in" bleiben.
WORT = re.compile(
    r"(?<![\w/.-])(?P<wort>[\w/.-]*?(?P<stamm>" + "|".join(STAEMME) + r"))"
    r"(?P<in>in)?(?![\w:*/_-])", re.IGNORECASE)

# "Als Senior UX / UI Designerin", "Rolle: Entwickler", "Position: Beraterin".
# Dazwischen nur, was zur Bezeichnung gehoert: gross geschriebene Woerter,
# Schraegstrich, Adjektive. Artikel und Praepositionen beenden die Wendung -
# "als Ansprechpartner fuer Entwickler" meint nicht die Person.
AUSLOESER = re.compile(r"(?i)(?:\bals|rolle:|position:)\s+((?:\S+\s+){0,4})$")
DAZWISCHEN = re.compile(r"[A-ZÄÖÜ][\w/&.+-]*|[/&]|[a-zäöüß]+(?:e|er|en|es|em)")
STOPP = {"der", "die", "den", "dem", "des", "eine", "einer", "einen", "einem",
         "eines", "andere", "anderen", "anderer", "alle", "viele", "mehrere",
         "unsere", "unserer", "unseren", "weitere", "weiteren", "diese",
         "dieser", "diesen", "jede", "jeder", "jeden", "seine", "ihre"}

# Was nach dem Neutralisieren noch auf ein Geschlecht deuten kann - gemeldet,
# nicht geaendert.
REST_DE = [
    (re.compile(r"\b(?:er|sie|ihm|ihn|ihr|ihre[mnrs]?|sein|seine[mnrs]?)\b", re.IGNORECASE),
     "Pronomen"),
    (re.compile(r"\b(?:Frau|Herrn?)\b"), "Anrede"),
    (re.compile(r"(?<![:*/_])\b\w{3,}(?:erin|istin|entin|antin|ektin|eurin|orin|ologin|ertin)\b",
                re.IGNORECASE), "feminine Form"),
    (re.compile(r"\b\w*(?:kauf|fach)(?:frau|mann)\b", re.IGNORECASE), "Berufsbezeichnung"),
    # Artikel oder Adjektiv vor der neutralen Form: "zur Designer:in",
    # "freiberuflicher Entwickler:in".
    (re.compile(r"\b(?!(?:als|und|oder|sowie|bzw)\b)[a-zäöüß]+\s+[\w/.-]+:in\b"),
     "Artikel/Adjektiv vor der neutralen Form"),
]
REST_EN = [
    (re.compile(r"\b(?:she|he|her|hers|herself|him|his|himself|Mrs?|Ms|Miss)\b",
                re.IGNORECASE), "Pronomen/Anrede"),
]


def _person_texte(daten):
    """(Behaelter, Schluessel, Pfad, ist_titel) fuer jeden Text der Person."""
    person = daten.get("person") or {}
    if isinstance(person.get("rolle"), str):
        yield person, "rolle", "person.rolle", True
    if isinstance(person.get("kurzprofil"), str):
        yield person, "kurzprofil", "person.kurzprofil", False
    knoten = []
    for i, s in enumerate(daten.get("stationen") or []):
        if isinstance(s.get("titel"), str):
            yield s, "titel", f"stationen[{i}].titel", True
        knoten.append((s, f"stationen[{i}]"))
        knoten += [(p, f"stationen[{i}].projekte[{j}]")
                   for j, p in enumerate(s.get("projekte") or []) if isinstance(p, dict)]
    knoten += [(p, f"projekte[{i}]") for i, p in enumerate(daten.get("projekte") or [])
               if isinstance(p, dict)]
    for k, pfad in knoten:
        for feld in ("zusammenfassung", "beschreibung"):
            if isinstance(k.get(feld), str):
                yield k, feld, f"{pfad}.{feld}", False
        aufgaben = k.get("aufgaben") or []
        for j, a in enumerate(aufgaben):
            if isinstance(a, str):
                yield aufgaben, j, f"{pfad}.aufgaben[{j}]", False
    for i, b in enumerate(daten.get("bildung") or []):
        if isinstance(b, dict) and isinstance(b.get("abschluss"), str):
            yield b, "abschluss", f"bildung[{i}].abschluss", False


def _bezeichnet_person(text, fund, ist_titel, erste_im_abschnitt):
    """Meint die Grundform an dieser Stelle die Person selbst?"""
    if ist_titel:
        return erste_im_abschnitt
    vor = AUSLOESER.search(text[:fund.start()])
    if not vor:
        return False
    zwischen = vor.group(1).split()
    return all(DAZWISCHEN.fullmatch(w) and w.lower() not in STOPP for w in zwischen)


def _funde(text, ist_titel):
    """(Fund, bezeichnet_person) fuer jede Bezeichnung im Text.

    Im Titel bezeichnet je Abschnitt nur die erste die Person: "UX/UI-Designer,
    Berater fuer digitale Barrierefreiheit" sind zwei Rollen, "Entwickler fuer
    Halbleiter" ist eine.
    """
    gesehen_bis = -1
    for fund in WORT.finditer(text):
        trenner = re.search(r"[,;|&]|\bund\b|\bsowie\b", text[gesehen_bis + 1:fund.start()])
        erste = gesehen_bis < 0 or bool(trenner)
        yield fund, _bezeichnet_person(text, fund, ist_titel, erste)
        gesehen_bis = fund.end() - 1


def mischung(daten):
    """Hinweise, wenn die Person feminin UND maskulin bezeichnet wird. Nur de."""
    if daten.get("sprache", "de") == "en":
        return []
    feminin, maskulin = {}, {}
    for behaelter, schluessel, pfad, ist_titel in _person_texte(daten):
        text = behaelter[schluessel]
        for fund, person in _funde(text, ist_titel):
            stamm = fund.group("stamm").lower().replace("ü", "ue")
            if fund.group("in"):
                feminin.setdefault(stamm, []).append(f"„{fund.group(0)}“ ({pfad})")
            elif person:
                maskulin.setdefault(stamm, []).append(f"„{fund.group(0)}“ ({pfad})")
    if not feminin:
        return []
    # Derselbe Stamm in beiden Formen ist immer gemischt; ein deutscher Stamm
    # maskulin neben irgendeinem Femininum auch ("Designerin" und "Berater").
    gemischt = [s for s in maskulin if s in feminin or s not in ENGLISCH]
    if not gemischt:
        return []
    fem = [x for v in feminin.values() for x in v]
    mas = [x for s in gemischt for x in maskulin[s]]
    return [f"Berufsbezeichnungen gemischt: feminin {', '.join(fem)} – maskulin "
            f"{', '.join(mas)}. In der cv.json einheitlich in der Form der Person "
            "schreiben (SKILL.md, Schritt 2)."]


def neutralisieren(daten):
    """Doppelpunkt-Form in den Texten der Person. Aendert die Daten an Ort und
    Stelle, gibt jede Ersetzung als (Pfad, altes Wort, neues Wort) zurueck.
    Nur de."""
    if daten.get("sprache", "de") == "en":
        return []
    geaendert = []
    for behaelter, schluessel, pfad, ist_titel in list(_person_texte(daten)):
        alt = behaelter[schluessel]
        teile, stelle = [], 0
        for fund, person in _funde(alt, ist_titel):
            if fund.group("in") or person:
                teile += [alt[stelle:fund.start()], fund.group("wort") + ":in"]
                stelle = fund.end()
                geaendert.append((pfad, fund.group(0), teile[-1]))
        if teile:
            behaelter[schluessel] = "".join(teile) + alt[stelle:]
    return geaendert


def restmeldungen(daten):
    """Was in den Texten der Person noch auf ein Geschlecht deuten kann."""
    muster = REST_EN if daten.get("sprache", "de") == "en" else REST_DE
    meldungen = []
    for behaelter, schluessel, pfad, _ in _person_texte(daten):
        text = behaelter[schluessel]
        for regel, art in muster:
            for fund in regel.finditer(text):
                links, rechts = max(0, fund.start() - 25), fund.end() + 25
                meldungen.append(f"{art} „{fund.group(0)}“ in {pfad}: "
                                 f"…{' '.join(text[links:rechts].split())}…")
    return meldungen
