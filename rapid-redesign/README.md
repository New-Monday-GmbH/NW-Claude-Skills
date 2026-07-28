# Rapid Redesign — Claude-Skill

Erzeugt aus einer Website-URL ein vollständiges **New-Monday-Rapid-Redesign-Deck**:
Playwright crawlt und vermisst die ganze Site, Claude bewertet strategisch und
technisch, und der Build setzt daraus ein lokales Folien-Deck (statische Website)
inkl. Admin-Modus zum Nachbearbeiten.

> **Intern.** Enthält das New-Monday-Design-System, Kundenlogos für die
> Referenz-Folie und Angebots-Richtwerte. Dieses Repo bleibt **privat**.

---

## Installation auf einem neuen Rechner

```bash
git clone <REPO-URL> ~/.claude/skills/rapid-redesign
bash ~/.claude/skills/rapid-redesign/scripts/setup.sh
```

`setup.sh` legt eine eigene Python-Umgebung mit Playwright + Chromium unter
`scripts/.venv` an (per `uv`, ohne Admin-Rechte, ~2 Minuten). Sie wird bewusst
**nicht** mit ausgeliefert — sie ist maschinenspezifisch.

Danach in Claude Code einfach fragen, z. B.:

> „Mach ein Rapid Redesign für example.com"

Der Skill greift automatisch. Die Ergebnisse (`audits/<domain>-<datum>/`)
entstehen **im aktuellen Projektordner**, nicht hier im Skill.

## Updates holen

```bash
cd ~/.claude/skills/rapid-redesign && git pull
```

## Am Skill arbeiten

| Wo | Was |
|---|---|
| `SKILL.md` | Der Ablauf, den Claude befolgt — die zentrale Datei |
| `references/` | Fachwissen: Prüf-Raster, Zielgruppen-Profile, Deck-Schema, Design-System (`site-styles.css`) |
| `templates/` | Eine HTML-Vorlage je Folientyp + `deck.head/tail`, `catalog.json` |
| `scripts/` | `audit_capture.py` (Playwright), `build_deck.py` (deck.json → index.html) |
| `tests/` | `check_deck.py` — prüft, dass die Vorlagen die Referenz-Folien reproduzieren |

Nach **jeder** Änderung an `templates/` oder `references/site-styles.css`:

```bash
scripts/.venv/bin/python tests/check_deck.py
```

Schlägt der Test fehl, war die Änderung entweder ungewollt — oder gewollt, dann
die Goldens unter `tests/reference/slides/` bewusst nachziehen und im Commit
begründen.

## Was NICHT im Repo liegt

- `audits/` — Ergebnisse einzelner Läufe (gehören ins jeweilige Projekt)
- `scripts/.venv/` — Python-Umgebung, wird von `setup.sh` erzeugt

Deshalb überspringt `check_deck.py` seinen zweiten Teil (Vergleich gegen das
freigegebene Referenz-Deck) in einem frischen Checkout — Teil 1 prüft alle
Folientypen trotzdem vollständig.
