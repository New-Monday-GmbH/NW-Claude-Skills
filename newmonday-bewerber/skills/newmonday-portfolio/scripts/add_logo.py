#!/usr/bin/env python3
"""Nimmt ein Firmenlogo in die Bibliothek auf.

    python3 scripts/add_logo.py <datei-oder-url> <name>

    python3 scripts/add_logo.py ~/Downloads/hays.svg hays
    python3 scripts/add_logo.py https://example.com/logo.svg team-gmbh

Legt die Datei als assets/logos/<name>.svg oder .png ab. PNG wird am
Alphakanal zugeschnitten — sonst schrumpft das Logo im Layout durch den
mitgelieferten Weissraum. SVG wird auf offensichtlichen Unfug geprueft.

Downloads funktionieren nur dort, wo das Netz offen ist (lokal, Claude Desktop).
Im Browser-Chat blockt der Proxy fremde Domains mit host_not_allowed — dort die
Datei von Hand ablegen und dieses Skript mit dem lokalen Pfad aufrufen.
"""
import math
import re
import shutil
import sys
import urllib.request
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from logo_lib import bibliothek as _bibliothek  # noqa: E402

# Gemeinsame Bibliothek mit dem Lebenslauf-Skill, siehe logo_lib.py
ZIEL = _bibliothek()


def datendatei():
    """Wie die Datendatei des Skills heisst, in dem dieses Skript liegt.

    Es liegt in beiden: Der Lebenslauf fuehrt eine cv.json, das Portfolio eine
    portfolio.json. Erkannt am Renderer nebenan statt am Ordnernamen - der
    Renderer ist das, was den Unterschied wirklich ausmacht. Abgeleitet und
    nicht hingeschrieben, damit dieselbe Anweisung in beiden Skills stimmt.
    """
    return "portfolio.json" if (Path(__file__).resolve().parent
                                / "render_portfolio.py").exists() else "cv.json"


def holen(quelle, tmp):
    if str(quelle).startswith(("http://", "https://")):
        anfrage = urllib.request.Request(
            quelle, headers={"User-Agent": "newmonday-cv/1.0"}
        )
        try:
            with urllib.request.urlopen(anfrage, timeout=30) as antwort:
                tmp.write_bytes(antwort.read())
        except Exception as fehler:
            raise SystemExit(
                f"Download fehlgeschlagen: {fehler}\n"
                "Im Browser-Chat ist das erwartbar. Datei herunterladen und den "
                "lokalen Pfad uebergeben."
            )
        return tmp
    pfad = Path(quelle).expanduser()
    if not pfad.exists():
        raise SystemExit(f"Nicht gefunden: {pfad}")
    return pfad


def als_svg(quelle, name):
    inhalt = quelle.read_text(encoding="utf-8", errors="replace")
    if "<svg" not in inhalt[:2000]:
        raise SystemExit("Das ist keine SVG-Datei.")
    ziel = ZIEL / f"{name}.svg"
    ziel.write_text(inhalt, encoding="utf-8")
    return ziel


MINDESTHOEHE = 242          # 58pt: hoechstes Mass eines Stationslogos, bei 300 dpi
INK_ANTEIL = 0.75           # Schwelle zwischen Hintergrund und Strichfarbe


def bibliothek_bereit():
    """Ist assets/logos/ beschreibbar? Sonst frueh und verstaendlich abbrechen."""
    try:
        ZIEL.mkdir(parents=True, exist_ok=True)
        probe = ZIEL / ".schreibtest"
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
    except OSError as fehler:
        raise SystemExit(
            f"Die Logobibliothek {ZIEL} ist nicht beschreibbar ({fehler}).\n"
            "In Claude Code liegt der Skill unter ~/.claude/skills/ — dort "
            "Schreibrechte setzen, sonst lassen sich keine neuen Logos ablegen."
        )


def slugify(text):
    """Dateinamen ohne Umlaute und Sonderzeichen — sonst brechen Pfade und URLs."""
    import unicodedata
    ersatz = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
              "Ä": "ae", "Ö": "oe", "Ü": "ue"}
    for alt, neu in ersatz.items():
        text = text.replace(alt, neu)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "logo"


def pixel(bild):
    """Pixelliste, ohne an Pillows Umbenennung von getdata haengen zu bleiben."""
    return list(getattr(bild, "get_flattened_data", bild.getdata)())


def otsu(histogramm):
    """Helligkeitsschwelle, die zwei Gruppen maximal trennt."""
    gesamt = sum(histogramm)
    summe = sum(i * h for i, h in enumerate(histogramm))
    summe_b = gewicht_b = 0
    bestes, schwelle = 0.0, 128
    for t in range(256):
        gewicht_b += histogramm[t]
        if gewicht_b == 0:
            continue
        gewicht_f = gesamt - gewicht_b
        if gewicht_f == 0:
            break
        summe_b += t * histogramm[t]
        abstand = summe_b / gewicht_b - (summe - summe_b) / gewicht_f
        streuung = gewicht_b * gewicht_f * abstand * abstand
        if streuung > bestes:
            bestes, schwelle = streuung, t
    return schwelle


def zweifarbig(bild):
    """Trennt das Bild in Hintergrund und Strichfarbe, wenn es zweifarbig ist.

    Median-Cut ist hier untauglich: bei einer Wortmarke, die nur ein Achtel der
    Flaeche ausmacht, zerlegt es den Hintergrund in zwei Toene und uebersieht
    die Schrift. Otsu trennt nach Helligkeit und findet sie.

    Gemessen an echten Logos: Strichmarken liegen ueber 80%, Fotos um 50%.
    """
    from PIL import Image
    klein = bild.convert("RGB").resize((128, 128), Image.LANCZOS)
    grau = klein.convert("L")
    schwelle = otsu(grau.histogram())

    hell_pixel, dunkel_pixel = [], []
    for rgb, l in zip(pixel(klein), pixel(grau)):
        (hell_pixel if l > schwelle else dunkel_pixel).append((l, rgb))
    if not hell_pixel or not dunkel_pixel:
        return None

    def kernfarbe(gruppe, oben):
        """Mittel nur ueber das aeussere Viertel — die Pixel dazwischen sind
        Kantenunschaerfe und wuerden die Farbe zur Gegenseite ziehen."""
        gruppe = sorted(gruppe, key=lambda e: e[0], reverse=oben)
        kern = [rgb for _, rgb in gruppe[: max(1, len(gruppe) // 4)]]
        farbe = tuple(round(sum(p[k] for p in kern) / len(kern)) for k in range(3))
        for rein in ((255, 255, 255), (0, 0, 0)):     # fast weiss/schwarz einrasten
            if sum(abs(a - b) for a, b in zip(farbe, rein)) < 40:
                return rein
        return farbe

    def passend(gruppe, ziel):
        return sum(
            1 for _, p in gruppe if sum(abs(a - b) for a, b in zip(p, ziel)) < 60
        )

    hell_farbe = kernfarbe(hell_pixel, True)
    dunkel_farbe = kernfarbe(dunkel_pixel, False)
    treffer = passend(hell_pixel, hell_farbe) + passend(dunkel_pixel, dunkel_farbe)
    if treffer / (len(hell_pixel) + len(dunkel_pixel)) < 0.75:
        return None

    # Die groessere Gruppe ist der Hintergrund, die kleinere die Strichfarbe.
    if len(hell_pixel) >= len(dunkel_pixel):
        return hell_farbe, dunkel_farbe
    return dunkel_farbe, hell_farbe


def hell(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def vektorisieren(bild, name, farben, durchsichtig=False):
    """Zweifarbiges Logo ueber potrace in echte Pfade wandeln.

    durchsichtig=True laesst den Hintergrund weg, damit ein freigestelltes
    Logo freigestellt bleibt.
    """
    import re
    import subprocess
    import tempfile
    if not shutil.which("potrace"):
        return None
    hintergrund, strich = farben
    h_hell, s_hell = hell(hintergrund), hell(strich)
    schwelle = h_hell + INK_ANTEIL * (s_hell - h_hell)
    heller_strich = s_hell > h_hell

    grau = bild.convert("L")
    gross = grau.resize((grau.width * 8, grau.height * 8), 1)   # 1 = LANCZOS
    maske = gross.point(
        lambda p: 0 if (p > schwelle if heller_strich else p < schwelle) else 255
    )

    with tempfile.TemporaryDirectory() as tmp:
        pbm, svg = f"{tmp}/in.pbm", f"{tmp}/out.svg"
        maske.convert("1").save(pbm)
        subprocess.run(
            ["potrace", "-s", "-o", svg, "--turdsize", "2",
             "--alphamax", "1.0", "--opttolerance", "0.2", pbm],
            check=True, capture_output=True,
        )
        roh = Path(svg).read_text(encoding="utf-8")

    if "<path" not in roh:
        return None
    hg = "#%02X%02X%02X" % hintergrund
    st = "#%02X%02X%02X" % strich
    roh = roh.replace('fill="#000000"', f'fill="{st}"')
    if not durchsichtig:
        roh = roh.replace(
            "<g ",
            f'<rect x="-9999" y="-9999" width="99999" height="99999" fill="{hg}"/><g ',
            1,
        )
    ziel = ZIEL / f"{name}.svg"
    ziel.write_text(roh, encoding="utf-8")
    return ziel


def rand_abschneiden(bild, hintergrund):
    """Einfarbigen Rand entfernen — auch farbigen, nicht nur weissen.

    Ein Badge-Logo bringt oft viel toten Rand mit. Bleibt der drin, schrumpft
    die Wortmarke im Layout so weit, dass sie unleserlich wird.
    """
    from PIL import Image, ImageChops
    flaeche = Image.new("RGB", bild.size, hintergrund)
    kasten = ImageChops.difference(bild.convert("RGB"), flaeche).convert("L")
    rand = kasten.point(lambda p: 255 if p > 45 else 0).getbbox()
    if not rand:
        return bild
    luft = max(2, round((rand[3] - rand[1]) * 0.12))   # etwas Luft stehen lassen
    return bild.crop((
        max(0, rand[0] - luft), max(0, rand[1] - luft),
        min(bild.width, rand[2] + luft), min(bild.height, rand[3] + luft),
    ))


def kontrolle(hintergrund, strich):
    """Reichen Farbabstand und Trennung fuer den Druck?"""
    abstand = sum(abs(a - b) for a, b in zip(hintergrund, strich))
    if abstand < 150:
        print(
            f"WARNUNG: Strichfarbe {strich} liegt zu nah am Hintergrund "
            f"{hintergrund} (Abstand {abstand}). So wird das Logo im Druck kaum "
            "lesbar — bitte eine bessere Quelle besorgen."
        )
        return False
    print(f"Farbtrennung geprueft: Strich {strich} auf {hintergrund}.")
    return True


def als_bild(quelle, name):
    from PIL import Image
    bild = Image.open(quelle)
    durchsichtig = bild.mode in ("RGBA", "LA", "P") and "transparency" in bild.info \
        or bild.mode in ("RGBA", "LA")
    if durchsichtig:
        bild = bild.convert("RGBA")
        rand = bild.split()[-1].getbbox()
        if rand:
            bild = bild.crop(rand)
        # Fuer die Analyse auf Weiss legen — so sieht das Logo im Layout aus.
        weiss = Image.new("RGBA", bild.size, (255, 255, 255, 255))
        bild = Image.alpha_composite(weiss, bild).convert("RGB")
    else:                                  # ohne Alpha: weissen Rand wegschneiden
        from PIL import ImageChops
        hell_bild = Image.new(bild.mode, bild.size, (255, 255, 255)[: len(bild.getbands())])
        rand = ImageChops.difference(bild, hell_bild).convert("L").getbbox()
        if rand:
            bild = bild.crop(rand)

    farben = zweifarbig(bild)
    if farben:
        hintergrund, strich = farben
        if not kontrolle(hintergrund, strich):
            farben = None
        else:
            vorher = bild.size
            bild = rand_abschneiden(bild, hintergrund)
            if bild.size != vorher:
                print(f"Toter Rand entfernt: {vorher} -> {bild.size}")

    if bild.height < MINDESTHOEHE:
        if farben:
            ziel = vektorisieren(bild, name, farben, durchsichtig)
            if ziel:
                print(f"Zu klein ({bild.height}px) und zweifarbig — vektorisiert.")
                return ziel
        faktor = MINDESTHOEHE / bild.height
        bild = bild.resize(
            (round(bild.width * faktor), MINDESTHOEHE), Image.LANCZOS
        )
        print(
            f"Zu klein, auf {MINDESTHOEHE}px hochgerechnet. Das glaettet nur, "
            "es entstehen keine neuen Details — moeglichst eine bessere Quelle besorgen."
        )

    ziel = ZIEL / f"{name}.png"
    bild.save(ziel)
    return ziel


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    quelle_arg, name = sys.argv[1], slugify(sys.argv[2])
    bibliothek_bereit()

    tmp = ZIEL / f".eingang-{name}"
    try:
        quelle = holen(quelle_arg, tmp)
        endung = Path(str(quelle_arg).split("?")[0]).suffix.lower()
        ziel = als_svg(quelle, name) if endung == ".svg" else als_bild(quelle, name)
    finally:
        if tmp.exists():
            tmp.unlink()

    groesse = ziel.stat().st_size
    print(f"{ziel.name} abgelegt ({groesse // 1024} KB)")
    sichtpruefung(ziel)
    print(f'In der {datendatei()} eintragen als:  "logo": "{ziel.name}"')


def sichtpruefung(ziel):
    """Logo in Einsatzgroesse rendern und zaehlen, was sichtbar bleibt.

    Faengt jede Ursache ab, aus der ein Logo leer oder unleserlich herauskommt —
    falsch bestimmte Farben, zu duenne Striche, kaputte Pfade.
    """
    try:
        from weasyprint import HTML
        from PIL import Image
    except ImportError:
        return
    import subprocess
    import tempfile
    # Einsatzgroesse heisst: das Mass, das render_portfolio.py diesem Logo auf
    # der Kundenwand gibt — aus seinem Seitenverhaeltnis, nicht aus einem festen
    # Kasten. Sonst misst die Deckung bei flachen Schriftzuegen nur den
    # Weissraum ueber und unter ihnen.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from render_portfolio import LOGO_MASS_MAX, seitenverhaeltnis
    v = math.sqrt(seitenverhaeltnis(ziel.as_uri()))
    breite, hoehe = LOGO_MASS_MAX * v, LOGO_MASS_MAX / v
    with tempfile.TemporaryDirectory() as tmp:
        pdf, png = f"{tmp}/p.pdf", f"{tmp}/p"
        HTML(
            string=f'<style>@page{{size:{breite}pt {hoehe}pt;margin:0}}'
                   'body{margin:0;background:#fff}'
                   f'img{{width:{breite}pt;height:{hoehe}pt}}</style>'
                   f'<img src="{ziel.name}">',
            base_url=str(ziel.parent),
        ).write_pdf(pdf)
        subprocess.run(["pdftoppm", "-png", "-r", "300", pdf, png],
                       check=True, capture_output=True)
        bild = Image.open(f"{png}-1.png").convert("RGB")

    farben = bild.getcolors(bild.width * bild.height) or []
    nicht_weiss = sum(n for n, c in farben if sum(abs(k - 255) for k in c) > 60)
    anteil = nicht_weiss / (bild.width * bild.height)
    if anteil < 0.02:
        print(
            f"WARNUNG: In Einsatzgroesse sind nur {anteil:.1%} der Flaeche sichtbar. "
            "Das Logo kommt praktisch leer heraus — bitte pruefen."
        )
    else:
        print(f"Sichtpruefung in Einsatzgroesse: {anteil:.0%} der Flaeche gedeckt.")


if __name__ == "__main__":
    main()
