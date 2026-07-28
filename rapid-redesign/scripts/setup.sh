#!/usr/bin/env bash
# Richtet eine lokale venv mit Playwright + Chromium ein.
# Nutzt bewusst `uv` mit einem EIGENSTÄNDIGEN Python (nicht den System-/Xcode-Python):
# Apples Library-Validation blockiert dort fremde C-Extensions wie `greenlet`
# ("library load disallowed by system policy" bzw. die Gatekeeper-Warnung
# "kann nicht auf Schadsoftware geprüft werden"). Ein uv-Python umgeht das.
# Idempotent: existiert die venv samt Playwright/Chromium schon, passiert nichts Teures.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
export PATH="$HOME/.local/bin:$PATH"

# 1) uv sicherstellen (user-lokal, kein Admin/Homebrew nötig)
if ! command -v uv >/dev/null 2>&1; then
  echo "→ Installiere uv (user-lokal nach ~/.local/bin)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2) venv mit eigenständigem Python 3.12 anlegen
if [ ! -x "$VENV/bin/python" ]; then
  echo "→ Erstelle venv mit eigenständigem Python 3.12 unter $VENV"
  uv python install 3.12
  uv venv "$VENV" --python 3.12 --seed
fi

# 3) Playwright installieren
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet playwright

# 4) Chromium installieren, nur wenn noch nicht vorhanden
if ! "$VENV/bin/python" -c "from playwright.sync_api import sync_playwright; \
    p=sync_playwright().start(); \
    import os,sys; sys.exit(0 if os.path.exists(p.chromium.executable_path) else 1)" 2>/dev/null; then
  echo "→ Installiere Chromium für Playwright"
  "$VENV/bin/python" -m playwright install chromium
fi

# 5) macOS-Quarantäne von den kompilierten Bibliotheken entfernen (harmlos auf anderen OS)
xattr -dr com.apple.quarantine "$VENV" 2>/dev/null || true

echo "✓ Setup fertig. Nutze: scripts/.venv/bin/python scripts/audit_capture.py ..."
