"""PDF/UA-1 mit veraPDF pruefen, wenn es installiert ist (brew install verapdf).

Dieselbe Datei liegt in newmonday-cv, -skillmatrix und -portfolio. veraPDF
prueft lokal die maschinell pruefbaren Regeln von PDF/UA-1 (Matterhorn-
Protokoll) - wie PAC und axesCheck, aber ohne Upload und ohne Captcha
(Entscheidung vom 09.11.2026). Fehlt es, bleibt es bei der Eigenpruefung des
Skills und einem Hinweis.
"""
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

_hinweis_gegeben = False


def pruefe(pdf):
    """Verletzte PDF/UA-1-Regeln als Textliste; [] wenn bestanden oder veraPDF fehlt."""
    global _hinweis_gegeben
    exe = shutil.which("verapdf")
    if not exe:
        if not _hinweis_gegeben:
            print("Hinweis: veraPDF ist nicht installiert (brew install verapdf) – PDF/UA-1 "
                  "nur mit der Eigenpruefung des Skills geprueft.", file=sys.stderr)
            _hinweis_gegeben = True
        return []
    try:
        lauf = subprocess.run([exe, "-f", "ua1", "--format", "xml", str(pdf)],
                              capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return ["veraPDF: nach 5 Minuten abgebrochen – PDF/UA-1 ungeprueft"]
    try:
        bericht = ET.fromstring(lauf.stdout).find(".//validationReport")
    except ET.ParseError:
        bericht = None
    if bericht is None:
        return [f"veraPDF: kein Pruefbericht – {' '.join(lauf.stderr.split())[-200:]}"]
    if bericht.get("isCompliant") == "true":
        return []
    return [f"veraPDF PDF/UA-1 {r.get('clause')}-{r.get('testNumber')} "
            f"({r.get('failedChecks')}x): {' '.join((r.findtext('description') or '').split())}"
            for r in bericht.iter("rule") if r.get("status") == "failed"]


if __name__ == "__main__":
    # python3 verapdf.py <pdf> ... - Exit 1, sobald eins durchfaellt.
    if not shutil.which("verapdf"):
        sys.exit("veraPDF ist nicht installiert: brew install verapdf")
    durchgefallen = False
    for datei in sys.argv[1:]:
        fehler = pruefe(datei)
        print(("FAIL " if fehler else "PASS ") + datei)
        for f in fehler:
            print(f"  - {f}")
        durchgefallen |= bool(fehler)
    sys.exit(1 if durchgefallen else 0)
