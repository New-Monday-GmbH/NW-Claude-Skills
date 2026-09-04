#!/usr/bin/env python3
"""Prueft, ob die Umgebung alles mitbringt, und sagt sonst, was fehlt.

    python3 scripts/pruefe_umgebung.py

Vor dem ersten Lauf auf einem unbekannten Rechner aufrufen. Der Skill laeuft in
Claude Code auf dem Rechner des Nutzers, nicht in einer vorbereiteten Sandbox -
was hier fehlt, faellt sonst erst mitten im Rendern auf.
"""
import importlib.util
import platform
import shutil
import sys
from pathlib import Path

PAKETE = [
    ("weasyprint", True, "Rendert das PDF. Fehlt sie, weicht der Skill auf "
                         "Chrome aus – dann Seitenumbrüche gegenprüfen."),
    ("fitz", True, "PyMuPDF: liest Eingangs-PDFs aus und misst das Ergebnis "
                   "auf Überlauf. Zwingend."),
    ("PIL", True, "Pillow: schneidet Fotos zu und liest Bildmaße. Zwingend."),
]
WERKZEUGE = [
    ("pdftoppm", False, "Sichtprüfung einzelner Seiten in hoher Auflösung."),
    ("potrace", False, "Vektorisiert zu kleine Logos beim Nachlegen."),
]
BEFEHLE = {
    "Darwin": ["brew install python-pango pango libffi gdk-pixbuf",
               "brew install poppler potrace",
               "pip3 install weasyprint pymupdf pillow"],
    "Linux": ["sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 "
              "poppler-utils potrace",
              "pip3 install weasyprint pymupdf pillow"],
    "Windows": ["WeasyPrint braucht GTK. Einfacher ist es, Chrome installiert "
                "zu lassen – der Skill nutzt ihn als Ausweichweg.",
                "pip install pymupdf pillow"],
}


def main() -> None:
    fehlt_zwingend, fehlt_optional = [], []

    for name, zwingend, zweck in PAKETE:
        da = importlib.util.find_spec(name) is not None
        print(f"  {'ok ' if da else 'FEHLT'} {name:12} {zweck}")
        if not da:
            (fehlt_zwingend if zwingend else fehlt_optional).append(name)

    for name, zwingend, zweck in WERKZEUGE:
        da = shutil.which(name) is not None
        print(f"  {'ok ' if da else '  · '} {name:12} {zweck}")
        if not da:
            (fehlt_zwingend if zwingend else fehlt_optional).append(name)

    chrome = any(Path(p).exists() for p in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("google-chrome") or "x", shutil.which("chromium") or "x"))
    print(f"  {'ok ' if chrome else '  · '} {'Chrome':12} "
          "Ausweichweg, falls WeasyPrint fehlt.")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from logo_lib import bibliothek
    ordner = bibliothek()
    anzahl = len([p for p in ordner.iterdir() if p.suffix in (".svg", ".png")])
    geteilt = "gemeinsam mit newmonday-cv" if "newmonday-cv" in str(ordner) else "eigen"
    print(f"  ok  {'Logos':12} {anzahl} Stück in {ordner} ({geteilt})")

    if fehlt_zwingend:
        print("\nEs fehlt: " + ", ".join(fehlt_zwingend))
        print("Diese Befehle helfen auf " + platform.system() + ":")
        for b in BEFEHLE.get(platform.system(), BEFEHLE["Linux"]):
            print("  " + b)
        sys.exit(1)
    if fehlt_optional:
        print("\nOptional fehlt: " + ", ".join(fehlt_optional)
              + " – der Skill läuft trotzdem.")
    print("\nAlles da.")


if __name__ == "__main__":
    main()
