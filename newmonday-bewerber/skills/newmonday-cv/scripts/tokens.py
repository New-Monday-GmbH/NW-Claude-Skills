"""Die Designwerte des Lebenslaufs — eine Quelle fuer PDF, Figma-Plan und Test.

Alle Werte stehen in assets/tokens.json und stammen aus der Figma-Datei, die
dort unter "quelle" steht. Hier wird nur gelesen und abgeleitet, nichts
festgelegt: Wer eine Groesse, einen Abstand oder eine Farbe aendern will,
aendert sie in tokens.json. cv.css traegt keine eigenen Zahlen, figma_plan.py
auch nicht — so koennen PDF und Figma-Frame nicht auseinanderlaufen.
"""
import json
from functools import lru_cache
from pathlib import Path

from markupsafe import Markup

ASSETS = Path(__file__).resolve().parent.parent / "assets"


@lru_cache(maxsize=1)
def laden():
    """tokens.json samt der Masse, die sich aus ihr ergeben.

    Abgeleitet wird hier und nicht im CSS: WeasyPrint wirft calc() an manchen
    Stellen kommentarlos weg (margin-left, flex-Kurzschreibweise), und der
    Figma-Plan braucht dieselben Zahlen ohnehin fertig ausgerechnet.
    """
    t = json.loads((ASSETS / "tokens.json").read_text(encoding="utf-8"))
    s, r = t["seite"], t["raster"]
    inhalt = s["breite"] - s["rand_links"] - s["rand_rechts"]              # 428
    einzug = r["logospalte"] + r["logoabstand"]                             # 120
    t["abgeleitet"] = {
        "inhaltsbreite": inhalt,
        # Der Footer ist breiter als der Satzspiegel (in Figma 475 statt 428pt).
        # Damit nichts ueber den Seitenrand ragt — Chrome verkleinert sonst die
        # ganze Seite, bis es passt —, ist der Druckbereich so breit wie der
        # Footer, und alles andere steht in 428pt darin.
        "rand_rechts_druck": s["breite"] - s["rand_links"] - r["fuss_breite"],
        "einzug": einzug,
        "inhaltsspalte": inhalt - einzug,                                   # 308
        "halbe_spalte": round((inhalt - r["spaltenabstand"]) / 2, 2),       # 202
        "fuss_spalte": round((r["fuss_block"] - 2 * r["fuss_spaltenabstand"]) / 3, 2),
    }
    return t


def pt(wert):
    """12 -> '12pt', -0.05 -> '-0.05pt', 0 -> '0'."""
    if not wert:
        return "0"
    zahl = f"{float(wert):.3f}".rstrip("0").rstrip(".")
    return f"{zahl}pt"


def stil(name):
    """Ein Textstil aus tokens.json, Farbe als Hex und Figma-Schnitt aufgeloest."""
    t = laden()
    s = dict(t["text"][name])
    s["farbe"] = s.get("farbe", "text")
    s["farbe_hex"] = t["farben"][s["farbe"]]
    s["figma_schnitt"] = t["schriften"][s["schrift"]]["figma"][str(s["gewicht"])]
    return s


def css(name):
    """Die CSS-Deklarationen eines Textstils, zum Einsetzen in cv.css.

    Die Zeilenhoehe steht in pt und nicht als Faktor: Figma rundet sie auf ganze
    Punkt, und nur als fester Wert setzen WeasyPrint und Chrome sie gleich.
    """
    s = stil(name)
    teile = [f'font-family: "{s["schrift"]}"', f'font-weight: {s["gewicht"]}',
             f'font-size: {pt(s["groesse"])}', f'line-height: {pt(s["zeile"])}',
             f'letter-spacing: {pt(s["laufweite"])}', f'color: {s["farbe_hex"]}']
    if s.get("versalien"):
        teile.append("text-transform: uppercase")
    return Markup("; ".join(teile) + ";")


def grundlinie(name):
    """Wie weit die Schriftlinie unter der Oberkante ihrer Zeile steht, in pt.

    CSS und Figma verteilen den Durchschuss gleich auf oben und unten. Daran
    misst der Selbsttest nach, ob ein Abstand im PDF wirklich dem aus
    tokens.json entspricht.
    """
    s = stil(name)
    m = laden()["schriften"][s["schrift"]]
    hoehe = (m["oben"] + m["unten"]) * s["groesse"]
    return (s["zeile"] - hoehe) / 2 + m["oben"] * s["groesse"]


def postscript(name):
    """Der Schriftname, unter dem ein Stil im PDF eingebettet ist.

    Die Dateien in assets/fonts heissen wie ihr PostScript-Name
    (Inter-Bold.ttf -> Inter-Bold); WeasyPrint bettet sie unter diesem Namen ein.
    """
    s = stil(name)
    datei = laden()["schriften"][s["schrift"]]["dateien"][str(s["gewicht"])]
    return Path(datei).stem


def jinja_globals():
    """Was cv.css beim Rendern braucht: die Tokens und die beiden Helfer."""
    t = laden()
    return {
        "tok": t, "pt": pt, "css": css,
        "f": t["farben"], "r": t["raster"], "a": t["abstand"], "ab": t["abgeleitet"],
        "dn": t["verdichtung"]["deckblatt"]["normal"],
        "sn": t["verdichtung"]["stationen"]["normal"],
    }
