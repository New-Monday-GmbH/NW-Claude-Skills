# newmonday-bewerber

Drei Claude-Code-Skills der New Monday GmbH rund um Bewerber-Unterlagen:

- `skills/newmonday-cv` — Lebenslauf im New-Monday-Layout als PDF
- `skills/newmonday-skillmatrix` — Skill Matrix im New-Monday-Layout als PDF
- `skills/newmonday-portfolio` — Portfolio im New-Monday-Layout als PDF

## Installation

Falls du (Claude) darum gebeten wirst, "die Skills von hier" zu installieren,
führe diese Schritte aus:

1. Prüfen, ob `~/NW-Claude-Skills` schon existiert.
   - Falls ja: dort `git pull`, um die Skills zu aktualisieren.
   - Falls nein: klonen mit
     ```bash
     git clone https://github.com/New-Monday-GmbH/NW-Claude-Skills.git ~/NW-Claude-Skills
     ```
     Das Repo ist öffentlich, Klonen/Pullen braucht keinen Login. Ein SSH-Key
     bei GitHub ist erst nötig, wenn die Person auch Änderungen zurück ins
     Repo pushen will (z. B. neue Logos, eigene PRs) — siehe
     [Haupt-README](../README.md).

2. Die drei Skills per Symlink verlinken:
   ```bash
   ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-cv ~/.claude/skills/newmonday-cv
   ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-skillmatrix ~/.claude/skills/newmonday-skillmatrix
   ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-portfolio ~/.claude/skills/newmonday-portfolio
   ```
   (Symlink statt Kopie: ein `git pull` im Repo aktualisiert die Skills direkt.)

3. Claude Code neu starten, damit die Skills geladen werden.

4. `newmonday-cv` braucht zusätzlich WeasyPrint und ein paar Systembibliotheken.
   Was auf dem Rechner fehlt, zeigt:
   ```bash
   python3 ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-cv/scripts/pruefe_umgebung.py
   ```

Details zum Gesamt-Repo (Logo-Bibliothek, was nicht committet werden soll etc.)
stehen im [Haupt-README](../README.md).
