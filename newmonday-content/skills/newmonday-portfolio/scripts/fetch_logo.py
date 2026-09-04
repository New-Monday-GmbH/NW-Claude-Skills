#!/usr/bin/env python3
"""Sucht ein Firmenlogo im Netz und legt es in der Bibliothek ab.

    python3 scripts/fetch_logo.py "Deutsche Bank" deutsche-bank
    python3 scripts/fetch_logo.py "Hays" hays --domain hays.de

Probiert mehrere Quellen der Reihe nach und nimmt die erste, die etwas
Brauchbares liefert. Das Ergebnis laeuft anschliessend durch dieselbe
Aufbereitung wie add_logo.py: Rand abschneiden, zu kleine zweifarbige Logos
vektorisieren, Sichtpruefung in Einsatzgroesse.

BRAUCHT OFFENES NETZ. Lokal und in Claude Desktop funktioniert das; im
Browser-Chat blockt der Proxy fremde Domains mit host_not_allowed. Dort die
Datei von Hand hochladen und add_logo.py mit dem Pfad aufrufen.

Erste Quelle ist simple-icons ueber die npm-Registry: 3400+ Markenlogos, ohne
Schluessel, und npm ist auch dort erreichbar, wo sonst alles gesperrt ist.
Aber: simple-icons liefert grundsaetzlich einfarbig Schwarz. Das genuegt nur
fuer Marken, die selbst schwarz auftreten (ChatGPT, Midjourney, ElevenLabs) -
fuer farbige Marken (Claude, Gemini, Perplexity, Ford ...) gehoert die farbige
Original-Variante in die Bibliothek: Wikimedia Commons oder die Brand-Seite,
dann add_logo.py. Das Ergebnis dieser Kette immer ansehen, bevor es ins PDF
geht.

Optionale Schluessel als Umgebungsvariable, deutlich bessere Treffer:
    BRANDFETCH_KEY=...     (brandfetch.com, liefert oft echte SVG)
    LOGODEV_KEY=...        (logo.dev, Nachfolger der abgeschalteten Clearbit-API)
"""
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_logo import ZIEL, als_bild, als_svg, bibliothek_bereit, slugify  # noqa: E402

KOPF = {"User-Agent": "newmonday-cv/1.0 (Lebenslauf-Aufbereitung)"}


def datendatei():
    """Wie die Datendatei des Skills heisst, in dem dieses Skript liegt.

    Es liegt unveraendert in beiden: Der Lebenslauf fuehrt eine cv.json, das
    Portfolio eine portfolio.json. Erkannt am Renderer nebenan statt am
    Ordnernamen - der Renderer ist das, was den Unterschied wirklich ausmacht.
    Abgeleitet und nicht hingeschrieben, damit dieselbe Datei in beiden Skills
    das Richtige sagt; ein Import aus add_logo.py ginge nicht, das Skript
    unterscheidet sich zwischen den Skills.
    """
    return "portfolio.json" if (Path(__file__).resolve().parent
                                / "render_portfolio.py").exists() else "cv.json"


def _zwischenlager():
    """Cache ausserhalb des Skill-Ordners — der ist unter ~/.claude/skills/ oft
    schreibgeschuetzt und soll ohnehin nicht wachsen."""
    for kandidat in (Path.home() / ".cache" / "newmonday-cv",
                     Path(tempfile.gettempdir()) / "newmonday-cv"):
        try:
            kandidat.mkdir(parents=True, exist_ok=True)
            return kandidat
        except OSError:
            continue
    return Path(tempfile.gettempdir())


ZWISCHENLAGER = _zwischenlager()


def laden(url, kopf=None):
    anfrage = urllib.request.Request(url, headers={**KOPF, **(kopf or {})})
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        return antwort.read(), antwort.headers.get("Content-Type", "")


def aus_simple_icons(firma, _domain):
    """simple-icons ueber die npm-Registry — 3400+ einfarbige Markenlogos, CC0.

    Beste erste Quelle: kein Schluessel, keine Domain, und der einfarbige Stil
    passt zu den Logos, die im New-Monday-Layout ohnehin schon liegen.
    Abgeglichen wird auf den Titel, nicht auf den Dateinamen — sonst trifft
    "Hays" das voellig andere "Haystack".
    """
    import tarfile
    paket = ZWISCHENLAGER / "simple-icons"
    if not paket.exists():
        antwort = json.loads(laden("https://registry.npmjs.org/simple-icons/latest")[0])
        daten, _ = laden(antwort["dist"]["tarball"])
        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as f:
            f.write(daten)
            archiv = f.name
        paket.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archiv) as t:
            t.extractall(paket, filter="data")
        Path(archiv).unlink(missing_ok=True)

    wurzel = paket / "package"
    katalog = json.loads((wurzel / "data" / "simple-icons.json").read_text(encoding="utf-8"))
    eintraege = katalog.get("icons", katalog) if isinstance(katalog, dict) else katalog

    def normal(text):
        return re.sub(r"[^a-z0-9]", "", text.lower())

    gesucht = normal(firma)
    for eintrag in eintraege:
        namen = [eintrag["title"]] + list(eintrag.get("aliases", {}).get("aka", []))
        if any(normal(n) == gesucht for n in namen):       # exakt, nicht per Praefix
            datei = wurzel / "icons" / f"{eintrag['slug']}.svg"
            if datei.exists():
                return datei.read_bytes(), "svg", f"simple-icons ({eintrag['title']})"
    return None


def aus_wikimedia(firma, _domain):
    """Commons durchsuchen und die Datei ueber Special:FilePath holen.

    Ohne Schluessel nutzbar und bei bekannten Marken oft ein echtes SVG.
    """
    suche = (
        "https://commons.wikimedia.org/w/api.php?action=query&list=search"
        "&srnamespace=6&format=json&srlimit=5&srsearch="
        + urllib.parse.quote(f"{firma} logo")
    )
    treffer = json.loads(laden(suche)[0]).get("query", {}).get("search", [])
    for eintrag in treffer:
        name = eintrag["title"].removeprefix("File:").removeprefix("Datei:")
        if not name.lower().endswith((".svg", ".png")):
            continue
        pfad = "https://commons.wikimedia.org/wiki/Special:FilePath/" + \
            urllib.parse.quote(name.replace(" ", "_"))
        daten, _ = laden(pfad)
        if daten:
            return daten, name.lower().rsplit(".", 1)[-1], f"Wikimedia ({name})"
    return None


def aus_brandfetch(_firma, domain):
    schluessel = os.environ.get("BRANDFETCH_KEY")
    if not (schluessel and domain):
        return None
    antwort = json.loads(laden(
        f"https://api.brandfetch.io/v2/brands/{domain}",
        {"Authorization": f"Bearer {schluessel}"},
    )[0])
    kandidaten = []
    for logo in antwort.get("logos", []):
        for datei in logo.get("formats", []):
            kandidaten.append((datei.get("format"), datei.get("src")))
    kandidaten.sort(key=lambda k: 0 if k[0] == "svg" else 1)   # SVG zuerst
    for endung, url in kandidaten:
        if url:
            return laden(url)[0], endung, "Brandfetch"
    return None


def aus_logodev(_firma, domain):
    schluessel = os.environ.get("LOGODEV_KEY")
    if not (schluessel and domain):
        return None
    daten, typ = laden(f"https://img.logo.dev/{domain}?token={schluessel}&size=512")
    return daten, "svg" if "svg" in typ else "png", "logo.dev"


def aus_favicon(_firma, domain):
    """Notnagel: liefert nur die Bildmarke, keine Wortmarke, dafuer ohne Schluessel."""
    if not domain:
        return None
    daten, _ = laden(
        f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
    )
    return (daten, "png", "Favicon (nur Bildmarke)") if len(daten) > 800 else None


QUELLEN = [aus_simple_icons, aus_wikimedia, aus_brandfetch, aus_logodev, aus_favicon]


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    firma, name = sys.argv[1], slugify(sys.argv[2])
    domain = None
    if "--domain" in sys.argv:
        domain = sys.argv[sys.argv.index("--domain") + 1]

    bibliothek_bereit()
    tmp = ZIEL / f".suche-{name}"
    for quelle in QUELLEN:
        try:
            ergebnis = quelle(firma, domain)
        except Exception as fehler:
            print(f"  {quelle.__name__}: {fehler}")
            continue
        if not ergebnis:
            continue
        daten, endung, woher = ergebnis
        tmp.write_bytes(daten)
        try:
            ziel = als_svg(tmp, name) if endung == "svg" else als_bild(tmp, name)
        except Exception as fehler:
            print(f"  {woher}: nicht verwertbar ({fehler})")
            continue
        finally:
            tmp.unlink(missing_ok=True)
        print(f"Gefunden ueber {woher}: {ziel.name}")
        print("Bitte ansehen — automatisch gefundene Logos sind manchmal veraltet "
              "oder gehoeren zu einer gleichnamigen Firma.")
        print(f'In der {datendatei()} eintragen als:  "logo": "{ziel.name}"')
        return

    tmp.unlink(missing_ok=True)
    raise SystemExit(
        f"Kein Logo fuer '{firma}' gefunden. Von der Firmenseite laden und "
        "add_logo.py mit dem Pfad aufrufen."
    )


if __name__ == "__main__":
    main()
