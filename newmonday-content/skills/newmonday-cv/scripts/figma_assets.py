#!/usr/bin/env python3
"""Schiebt Bilddateien in die Upload-URLs, die `upload_assets` zurueckgibt.

    python3 scripts/figma_assets.py <url> <datei> [<url> <datei> ...]
    python3 scripts/figma_assets.py --paare arbeit/uploads.json

Die JSON-Form ist der sichere Weg: Die signierten URLs sind lang und tragen
Sonderzeichen, die in der Kommandozeile leicht zerbrechen.

    [{"url": "https://…", "datei": "arbeit/fotos/01.png"}]

Warum ein eigenes Skript und kein curl: Der Skill gibt in `allowed-tools` nur
`Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*)` frei. So bleibt die Zeile, wie sie
ist, und der Weg funktioniert auch dort, wo curl nicht freigegeben ist.

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
    paare = paare_lesen(sys.argv[1:])
    ergebnisse = [hochladen(url, datei) for url, datei in paare]
    print(json.dumps(ergebnisse, ensure_ascii=False, indent=2))
    fehler = [e for e in ergebnisse if not e["ok"]]
    if fehler:
        print(f"\n{len(fehler)} von {len(ergebnisse)} nicht hochgeladen.",
              file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
