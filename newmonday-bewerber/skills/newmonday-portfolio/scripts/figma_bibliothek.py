#!/usr/bin/env python3
"""Der Bibliotheksweg nach Figma: Die Folien entstehen aus Instanzen der
veröffentlichten Master-Bibliothek „Portfolio - CV Master“, nicht als rohe
Frames. Aufgerufen wird das über figma_plan.py (Standard); hier steht, wie aus
dem gerenderten Portfolio der Bauplan für die Instanzen wird.

Warum Instanzen: Eine Änderung im Master erreicht per Bibliotheks-Update jede
Kandidatendatei. Dafür dürfen die Folien nie gelöst werden, und alles
Kandidateneigene geht über die Wege, die der Master dafür vorsieht:
Component-Properties (Texte, Schalter, Varianten), exponierte verschachtelte
Instanzen und Bildfüllungen der Bildebenen.

Woher die Inhalte kommen: aus demselben HTML wie das PDF (render_portfolio.
baue_html) und derselben Layoutrechnung von WeasyPrint. Der Folientyp steht an
der <section> (seite--cover, seite--profil …), die Texte stehen in deren
Elementen - mit allem, was das Renderskript schon geregelt hat (Sprachvorgabe,
„3+“, Rollenzeile, Fettungen). Die Bildflächen (Foto, Logos, Screens) kommen
mit ihrer Lage aus dem Layout: Ein Logo steht in Figma dort, wo es im PDF
steht. Die Zuordnung Seite -> Komponente steht in ZUORDNUNG; die Namen der
Properties stehen in assets/master-bibliothek.json und werden vor dem
Schreiben gegen den Katalog geprüft.

Die Bilder gehen über eine „Bildablage“: upload_assets kann nur Knoten mit
einfacher ID füllen, Ebenen in Instanzen haben zusammengesetzte IDs
(I12:3;45:6). Deshalb legt der Start-Aufruf je Bild ein Trägerrechteck an, die
Bilder werden dorthin hochgeladen, und die Folien-Pakete übernehmen den
imageHash in die Bildebenen der Instanzen. Das letzte Paket räumt die Ablage weg.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import design_tokens as ds
import render_portfolio as rp

KATALOG_DATEI = rp.ASSETS / "master-bibliothek.json"
CODE_GRENZE = 44000
FOLIEN_JE_PAKET = 12


def katalog() -> dict:
    return json.loads(KATALOG_DATEI.read_text(encoding="utf-8"))


# ── DOM lesen ────────────────────────────────────────────────────────────

def _klassen(el) -> list[str]:
    return (el.get("class") or "").split() if el is not None else []


def alle(el, klasse: str | None = None, tag: str | None = None) -> list:
    """Nachfahren (ohne el selbst) mit Klasse und/oder Tag, in Dokumentreihenfolge."""
    raus = []
    for n in el.iter():
        if n is el:
            continue
        if klasse and klasse not in _klassen(n):
            continue
        if tag and _tag(n) != tag:
            continue
        raus.append(n)
    return raus


def eins(el, klasse: str | None = None, tag: str | None = None):
    treffer = alle(el, klasse, tag) if el is not None else []
    return treffer[0] if treffer else None


def _tag(el) -> str:
    t = el.tag if isinstance(el.tag, str) else ""
    return t.rsplit("}", 1)[-1].lower()


def laeufe(el) -> dict | None:
    """Text eines Elements wie im HTML gesetzt: Leerraum zusammengefasst,
    <br> als Umbruch, <b>/<strong> als Fettbereich, <a> als Link. Zurück kommt
    {"s": text, "f": [[von, bis]], "l": [[von, bis, url]]} oder None."""
    if el is None:
        return None
    zeichen: list[tuple[str, bool, str | None, bool]] = []   # (z, fett, link, hart)

    def gehe(n, fett, link):
        t = _tag(n)
        if t == "br":
            zeichen.append(("\n", fett, link, True))
            return
        fett = fett or t in ("b", "strong")
        if t == "a" and n.get("href"):
            link = n.get("href")
        for z in n.text or "":
            zeichen.append((z, fett, link, False))
        for k in n:
            gehe(k, fett, link)
            for z in k.tail or "":            # der Rest hinter einem Kind gehoert zu n
                zeichen.append((z, fett, link, False))

    gehe(el, False, None)

    text, fett, link = [], [], []
    for z, f, l, hart in zeichen:
        if not hart and z in " \t\r\n":
            if not text or text[-1] in (" ", "\n"):
                continue
            z = " "
        elif hart and text and text[-1] == " ":
            text.pop(); fett.pop(); link.pop()
        text.append(z); fett.append(f); link.append(l)
    while text and text[-1] == " ":
        text.pop(); fett.pop(); link.pop()
    s = "".join(text)
    if not s.strip():
        return None

    def bereiche(werte, mit_wert=False):
        raus, start = [], None
        for i in range(len(werte) + 1):
            w = werte[i] if i < len(werte) else None
            vor = werte[i - 1] if i else None
            if start is not None and w != vor:
                raus.append([start, i] + ([vor] if mit_wert else []))
                start = None
            if start is None and w:
                start = i
        return raus

    raus = {"s": s}
    f = bereiche(fett)
    if f and f != [[0, len(s)]]:
        raus["f"] = f
    elif f:
        raus["ganz_fett"] = True
    l_ = bereiche(link, True)
    if l_:
        raus["l"] = l_
    return raus


def text(el) -> str:
    t = laeufe(el)
    return t["s"] if t else ""


def absaetze(el) -> list[dict]:
    """Die <p> eines Fließtextblocks (render_portfolio.absaetze)."""
    if el is None:
        return []
    return [t for t in (laeufe(p) for p in alle(el, tag="p")) if t]


def verbinde(teile: list[dict], trenner: str = "\n\n") -> dict | None:
    """Mehrere Absätze in eine Text-Property, Fett- und Linkbereiche verschoben."""
    if not teile:
        return None
    s, f, l, pos = [], [], [], 0
    for i, t in enumerate(teile):
        if i:
            s.append(trenner)
            pos += len(trenner)
        s.append(t["s"])
        if t.get("ganz_fett"):
            f.append([pos, pos + len(t["s"])])
        f += [[a + pos, b + pos] for a, b in t.get("f", [])]
        l += [[a + pos, b + pos, u] for a, b, u in t.get("l", [])]
        pos += len(t["s"])
    raus = {"s": "".join(s)}
    if f:
        raus["f"] = f
    if l:
        raus["l"] = l
    return raus


def versal(el, t: dict | None) -> dict | None:
    """Stile mit Versalien (Eyebrow) setzt das CSS per text-transform - in der
    Figma-Property steht der Text so, wie er zu sehen ist."""
    if not t:
        return t
    stile = ds.laden()["textstile"]
    for k in _klassen(el):
        if k.startswith("t-") and stile.get(k[2:], {}).get("versalien"):
            return {**t, "s": t["s"].upper()}
    return t


# ── Bauplan je Folientyp ─────────────────────────────────────────────────

class Grenze(Exception):
    pass


class Plan:
    """Bauplan einer Folie: Komponente, Schalter, Texte, Bilder, Chrome."""

    def __init__(self, nr: int, typ: str):
        self.nr, self.typ = nr, typ
        self.variante: dict = {}
        self.schalter: dict = {}
        self.texte: dict = {}
        self.kinder: list[dict] = []
        self.bilder: list[dict] = []
        self.chrome = {"Logo": "aus", "Seitenzahl": "aus", "Nummer": None}

    def kind(self, pfad: list[str], schalter=None, texte=None, variante=None) -> dict:
        k = {"pfad": pfad}
        if variante:
            k["v"] = variante
        if schalter:
            k["b"] = schalter
        if texte:
            k["t"] = {n: t for n, t in texte.items() if t is not None}
        self.kinder.append(k)
        return k

    def json(self, kat: dict) -> dict:
        eintrag = kat["folie"][self.typ]
        sauber = lambda d: {n: {k: v for k, v in t.items() if k != "ganz_fett"}
                            for n, t in d.items() if t is not None}
        for kd in self.kinder:
            if "t" in kd:
                kd["t"] = sauber(kd["t"])
        return {"name": f"{self.nr:02d}", "typ": self.typ, "key": eintrag["key"],
                "set": eintrag["typ"] == "set", "v": self.variante, "b": self.schalter,
                "t": sauber(self.texte),
                "k": self.kinder, "i": self.bilder, "c": self.chrome}


def _t(s: str) -> dict:
    return {"s": s}


def grenze(liste: list, wie_viele: int, was: str, nr: int) -> list:
    if len(liste) > wie_viele:
        rp.merke(f"Figma (Bibliothek): Folie {nr:02d} hat {len(liste)} {was} – die Komponente "
                 f"trägt höchstens {wie_viele}. In Figma stehen die ersten {wie_viele}, "
                 "der Rest fehlt dort (im PDF steht er).")
        return liste[:wie_viele]
    return liste


def _bild_von(img, bilder_je_el: dict) -> dict | None:
    return bilder_je_el.get(id(img)) if img is not None else None


def chrome_lesen(sec, plan: Plan) -> None:
    """Wortmarke und Seitenzahl, wie das Renderskript sie gesetzt hat:
    nm-logo-weiss -> hell, nm-logo -> farbig, keine -> aus."""
    logo = eins(sec, "logo")
    if logo is not None:
        img = eins(logo, tag="img")
        plan.chrome["Logo"] = "hell" if img is not None and "weiss" in (img.get("src") or "") else "farbig"
    zahl = eins(sec, "seitenzahl")
    if zahl is not None:
        plan.chrome["Seitenzahl"] = "hell" if "seitenzahl--hell" in _klassen(zahl) else "dunkel"
        plan.chrome["Nummer"] = text(zahl)


def logos_in_slots(plan: Plan, imgs: list, bilder_je_el: dict, behaelter: list[str],
                   limit: int, was: str) -> list:
    """Logos auf Logo-Slots: der Slot spannt den Behälter auf, das Logo steht
    an seiner Stelle aus dem Layout (so in der Testbefüllung des Masters)."""
    imgs = grenze(imgs, limit, was, plan.nr)
    for i, img in enumerate(imgs, 1):
        e = _bild_von(img, bilder_je_el)
        if e is None:
            continue
        plan.bilder.append({"pfad": behaelter + [f"Logo {i}", "Logo"], "e": id(e),
                            "slot": behaelter + [f"Logo {i}"], "lage": True})
    return imgs


def kundenlogos(sec, plan: Plan, bilder_je_el: dict, grenzen: dict) -> None:
    box = eins(sec, "kundenlogo")
    imgs = alle(box, tag="img") if box is not None else []
    imgs = logos_in_slots(plan, imgs, bilder_je_el, ["Kundenlogo"],
                          grenzen["kundenlogos"], "Kundenlogos")
    plan.kind(["Kundenlogo"], schalter={f"Logo {i} anzeigen": i <= len(imgs) for i in (2, 3)})
    if not imgs:
        plan.bilder.append({"versteckt": ["Kundenlogo"]})


def aufzaehlung(plan: Plan, pfad: list[str], punkte: list, groesse: str, grenzen: dict) -> None:
    punkte = grenze(punkte, grenzen["aufzaehlung_punkte"], "Aufzählungspunkte", plan.nr)
    plan.kind(pfad, schalter={f"Punkt {i}": i <= len(punkte) for i in range(2, 7)},
              variante={"Größe": groesse})
    for i, p in enumerate(punkte, 1):
        plan.kind(pfad + [f"Punkt {i}"], texte={"Text": p})


def nda(sec, plan: Plan, pfad: list[str]) -> bool:
    n = eins(sec, "nda-hinweis")
    if n is None:
        return False
    farbe = "hell" if "nda-hinweis--hell" in _klassen(n) else "dunkel"
    plan.kind(pfad, variante={"Farbe": farbe}, texte={"Text": laeufe(n)})
    return True


def bildebene(plan: Plan, sec, wo, bilder_je_el, pfad: list[str]) -> bool:
    img = eins(wo, tag="img") if wo is not None else None
    e = _bild_von(img, bilder_je_el)
    if e is None:
        return False
    plan.bilder.append({"pfad": pfad, "e": id(e)})
    return True


def absatz_props(plan: Plan, teile: list[dict], n_max: int, praefix: str, schalter_ab: int = 2,
                 schalter_name=lambda i: f"Absatz {i} anzeigen", erster: int = 1) -> None:
    if len(teile) > n_max:
        rp.merke(f"Figma (Bibliothek): Folie {plan.nr:02d} hat {len(teile)} Absätze – die "
                 f"Komponente trägt {n_max}; die übrigen stehen im letzten Absatz.")
        teile = teile[:n_max - 1] + [verbinde(teile[n_max - 1:])]
    for i in range(erster, n_max + 1):
        t = teile[i - erster] if i - erster < len(teile) else None
        if t is not None:
            plan.texte[f"{praefix}{i}"] = t
        if i >= schalter_ab:
            plan.schalter[schalter_name(i)] = t is not None


def folie_planen(nr: int, sec, bilder_je_el: dict, sprache: str, kat: dict,
                 zaehler: dict) -> Plan | None:
    k = _klassen(sec)
    grenzen = kat["grenzen"]
    sprachvariante = {"Sprache": "Deutsch" if sprache == "de" else "Englisch"}

    if "seite--cover" in k:
        p = Plan(nr, "Cover")
        for name, klasse in (("Titel", "titel"), ("Name", "name"), ("Rolle", "rolle"), ("Jahr", "jahr")):
            p.texte[name] = laeufe(eins(sec, klasse)) or _t("")
    elif "seite--profil" in k:
        p = Plan(nr, "Profil")
        p.texte["Name"] = laeufe(eins(sec, "p-name"))
        p.texte["Rolle"] = laeufe(eins(sec, "p-rolle")) or _t("")
        foto = eins(sec, "foto")
        bildebene(p, sec, foto, bilder_je_el, ["Foto"])
        top = eins(sec, "karte--top")
        p.schalter["Top-Kenntnisse anzeigen"] = top is not None
        if top is not None:
            p.kind(["Top-Kenntnisse"], texte={"Titel": laeufe(eins(top, tag="h3")),
                                              "Text": laeufe(eins(top, tag="p"))})
        koennen = eins(sec, "karte--koennen")
        zeilen = grenze([laeufe(li) for li in alle(koennen, tag="li")],
                        grenzen["kenntnisse"], "Kenntnisse", nr)
        p.kind(["Kenntnisse"], texte={"Titel": laeufe(eins(koennen, tag="h3"))},
               schalter={f"Kenntnis {i}": i <= len(zeilen) for i in range(2, 11)})
        for i, z in enumerate(zeilen, 1):
            p.kind(["Kenntnisse", f"Kenntnis {i}"], texte={"Kenntnis": z},
                   schalter={"Trennlinie anzeigen": i > 1})
        karten = alle(sec, "pkarte")
        erfahrung = next((c for c in karten if eins(c, "zahl") is not None), None)
        verbindung = next((c for c in karten if eins(c, "paar--link") is not None), None)
        sprachen = next((c for c in karten if c is not erfahrung and c is not verbindung), None)
        p.schalter["Arbeitserfahrung anzeigen"] = erfahrung is not None
        p.schalter["Sprachen anzeigen"] = sprachen is not None
        p.schalter["Connect anzeigen"] = verbindung is not None
        if erfahrung is not None:
            fuss = laeufe(eins(erfahrung, "fuss"))
            p.kind(["Arbeitserfahrung"], schalter={"Fußtext anzeigen": fuss is not None},
                   texte={"Titel": laeufe(eins(erfahrung, tag="h3")),
                          "Zahl": laeufe(eins(erfahrung, "zahl")), "Fußtext": fuss})
        if sprachen is not None:
            paare = grenze(alle(sprachen, "paar"), grenzen["sprachen"], "Sprachen", nr)
            texte = {"Titel": laeufe(eins(sprachen, tag="h3"))}
            for i, paar in enumerate(paare, 1):
                texte[f"Sprache {i}"] = laeufe(eins(paar, tag="b"))
                texte[f"Niveau {i}"] = laeufe(eins(paar, tag="span"))
            p.kind(["Sprachen"], texte=texte,
                   schalter={f"Sprache {i} anzeigen": i <= len(paare) for i in (2, 3, 4)})
        if verbindung is not None:
            paare = grenze(alle(verbindung, "paar--link"), grenzen["links"], "Links", nr)
            texte = {"Titel": laeufe(eins(verbindung, tag="h3"))}
            for i, paar in enumerate(paare, 1):
                texte[f"Link {i}"] = laeufe(paar)
            p.kind(["Connect"], texte=texte,
                   schalter={f"Link {i} anzeigen": i <= len(paare) for i in (2, 3, 4)})
    elif "seite--kunden" in k:
        p = Plan(nr, "Kundenwand")
        p.texte["Titel"] = laeufe(eins(sec, "h1"))
        wand = eins(sec, "kundenwand")
        imgs = alle(wand, tag="img") if wand is not None else []
        imgs = logos_in_slots(p, imgs, bilder_je_el, ["Logowand"],
                              grenzen["kundenwand_logos"], "Kundenlogos")
        for i in range(2, 29):
            p.schalter[f"Logo {i}"] = i <= len(imgs)
        if not imgs:
            p.bilder.append({"versteckt": ["Logowand"]})
    elif "seite--statement" in k:
        p = Plan(nr, "Statement")
        p.texte["Rolle"] = laeufe(eins(sec, "rolle")) or _t("")
        p.texte["Zitat"] = laeufe(eins(sec, "aussage")) or _t("")
    elif "seite--divider" in k:
        p = Plan(nr, "Trenner")
        p.texte["Titel"] = laeufe(eins(sec, "h1"))
    elif "seite--prozess" in k:
        p = Plan(nr, "Prozess-Übersicht")
        dach = eins(sec, "eyebrow")
        p.texte["Dachzeile"] = versal(dach, laeufe(dach))
        spalten = grenze(alle(sec, "prozess-spalte"), grenzen["prozess_spalten"],
                         "Prozessschritte", nr)
        p.kind(["Prozess-Reihe"], schalter={"Spalte 4": len(spalten) >= 4})
        for i, sp in enumerate(spalten, 1):
            p.kind(["Prozess-Reihe", f"Spalte {i}"],
                   texte={"Titel": laeufe(eins(sp, tag="h2")), "Text": laeufe(eins(sp, tag="p"))})
    elif "seite--arbeitsweise" in k:
        p = Plan(nr, "Prozess-Schritt")
        ki = "seite--ki" in k
        if not ki:
            zaehler["schritt"] = zaehler.get("schritt", 0) + 1
        p.variante["Art"] = "Werkzeuge" if ki else f"Schritt {zaehler['schritt']}"
        dach = eins(sec, "eyebrow")
        p.texte["Dachzeile"] = versal(dach, laeufe(dach))
        kopf = eins(sec, "h1")
        p.texte["Titel"] = laeufe(kopf)
        grad = re.search(r"font-size:\s*([\d.]+)pt", kopf.get("style") or "") if kopf is not None else None
        if grad:
            p.texte["Titel"] = {**p.texte["Titel"], "g": float(grad.group(1))}
        teile = absaetze(eins(sec, "fliess"))
        unter = teile.pop(0) if teile and teile[0].get("ganz_fett") else None
        p.schalter["Untertitel anzeigen"] = unter is not None
        if unter is not None:
            p.texte["Untertitel"] = {"s": unter["s"]}
        absatz_props(p, teile, grenzen["schritt_texte"], "Text ",
                     schalter_name=lambda i: f"Text {i} anzeigen")
        if ki:
            reihe = eins(sec, "werkzeuge")
            imgs = grenze(alle(reihe, tag="img") if reihe is not None else [],
                          grenzen["werkzeuge"], "KI-Werkzeuge", nr)
            p.kind(["Werkzeuge"], schalter={f"Werkzeug {i}": i <= len(imgs) for i in range(2, 7)})
            for i, img in enumerate(imgs, 1):
                e = _bild_von(img, bilder_je_el)
                if e is not None:
                    p.bilder.append({"pfad": ["Werkzeuge", f"Werkzeug {i}", "Logo"], "e": id(e),
                                     "mitte": True})
            if not imgs:
                p.bilder.append({"versteckt": ["Werkzeuge"]})
        else:
            labels = [laeufe(eins(s_, tag="span")) for s_ in alle(sec, "schritt")][:3]
            p.kind(["Fortschritt"], variante={"Schritt": str(min(zaehler["schritt"], 3))},
                   texte={f"Label {i}": l_ for i, l_ in enumerate(labels, 1)})
    elif "seite--schwerpunkt" in k:
        p = Plan(nr, "Schwerpunkt")
        dach = eins(sec, "eyebrow")
        p.texte["Dachzeile"] = versal(dach, laeufe(dach))
        kopf = eins(sec, "h1")
        p.texte["Titel"] = laeufe(kopf)
        grad = re.search(r"font-size:\s*([\d.]+)pt", kopf.get("style") or "") if kopf is not None else None
        if grad:
            p.texte["Titel"] = {**p.texte["Titel"], "g": float(grad.group(1))}
        absatz_props(p, absaetze(eins(sec, "fliess")), grenzen["schwerpunkt_absaetze"], "Absatz ")
        karten = grenze(alle(sec, "pkarte"), grenzen["schwerpunkt_karten"], "Karten", nr)
        for i in (2, 3, 4):
            p.schalter[f"Karte {i} anzeigen"] = i <= len(karten)
        for i, c in enumerate(karten, 1):
            p.kind([f"Karte {i}"], texte={"Titel": laeufe(eins(c, tag="h3")),
                                          "Text": laeufe(eins(c, tag="p")) or _t("")})
    elif "seite--agentur" in k:
        p = Plan(nr, "Agentur")
        p.variante.update(sprachvariante)
    elif "seite--projekt" in k:
        p = Plan(nr, "Projekt-Kopf")
        p.texte["Titel"] = laeufe(eins(sec, "h1"))
        links = eins(sec, "sp-projekt")
        labels = [lb for lb in alle(links, "label")]
        p.texte["Label Projekt"] = laeufe(labels[0]) if labels else None
        fliess = [f for f in alle(links, "fliess")]
        p.texte["Projekttext"] = verbinde(absaetze(fliess[0])) if fliess else _t("")
        rolle = eins(sec, "rolle-block")
        p.schalter["Meine Rolle anzeigen"] = rolle is not None
        if rolle is not None:
            p.texte["Label Rolle"] = laeufe(eins(rolle, "label"))
            aufzaehlung(p, ["Rollen"], [laeufe(li) for li in alle(rolle, tag="li")], "24", grenzen)
        rechts = eins(sec, "sp-kunde")
        kunde = verbinde(absaetze(eins(rechts, "fliess"))) if rechts is not None else None
        p.schalter["Kunde anzeigen"] = kunde is not None
        if rechts is not None:
            p.texte["Label Kunde"] = laeufe(eins(rechts, "label"))
        if kunde is not None:
            p.texte["Kundentext"] = kunde
        kundenlogos(sec, p, bilder_je_el, grenzen)
    elif "seite--summary" in k:
        p = Plan(nr, "Projekt-Summary")
        p.texte["Titel"] = laeufe(eins(sec, "h1"))
        fliess = [f for f in alle(sec, "fliess")]
        absatz_props(p, absaetze(fliess[0]) if fliess else [], grenzen["summary_absaetze"], "Absatz ")
        hat = bildebene(p, sec, next((b for b in alle(sec, "bild") if "bild--platzhalter" not in _klassen(b)), None),
                        bilder_je_el, ["Bild"])
        p.schalter["Bild anzeigen"] = hat
        if not hat:
            rp.merke(f"Figma (Bibliothek): Folie {nr:02d} (Summary) ohne Bild – die Bildebene "
                     "ist ausgeblendet, im PDF steht der Platzhalter.")
        kundenlogos(sec, p, bilder_je_el, grenzen)
    elif "seite--loesung" in k:
        p = Plan(nr, "Lösung")
        p.variante["Fläche"] = "Standard"
        inhalt = eins(sec, "inhalt")
        p.texte["Einleitung"] = laeufe(eins(inhalt, "einleitung"))
        txt = verbinde(absaetze(eins(inhalt, "fliess")))
        p.schalter["Text anzeigen"] = txt is not None
        if txt is not None:
            p.texte["Text"] = txt
        punkte = [laeufe(li) for li in alle(eins(inhalt, "punkte"), tag="li")] if eins(inhalt, "punkte") is not None else []
        p.schalter["Aufzählung anzeigen"] = bool(punkte)
        if punkte:
            aufzaehlung(p, ["Aufzählung"], punkte, "20", grenzen)
        p.schalter["NDA-Hinweis anzeigen"] = nda(sec, p, ["NDA-Hinweis"])
        hat = bildebene(p, sec, next((b for b in alle(sec, "bild") if "bild--platzhalter" not in _klassen(b)), None),
                        bilder_je_el, ["Bild"])
        p.schalter["Bild anzeigen"] = hat
        if not hat:
            rp.merke(f"Figma (Bibliothek): Folie {nr:02d} (Lösung) ohne Screenfläche – die "
                     "Bildebene ist ausgeblendet, im PDF steht der Platzhalter.")
        kundenlogos(sec, p, bilder_je_el, grenzen)
    elif "seite--abschluss" in k:
        p = Plan(nr, "Vollbild")
        p.schalter["Bild anzeigen"] = bildebene(p, sec, eins(sec, "vollflaeche"), bilder_je_el, ["Bild"])
        p.schalter["NDA-Hinweis anzeigen"] = nda(sec, p, ["NDA-Hinweis"])
    elif "seite--kontakt" in k:
        p = Plan(nr, "Kontakt")
        p.variante.update(sprachvariante)
    else:
        rp.merke(f"Figma (Bibliothek): Folie {nr:02d} hat keinen bekannten Folientyp "
                 f"({' '.join(k)}) – sie fehlt in Figma.")
        return None
    chrome_lesen(sec, p)
    # Folien mit festem Foto im Master: Wortmarke und Seitenzahl nach diesem
    # Foto, nicht nach dem Foto, das das PDF zeigt.
    fest = kat.get("chrome_fest", {}).get(p.typ, {}).get(p.variante.get("Art", ""))
    if fest:
        p.chrome.update(fest)
    return p


# ── Prüfen gegen den Katalog ─────────────────────────────────────────────

def _baustein_fuer(typ: str, pfad: list[str]) -> str | None:
    """Welche Baustein-Komponente unter einem Pfad steckt - für die Prüfung der
    Property-Namen gegen den Katalog."""
    letzter = pfad[-1]
    if typ == "Profil":
        if letzter in ("Top-Kenntnisse", "Kenntnisse"):
            return "Kenntnis-Karte"
        if letzter.startswith("Kenntnis "):
            return "Kenntnis-Zeile"
        return "Panel-Karte"
    if letzter.startswith("Punkt "):
        return "Aufzählungspunkt"
    return {"Kundenlogo": "Kundenlogos", "Rollen": "Aufzählung", "Aufzählung": "Aufzählung",
            "NDA-Hinweis": "NDA-Hinweis", "Prozess-Reihe": "Prozess-Reihe",
            "Fortschritt": "Prozess-Fortschritt", "Werkzeuge": "Werkzeug-Reihe"}.get(
        letzter, "Prozess-Spalte" if letzter.startswith("Spalte ") else
        "Panel-Karte" if letzter.startswith("Karte ") else None)


def pruefen(plaene: list[dict], kat: dict) -> list[str]:
    befunde = []

    def gegen(komp: dict, werte: dict, wo: str, art=None):
        eig = komp["eigenschaften"]
        for n, w in werte.items():
            e = eig.get(n)
            if e is None:
                befunde.append(f"{wo}: Property „{n}“ gibt es an {komp['name']} nicht")
            elif e["art"] == "VARIANT" and w not in e["werte"]:
                befunde.append(f"{wo}: {n}={w} – möglich: {', '.join(e['werte'])}")
            elif art and e["art"] not in art:
                befunde.append(f"{wo}: „{n}“ ist {e['art']}")

    for p in plaene:
        wo = f"Folie {p['name']} ({p['typ']})"
        komp = kat["folie"][p["typ"]]
        gegen(komp, p["v"], wo, ("VARIANT",))
        gegen(komp, p["b"], wo, ("BOOLEAN",))
        gegen(komp, p["t"], wo, ("TEXT",))
        for kd in p["k"]:
            b = _baustein_fuer(p["typ"], kd["pfad"])
            if b is None:
                befunde.append(f"{wo}: unbekannte Ebene {'/'.join(kd['pfad'])}")
                continue
            komp_b = kat["baustein"][b]
            wo_k = f"{wo} › {'/'.join(kd['pfad'])}"
            gegen(komp_b, kd.get("v", {}), wo_k, ("VARIANT",))
            gegen(komp_b, kd.get("b", {}), wo_k, ("BOOLEAN",))
            gegen(komp_b, kd.get("t", {}), wo_k, ("TEXT",))
        ch = kat["baustein"]["Chrome"]["eigenschaften"]
        for n in ("Logo", "Seitenzahl"):
            if p["c"][n] not in ch[n]["werte"]:
                befunde.append(f"{wo}: Chrome {n}={p['c'][n]}")
    return befunde


# ── use_figma-Skripte ────────────────────────────────────────────────────

START = r"""
// Bibliotheksweg: Vorflug, Zielseite, Sammelrahmen, Bildablage.
const VORFLUG = __VORFLUG__;
try { await figma.importComponentSetByKeyAsync(VORFLUG); }
catch (e) { throw new Error("Bibliothek nicht erreichbar (" + (e && e.message || e) + ") – Master-Bibliothek in der Zieldatei aktivieren oder figma_plan.py mit --roh bauen"); }
const KNOTEN = "__KNOTEN__";
const RAHMEN_ALT = "__RAHMEN_ALT__";
let seite = null;
if (KNOTEN && !KNOTEN.startsWith("__")) {
  let n = await figma.getNodeByIdAsync(KNOTEN);
  while (n && n.type !== "PAGE") n = n.parent;
  seite = n;
}
if (!seite) { seite = figma.createPage(); seite.name = __NAME__; }
await figma.setCurrentPageAsync(seite);
let R = null;
if (RAHMEN_ALT && !RAHMEN_ALT.startsWith("__")) R = await figma.getNodeByIdAsync(RAHMEN_ALT);
if (!R) {
  const rechts = seite.children.length ? Math.max(...seite.children.map(n => n.x + n.width)) : 0;
  R = figma.createAutoLayout("VERTICAL", { name: __NAME__, itemSpacing: 300 });
  R.fills = [];
  R.resize(1920, 10); R.counterAxisSizingMode = "FIXED"; R.primaryAxisSizingMode = "AUTO";
  R.clipsContent = false;
  seite.appendChild(R);
  R.x = seite.children.length > 1 ? rechts + 300 : 0; R.y = 0;
}
// Bildablage: je Bild ein Trägerrechteck, Ziel von upload_assets. Die Pakete
// übernehmen den imageHash in die Bildebenen der Instanzen; das letzte räumt sie weg.
const A = figma.createFrame();
A.name = "Bildablage – wird vom letzten Paket entfernt";
seite.appendChild(A);
A.x = R.x + R.width + 300; A.y = R.y; A.fills = [];
const N = __BILDER__;
A.resize(Math.max(1, N.length) * 60, 60);
const traeger = [];
N.forEach((nr, i) => {
  const r = figma.createRectangle();
  A.appendChild(r); r.name = "bild:" + nr; r.resize(50, 50); r.x = i * 60; r.y = 0;
  r.fills = [{ type: "SOLID", color: { r: 0.92, g: 0.95, b: 0.96 } }];
  traeger.push([r.id, nr]);
});
return { seite: seite.id, rahmen: R.id, ablage: A.id, FILL: traeger };
"""

BAUER = r"""
const SEITE = await figma.getNodeByIdAsync("__SEITE__");
const RAHMEN = await figma.getNodeByIdAsync("__RAHMEN__");
const ABLAGE = await figma.getNodeByIdAsync("__ABLAGE__");
if (!SEITE || !RAHMEN || !ABLAGE) throw new Error("IDs fehlen: erst figma_plan.py --einsetzen laufen lassen");
await figma.setCurrentPageAsync(SEITE);
const HASH = {};
for (const c of ABLAGE.children) {
  const f = c.fills && c.fills[0];
  if (c.name.startsWith("bild:") && f && f.type === "IMAGE") HASH[parseInt(c.name.slice(5))] = f.imageHash;
}
const KOMP = {};
async function komp(key, set) {
  if (!KOMP[key]) KOMP[key] = set ? await figma.importComponentSetByKeyAsync(key) : await figma.importComponentByKeyAsync(key);
  return KOMP[key];
}
async function instanz(key, set) { const c = await komp(key, set); return (set ? c.defaultVariant : c).createInstance(); }
function eigen(inst, name) {
  const k = Object.keys(inst.componentProperties).find(k => k === name || k.split("#")[0] === name);
  if (!k) throw new Error("Property „" + name + "“ fehlt an „" + inst.name + "“ – hat sich der Master geändert?");
  return k;
}
function setze(inst, werte) {
  if (!werte) return;
  const o = {};
  for (const [n, v] of Object.entries(werte)) o[eigen(inst, n)] = v;
  if (Object.keys(o).length) inst.setProperties(o);
}
function such(wurzel, pfad) {
  let n = wurzel;
  for (const name of pfad) {
    // Exponierte Instanzen zuerst: eine gleichnamige Ebene in einer anderen
    // Kartenvariante soll nicht gewinnen.
    const t = n.findOne(x => x.name === name && x.type === "INSTANCE") || n.findOne(x => x.name === name);
    if (!t) throw new Error("Ebene „" + pfad.join("/") + "“ fehlt in „" + wurzel.name + "“");
    n = t;
  }
  return n;
}
function textknoten(inst, prop) {
  const st = [...inst.children];
  while (st.length) {
    const n = st.shift();
    const r = n.componentPropertyReferences;
    if (n.type === "TEXT" && r && r.characters && r.characters.split("#")[0] === prop) return n;
    if (n.type !== "INSTANCE" && "children" in n) st.push(...n.children);
  }
  return null;
}
async function schriften(wurzel) {
  const fs = new Map();
  for (const t of wurzel.findAllWithCriteria({ types: ["TEXT"] })) {
    const liste = t.characters.length ? t.getRangeAllFontNames(0, t.characters.length) : (t.fontName === figma.mixed ? [] : [t.fontName]);
    for (const f of liste) fs.set(f.family + "/" + f.style, f);
  }
  for (const f of fs.values()) await figma.loadFontAsync(f);
}
async function texte(inst, werte) {
  if (!werte) return;
  const plain = {};
  for (const [n, t] of Object.entries(werte)) plain[n] = t.s;
  setze(inst, plain);
  for (const [n, t] of Object.entries(werte)) {
    if (!t.f && !t.l && !t.g) continue;
    const k = textknoten(inst, n);
    if (!k) continue;
    if (t.g) k.fontSize = t.g;
    for (const [a, b] of t.f || []) {
      const f = k.getRangeFontName(a, a + 1);
      const fett = { family: f.family, style: P.fett[f.family] || "Bold" };
      await figma.loadFontAsync(fett);
      k.setRangeFontName(a, b, fett);
    }
    for (const [a, b, u] of t.l || []) k.setRangeHyperlink(a, b, { type: "URL", value: u });
  }
}
function fuelle(n, nr, modus) {
  if (!HASH[nr]) throw new Error("Bild " + nr + " ist noch nicht in der Bildablage – erst upload_assets und figma_assets.py");
  n.fills = [{ type: "IMAGE", imageHash: HASH[nr], scaleMode: modus }];
}
const ab = (n, F) => [n.absoluteTransform[0][2] - F.absoluteTransform[0][2], n.absoluteTransform[1][2] - F.absoluteTransform[1][2]];
const angelegt = [];
for (const s of P.folien) {
  const F = figma.createFrame();
  F.name = s.name; F.resize(1920, 1080); F.clipsContent = true;
  F.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
  const alt = RAHMEN.children.find(c => c.name === s.name);
  if (alt) { RAHMEN.insertChild(RAHMEN.children.indexOf(alt), F); alt.remove(); }
  else RAHMEN.appendChild(F);
  const I = await instanz(s.key, s.set);
  F.appendChild(I); I.x = 0; I.y = 0; I.name = "Folie";
  // 1. Varianten und Schalter, 2. Schriften laden, 3. Texte, 4. Bilder.
  setze(I, s.v); setze(I, s.b);
  // Jede Ebene erst holen, wenn ihr Elternteil fertig umgeschaltet ist - ein
  // Variantenwechsel (Aufzählung 24 -> 20) ersetzt die Knoten darunter.
  for (const k of s.k) { const n = such(I, k.pfad); setze(n, k.v); setze(n, k.b); }
  await schriften(I);
  await texte(I, s.t);
  for (const k of s.k) if (k.t) await texte(such(I, k.pfad), k.t);
  for (const b of s.i) {
    if (b.versteckt) { such(I, b.versteckt).visible = false; continue; }
    const z = such(I, b.pfad);
    fuelle(z, b.nr, b.modus);
    if (b.lage || b.mitte) {
      // Logo-Slot und Werkzeugkachel sind Auto-Layouts, das Logo füllt sie
      // (FILL). Gesetzt wird deshalb der Innenabstand des Slots - Lage und
      // Größe einer Ebene in einer Instanz lassen sich nicht überschreiben.
      const slot = b.lage ? such(I, b.slot) : z.parent;
      const [sx, sy] = ab(slot, F);
      const x = b.lage ? b.g[0] - sx : (slot.width - b.g[2]) / 2;
      const y = b.lage ? b.g[1] - sy : (slot.height - b.g[3]) / 2;
      if (slot.layoutMode && slot.layoutMode !== "NONE") {
        slot.paddingLeft = Math.max(0, x); slot.paddingTop = Math.max(0, y);
        slot.paddingRight = Math.max(0, slot.width - x - b.g[2]);
        slot.paddingBottom = Math.max(0, slot.height - y - b.g[3]);
      } else {
        try { z.resize(b.g[2], b.g[3]); } catch (e) { /* Größe fest im Master - FIT verzerrt nicht */ }
      }
    }
  }
  const frei = figma.createFrame();
  F.appendChild(frei); frei.name = "Freie Bilder"; frei.resize(1920, 1080); frei.x = 0; frei.y = 0;
  frei.fills = []; frei.clipsContent = true;
  const C = await instanz(P.chrome.key, true);
  F.appendChild(C); C.x = 0; C.y = 0; C.name = "Chrome";
  setze(C, { Logo: s.c.Logo, Seitenzahl: s.c.Seitenzahl });
  if (s.c.Seitenzahl !== "aus" && s.c.Nummer) {
    const z = such(C, ["Seitenzahl"]);
    await schriften(z);
    setze(z, { Nummer: s.c.Nummer });
  }
  angelegt.push(F.id);
}
if (P.letztes) ABLAGE.remove();
return { folien: angelegt, rahmen: RAHMEN.id, ablage_entfernt: !!P.letztes };
"""


def plaene_bauen(folien, d: dict, nur: set[int] | None = None) -> tuple[list[Plan], dict]:
    """Je Folie der Bauplan; dazu die Bildebenen, die tatsächlich gebraucht
    werden (id(Eintrag) -> Eintrag aus dem Layout). Geplant wird immer das
    ganze Deck - die Arbeitsweise-Seiten zählen ihren Schritt mit -, `nur`
    wählt danach aus."""
    kat = katalog()
    sprache = d.get("sprache", "de")
    plaene, zaehler = [], {}
    for f in folien:
        bilder_je_el = {}
        for e in f.ebenen:
            if e.get("t") == "i" and e.get("_el") is not None:
                bilder_je_el[id(e["_el"])] = e
        if f.element is None:
            rp.merke(f"Figma (Bibliothek): Folie {f.nr:02d} – keine <section> gefunden.")
            continue
        p = folie_planen(f.nr, f.element, bilder_je_el, sprache, kat, zaehler)
        if p is not None:
            plaene.append(p)
    if nur is not None:
        plaene = [p for p in plaene if p.nr in nur]
    alle_bilder = {id(e): e for f in folien for e in f.ebenen if e.get("t") == "i"}
    gebraucht = {b["e"]: alle_bilder[b["e"]] for p in plaene for b in p.bilder if "e" in b}
    return plaene, gebraucht


def skripte_schreiben(plaene: list[Plan], gebraucht: dict, liste: list[dict], name: str,
                      ordner: Path, knoten: str = "", rahmen_alt: str = "") -> list[Path]:
    kat = katalog()
    modus = {b["nr"]: b["modus"] for b in liste}
    for alt in list(ordner.glob("[0-9][0-9]-folien.js")) + [ordner / "99-bilder.js"]:
        if alt.exists():
            alt.unlink()
    fertig = []
    for p in plaene:
        j = p.json(kat)
        bilder = []
        for b in j["i"]:
            if "versteckt" in b:
                bilder.append(b)
                continue
            e = gebraucht[b.pop("e")]
            b["nr"], b["modus"] = e["bild"], modus[e["bild"]]
            if b.get("lage") or b.get("mitte"):
                b["g"] = [e["x"], e["y"], e["w"], e["h"]]
            bilder.append(b)
        j["i"] = bilder
        fertig.append(j)
    befunde = pruefen(fertig, kat)
    if befunde:
        raise SystemExit("Bauplan passt nicht zum Katalog assets/master-bibliothek.json:\n  - "
                         + "\n  - ".join(befunde))
    nummern = sorted({b["nr"] for j in fertig for b in j["i"] if "nr" in b})
    start = (START.replace("__VORFLUG__", json.dumps(kat["baustein"][kat["vorflug"]]["key"]))
             .replace("__NAME__", json.dumps(f"Portfolio — {name}"))
             .replace("__BILDER__", json.dumps(nummern)))
    if knoten:
        start = start.replace("__KNOTEN__", knoten)
    if rahmen_alt:
        start = start.replace("__RAHMEN_ALT__", rahmen_alt)
    (ordner / "00-start.js").write_text(start, encoding="utf-8")

    fett = {fam: ds.laden()["schriftdateien"][fam].get(str(ds.laden()["fett"]), {}).get("figma", "Bold")
            for fam in ds.laden()["schriftdateien"]}
    chrome = {"key": kat["baustein"]["Chrome"]["key"]}
    pakete, paket, groesse = [], [], len(BAUER)
    for j in fertig:
        n = len(json.dumps(j, ensure_ascii=False, separators=(",", ":")))
        if paket and (groesse + n > CODE_GRENZE or len(paket) >= FOLIEN_JE_PAKET):
            pakete.append(paket)
            paket, groesse = [], len(BAUER)
        paket.append(j)
        groesse += n
    if paket:
        pakete.append(paket)
    dateien = []
    for i, liste_ in enumerate(pakete, 1):
        daten = {"fett": fett, "chrome": chrome, "folien": liste_, "letztes": i == len(pakete)}
        code = "const P = " + json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + ";\n" + BAUER
        if len(code) > 50000:
            rp.merke(f"Figma-Paket {i} ist {len(code)} Zeichen lang – über dem Deckel von use_figma.")
        datei = ordner / f"{i:02d}-folien.js"
        datei.write_text(code, encoding="utf-8")
        dateien.append(datei)
    return dateien


def einsetzen(ordner: Path, antwort: Path) -> None:
    """Die Antwort des Start-Aufrufs: IDs in die Pakete, Träger nach knoten.json."""
    a = json.loads(Path(antwort).read_text(encoding="utf-8"))
    for datei in sorted(ordner.glob("[0-9][0-9]-folien.js")):
        t = datei.read_text(encoding="utf-8")
        t = (t.replace("__SEITE__", a["seite"]).replace("__RAHMEN__", a["rahmen"])
              .replace("__ABLAGE__", a["ablage"]))
        datei.write_text(t, encoding="utf-8")
    (ordner / "knoten.json").write_text(json.dumps({"FILL": a["FILL"]}, ensure_ascii=False),
                                        encoding="utf-8")
    print(f"IDs eingesetzt: Seite {a['seite']}, Rahmen {a['rahmen']}, Bildablage {a['ablage']} "
          f"– {len(a['FILL'])} Bildträger in knoten.json")
