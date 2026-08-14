#!/usr/bin/env python3
"""Prueft, ob die Umgebung alles mitbringt, und sagt sonst, was fehlt.

    python3 scripts/pruefe_umgebung.py

Vor dem ersten Lauf aufrufen — besonders in Claude Code, wo der Skill auf dem
Rechner des Nutzers laeuft und nicht in einer vorbereiteten Sandbox.
"""
import importlib.util
import platform
import shutil
import sys

PY_PAKETE = [
    ("weasyprint", "Rendert das PDF. Ohne sie faellt der Skill auf Chrome zurueck."),
    ("jinja2", "Fuellt das Template. Zwingend."),
    ("pypdf", "Zaehlt Seiten fuer die Umbruchpruefung. Zwingend."),
    ("PIL", "Bearbeitet Fotos und Logos. Zwingend."),
]
WERKZEUGE = [
    ("pdftotext", "Liest den Eingangs-Lebenslauf.", True),
    ("pdfimages", "Holt das Foto aus dem PDF.", True),
    ("pdftoppm", "Sichtpruefung der Logos.", False),
    ("potrace", "Vektorisiert zu kleine Logos.", False),
]

BEFEHLE = {
    "Darwin": [
        "brew install python-pango pango libffi gdk-pixbuf   # fuer WeasyPrint",
        "brew install poppler potrace",
        "pip3 install weasyprint jinja2 pypdf pillow",
    ],
    "Linux": [
        "sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 poppler-utils potrace",
        "pip3 install weasyprint jinja2 pypdf pillow",
    ],
    "Windows": [
        "WeasyPrint braucht GTK. Einfacher: Chrome installiert lassen,",
        "der Skill nutzt ihn als Ausweichweg.",
        "pip install jinja2 pypdf pillow",
        "poppler und potrace ueber scoop oder chocolatey nachziehen.",
    ],
}


def chrome_da():
    import os
    kandidaten = [
        "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    return any(shutil.which(k) or os.path.exists(k) for k in kandidaten)


def main():
    fehlt_hart, fehlt_weich = [], []
    print(f"System: {platform.system()} {platform.machine()}, Python {sys.version.split()[0]}\n")

    print("Python-Pakete")
    for name, zweck in PY_PAKETE:
        da = importlib.util.find_spec(name) is not None
        print(f"  {'ok ' if da else 'FEHLT'}  {name:12} {zweck}")
        if not da:
            (fehlt_weich if name == "weasyprint" else fehlt_hart).append(name)

    print("\nKommandozeilenwerkzeuge")
    for name, zweck, noetig in WERKZEUGE:
        da = shutil.which(name) is not None
        print(f"  {'ok ' if da else 'FEHLT'}  {name:12} {zweck}")
        if not da:
            (fehlt_hart if noetig else fehlt_weich).append(name)

    print("\nRender-Engine")
    if importlib.util.find_spec("weasyprint"):
        print("  ok    WeasyPrint — das Layout ist darauf abgestimmt.")
    elif chrome_da():
        print("  ok    Chrome als Ausweichweg. Ergebnis bitte gegenpruefen:")
        print("        Seitenumbrueche und Spalten koennen abweichen.")
    else:
        fehlt_hart.append("Render-Engine")
        print("  FEHLT weder WeasyPrint noch Chrome — es entsteht kein PDF.")

    if not fehlt_hart and not fehlt_weich:
        print("\nAlles da. Der Skill laeuft.")
        return

    if fehlt_hart:
        print(f"\nZwingend nachzuziehen: {', '.join(fehlt_hart)}")
    if fehlt_weich:
        print(f"Empfohlen, sonst mit Einschraenkungen: {', '.join(fehlt_weich)}")

    print("\nInstallation:")
    for zeile in BEFEHLE.get(platform.system(), BEFEHLE["Linux"]):
        print(f"  {zeile}")


if __name__ == "__main__":
    main()
