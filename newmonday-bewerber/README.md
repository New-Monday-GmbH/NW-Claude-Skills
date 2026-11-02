# newmonday-bewerber

Vier Claude-Code-Skills der New Monday GmbH rund um Bewerber-Unterlagen:

- `skills/newmonday-cv` — Lebenslauf im New-Monday-Layout als PDF und Figma-Frames, vollständig und anonymisiert
- `skills/newmonday-skillmatrix` — Skill Matrix im New-Monday-Layout als PDF
- `skills/newmonday-portfolio` — Portfolio im New-Monday-Layout als PDF
- `skills/newmonday-bewerbermappe` — alle drei in einem Lauf: gemeinsame Fragen einmal, Lückencheck und Matching-Prüfung vorab, alle drei Dokumente auf die Anfrage aus dem Profilmatching ausgerichtet (Gewichtung, nie Beleg), Entscheidungen gebündelt (braucht die drei anderen daneben)

## Installation

Falls du (Claude) darum gebeten wirst, "die Skills von hier" zu installieren:
Das geht über diese zwei Befehle, die der Nutzer in Claude Code eintippt
(Terminal, Desktop-App im Code-Tab oder IDE):

```
/plugin marketplace add New-Monday-GmbH/NW-Claude-Skills
/plugin install newmonday-bewerber@nw-claude-skills
```

Ab Claude Code 2.1.275 geht es auch in einem Schritt:

```
/plugin install newmonday-bewerber --marketplace New-Monday-GmbH/NW-Claude-Skills
```

Danach Claude Code neu starten. Das Repo ist öffentlich, es braucht weder einen
GitHub-Zugang noch einen Account in der claude.ai-Organisation – ein privater
Claude-Account genügt. Im claude.ai-Chat (Browser) gibt es keine Plugins.

### Auto-Update einschalten

Einmal pro Person: `/plugin` → **Marketplaces** → `nw-claude-skills` →
**Enable auto-update**. Ab dann holt Claude Code jede Änderung auf `main` beim
Start; das Plugin hat bewusst keine Versionsnummer, jeder Commit ist ein Update.
Alternativ per `~/.claude/settings.json` oder für die ganze Organisation per
Managed Settings – siehe [Haupt-README](../README.md#auto-update-einschalten-einmal-pro-person).

### Was der Rechner braucht

`newmonday-cv` braucht WeasyPrint und ein paar Systembibliotheken. Was fehlt,
prüft der Skill beim ersten Lauf (`scripts/pruefe_umgebung.py`) und nennt die
Befehle dafür.

## Für die Pfleger

Wer die Skills per Symlink aus einem Checkout nutzt, installiert das Plugin
**nicht** zusätzlich – sonst stehen alle vier Skills doppelt da. Entweder
Symlinks oder Plugin; wie man wechselt, steht im [Haupt-README](../README.md#für-die-pfleger-symlink-oder-plugin-nie-beides).

Neue Logos landen bei allen in `~/.newmonday/logos/`, nicht im Plugin-Ordner
(den ersetzt jedes Update). Die Übergabe jedes Laufs nennt sie; in den
Grundstock im Repo holt sie `skills/newmonday-cv/scripts/logos_uebernehmen.py`.

Vor dem Push: `python3 scripts/selbsttest.py` in `newmonday-cv`,
`newmonday-portfolio` und `newmonday-bewerbermappe`. Jeder Commit auf `main`
geht per Auto-Update an alle – es gibt keine Version, hinter der sich ein
halbfertiger Stand verstecken könnte. Größere Umbauten auf einem Branch
machen und erst mergen, wenn die Selbsttests grün sind.
