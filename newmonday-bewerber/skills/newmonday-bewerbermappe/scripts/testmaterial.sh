#!/usr/bin/env bash
# Legt Testmaterial ohne echte Kandidatendaten an: den Beispiel-Lebenslauf
# aus newmonday-cv (beispiel/cv.json) als gerendertes PDF.
#
#   bash scripts/testmaterial.sh <zielordner>
#
# Ergebnis: <zielordner>/lebenslauf.pdf. Schreibt nichts in die Skill-Ordner.
set -euo pipefail
ZIEL="${1:?Zielordner fehlt}"
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CV="$(cd "$HIER/../../newmonday-cv" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
( cd "$CV" && python3 scripts/render_cv.py beispiel/cv.json "$TMP/" >/dev/null 2>&1 )
mkdir -p "$ZIEL"
mv "$TMP"/*.pdf "$ZIEL/lebenslauf.pdf"
echo "$ZIEL/lebenslauf.pdf"
