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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system  # noqa: E402  — nach sys.path.insert

PY_PAKETE = [
    ("weasyprint", "Rendert die PDFs. Ohne sie faellt die lange Fassung auf Chrome zurueck, "
                   "die A4-Fassung entfaellt."),
    ("jinja2", "Fuellt das Template. Zwingend."),
    ("pypdf", "Zaehlt Seiten und legt die Seitenaufteilung der A4-Fassung ab (fuer Figma). Empfohlen."),
    ("PIL", "Bearbeitet Fotos und misst die Seitenhoehe. Zwingend."),
    ("fitz", "PyMuPDF — schnellste Hoehenmessung. Sonst pdftoppm+Pillow."),
]
WERKZEUGE = [
    ("pdftotext", "Liest Lebenslauf und LinkedIn-Export.", True),
    ("pdfimages", "Holt das Foto aus dem PDF.", True),
    ("pdftoppm", "Zertifikate rendern, Seitenhoehe messen, Sichtpruefung.", True),
]

BEFEHLE = {
    "Darwin": [
        "brew install python-pango pango libffi gdk-pixbuf   # fuer WeasyPrint",
        "brew install poppler",
        "pip3 install weasyprint jinja2 pypdf pillow pymupdf",
        "xcode-select --install   # swiftc fuer die Kopferkennung beim Fotozuschnitt",
    ],
    "Linux": [
        "sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 poppler-utils",
        "pip3 install weasyprint jinja2 pypdf pillow pymupdf",
    ],
    "Windows": [
        "WeasyPrint braucht GTK. Einfacher: Chrome installiert lassen,",
        "der Skill nutzt ihn als Ausweichweg.",
        "pip install jinja2 pypdf pillow pymupdf",
        "poppler ueber scoop oder chocolatey nachziehen.",
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
            (fehlt_hart if name in ("jinja2", "PIL") else fehlt_weich).append(name)

    print("\nKommandozeilenwerkzeuge")
    for name, zweck, noetig in WERKZEUGE:
        da = shutil.which(name) is not None
        print(f"  {'ok ' if da else 'FEHLT'}  {name:12} {zweck}")
        if not da:
            (fehlt_hart if noetig else fehlt_weich).append(name)

    print("\nSchriften (assets/tokens.json)")
    design = design_system.laden()
    fehlend = design_system.schriften_fehlen(design)
    for datei in fehlend:
        print(f"  FEHLT {datei.name:26} ohne sie rendert jede Engine still eine Ersatzschrift")
    if fehlend:
        fehlt_hart.append("Schriftdateien (Google Fonts, OFL — Namen in tokens.json)")
    else:
        print(f"  ok    {', '.join(design['schriften'])} liegen in assets/fonts/.")

    print("\nKopferkennung fuer den Fotozuschnitt")
    import kopf_ausschnitt
    if kopf_ausschnitt.swift_da():
        print("  ok    macOS Vision ueber swiftc - der Kopf wird automatisch zentriert.")
    else:
        fehlt_weich.append("Kopferkennung")
        print("  FEHLT kein macOS mit Command Line Tools - Fotos werden mittig/oben buendig geschnitten;")
        print("        den Kopf dann von Hand angeben: kopf_ausschnitt.py … --kopf x0,y0,x1,y1")

    print("\nRender-Engine")
    if importlib.util.find_spec("weasyprint"):
        print("  ok    WeasyPrint — das Layout ist darauf abgestimmt.")
    elif chrome_da():
        print("  ok    Chrome als Ausweichweg. Ergebnis bitte gegenpruefen.")
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
