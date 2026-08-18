#!/usr/bin/env python3
"""Holt das Profilfoto von einem oeffentlichen LinkedIn-Profil.

    python3 scripts/linkedin_foto.py "https://www.linkedin.com/in/timo-muster" arbeit/

Legt das fertig zugeschnittene Graustufenfoto in arbeit/fotos/ ab — im selben
Format wie extract_input.py, das Ergebnis ist direkt als "foto" in die cv.json
eintragbar.

Wie das geht: Die oeffentliche Profilseite liefert das Foto in den
Meta-Tags mit, wenn man sie mit einem Browser-User-Agent und mit Redirects
abruft. Ohne beides antwortet LinkedIn mit HTTP 999 beziehungsweise 301 —
daher die Login-Wall-Meldung, die man sonst zu sehen bekommt.

Grenzen, die nicht am Skript liegen:
  - Nur oeffentliche Profile. Steht die Fotosichtbarkeit auf "Nur Kontakte"
    oder ist das Profil nicht oeffentlich, ist kein Foto zu holen.
  - Hoechste erreichbare Aufloesung ist 400x400. Die Signatur in der Bild-URL
    gilt je Groesse, groessere Varianten antworten mit 403.
"""
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_input import portraet_zuschneiden  # noqa: E402

# Ohne Browser-User-Agent antwortet LinkedIn mit HTTP 999.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Nur Portraetfotos. Schneidet Firmenlogos und Hintergrundbanner derselben
# Seite aus, die ueber dieselbe Bilddomain kommen.
FOTO_URL = re.compile(
    r'https://media\.licdn\.com/dms/image/v2/(?P<id>[^/]+)/'
    r'profile-displayphoto[a-z_-]*_(?P<breite>\d+)_(?P<hoehe>\d+)[^"\'\\ ]*'
)
OG_IMAGE = re.compile(r'og:image"\s+content="([^"]+)"')
VANITY = re.compile(r'^[A-Za-z0-9\-_%À-ÿ]{3,100}$')


def url_normalisieren(eingabe):
    """Akzeptiert volle URLs, de.linkedin.com, blanke Vanity-Namen."""
    eingabe = eingabe.strip().strip('<>').rstrip('/')
    if not eingabe:
        raise SystemExit("Kein Profil angegeben.")
    if "linkedin.com" in eingabe:
        treffer = re.search(r'linkedin\.com/in/([^/?#]+)', eingabe)
        if not treffer:
            raise SystemExit(
                f"Das sieht nicht nach einem Profil-Link aus: {eingabe}\n"
                "Gebraucht wird die Form linkedin.com/in/name — "
                "nicht /company/, /posts/ oder /feed/."
            )
        vanity = treffer.group(1)
    else:
        vanity = eingabe
    if not VANITY.match(vanity):
        raise SystemExit(f"Unbrauchbarer Profilname: {vanity!r}")
    return f"https://www.linkedin.com/in/{vanity}/", vanity


def seite_laden(url, versuche=3):
    """Profilseite holen, mit Backoff gegen die Abwehr von LinkedIn.

    HTTP 999 ist doppeldeutig und laesst sich von aussen nicht aufloesen:
    es kommt sowohl bei nicht existierenden oder nicht oeffentlichen
    Profilen als auch dann, wenn zu viele Abrufe kurz hintereinander
    laufen — im Test antworteten zuvor funktionierende Profile nach
    einigen Abrufen ploetzlich ebenfalls mit 999. Deshalb wird
    nachgefasst, statt beim ersten 999 aufzugeben.
    """
    anfrage = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    for versuch in range(1, versuche + 1):
        try:
            # urllib folgt Redirects von selbst — ohne sie kommt nur ein 301.
            with urllib.request.urlopen(anfrage, timeout=30) as antwort:
                return antwort.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as fehler:
            if fehler.code == 404:
                raise SystemExit(
                    f"{url}\nProfil nicht gefunden (404). "
                    "Schreibweise der Profil-URL pruefen."
                )
            if fehler.code == 999 and versuch < versuche:
                wartezeit = 5 * 2 ** (versuch - 1)
                print(f"LinkedIn blockt (999), neuer Versuch in {wartezeit}s …",
                      file=sys.stderr)
                time.sleep(wartezeit)
                continue
            if fehler.code == 999:
                raise SystemExit(
                    f"{url}\nLinkedIn hat den Abruf {versuche}x mit 999 "
                    "abgewiesen. Das heisst eines von beiden:\n"
                    "  - Das Profil gibt es nicht oder es ist nicht "
                    "oeffentlich sichtbar (Schreibweise im ausgeloggten "
                    "Browser gegenpruefen), oder\n"
                    "  - es liefen zu viele Abrufe kurz hintereinander; "
                    "dann hilft ein paar Minuten warten.\n"
                    "Bleibt es dabei: Foto aus dem LinkedIn-PDF-Export "
                    "ziehen oder beim Kandidaten anfragen."
                )
            raise SystemExit(f"Abruf fehlgeschlagen (HTTP {fehler.code}).")
        except urllib.error.URLError as fehler:
            raise SystemExit(
                f"Kein Netz zu linkedin.com: {fehler.reason}\n"
                "Im Browser-Chat blockt der Proxy fremde Domains — dort das "
                "Foto aus dem LinkedIn-PDF-Export ziehen oder beim Kandidaten "
                "anfragen."
            )


def entmaskieren(url):
    """Die URLs stehen teils in JSON-Bloecken, also & maskiert."""
    return url.replace("\\u0026", "&").replace("&amp;", "&")


def foto_urls(html):
    """Kandidaten fuer das Foto DIESER Person, groesste Variante zuerst.

    Wichtig: Auf der oeffentlichen Profilseite stehen unter "Weitere
    aehnliche Profile" die Fotos fremder Personen — gemessen 13 fremde
    neben dem einen echten, und ausgerechnet die fremden liegen in der
    groesseren 400er-Variante vor. Wer einfach das groesste Bild der Seite
    nimmt, laedt verlaesslich ein falsches Gesicht in den Lebenslauf.

    Verankert wird deshalb am og:image-Tag: der gehoert immer zum Profil
    selbst. Aus seiner Media-ID ergibt sich, welche der vielen Bild-URLs
    dieselbe Person zeigen; nur unter denen wird die groesste gesucht.
    """
    treffer_og = OG_IMAGE.search(html)
    if not treffer_og:
        return []
    og_url = entmaskieren(treffer_og.group(1))

    person = FOTO_URL.search(og_url)
    if not person:
        return []          # Platzhalter-Avatar oder Firmenlogo, kein Foto
    person_id = person.group("id")

    gefunden = {og_url: 0}   # das og:image gilt als sichere Rueckfallebene
    for kandidat in FOTO_URL.finditer(html):
        if kandidat.group("id") != person_id:
            continue         # fremdes Gesicht aus der Seitenspalte
        url = entmaskieren(kandidat.group(0))
        gefunden[url] = int(kandidat.group("breite")) * int(kandidat.group("hoehe"))
    return sorted(gefunden, key=gefunden.get, reverse=True)


def bild_laden(url, ziel):
    anfrage = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        daten = antwort.read()
    if len(daten) < 1024:
        raise ValueError("Antwort zu klein fuer ein Foto")
    ziel.write_bytes(daten)
    return ziel


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    url, vanity = url_normalisieren(sys.argv[1])
    ziel = Path(sys.argv[2])
    fotos = ziel / "fotos"
    fotos.mkdir(parents=True, exist_ok=True)

    html = seite_laden(url)
    kandidaten = foto_urls(html)

    if not kandidaten:
        # Zwei verschiedene Faelle, die der Nutzer unterschiedlich loest.
        if "authwall" in html or "Anmelden" in html[:5000] or len(html) < 50_000:
            raise SystemExit(
                f"{url}\nLinkedIn hat statt des Profils die Login-Wall "
                "ausgeliefert. Das Foto laesst sich so nicht holen — "
                "LinkedIn-PDF-Export nutzen oder Foto anfragen."
            )
        raise SystemExit(
            f"{url}\nProfil erreichbar, aber kein Profilfoto darin. "
            "Entweder hat die Person keins hinterlegt oder die Sichtbarkeit "
            "steht auf 'Nur Kontakte'. Foto beim Kandidaten anfragen."
        )

    roh = ziel / "roh"
    roh.mkdir(parents=True, exist_ok=True)
    letzter_fehler = None
    for url_bild in kandidaten:
        try:
            datei = bild_laden(url_bild, roh / f"linkedin-{vanity}.jpg")
            break
        except Exception as fehler:      # 403 bei zu grosser Variante
            letzter_fehler = fehler
    else:
        raise SystemExit(
            f"Foto gefunden, aber nicht ladbar ({letzter_fehler}). "
            "Foto beim Kandidaten anfragen."
        )

    from PIL import Image
    breite, hoehe = Image.open(datei).size
    ergebnis = portraet_zuschneiden(datei, fotos, pruefen=False)
    if not ergebnis:
        raise SystemExit("Bild nicht verwertbar.")

    print(f"Foto: {ergebnis}")
    print(f"Quelle: {url} ({breite}x{hoehe} px)")
    # Die Fotokarte im Hero ist 433pt breit, also 433/72 Zoll — sechsmal so
    # breit wie der Fotokasten im CV. Das 400px-Thumbnail von LinkedIn kommt
    # damit nur auf rund 65 dpi und ist auf der Karte sichtbar weich. Die
    # Matrix wird meist am Bildschirm gelesen, deshalb liegt die Grenze bei
    # 100 dpi statt der 200 aus dem CV-Skill — darunter lohnt immer die
    # Anfrage nach einem richtigen Foto.
    dpi = round(Image.open(ergebnis).size[0] / (433 / 72))
    print(f"Aufloesung im Layout: ~{dpi} dpi")
    if dpi < 100:
        print("Hinweis: unter 100 dpi auf der grossen Fotokarte — sichtbar "
              "weich. Ein schaerferes Foto beim Kandidaten anfragen lohnt sich; "
              "oft liegt im Lebenslauf oder Portfolio ein groesseres.")


if __name__ == "__main__":
    main()
