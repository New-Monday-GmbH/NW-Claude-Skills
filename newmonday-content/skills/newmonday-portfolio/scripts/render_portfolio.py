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


def absaetze(text: str, klasse: str = "fliess", stil: str = "") -> str:
    """Leerzeilen im Quelltext werden zu Absaetzen, **fett** zu <b>."""
    if not text:
        return ""
    teile = [t.strip() for t in re.split(r"\n\s*\n", text.strip()) if t.strip()]
    body = "".join(f"<p>{fett(t)}</p>" for t in teile)
    attr = f' style="{stil}"' if stil else ""
    return f'<div class="{klasse}"{attr}>{body}</div>'


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
FLAECHENBREITE = {"bild--halb": 909, "bild--breit": 1020, "vollflaeche": 1920}

# Ab dieser Helligkeit liest Schwarz besser als Weiss: bei 0,18 sind beide
# WCAG-Kontraste gleich (rund 4,6:1). Die Schwelle von hell() taugt dafuer
# nicht - zwischen 0,18 und 0,36 setzte sie Weiss auf Himmel und Glasfassaden,
# und genau dort liegen die HQ-Fotos (0,20 bis 0,30).
TINTENWECHSEL = 0.18

# Wo Wortmarke und Seitenzahl auf der Folie liegen, in Folienpunkten und mit
# etwas Luft: Wortmarke 148x15pt auf 1712/60, Seitenzahl rechtsbuendig auf
# 60pt und 46pt ueber der Kante (so steht beides im CSS). Gemessen wird genau
# dieses Feld - eine ganze Bildecke mittelt Himmel und Fassade zusammen und
# entscheidet dann fuer eine Stelle, an der nichts steht.
MOEBELFELD = {True: (1700, 48, 1872, 88), False: (1800, 1000, 1872, 1046)}

# Der Verlauf aus .bildschatten: 298pt hoch, unten 55 % Schwarz. Er liegt auf
# den Arbeitsweise-Seiten ueber dem Motiv und macht die Seitenzahl-Ecke dunkel,
# egal wie hell das Foto ist. Wer ihn nicht mitrechnet, misst das falsche Bild.
SCHATTEN_HOCH, SCHATTEN_TIEF = 298, 0.55

# Ab welchem Anteil widersprechender Pixel das Moebelfeld als gescheckt gilt,
# und ab welcher Helligkeit ein Pixel widerspricht. Das Feld ist breiter als die
# Schrift darin, ein Drittel Widerspruch traegt die Wortmarke also noch:
# arbeitsweise-4 kommt auf 31 % und steht im PDF sauber auf dem dunklen Teil.
# Erst wo das Feld etwa halb und halb liegt, geht Schrift verloren.
FELD_UNRUHE, HELL_GRENZE, DUNKEL_GRENZE = 0.40, 150, 100


def ecke_dunkel(uri: str | None, oben: bool, klasse: str = "bild--breit",
                schatten: bool = False) -> bool | None:
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
        dunkel = helligkeit("#%02x%02x%02x" % tuple(mittel)) <= TINTENWECHSEL
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


def kopfzeile(bild, basis: Path, nr: int, klasse: str = "bild--breit",
              schatten: bool = False) -> str:
    """Wortmarke und Seitenzahl, je nach Motiv hell oder dunkel gesetzt.
    `klasse` und `schatten` beschreiben die Flaeche, in der das Motiv steht -
    erst damit misst ecke_dunkel das, was auf der Folie zu sehen ist."""
    uri = datei_uri(bild.get("datei") if isinstance(bild, dict) else bild, basis) if bild else None
    zahl = ("seitenzahl seitenzahl--hell"
            if ecke_dunkel(uri, False, klasse, schatten) else "seitenzahl")
    return (logo_block(ecke_dunkel(uri, True, klasse, schatten))
            + f'<div class="{zahl}">{nr}</div>')


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
    if not bild:
        merke(f"Platzhalter gesetzt: {was}")
        return (f'<div class="bild {klasse} bild--platzhalter">'
                f'<div class="hinweis"><b>{e(t["fehlt"])}</b>{e(was)}</div></div>')
    quelle = bild.get("datei") if isinstance(bild, dict) else bild
    passung = bild.get("passung", "cover") if isinstance(bild, dict) else "cover"
    uri = datei_uri(quelle, basis)
    if not uri:
        return (f'<div class="bild {klasse} bild--platzhalter">'
                f'<div class="hinweis"><b>{e(t["fehlt"])}</b>{e(was)}</div></div>')
    pruefe_aufloesung(uri, klasse, was)
    return (f'<div class="bild {klasse}"{stil}>'
            f'<img src="{uri}" style="object-fit:{passung}">{schicht}</div>')


def spalten_fuer(anzahl: int) -> int:
    """Wie viele Logos nebeneinander. Wenige Logos duerfen gross stehen,
    viele muessen enger - sonst wird die Wand entweder leer oder unlesbar.
    Bis zu fuenf stehen in einer Reihe: p-03 zeigt vier Logos nebeneinander,
    und eine Restzeile mit einem einzelnen Logo sieht nach Versehen aus."""
    if anzahl <= 5:
        return max(1, anzahl)
    for grenze, spalten in ((6, 3), (12, 4), (15, 5), (24, 6), (28, 7)):
        if anzahl <= grenze:
            return spalten
    return 8


# Obergrenze fuer die Logogroesse auf der Kundenwand, in Punkt. Der Wert ist die
# Hoehe eines quadratischen Logos; breite Schriftzuege stehen entsprechend
# niedriger und breiter. Zwei Saetze von Grenzen:
#
# - Das dichte Raster (ab 6 Logos) laeuft mit 132/104 und Zellfaktor 0,40 -
#   eine Stufe unter den aus p-03 gemessenen Werten, weil ein volles Raster
#   mit den Referenzwerten als zu wuchtig zurueckkam (Freia-Portfolio, S. 3,
#   12 Logos).
# - Die eine Reihe (bis 5 Logos) steht wieder exakt im Referenzmass von p-03
#   (Paul Hecker): 160/128, Zellfaktor 0,46, Reihenmitte ~717pt statt 620pt.
#   Die Rueckmeldung dazu kam ausdruecklich mit Paul als Massstab - die
#   Verkleinerung von damals galt dem vollen Raster, nicht der Reihe.
LOGO_MASS_MAX = 132
LOGO_HOEHE_MAX = 104
LOGO_MASS_REIHE = 160
LOGO_HOEHE_REIHE = 128
# align-content: center setzt die Reihenmitte auf top + Hoehe/2. In p-03 liegt
# sie bei ~717pt; bei 640pt Wandhoehe ergibt das eine Oberkante von 397pt.
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
  <div class="titel">{e(p.get("cover_titel"))}</div>
  <div class="name">{e(p["name"])}</div>
  <div class="rolle">{e(p.get("rolle"))}</div>
  <div class="jahr">{e(p.get("jahr"))}</div>
</section>'''


def seite_profil(d, t, basis, nr):
    p = d["person"]
    foto = datei_uri(p.get("foto"), basis)
    foto_html = f'<img src="{foto}">' if foto else ""
    if not foto:
        merke("Profilfoto fehlt - die Fotofläche bleibt leer.")

    koennen = "".join(f"<li>{fett(k)}</li>" for k in p.get("kenntnisse", []))
    sprachen = "".join(
        f'<div class="paar"><b>{e(s["sprache"])}</b><span>{e(s.get("niveau"))}</span></div>'
        for s in p.get("sprachen", []))
    # Connect wie in der Referenz (Paul Hecker, S. 2): der Titel selbst ist
    # der petrolfarbene Pfeil-Link - kein schwarzer Titel daruber, kein
    # "Anzeigen", keine Trennlinie. Diese Karte bleibt immer in diesem Muster.
    links = "".join(
        (f'<div class="paar paar--link"><a href="{e(l["url"])}">{e(l["titel"])}'
         " →</a></div>") if l.get("url") else
        f'<div class="paar paar--link"><span>{e(l["titel"])}</span></div>'
        for l in p.get("links", []))

    karten = []
    y = 223
    if p.get("erfahrung_jahre"):
        karten.append(f'''<div class="pkarte" style="top:{y}pt">
      <h3>{e(t["erfahrung"])}</h3>
      <div class="zahl">{e(p["erfahrung_jahre"])}</div>
      <div class="fuss">{e(t["jahre"])}</div></div>''')
        y += 293
    if sprachen:
        karten.append(f'<div class="pkarte" style="top:{y}pt">'
                      f'<h3>{e(t["sprachen"])}</h3>{sprachen}</div>')
        # Der Platz bis zur nächsten Karte ist für zwei Einträge vermessen;
        # jeder weitere braucht rund 80 pt (zwei 20-pt-Zeilen + Abstand).
        # Sprachen werden nie gestrichen - bei Platznot gleiche Niveaus zu
        # einer Zeile zusammenfassen ("Deutsch, Italienisch" / "Muttersprache").
        y += 276 + max(0, len(p.get("sprachen", [])) - 2) * 80
    if links:
        karten.append(f'<div class="pkarte" style="top:{y}pt">'
                      f'<h3>{e(t["connect"])}</h3>{links}</div>')
        connect_ende = y + 56 + len(p.get("links", [])) * 80
        if connect_ende > 1040:
            merke("Profilseite: die rechte Kartenspalte läuft unten aus der "
                  "Folie. Keine Sprache streichen - gleiche Niveaus zu einer "
                  "Zeile zusammenfassen (\"Deutsch, Italienisch\" / "
                  "\"Muttersprache\").")

    top = ""
    if p.get("top_kenntnisse"):
        top = (f'<div class="karte karte--top"><h3>{e(t["top"])}</h3>'
               f'<p>{"  •  ".join(fett(k) for k in p["top_kenntnisse"])}</p></div>')
    return f'''<section class="seite seite--profil">
  <div class="foto">{foto_html}</div>
  <div class="p-name">{e(p["name"])}</div>
  <div class="p-rolle">{e(p.get("rolle"))}</div>
  {top}
  <div class="karte karte--koennen"><h3>{e(t["koennen"])}</h3>
    <ul class="zeilen">{koennen}</ul></div>
  <div class="panel"></div>{"".join(karten)}
  {logo_block(True)}<div class="seitenzahl seitenzahl--hell">{nr}</div>
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
    wand_stil = f' style="top:{REIHE_OBEN}pt"' if reihe else ""
    sp = spalten_fuer(len(dateien)) or 1
    zeilen = max(1, math.ceil(len(dateien) / sp))
    # Abrunden: 4 x 401.8pt waeren 1607.2 und wuerden im 1607pt breiten
    # Kasten auf drei Kacheln je Zeile umbrechen.
    zelle_b, zelle_h = math.floor(1605 / sp * 10) / 10, 640 / zeilen
    # Gleiche Flaeche statt gleicher Hoehe: ueber die Hoehe skaliert wirkt eine
    # kompakte Bildmarke doppelt so schwer wie ein breiter Schriftzug.
    frei_b, frei_h = zelle_b - 44, zelle_h - 48
    # In der Referenz (p-03) steht ein Logo auf gut 0.46 der Zellbreite; das
    # Raster liegt eine Stufe darunter, seit eine volle Wand als zu wuchtig
    # zurueckkam. Nach oben deckelt LOGO_MASS_MAX, sonst wachsen wenige Logos
    # ins Erschlagende.
    flaeche = min(frei_b * 0.40, frei_h * 1.15, LOGO_MASS_MAX)
    for uri in [] if reihe else dateien:
        v = seitenverhaeltnis(uri)
        b = min(frei_b, flaeche * math.sqrt(v))
        h = b / v
        # Der Flaechendeckel allein laesst quadratische Bildmarken auf volle
        # LOGO_MASS_MAX Hoehe wachsen - in p-03 misst das hoechste Logo 128pt.
        # Deshalb zusaetzlich die Hoehe deckeln und die Breite nachziehen.
        if h > min(frei_h, LOGO_HOEHE_MAX):
            h = min(frei_h, LOGO_HOEHE_MAX)
            b = h * v
        # Zentriert wird mit gerechnetem Padding, nicht mit Flexbox:
        # WeasyPrint setzt justify-content nicht um, und die Logos hingen
        # linksbuendig in ihren Zellen - die "verschobenen" Logos der
        # Rueckmeldung. Padding ist deterministisch und rendert ueberall gleich.
        kacheln.append(
            f'<div class="kachel" style="width:{zelle_b:.1f}pt;height:{zelle_h:.1f}pt;'
            f'padding:{(zelle_h - h) / 2:.1f}pt 0 0 {(zelle_b - b) / 2:.1f}pt">'
            f'<img src="{uri}" style="width:{b:.0f}pt;height:{h:.0f}pt"></div>')
    if not kacheln:
        merke("Logowand „Meine Kunden“ ist leer - keine Kundenlogos zugeordnet.")
    return f'''<section class="seite seite--kunden">
  <div class="streifen streifen--weiter"></div>
  <div class="h1">{e(t["kunden"])}</div>
  <div class="kundenwand"{wand_stil}>{"".join(kacheln)}</div>
  {logo_block(False)}<div class="seitenzahl">{nr}</div>
</section>'''


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
  <div class="halb-rechts"><div class="aussage">{fett(text)}</div></div>
  <div class="rolle">{rolle}</div>
  {logo_block(False)}<div class="seitenzahl">{nr}</div>
</section>'''


def seite_divider(titel):
    zeilen = e(titel).replace("\n", "<br>")
    return f'''<section class="seite seite--divider">
  <div class="h1">{zeilen}</div>{logo_block(True)}
</section>'''


def seite_prozess(d, t, basis, nr):
    """Die Prozess-Uebersicht - immer drei Spalten, nie vier. Eine fruehere
    Fassung haengte „KI-Einsatz" als vierte Spalte an, sobald die KI-Folie
    existierte. Genau das kam zurueck: KI ist Teil jeder Phase, kein Schritt
    nach der Umsetzung - als letzte Spalte sah sie aus wie einer. Die KI-Folie
    (Seite 10) bleibt, aber als eigene Arbeitsweise-Seite, nicht als
    Prozessschritt."""
    eintraege = [(s["titel"], s.get("kurztext", ""))
                 for s in d.get("prozess", [])[:3]]
    spalten = "".join(
        f'<div class="prozess-spalte" style="left:{193 + i * 489}pt;">'
        f'<div class="balken"></div>'
        f'<h2>{e(titel).replace(chr(10), "<br>")}</h2>'
        f'<p>{fett(kurztext)}</p></div>'
        for i, (titel, kurztext) in enumerate(eintraege))
    return f'''<section class="seite seite--prozess">
  <div class="streifen streifen--start"></div>
  <div class="eyebrow">{e(t["prozess"])}</div>
  {spalten}
  {logo_block(False)}<div class="seitenzahl">{nr}</div>
</section>'''


# Die Ueberschrift der Arbeitsweise-Seiten steht auf 155pt und laeuft mit 96pt
# bei 1.2 Zeilenabstand, also 115.2pt je Zeile. Ein fester Textbeginn kollidiert
# deshalb ab zwei Zeilen mit ihr. Der Abstand ist aus p-07 (dreizeilig) und
# p-10 (einzeilig) abgeleitet, die Breite steht so im CSS.
KOPF_OBEN, KOPF_GRAD, KOPF_ABSTAND, KOPF_BREITE = 155, 96, 105, 800
# Ab der vierten Zeile beginnt der Fliesstext unter 720pt und laeuft in die
# Schrittleiste. Drei Zeilen sind die Grenze, die p-07 noch sauber zeigt.
KOPF_MAX_ZEILEN = 3
# Unterkante der Textzone auf den Arbeitsweise-Seiten: darunter liegt die
# Schrittleiste (Oberkante 942pt).
ARBEIT_UNTEN = 940
# Die Kundenueberschrift der Projekt-Kopfseite hat seit dem Wegfall des
# Aufmacherbildes die ganze Blattbreite; der Wert steht so im CSS.
KOPF_PROJEKT = 1534
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
    """Zeilen der 96-pt-Ueberschrift. -2pt Laufweite je Zeichen steht so im CSS
    und gilt als fester Punktwert auch fuer verkleinerte Grade."""
    return zeilenzahl(titel, breite, "Inter-ExtraBold.ttf", grad, 2.0)


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
    return KOPF_OBEN + zeilen * grad * 1.2 + KOPF_ABSTAND


def schrittleiste(schritte, t, aktiv: int) -> str:
    """Die Leiste zeigt, an welcher Stelle des Prozesses die Seite steht. Sie
    fuellt sich auf: p-07 hat einen Balken, p-09 alle drei. Nur den aktuellen
    zu faerben erzaehlt keinen Fortschritt. Drei Balken, nicht vier: eine
    fruehere Fassung zaehlte „KI-Einsatz" als vierten Schritt mit, und genau
    das kam zurueck - KI laeuft in allen Phasen mit und ist kein Schritt nach
    der Umsetzung. Die Balken stehen im Takt der Prozessseite (x 193 / 682 /
    1171, 323 pt); der dritte liegt auf dem Bild und wird dort weiss - sonst
    verschwindet er im Motiv."""
    # Im Titel darf ein weicher Trenner stehen ("Konzept-\nentwicklung"),
    # damit die 96pt-Headline umbricht. In der Leiste steht das Wort ganz.
    namen = [e(s["titel"]).replace("-\n", "").replace(chr(10), " ")
             for s in schritte[:3]]
    balken = []
    for j, name in enumerate(namen):
        links = 193 + j * 489
        aufbild = links + 323 > 1011          # Bildkante der Arbeitsweise-Seiten
        klassen = ("schritt" + (" ist" if j <= aktiv else "")
                   + (" aufbild" if aufbild else ""))
        balken.append(f'<div class="{klassen}" style="left:{links}pt">'
                      f'<div class="balken"></div><span>{name}</span></div>')
    return f'<div class="schritte">{"".join(balken)}</div>'


def seite_arbeitsweise(d, t, basis, nr, i):
    schritte = d.get("prozess", [])
    s = schritte[i]
    bild = (ASSETS / f"bilder/arbeitsweise-{i + 1}.jpg").as_uri()
    grad, zeilen = kopfmass(s["titel"])
    return f'''<section class="seite seite--arbeitsweise">
  <div class="streifen streifen--weiter"></div>
  <div class="bild bild--halb"><img src="{bild}">
    <div class="bildschatten" style="left:0;right:0"></div></div>
  <div class="eyebrow">{e(t["arbeitsweise"])}</div>
  <div class="h1" style="font-size:{grad}pt">{e(s["titel"]).replace(chr(10), "<br>")}</div>
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
  <div class="eyebrow">{e(t["arbeitsweise"])}</div>
  <div class="h1">{e(t["ki"])}</div>
  {absaetze(nuechtern(ki.get("text", "")), stil=f"top:{textkante(1):.1f}pt")}
  {werkzeuge}
  {kopfzeile(ASSETS / "bilder/arbeitsweise-4.jpg", basis, nr, "bild--halb", True)}
</section>''', zone


def seite_agentur(d, t, basis, nr):
    b = AGENTUR["badge"]
    return f'''<section class="seite seite--agentur">
  <div class="streifen streifen--weiter"></div>
  <div class="h1">{e(t["agentur_h"]).replace(chr(10), "<br>")}</div>
  <div class="subline">{e(t["agentur_sub"])}</div>
  <div class="kunden"><img src="{(ASSETS / 'marke/nm-agentur-kunden.png').as_uri()}"></div>
  <div class="badge"><img src="{(ASSETS / 'marke/ux-awards-badge.png').as_uri()}"></div>
  <div class="badge-text">{e(b[0])}<br>{e(b[1])}<br>{e(b[2])}</div>
  <div class="panel"></div>
  <div class="pkarte" style="top:227pt"><h3>{e(t["team"])}</h3>
    <div class="zahl">{AGENTUR["teammitglieder"]}</div></div>
  <div class="pkarte" style="top:482pt"><h3>{e(t["gegruendet"])}</h3>
    <div class="zahl">{AGENTUR["gegruendet"]}</div></div>
  <div class="pkarte" style="top:737pt"><h3>{e(t["zufriedenheit"])}</h3>
    <div class="zahl">{AGENTUR["zufriedenheit"]}</div></div>
  {logo_block(True)}<div class="seitenzahl seitenzahl--hell">{nr}</div>
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
    oben = ecke_dunkel(uri, True, klasse)
    unten = ecke_dunkel(uri, False, klasse)
    oben = ersatz if oben is None else oben
    unten = ersatz if unten is None else unten
    nda = (f'<div class="nda-hinweis nda-hinweis--{"hell" if unten else "dunkel"}">'
           f'{e(t["nda"])}</div>' if pr.get("nda") else "")
    return (nda + logo_block(oben)
            + f'<div class="seitenzahl{" seitenzahl--hell" if unten else ""}">{nr}</div>')


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
                  seed: int, was: str) -> Path | None:
    """Die markenfarbene Flaeche mit den schraeg fliegenden Screens. Das Rechnen
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
        "|".join([stand, variante, str(farbe), str(seed)]
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
        gebaut = Path(baue_screens(pfade, farbe, ziel, variante=variante, seed=seed))
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
    spalten_oben = 252 + kzeilen * KOPF_GRAD * 1.2 + (84 if kzeilen == 1 else 46)
    # „Meine Rolle" steht im Fluss der Projekt-Spalte, direkt unter deren Text -
    # so sitzt der Block dort, wo der Text endet, wie in der Referenz
    # (p-13/18/23). Die alte Fassung liess ihn von der Blattkante nach oben
    # wachsen; bei kurzen Texten klebte er dann allein am unteren Rand.
    rolle_html = (f'<div class="rolle-block"><div class="label">'
                  f'{e(t["meine_rolle"])}</div><ul class="punkte">{rolle}</ul></div>'
                  if rolle else "")
    out.append((f'''<section class="seite seite--projekt">
  <div class="streifen streifen--start"></div>
  {kundenlogo(pr, basis)}
  <div class="h1">{e(titel)}</div>
  <div class="sp-projekt" style="top:{spalten_oben:.1f}pt"><div class="label">{e(t["projekt"])}</div>
    {absaetze(pr.get("projekt", ""))}{rolle_html}</div>
  <div class="sp-kunde" style="top:{spalten_oben:.1f}pt"><div class="label">{e(t["kunde"])}</div>
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
  <div class="h1">{e(t["summary"])}</div>
  {absaetze(sm.get("text", ""))}
  {kopfzeile(sm.get("bild"), basis, nr)}
</section>''', Zone(PROJEKT_OBEN, 1010, 880, '„summary.text“ kürzen')))
    nr += 1

    farbe = pr.get("markenfarbe")
    for k, lo in enumerate((pr.get("loesungen") or [])[:2]):
        was = f'{pr.get("kunde", "")} – {t["loesung"]}'
        bild = screenflaeche(lo.get("screens"), farbe, "panel", basis, cache, k, was)
        punkte = "".join(f"<li>{fett(x)}</li>" for x in lo.get("punkte", []))
        out.append((f'''<section class="seite seite--loesung">
  <div class="streifen streifen--weiter"></div>
  {bildflaeche(bild, "bild--breit", basis, t, farbe=farbe, was=was)}
  {kundenlogo(pr, basis)}
  <div class="inhalt">
    <div class="einleitung">{fett(lo.get("titel") or t["loesung"])}</div>
    {absaetze(lo.get("text", ""))}
    {f'<ul class="punkte" style="margin-top:26pt">{punkte}</ul>' if punkte else ""}</div>
  {marken_moebel(pr, t, nr, bild, farbe)}
</section>''', Zone(PROJEKT_OBEN, 1010, 880,
                     "kürzen oder auf eine weitere Lösungsseite verteilen")))
        nr += 1

    # Eigener Seed, damit die Abschlussseite die Anordnung der Lösungsseiten
    # nicht wiederholt - dieselben Screens liegen sonst gleich.
    was = f'{pr.get("kunde", "")} – {t["screens"]}'
    voll = screenflaeche(pr.get("screens"), farbe, "voll", basis, cache, 9, was)
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
    return f'''<section class="seite seite--kontakt">
  <div class="band"></div>
  <div class="adresse">{e(FIRMA["name"])}<br>{e(FIRMA["strasse"])}<br>{e(FIRMA["ort"])}
    <br><br><a href="mailto:{e(FIRMA["mail"])}">{e(FIRMA["mail"])}</a>
    <br><a href="https://{e(FIRMA["web"])}">{e(FIRMA["web"])}</a></div>
  <div class="aufruf"><h2>{e(t["aufruf_h"])}</h2>
    <p>{e(t["aufruf_p"].format(name=a["name"]))}</p></div>
  <div class="box"><h3>{e(t["fragen_h"])}</h3><p>{e(t["fragen_p"])}</p>
    <div class="felder">
      <div><b>{e(t["mail"])}</b><a href="mailto:{e(a["mail"])}">{e(a["mail"])}</a></div>
      <div><b>{e(t["telefon"])}</b>
        <a href="tel:{re.sub(r"[^+0-9]", "", a["telefon"])}">{e(a["telefon"])}</a></div>
    </div></div>
  <div class="person"><img src="{(ASSETS / a["foto"]).as_uri()}">
    <div class="name"><b>{e(a["name"])}</b>
      <span>{"<br>".join(e(x) for x in titel)}</span></div></div>
  {logo_block(False)}<div class="seitenzahl">{nr}</div>
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

    lege_ab(seite_cover(d, t, basis), oben=430)
    lege_ab(seite_profil(d, t, basis, len(seiten) + 1), 1060, oben=110,
            rat="weniger „kenntnisse“ oder kürzere Einträge")
    lege_ab(seite_kunden(d, t, basis, len(seiten) + 1), 985, 1800, oben=135)
    # Das Zitat steht mittig und waechst nach beiden Seiten: eine obere Grenze
    # wuerde es faelschlich als Uebertrag der Vorseite melden. Zu lang ist es
    # trotzdem nicht unbemerkt - dafuer sorgt die untere Kante.
    lege_ab(seite_statement(d, t, basis, len(seiten) + 1), oben=None,
            rat='„statement.text“ kürzen')
    lege_ab(seite_divider(t["prozess"].replace(" Prozess", "\nProzess")
                                      .replace(" Process", "\nProcess")), oben=340)
    lege_ab(seite_prozess(d, t, basis, len(seiten) + 1), 990, oben=112,
            rat='„prozess.kurztext“ kürzen')

    schritte = d.get("prozess", [])
    if len(schritte) != 3:
        merke(f"Der Design-Prozess hat {len(schritte)} Schritte statt 3 – "
              "die Vorlage sieht genau drei vor.")
    ki = (d.get("person") or {}).get("ki") or {}
    if not ki.get("text"):
        merke("Ohne person.ki entfällt die Folie zum KI-Einsatz – "
              "Text und Werkzeuge nachtragen.")
    for i in range(min(3, len(schritte))):
        # Unterhalb von 940pt liegt die Schrittleiste; Text darf da nicht hin.
        lege_ab(seite_arbeitsweise(d, t, basis, len(seiten) + 1, i),
                ARBEIT_UNTEN, 1011, oben=112, rat='„prozess.langtext“ kürzen')
    if ki.get("text"):
        # Mit Werkzeugreihe endet die Textzone schon über deren Oberkante -
        # wo genau, weiß nur die Seite selbst.
        aufbau, unten = seite_ki(d, t, basis, len(seiten) + 1)
        lege_ab(aufbau, unten, 1011, oben=112, rat='„person.ki.text“ kürzen')

    lege_ab(seite_agentur(d, t, basis, len(seiten) + 1), oben=108)
    lege_ab(seite_divider(t["projekte"]), oben=340)

    projekte = d.get("projekte", [])
    if not 3 <= len(projekte) <= 5:
        merke(f"{len(projekte)} Projekte – die Vorlage ist auf 3 bis 5 ausgelegt. "
              "Ein Projekt belegt 3 bis 5 Seiten: Kopf, Summary, bis zu zwei "
              "Lösungsseiten, Abschluss.")
    for pr in projekte:
        block, _ = seiten_projekt(pr, t, basis, len(seiten) + 1, cache)
        for seite in block:
            lege_zone(seite)

    lege_ab(seite_divider(t["kontakt"]), oben=340)
    lege_ab(seite_kontakt(d, t, basis, len(seiten) + 1))

    css = (ASSETS / "portfolio.css").read_text()
    css = css.replace('url("fonts/', f'url("{(ASSETS / "fonts").as_uri()}/')
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
