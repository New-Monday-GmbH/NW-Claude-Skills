#!/usr/bin/env python3
"""Nimmt ein Firmenlogo in die Bibliothek auf.

    python3 scripts/add_logo.py <datei-oder-url> <name> [--kontrolle <bild.png>]

    python3 scripts/add_logo.py ~/Downloads/hays.svg hays
    python3 scripts/add_logo.py https://example.com/logo.svg team-gmbh

Legt die Datei als assets/logos/<name>.svg oder .png ab. PNG wird am
Alphakanal zugeschnitten — sonst schrumpft das Logo im Layout durch den
mitgelieferten Weissraum. SVG wird auf offensichtlichen Unfug geprueft.

Logos werden nie verzerrt — und weil das Layout das Seitenverhaeltnis immer
aus der Datei nimmt, ist eine gestauchte Datei die einzige Stelle, an der es
doch passieren kann (so war es beim beQ-Logo, 03.10.2026). Deshalb gibt das
Skript bei jeder Aufnahme das Seitenverhaeltnis von Quelle und abgelegter
Datei aus und legt ein Kontrollbild ab: oben die Quelle, unten das Logo so,
wie der Lebenslauf es setzt. Dieses Bild ansehen und mit dem Logo auf der
Seite der Firma vergleichen. Wirkt die Schrift gestreckt oder gestaucht oder
weicht das Verhaeltnis von der Quelle ab: nicht aufnehmen, die Datei wieder
entfernen. Das Kontrollbild liegt neben der Quelle (<quelle>-kontrolle.png),
bei einer URL im Arbeitsverzeichnis — nie in der Bibliothek.

Downloads funktionieren nur dort, wo das Netz offen ist (lokal, Claude Desktop).
Im Browser-Chat blockt der Proxy fremde Domains mit host_not_allowed — dort die
Datei von Hand ablegen und dieses Skript mit dem lokalen Pfad aufrufen.
"""
import re
import shutil
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_cv import (  # noqa: E402  — erst nach sys.path.insert moeglich
    LOGO_GROESSE, masse_aus_verhaeltnis, svg_masse, verhaeltnis_der_datei,
)

ZIEL = Path(__file__).resolve().parent.parent / "assets" / "logos"
# Ab dieser Abweichung ist ein anderes Seitenverhaeltnis keine Rundung mehr,
# sondern ein gestrecktes oder gestauchtes Logo — gleich wie in figma_plan.py.
TOLERANZ = 0.01


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
    argumente = list(sys.argv[1:])
    kontrolle = None
    if "--kontrolle" in argumente:
        stelle = argumente.index("--kontrolle")
        if stelle + 1 >= len(argumente):
            raise SystemExit("--kontrolle braucht einen Dateinamen")
        kontrolle = Path(argumente[stelle + 1]).expanduser()
        del argumente[stelle:stelle + 2]
    if len(argumente) < 2:
        raise SystemExit(__doc__)
    quelle_arg, name = argumente[0], slugify(argumente[1])
    bibliothek_bereit()

    tmp = ZIEL / f".eingang-{name}"
    try:
        quelle = holen(quelle_arg, tmp)
        endung = Path(str(quelle_arg).split("?")[0]).suffix.lower()
        vorher = vorhandene_verhaeltnisse(name)
        ziel = als_svg(quelle, name) if endung == ".svg" else als_bild(quelle, name)
        if kontrolle is None:
            kontrolle = kontrollbild_pfad(quelle_arg, name)
        groesse = ziel.stat().st_size
        print(f"{ziel.name} abgelegt ({groesse // 1024} KB)")
        verhaeltnis_pruefen(quelle, ziel, vorher, kontrolle)
    finally:
        if tmp.exists():
            tmp.unlink()
    print(f'In der cv.json eintragen als:  "logo": "{ziel.name}"')


# --- Seitenverhaeltnis und Kontrollbild ---------------------------------------

def _zahl(wert):
    """1.8611 -> '1,861' — der Bericht wird gelesen, nicht geparst."""
    return f"{wert:.3f}".replace(".", ",")


def vorhandene_verhaeltnisse(name):
    """Seitenverhaeltnis der Bibliotheksdatei, die gleich ersetzt wird — je
    Endung, gemessen bevor sie ueberschrieben ist."""
    return {p.suffix.lower(): verhaeltnis_der_datei(p)
            for p in (ZIEL / f"{name}.svg", ZIEL / f"{name}.png") if p.exists()}


def kontrollbild_pfad(quelle_arg, name):
    """Neben die Quelle, wenn sie eine lokale Datei ist und der Ordner
    beschreibbar; sonst ins Arbeitsverzeichnis. Nie in die Bibliothek: dort
    hielte logos_ergaenzen.py das Kontrollbild fuer ein Logo."""
    text = str(quelle_arg)
    if not text.startswith(("http://", "https://")):
        quelle = Path(text).expanduser().resolve()
        if quelle.parent != ZIEL.resolve() and _beschreibbar(quelle.parent):
            return quelle.parent / f"{quelle.stem}-kontrolle.png"
    return Path.cwd() / f"{name}-kontrolle.png"


def _beschreibbar(ordner):
    try:
        probe = ordner / ".kontrolle-schreibtest"
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _svg_breite_hoehe(pfad):
    """Verhaeltnis aus width/height und ob preserveAspectRatio="none" gesetzt
    ist. Ein Browser zeigt das SVG in width/height, render_cv.py rechnet mit
    der viewBox — passen beide nicht zusammen, sieht das Logo je nach Programm
    anders aus, mit "none" sogar verzerrt. Gelesen wie in render_cv.py."""
    rohdaten = Path(pfad).read_bytes()
    kopf = re.search(rb"<svg\b[^>]*>", rohdaten, re.S)
    keins = bool(kopf and re.search(rb'preserveAspectRatio\s*=\s*["\']\s*none',
                                    kopf.group(0)))
    return svg_masse(rohdaten)[1], keins


def verhaeltnis_pruefen(quelle, ziel, vorher, kontrolle):
    """Seitenverhaeltnis ausgeben, Abweichungen melden, Kontrollbild ablegen.

    Pflicht bei jeder Aufnahme (SKILL.md, Schritt 3): Das Skript selbst skaliert
    nur gleichmaessig und schneidet Rand ab — ein anderes Verhaeltnis als die
    Quelle kommt also nur vom Zuschnitt. Eine Quelle, die selbst schon gestaucht
    ist, erkennt keine Rechnung; die sieht man nur. Gibt die Warnungen zurueck.
    """
    warnungen = []
    neu = verhaeltnis_der_datei(ziel)
    if not neu:
        warnungen.append(f"Seitenverhaeltnis von {ziel.name} nicht lesbar — "
                         "render_cv.py setzt es dann 1:1 und verzerrt das Logo.")
    if ziel.suffix.lower() == ".svg":
        breit_hoch, keins = _svg_breite_hoehe(ziel)
        print(f"Seitenverhaeltnis: viewBox {_zahl(neu) if neu else '?'}:1"
              + (f", width/height {_zahl(breit_hoch)}:1" if breit_hoch else ""))
        if neu and breit_hoch and abs(breit_hoch / neu - 1) > TOLERANZ:
            warnungen.append(
                f"viewBox ({_zahl(neu)}:1) und width/height ({_zahl(breit_hoch)}:1) "
                "passen nicht zusammen. Der Lebenslauf rechnet mit der viewBox, "
                "ein Browser mit width/height — eins von beiden zeigt das Logo "
                "falsch. Datei korrigieren oder eine andere Quelle nehmen.")
        if keins:
            # Allein kein Fehler (connox, porsche, synaos tragen es): render_cv.py
            # setzt jedes SVG in seinem eigenen Verhaeltnis. Es nimmt aber jedem
            # falschen Rahmen die Gegenwehr — deshalb gesagt, nicht gewarnt.
            print('  Hinweis: preserveAspectRatio="none" — das SVG folgt jedem '
                  "Rahmen, auch einem falsch proportionierten. In Figma die "
                  "Verhaeltnispruefung aus references/figma.md laufen lassen.")
    else:
        try:
            from PIL import Image
            with Image.open(quelle) as roh:
                qb, qh = roh.size
            with Image.open(ziel) as fertig:
                zb, zh = fertig.size
        except Exception:
            qb = qh = zb = zh = 0
        if qb and qh and zb and zh:
            print(f"Seitenverhaeltnis: Quelle {qb} x {qh} px ({_zahl(qb / qh)}:1) -> "
                  f"Bibliothek {zb} x {zh} px ({_zahl(zb / zh)}:1)")
            if abs((zb / zh) / (qb / qh) - 1) > TOLERANZ:
                print("  Der Unterschied kommt vom abgeschnittenen Rand, nicht vom "
                      "Skalieren — skaliert wird nur gleichmaessig. Im Kontrollbild "
                      "pruefen, dass das Logo selbst gleich aussieht.")
    for endung, alt in vorher.items():
        if endung == ziel.suffix.lower() and alt and neu and abs(neu / alt - 1) > TOLERANZ:
            warnungen.append(
                f"Die ersetzte Datei {ziel.name} hatte {_zahl(alt)}:1, die neue hat "
                f"{_zahl(neu)}:1. Eine von beiden ist verzerrt oder anders "
                "beschnitten — im Kontrollbild nachsehen, bevor sie bleibt.")

    gerendert = sichtpruefung(ziel)
    gemacht = kontrollbild(quelle, ziel, gerendert, kontrolle, neu)
    for w in warnungen:
        print(f"WARNUNG: {w}")
    if gemacht:
        print(f"Kontrollbild: {gemacht}")
        print("  Pflicht: ansehen und mit dem Logo der Firma vergleichen. Wirkt die "
              "Schrift gestreckt oder gestaucht oder weicht das Verhaeltnis von der "
              f"Quelle ab, nicht aufnehmen — {ziel.name} wieder entfernen.")
    else:
        print("Kein Kontrollbild moeglich (Pillow, WeasyPrint oder pdftoppm fehlt) — "
              f"{ziel.name} von Hand mit der Quelle vergleichen.")
    return warnungen


def _svg_als_bild(pfad, breite, hoehe):
    """Ein SVG in genau breite x hoehe pt rastern, 300 dpi. None ohne Werkzeug."""
    try:
        from weasyprint import HTML
        from PIL import Image
    except ImportError:
        return None
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        pdf, png = f"{tmp}/p.pdf", f"{tmp}/p"
        HTML(
            string=f'<style>@page{{size:{breite}pt {hoehe}pt;margin:0}}'
                   'body{margin:0;background:#fff}'
                   f'img{{display:block;width:{breite}pt;height:{hoehe}pt}}</style>'
                   f'<img src="{Path(pfad).name}">',
            base_url=str(Path(pfad).parent),
        ).write_pdf(pdf)
        try:
            subprocess.run(["pdftoppm", "-png", "-r", "300", pdf, png],
                           check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            return None
        return Image.open(f"{png}-1.png").convert("RGB")


def kontrollbild(quelle, ziel, gerendert, pfad, verhaeltnis):
    """Oben die Quelle, wie sie geliefert wurde, unten das Logo so, wie der
    Lebenslauf es setzt — beide gleich hoch, darueber die Verhaeltnisse.
    Gibt den Pfad zurueck oder None, wenn es sich nicht bauen liess."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    if gerendert is None:
        return None
    hoehe = 160
    try:
        if Path(quelle).suffix.lower() == ".svg" or ziel.suffix.lower() == ".svg":
            # Die Quelle so, wie ein Browser sie zeigt: in width/height, wenn
            # das SVG sie traegt, sonst in der viewBox.
            breit_hoch = _svg_breite_hoehe(ziel)[0] or verhaeltnis or 1.0
            oben = _svg_als_bild(ziel, round(40 * breit_hoch, 2), 40)
            q_text = f"Quelle (SVG, wie im Browser): {_zahl(breit_hoch)}:1"
        else:
            roh = Image.open(quelle)
            q_text = f"Quelle: {roh.width} x {roh.height} px, {_zahl(roh.width / roh.height)}:1"
            if roh.mode in ("RGBA", "LA", "P"):
                roh = roh.convert("RGBA")
                weiss = Image.new("RGBA", roh.size, (255, 255, 255, 255))
                roh = Image.alpha_composite(weiss, roh)
            oben = roh.convert("RGB")
    except Exception:
        oben = None
    if oben is None:
        return None

    def auf_hoehe(bild):
        return bild.resize((max(1, round(bild.width * hoehe / bild.height)), hoehe))

    teile = [(q_text, auf_hoehe(oben)),
             (f"Bibliothek, wie im Lebenslauf gesetzt: "
              f"{_zahl(verhaeltnis) if verhaeltnis else '?'}:1", auf_hoehe(gerendert))]
    rand, zeile = 20, 24
    breite = max(b.width for _, b in teile) + 2 * rand
    gesamt = rand + sum(zeile + b.height + rand for _, b in teile)
    blatt = Image.new("RGB", (max(breite, 520), gesamt), (255, 255, 255))
    stift = ImageDraw.Draw(blatt)
    y = rand
    for text, bild in teile:
        stift.text((rand, y), text, fill=(17, 17, 17))
        y += zeile
        blatt.paste(bild, (rand, y))
        # Haarlinie um das Bild: zeigt, wo die Datei endet — ein Logo, das an
        # die Kante stoesst, ist angeschnitten.
        stift.rectangle((rand - 1, y - 1, rand + bild.width, y + bild.height),
                        outline=(200, 200, 200))
        y += bild.height + rand
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    blatt.save(pfad)
    return pfad


def sichtpruefung(ziel):
    """Logo in Einsatzgroesse rendern und zaehlen, was sichtbar bleibt.

    Faengt jede Ursache ab, aus der ein Logo leer oder unleserlich herauskommt —
    falsch bestimmte Farben, zu duenne Striche, kaputte Pfade. Gibt das
    gerenderte Bild zurueck (fuers Kontrollbild), None ohne Werkzeuge.
    """
    # Einsatzgroesse heisst: das Mass, das render_cv.py diesem Logo als
    # Stationslogo gibt — aus seinem Seitenverhaeltnis, nicht aus einem festen
    # Kasten. Sonst misst die Deckung bei flachen Schriftzuegen nur den
    # Weissraum ueber und unter ihnen. Gelesen wird die Datei selbst, nicht
    # ihr Name in der Bibliothek: so geht es auch ausserhalb von assets/logos/.
    verhaeltnis = verhaeltnis_der_datei(ziel) or 1.0
    breite, hoehe = masse_aus_verhaeltnis(verhaeltnis, LOGO_GROESSE[1])
    bild = _svg_als_bild(ziel, breite, hoehe)
    if bild is None:
        return None

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
    return bild


if __name__ == "__main__":
    main()
