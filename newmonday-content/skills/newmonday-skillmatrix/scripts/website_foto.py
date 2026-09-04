#!/usr/bin/env python3
"""Sucht ein Profilfoto auf der Website oder im Portfolio des Bewerbers.

    python3 scripts/website_foto.py "https://timo-muster.de" arbeit/

Legt die Kandidaten fertig zugeschnitten in arbeit/fotos/ ab — im selben Format
wie extract_input.py und linkedin_foto.py, also direkt als "foto" in die cv.json
eintragbar. Gedacht als dritter Weg, wenn der Lebenslauf kein Foto mitbringt und
LinkedIn keins hergibt: viele Portfolios tragen auf "Ueber mich" ein besseres
Bild als das 400x400-Thumbnail von LinkedIn.

Anders als bei LinkedIn ist hier nicht sicher, wer auf dem Bild zu sehen ist.
Eine Portfolioseite zeigt Teamfotos, Kundengesichter, Stockmaterial und
Projektbilder. Das Skript sortiert nur aus, was technisch kein Portraet sein
kann (querformatig, winzig, zweifarbig) — WER da steht, muss angesehen werden.
"""
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_input import portraet_zuschneiden  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Unterseiten, auf denen das Portraet ueblicherweise steht. Die Startseite wird
# immer gelesen, diese hier nur, wenn sie von dort verlinkt sind.
UNTERSEITEN = ("ueber", "uber", "about", "profil", "profile", "team", "person",
               "vita", "cv", "lebenslauf", "kontakt", "contact", "me")
MAX_SEITEN = 4
MAX_BILDER = 14

OG_IMAGE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I)
IMG_SRC = re.compile(r'<img\b[^>]*?\bsrc=["\']([^"\']+)["\']', re.I)
IMG_SRCSET = re.compile(r'<img\b[^>]*?\bsrcset=["\']([^"\']+)["\']', re.I)
LINKS = re.compile(r'<a\b[^>]*?\bhref=["\']([^"\']+)["\']', re.I)
# Dateinamen, die nie ein Portraet sind. Der Rest wird am Bild selbst gemessen.
KEIN_FOTO = re.compile(r'(logo|icon|favicon|sprite|placeholder|avatar-default)', re.I)


def laden(url, timeout=30):
    anfrage = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,image/*",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(anfrage, timeout=timeout) as antwort:
        return antwort.read()


def seite_laden(url):
    try:
        return laden(url).decode("utf-8", "replace")
    except urllib.error.HTTPError as fehler:
        if fehler.code in (401, 403, 406, 429):
            raise SystemExit(
                f"{url}\nDie Seite weist automatische Abrufe ab "
                f"(HTTP {fehler.code}). Daran ist nichts zu drehen — das Foto "
                "aus dem LinkedIn-Export ziehen oder beim Kandidaten anfragen."
            )
        raise SystemExit(f"{url}\nAbruf fehlgeschlagen (HTTP {fehler.code}).")
    except urllib.error.URLError as fehler:
        raise SystemExit(
            f"Kein Netz zu {url}: {fehler.reason}\n"
            "Im Browser-Chat blockt der Proxy fremde Domains — dort das Foto "
            "beim Kandidaten anfragen."
        )


def bild_urls(html, basis):
    """Bildadressen einer Seite, og:image zuerst. Absolut und ohne Dubletten."""
    gefunden = []
    for treffer in OG_IMAGE.findall(html):
        gefunden.append(treffer)
    for treffer in IMG_SRC.findall(html):
        gefunden.append(treffer)
    for satz in IMG_SRCSET.findall(html):
        # Groesste Variante des srcset: "bild-400.jpg 400w, bild-800.jpg 800w"
        varianten = []
        for teil in satz.split(","):
            stuecke = teil.split()
            if stuecke:
                breite = re.match(r"(\d+)w", stuecke[-1]) if len(stuecke) > 1 else None
                varianten.append((int(breite.group(1)) if breite else 0, stuecke[0]))
        if varianten:
            gefunden.append(max(varianten)[1])

    sauber, gesehen = [], set()
    for roh in gefunden:
        roh = roh.strip()
        if not roh or roh.startswith("data:"):
            continue
        url = urllib.parse.urljoin(basis, roh)
        if url.lower().split("?")[0].endswith(".svg") or KEIN_FOTO.search(url):
            continue                      # Vektorgrafik oder erkennbar kein Foto
        if url not in gesehen:
            gesehen.add(url)
            sauber.append(url)
    return sauber


def unterseiten(html, basis):
    """Bis zu MAX_SEITEN-1 Unterseiten derselben Domain, die nach Portraet klingen."""
    heim = urllib.parse.urlparse(basis).netloc
    treffer, gesehen = [], {basis.rstrip("/")}
    for roh in LINKS.findall(html):
        url = urllib.parse.urljoin(basis, roh.strip()).split("#")[0].rstrip("/")
        teile = urllib.parse.urlparse(url)
        if teile.netloc != heim or url in gesehen:
            continue
        pfad = teile.path.lower()
        if any(w in pfad for w in UNTERSEITEN):
            gesehen.add(url)
            treffer.append(url)
        if len(treffer) >= MAX_SEITEN - 1:
            break
    return treffer


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    start = sys.argv[1].strip().strip("<>")
    if not start.startswith(("http://", "https://")):
        start = "https://" + start
    ziel = Path(sys.argv[2])
    fotos, roh = ziel / "fotos", ziel / "roh"
    fotos.mkdir(parents=True, exist_ok=True)
    roh.mkdir(parents=True, exist_ok=True)

    html = seite_laden(start)
    kandidaten = bild_urls(html, start)
    for weiter in unterseiten(html, start):
        try:
            kandidaten += [u for u in bild_urls(seite_laden(weiter), weiter)
                           if u not in kandidaten]
        except SystemExit:
            continue                      # eine tote Unterseite bricht nichts ab
    if not kandidaten:
        raise SystemExit(f"{start}\nKeine Bilder auf der Seite gefunden.")

    treffer = []
    for nummer, url in enumerate(kandidaten[:MAX_BILDER], start=1):
        try:
            daten = laden(url, timeout=20)
        except Exception:
            continue
        if len(daten) < 4096:             # zu klein fuer ein brauchbares Portraet
            continue
        endung = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
        datei = roh / f"web-{nummer:02d}{endung}"
        datei.write_bytes(daten)
        try:
            # pruefen=True: querformatige, winzige und zweifarbige Bilder fallen
            # raus — das sind die Projektbilder und Grafiken drumherum.
            ergebnis = portraet_zuschneiden(datei, fotos)
        except Exception:
            continue
        if ergebnis:
            treffer.append((ergebnis, url))

    if not treffer:
        raise SystemExit(
            f"{start}\nKein Portraet gefunden — die Seite fuehrt nur Grafiken "
            "und querformatige Bilder. Foto beim Kandidaten anfragen."
        )

    from PIL import Image
    print("Portraetkandidaten (groesster zuerst pruefen):")
    for ergebnis, url in sorted(treffer, key=lambda p: p[0].stat().st_size, reverse=True):
        # Die Fotokarte im Hero ist 433pt breit, also 433/72 Zoll.
        dpi = round(Image.open(ergebnis).size[0] / (433 / 72))
        hinweis = "  — unter 100 dpi, auf der grossen Fotokarte sichtbar weich" if dpi < 100 else ""
        print(f"  {ergebnis}  ~{dpi} dpi{hinweis}")
        print(f"    Quelle: {url}")
    print("\nAnsehen, bevor eins davon ins Dokument geht: eine Website zeigt "
          "auch Teamfotos, Kundengesichter und Stockmaterial.")


if __name__ == "__main__":
    main()
