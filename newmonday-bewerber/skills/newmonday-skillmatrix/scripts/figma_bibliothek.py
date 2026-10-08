#!/usr/bin/env python3
"""Der Bibliotheksweg: beide Figma-Fassungen aus Instanzen der Master-Bibliothek.

Wird von figma_plan.py aufgerufen, nicht direkt. Baut je Fassung einen
Befuellungsplan - welche Komponente als Instanz entsteht und welche
Component-Properties, exponierten Instanzen, Bildebenen und Bildfeld-Paddings
darin gesetzt werden - und daraus das fertige use_figma-Skript
(assets/figma-bibliothek.js mit dem Plan davor).

Die Komponenten, ihre Keys und Property-Namen stehen in
assets/master-bibliothek.json. Jeder Property-Name wird dort nachgeschlagen;
fehlt einer, bricht der Plan ab, statt still nichts zu setzen.

Gesetzt werden nur Inhalte: Texte, Booleans, Varianten, Bilder und die
Paddings des Bildfelds der Zertifikatskacheln (so bekommt das Bild das
Seitenverhaeltnis der Datei - Breiten von Instanzen lassen sich nicht
ueberschreiben). Farben, Schriften, Abstaende kommen aus der Bibliothek.
"""
import json
from pathlib import Path

import design_system

KATALOG = design_system.ASSETS / "master-bibliothek.json"
SKRIPT = design_system.ASSETS / "figma-bibliothek.js"

LANG, A4 = "Skillmatrix lang/", "Skillmatrix A4/"


def katalog():
    return json.loads(KATALOG.read_text(encoding="utf-8"))


class Bib:
    """Nachschlagen von Komponenten und Property-Namen im Katalog."""

    def __init__(self):
        self.k = katalog()
        self.komp = self.k["komponenten"]
        self.grenzen = self.k["grenzen"]

    def p(self, komponente, name):
        """Voller Property-Name (mit #-Suffix) zu einem Kurznamen."""
        eig = self.komp[komponente]["eigenschaften"]
        for schluessel in eig:
            if schluessel.split("#")[0] == name:
                return schluessel
        raise SystemExit(f"master-bibliothek.json: „{komponente}“ hat keine Eigenschaft „{name}“ "
                         "- Katalog neu auslesen (references/figma.md).")

    def props(self, komponente, **werte):
        """Kurznamen -> volle Namen. Unterstriche im Kurznamen stehen fuer
        Leerzeichen (Tag_4 -> "Tag 4")."""
        return {self.p(komponente, k.replace("_", " ")): v for k, v in werte.items()}

    def slots(self, komponente, praefix, anzahl, erster=None):
        """Booleans "Kachel 5" … "Kachel 12": an, solange belegt."""
        aus = {}
        for schluessel, d in self.komp[komponente]["eigenschaften"].items():
            name = schluessel.split("#")[0]
            if d["typ"] == "BOOLEAN" and name.startswith(praefix + " ") \
                    and name[len(praefix) + 1:].isdigit():
                aus[schluessel] = int(name[len(praefix) + 1:]) <= anzahl
        return aus

    def key(self, komponente):
        return self.komp[komponente]["key"]


def knoten(name, props=None, kinder=None, **rest):
    k = {"name": name}
    if props:
        k["props"] = props
    if kinder:
        k["kinder"] = [x for x in kinder if x]
    k.update({s: v for s, v in rest.items() if v is not None})
    return k


def aus(name):
    """Eine exponierte Instanz ohne eigenen Boolean ausblenden (Slots 1-3 der
    Kategorie, 1-4 der Kacheln, Tag 1-3): Sichtbarkeit ist ein Inhalt, kein Wert."""
    return {"name": name, "sichtbar": False}


def _bild(ebene, datei, skalierung):
    """Bildebene mit absolutem Pfad - derselbe Schluessel wie in bilder.json."""
    if not datei:
        return None
    p = Path(str(datei)).expanduser()
    p = p if p.is_absolute() else Path.cwd() / p
    return {"ebene": ebene, "datei": str(p.resolve()), "skalierung": skalierung}


def _padding(buehne, bild):
    """Bildfeld-Padding, damit das Bild mit dem Seitenverhaeltnis der Datei in
    der Buehne steht (oben, rechts, unten, links)."""
    w, h = buehne
    bw, bh = bild
    py, px = round((h - bh) / 2, 2), round((w - bw) / 2, 2)
    return [py, px, py, px]


def _bewertung(s, hinweise, wo):
    p = s.get("punkte")
    if not isinstance(p, int) or not 1 <= p <= 5:
        hinweise.append(f"{wo}: „{s.get('name')}“ hat keine Bewertung 1–5 ({p!r}) — 1 gesetzt.")
        p = 1
    return str(p)


def _ueber(hinweise, was, anzahl, grenze, fassung):
    if anzahl > grenze:
        hinweise.append(f"{fassung}: {anzahl} {was} — die Komponente traegt hoechstens {grenze}. "
                        "Diese Fassung aus dem rohen Plan bauen oder kuerzen.")
        return True
    return False


# --- lang -------------------------------------------------------------------

def plan_lang(daten, labels, zplan, kontakt, hinweise):
    b = Bib()
    G = b.grenzen["lang"]
    person = daten.get("person") or {}
    name = " ".join(str(person.get("name") or "Skillmatrix").split())
    zu_viel = False
    T, TB, TAG = LANG + "Textbausteine", LANG + "Badge", LANG + "Tag"
    KK, KAT = LANG + "Kompetenzkarte", LANG + "Kategorie"

    # Hero
    sp = list(person.get("schwerpunkte") or [])
    zu_viel |= _ueber(hinweise, "Schwerpunkte", len(sp), G["schwerpunkte"], "lang")
    sp = sp[:G["schwerpunkte"]]
    foto = person.get("foto")
    if not foto:
        hinweise.append("lang: Kein Foto — die Fotokarte zeigt nur den Verlauf.")
    hero = knoten("Hero", kinder=[
        knoten("Verfügbarkeit", b.props(TB, Text=f"{labels['verfuegbar']} "
                                        f"{person.get('verfuegbar_ab', '')}".strip())),
        knoten("Name", b.props(T, Text=name)),
        knoten("Rolle", b.props(T, Text=str(person.get("rolle") or ""))),
        knoten("Beschreibung", b.props(T, Text=str(person.get("beschreibung") or ""))),
        (knoten("Schwerpunkte", b.slots(LANG + "Schwerpunkte", "Tag", len(sp)),
                [knoten(f"Tag {i}", b.props(TAG, Text=s)) for i, s in enumerate(sp, 1)])
         if sp else aus("Schwerpunkte")),
        knoten("Fotokarte", b.props(LANG + "Fotokarte", Name=name,
                                    Erfahrung=str(person.get("erfahrung") or "")),
               bild=_bild("Foto", foto, "FILL"), ausblenden=None if foto else ["Foto"]),
    ], k=LANG + "Hero")

    # Zertifikate
    zert = aus("Zertifikate")
    if zplan:
        ein = zplan["eintraege"]
        zu_viel |= _ueber(hinweise, "Zertifikatskacheln", len(ein), G["kacheln"], "lang")
        ein = ein[:G["kacheln"]]
        g = zplan["geometrie"]
        kacheln = []
        for i, e in enumerate(ein, 1):
            props = b.props(LANG + "Zertifikat-Kachel", Titel=e["titel"], Aussteller=e["meta"] or "")
            if e.get("bild"):
                kacheln.append(knoten(f"Kachel {i}", props, bild=_bild("Bild", e["bild"], "FIT"),
                                      padding={"ebene": "Buehne",
                                               "werte": _padding(g["buehne"], (e["breite"], e["hoehe"]))}))
            else:
                kacheln.append(knoten(f"Kachel {i}", props, ausblenden=["Bild"]))
                hinweise.append(f"lang: Kachel „{e['titel']}“ ohne Bild — die lange Kachel hat "
                                "keine Platzhalter-/Buendel-Variante, die Buehne bleibt leer"
                                + (f" (das „+{e['anzahl']}“ fehlt)" if e["art"] == "buendel" else "")
                                + ". Im Master nachziehen.")
        kacheln += [aus(f"Kachel {i}") for i in range(len(ein) + 1, 5)]
        karte = zplan.get("karte")
        if karte:
            tags = list(karte.get("tags") or [])
            zu_viel |= _ueber(hinweise, "Tags der Qualifikationskarte", len(tags),
                              G["qualifikations_tags"], "lang")
            tags = tags[:G["qualifikations_tags"]]
            QK = LANG + "Qualifikationskarte"
            erkl = knoten("Erklärung", {**b.props(QK, Titel=labels["qualifikationen"],
                                                  Beschreibung=karte.get("text") or ""),
                                        **b.slots(QK, "Tag", len(tags))},
                          [knoten(f"Tag {i}", b.props(TAG, Text=t)) for i, t in enumerate(tags, 1)]
                          + [aus(f"Tag {i}") for i in range(len(tags) + 1, 4)])
        else:
            erkl = aus("Erklärung")
        zert = knoten("Zertifikate", b.slots(LANG + "Zertifikate", "Kachel", len(ein)),
                      [knoten("Ueberschrift", b.props(T, Text=labels["zertifikate"])), erkl] + kacheln,
                      k=LANG + "Zertifikate")

    def karten(skills, wo):
        aus_ = []
        for j, s in enumerate(skills, 1):
            aus_.append(knoten(f"Karte {j}", b.props(KK, Titel=str(s.get("name") or ""),
                                                      Beschreibung=str(s.get("beschreibung") or "")),
                               [knoten("Bewertung", {"Bewertung": _bewertung(s, hinweise, wo)})]))
        return aus_ + [aus(f"Karte {j}") for j in range(len(skills) + 1, 4)]

    # Kernkompetenzen
    kats = list(daten.get("kompetenzen") or [])
    kern = aus("Kernkompetenzen")
    if kats:
        zu_viel |= _ueber(hinweise, "Kategorien", len(kats), G["kategorien"], "lang")
        kats = kats[:G["kategorien"]]
        kinder = [knoten("Ueberschrift", b.props(T, Text=labels["kernkompetenzen"]))]
        for i, k in enumerate(kats, 1):
            skills = list(k.get("skills") or [])
            zu_viel |= _ueber(hinweise, f"Karten in „{k.get('kategorie')}“", len(skills),
                              G["karten_je_kategorie"], "lang")
            skills = skills[:G["karten_je_kategorie"]]
            kinder.append(knoten(f"Kategorie {i}",
                                 {b.p(KAT, "Label anzeigen"): True, **b.slots(KAT, "Karte", len(skills))},
                                 [knoten("Kategorie", b.props(T, Text=str(k.get("kategorie") or "")))]
                                 + karten(skills, "lang")))
        kern = knoten("Kernkompetenzen", b.slots(LANG + "Kernkompetenzen", "Kategorie", len(kats)),
                      kinder, k=LANG + "Kernkompetenzen")

    # Tools
    tools = list(daten.get("tools") or [])
    werkzeuge = aus("Tools")
    if tools:
        zu_viel |= _ueber(hinweise, "Tools", len(tools), G["tools"], "lang")
        tools = tools[:G["tools"]]
        werkzeuge = knoten("Tools", None, [
            knoten("Ueberschrift", b.props(T, Text=labels["tools"])),
            knoten("Karten", {b.p(KAT, "Label anzeigen"): False, **b.slots(KAT, "Karte", len(tools))},
                   karten(tools, "lang Tools"))], k=LANG + "Tools")

    ende = daten.get("zertifikate_position") == "ende"
    if ende:
        # Die Rumpf-Komponente hat die Zertifikate fest vorn. Fuer die
        # Florian-Variante ein Rahmen mit den drei Sektions-Instanzen.
        hinweise.append("lang: Zertifikate am Ende — die Rumpf-Komponente kennt das nicht; der Rumpf "
                        "ist ein Rahmen mit den drei Sektions-Instanzen (Werte aus tokens.json).")
        rumpf = knoten("Rumpf", rahmen="rumpf",
                       kinder=[x for x in (kern, werkzeuge, zert) if x.get("k")])
    else:
        rumpf = knoten("Rumpf", None, [{k: v for k, v in x.items() if k != "k"}
                                       for x in (zert, kern, werkzeuge)], k=LANG + "Rumpf")

    # Fuss: Name, Funktion, Mail, Telefon sind Properties; Adresse, Labels und
    # Frage stehen fest in der Komponente.
    fuss = knoten("Fuß", b.props(LANG + "Fuß", Ansprechpartner=kontakt["name"], Funktion=kontakt["rolle"],
                                 **{"E-Mail": kontakt["mail"]}, Telefon=kontakt["telefon"]),
                  k=LANG + "Fuß")
    from render_skillmatrix import KONTAKT_VORGABE
    if any(kontakt[s] != KONTAKT_VORGABE[s] for s in ("firma", "strasse", "ort")):
        hinweise.append("lang: Die Adresse im Fuss steht fest in der Komponente — abweichende "
                        "Adresse aus der JSON nicht gesetzt.")
    if daten.get("sprache", "de") != "de":
        hinweise.append("lang: Frage und Labels im Fuss stehen deutsch in der Komponente — fuer eine "
                        "englische Matrix im Master Properties ergaenzen oder roh bauen.")

    oben = [knoten("Kopfzeile", k=LANG + "Kopfzeile"), hero, rumpf, fuss]
    return {"fassung": "lang", "name": f"Skillmatrix — {name}", "breite": b.komp[LANG + "Kopfzeile"]["groesse"][0],
            "zu_viel": zu_viel, "instanzen": oben}


# --- A4 ---------------------------------------------------------------------

def plan_a4(daten, labels, za4, kontakt, foto, bloecke, seiten, hinweise):
    b = Bib()
    G = b.grenzen["a4"]
    person = daten.get("person") or {}
    name = " ".join(str(person.get("name") or "Skillmatrix").split())
    zu_viel = False
    S, TAG, AT = A4 + "Seite", "A4/Tag", "A4/Abschnittstitel"
    KAT, KOMP, KS = A4 + "Kategorie", A4 + "Kompetenz", "A4/Kontaktspalte"
    ende = daten.get("zertifikate_position") == "ende"

    def auf(nr):
        return {bl for bl, s in bloecke.items() if s == nr}

    def zeilen(skills, wo):
        kinder = []
        for j, s in enumerate(skills, 1):
            kinder.append(knoten(f"Kompetenz {j}", b.props(
                KOMP, Titel=str(s.get("name") or ""), Beschreibung=str(s.get("beschreibung") or ""),
                Trennlinie_oben_anzeigen=j > 2),
                [knoten("Bewertung", {"Bewertung": _bewertung(s, hinweise, wo)})]))
        return kinder

    sp = list(person.get("schwerpunkte") or [])
    zu_viel |= _ueber(hinweise, "Schwerpunkte", len(sp), G["schwerpunkte"], "A4")
    sp = sp[:G["schwerpunkte"]]
    ein = (za4 or {}).get("eintraege") or []
    zu_viel |= _ueber(hinweise, "Zertifikatskacheln", len(ein), G["kacheln"], "A4")
    tools = list(daten.get("tools") or [])
    zu_viel |= _ueber(hinweise, "Tools", len(tools), G["tools"], "A4")
    kats = list(daten.get("kompetenzen") or [])
    T4 = design_system.fassung(design_system.laden(), "a4")["komponenten"]["zertkachel"]
    spalten, buehne = T4["spalten"], (T4["breite"], T4["buehne-hoehe"])   # wie im PDF

    seiten_plan = []
    for nr in range(1, seiten + 1):
        bl, letzte = auf(nr), nr == seiten
        kinder = [knoten("Kopfzeile", b.props("A4/Kopfzeile", Badge_anzeigen=nr == 1),
                         [knoten("Verfügbarkeit", b.props("A4/Badge", Text=f"{labels['verfuegbar']} "
                                                          f"{person.get('verfuegbar_ab', '')}".strip()))]
                         if nr == 1 else None)]
        hat = {"hero": "hero" in bl, "zert": any(x.startswith("zert-") for x in bl) and bool(za4),
               "kern": any(x.startswith("kategorie-") for x in bl), "tools": "tools" in bl and bool(tools)}
        if hat["hero"]:
            H = A4 + "Hero"
            kinder.append(knoten("Hero", {**b.props(H, Name=name, Rolle=str(person.get("rolle") or ""),
                                                    Beschreibung=str(person.get("beschreibung") or ""),
                                                    Schwerpunkte_anzeigen=bool(sp)),
                                          **b.slots(H, "Schwerpunkt", len(sp))},
                                 [knoten(f"Schwerpunkt {i}", b.props(TAG, Text=s)) for i, s in enumerate(sp, 1)]
                                 + [knoten("Fotokarte", b.props(A4 + "Fotokarte", Foto_anzeigen=bool(foto)),
                                           bild=_bild("Foto", foto, "FILL"))]))
        if hat["zert"]:
            Z, QK, ZK = A4 + "Zertifikate", A4 + "Qualifikationskarte", A4 + "Zertifikat-Kachel"
            reihen = sorted(int(x.rsplit("-", 1)[1]) for x in bl if x.startswith("zert-zeile-"))
            hier = [e for r in reihen for e in ein[(r - 1) * spalten:r * spalten]][:G["kacheln"]]
            karte = za4.get("karte") if "zert-karte" in bl else None
            # Ausgeblendete Bloecke (Boolean aus) sind aus dem Baum - nur
            # befuellen, was auf dieser Seite steht.
            zk = ([knoten("Überschrift", b.props(AT, Titel=labels["zertifikate"]))]
                  if "zert-titel" in bl else [])
            if karte:
                tags = list(karte.get("tags") or [])
                zu_viel |= _ueber(hinweise, "Tags der Qualifikationskarte", len(tags),
                                  G["qualifikations_tags"], "A4")
                tags = tags[:G["qualifikations_tags"]]
                zk.append(knoten("Qualifikationskarte", {
                    **b.props(QK, Titel=labels["qualifikationen"], Satz=karte.get("text") or "",
                              Satz_anzeigen=bool(karte.get("text")), Tags_anzeigen=bool(tags)),
                    **b.slots(QK, "Tag", len(tags))},
                    [knoten(f"Tag {i}", b.props(TAG, Text=t)) for i, t in enumerate(tags, 1)]))
            for i, e in enumerate(hier, 1):
                art = "Bild" if e.get("bild") else ("Bündel" if e["art"] == "buendel" else "Platzhalter")
                props = {"Art": art, **b.props(ZK, Titel=e["titel"], Aussteller=e.get("meta") or "",
                                               Aussteller_anzeigen=bool(e.get("meta")))}
                if art == "Bündel":
                    props[b.p(ZK, "Anzahl")] = f"+{e['anzahl']}"
                zk.append(knoten(f"Kachel {i}", props, bild=_bild("Bild", e.get("bild"), "FIT"),
                                 padding={"ebene": "Bühne", "werte": _padding(
                                     buehne, (e["a4_breite"], e["a4_hoehe"]))} if art == "Bild" else None))
            kinder.append(knoten("Zertifikate (Ende)" if ende else "Zertifikate", {
                **b.props(Z, Überschrift_anzeigen="zert-titel" in bl,
                          Qualifikationskarte_anzeigen=bool(karte), Kacheln_anzeigen=bool(hier)),
                **b.slots(Z, "Kachel", len(hier))}, zk))
        if hat["kern"]:
            nrn = sorted(int(x.rsplit("-", 1)[1]) for x in bl if x.startswith("kategorie-"))
            if _ueber(hinweise, f"Kategorien auf Seite {nr}", len(nrn), G["kategorien_je_seite"], "A4"):
                zu_viel, nrn = True, nrn[:G["kategorien_je_seite"]]
            kk = ([knoten("Überschrift", b.props(AT, Titel=labels["kernkompetenzen"]))]
                  if "kompetenzen-titel" in bl else [])
            for i, knr in enumerate(nrn, 1):
                k = kats[knr - 1]
                skills = list(k.get("skills") or [])
                zu_viel |= _ueber(hinweise, f"Kompetenzen in „{k.get('kategorie')}“", len(skills),
                                  G["kompetenzen_je_kategorie"], "A4")
                skills = skills[:G["kompetenzen_je_kategorie"]]
                kk.append(knoten(f"Kategorie {i}", b.slots(KAT, "Kompetenz", len(skills)),
                                 [knoten("Label", b.props(A4 + "Kategorie-Label",
                                                          Kategorie=str(k.get("kategorie") or ""),
                                                          **{"Label-Text anzeigen": True}))]
                                 + zeilen(skills, "A4")))
            kinder.append(knoten("Kernkompetenzen", {
                **b.props(A4 + "Kernkompetenzen", Überschrift_anzeigen="kompetenzen-titel" in bl),
                **b.slots(A4 + "Kernkompetenzen", "Kategorie", len(nrn))}, kk))
        if hat["tools"]:
            t = tools[:G["tools"]]
            kinder.append(knoten("Tools", b.props(A4 + "Tools", Überschrift_anzeigen=True), [
                knoten("Überschrift", b.props(AT, Titel=labels["tools"])),
                knoten("Einträge", b.slots(KAT, "Kompetenz", len(t)),
                       [knoten("Label", b.props(A4 + "Kategorie-Label", **{"Label-Text anzeigen": False}))]
                       + zeilen(t, "A4 Tools"))]))
        if letzte:
            kinder.append(knoten("Fuß", None, [
                knoten("Ansprechpartner", b.props(KS, Label=labels["ansprechpartner"], Name=kontakt["name"],
                                                  Name_anzeigen=True, Wert_1=kontakt["rolle"],
                                                  Wert_2_anzeigen=False)),
                knoten("Kontakt", b.props(KS, Label=labels["kontakt"], Name_anzeigen=False,
                                          Wert_1=kontakt["mail"], Wert_2=kontakt["telefon"],
                                          Wert_2_anzeigen=True)),
                knoten("Adresse", b.props(KS, Label=labels["adresse"], Name_anzeigen=False,
                                          Wert_1=f"{kontakt['firma']}\n{kontakt['strasse']}\n{kontakt['ort']}",
                                          Wert_2_anzeigen=False))]))
        seite_props = b.props(S, Hero_anzeigen=hat["hero"], Zertifikate_anzeigen=hat["zert"] and not ende,
                              Zertifikate_am_Ende_anzeigen=hat["zert"] and ende,
                              Kernkompetenzen_anzeigen=hat["kern"], Tools_anzeigen=hat["tools"],
                              Fuß_anzeigen=letzte)
        seiten_plan.append(knoten(f"Skillmatrix A4 — {name} — Seite {nr}", seite_props, kinder, k=S))
    return {"fassung": "a4", "name": f"Skillmatrix A4 — {name}", "anker": f"Skillmatrix — {name}",
            "zu_viel": zu_viel, "instanzen": seiten_plan}


# --- Bilder und Skripte -----------------------------------------------------

def bilder(plan):
    """Alle Bilddateien eines Plans, in Bauordnung."""
    gesehen = []

    def lauf(k):
        if k.get("bild") and k["bild"]["datei"] not in gesehen:
            gesehen.append(k["bild"]["datei"])
        for kind in k.get("kinder", []):
            lauf(kind)
    for k in plan["instanzen"]:
        lauf(k)
    return gesehen


def keys(plan):
    return {k["k"]: Bib().key(k["k"]) for k in _alle_oben(plan)}


def _alle_oben(plan):
    for k in plan["instanzen"]:
        if k.get("k"):
            yield k
        for kind in k.get("kinder", []) if k.get("rahmen") else []:
            yield kind


def skript(plan, seite_id, hashes, entfernen, uploads, rumpf_werte=None):
    """Das use_figma-Skript: Konstanten, dann der feste Teil aus
    assets/figma-bibliothek.js. Bilder heissen im Skript b1, b2 … (Reihenfolge
    von uploads), damit der Code kurz bleibt."""
    import copy
    kurz = {d: f"b{i}" for i, d in enumerate(uploads, 1)}
    plan = copy.deepcopy(plan)

    def umbenennen(k):
        if k.get("bild"):
            k["bild"]["datei"] = kurz.get(k["bild"]["datei"], k["bild"]["datei"])
        for kind in k.get("kinder", []):
            umbenennen(kind)
    dateien = bilder(plan)
    for k in plan["instanzen"]:
        umbenennen(k)
    kopf = {
        "SEITE_ID": seite_id,
        "PLAN": {**{k: v for k, v in plan.items() if k != "zu_viel"}, "keys": keys(plan),
                 **({"rumpf": rumpf_werte} if rumpf_werte else {})},
        "BILDER": {kurz[d]: {"hash": hashes[d]["hash"], "datei": Path(d).name}
                   for d in dateien if d in hashes and d in kurz},
        "ENTFERNEN": [hashes[d]["temp"] for d in entfernen if d in hashes and hashes[d].get("temp")],
    }
    zeilen = [f"const {n} = {json.dumps(w, ensure_ascii=False, separators=(',', ':'))};"
              for n, w in kopf.items()]
    return "\n".join(zeilen) + "\n" + SKRIPT.read_text(encoding="utf-8")


def vorflug_skript(seite_id=None):
    b = Bib()
    proben = [b.key(LANG + "Kopfzeile"), b.key(A4 + "Seite")]
    return (f"const SEITE_ID = {json.dumps(seite_id)};\nconst PROBEN = {json.dumps(proben)};\n"
            + VORFLUG)


VORFLUG = r"""const seiten = figma.root.children.map(p => ({ id: p.id, name: p.name }));
const alle = await figma.listAvailableFontsAsync();
const schnitte = fam => alle.filter(f => f.fontName.family === fam).map(f => f.fontName.style);
const bibliothek = [];
for (const key of PROBEN) {
  try { const k = await figma.importComponentByKeyAsync(key); bibliothek.push({ key, ok: true, name: k.name }); }
  catch (e) { bibliothek.push({ key, ok: false, fehler: String(e).slice(0, 200) }); }
}
const ziel = SEITE_ID ? await figma.getNodeByIdAsync(SEITE_ID) : null;
return { editor: figma.editorType, seiten, zielseite: ziel ? ziel.name : null,
         bibliothek_ok: bibliothek.every(b => b.ok), bibliothek,
         inter: schnitte("Inter"), rethink: schnitte("Rethink Sans") };
"""
