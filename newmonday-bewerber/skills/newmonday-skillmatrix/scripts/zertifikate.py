#!/usr/bin/env python3
"""Plant die Zertifikatssektion der Skillmatrix — fuer PDF und Figma-Plan gleich.

    python3 scripts/zertifikate.py skillmatrix.json

zeigt, was die Sektion zeigen wird: Karte, Kacheln, Buendel, Hoehe.

Die Zertifikate stehen als Kacheln, vier je Reihe (komponenten.zertkachel):
Bild oben auf der Buehne, darunter Titel und "Aussteller · Jahr". Eine andere
Darstellung gibt es nicht; die frueheren Schalter "zertifikate_darstellung" und
"hervorheben" werden mit Hinweis uebergangen. Steht "qualifikationen" in der
JSON, kommt zwischen Ueberschrift und Kacheln die Karte "Erworbene
Qualifikationen" (komponenten.qualikarte): ein Satz und Tags. Sie wird nie
gekuerzt.

Die Sektion ist hoechstens komponenten.zertifikate.max-hoehe hoch (924), die
Karte eingerechnet: ohne Karte drei Kachelreihen, mit Karte zwei. Reicht der
Platz nicht, werden die aeltesten Eintraege eines Ausstellers zu einer Kachel
gebuendelt ("+ 3 weitere Kurse von Anthropic"), bis es passt — der neueste
Eintrag jedes Ausstellers bleibt sichtbar. Reicht auch das nicht (zu viele
Aussteller), kommen die aeltesten Kacheln in eine Sammelkachel ("+ 5 weitere
Zertifikate"). Gestrichen wird nichts.

Die Hoehe wird hier gerechnet, nicht gemessen: aus tokens.json und einer
Zeilenschaetzung mit den eingebetteten Schriften (etwas grosszuegig, damit die
Schaetzung eher eine Zeile zu viel annimmt). So treffen render_skillmatrix.py
und figma_plan.py dieselbe Auswahl. render_skillmatrix.py misst die Sektion
danach im fertigen Layout nach und meldet Abweichungen.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert

# Breiten werden um diesen Faktor grosszuegiger geschaetzt: Die Schaetzung kennt
# kein Kerning und bricht nur an Leerzeichen um, Pango auch nach Bindestrichen.
SICHERHEIT = 1.03

ALTES_MODELL = """\
Die skillmatrix.json nutzt das alte Zertifikatsmodell: eine Liste
"zertifikat_bilder" getrennt von den Eintraegen in "zertifikate".

Seit 2026-10-03 traegt jedes Zertifikat sein Bild selbst:

  "zertifikate": [
    {"titel": "Claude Code in Action", "aussteller": "Anthropic",
     "datum": "September 2026", "bild": "arbeit/zertifikate/zert-01-....png"}
  ]

Welches Bild zu welchem Zertifikat gehoert, laesst sich nicht erraten - deshalb
bricht das Skript hier ab, statt Bilder neben die falschen Titel zu setzen.
Umstellen: je Zertifikat einen Eintrag (bisher zu einer Karte gebuendelte
einzeln) mit titel, aussteller, datum und bild, neueste zuerst; "jahr" wird zu
"datum", "beschreibung" und "tags" entfallen; "zertifikat_bilder" loeschen.
Siehe SKILL.md, Schritt 3."""

_MONATE = [
    ("jan", 1), ("feb", 2), ("mär", 3), ("maer", 3), ("mrz", 3), ("mar", 3),
    ("apr", 4), ("mai", 5), ("may", 5), ("jun", 6), ("jul", 7), ("aug", 8),
    ("sep", 9), ("okt", 10), ("oct", 10), ("nov", 11), ("dez", 12), ("dec", 12),
]


def datum_lesen(text):
    """'September 2026' -> (2026, 9), '09/2026' -> (2026, 9), '2021' -> (2021, None).
    Ohne Jahr (None, None)."""
    t = str(text or "").strip().lower()
    jahr = re.search(r"\b(?:19|20)\d{2}\b", t)
    if not jahr:
        return None, None
    monat = None
    zahl = re.search(r"\b(\d{1,2})\s*[./-]\s*(?:19|20)\d{2}\b", t)
    if zahl and 1 <= int(zahl.group(1)) <= 12:
        monat = int(zahl.group(1))
    else:
        for name, nr in _MONATE:
            if re.search(r"\b" + name, t):
                monat = nr
                break
    return int(jahr.group(0)), monat


def _sortierschluessel(e):
    jahr, monat = datum_lesen(e.get("datum"))
    return (jahr or 0, monat or 0)


def _jahr_text(datum):
    jahr, _ = datum_lesen(datum)
    return str(jahr) if jahr else str(datum or "").strip()


# --- Zeilenschaetzung -------------------------------------------------------

class Schaetzer:
    """Zeilenzahl eines Texts bei gegebener Breite, mit den Schriftdateien und
    Textstilen aus tokens.json. Umbruch an Leerzeichen, wie ein Browser.
    sicherheit 1.0 schaetzt knapp (Gegenrechnung gegen ein fertiges PDF), die
    Vorgabe grosszuegig (Planung, die halten muss)."""

    def __init__(self, ds, sicherheit=SICHERHEIT):
        self.ds = ds
        self.sicherheit = sicherheit
        self._schriften = {}
        self._zeilen = {}

    def _schrift(self, verwendung):
        if verwendung not in self._schriften:
            from PIL import ImageFont
            s = design_system.textstil(self.ds, verwendung)
            datei = design_system.FONTS / self.ds["schriften"][s["familie"]][str(s["gewicht"])]
            lauf = s.get("laufweite") or 0
            if s.get("laufweite_prozent"):
                lauf = s["laufweite_prozent"] / 100 * s["groesse"]
            self._schriften[verwendung] = (ImageFont.truetype(str(datei), size=s["groesse"]), lauf)
        return self._schriften[verwendung]

    def breite(self, text, verwendung):
        """Breite eines einzeiligen Texts in pt, so grosszuegig wie zeilen()."""
        schrift, lauf = self._schrift(verwendung)
        text = str(text or "")
        return (schrift.getlength(text) + lauf * len(text)) * self.sicherheit

    def zeilen(self, teile, breite):
        """teile: [(text, verwendung), ...] hintereinander in einem Absatz."""
        schluessel = (tuple(map(tuple, teile)), round(breite, 2))
        if schluessel not in self._zeilen:
            self._zeilen[schluessel] = self._umbrechen(teile, breite)
        return self._zeilen[schluessel]

    def _umbrechen(self, teile, breite):
        woerter, luecke, neu = [], 0.0, True        # woerter: [breite, leerraum davor]
        for text, verwendung in teile:
            schrift, lauf = self._schrift(verwendung)
            for stueck in re.findall(r"\s+|\S+", str(text or "")):
                if stueck.isspace():
                    luecke += (schrift.getlength(" ") + lauf) * self.sicherheit
                    neu = True
                    continue
                b = (schrift.getlength(stueck) + lauf * len(stueck)) * self.sicherheit
                if neu or not woerter:
                    woerter.append([b, luecke])
                    luecke, neu = 0.0, False
                else:                                # Wort laeuft ueber den Stilwechsel
                    woerter[-1][0] += b
        if not woerter:
            return 0
        zeilen, x = 1, woerter[0][0]
        for b, l in woerter[1:]:
            if x + l + b <= breite:
                x += l + b
            else:
                zeilen, x = zeilen + 1, b
        return zeilen


# --- Eintraege lesen --------------------------------------------------------

def einlesen(daten):
    """(eintraege, hinweise). Neueste zuerst; altes Modell ohne Bilderliste wird
    uebernommen und gemeldet, mit Bilderliste bricht es ab (ALTES_MODELL)."""
    if daten.get("zertifikat_bilder"):
        raise SystemExit(ALTES_MODELL)
    hinweise, eintraege, jahr_alt, weg, markiert = [], [], 0, 0, 0
    if daten.get("zertifikate_darstellung") not in (None, "", "kacheln"):
        hinweise.append(f"„zertifikate_darstellung“: „{daten['zertifikate_darstellung']}“ gibt es "
                        "nicht mehr — die Zertifikate stehen immer als Kacheln. Das Feld wird "
                        "uebergangen; in der JSON loeschen.")
    elif daten.get("zertifikate_darstellung"):
        hinweise.append("„zertifikate_darstellung“ ist ueberfluessig — die Zertifikate stehen "
                        "immer als Kacheln. In der JSON loeschen.")
    for nr, z in enumerate(daten.get("zertifikate") or []):
        e = {"titel": " ".join(str(z.get("titel") or "").split()),
             "aussteller": " ".join(str(z.get("aussteller") or "").split()),
             "datum": " ".join(str(z.get("datum") or "").split()),
             "bild": z.get("bild") or None,
             "nr": nr}
        if z.get("hervorheben"):
            markiert += 1
        if not e["datum"] and z.get("jahr"):
            e["datum"] = str(z["jahr"]).strip()
            jahr_alt += 1
        if z.get("beschreibung") or z.get("tags"):
            weg += 1
        if not e["titel"]:
            hinweise.append("Ein Zertifikat ohne Titel.")
        if not e["datum"]:
            hinweise.append(f"Zertifikat ohne Datum: {e['titel']} — steht zuletzt.")
        elif datum_lesen(e["datum"])[0] is None:
            hinweise.append(f"Zertifikat „{e['titel']}“: Datum „{e['datum']}“ nicht lesbar "
                            "(erwartet „September 2026“ oder „2026“) — steht zuletzt.")
        if not e["aussteller"]:
            hinweise.append(f"Zertifikat ohne Aussteller: {e['titel']}")
        eintraege.append(e)
    if jahr_alt:
        hinweise.append(f"{jahr_alt} Zertifikat(e) mit dem alten Feld „jahr“ — als „datum“ "
                        "uebernommen. In der JSON auf „datum“ umstellen (Monat und Jahr, "
                        "wenn belegt).")
    if weg:
        hinweise.append(f"{weg} Zertifikat(e) mit „beschreibung“/„tags“ — beide Felder "
                        "entfallen und werden nicht gezeigt.")
    if markiert:
        hinweise.append(f"{markiert} Zertifikat(e) mit „hervorheben“ — das Feld gibt es nicht "
                        "mehr (alle Kacheln sind gleich gross), es wird uebergangen.")
    sortiert = sorted(eintraege, key=_sortierschluessel, reverse=True)
    if [e["nr"] for e in sortiert] != [e["nr"] for e in eintraege]:
        hinweise.append("Zertifikate nach Datum umsortiert (neueste zuerst): "
                        + " → ".join(e["titel"] for e in sortiert))
    return sortiert, hinweise


def _bildgroesse(wert):
    """(absoluter Pfad, (breite_px, hoehe_px)) oder (None, None)."""
    if not wert:
        return None, None
    p = Path(str(wert)).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        return None, None
    from PIL import Image
    with Image.open(p) as bild:
        return str(p), bild.size


def _einpassen(format_, flaeche_b, flaeche_h):
    """Groesste Flaeche mit dem Seitenverhaeltnis format_ (b/h), die in die
    Flaeche passt. Nie beschnitten, nie verzerrt."""
    s = min(flaeche_b / format_, flaeche_h)
    return round(format_ * s, 2), round(s, 2)


# --- Geometrie --------------------------------------------------------------

def geometrie(ds):
    """Alle Masse der Kacheln in pt, aus tokens.json."""
    K = ds["komponenten"]
    T, B = K["zertkachel"], K["zertbuehne"]

    def m(ref):
        return design_system.aufloesen(ds, ref)

    def lh(verwendung):
        return design_system.zeilenhoehe(ds, verwendung)

    rahmen, pad, bp = T["rahmen"]["breite"], m(T["padding"]), m(B["padding"])
    innen = T["breite"] - 2 * rahmen - 2 * pad
    g = {"grenze": K["zertifikate"]["max-hoehe"],
         "kopf": lh("sektion-titel") + m(K["zertifikate"]["titel-abstand"]),
         "platz_format": K["zertbild"]["platz-format"],
         "spalten": T["spalten"], "eintraege": T["eintraege"],
         "zeilenabstand": m(T["zeilenabstand"]), "spaltenabstand": m(T["spaltenabstand"]),
         "breite": T["breite"], "titel_zeilen": T["titel-zeilen"], "text_zeilen": T["text-zeilen"],
         "text_abstand": m(T["text-abstand"]), "text_breite": innen,
         "buehne": (innen, T["buehne-hoehe"]),
         "platz": (innen - 2 * bp, T["buehne-hoehe"] - 2 * bp)}
    # Textfeld fest: hoechste erlaubte Kombination aus Titel- und Metazeilen.
    g["text_hoehe"] = max(n * lh("karte-titel") + g["text_abstand"]
                          + (T["text-zeilen"] - n) * lh("zert-aussteller")
                          for n in range(1, T["titel-zeilen"] + 1))
    g["zeile"] = (2 * rahmen + 2 * pad + T["buehne-hoehe"] + m(T["abstand"])
                  + g["text_hoehe"])
    # Qualifikationskarte und ihre Tags.
    Q, QT, QG = K["qualikarte"], K["qualitag"], K["qualitags"]
    q_rand = Q["rahmen"]["breite"] + m(Q["padding"])
    g["karte"] = {
        "abstand": m(K["zertifikate"]["titel-abstand"]),     # Karte -> Kacheln
        "innen": K["seite"]["inhalt"] - 2 * q_rand, "rand": q_rand,
        "titel": lh("quali-titel"), "titel_abstand": m(Q["abstand"]),
        "text_zeile": lh("quali-text"), "text_zeilen": Q["text-zeilen"],
        "gruppen_abstand": m(Q["gruppen-abstand"]),
        "tag_abstand": m(QG["abstand"]), "tags_min": QG["min-anzahl"], "tags_max": QG["max-anzahl"],
        "tag_rand": QT["rahmen"]["breite"] + m(QT["padding-x"]),
        "tag_hoehe": 2 * (QT["rahmen"]["breite"] + m(QT["padding-y"])) + lh("quali-tag")}
    return g


def _hoehe(g, anzahl, karte=None):
    """Sektion von der Ueberschrift bis zur letzten Kachelreihe, mit Karte."""
    if not anzahl:
        return 0
    reihen = math.ceil(anzahl / g["spalten"])
    oben = g["kopf"] + (karte["hoehe"] + g["karte"]["abstand"] if karte else 0)
    return oben + reihen * g["zeile"] + (reihen - 1) * g["zeilenabstand"]


def tag_reihen(breiten, innen, abstand):
    """Zeilen der Tag-Reihe. Gerechnet wie im PDF: jedes Tag traegt seinen
    Abstand rechts mit (flex-wrap mit margin). Figma bricht nach dem Abstand
    zwischen den Tags um und kommt deshalb hoechstens auf so viele Zeilen."""
    reihen, x = (1 if breiten else 0), 0.0
    for b in breiten:
        if x and x + b + abstand > innen:
            reihen, x = reihen + 1, 0.0
        x += b + abstand
    return reihen


def karte_planen(daten, g, schaetzer, hinweise):
    """Die Karte "Erworbene Qualifikationen": Satz, Tags, Hoehe. None ohne
    "qualifikationen" in der JSON."""
    q = daten.get("qualifikationen")
    if not q:
        return None
    if not isinstance(q, dict):
        hinweise.append("„qualifikationen“ muss ein Objekt sein: {\"text\": \"…\", \"tags\": […]} "
                        "— die Karte entfaellt.")
        return None
    k = g["karte"]
    text = " ".join(str(q.get("text") or "").split())
    tags = [" ".join(str(t).split()) for t in q.get("tags") or [] if str(t).strip()]
    if not text and not tags:
        hinweise.append("„qualifikationen“ ohne Text und Tags — die Karte entfaellt.")
        return None
    if not text:
        hinweise.append("Qualifikationskarte ohne Satz — es stehen nur die Tags darin.")
    zeilen = schaetzer.zeilen([(text, "quali-text")], k["innen"]) if text else 0
    if zeilen > k["text_zeilen"]:
        hinweise.append(f"Qualifikationskarte: Der Satz braucht {zeilen} Zeilen, erlaubt sind "
                        f"{k['text_zeilen']}. Die Karte wird nicht gekuerzt — den Satz kuerzer "
                        "fassen.")
    if not k["tags_min"] <= len(tags) <= k["tags_max"]:
        hinweise.append(f"Qualifikationskarte: {len(tags)} Tags — vorgesehen sind "
                        f"{k['tags_min']} bis {k['tags_max']}, jedes von einem Zertifikat belegt.")
    doppelt = sorted({t for t in tags if [x.lower() for x in tags].count(t.lower()) > 1})
    if doppelt:
        hinweise.append("Qualifikationskarte: Tag doppelt — " + ", ".join(doppelt))
    breiten = [schaetzer.breite(t, "quali-tag") + 2 * k["tag_rand"] for t in tags]
    reihen = tag_reihen(breiten, k["innen"], k["tag_abstand"])
    block = zeilen * k["text_zeile"] + reihen * (k["tag_abstand"] + k["tag_hoehe"])
    if zeilen and reihen:
        block += k["gruppen_abstand"]
    hoehe = 2 * k["rand"] + k["titel"] + k["titel_abstand"] + block
    return {"text": text, "tags": tags, "text_zeilen": zeilen, "tag_reihen": reihen,
            "hoehe": round(hoehe, 2)}


# --- Buendeln ---------------------------------------------------------------

def _anzeige(eintraege, gebuendelt, labels):
    """Kacheln fuer die Ausgabe: einzelne und je Aussteller ein Buendel, das
    an der Stelle seines neuesten Mitglieds steht."""
    aus, gesetzt = [], set()
    for e in eintraege:
        a = e["aussteller"]
        if e["nr"] in gebuendelt.get(a, ()):
            if a in gesetzt:
                continue
            gesetzt.add(a)
            mitglieder = [x for x in eintraege if x["nr"] in gebuendelt[a]]
            jahre = sorted({datum_lesen(x["datum"])[0] for x in mitglieder} - {None})
            spanne = (f"{jahre[0]}–{jahre[-1]}" if len(jahre) > 1 else str(jahre[0])) if jahre else ""
            aus.append({
                "art": "buendel", "aussteller": a, "anzahl": len(mitglieder),
                # Im Buendeltitel die Kurzform: "IxDF – Interaction Design
                # Foundation" -> "+ 2 weitere Kurse von IxDF".
                "titel": labels["buendel"].format(n=len(mitglieder),
                                                  aussteller=a.split(" – ")[0].strip()),
                "meta": " · ".join(t for t in (spanne, ", ".join(x["titel"] for x in mitglieder)) if t),
                "mitglieder": [x["titel"] for x in mitglieder], "_eintraege": mitglieder,
                "bild": None})
        else:
            jahr = _jahr_text(e["datum"])
            aus.append({
                "art": "zertifikat", "aussteller": a, "titel": e["titel"], "_jahr": jahr,
                "meta": " · ".join(t for t in (a, jahr) if t), "bild": e["bild"],
                "_eintraege": [e]})
    return aus


def _sammeln(anzeige, platz, labels):
    """Zweite Stufe, wenn das Buendeln je Aussteller nicht reicht: Die ersten
    platz - 1 Kacheln bleiben, alle aelteren kommen in eine Sammelkachel."""
    rest = [x for e in anzeige[platz - 1:] for x in e["_eintraege"]]
    jahre = sorted({datum_lesen(x["datum"])[0] for x in rest} - {None})
    spanne = (f"{jahre[0]}–{jahre[-1]}" if len(jahre) > 1 else str(jahre[0])) if jahre else ""
    return anzeige[:platz - 1] + [{
        "art": "buendel", "aussteller": "", "anzahl": len(rest),
        "titel": labels["sammel"].format(n=len(rest)),
        "meta": " · ".join(t for t in (spanne, ", ".join(x["titel"] for x in rest)) if t),
        "mitglieder": [f"{x['titel']} ({x['aussteller'].split(' – ')[0].strip()})" for x in rest],
        "_eintraege": rest, "bild": None, "sammel": True}]


def _passt_text(g, e, meta, schaetzer):
    """Passt "Aussteller · Jahr" in die Zeilen, die der Titel uebrig laesst?"""
    titel = min(schaetzer.zeilen([(e["titel"], "karte-titel")], g["text_breite"]),
                g["titel_zeilen"])
    return schaetzer.zeilen([(meta, "zert-aussteller")], g["text_breite"]) <= g["text_zeilen"] - titel


def _meta_einpassen(g, e, schaetzer):
    """Ist "Aussteller · Jahr" zu lang, wird der Aussteller gekuerzt, nie das
    Jahr: zuerst auf die Kurzform vor dem Gedankenstrich ("UXQB – International
    …" -> "UXQB"), sonst wortweise mit Auslassungszeichen."""
    if e["art"] != "zertifikat" or _passt_text(g, e, e["meta"], schaetzer):
        return e
    a, jahr = e["aussteller"], e["_jahr"]
    kandidaten = [a.split(" – ")[0].strip()] if " – " in a else []
    woerter = a.split()
    kandidaten += [" ".join(woerter[:n]).rstrip(" –-·,:;") + "…"
                   for n in range(len(woerter) - 1, 0, -1)]
    for kurz in kandidaten:
        meta = " · ".join(t for t in (kurz, jahr) if t)
        if _passt_text(g, e, meta, schaetzer):
            e["meta_lang"], e["meta"] = e["meta"], meta
            break
    return e


def _buendeln(eintraege, passt):
    """Buendelt Schritt fuer Schritt die aeltesten Eintraege des Ausstellers mit
    den meisten Einzeleintraegen, bis passt(gebuendelt) wahr ist. Jeder Schritt
    spart eine Kachel. Gibt (gebuendelt, passt) zurueck."""
    gebuendelt = {}
    while not passt(gebuendelt):
        beste, bester_schluessel = None, None
        for a in dict.fromkeys(e["aussteller"] for e in eintraege):
            if not a:
                continue
            eigene = [e for e in eintraege if e["aussteller"] == a]
            # Der neueste Eintrag eines Ausstellers bleibt sichtbar.
            frei = [e for e in eigene[1:] if e["nr"] not in gebuendelt.get(a, ())]
            noetig = 1 if gebuendelt.get(a) else 2
            if len(frei) < noetig:
                continue
            einzeln = len([e for e in eigene if e["nr"] not in gebuendelt.get(a, ())])
            aeltester = _sortierschluessel(frei[-1])
            schluessel = (einzeln, tuple(-x for x in aeltester))
            if bester_schluessel is None or schluessel > bester_schluessel:
                beste, bester_schluessel = (a, frei[-noetig:]), schluessel
        if not beste:
            return gebuendelt, False
        a, neu = beste
        gebuendelt.setdefault(a, set()).update(e["nr"] for e in neu)
    return gebuendelt, True


# --- Plan -------------------------------------------------------------------

def planen(daten, ds, labels):
    """(plan, hinweise). plan ist None ohne Zertifikate. labels braucht
    "buendel" ("+ {n} weitere Kurse von {aussteller}") und "sammel"
    ("+ {n} weitere Zertifikate")."""
    eintraege, hinweise = einlesen(daten)
    if not eintraege:
        if daten.get("qualifikationen"):
            hinweise.append("„qualifikationen“ ohne Zertifikate — die Karte entfaellt mit der "
                            "Zertifikatssektion; ihre Tags muessen von Zertifikaten kommen.")
        return None, hinweise
    g = geometrie(ds)
    schaetzer = Schaetzer(ds)
    karte = karte_planen(daten, g, schaetzer, hinweise)

    def anzeige_von(gebuendelt):
        return [_meta_einpassen(g, e, schaetzer) for e in _anzeige(eintraege, gebuendelt, labels)]

    def passt(gebuendelt):
        anzahl = len(anzeige_von(gebuendelt))
        return anzahl <= g["eintraege"] and _hoehe(g, anzahl, karte) <= g["grenze"]

    gebuendelt, ok = _buendeln(eintraege, passt)
    anzeige = anzeige_von(gebuendelt)
    if not ok:
        platz = max([n for n in range(1, g["eintraege"] + 1)
                     if _hoehe(g, n, karte) <= g["grenze"]] or [1])
        if 1 < platz < len(anzeige):
            anzeige, ok = _sammeln(anzeige, platz, labels), True
    hoehe = round(_hoehe(g, len(anzeige), karte), 2)

    abgleich = " und die Tags der Qualifikationskarte abgleichen." if karte else "."
    for b in (e for e in anzeige if e["art"] == "buendel"):
        if b.get("sammel"):
            hinweise.append(
                f"Sammelkachel: Das Buendeln je Aussteller reicht nicht (zu viele Aussteller), "
                f"deshalb stehen die {b['anzahl']} aeltesten Zertifikate als „{b['titel']}“ — "
                + ", ".join(b["mitglieder"]) + ". In der Uebergabe nennen" + abgleich)
        else:
            hinweise.append(
                f"Gebuendelt: {b['anzahl']} Zertifikate von {b['aussteller']} stehen als "
                f"„{b['titel']}“ — " + ", ".join(b["mitglieder"]) + ". In der Uebergabe nennen"
                + abgleich)
    if not ok:
        hinweise.append(
            f"Zertifikatssektion {hoehe:g}pt hoch ({len(anzeige)} Kacheln) — "
            f"{hoehe - g['grenze']:g}pt ueber der Grenze von {g['grenze']}, und es laesst sich "
            "nichts mehr buendeln. Eintraege mit dem Nutzer streichen.")

    _ausgestalten(g, anzeige, schaetzer, hinweise)
    return {"grenze": g["grenze"], "hoehe": hoehe, "eintraege": anzeige, "karte": karte,
            "geometrie": g}, hinweise


def _ausgestalten(g, anzeige, schaetzer, hinweise):
    """Bildgroessen, Zeilenbegrenzung und Kuerzungshinweise je Kachel."""
    for nr, e in enumerate(anzeige, start=1):
        e["nr"] = nr
        if e.get("meta_lang"):
            hinweise.append(f"Zertifikat „{e['titel']}“: gezeigt wird „{e['meta']}“ statt "
                            f"„{e['meta_lang']}“, damit das Jahr stehen bleibt.")
        t = schaetzer.zeilen([(e["titel"], "karte-titel")], g["text_breite"])
        e["titel_max"] = g["titel_zeilen"]
        e["meta_max"] = g["text_zeilen"] - min(t, g["titel_zeilen"])
        if t > g["titel_zeilen"]:
            hinweise.append(f"Zertifikat „{e['titel']}“: Titel braucht {t} Zeilen, gezeigt werden "
                            f"{g['titel_zeilen']} — kuerzer fassen.")
        mz = schaetzer.zeilen([(e["meta"], "zert-aussteller")], g["text_breite"])
        if mz > e["meta_max"] and e["art"] != "buendel":
            hinweise.append(f"Zertifikat „{e['titel']}“: „{e['meta']}“ wird nach {e['meta_max']} "
                            "Zeile(n) gekuerzt — den Aussteller kuerzer fassen, etwa mit seiner "
                            "Abkuerzung.")
        pfad, px = _bildgroesse(e.get("bild"))
        if e.get("bild") and not pfad:
            hinweise.append(f"Zertifikatsbild nicht gefunden: {e['bild']} — an seiner Stelle "
                            "steht das Platzhalterfeld.")
        e["bild"] = pfad
        format_ = (px[0] / px[1]) if px else g["platz_format"]
        e["breite"], e["hoehe"] = _einpassen(format_, *g["platz"])
        if px and e["hoehe"] < 0.6 * g["platz"][1] and e["breite"] < 0.6 * g["platz"][0]:
            hinweise.append(f"Zertifikatsbild {Path(pfad).name}: ungewoehnliches Format "
                            f"({px[0]}x{px[1]}), wirkt eingepasst klein.")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    daten = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    from render_skillmatrix import BESCHRIFTUNG
    labels = BESCHRIFTUNG.get(daten.get("sprache", "de"), BESCHRIFTUNG["de"])
    plan, hinweise = planen(daten, design_system.laden(), labels)
    if not plan:
        print("Keine Zertifikate — die Sektion entfaellt.")
    else:
        if plan["karte"]:
            k = plan["karte"]
            print(f"Karte „{labels['qualifikationen']}“: {k['hoehe']:g}pt, Satz {k['text_zeilen']} "
                  f"Zeile(n), {len(k['tags'])} Tags in {k['tag_reihen']} Zeile(n)")
        print(f"Kacheln: {len(plan['eintraege'])}, Sektion {plan['hoehe']:g}pt hoch "
              f"(Grenze {plan['grenze']})")
        for e in plan["eintraege"]:
            print(f"  {'+' if e['art'] == 'buendel' else '-'}  {e['titel']} — {e['meta']}")
    for h in hinweise:
        print(f"  Hinweis: {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
