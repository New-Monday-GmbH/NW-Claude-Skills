# NW Claude Skills

Claude-Code-Skills der New Monday GmbH. Jeder Skill liegt in einem eigenen
Ordner und ist für sich installierbar.

| Skill | Was er macht |
|-------|--------------|
| [`rapid-redesign`](rapid-redesign/) | Erzeugt ein komplettes New-Monday-Rapid-Redesign: UX/UI- und Usability-Audit einer ganzen Website (echter Browser via Playwright) und daraus ein fertiges Folien-Deck im RR-Stil. |

## Installation

Repository klonen (einmalig):

```bash
git clone https://github.com/New-Monday-GmbH/NW-Claude-Skills.git ~/NW-Claude-Skills
```

Gewünschten Skill in den Claude-Skills-Ordner verlinken:

```bash
ln -s ~/NW-Claude-Skills/rapid-redesign ~/.claude/skills/rapid-redesign
```

Ein Symlink statt einer Kopie sorgt dafür, dass ein `git pull` im Repo den
Skill direkt aktualisiert.

Falls der Skill eigene Abhängigkeiten braucht, liegt ein Setup-Skript bei —
bei `rapid-redesign` installiert es Playwright samt Chromium pro Rechner:

```bash
bash ~/.claude/skills/rapid-redesign/scripts/setup.sh
```

## Was hier NICHT hineingehört

Ergebnisse von Skill-Läufen (bei `rapid-redesign` die `audits/`-Ordner mit
Kundendaten) bleiben im jeweiligen Projekt und sind per `.gitignore`
ausgeschlossen. Dieses Repository enthält ausschließlich die Werkzeuge.
