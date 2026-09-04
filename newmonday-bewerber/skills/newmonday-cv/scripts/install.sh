#!/usr/bin/env bash
# Installiert den newmonday-cv-Skill für Claude Code.
#
#   bash install-newmonday-cv.sh newmonday-cv.skill            # persönlich
#   bash install-newmonday-cv.sh newmonday-cv.skill --projekt  # ins aktuelle Projekt
#
# Faengt den haeufigsten Fehler ab: Beim Entpacken per Doppelklick legt macOS
# eine zusaetzliche Ordnerebene an. Claude Code sucht SKILL.md aber genau eine
# Ebene unter skills/ und findet dann nichts. Das Skript sucht die Datei selbst,
# egal wie tief sie liegt.

set -euo pipefail

PAKET="${1:-}"
ZIEL_BASIS="$HOME/.claude/skills"
[ "${2:-}" = "--projekt" ] && ZIEL_BASIS="$PWD/.claude/skills"

if [ -z "$PAKET" ] || [ ! -f "$PAKET" ]; then
  echo "Aufruf: bash install-newmonday-cv.sh <pfad/zu/newmonday-cv.skill> [--projekt]" >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Entpacke ..."
unzip -q "$PAKET" -d "$TMP"

# SKILL.md in beliebiger Tiefe finden
GEFUNDEN="$(find "$TMP" -name SKILL.md -maxdepth 4 | head -1)"
if [ -z "$GEFUNDEN" ]; then
  echo "Im Paket ist keine SKILL.md. Ist das die richtige Datei?" >&2
  exit 1
fi
QUELLE="$(dirname "$GEFUNDEN")"

ZIEL="$ZIEL_BASIS/newmonday-cv"
if [ -d "$ZIEL" ]; then
  SICHERUNG="$ZIEL.alt-$(date +%Y%m%d-%H%M%S)"
  echo "Vorhandene Fassung wird gesichert nach $SICHERUNG"
  mv "$ZIEL" "$SICHERUNG"
  # Logobibliothek aus der alten Fassung mitnehmen, sie ist mühsam gewachsen
  if [ -d "$SICHERUNG/assets/logos" ]; then
    mkdir -p "$QUELLE/assets/logos"
    cp -n "$SICHERUNG/assets/logos/"* "$QUELLE/assets/logos/" 2>/dev/null || true
    echo "Logobibliothek aus der alten Fassung übernommen."
  fi
fi

mkdir -p "$ZIEL_BASIS"
cp -R "$QUELLE" "$ZIEL"

echo
echo "Installiert: $ZIEL/SKILL.md"
if [ -f "$ZIEL/SKILL.md" ]; then
  echo "Ordnername = Befehl, also:  /newmonday-cv"
else
  echo "FEHLER: SKILL.md liegt nicht an der erwarteten Stelle." >&2
  exit 1
fi

echo
echo "Abhängigkeiten:"
python3 "$ZIEL/scripts/pruefe_umgebung.py" || true

echo
echo "Selbsttest:"
python3 "$ZIEL/scripts/selbsttest.py" || echo "  -> Selbsttest fehlgeschlagen, siehe Meldung oben."

echo
echo "Claude Code neu starten, dann prüfen:"
echo "  /skills            zeigt die geladenen Skills"
echo "  /newmonday-cv      ruft ihn direkt auf"
echo "  /doctor            meldet Ladefehler"
