#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profilmatching für New Monday
=============================

Gleicht eine Projektanfrage aus dem EspoCRM gegen den Kandidatenpool ab und gibt
eine Trefferliste mit Abdeckungsgrad aus.

Braucht nur Python 3 — keine zusätzlichen Pakete.

Aufruf
------
    python3 matching.py                      # offene Anfragen zur Auswahl anzeigen
    python3 matching.py --anfrage <ID>       # eine bestimmte Anfrage abgleichen
    python3 matching.py --anfrage <ID> --alle    # auch nicht verfügbare Kandidaten zeigen
    python3 matching.py --anfrage <ID> --csv     # Ergebnis als CSV daneben ablegen

Konfiguration
-------------
matching.config.json im selben Ordner. Vorlage: matching.config.beispiel.json
Der Connector-Ordner hat bereits einen CRM-Schlüssel — derselbe funktioniert hier.

Was das Skript NICHT tut
------------------------
Es schreibt nichts. Weder ins CRM noch nach JOIN. Es liest und rechnet.
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime

HIER = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HIER, "matching.config.json")

# --------------------------------------------------------------- Gewichtung
#
# Der Abdeckungsgrad ist bewusst simpel gehalten und nachvollziehbar:
#
#   Muss-Skills      zählen voll. Fehlt einer, sinkt die Quote sichtbar.
#   Kann-Skills      zählen ein Drittel.
#   Fachdomäne       zählt wie ein Muss-Skill, wenn die Anfrage eine fordert.
#   Rolle            muss passen, sonst gibt es einen deutlichen Abzug.
#   Seniorität       zu niedrig kostet, zu hoch kostet nichts.
#   Deutsch          zu niedrig ist ein K.-o.-Kriterium, wenn gefordert.
#
# Es gibt keine geheime Formel. Wer das Ergebnis anzweifelt, sieht in der
# Begründungsspalte, woran es lag.

GEWICHT_MUSS = 1.0
GEWICHT_KANN = 0.33
GEWICHT_DOMAENE = 1.0

# --------------------------------------------------------------- Schwelle
#
# Ab dieser Abdeckung wird ein Profil überhaupt vorgeschlagen und die Person
# angesprochen. Darunter wird abgesagt, ohne jemanden zu kontaktieren.
#
# Festgelegt von Manuel Klein am 22.09.2026: "Ich kontaktiere die jeweiligen
# Profilmember erst, wenn ein Match vorhanden ist. Bei 24 % brauche ich nicht
# zu fragen." Sinnvoll ab 70 Prozent.
SCHWELLE = 70

SENIORITAET_RANG = {"": 0, "Junior": 1, "Mid": 2, "Senior": 3, "Principal": 4}
DEUTSCH_RANG = {
    "": 0, "unbekannt": 0, "B1 oder darunter": 1, "B2": 2,
    "C1": 3, "C2": 4, "Muttersprache": 5,
}

# Rollen, die sich in der Praxis überschneiden. Wer links steht, kommt für
# rechts grundsätzlich in Frage — mit Abschlag, nicht als Volltreffer.
ROLLEN_NACHBARN = {
    "UX/UI Design": {"Product Owner / PM"},
    "Frontend": {"Fullstack"},
    "Fullstack": {"Frontend", "Backend"},
    "Backend": {"Fullstack"},
    "DevOps / Cloud": {"Infrastruktur"},
    "Infrastruktur": {"DevOps / Cloud"},
    "Data / BI": {"Backend"},
}


# ------------------------------------------------------------------- EspoCRM

class Espo:
    def __init__(self, basis, api_key):
        self.basis = basis.rstrip("/")
        self.kopf = {"X-Api-Key": api_key, "Accept": "application/json"}

    def holen(self, pfad):
        url = f"{self.basis}/api/v1/{pfad.lstrip('/')}"
        req = urllib.request.Request(url, headers=self.kopf)
        try:
            with urllib.request.urlopen(req, timeout=30) as antwort:
                return json.loads(antwort.read().decode("utf-8"))
        except urllib.error.HTTPError as fehler:
            grund = fehler.headers.get("X-Status-Reason", "")
            raise RuntimeError(f"HTTP {fehler.code} bei {pfad} — {grund}") from None

    def liste(self, entitaet, **params):
        teile = []
        for k, v in params.items():
            teile.append(f"{k}={urllib.request.quote(str(v))}")
        return self.holen(f"{entitaet}?{'&'.join(teile)}")


# -------------------------------------------------------------------- Rechnen

def tage_bis(datum_text):
    """Tage von heute bis zum Datum. Negativ heißt: liegt in der Vergangenheit."""
    if not datum_text:
        return None
    try:
        d = datetime.strptime(datum_text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    return (d - date.today()).days


def bewerten(anfrage, kandidat):
    """Gibt (prozent, treffer, luecken, ausschluss) zurück."""
    muss = set(anfrage.get("cSkillsMuss") or [])
    kann = set(anfrage.get("cSkillsKann") or [])
    domaenen = set(anfrage.get("cFachdomaene") or [])

    # Geprüfte Skills zählen. Erkannte zählen nur halb, weil sie niemand
    # bestätigt hat — sie tauchen in der Begründung als "ungeprüft" auf.
    geprueft = set(kandidat.get("skills") or [])
    erkannt = set(kandidat.get("skillsErkannt") or []) - geprueft
    hat_domaene = set(kandidat.get("fachdomaene") or [])

    treffer, luecken, ausschluss = [], [], []

    punkte = 0.0
    maximum = 0.0

    for s in sorted(muss):
        maximum += GEWICHT_MUSS
        if s in geprueft:
            punkte += GEWICHT_MUSS
            treffer.append(s)
        elif s in erkannt:
            punkte += GEWICHT_MUSS * 0.5
            treffer.append(f"{s} (ungeprüft)")
        else:
            luecken.append(s)

    for s in sorted(kann):
        maximum += GEWICHT_KANN
        if s in geprueft:
            punkte += GEWICHT_KANN
            treffer.append(f"{s} (Kann)")
        elif s in erkannt:
            punkte += GEWICHT_KANN * 0.5
            treffer.append(f"{s} (Kann, ungeprüft)")

    if domaenen:
        maximum += GEWICHT_DOMAENE
        gemeinsam = domaenen & hat_domaene
        if gemeinsam:
            punkte += GEWICHT_DOMAENE
            treffer.append("Domäne: " + ", ".join(sorted(gemeinsam)))
        else:
            luecken.append("Domäne: " + " oder ".join(sorted(domaenen)))

    prozent = round(100 * punkte / maximum) if maximum else 0

    # ---- Rolle
    gesucht = anfrage.get("cRolle") or ""
    hat = kandidat.get("hauptrolle") or ""
    if gesucht and hat and gesucht != "Sonstige":
        if hat == gesucht:
            pass
        elif gesucht in ROLLEN_NACHBARN.get(hat, set()):
            prozent = round(prozent * 0.8)
            luecken.append(f"Rolle benachbart ({hat} statt {gesucht})")
        else:
            prozent = round(prozent * 0.4)
            luecken.append(f"Rolle passt nicht ({hat} statt {gesucht})")

    # ---- Seniorität
    gefordert = SENIORITAET_RANG.get(anfrage.get("cSenioritaet") or "", 0)
    vorhanden = SENIORITAET_RANG.get(kandidat.get("senioritaet") or "", 0)
    if gefordert and vorhanden and vorhanden < gefordert:
        prozent = round(prozent * 0.7)
        luecken.append(f"Seniorität {kandidat.get('senioritaet')} statt "
                       f"{anfrage.get('cSenioritaet')}")

    # ---- Deutsch: echtes Ausschlusskriterium
    d_gefordert = DEUTSCH_RANG.get(anfrage.get("cDeutsch") or "", 0)
    d_vorhanden = DEUTSCH_RANG.get(kandidat.get("deutsch") or "", 0)
    if d_gefordert:
        if d_vorhanden == 0:
            luecken.append("Deutschniveau nicht erfasst")
        elif d_vorhanden < d_gefordert:
            ausschluss.append(f"Deutsch {kandidat.get('deutsch')} < "
                              f"{anfrage.get('cDeutsch')}")

    # ---- Verfügbarkeit
    status = kandidat.get("statusPool") or ""
    if status == "ausgeschieden":
        ausschluss.append("ausgeschieden")
    elif status == "nicht verfügbar":
        ausschluss.append("nicht verfügbar")

    start = anfrage.get("cStartGeplant")
    frei = kandidat.get("verfuegbarAb")
    if start and frei and frei[:10] > start[:10]:
        luecken.append(f"frei erst ab {frei[:10]}, Start {start[:10]}")
        prozent = round(prozent * 0.85)

    # ---- Satz
    kundensatz = anfrage.get("cSatzKunde")
    mindest = kandidat.get("mindestsatz")
    if kundensatz and mindest and mindest > kundensatz:
        ausschluss.append(f"Mindestsatz {mindest:.0f} € über Kundensatz "
                          f"{kundensatz:.0f} €")

    return max(0, min(100, prozent)), treffer, luecken, ausschluss


# -------------------------------------------------------------------- Ausgabe

def kuerzen(text, laenge):
    text = str(text or "")
    return text if len(text) <= laenge else text[:laenge - 1] + "…"


def ausgeben(anfrage, ergebnisse, zeige_alle):
    print()
    print("=" * 96)
    print(f"  {anfrage.get('name')}")
    print("=" * 96)
    zeilen = [
        ("Vermittler", anfrage.get("cVermittlerName")),
        ("Endkunde", anfrage.get("cEndkundeName")),
        ("Rolle", anfrage.get("cRolle")),
        ("Domäne", ", ".join(anfrage.get("cFachdomaene") or []) or None),
        ("Muss", ", ".join(anfrage.get("cSkillsMuss") or []) or None),
        ("Kann", ", ".join(anfrage.get("cSkillsKann") or []) or None),
        ("Deutsch", anfrage.get("cDeutsch")),
        ("Start", (anfrage.get("cStartGeplant") or "")[:10] or None),
        ("Kundensatz", f"{anfrage['cSatzKunde']:.2f} €"
                       if anfrage.get("cSatzKunde") else None),
    ]
    for bezeichnung, wert in zeilen:
        if wert:
            print(f"  {bezeichnung:<12} {wert}")

    if not (anfrage.get("cSkillsMuss") or anfrage.get("cFachdomaene")):
        print()
        print("  ⚠  Diese Anfrage hat weder Muss-Skills noch eine Fachdomäne.")
        print("     Ohne Anforderungsprofil kann nicht abgeglichen werden.")
        print()
        return

    passend = [e for e in ergebnisse if not e["ausschluss"]]
    raus = [e for e in ergebnisse if e["ausschluss"]]

    print()
    print(f"    {'Kandidat':<24} {'Status':<14} {'Frei ab':<11} {'Quote':>6}   Lücken")
    print("  " + "-" * 92)

    if not passend:
        print("  Kein Kandidat ohne Ausschlusskriterium.")
    for e in passend:
        k = e["kandidat"]
        marke = "●" if e["prozent"] >= SCHWELLE else "·"
        frei = (k.get("verfuegbarAb") or "")[:10] or "—"
        print(f"  {marke} {kuerzen(k.get('name'), 23):<24} "
              f"{kuerzen(k.get('statusPool'), 13):<14} "
              f"{frei:<11} "
              f"{e['prozent']:>4} %   {kuerzen('; '.join(e['luecken']), 40)}")
    print()
    print(f"  ● ab {SCHWELLE} % — vorstellen und die Person ansprechen")
    print("  · darunter — nicht ansprechen")

    if raus and zeige_alle:
        print()
        print("  Ausgeschlossen:")
        for e in raus:
            k = e["kandidat"]
            print(f"    {kuerzen(k.get('name'), 24):<26} "
                  f"{'; '.join(e['ausschluss'])}")
    elif raus:
        print()
        print(f"  {len(raus)} Kandidaten ausgeschlossen — mit --alle anzeigen.")

    treffer = [e for e in passend if e["prozent"] >= SCHWELLE]
    bester = passend[0] if passend else None
    print()
    if len(treffer) == 1:
        print(f"  → {treffer[0]['kandidat'].get('name')} ansprechen und vorstellen.")
    elif len(treffer) > 1:
        namen = ", ".join(e["kandidat"].get("name") for e in treffer[:3])
        print(f"  → {len(treffer)} Treffer: {namen}. Ansprechen und vorstellen.")
    else:
        bestwert = bester["prozent"] if bester else 0
        print(f"  → Kein Treffer. Bester Wert {bestwert} %, Schwelle {SCHWELLE} %.")
        print("     Absagen oder sourcen — niemanden ansprechen.")
    print()


def csv_schreiben(anfrage, ergebnisse, pfad):
    with open(pfad, "w", encoding="utf-8-sig", newline="") as f:
        s = csv.writer(f, delimiter=";")
        s.writerow(["Anfrage", anfrage.get("name")])
        s.writerow([])
        s.writerow(["Kandidat", "Rolle", "Seniorität", "Status", "Verfügbar ab",
                    "Quote %", "Treffer", "Lücken", "Ausschluss"])
        for e in ergebnisse:
            k = e["kandidat"]
            s.writerow([
                k.get("name"), k.get("hauptrolle"), k.get("senioritaet"),
                k.get("statusPool"), (k.get("verfuegbarAb") or "")[:10],
                e["prozent"], "; ".join(e["treffer"]),
                "; ".join(e["luecken"]), "; ".join(e["ausschluss"]),
            ])
    print(f"  CSV abgelegt: {pfad}")


# ------------------------------------------------------------------ Hauptlauf

OFFENE_STUFEN = ["Prospecting", "Qualification", "Kandidat ausgewählt",
                 "Proposal", "Interview", "Negotiation",
                 "Vertrag in Abwicklung", "Hold – Direktkunde"]


def anfragen_zeigen(espo):
    daten = espo.liste("Opportunity", maxSize=200, orderBy="createdAt", order="desc")
    offen = [o for o in daten.get("list", []) if o.get("stage") in OFFENE_STUFEN]
    print()
    print("  Offene Anfragen — ID für --anfrage übernehmen")
    print("  " + "-" * 92)
    for o in offen:
        profil = "Profil ✓" if o.get("cSkillsMuss") else "ohne Profil"
        print(f"  {o['id']}  {kuerzen(o.get('name'), 58):<60} "
              f"{kuerzen(o.get('stage'), 14):<16} {profil}")
    print()
    print(f"  {len(offen)} offene Anfragen, davon "
          f"{sum(1 for o in offen if o.get('cSkillsMuss'))} mit Anforderungsprofil.")
    print()


def main():
    p = argparse.ArgumentParser(description="Profilmatching gegen den Kandidatenpool")
    p.add_argument("--anfrage", help="ID der Projektanfrage")
    p.add_argument("--alle", action="store_true",
                   help="auch ausgeschlossene Kandidaten anzeigen")
    p.add_argument("--csv", action="store_true", help="Ergebnis als CSV ablegen")
    args = p.parse_args()

    if not os.path.exists(CONFIG):
        print("Es fehlt matching.config.json.")
        print("Kopiere matching.config.beispiel.json und trage die Zugänge ein.")
        sys.exit(1)
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)

    espo = Espo(cfg["espo_url"], cfg["espo_api_key"])

    if not args.anfrage:
        anfragen_zeigen(espo)
        return

    anfrage = espo.holen(f"Opportunity/{args.anfrage}")
    kandidaten = espo.liste("CKandidat", maxSize=200, orderBy="name").get("list", [])

    ergebnisse = []
    for k in kandidaten:
        prozent, treffer, luecken, ausschluss = bewerten(anfrage, k)
        ergebnisse.append({"kandidat": k, "prozent": prozent, "treffer": treffer,
                           "luecken": luecken, "ausschluss": ausschluss})
    ergebnisse.sort(key=lambda e: (-e["prozent"], e["kandidat"].get("name") or ""))

    ausgeben(anfrage, ergebnisse, args.alle)

    if args.csv:
        sicher = "".join(c if c.isalnum() or c in " -_" else "_"
                         for c in (anfrage.get("name") or "Anfrage"))[:60].strip()
        csv_schreiben(anfrage, ergebnisse,
                      os.path.join(HIER, f"Matching {sicher}.csv"))


if __name__ == "__main__":
    main()
