#!/usr/bin/env python3
"""Baut aus portfolio.json das fertige PDF im New-Monday-Portfolio-Layout.

    python3 render_portfolio.py portfolio.json ausgabe/nachname-vorname-portfolio.pdf

Das Skript sucht sich die Render-Engine selbst (WeasyPrint, sonst headless
Chrome) und prueft danach das erzeugte PDF auf Ueberlauf: Text, der aus seiner
Flaeche laeuft, faellt in einem Folienlayout nicht von selbst auf, weil nichts
umbricht - er verschwindet unter dem Bild, unter der Blattkante oder auf der
Folgeseite, wo ihn der Beschnitt der Folie unsichtbar macht.

Die gerechneten Screenflaechen sind Arbeitsdateien und liegen deshalb in
`arbeit/screens/` neben der portfolio.json, nicht im Ausgabeordner: der wird
weitergereicht, und ein Zwischenspeicher von einigen Dutzend Megabyte ginge
sonst mit. Der Ordner darf jederzeit geloescht werden - er baut sich neu auf.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_tokens as ds  # noqa: E402
import screens  # noqa: E402
from logo_lib import bibliothek  # noqa: E402
from screens import baue_screens  # noqa: E402

# ── Feste Angaben von New Monday ─────────────────────────────────────────
# Diese Werte stehen nicht im Kandidatenmaterial, sondern gehoeren der Agentur.
# Sie hier zu pflegen ist ein bewusster Vorgang - deshalb stehen sie an einer
# Stelle und nicht verstreut im Template.
AGENTUR = {
    "teammitglieder": "26",
    "gegruendet": "2018",
    "zufriedenheit": "100%",
    "badge": ["Best 2026", "Nominated", "UX Design Agency"],
}
ANSPRECHPARTNER = {
    "name": "Manuel Klein",
    "titel_de": ["Chief Commercial Officer (CCO)", "Business Development"],
    "titel_en": ["Chief Commercial Officer (CCO)", "Business Development"],
    "mail": "manuel.klein@newmonday.co",
    "telefon": "+49 (0) 155 11480130",
    "foto": "kontakt/ansprechpartner.jpg",
}
FIRMA = {
    "name": "New Monday GmbH",
    "strasse": "Stresemannstr. 23",
    "ort": "10963 Berlin",
    "mail": "hallo@newmonday.co",
    "web": "www.newmonday.co",
}

TEXTE = {
    "de": {
        "kunden": "Meine Kunden", "prozess": "Mein Design Prozess",
        "arbeitsweise": "Arbeitsweise", "projekte": "Meine Projekte",
        "kontakt": "Kontakt",
        "agentur_h": "Ich bin Teil der\nNew Monday Agentur.",
        "agentur_sub": "Seit 2018 verlängern 100% unserer Kunden ihre Projekte mit uns.",
        "team": "Teammitglieder", "gegruendet": "Gegründet",
        "zufriedenheit": "Kundenzufriedenheit",
        "top": "Top-Kenntnisse", "koennen": "Kenntnisse",
        "erfahrung": "Arbeitserfahrung", "jahre": "Jahre",
        "sprachen": "Sprachen", "connect": "Connect", "anzeigen": "Anzeigen",
        "ki": "KI-Einsatz",
        "projekt": "Projekt", "kunde": "Kunde", "meine_rolle": "Meine Rolle",
        "summary": "Summary", "loesung": "Die Lösung", "screens": "Screens",
        "aufruf_h": "Interessiert an einer Zusammenarbeit?",
        "aufruf_p": "Setzen Sie sich mit {name} in Verbindung, um ein Meeting zu "
                    "vereinbaren. In diesem Gespräch können Sie mehr über unsere "
                    "Arbeitsweise erfahren und gemeinsam die nächsten Schritte und "
                    "Details einer möglichen Zusammenarbeit besprechen.",
        "fragen_h": "Haben Sie weitere Fragen?",
        "fragen_p": "Ihr Ansprechpartner für Business Development & Commercial Strategy",
        "mail": "E-Mail", "telefon": "Telefon",
        "nda": "* Aus Datenschutzgründen zeigen wir nur eine Darstellung, "
               "die vom originalen Software-Layout und Inhalt abweicht.",
        "fehlt": "Bild fehlt",
    },
    "en": {
        "kunden": "My Clients", "prozess": "My Design Process",
        "arbeitsweise": "How I Work", "projekte": "My Projects",
        "kontakt": "Contact",
        "agentur_h": "I am part of the\nNew Monday agency.",
        "agentur_sub": "Since 2018, 100% of our clients have extended their projects with us.",
        "team": "Team members", "gegruendet": "Founded",
        "zufriedenheit": "Client satisfaction",
        "top": "Key skills", "koennen": "Skills",
        "erfahrung": "Experience", "jahre": "Years",
        "sprachen": "Languages", "connect": "Connect", "anzeigen": "View",
        "ki": "Use of AI",
        "projekt": "Project", "kunde": "Client", "meine_rolle": "My role",
        "summary": "Summary", "loesung": "The solution", "screens": "Screens",
        "aufruf_h": "Interested in working together?",
        "aufruf_p": "Get in touch with {name} to arrange a meeting. In this "
                    "conversation you can learn more about how we work and "
                    "discuss the next steps and details of a possible "
                    "collaboration together.",
        "fragen_h": "Any further questions?",
        "fragen_p": "Your contact for Business Development & Commercial Strategy",
        "mail": "Email", "telefon": "Phone",
        "nda": "* For data protection reasons we show a representation that "
               "deviates from the original software layout and content.",
        "fehlt": "Image missing",
    },
}

hinweise: list[str] = []


def merke(text: str) -> None:
    hinweise.append(text)


# ── Hilfen ───────────────────────────────────────────────────────────────

def e(text) -> str:
    return html.escape(str(text or ""))


def absaetze(text: str, klasse: str = "fliess", stil: str = "",
             ts: str = "subheadline-2-regular") -> str:
    """Leerzeilen im Quelltext werden zu Absaetzen, **fett** zu <b>. `ts` ist
    der Textstil aus tokens.json - ohne ihn stuende der Text in keiner Schrift
    des Design Systems."""
    if not text:
        return ""
    teile = [t.strip() for t in re.split(r"\n\s*\n", text.strip()) if t.strip()]
    body = "".join(f"<p>{fett(t)}</p>" for t in teile)
    attr = f' style="{stil}"' if stil else ""
    return f'<div class="{klasse} t-{ts}"{attr}>{body}</div>'


def fett(text: str) -> str:
    """**fett** gilt in jedem Textfeld - auch in kurzen Listeneintraegen.
    Sonst haengt es vom Feld ab, ob die Sternchen woertlich erscheinen, und das
    merkt beim Schreiben niemand."""
    text = e(text).replace("\n", " ")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def nuechtern(text: str) -> str:
    """**fett** entfernen statt setzen. Die KI-Folie ist die einzige Flaeche,
    auf der Halbfett im Fliesstext stoert - in den Referenzen steht sie
    durchgehend mager, und markierte Halbsaetze lasen sich dort wie
    Werbeclaims. Die Sternchen verschwinden, der Text bleibt. re.S, weil eine
    Fettmarke ueber einen Zeilenumbruch laufen darf - fett() normalisiert \\n
    vor dem Matchen, hier muss das Muster selbst darueber hinweg."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text or "", flags=re.S)


def datei_suchen(pfad, basis: Path) -> Path | None:
    """Pfade duerfen relativ zur JSON, zum Materialordner oder zum Skill stehen.
    `material/` und `material/logos/` gehoeren dazu, weil die JSON dort blosse
    Dateinamen fuehren darf - ohne sie findet ein weitergereichter Ordner seine
    eigenen Logos nur ueber die gemeinsame Bibliothek, also nur auf dem Rechner,
    auf dem auch der Lebenslauf-Skill liegt."""
    if not pfad:
        return None
    p = Path(str(pfad)).expanduser()
    for kandidat in (p, basis / p, basis / "material" / p,
                     basis / "material" / "logos" / p, ASSETS / p,
                     bibliothek() / p):
        if kandidat.exists():
            return kandidat.resolve()
    merke(f"Datei nicht gefunden: {pfad}")
    return None


def datei_uri(pfad, basis: Path) -> str | None:
    gefunden = datei_suchen(pfad, basis)
    return gefunden.as_uri() if gefunden else None


def uri_pfad(uri: str) -> Path:
    """Vom file:-URI zurueck zum Pfad. Ein Leerzeichen im Ordnernamen steht dort
    als %20 - blosses Abschneiden von "file://" liefert eine tote Datei."""
    return Path(url2pathname(urlparse(uri).path))


def seitenverhaeltnis(uri: str) -> float:
    """Breite/Hoehe einer Bild- oder SVG-Datei. 1.0, wenn unlesbar."""
    pfad = uri_pfad(uri)
    try:
        if pfad.suffix.lower() == ".svg":
            kopf = pfad.read_text(errors="ignore")[:2000]
            m = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', kopf)
            if m:
                return float(m.group(1)) / float(m.group(2))
            mb = re.search(r'width="([\d.]+)"[^>]*height="([\d.]+)"', kopf)
            if mb:
                return float(mb.group(1)) / float(mb.group(2))
            return 1.0
        from PIL import Image
        with Image.open(pfad) as im:
            return im.width / im.height
    except Exception:
        return 1.0


def helligkeit(farbe: str) -> float:
    """Relative Helligkeit nach WCAG, 0 bis 1. Fehlerhafte Angaben gelten als
    Weiss - eine unlesbare Farbe soll nicht auch noch die Schrift verstellen."""
    f = (farbe or "#ffffff").lstrip("#")
    if len(f) == 3:
        f = "".join(c * 2 for c in f)
    try:
        r, g, b = (int(f[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return 1.0
    lin = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def hell(farbe: str) -> bool:
    """Gilt die Flaeche als hell? Die Schwelle liegt hoch, weil sie ueber die
    ganze Seite entscheidet (Markenfarbe, Streifen, Platzhalter) und ein knapp
    dunkler Grund dort noch weisse Schrift traegt."""
    return helligkeit(farbe) > 0.36


# Die Folie in Punkt, und die Breite der Bildflaeche je Seitentyp. Alle
# Flaechen stehen rechtsbuendig und ueber die volle Hoehe.
SEITE_BREIT, SEITE_HOCH = 1920, 1080
# Bildkanten wie in Figma: Arbeitsweise 1122pt, Summary/Loesung 932pt.
FLAECHENBREITE = {"bild--halb": 798, "bild--breit": 988, "vollflaeche": 1920}
BILDKANTE_HALB = SEITE_BREIT - FLAECHENBREITE["bild--halb"]
BILDKANTE_BREIT = SEITE_BREIT - FLAECHENBREITE["bild--breit"]

# Ab dieser Helligkeit liest Schwarz besser als Weiss: bei 0,18 sind beide
# WCAG-Kontraste gleich (rund 4,6:1). Die Schwelle von hell() taugt dafuer
# nicht - zwischen 0,18 und 0,36 setzte sie Weiss auf Himmel und Glasfassaden,
# und genau dort liegen die HQ-Fotos (0,20 bis 0,30).
TINTENWECHSEL = 0.18
# Auf den Screenflaechen liegen Wortmarke und Seitenzahl auf satter
# Markenfarbe (screens.py haelt ihre Felder frei). Dort gilt die Regel der
# Referenzen, nicht die WCAG-Mitte: Weiss auf Petrol, Blau, Magenta und selbst
# auf Orange (#f07d00, Luminanz 0,36) - Schwarz erst auf hellen Toenen.
MARKE_TINTENWECHSEL = 0.40

# Wo Wortmarke und Seitenzahl auf der Folie liegen, in Folienpunkten und mit
# etwas Luft: Wortmarke 148x15pt auf 1712/60, Seitenzahl im 66x43pt-Feld der
# Figma-Komponente slideNumber auf 1832/1003 (so steht beides im CSS).
# Gemessen wird genau dieses Feld - eine ganze Bildecke mittelt Himmel und
# Fassade zusammen und entscheidet dann fuer eine Stelle, an der nichts steht.
MOEBELFELD = {True: (1700, 48, 1872, 88), False: (1832, 1003, 1898, 1046)}

# Der Verlauf aus .bildschatten, Werte aus tokens.json (Figma: 298pt hoch,
# unten 20 % Schwarz). Er liegt auf den Arbeitsweise-Seiten ueber dem Motiv
# und macht die Seitenzahl-Ecke dunkler, egal wie hell das Foto ist. Wer ihn
# nicht mitrechnet, misst das falsche Bild.
_verlauf = ds.laden()["verlaeufe"]["bildschatten"]
SCHATTEN_HOCH, SCHATTEN_TIEF = float(_verlauf["hoehe"]), float(_verlauf["bis"])

# Ab welchem Anteil widersprechender Pixel das Moebelfeld als gescheckt gilt,
# und ab welcher Helligkeit ein Pixel widerspricht. Das Feld ist breiter als die
# Schrift darin, ein Drittel Widerspruch traegt die Wortmarke also noch:
# arbeitsweise-4 kommt auf 31 % und steht im PDF sauber auf dem dunklen Teil.
# Erst wo das Feld etwa halb und halb liegt, geht Schrift verloren.
FELD_UNRUHE, HELL_GRENZE, DUNKEL_GRENZE = 0.40, 150, 100


def ecke_dunkel(uri: str | None, oben: bool, klasse: str = "bild--breit",
                schatten: bool = False,
                schwelle: float = TINTENWECHSEL) -> bool | None:
    """Braucht die Wortmarke (oben) bzw. die Seitenzahl (unten) weisse Schrift?
    In den Vorlagen wechselt beides von Projektseite zu Projektseite mit dem
    Motiv. None heisst: nicht messbar - dann entscheidet der Aufrufer.

    `klasse` sagt, in welcher Flaeche das Motiv steht. Die Flaechen sind
    `object-fit: cover` und rechtsbuendig: gemessen werden muss, was auf der
    Folie zu sehen ist, nicht was in der Datei liegt - sonst entscheidet ein
    abgeschnittener Bildrand mit. `schatten` rechnet den Verlauf mit."""
    if not uri:
        return None
    breite = FLAECHENBREITE.get(klasse, 1020)
    x0, y0, x1, y1 = MOEBELFELD[oben]
    links = SEITE_BREIT - breite
    try:
        from PIL import Image
        with Image.open(uri_pfad(uri)) as im:
            im = im.convert("RGB")
            w, h = im.size
            seitenmass = breite / SEITE_HOCH
            if w / h > seitenmass:                  # zu breit: Seiten fallen weg
                neu = max(1, round(h * seitenmass))
                rand = (w - neu) // 2
                im = im.crop((rand, 0, rand + neu, h))
            else:                                   # zu hoch: oben und unten
                neu = max(1, round(w / seitenmass))
                rand = (h - neu) // 2
                im = im.crop((0, rand, w, rand + neu))
            w, h = im.size
            eng = lambda v: max(0.0, min(1.0, v))
            u0, u1 = eng((x0 - links) / breite), eng((x1 - links) / breite)
            v0, v1 = eng(y0 / SEITE_HOCH), eng(y1 / SEITE_HOCH)
            feld = (int(u0 * w), int(v0 * h),
                    max(int(u0 * w) + 1, int(u1 * w)),
                    max(int(v0 * h) + 1, int(v1 * h)))
            klein = im.crop(feld).resize((8, 8))
        px = list(klein.getdata())
        mittel = [sum(k[i] for k in px) // len(px) for i in range(3)]
        tiefe = 0.0
        if schatten:
            tiefe = SCHATTEN_TIEF * eng(
                ((y0 + y1) / 2 - (SEITE_HOCH - SCHATTEN_HOCH)) / SCHATTEN_HOCH)
            mittel = [round(v * (1 - tiefe)) for v in mittel]
        dunkel = helligkeit("#%02x%02x%02x" % tuple(mittel)) <= schwelle
        # Der Mittelwert entscheidet richtig, verschweigt aber gescheckte Felder:
        # Liegt ein Teil des Motivs auf der falschen Seite, verschwindet dort ein
        # Stueck Wortmarke, ohne dass die Seite als Ganzes falsch aussieht. Das
        # loest keine Tinte, nur ein anderes Bild - also wird es gemeldet.
        stoerer = sum(1 for k in px
                      if (sum(k) / 3 * (1 - tiefe) > HELL_GRENZE if dunkel
                          else sum(k) / 3 * (1 - tiefe) < DUNKEL_GRENZE))
        if stoerer / len(px) > FELD_UNRUHE:
            merke(f"{uri_pfad(uri).name}: Das Motiv wechselt unter "
                  f"{'der Wortmarke' if oben else 'der Seitenzahl'} von hell auf "
                  f"dunkel – auf {stoerer / len(px):.0%} der Fläche trägt die "
                  "gewählte Schriftfarbe nicht. Anderes Bild wählen.")
        return dunkel
    except Exception:
        return None


# ── Bausteine ────────────────────────────────────────────────────────────

def logo_block(hell_grund: bool) -> str:
    datei = "marke/nm-logo-weiss.svg" if hell_grund else "marke/nm-logo.svg"
    return f'<div class="logo"><img src="{(ASSETS / datei).as_uri()}"></div>'


def seitenzahl(nr: int, hell_grund: bool = False) -> str:
    """Die Seitenzahl in der Schrift der Figma-Komponente slideNumber."""
    return (f'<div class="seitenzahl t-seitenzahl'
            f'{" seitenzahl--hell" if hell_grund else ""}">{nr}</div>')


def kopfzeile(bild, basis: Path, nr: int, klasse: str = "bild--breit",
              schatten: bool = False) -> str:
    """Wortmarke und Seitenzahl, je nach Motiv hell oder dunkel gesetzt.
    `klasse` und `schatten` beschreiben die Flaeche, in der das Motiv steht -
    erst damit misst ecke_dunkel das, was auf der Folie zu sehen ist."""
    uri = datei_uri(bild.get("datei") if isinstance(bild, dict) else bild, basis) if bild else None
    return (logo_block(ecke_dunkel(uri, True, klasse, schatten))
            + seitenzahl(nr, bool(ecke_dunkel(uri, False, klasse, schatten))))


def pruefe_aufloesung(uri: str, klasse: str, was: str) -> None:
    """Ein Bild sollte mindestens so viele Pixel breit sein wie seine Flaeche
    Punkte misst - die Folie ist 1920pt breit und wird auch so gezeigt. Darunter
    wird es sichtbar weich, und das faellt erst im fertigen PDF auf."""
    soll = FLAECHENBREITE.get(klasse, 960)
    try:
        from PIL import Image
        with Image.open(uri_pfad(uri)) as im:
            breite = im.width
    except Exception:
        return
    faktor = breite / soll
    if faktor < 1.0:
        merke(f"{was}: Bild ist mit {breite}px für die {soll}pt breite Fläche zu "
              f"klein ({faktor:.2f}×) – bessere Fassung anfragen.")


def bildflaeche(bild, klasse: str, basis: Path, t: dict,
                farbe: str | None = None, was: str = "", schatten=False) -> str:
    """Bildhaelfte. Fehlt das Bild, bleibt die Flaeche als Platzhalter stehen -
    das Raster bricht nicht und es ist sofort zu sehen, was nachzuliefern ist."""
    stil = f' style="background:{farbe}"' if farbe else ""
    schicht = ('<div class="bildschatten" style="left:0;right:0"></div>'
               if schatten else "")
    platzhalter = (f'<div class="bild {klasse} bild--platzhalter">'
                   f'<div class="hinweis t-subheadline-2-regular"><b>{e(t["fehlt"])}</b>'
                   f'{e(was)}</div></div>')
    if not bild:
        merke(f"Platzhalter gesetzt: {was}")
        return platzhalter
    quelle = bild.get("datei") if isinstance(bild, dict) else bild
    passung = bild.get("passung", "cover") if isinstance(bild, dict) else "cover"
    uri = datei_uri(quelle, basis)
    if not uri:
        return platzhalter
    pruefe_aufloesung(uri, klasse, was)
    return (f'<div class="bild {klasse}"{stil}>'
            f'<img src="{uri}" style="object-fit:{passung}">{schicht}</div>')


# Obergrenze fuer die Logogroesse auf der Kundenwand, in Punkt. Der Wert ist die
# Hoehe eines quadratischen Logos; breite Schriftzuege stehen entsprechend
# niedriger und breiter. Bis fuenf Logos stehen in einer Reihe: p-03 zeigt vier
# Logos nebeneinander, und eine Restzeile mit einem einzelnen Logo sieht nach
# Versehen aus. Die Reihe steht exakt im Referenzmass von p-03 (Paul Hecker):
# 160/128, Zellfaktor 0,46, Reihenmitte ~717pt - die Rueckmeldung dazu kam
# ausdruecklich mit Paul als Massstab.
#
# Seit dem Abgleich mit der Figma-Seite »Portfolio« (September 2026) folgt das
# dichte Raster deren Folie 3: Zeilen zu 100pt mit 60pt Luft ab y 471, 1579pt
# breit ab x 196, je Zeile bis zu sieben Logos von Kante zu Kante verteilt.
# Die Logogroessen dort entsprechen genau Mass 100 / Hoehe 80 / Breite 350
# (Union Investment 142 x 64, Porsche 348 x 23, SCA 61 x 80).
LOGO_MASS_MAX = 100
LOGO_HOEHE_MAX = 80
LOGO_BREITE_MAX = 350
WAND_LINKS, WAND_OBEN, WAND_BREIT, WAND_HOCH = 196, 471, 1579, 420
ZEILE_HOCH, ZEILE_LUFT, JE_ZEILE_MAX = 100, 60, 7
LOGO_LUFT_MIN = 40
LOGO_MASS_REIHE = 160
LOGO_HOEHE_REIHE = 128
# align-content: center setzt die Reihenmitte auf top + Hoehe/2. In p-03 liegt
# sie bei ~717pt; bei 640pt Wandhoehe ergibt das eine Oberkante von 397pt.
# Die eine Reihe (bis 5 Logos) steht bewusst weiter im Referenzmass von p-03 -
# die Figma-Seite zeigt diesen Fall nicht, und die Rueckmeldung „wie bei Paul"
# gilt fuer ihn.
REIHE_OBEN = 397


# Die Inhaltszone einer Folie, gegen die das fertige PDF geprueft wird: oberste
# und unterste erlaubte Textkante, rechte Kante, dazu der Rat, der bei Ueberlauf
# gemeldet wird. Der Rat gehoert zur Seite - "auf eine weitere Loesungsseite
# verteilen" ist auf der Kopfseite ein Irrweg, dort gibt es keine.
Zone = namedtuple("Zone", "oben unten rechts rat")
RAT_STD = "Text kürzen"


# ── Seiten ───────────────────────────────────────────────────────────────

def seite_cover(d, t, basis):
    p = d["person"]
    return f'''<section class="seite seite--cover">
  <img class="cover-logo" src="{(ASSETS / 'marke/nm-logo-weiss.svg').as_uri()}">
  <div class="kopf">
    <div class="titel t-h1">{e(p.get("cover_titel"))}</div>
    <div class="name t-h2">{e(p["name"])}</div>
    <div class="rolle t-h4-regular">{e(p.get("rolle"))}</div>
  </div>
  <div class="jahr t-cover-jahr">{e(p.get("jahr"))}</div>
</section>'''


def graues_foto(pfad: Path | None, cache: Path) -> str | None:
    """Das Profilfoto steht immer in Graustufen. Das CSS kann es nicht färben -
    WeasyPrint kennt kein filter: grayscale(), ein farbiges Foto aus der JSON
    kam deshalb farbig ins PDF. Entfärbt wird hier, einmal, in den
    Zwischenspeicher neben der portfolio.json."""
    if not pfad:
        return None
    try:
        from PIL import Image
        marke = hashlib.sha1(f"{pfad}:{pfad.stat().st_mtime_ns}".encode()).hexdigest()[:12]
        ziel = cache / f"foto-grau-{marke}.jpg"
        if not ziel.exists():
            with Image.open(pfad) as im:
                im.convert("L").convert("RGB").save(ziel, quality=92)
        return ziel.resolve().as_uri()
    except Exception as fehler:
        merke(f"Profilfoto nicht entfärbt ({fehler}) – es steht wie geliefert im PDF.")
        return pfad.as_uri()


# Die linke Spalte der Profilseite ist in Figma ein Auto-Layout: Name (H2),
# 8pt, Rolle (H4 Regular), 32pt, Top-Karte, 32pt, Kenntnisse-Karte. Jede Karte:
# Rand, Titel, Abstand, Inhalt, Rand - die Masse aus tokens.json, wie im CSS.
# Die Vorlage endet bei y 1041 - mit acht einzeiligen Kenntnissen und
# einzeiligen Top-Kenntnissen. Die Kontur der Karten zieht diese Kante
# sichtbar; was darunter laeuft, stoesst an den Folienrand, ohne dass Text
# ueberlaeuft - deshalb hier gemessen.
PROFIL_SPALTE_OBEN, PROFIL_SPALTE_UNTEN, PROFIL_ROLLE_ABSTAND = 120, 1041, 8
PROFIL_TEXTBREITE = 832


def profil_linke_spalte(p: dict) -> float:
    tk = ds.laden()
    masse, trenner = tk["masse"], tk["linien"]["trenner"]
    rand, abstand, stapel = masse["karte-innen"], masse["karte-abstand"], masse["stapel-abstand"]
    kartentext = PROFIL_TEXTBREITE - 2 * rand
    luecke = 2 * masse["trenner-luft"] + trenner["staerke"]

    def z(text, stil, breite):
        # So, wie fett() den Text setzt: Umbrueche werden Leerzeichen.
        text = str(text or "").replace("*", "").replace("\n", " ")
        s = ds.stil(stil)
        return zeilenzahl(text, breite, s["datei"], round(s["groesse"]),
                          -s["laufweite"]) if text.strip() else 0
    zeile = lambda stil: ds.stil(stil)["zeile"]
    karte = lambda inhalt: rand + zeile("karten-titel") + abstand + inhalt + rand
    unten = PROFIL_SPALTE_OBEN + z(p.get("name"), "h2", PROFIL_TEXTBREITE) * zeile("h2")
    rolle = z(p.get("rolle"), "h4-regular", PROFIL_TEXTBREITE)
    if rolle:   # eine leere Rolle ist ein leerer Block - sein Rand faellt weg
        unten += PROFIL_ROLLE_ABSTAND + rolle * zeile("h4-regular")
    unten += stapel
    if p.get("top_kenntnisse"):
        n = z(" • ".join(p["top_kenntnisse"]), "body-1-regular", kartentext)
        unten += karte(n * zeile("body-1-regular")) + stapel
        if n > 1:
            merke(f"Top-Kenntnisse brechen auf der Profilseite in {n} Zeilen um – "
                  "in der Vorlage stehen sie in einer (rund 70 Zeichen). Kürzere "
                  "Begriffe wählen.")
    liste = p.get("kenntnisse") or []
    zeilen = sum(z(k, "body-1-regular", kartentext) for k in liste)
    unten += karte(zeilen * zeile("body-1-regular") + luecke * max(0, len(liste) - 1))
    if unten > PROFIL_SPALTE_UNTEN + 0.5:
        merke(f"Profilseite: die Kenntnisse-Karte reicht bis y {unten:.0f}, in der "
              f"Vorlage endet sie bei {PROFIL_SPALTE_UNTEN}. Höchstens acht "
              "einzeilige Kenntnisse und die Top-Kenntnisse in einer Zeile – "
              "Einträge kürzen oder die schwächsten streichen.")
    return unten


# Sprachen: Vorgabe von New Monday (September 2026) - Deutsch ist immer
# Muttersprache, Englisch immer Business-Niveau, beide stehen immer auf der
# Profilseite, auch wenn das Material nichts dazu sagt. Weitere Sprachen
# kommen aus dem Material, mit ihrem eigenen Niveau.
SPRACH_VORGABE = {
    "de": [(("deutsch", "german"), "Deutsch", "Muttersprache"),
           (("englisch", "english"), "Englisch", "Business Niveau")],
    "en": [(("deutsch", "german"), "German", "Native speaker"),
           (("englisch", "english"), "English", "Business level")],
}


def sprachen_mit_vorgabe(liste: list | None, sprache: str) -> list[dict]:
    vorgabe = SPRACH_VORGABE.get(sprache, SPRACH_VORGABE["de"])
    rest = [dict(s) for s in (liste or []) if isinstance(s, dict) and s.get("sprache")]
    kopf = []
    for namen, anzeige, niveau in vorgabe:
        teile = lambda s: {t.strip().lower() for t in str(s["sprache"]).split(",")}
        einzeln = [s for s in rest if teile(s) <= set(namen)]
        # Eine zusammengefasste Zeile ("Deutsch, Italienisch" / "Muttersprache")
        # traegt die Sprache schon - sie bleibt, wie sie ist, an ihrer Stelle.
        gruppe = [s for s in rest if len(teile(s)) > 1 and teile(s) & set(namen)]
        alt = str((einzeln[0].get("niveau") if einzeln else "") or "").strip()
        if alt and alt.lower() != niveau.lower():
            merke(f"Sprachen: {anzeige} steht als „{niveau}“ (Vorgabe) – im Material "
                  f"stand „{alt}“.")
        kopf.append(gruppe[0] if gruppe else {"sprache": anzeige, "niveau": niveau})
        rest = [s for s in rest if s not in einzeln and s not in gruppe[:1]]
    return kopf + rest


def erfahrung_anzeige(wert) -> str:
    """Die Zahl auf der Karte „Arbeitserfahrung“ steht immer mit „+“ dahinter
    (Vorgabe von New Monday, September 2026 – wie im Beispiel „25+“). Eine
    reine Zahl bekommt es angehängt, ob als Text („10“, „ 10 “) oder als
    JSON-Zahl (10); aus „N+“ und „N +“ wird „N+“. Alle anderen Formen
    („über 10“, „10 Jahre“, „10+ Jahre“, „+10“) setzt das Skript wie
    geliefert – welche Zahl gemeint ist, kann es nicht entscheiden – und
    meldet sie. `erfahrung_jahre` sind volle Jahre, abgerundet."""
    if isinstance(wert, float) and wert.is_integer():
        wert = int(wert)
    text = str(wert if wert is not None else "").strip()
    if not text:
        return text
    m = re.fullmatch(r"([0-9]+)\s*\+?", text)
    if m:
        return f"{m.group(1)}+"
    merke(f"Profilseite: Arbeitserfahrung „{text}“ ist keine reine Zahl – gesetzt "
          "wie geliefert, ohne eigenes „+“. Als Zahl eintragen – volle Jahre, "
          "abgerundet (z. B. „10“) –, das „+“ ergänzt das Skript.")
    return text


def seite_profil(d, t, basis, nr, cache: Path):
    p = dict(d["person"])
    p["sprachen"] = sprachen_mit_vorgabe(p.get("sprachen"), d.get("sprache", "de"))
    foto = graues_foto(datei_suchen(p.get("foto"), basis), cache)
    foto_html = f'<img src="{foto}">' if foto else ""
    if not foto:
        merke("Profilfoto fehlt - die Fotofläche bleibt leer.")

    koennen = "".join(f'<li class="t-body-1-regular">{fett(k)}</li>'
                      for k in p.get("kenntnisse", []))
    sprachen = "".join(
        f'<div class="paar"><b class="t-body-1-bold">{e(s["sprache"])}</b>'
        f'<span class="t-body-1-regular">{e(s.get("niveau"))}</span></div>'
        for s in p.get("sprachen", []))
    # Connect wie in der Referenz (Paul Hecker, S. 2): der Titel selbst ist
    # der petrolfarbene Pfeil-Link - kein schwarzer Titel daruber, kein
    # "Anzeigen", keine Trennlinie. Diese Karte bleibt immer in diesem Muster,
    # auch gegen Figma V2 (Entscheidung vom September 2026).
    links = "".join(
        (f'<div class="paar paar--link"><a class="t-body-1-regular" href="{e(l["url"])}">'
         f'{e(l["titel"])} →</a></div>') if l.get("url") else
        f'<div class="paar paar--link"><span class="t-body-1-regular">{e(l["titel"])}</span></div>'
        for l in p.get("links", []))

    # Die rechte Spalte ist ein Stapel wie das Auto-Layout in Figma: Karten mit
    # 24pt Innenabstand, 32pt dazwischen, ab y 229. Die Hoehen folgen dem
    # Inhalt; geschaetzt wird nur, ob der Stapel aus der Folie laeuft.
    karten, hoehe = [], 0.0
    titel = lambda s: f'<h3 class="t-subheadline-1-bold">{e(s)}</h3>'
    jahre = erfahrung_anzeige(p["erfahrung_jahre"]) if p.get("erfahrung_jahre") else ""
    if jahre:
        karten.append(f'''<div class="pkarte">{titel(t["erfahrung"])}
      <div class="zahl t-h1">{e(jahre)}</div>
      <div class="fuss t-body-1-regular">{e(t["jahre"])}</div></div>''')
        hoehe += 246
    if sprachen:
        karten.append(f'<div class="pkarte">{titel(t["sprachen"])}{sprachen}</div>')
        # Sprachen werden nie gestrichen - bei Platznot gleiche Niveaus zu
        # einer Zeile zusammenfassen ("Deutsch, Italienisch" / "Muttersprache").
        hoehe += 104 + len(p.get("sprachen", [])) * 93 - 33
    if links:
        karten.append(f'<div class="pkarte">{titel(t["connect"])}{links}</div>')
        hoehe += 104 + len(p.get("links", [])) * 46 - 16
    hoehe += 32 * max(0, len(karten) - 1)
    # Unter dem Stapel steht ab y 1003 das Feld der Seitenzahl (x 1832-1898),
    # und die Karten reichen bis x 1860: Schluss ist deshalb 12pt darueber.
    if 229 + hoehe > 990:
        n_spr, n_link = len(p.get("sprachen", [])), len(p.get("links", []))
        merke(f"Profilseite: die rechte Kartenspalte reicht bis y {229 + hoehe:.0f} "
              f"und damit an die Seitenzahl (Schluss bei y 990) – "
              f"{n_spr} Sprache(n), {n_link} Link(s). Keine Sprache streichen: "
              "gleiche Niveaus zu einer Zeile zusammenfassen (\"Deutsch, "
              "Italienisch\" / \"Muttersprache\"). Reicht das nicht, beim "
              "Nutzer nachfragen, welcher Link entfallen darf (meist Xing).")

    # Die Karten links tragen eigene Titel (Inter Bold 24/150 %, in Figma ohne
    # Stil) und den Text in Body 1 - nicht die Titel der Panelkarten rechts.
    ktitel = lambda s: f'<h3 class="t-karten-titel">{e(s)}</h3>'
    top = ""
    if p.get("top_kenntnisse"):
        top = (f'<div class="karte karte--top">{ktitel(t["top"])}'
               f'<p class="t-body-1-regular">'
               f'{" • ".join(fett(k) for k in p["top_kenntnisse"])}</p></div>')
    profil_linke_spalte(p)
    return f'''<section class="seite seite--profil">
  <div class="foto">{foto_html}</div>
  <div class="inhalt">
    <div class="p-name t-h2">{e(p["name"])}</div>
    <div class="p-rolle t-h4-regular">{e(p.get("rolle"))}</div>
    <div class="skillset">{top}
      <div class="karte karte--koennen">{ktitel(t["koennen"])}
        <ul class="zeilen">{koennen}</ul></div></div>
  </div>
  <div class="panel"></div><div class="pstapel" style="top:229pt">{"".join(karten)}</div>
  {logo_block(True)}{seitenzahl(nr, True)}
</section>'''


def seite_kunden(d, t, basis, nr):
    # Ein Eintrag ist {"name": "Deutsche Bank", "logo": "deutsche-bank.svg"}.
    # Ein blanker String wird als Dateiname gelesen - so bleiben von Hand
    # gepflegte Listen weiter gültig.
    dateien = []
    for k in d.get("kunden", []):
        quelle = k.get("logo") if isinstance(k, dict) else k
        if not quelle:
            merke(f"Kein Logo für {k.get('name')} – Platz auf der Wand entfällt.")
            continue
        uri = datei_uri(quelle, basis)
        if uri:
            dateien.append(uri)
    # Bis fuenf Logos: eine Reihe im Referenzmass von p-03, tiefer gesetzt und
    # mit gleichmaessigen Luecken verteilt wie in der Referenz - feste Zellen
    # liessen zwei breite Wortmarken aneinanderkleben, waehrend daneben Luft
    # blieb. Darueber: das dichte Raster mit den gedeckelten Werten.
    reihe = len(dateien) <= 5
    kacheln = []
    if reihe and dateien:
        masse = []
        for uri in dateien:
            v = seitenverhaeltnis(uri)
            b = LOGO_MASS_REIHE * math.sqrt(v)
            h = b / v
            if h > LOGO_HOEHE_REIHE:
                h, b = LOGO_HOEHE_REIHE, LOGO_HOEHE_REIHE * v
            if b > 420:
                b, h = 420, 420 / v
            masse.append((uri, b, h))
        summe = sum(b for _, b, _ in masse)
        luecke = ((1605 - summe) / (len(masse) - 1)) if len(masse) > 1 else 0.0
        luecke = max(60.0, min(220.0, luecke))
        lead = max(0.0, (1605 - summe - luecke * (len(masse) - 1)) / 2)
        for i, (uri, b, h) in enumerate(masse):
            links = lead if i == 0 else luecke
            kacheln.append(
                f'<div class="kachel" style="width:{b:.1f}pt;height:640pt;'
                f'margin-left:{links:.1f}pt;padding-top:{(640 - h) / 2:.1f}pt">'
                f'<img src="{uri}" style="width:{b:.0f}pt;height:{h:.0f}pt"></div>')
    wand_stil = (f' style="left:193pt;top:{REIHE_OBEN}pt;width:1607pt;height:640pt"'
                 if reihe else "")
    if not reihe and dateien:
        kacheln = logoraster(dateien)
    if not kacheln:
        merke("Logowand „Meine Kunden“ ist leer - keine Kundenlogos zugeordnet.")
    return f'''<section class="seite seite--kunden">
  <div class="streifen streifen--weiter"></div>
  <div class="h1 t-h1">{e(t["kunden"])}</div>
  <div class="kundenwand{" kundenwand--reihe" if reihe else ""}"{wand_stil}>{"".join(kacheln)}</div>
  {logo_block(False)}{seitenzahl(nr)}
</section>'''


def logoraster(dateien: list[str]) -> list[str]:
    """Das dichte Raster der Kundenwand, wie auf Folie 3 der Figma-Seite
    »Portfolio«: Zeilen zu 100pt mit 60pt Luft, je Zeile bis zu sieben Logos,
    das erste an der linken, das letzte an der rechten Kante, die Luft
    dazwischen gleich (SPACE_BETWEEN in Figma). Die vorderen Zeilen tragen bei
    ungerader Menge eines mehr (19 Logos: 7 / 6 / 6 wie in Figma).

    Gerechnet wird jede Position selbst - WeasyPrint setzt justify-content
    nicht um, und die Logos hingen einmal linksbuendig in ihren Zellen: die
    „verschobenen" Logos einer Rueckmeldung."""
    n = len(dateien)
    zeilen = max(1, min(4, math.ceil(n / JE_ZEILE_MAX)))
    if zeilen == 4:
        # Vier Zeilen passen nur enger in das Band: 80pt Zeile, 33pt Luft.
        zeile_h, luft = 80.0, (WAND_HOCH - 4 * 80) / 3
    else:
        zeile_h, luft = float(ZEILE_HOCH), float(ZEILE_LUFT)
    block = zeilen * zeile_h + (zeilen - 1) * luft
    oben = (WAND_HOCH - block) / 2           # wenige Zeilen: mittig im Band
    basis_n, rest = divmod(n, zeilen)
    mengen = [basis_n + (1 if i < rest else 0) for i in range(zeilen)]
    hoehe_max = min(LOGO_HOEHE_MAX, zeile_h - 20)
    raus, start = [], 0
    for z, k in enumerate(mengen):
        masse = []
        for uri in dateien[start:start + k]:
            # Gleiche Flaeche statt gleicher Hoehe: ueber die Hoehe skaliert
            # wirkt eine kompakte Bildmarke doppelt so schwer wie ein breiter
            # Schriftzug. Hoehe und Breite zusaetzlich gedeckelt.
            v = seitenverhaeltnis(uri)
            b = LOGO_MASS_MAX * math.sqrt(v)
            h = b / v
            if h > hoehe_max:
                h, b = hoehe_max, hoehe_max * v
            if b > LOGO_BREITE_MAX:
                b, h = LOGO_BREITE_MAX, LOGO_BREITE_MAX / v
            masse.append([uri, b, h])
        start += k
        # Passt die Zeile nicht mit Mindestluft, schrumpfen alle Logos der
        # Zeile gleichmaessig - lieber kleiner als uebereinander.
        summe = sum(b for _, b, _ in masse)
        platz = WAND_BREIT - (k - 1) * LOGO_LUFT_MIN
        if summe > platz:
            f = platz / summe
            for m in masse:
                m[1], m[2] = m[1] * f, m[2] * f
            summe = platz
        lucke = (WAND_BREIT - summe) / (k - 1) if k > 1 else 0
        x = 0.0 if k > 1 else (WAND_BREIT - summe) / 2
        bilder = []
        for uri, b, h in masse:
            bilder.append(f'<img src="{uri}" style="left:{x:.1f}pt;'
                          f'top:{(zeile_h - h) / 2:.1f}pt;width:{b:.0f}pt;height:{h:.0f}pt">')
            x += b + lucke
        raus.append(f'<div class="logozeile" style="top:{oben + z * (zeile_h + luft):.1f}pt;'
                    f'height:{zeile_h:.0f}pt">{"".join(bilder)}</div>')
    return raus


def seite_statement(d, t, basis, nr):
    p = d["person"]
    st = p.get("statement") or {}
    text = st.get("text", "")
    if not text:
        merke("Statement auf Seite 4 fehlt - die Fläche bleibt leer.")
    if st.get("zitat") and text and not text.startswith("»"):
        text = f"»{text}«"
    rolle = e(p.get("statement_rolle") or p.get("rolle", "")).replace("\n", "<br>")
    return f'''<section class="seite seite--statement">
  <div class="streifen streifen--weiter"></div>
  <div class="halb-rechts"></div>
  <div class="aussage t-h2-regular">{fett(text)}</div>
  <div class="rolle h1 t-h1">{rolle}</div>
  {logo_block(False)}{seitenzahl(nr)}
</section>'''


def seite_divider(titel):
    zeilen = e(titel).replace("\n", "<br>")
    return f'''<section class="seite seite--divider">
  <div class="h1 t-h1">{zeilen}</div>{logo_block(True)}
</section>'''


# Die Prozessseite traegt drei oder vier Schritte (Entscheidung September 2026,
# Figma zeigt vier): Spalten zu 350pt im 414-pt-Takt ab x 193.
PROZESS_MIN, PROZESS_MAX, PROZESS_TAKT = 3, 4, 414


def seite_prozess(d, t, basis, nr):
    """Die Prozess-Uebersicht mit drei oder vier Spalten im Raster der
    Figma-Seite. „KI-Einsatz" ist nie eine davon: Eine fruehere Fassung haengte
    ihn als Spalte an, sobald die KI-Folie existierte, und genau das kam
    zurueck - KI ist Teil jeder Phase, kein Schritt nach der Umsetzung. Die
    KI-Folie bleibt eine eigene Arbeitsweise-Seite, kein Prozessschritt."""
    eintraege = [(s["titel"], s.get("kurztext", ""))
                 for s in d.get("prozess", [])[:PROZESS_MAX]]
    spalten = "".join(
        f'<div class="prozess-spalte" style="left:{193 + i * PROZESS_TAKT}pt;">'
        f'<div class="balken"></div>'
        f'<h2 class="t-h4">{e(titel).replace(chr(10), "<br>")}</h2>'
        f'<p class="t-body-1-regular">{fett(kurztext)}</p></div>'
        for i, (titel, kurztext) in enumerate(eintraege))
    return f'''<section class="seite seite--prozess">
  <div class="streifen streifen--start"></div>
  <div class="eyebrow t-eyebrow">{e(t["prozess"])}</div>
  {spalten}
  {logo_block(False)}{seitenzahl(nr)}
</section>'''


# Die Ueberschrift der Arbeitsweise-Seiten steht auf 181pt und laeuft im Stil
# h1 (Rethink Sans SemiBold 96pt, Zeilenhoehe 108 %). Der Fliesstext beginnt
# 80pt unter ihrer letzten Zeile - so steht es in Figma (Folien 7-9), und ein
# fester Textbeginn kollidierte ab zwei Zeilen mit der Ueberschrift.
KOPF_STIL = "h1"
KOPF_OBEN, KOPF_ABSTAND, KOPF_BREITE = 181, 80, 807
KOPF_GRAD = int(ds.stil(KOPF_STIL)["groesse"])
KOPF_ZEILE = ds.stil(KOPF_STIL)["zeilenfaktor"]
# Ab der vierten Zeile rueckt der Fliesstext zu tief und laeuft in die
# Schrittleiste. Drei Zeilen sind die Grenze.
KOPF_MAX_ZEILEN = 3
# Unterkante der Textzone auf den Arbeitsweise-Seiten: darunter liegt die
# Schrittleiste (Balken bei 955pt).
ARBEIT_UNTEN = 940
# Die Projektueberschrift der Kopfseite: 1300pt breit ab y 243 wie in Figma
# (32pt unter dem 91pt hohen Logofeld), die Spalten 80pt unter ihr.
KOPF_PROJEKT, PROJEKT_KOPF_OBEN, PROJEKT_SPALTEN_ABSTAND = 1300, 243, 80
_schriften: dict = {}


def schriftmass(datei: str, grad: int):
    """Die Schriftdatei selbst, gecacht. Gemessen statt geschaetzt: ein
    uebersehener Umbruch schiebt den Text um eine ganze Zeile."""
    if (datei, grad) not in _schriften:
        try:
            from PIL import ImageFont
            _schriften[(datei, grad)] = ImageFont.truetype(
                str(ASSETS / "fonts" / datei), grad)
        except Exception:
            _schriften[(datei, grad)] = None
    return _schriften[(datei, grad)]


def zeilenzahl(text: str, breite: float, datei: str, grad: int,
               laufweite: float = 0.0) -> int:
    """Wie viele Zeilen der Text im Kasten belegt. Weiche Trenner
    ("Konzept-\\nentwicklung") brechen hart um."""
    schrift = schriftmass(datei, grad)

    def breit(stueck: str) -> float:
        if schrift is None:
            # Notnagel ohne PIL: gemessener Mittelwert je Zeichen.
            return len(stueck) * (grad * 0.55 - laufweite)
        return schrift.getlength(stueck) - laufweite * len(stueck)

    zeilen = 0
    for teil in str(text).split("\n"):
        zeilen += 1
        stand = ""
        for wort in teil.split():
            probe = f"{stand} {wort}".strip()
            if stand and breit(probe) > breite:
                zeilen, stand = zeilen + 1, wort
            else:
                stand = probe
            # Ein Wort, das allein nicht in den Kasten passt, bricht mitten im
            # Wort um (overflow-wrap: break-word). Ohne diesen Schritt zaehlt
            # eine lange Fuegung wie "Anforderungsaufnahme" eine Zeile zu wenig
            # - und genau die schiebt den Fliesstext in die Schrittleiste.
            while len(stand) > 1 and breit(stand) > breite:
                k = 1
                while k < len(stand) and breit(stand[:k + 1]) <= breite:
                    k += 1
                zeilen, stand = zeilen + 1, stand[k:]
    return max(1, zeilen)


def kopfzeilen(titel: str, breite: float = KOPF_BREITE, grad: int = KOPF_GRAD) -> int:
    """Zeilen der Ueberschrift - gemessen mit derselben Schriftdatei und
    Laufweite, die tokens.json fuer den Stil h1 fuehrt. Die Laufweite ist dort
    ein Anteil des Grades (-0,3 %) und schrumpft mit verkleinerten Graden mit."""
    s = ds.stil(KOPF_STIL)
    return zeilenzahl(titel, breite, s["datei"], grad, -s["laufweite_anteil"] * grad)


def kopfmass(titel: str) -> tuple[int, int]:
    """Schriftgrad und Zeilenzahl der Arbeitsweise-Ueberschrift. Ein
    viergliedriger Titel laeuft bei 96pt in die Schrittleiste und ueber den
    Fliesstext. Kuerzen kann das Skript nicht, ohne Inhalt zu verlieren -
    also wird die Ueberschrift verkleinert, bis sie in drei Zeilen passt."""
    for grad in (KOPF_GRAD, 84, 72, 64):
        zeilen = kopfzeilen(titel, KOPF_BREITE, grad)
        if zeilen <= KOPF_MAX_ZEILEN:
            if grad != KOPF_GRAD:
                merke(f"Überschrift „{titel.replace(chr(10), ' ')}“ braucht bei "
                      f"96pt {kopfzeilen(titel)} Zeilen – gesetzt wird sie mit "
                      f"{grad}pt. Kürzer wäre besser.")
            return grad, zeilen
    zeilen = kopfzeilen(titel, KOPF_BREITE, 64)
    merke(f"Überschrift „{titel.replace(chr(10), ' ')}“ bleibt auch mit 64pt "
          f"{zeilen}-zeilig – der Fließtext rückt entsprechend nach unten. "
          "Titel kürzen oder mit „-\\n“ trennen.")
    return 64, zeilen


def textkante(zeilen: int, grad: int = KOPF_GRAD) -> float:
    return KOPF_OBEN + zeilen * grad * KOPF_ZEILE + KOPF_ABSTAND


# Die Schrittleiste der Arbeitsweise-Seiten: drei Balken zu 323pt bei
# x 193 / 678 / 1162, wie in Figma (Folien 7-9).
SCHRITT_LINKS, SCHRITT_BREIT = (193, 678, 1162), 323


def schrittleiste(schritte, t, aktiv: int) -> str:
    """Die Leiste zeigt, an welcher Stelle des Prozesses die Seite steht. Sie
    fuellt sich auf: die erste Seite hat einen Petrol-Balken, die dritte alle
    drei - kommende Schritte stehen weiss, auf der weissen Seite also
    unsichtbar, auf dem Bild sichtbar (so in Figma). Drei Balken, nicht vier,
    auch wenn die Prozessseite vier Schritte traegt: die Arbeitsweise-Seiten
    gibt es fuer die ersten drei. KI-Einsatz zaehlt nie als Schritt - eine
    fruehere Fassung zaehlte ihn als vierten Balken, und genau das kam
    zurueck. Der dritte Balken liegt auf dem Bild."""
    # Im Titel darf ein weicher Trenner stehen ("Konzept-\nentwicklung"),
    # damit die 96pt-Headline umbricht. In der Leiste steht das Wort ganz.
    namen = [e(s["titel"]).replace("-\n", "").replace(chr(10), " ")
             for s in schritte[:3]]
    balken = []
    for j, name in enumerate(namen):
        links = SCHRITT_LINKS[j]
        aufbild = links + SCHRITT_BREIT > BILDKANTE_HALB
        klassen = ("schritt" + (" ist" if j <= aktiv else "")
                   + (" aufbild" if aufbild else ""))
        balken.append(f'<div class="{klassen}" style="left:{links}pt">'
                      f'<div class="balken"></div><span class="t-body-1-bold">{name}</span></div>')
    return f'<div class="schritte">{"".join(balken)}</div>'


def seite_arbeitsweise(d, t, basis, nr, i):
    schritte = d.get("prozess", [])
    s = schritte[i]
    bild = (ASSETS / f"bilder/arbeitsweise-{i + 1}.jpg").as_uri()
    grad, zeilen = kopfmass(s["titel"])
    # Verkleinerte Grade laufen in derselben Schrift, nur der Grad wechselt -
    # der Stil bleibt h1, die Zeilenhoehe wandert als Anteil mit.
    gross = f' style="font-size:{grad}pt"' if grad != KOPF_GRAD else ""
    return f'''<section class="seite seite--arbeitsweise">
  <div class="streifen streifen--weiter"></div>
  <div class="bild bild--halb"><img src="{bild}">
    <div class="bildschatten" style="left:0;right:0"></div></div>
  <div class="eyebrow t-h6-regular">{e(t["arbeitsweise"])}</div>
  <div class="h1 t-{KOPF_STIL}"{gross}>{e(s["titel"]).replace(chr(10), "<br>")}</div>
  {absaetze(s.get("langtext", ""), stil=f"top:{textkante(zeilen, grad):.1f}pt")}
  {schrittleiste(schritte, t, i)}
  {kopfzeile(ASSETS / f"bilder/arbeitsweise-{i + 1}.jpg", basis, nr, "bild--halb", True)}
</section>'''


# Werkzeugreihe der KI-Seite. In p-10 stehen fuenf Kacheln zu 80pt im
# 102,4-pt-Takt, die Reihe misst so 489,6pt und endet auf 826pt. Sechs Kacheln
# passen noch in die Textspalte; darueber hinaus bleibt keine Zeile mehr frei,
# ohne die Schrittleiste zu erreichen.
WERKZEUG_LUFT, WERKZEUG_UNTEN = 22.4, 826.0
WERKZEUG_KLEIN, WERKZEUG_MAX = 80.0, 6


def werkzeugmass(anzahl: int) -> float:
    """Immer das Referenzmass von 80pt. Eine fruehere Fassung liess ein bis
    drei Kacheln auf 120pt wachsen - damit rueckte die Reihe hoeher und die
    Kacheln sassen sichtbar anders als in der Referenz: genau das kam als
    „verrutscht" zurueck. Wenige Kacheln stehen jetzt einfach als kurze Reihe
    am gewohnten Platz."""
    return WERKZEUG_KLEIN


def werkzeugreihe(ki, basis) -> tuple[str, float]:
    """Liefert die Reihe und die Unterkante der Textzone: mit Werkzeugen endet
    der Fliesstext ueber der Reihe, ohne sie erst ueber der Schrittleiste."""
    uris = []
    for werkzeug in ki.get("tools", []):
        uri = datei_uri(werkzeug, basis)
        if uri:
            uris.append(uri)
    if len(uris) > WERKZEUG_MAX:
        merke(f"{len(uris)} KI-Werkzeuge – gezeigt werden die ersten "
              f"{WERKZEUG_MAX}, mehr passen nicht über die Schrittleiste.")
        uris = uris[:WERKZEUG_MAX]
    if not uris:
        return "", ARBEIT_UNTEN
    mass = werkzeugmass(len(uris))
    breite = len(uris) * mass + (len(uris) - 1) * WERKZEUG_LUFT
    oben = WERKZEUG_UNTEN - mass
    # Gerechnetes Padding statt Flex-Zentrierung: WeasyPrint setzt
    # justify-content nicht um, und die Logos sassen sichtbar verschoben in
    # den Kacheln - genau die Rueckmeldung zur KI-Folie.
    rand = mass * 0.175
    kacheln = "".join(
        f'<div class="werkzeug" style="width:{mass:.1f}pt;height:{mass:.1f}pt;'
        f'border-radius:{mass * 0.0625:.1f}pt;padding:{rand:.1f}pt">'
        f'<img src="{uri}" style="width:{mass * .65:.1f}pt;height:{mass * .65:.1f}pt">'
        f'</div>' for uri in uris)
    return (f'<div class="werkzeuge" style="top:{oben:.1f}pt;'
            f'width:{breite:.1f}pt">{kacheln}</div>', oben - 11)


def seite_ki(d, t, basis, nr) -> tuple[str, float]:
    """Die KI-Seite haengt hinter den drei Arbeitsweise-Seiten, ist aber kein
    vierter Prozessschritt - KI laeuft in allen Phasen mit. Deshalb traegt sie
    keine Schrittleiste: eine fruehere Fassung zaehlte sie dort als vierten
    Balken, und genau das kam als Quatsch zurueck. Neu gegenueber den drei
    Prozessschritten ist die Reihe der Werkzeuge unter dem Text - sie belegt,
    womit gearbeitet wird, ohne dass der Text es aufzaehlen muss. Zurueck kommt
    mit der Seite ihre Textzone - wie tief der Text reichen darf, haengt an der
    Werkzeugreihe."""
    ki = (d.get("person") or {}).get("ki") or {}
    bild = (ASSETS / "bilder/arbeitsweise-4.jpg").as_uri()
    werkzeuge, zone = werkzeugreihe(ki, basis)
    return f'''<section class="seite seite--arbeitsweise seite--ki">
  <div class="streifen streifen--weiter"></div>
  <div class="bild bild--halb"><img src="{bild}">
    <div class="bildschatten" style="left:0;right:0"></div></div>
  <div class="eyebrow t-h6-regular">{e(t["arbeitsweise"])}</div>
  <div class="h1 t-{KOPF_STIL}">{e(t["ki"])}</div>
  {absaetze(nuechtern(ki.get("text", "")), stil=f"top:{textkante(1):.1f}pt")}
  {werkzeuge}
  {kopfzeile(ASSETS / "bilder/arbeitsweise-4.jpg", basis, nr, "bild--halb", True)}
</section>''', zone


def seite_agentur(d, t, basis, nr):
    b = AGENTUR["badge"]
    karte = lambda titel, zahl: (f'<div class="pkarte"><h3 class="t-subheadline-2-bold">'
                                 f'{e(titel)}</h3><div class="zahl t-h1">{zahl}</div></div>')
    return f'''<section class="seite seite--agentur">
  <div class="streifen streifen--weiter"></div>
  <div class="h1 t-h1">{e(t["agentur_h"]).replace(chr(10), "<br>")}</div>
  <div class="subline t-subheadline-2-regular">{e(t["agentur_sub"])}</div>
  <div class="kunden"><img src="{(ASSETS / 'marke/nm-agentur-kunden.png').as_uri()}"></div>
  <div class="badge"><img src="{(ASSETS / 'marke/ux-awards-badge.png').as_uri()}"></div>
  <div class="badge-text t-badge-text">{e(b[0])}<br>{e(b[1])}<br>{e(b[2])}</div>
  <div class="panel"></div>
  <div class="pstapel" style="top:278pt">{karte(t["team"], AGENTUR["teammitglieder"])}
    {karte(t["gegruendet"], AGENTUR["gegruendet"])}
    {karte(t["zufriedenheit"], AGENTUR["zufriedenheit"])}</div>
  {logo_block(True)}{seitenzahl(nr, True)}
</section>'''


# Kundenlogo der Projektseiten: flaechengleich skaliert wie auf der Wand,
# nicht auf feste Hoehe. Mit festen 61pt stand eine breite Wortmarke
# (norisbank) doppelt so wuchtig da wie eine kompakte Bildmarke - in der
# Referenz (p-13/18/23) wirken alle Logos gleich schwer: die Samsung-Wortmarke
# ~32pt hoch, das kompakte OSMR-Zeichen ~90pt. Das Mass ist daraus abgeleitet;
# die Deckel halten Extreme aus der 96-pt-Ueberschrift (ab 252pt) heraus.
LOGO_PROJEKT_MASS = 105
LOGO_PROJEKT_HOCH = 80
LOGO_PROJEKT_BREIT = 420


def kundenlogo(pr, basis):
    # "logo" nimmt einen Dateinamen oder eine Liste: Projekte mit mehreren
    # Auftraggebern (Postbank & FYRST, Opel/Peugeot/Citroen) fuehren alle
    # Marken nebeneinander, wie in den Showcases der Kandidaten.
    logos = pr.get("logo")
    if not isinstance(logos, list):
        logos = [logos] if logos else []
    imgs = []
    for eintrag in logos:
        uri = datei_uri(eintrag, basis)
        if not uri:
            continue
        v = seitenverhaeltnis(uri)
        b = LOGO_PROJEKT_MASS * math.sqrt(v)
        h = b / v
        if h > LOGO_PROJEKT_HOCH:
            h, b = LOGO_PROJEKT_HOCH, LOGO_PROJEKT_HOCH * v
        if b > LOGO_PROJEKT_BREIT:
            b, h = LOGO_PROJEKT_BREIT, LOGO_PROJEKT_BREIT / v
        imgs.append(f'<img src="{uri}" style="width:{b:.0f}pt;height:{h:.0f}pt">')
    if not imgs:
        merke(f"Kundenlogo fehlt: {pr.get('kunde')}")
        return ""
    return f'<div class="kundenlogo">{"".join(imgs)}</div>'


def marken_moebel(pr, t, nr: int, bild: Path | None, farbe: str | None,
                  klasse: str = "bild--breit") -> str:
    """Wortmarke, Seitenzahl und NDA-Hinweis auf der Screenflaeche. Gemessen
    wird die Ecke des fertigen Bildes, oben und unten getrennt: dort liegt mal
    ein dunkler Screenshot, mal die Markenflaeche, und die Markenfarbe allein
    sagt darueber nichts. Ist die Ecke nicht messbar, entscheidet sie doch -
    besser eine begruendete Annahme als weisse Schrift auf Gelb. screens.py
    haelt die Ecken frei, damit die Messung nicht auf einen Screenrand faellt.

    screens.py liefert die Flaeche heute schon im Mass ihrer Seite, `klasse`
    beschneidet also nichts. Sie steht trotzdem hier, damit die Messung nicht
    stillschweigend danebengreift, wenn sich eines der beiden Masse aendert.
    Einen Verlauf traegt keine der beiden Screenseiten."""
    uri = bild.resolve().as_uri() if bild else None
    ersatz = bool(bild) and not hell(farbe or "#ffffff")
    oben = ecke_dunkel(uri, True, klasse, schwelle=MARKE_TINTENWECHSEL)
    unten = ecke_dunkel(uri, False, klasse, schwelle=MARKE_TINTENWECHSEL)
    oben = ersatz if oben is None else oben
    unten = ersatz if unten is None else unten
    nda = (f'<div class="nda-hinweis nda-hinweis--{"hell" if unten else "dunkel"} t-hinweis">'
           f'{e(t["nda"])}</div>' if pr.get("nda") else "")
    return nda + logo_block(oben) + seitenzahl(nr, bool(unten))


def screens_meldungen() -> list[str]:
    """Meldungen von screens.py abholen und dort leeren. hole_hinweise() ist
    der dokumentierte Weg; aeltere Staende fuehren nur die Liste, die dann hier
    geleert wird - ungeleert zaehlte jede weitere Flaeche die alten mit."""
    holen = getattr(screens, "hole_hinweise", None)
    if callable(holen):
        return [str(h) for h in holen()]
    liste = getattr(screens, "hinweise", None)
    if not isinstance(liste, list):
        return []
    raus = [str(h) for h in liste]
    liste.clear()
    return raus


def screenflaeche(bilder, farbe, variante: str, basis: Path, cache: Path,
                  seed: int, was: str, nda: bool = False) -> Path | None:
    """Die markenfarbene Flaeche mit dem gekippten Screen-Raster. Das Rechnen
    kostet Sekunden, das Ergebnis haengt aber nur an den Rohbildern, der Farbe
    und dem Seed - deshalb traegt die Datei den Fingerabdruck ihrer Eingabe im
    Namen und ein zweiter Lauf greift sie einfach wieder ab."""
    pfade = []
    for b in bilder or []:
        gefunden = datei_suchen(b, basis)
        if gefunden:
            pfade.append(gefunden)
    if not pfade:
        return None
    # Der Stand des Anordnungs-Algorithmus gehoert in den Fingerabdruck: ohne
    # ihn liefert ein Zwischenspeicher von vor einer Layoutaenderung die alte
    # Anordnung weiter und spielt per Notiz auch deren alte Meldungen wieder ab.
    stand = str(getattr(screens, "LAYOUT_STAND", 1))
    marke = hashlib.sha1(
        "|".join([stand, variante, str(farbe), str(seed), str(bool(nda))]
                 + [f"{p}:{p.stat().st_mtime_ns}" for p in pfade]
                 ).encode()).hexdigest()[:16]
    ziel = cache / f"{variante}-{marke}.png"
    # Was screens.py zu dieser Flaeche gemeldet hat, liegt als Nebendatei
    # daneben: aus dem Zwischenspeicher kommt kein Neubau und damit auch keine
    # Meldung, und ein zweiter Lauf verschwiege sonst stumm die Doubletten und
    # die zu kleinen Screens, die der erste gefunden hat.
    notiz = cache / f"{variante}-{marke}.txt"
    # Welches Bildformat screens.py schreibt, entscheidet screens.py - gesucht
    # wird deshalb nach dem Fingerabdruck, nicht nach der Endung. Die Nebendatei
    # ist kein Ergebnis und bleibt aussen vor.
    fertig = sorted(p for p in cache.glob(f"{variante}-{marke}.*")
                    if p.suffix.lower() != ".txt")
    if fertig:
        if notiz.exists():
            for zeile in notiz.read_text(encoding="utf-8").splitlines():
                if zeile.strip():
                    merke(zeile)
        return fertig[0]
    try:
        gebaut = Path(baue_screens(pfade, farbe, ziel, variante=variante, seed=seed,
                                   nda=bool(nda)))
    except Exception as fehler:
        screens_meldungen()      # Angefangenes nicht der naechsten Flaeche anhaengen
        merke(f"Screenfläche für {was} nicht gebaut ({fehler}) – Platzhalter gesetzt.")
        return None
    neu = screens_meldungen()
    try:
        notiz.write_text("\n".join(neu), encoding="utf-8")
    except OSError:
        pass                     # Ohne Notiz meldet nur dieser Lauf - kein Grund abzubrechen
    for zeile in neu:
        merke(zeile)
    return gebaut


# Die Spalten der Kopfseite stehen wieder im Referenzmass: 575pt breit bei
# x 193 und x 916, wie in p-13/18/23 gemessen. Eine fruehere Fassung zog sie
# auf 693pt auseinander, weil „Meine Rolle" damals von der Blattkante nach oben
# wuchs und den Spalten Hoehe nahm. Genau dieser Block kam als Fehler zurueck -
# er klebte sichtbar am unteren Rand. Jetzt folgt er dem Textfluss der
# Projekt-Spalte wie in der Referenz, und die Spalten tragen das Referenzmass.

# Oberste erlaubte Textkante der Projektseiten: knapp ueber dem Kundenlogo auf
# 121pt. Es steht dort als Bild, kann aber Schrift enthalten - unter 121pt liegt
# auf diesen Seiten nichts Eigenes mehr, alles Hoehere kommt von der Vorseite.
PROJEKT_OBEN = 115


def seiten_projekt(pr, t, basis, nr, cache: Path):
    """Ein Projektblock: Kopf, Summary, bis zu zwei Loesungsseiten und die
    randlose Abschlussseite. Je Seite kommt ihre Inhaltszone zurueck - sie ist
    je Seitentyp verschieden, und mit ihr der Rat bei Ueberlauf."""
    out: list[tuple[str, Zone]] = []
    punkte_rolle = list(pr.get("rolle") or [])
    if len(punkte_rolle) > 3:
        merke(f'{pr.get("kunde")}: {len(punkte_rolle)} Einträge unter „Meine '
              "Rolle“ – dort stehen Rollenbezeichnungen, keine Aufgaben, und "
              "höchstens drei. Aufgaben gehören in den Projekttext.")
    rolle = "".join(f"<li>{fett(r)}</li>" for r in punkte_rolle)
    # Lange Kundennamen brechen um und schoeben die Labels sonst unter die
    # zweite Zeile ("Opel, Peugeot und Citroën").
    # Ueberschrift ist der Projektname, nicht der Kunde: der steht schon als
    # Logo darueber, und zwei Projekte beim selben Kunden waeren sonst nicht zu
    # unterscheiden. Fehlt er, traegt der Kundenname die Seite wie bisher.
    titel = pr.get("projektname") or pr.get("kunde") or ""
    kzeilen = kopfzeilen(titel, KOPF_PROJEKT)
    # Die Spalten beginnen 80pt unter der letzten Zeile der Ueberschrift - in
    # Figma ein Auto-Layout, ein zweizeiliger Projektname schiebt sie nach unten.
    spalten_oben = (PROJEKT_KOPF_OBEN + kzeilen * KOPF_GRAD * KOPF_ZEILE
                    + PROJEKT_SPALTEN_ABSTAND)
    # „Meine Rolle" steht im Fluss der Projekt-Spalte, direkt unter deren Text -
    # so sitzt der Block dort, wo der Text endet, wie in der Referenz
    # (p-13/18/23). Die alte Fassung liess ihn von der Blattkante nach oben
    # wachsen; bei kurzen Texten klebte er dann allein am unteren Rand.
    label = lambda s: f'<div class="label t-subheadline-1-bold">{e(s)}</div>'
    rolle_html = (f'<div class="rolle-block">{label(t["meine_rolle"])}'
                  f'<ul class="punkte t-subheadline-2-regular">{rolle}</ul></div>'
                  if rolle else "")
    out.append((f'''<section class="seite seite--projekt">
  <div class="streifen streifen--start"></div>
  {kundenlogo(pr, basis)}
  <div class="h1 t-h1">{e(titel)}</div>
  <div class="sp-projekt" style="top:{spalten_oben:.1f}pt">{label(t["projekt"])}
    {absaetze(pr.get("projekt", ""))}{rolle_html}</div>
  <div class="sp-kunde" style="top:{spalten_oben:.1f}pt">{label(t["kunde"])}
    {absaetze(pr.get("kunde_text", ""))}</div>
  {kopfzeile(None, basis, nr)}
</section>''', Zone(PROJEKT_OBEN, 1010, 1920,
                    '„projekt“ oder „kunde_text“ kürzen oder weniger '
                    '„rolle“-Stichpunkte – die Kopfseite hat keine Folgeseite')))
    nr += 1

    sm = pr.get("summary")
    if isinstance(sm, str):
        # Aeltere Dateien fuehren dort blossen Text. Der bekommt kein Bild,
        # aber auch keinen Absturz - hq_bilder.py faengt denselben Fall ab.
        merke(f'{pr.get("kunde")}: „summary“ ist Text statt Objekt – '
              'als {"text": …} gelesen, ein Bild fehlt dann.')
        sm = {"text": sm}
    elif not isinstance(sm, dict):
        sm = {}
    out.append((f'''<section class="seite seite--summary">
  <div class="streifen streifen--weiter"></div>
  {bildflaeche(sm.get("bild"), "bild--breit", basis, t,
               was=f'{pr.get("kunde", "")} – {t["summary"]}')}
  {kundenlogo(pr, basis)}
  <div class="h1 t-h1">{e(t["summary"])}</div>
  {absaetze(sm.get("text", ""))}
  {kopfzeile(sm.get("bild"), basis, nr)}
</section>''', Zone(PROJEKT_OBEN, 1010, BILDKANTE_BREIT - 12, '„summary.text“ kürzen')))
    nr += 1

    farbe = pr.get("markenfarbe")
    for k, lo in enumerate((pr.get("loesungen") or [])[:2]):
        was = f'{pr.get("kunde", "")} – {t["loesung"]}'
        bild = screenflaeche(lo.get("screens"), farbe, "panel", basis, cache, k, was,
                             nda=pr.get("nda"))
        punkte = "".join(f"<li>{fett(x)}</li>" for x in lo.get("punkte", []))
        out.append((f'''<section class="seite seite--loesung">
  <div class="streifen streifen--weiter"></div>
  {bildflaeche(bild, "bild--breit", basis, t, farbe=farbe, was=was)}
  {kundenlogo(pr, basis)}
  <div class="inhalt">
    <div class="einleitung t-subheadline-2-bold">{fett(lo.get("titel") or t["loesung"])}</div>
    {absaetze(lo.get("text", ""), ts="body-1-regular")}
    {f'<ul class="punkte t-body-1-regular" style="margin-top:30pt">{punkte}</ul>' if punkte else ""}</div>
  {marken_moebel(pr, t, nr, bild, farbe)}
</section>''', Zone(PROJEKT_OBEN, 1010, BILDKANTE_BREIT - 12,
                     "kürzen oder auf eine weitere Lösungsseite verteilen")))
        nr += 1

    # Eigener Seed, damit die Abschlussseite die Anordnung der Lösungsseiten
    # nicht wiederholt - dieselben Screens liegen sonst gleich.
    was = f'{pr.get("kunde", "")} – {t["screens"]}'
    voll = screenflaeche(pr.get("screens"), farbe, "voll", basis, cache, 9, was,
                         nda=pr.get("nda"))
    if voll:
        # Randlos und ohne Text - es bleiben Wortmarke, Seitenzahl und der
        # Hinweis, alle drei nach der Markenfarbe gesetzt.
        out.append((f'''<section class="seite seite--abschluss">
  <div class="vollflaeche"><img src="{voll.resolve().as_uri()}"></div>
  {marken_moebel(pr, t, nr, voll, farbe, "vollflaeche")}
</section>''', Zone(900, 1010, 1920, RAT_STD)))
        nr += 1
    else:
        merke(f'{pr.get("kunde")}: keine „screens" – die randlose Abschlussseite '
              "entfällt. Ohne Bildmaterial wäre sie eine leere Folie.")
    return out, nr


def seite_kontakt(d, t, basis, nr):
    a = ANSPRECHPARTNER
    titel = a["titel_de"] if d.get("sprache", "de") == "de" else a["titel_en"]
    # Die Box traegt wie in Figma nur Frage, E-Mail und Telefon - der fruehere
    # Satz zum Ansprechpartner stand dort nicht mehr (Abgleich September 2026).
    return f'''<section class="seite seite--kontakt">
  <div class="band"></div>
  <div class="adresse t-subheadline-2-regular">{e(FIRMA["name"])}<br>{e(FIRMA["strasse"])}<br>{e(FIRMA["ort"])}
    <br><br><a href="mailto:{e(FIRMA["mail"])}">{e(FIRMA["mail"])}</a>
    <br><a href="https://{e(FIRMA["web"])}">{e(FIRMA["web"])}</a></div>
  <div class="aufruf"><h2 class="t-h5">{e(t["aufruf_h"])}</h2>
    <p class="t-subheadline-2-regular">{e(t["aufruf_p"].format(name=a["name"]))}</p></div>
  <div class="box"><h3 class="t-subheadline-1-bold">{e(t["fragen_h"])}</h3>
    <div class="felder">
      <div><b class="t-body-1-bold">{e(t["mail"])}</b>
        <a class="t-body-1-regular" href="mailto:{e(a["mail"])}">{e(a["mail"])}</a></div>
      <div><b class="t-body-1-bold">{e(t["telefon"])}</b>
        <a class="t-body-1-regular" href="tel:{re.sub(r"[^+0-9]", "", a["telefon"])}">{e(a["telefon"])}</a></div>
    </div></div>
  <div class="person"><img src="{(ASSETS / a["foto"]).as_uri()}">
    <div class="name"><b class="t-person-name">{e(a["name"])}</b>
      <span class="t-person-rolle">{"<br>".join(e(x) for x in titel)}</span></div></div>
  {logo_block(False)}{seitenzahl(nr)}
</section>'''


# ── Aufbau ───────────────────────────────────────────────────────────────

def baue_html(d: dict, basis: Path, cache: Path) -> tuple[str, dict[int, Zone]]:
    """Liefert das HTML und je Seite die Inhaltszone fuer den Ueberlaufcheck.
    Die obere Kante steht dabei knapp ueber dem, was auf der Seite als Erstes
    stehen darf: was hoeher beginnt, ist Text der Vorseite."""
    # Eine unbekannte Sprache darf nicht mit KeyError enden - das Material ist
    # dann fertig, nur die Kennung falsch. Die geprüfte Kennung wandert zurueck
    # in die Daten, weil die Kontaktseite sie noch einmal liest.
    sprache = str(d.get("sprache") or "de").strip().lower()
    if sprache not in TEXTE:
        merke(f"Sprache „{d.get('sprache')}“ ist nicht hinterlegt – gesetzt "
              f"wird Deutsch. Möglich: {', '.join(TEXTE)}.")
        sprache = "de"
    d["sprache"] = sprache
    t = TEXTE[sprache]
    seiten: list[str] = []
    grenzen: dict[int, Zone] = {}

    def lege_ab(html_text: str, unten: float = 1010, rechts: float = 1920,
                oben: float | None = 95, rat: str = RAT_STD) -> None:
        seiten.append(html_text)
        grenzen[len(seiten)] = Zone(oben, unten, rechts, rat)

    def lege_zone(seite: tuple[str, Zone]) -> None:
        """Projektseiten bringen ihre Zone mit - sie haengt am Rolle-Block."""
        seiten.append(seite[0])
        grenzen[len(seiten)] = seite[1]

    # Farben und Schriften sind nur dann die des Design Systems, wenn
    # portfolio.css sie nicht selbst setzt - das prueft design_tokens.py.
    for befund in ds.pruefe():
        merke(f"Design System: {befund}")

    # Die oberen Kanten liegen gut 10pt ueber den Elementen: Rethink Sans hat
    # einen hoeheren Schriftkasten (1,3 Grad) als ihre Zeilenhoehe (1,08) - die
    # Glyphenbox einer 96-pt-Ueberschrift beginnt 10,6pt ueber ihrer Zeile.
    lege_ab(seite_cover(d, t, basis), oben=340)
    lege_ab(seite_profil(d, t, basis, len(seiten) + 1, cache), 1060, oben=100,
            rat="weniger „kenntnisse“ oder kürzere Einträge")
    lege_ab(seite_kunden(d, t, basis, len(seiten) + 1), 985, 1800, oben=135)
    lege_ab(seite_statement(d, t, basis, len(seiten) + 1), oben=265,
            rat='„statement.text“ kürzen')
    lege_ab(seite_divider(t["prozess"]), oben=330)
    lege_ab(seite_prozess(d, t, basis, len(seiten) + 1), 990, oben=112,
            rat='„prozess.kurztext“ kürzen')

    schritte = d.get("prozess", [])
    if not PROZESS_MIN <= len(schritte) <= PROZESS_MAX:
        merke(f"Der Design-Prozess hat {len(schritte)} Schritte – die Prozessseite "
              f"trägt {PROZESS_MIN} oder {PROZESS_MAX}"
              + (f", gezeigt werden die ersten {PROZESS_MAX}." if len(schritte) > PROZESS_MAX
                 else "."))
    ki = (d.get("person") or {}).get("ki") or {}
    if not ki.get("text"):
        merke("Ohne person.ki entfällt die Folie zum KI-Einsatz – "
              "Text und Werkzeuge nachtragen.")
    for i in range(min(3, len(schritte))):
        # Unterhalb von 940pt liegt die Schrittleiste; Text darf da nicht hin.
        lege_ab(seite_arbeitsweise(d, t, basis, len(seiten) + 1, i),
                ARBEIT_UNTEN, BILDKANTE_HALB, oben=112, rat='„prozess.langtext“ kürzen')
    if ki.get("text"):
        # Mit Werkzeugreihe endet die Textzone schon über deren Oberkante -
        # wo genau, weiß nur die Seite selbst.
        aufbau, unten = seite_ki(d, t, basis, len(seiten) + 1)
        lege_ab(aufbau, unten, BILDKANTE_HALB, oben=112, rat='„person.ki.text“ kürzen')

    lege_ab(seite_agentur(d, t, basis, len(seiten) + 1), oben=100)
    lege_ab(seite_divider(t["projekte"]), oben=330)

    projekte = d.get("projekte", [])
    if not 3 <= len(projekte) <= 5:
        merke(f"{len(projekte)} Projekte – die Vorlage ist auf 3 bis 5 ausgelegt. "
              "Ein Projekt belegt 3 bis 5 Seiten: Kopf, Summary, bis zu zwei "
              "Lösungsseiten, Abschluss.")
    for pr in projekte:
        block, _ = seiten_projekt(pr, t, basis, len(seiten) + 1, cache)
        for seite in block:
            lege_zone(seite)

    lege_ab(seite_divider(t["kontakt"]), oben=330)
    lege_ab(seite_kontakt(d, t, basis, len(seiten) + 1), oben=85)

    # Zuerst das Design System (Schriften, Farben, Textstile aus tokens.json),
    # dann das Layout. portfolio.css traegt selbst keine Farb- und Schriftwerte.
    css = ds.css() + (ASSETS / "portfolio.css").read_text()
    schablone = (ASSETS / "template.html").read_text()
    return (schablone.replace("{{css}}", css).replace("{{seiten}}", "\n".join(seiten)),
            grenzen)


# ── Rendern ──────────────────────────────────────────────────────────────

def rendere(html_text: str, ziel: Path) -> str:
    # Die eingebetteten Schriftschnitte tragen sonst die Uhrzeit des Laufs im
    # Kopf, und zwei Laeufe derselben Datei sind nicht mehr byte-gleich. Wer
    # den Wert selbst setzt, behaelt ihn.
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp()) / "portfolio.html"
    tmp.write_text(html_text, encoding="utf-8")
    try:
        from weasyprint import HTML
        HTML(filename=str(tmp)).write_pdf(str(ziel))
        return "WeasyPrint"
    except ImportError:
        pass
    for chrome in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   shutil.which("google-chrome"), shutil.which("chromium")):
        if chrome and Path(chrome).exists():
            subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                            f"--print-to-pdf={ziel}", "--no-pdf-header-footer",
                            tmp.as_uri()], check=True, capture_output=True)
            merke("Gerendert mit Chrome statt WeasyPrint – Seitenumbrüche und "
                  "Schriftgrößen vor dem Versand gegenprüfen.")
            return "Chrome"
    raise SystemExit("Keine Render-Engine gefunden. "
                     "Abhilfe: pip install weasyprint --break-system-packages")


def pruefe_ueberlauf(pdf: Path, grenzen: dict[int, Zone]) -> None:
    """In einem Folienlayout bricht nichts um - zu langer Text laeuft unter die
    Blattkante oder unter das Bild und faellt beim Ueberfliegen nicht auf.
    Deshalb wird das fertige PDF nachgemessen: gemeldet wird jeder Textblock,
    der aus seiner Inhaltszone heraustritt. Was komplett ausserhalb liegt, ist
    Seitenmoebel (Seitenzahl, Schrittleiste) und zaehlt nicht.

    Die obere Kante ist dabei genauso wichtig wie die untere: WeasyPrint
    beschneidet einen zu hohen Kasten nicht, sondern setzt den Rest auf die
    Folgeseite. Dort verschwindet er unter deren Beschnitt - im PDF steht er,
    sichtbar ist er nicht. Wer nur misst, was auf einer Seite *beginnt*,
    uebersieht genau den Fall, in dem Inhalt verlorengeht."""
    try:
        import fitz
    except ImportError:
        merke("PyMuPDF fehlt – der Überlaufcheck wurde übersprungen.")
        return
    leer = Zone(95, 1010, 1920, RAT_STD)
    doc = fitz.open(pdf)
    for i, page in enumerate(doc, 1):
        z = grenzen.get(i, leer)
        uebertrag = False
        gemeldet = False
        for blk in page.get_text("dict")["blocks"]:
            if blk["type"] != 0:
                continue
            x0, y0, x1, y1 = blk["bbox"]
            if x0 > 1780 and y0 > 990:      # Seitenzahl, kein Inhalt
                continue
            if z.oben is not None and y0 < z.oben:
                uebertrag = True
                continue
            if x0 >= z.rechts or y0 >= z.unten or gemeldet:
                continue
            if y1 > z.unten + 2:
                merke(f"Seite {i}: Text läuft {y1 - z.unten:.0f}pt über die "
                      f"Inhaltszone hinaus – {z.rat}.")
                gemeldet = True
            elif x1 > z.rechts + 2:
                merke(f"Seite {i}: Text ragt {x1 - z.rechts:.0f}pt unter das "
                      f"Bild – {z.rat} oder das Bild weglassen.")
                gemeldet = True
        if uebertrag and i > 1:
            vorher = grenzen.get(i - 1, leer)
            merke(f"Seite {i - 1}: Text reicht bis auf Seite {i} und wird dort "
                  f"vom Folienrand abgeschnitten – er fehlt im Dokument. "
                  f"{vorher.rat[0].upper()}{vorher.rat[1:]}.")
    doc.close()


def zwischenlager(quelle: Path) -> Path:
    """Die gerechneten Screenflaechen sind Arbeitsdateien und gehoeren neben die
    portfolio.json, nicht in den Ausgabeordner: der wird weitergereicht, und ein
    Zwischenspeicher von Dutzenden Megabyte ginge sonst mit."""
    ordner = quelle.parent / "arbeit" / "screens"
    try:
        ordner.mkdir(parents=True, exist_ok=True)
    except OSError:
        ordner = Path(tempfile.gettempdir()) / "newmonday-portfolio-screens"
        ordner.mkdir(parents=True, exist_ok=True)
        merke(f"Kein Schreibrecht neben der portfolio.json – die Screenflächen "
              f"liegen in {ordner}.")
    return ordner


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    quelle, ziel = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    d = json.loads(quelle.read_text(encoding="utf-8"))
    html_text, grenzen = baue_html(d, quelle.parent, zwischenlager(quelle))
    engine = rendere(html_text, ziel)
    pruefe_ueberlauf(ziel, grenzen)
    # Jede Textstelle im PDF muss einen Schnitt und Grad aus tokens.json tragen.
    for befund in ds.pruefe_pdf(ziel):
        merke(f"Design System: {befund}")
    # Der Regelfall ist schon beim Bauen der Flaechen abgeholt; hier bleibt der
    # Rest - Meldungen, die screens.py ausserhalb eines Flaechenbaus abgelegt
    # hat. Ohne diesen Abruf verschwaenden sie stumm.
    for h in screens_meldungen():
        merke(h)

    import fitz
    n = fitz.open(ziel).page_count
    print(f"{ziel}  ·  {n} Seiten  ·  {engine}")
    if hinweise:
        print("\nHinweise:", file=sys.stderr)
        for h in dict.fromkeys(hinweise):
            print(f"  - {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
