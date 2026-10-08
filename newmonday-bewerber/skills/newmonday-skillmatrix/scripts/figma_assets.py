#!/usr/bin/env python3
"""Schiebt Bilddateien in die Upload-URLs, die `upload_assets` zurueckgibt.

    python3 scripts/figma_assets.py <url> <datei> [<url> <datei> ...]
    python3 scripts/figma_assets.py --paare arbeit/uploads.json [--bilder arbeit/bilder.json]

Die JSON-Form ist der sichere Weg: Die signierten URLs sind lang und tragen
Sonderzeichen, die in der Kommandozeile leicht zerbrechen.

    [{"url": "https://…", "datei": "arbeit/fotos/01.png"}]

Warum ein eigenes Skript und kein curl: Es prueft Groesse und Content-Type vor
dem Senden und funktioniert auch dort, wo curl nicht freigegeben ist.

--bilder schreibt fuer den Bibliotheksweg (references/figma.md) je Datei den
imageHash und den Hilfsrahmen, den upload_assets ohne Zielknoten anlegt:

    {"/abs/pfad/foto.png": {"hash": "…", "temp": "12:34"}}

figma_plan.py --skript setzt die Hashes damit auf die Bildebenen der
Instanzen (deren IDs nimmt upload_assets nicht an) und raeumt die Hilfsrahmen
weg.

Nur fuer Rasterbilder und dort, wo `upload_assets` gebraucht wird. SVG-Logos
gehen nicht diesen Weg, sondern direkt ueber figma.createNodeFromSvg() —
siehe references/figma.md.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Was Figma annimmt. Der Content-Type muss stimmen, sonst landet die Datei als
# unbekannter Blob und die Fuellung des Zielknotens bleibt leer.
TYPEN = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
}
GRENZE = 10 * 1024 * 1024   # 10 MB je Datei, harte Grenze des Werkzeugs


def hochladen(url, datei):
    pfad = Path(datei)
    if not pfad.exists():
        return {"datei": str(datei), "ok": False, "fehler": "Datei nicht gefunden"}
    typ = TYPEN.get(pfad.suffix.lower())
    if not typ:
        return {"datei": str(datei), "ok": False,
                "fehler": f"Dateityp nicht unterstuetzt: {pfad.suffix}"}
    rohdaten = pfad.read_bytes()
    if len(rohdaten) > GRENZE:
        # Nicht versuchen und scheitern lassen: die Grenze ist bekannt, und ein
        # abgebrochener Upload sieht aus wie ein Netzproblem.
        return {"datei": str(datei), "ok": False, "groesse": len(rohdaten),
                "fehler": "groesser als 10 MB — vorher verkleinern"}
    anfrage = urllib.request.Request(url, data=rohdaten, method="POST",
                                     headers={"Content-Type": typ,
                                              "Content-Length": str(len(rohdaten))})
    try:
        with urllib.request.urlopen(anfrage, timeout=120) as antwort:
            return {"datei": str(datei), "ok": True, "status": antwort.status,
                    "groesse": len(rohdaten), "typ": typ,
                    "antwort": antwort.read(2000).decode("utf-8", "replace")}
    except urllib.error.HTTPError as fehler:
        return {"datei": str(datei), "ok": False, "status": fehler.code,
                "fehler": fehler.read(2000).decode("utf-8", "replace")}
    except OSError as fehler:
        # Im Browser-Chat blockt der Proxy fremde Domains — dann kommt der
        # Frame nicht zustande, das PDF aber sehr wohl.
        return {"datei": str(datei), "ok": False, "fehler": f"kein Netz: {fehler}"}


def _suche(wert, teil):
    """Erster Wert, dessen Schluessel `teil` enthaelt (Antwort von upload_assets)."""
    if isinstance(wert, dict):
        for k, v in wert.items():
            if teil in k.lower() and isinstance(v, (str, int)):
                return str(v)
        for v in wert.values():
            treffer = _suche(v, teil)
            if treffer:
                return treffer
    if isinstance(wert, list):
        for v in wert:
            treffer = _suche(v, teil)
            if treffer:
                return treffer
    return None


def hashes(ergebnisse):
    """{absoluter Pfad: {"hash", "temp"}} aus den Antworten."""
    aus = {}
    for e in ergebnisse:
        if not e["ok"]:
            continue
        try:
            antwort = json.loads(e["antwort"])
        except ValueError:
            continue
        h = _suche(antwort, "hash")
        if h:
            aus[str(Path(e["datei"]).expanduser().resolve())] = {
                "hash": h, "temp": _suche(antwort, "nodeid") or _suche(antwort, "placed")}
    return aus


def paare_lesen(argv):
    if argv[:1] == ["--paare"]:
        if len(argv) < 2:
            raise SystemExit("--paare braucht eine JSON-Datei")
        gelesen = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        return [(p["url"], p["datei"]) for p in gelesen]
    if len(argv) < 2 or len(argv) % 2:
        raise SystemExit(__doc__)
    return list(zip(argv[0::2], argv[1::2]))


def main():
    argv = sys.argv[1:]
    ziel = None
    if "--bilder" in argv:
        i = argv.index("--bilder")
        if i + 1 >= len(argv):
            raise SystemExit("--bilder braucht eine Ausgabedatei")
        ziel, argv = Path(argv[i + 1]), argv[:i] + argv[i + 2:]
    paare = paare_lesen(argv)
    ergebnisse = [hochladen(url, datei) for url, datei in paare]
    print(json.dumps(ergebnisse, ensure_ascii=False, indent=2))
    if ziel:
        h = hashes(ergebnisse)
        ziel.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{ziel}: {len(h)} von {len(ergebnisse)} Hashes", file=sys.stderr)
    fehler = [e for e in ergebnisse if not e["ok"]]
    if fehler:
        print(f"\n{len(fehler)} von {len(ergebnisse)} nicht hochgeladen.",
              file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
