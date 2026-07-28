#!/usr/bin/env python3
"""Round-Trip-Pruefung fuer eine Folien-Vorlage.

    check_slide.py <template.html> <content.json> <erwartet.html> [<erwartet2.html> ...]

content.json ist entweder ein Objekt (eine Folie) oder eine Liste von Objekten
(mehrere Instanzen desselben Typs, z. B. die vier Erkenntnis-Folien). Es wird
je Instanz gerendert und gegen die erwartete Original-Folie verglichen.

Verglichen wird normalisiert (Whitespace zwischen Tags), weil Einrueckung im
HTML bedeutungslos ist -- aber NICHT der Inhalt: jedes Zeichen Text zaehlt.
Exit 0 = identisch, Exit 1 = Abweichung (mit Diff).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck_render import render, TemplateError  # noqa: E402
from deck_content import enrich, ContentError  # noqa: E402


def normalize(html):
    """Einrueckung/Zeilenumbrueche egalisieren, Textinhalt unangetastet lassen."""
    h = html.strip()
    h = re.sub(r">\s+<", "><", h)          # Whitespace zwischen Tags
    h = re.sub(r"\s*\n\s*", " ", h)        # Umbrueche im Text -> ein Space
    h = re.sub(r"[ \t]{2,}", " ", h)
    return h.strip()


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2

    tpl_path, json_path = Path(sys.argv[1]), Path(sys.argv[2])
    expected_paths = [Path(p) for p in sys.argv[3:]]

    tpl = tpl_path.read_text()
    data = json.loads(json_path.read_text())
    items = data if isinstance(data, list) else [data]

    if len(items) != len(expected_paths):
        print(f"FAIL: {len(items)} JSON-Eintraege, aber {len(expected_paths)} Erwartungs-Dateien")
        return 1

    ok = True
    for item, exp_path in zip(items, expected_paths):
        try:
            # enrich() genau wie im Build, sonst prueft der Check etwas anderes,
            # als der Builder spaeter erzeugt.
            got = render(tpl, enrich({"type": tpl_path.stem, **item}))
        except (TemplateError, ContentError) as e:
            print(f"FAIL {exp_path.name}: {e}")
            ok = False
            continue

        want = exp_path.read_text()
        if normalize(got) == normalize(want):
            print(f"OK   {exp_path.name}")
            continue

        ok = False
        print(f"FAIL {exp_path.name}: gerendert != Original")
        g, w = normalize(got), normalize(want)
        # erste Abweichung zeigen
        i = next((k for k in range(min(len(g), len(w))) if g[k] != w[k]), min(len(g), len(w)))
        lo = max(0, i - 90)
        print(f"  ab Zeichen {i}:")
        print(f"  ORIGINAL : ...{w[lo:i+90]}")
        print(f"  GERENDERT: ...{g[lo:i+90]}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
