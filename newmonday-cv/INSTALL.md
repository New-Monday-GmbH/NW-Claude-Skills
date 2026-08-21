# Installation

## Claude Code — der einfache Weg

```bash
bash install-newmonday-cv.sh newmonday-cv.skill
```

Das Skript entpackt, findet `SKILL.md` auch dann, wenn beim Entpacken eine
Ordnerebene zu viel entstanden ist, legt alles an der richtigen Stelle ab, prüft
die Abhängigkeiten und sagt, was fehlt. Bei einer Aktualisierung sichert es die
alte Fassung und übernimmt die gewachsene Logobibliothek.

Mit `--projekt` landet der Skill in `.claude/skills/` des aktuellen Projekts
statt unter `~/.claude/skills/`. Dann wandert er über Git ins Team, und die
Logobibliothek wächst für alle mit.

Danach Claude Code neu starten.

## Von Hand

```bash
mkdir -p ~/.claude/skills
unzip newmonday-cv.skill -d ~/.claude/skills/
ls ~/.claude/skills/newmonday-cv/SKILL.md      # muss existieren
```

**Der Ordnername ist der Befehl.** `~/.claude/skills/newmonday-cv/SKILL.md`
ergibt `/newmonday-cv`. Liegt die Datei eine Ebene tiefer, etwa unter
`newmonday-cv/newmonday-cv/SKILL.md`, findet Claude Code den Skill nicht — das
passiert regelmäßig, wenn man das Archiv im Finder per Doppelklick öffnet.

## Wenn `/newmonday-cv` nicht auftaucht

Der Reihe nach:

```bash
ls ~/.claude/skills/newmonday-cv/SKILL.md    # 1. Liegt die Datei richtig?
```

Fehlt sie, ist es fast immer die zusätzliche Ordnerebene. Das Installationsskript
oben räumt das auf.

Liegt sie richtig, in Claude Code:

- `/skills` — listet alle geladenen Skills
- `/doctor` — meldet Ladefehler
- Frag Claude direkt: *Welche Skills stehen zur Verfügung?*

Bleibt es dabei, mit `claude --debug` starten. Dort steht, warum ein Skill nicht
geladen wurde.

Zwei Dinge, die man leicht übersieht: Claude Code muss neu gestartet werden, wenn
der Ordner `~/.claude/skills/` vorher gar nicht existierte. Und persönliche Skills
aus `~/.claude/skills/` werden in Cowork- und Cloud-Sitzungen nicht geladen — dafür
muss der Skill entweder im Projekt liegen oder für das claude.ai-Konto aktiviert
sein.

## Abhängigkeiten

```bash
python3 ~/.claude/skills/newmonday-cv/scripts/pruefe_umgebung.py
```

Nennt für dein System die passenden Befehle. Auf macOS meist:

```bash
brew install python-pango pango libffi gdk-pixbuf poppler potrace
pip3 install weasyprint jinja2 pypdf pillow
```

`pango` ist der Teil, an dem WeasyPrint auf macOS am häufigsten scheitert — ohne
die Bibliothek startet der Import nicht.

## Figma (optional)

Der Skill kann den fertigen Lebenslauf zusätzlich als bearbeitbaren Frame in ein
Figma-File legen. Das ist eine Zugabe: **ohne Figma läuft der Skill vollständig**,
das PDF entsteht genauso.

Gebraucht wird dafür:

- **Die Figma-MCP-Anbindung**, verbunden und angemeldet. In Claude Code über
  `claude mcp` bzw. `/mcp` in einer interaktiven Sitzung, in den claude.ai-Apps
  über die Connector-Einstellungen. Ist sie nicht angemeldet, meldet der Skill das
  und liefert nur das PDF.
- **Bearbeitungsrechte** auf der Zieldatei. Ein Betrachter-Link genügt nicht.
- **Eine Design-Datei**, also ein Link der Form `figma.com/design/…`. FigJam
  (`/board/`), Slides (`/slides/`), Make (`/make/`) und Prototypen (`/proto/`)
  lassen sich nicht beschreiben.
- **`pypdf`**, siehe Abhängigkeiten. Ohne es lässt sich die Seitenaufteilung nicht
  aus dem PDF lesen, und ohne die wird kein Frame gebaut.

Gefragt wird gleich zu Beginn, zusammen mit der Sprache — mitschicken muss man nur
den Link zur Datei.

**Warum der Skill keine `allowed-tools`-Zeile mehr hat:** Sie zählte auf, welche
Werkzeuge der Skill benutzen darf. Der Name des Figma-Servers steht aber nicht fest
— je nach Installation heißt er `mcp__figma__use_figma` oder trägt eine ID, die sich
ändern kann. Ein Name, der nicht passt, hätte den Figma-Teil stillschweigend
lahmgelegt. Ohne die Zeile gelten die normalen Berechtigungsregeln: Claude Code
fragt beim ersten Aufruf nach, danach nicht mehr. Wer die Zeile zurück will, findet
sie in den Schwesterskills `newmonday-portfolio` und `newmonday-skillmatrix`.

## Selbsttest

```bash
python3 ~/.claude/skills/newmonday-cv/scripts/selbsttest.py
```

Rendert den mitgelieferten Beispiel-Lebenslauf und prüft das Ergebnis: A4-Format,
eingebettete Inter-Schnitte, Logos und Foto. Läuft der durch, funktioniert die
ganze Kette. Das Installationsskript ruft ihn am Ende von selbst auf.

## Ohne WeasyPrint

Der Skill weicht auf Chrome im Kopflos-Modus aus. Das erzeugt ein PDF, aber
**das Layout ist auf WeasyPrint abgestimmt**: Bei Seitenumbrüchen und den
Skillset-Spalten kann Chrome abweichen. Dann das Ergebnis vor dem Versand einmal
ganz durchsehen.

## Was der Skill in seinen Ordner schreibt

Nur eines: neue Logos in `assets/logos/`. Das ist beabsichtigt, die Bibliothek
soll mit jedem Kandidaten wachsen. Zwischenstände beim Rendern und das
heruntergeladene Icon-Paket liegen außerhalb, unter `~/.cache/newmonday-cv`
beziehungsweise im temporären Verzeichnis.

## Erster Lauf

Lebenslauf und LinkedIn-Export in einen Ordner legen, Claude Code dort starten:

> Mach aus diesem Lebenslauf einen im New Monday Layout

Der Skill fragt zuerst nach der Sprache und nach den Firmenlogos. Die Einzelteile
lassen sich auch ohne Claude aufrufen:

```bash
S=~/.claude/skills/newmonday-cv
python3 $S/scripts/extract_input.py eingang.pdf arbeit/
python3 $S/scripts/logos_ergaenzen.py cv.json
python3 $S/scripts/render_cv.py cv.json ausgabe/
```
