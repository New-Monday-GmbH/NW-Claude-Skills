# Installation

## Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R newmonday-skillmatrix ~/.claude/skills/
ls ~/.claude/skills/newmonday-skillmatrix/SKILL.md      # muss existieren
```

**Der Ordnername ist der Befehl.** `~/.claude/skills/newmonday-skillmatrix/SKILL.md`
ergibt `/newmonday-skillmatrix`. Liegt die Datei eine Ebene tiefer
(`newmonday-skillmatrix/newmonday-skillmatrix/SKILL.md`), findet Claude Code
den Skill nicht — das passiert regelmäßig, wenn ein Archiv im Finder per
Doppelklick geöffnet wurde.

Danach Claude Code neu starten. Taucht `/newmonday-skillmatrix` nicht auf:
`/skills` listet die geladenen Skills, `/doctor` meldet Ladefehler,
`claude --debug` sagt, warum ein Skill nicht geladen wurde. Persönliche
Skills aus `~/.claude/skills/` werden in Cowork- und Cloud-Sitzungen nicht
geladen — dafür muss der Skill im Projekt (`.claude/skills/`) liegen oder für
das claude.ai-Konto aktiviert sein.

## Abhängigkeiten

```bash
python3 ~/.claude/skills/newmonday-skillmatrix/scripts/pruefe_umgebung.py
```

Nennt für dein System die passenden Befehle. Auf macOS meist:

```bash
brew install python-pango pango libffi gdk-pixbuf poppler
pip3 install weasyprint jinja2 pypdf pillow pymupdf
```

`pango` ist der Teil, an dem WeasyPrint auf macOS am häufigsten scheitert —
ohne die Bibliothek startet der Import nicht. Ohne WeasyPrint weicht der
Skill auf Chrome aus; das Layout ist aber auf WeasyPrint abgestimmt, das
Ergebnis dann einmal ganz durchsehen.

## Selbsttest

Die mitgelieferte Beispielmatrix (Wissems Vorlage) rendern:

```bash
cd ~/.claude/skills/newmonday-skillmatrix/beispiel
python3 ../scripts/render_skillmatrix.py skillmatrix.json /tmp/skillmatrix-beispiel.pdf
```

Läuft das durch und meldet `Seitenformat: 1440 x …pt`, funktioniert die
ganze Kette: Template, Schriften, Bilder, Höhenmessung.

## Erster Lauf

Lebenslauf, LinkedIn-Export und Portfolio in einen Ordner legen, Claude Code
dort starten:

> Mach mir daraus eine Skill Matrix im New Monday Layout

Der Skill fragt zuerst nach Sprache und Verfügbarkeit, liest dann die
Quellen und legt Auswahl und Bewertung der Attribute zur Freigabe vor,
bevor gerendert wird.
