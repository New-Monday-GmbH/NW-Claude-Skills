#!/usr/bin/env python3
"""Selbsttest für newmonday-anfrage: ablage.py und vergleich.py."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ablage import anlegen, einsammeln, initialen, zielname  # noqa: E402
from vergleich import fehlend  # noqa: E402

fehler = []


def pruefe(bedingung, text):
    if not bedingung:
        fehler.append(text)


# ablage: Namen
pruefe(initialen("Timo Muster") == "T. M.", "Initialen")
pruefe(zielname("New-Monday - Timo Muster - UX Designer - CV.pdf", "Timo Muster")
       == "New Monday - Timo Muster - CV.pdf", "CV voll")
pruefe(zielname("New-Monday - T. M. - UX Designer - CV.pdf", "Timo Muster")
       == "New Monday - T. M. - CV.pdf", "CV anonym")
pruefe(zielname("New-Monday - Timo Muster - UX Designer - Skillmatrix A4.pdf", "Timo Muster")
       == "New Monday - Timo Muster - Skillmatrix A4.pdf", "Skillmatrix A4")
pruefe(zielname("New-Monday - Timo Muster - UX Designer - Skillmatrix.pdf", "Timo Muster")
       == "New Monday - Timo Muster - Skillmatrix.pdf", "Skillmatrix lang")
pruefe(zielname("muster-timo-portfolio.pdf", "Timo Muster")
       == "New Monday - Timo Muster - Portfolio.pdf", "Portfolio, altes Namensschema")
pruefe(zielname("notizen.pdf", "Timo Muster") is None, "fremdes PDF bleibt liegen")

# ablage: Ordner anlegen und einsammeln
with tempfile.TemporaryDirectory() as tmp:
    lauf = anlegen(Path(tmp), "C0123 UX/UI Designer", "Timo Muster")
    pruefe(lauf == Path(tmp) / "C0123 UX UI Designer" / "Timo Muster" / "_arbeit", f"Laufordner {lauf}")
    (lauf / "ausgabe").mkdir()
    for n in ("New-Monday - Timo Muster - UX - CV.pdf", "New-Monday - T. M. - UX - CV.pdf",
              "New-Monday - Timo Muster - UX - Skillmatrix.pdf",
              "New-Monday - Timo Muster - UX - Skillmatrix A4.pdf",
              "New-Monday - Timo Muster - UX - Portfolio.pdf"):
        (lauf / "ausgabe" / n).write_bytes(b"%PDF")
    # gleiches Dokument im alten Namensschema, älter als das neue
    (lauf / "ausgabe" / "muster-timo-portfolio.pdf").write_bytes(b"%PDF alt")
    import os
    os.utime(lauf / "ausgabe" / "muster-timo-portfolio.pdf", (1, 1))
    kopiert = einsammeln(lauf.parent)
    pruefe(len(kopiert) == 6, f"einsammeln: {len(kopiert)} statt 6")
    pruefe((lauf.parent / "New Monday - Timo Muster - Portfolio.pdf").read_bytes() == b"%PDF",
           "beim doppelten Portfolio hat das ältere gewonnen")
    pruefe((lauf.parent / "New Monday - T. M. - CV.pdf").exists(), "anonymer CV im Kandidatenordner")

# vergleich
bestand = {"person": {"kurzprofil": "Alt.", "kenntnisse": ["Usability-Tests", "Figma"]},
           "stationen": [{"firma": "Acme", "projekte": [{"beschreibung": "Konzeption der Suche."}]}],
           "prozess": [{"text": "Wir machen Usability-Tests mit Nutzern."}],
           "foto": "/tmp/foto.png"}
neu_ok = {"person": {"kurzprofil": "Neu auf die Stelle.", "kenntnisse": ["Figma", "Design-QA"]},
          "stationen": [{"firma": "Acme", "projekte": [
              {"beschreibung": "Konzeption der Suche. Barrierefreiheit berücksichtigt."}]}],
          "prozess": [{"text": "Wir machen Usability-Tests mit Nutzern."}]}
pruefe(fehlend(bestand, neu_ok) == [], f"erlaubte Änderungen gemeldet: {fehlend(bestand, neu_ok)}")
neu_weg = {"person": {"kenntnisse": ["Figma"]}, "stationen": [{"firma": "Acme"}], "prozess": []}
weg = {t for _, t in fehlend(bestand, neu_weg)}
pruefe("Konzeption der Suche." in weg, "entfernter Projekttext nicht gemeldet")
pruefe("Usability-Tests" in weg, "Kenntnis, die nirgends mehr steht, nicht gemeldet")
pruefe("Alt." not in weg, "Kurzprofil darf frei sein")
einschub = {"a": "Optimierung von Accessibility, UX und Aufbau."}
pruefe(fehlend(einschub, {"a": "Optimierung von Accessibility (WCAG/BITV), UX und Aufbau."}) == [],
       "Einschub mitten im Satz als Streichung gemeldet")
pruefe(fehlend(einschub, {"a": "Optimierung von UX und Aufbau."}) != [], "Streichung im Satz nicht gemeldet")
pruefe(fehlend(einschub, {"a": "Kurz."}, frozenset(einschub.values())) == [], "freigegebene Ausnahme gemeldet")
kenntnis = {"person": {"kenntnisse": ["User Research (Usability-Testing, Interviews, etc.)"]}}
pruefe(fehlend(kenntnis, {"person": {"kenntnisse": [
    "User Research (Usability-Testing, Interviews, Analytics, etc.)"]}}) == [],
    "Einschub in einer Kenntnis als Streichung gemeldet")

if fehler:
    sys.exit("Selbsttest fehlgeschlagen:\n- " + "\n- ".join(fehler))
print("Selbsttest bestanden (ablage, vergleich).")
