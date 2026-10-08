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

Die mitgelieferte Beispielmatrix (Wissems Vorlage) rendern – es entstehen
beide Fassungen:

```bash
cd ~/.claude/skills/newmonday-skillmatrix/beispiel
python3 ../scripts/render_skillmatrix.py skillmatrix.json /tmp/
```

Sollwerte:

| | lang | A4 |
|---|---|---|
| Datei | `New-Monday - Wissem Kordi - Senior UX-UI Designer - Skillmatrix.pdf` | `… - Skillmatrix A4.pdf` |
| Meldung | `Seitenformat: 1444 x 3786pt, 33 Kartenschatten` und `Zertifikatssektion: 803pt hoch (8 Kacheln, geplant 803, Grenze 924)` | `Seitenformat A4: 595 x 842pt, 3 Seiten` |
| Inhalt | eine Seite | Seite 1 Hero und Zertifikate, Seite 2 Kernkompetenzen bis „User Research & Insights“, Seite 3 „Design Systems & Scaling“, „Coding Skills“, Tools und Fuß |

Unter „Pruefen:“ stehen genau zwei Hinweise („Product Thinking“ und „Workshop
Facilitation“ stehen in der nächstverwandten Kategorie „User Research &
Insights“) – keiner mit „A4:“, keiner zur Durchkopplung –, und zuletzt steht
`Design System eingehalten`. In der Vorschau sind die leeren Punkte Ringe,
gleich groß wie die vollen – lang 9, A4 5 auf Seite 2 und 4 auf Seite 3.
Dann funktioniert die ganze Kette: Templates, Tokens beider Fassungen,
Schriften, Schatten, Bilder samt A4-Fotozuschnitt (`material/foto-karte-a4.png`),
Qualifikationskarte, Zertifikatsplanung, Katalogprüfung, Durchkopplung,
Höhenmessung, Seitenumbruch und Fuß der A4-Fassung und die Designprüfung beider
PDFs, die den Ring (`roh/punkt-rahmen`) als Palettenfarbe kennt.

Die Figma-Pläne dazu, aus dem Ordner `beispiel/` heraus (relative Bildpfade):

```bash
python3 ../scripts/figma_plan.py skillmatrix.json /tmp/plan/ \
        --pdf "/tmp/New-Monday - Wissem Kordi - Senior UX-UI Designer - Skillmatrix.pdf"
```

Soll: `figma_bibliothek.json` für den Bibliotheksweg – „lang und A4 (3
Seiten), 8 Bilder zum Hochladen“ –, daneben die rohen Pläne für den Rückfall:
`figma_plan.json` mit 9 Bauschritten und 7 Bildern, `figma_plan_a4.json` mit 3
Seiten, 14 Bauschritten und 7 Bildern; in beiden tragen die 9 leeren Punkte
eine `kontur` (1,5, `#6b7b7e`). Unter „Pruefen:“ stehen genau zwei Hinweise
„lang: Kachel … ohne Bild“ (Google, Microsoft – die lange Kachel hat im Master
keine Platzhalter-Variante). Danach erzeugt

```bash
python3 ../scripts/figma_plan.py --skript lang /tmp/plan/ --seite 1:2
python3 ../scripts/figma_plan.py --skript a4 /tmp/plan/ --seite 1:2
```

je ein `use_figma`-Skript (ohne `--bilder` mit dem Hinweis „7 Bild(er) ohne
Upload“) – damit sind Katalog, Property-Namen und Mengen geprüft, ohne Figma
anzufassen.

Mit einem Feld `"anfrage"` in der JSON bleibt die Reihenfolge der Kategorien,
wie sie dasteht, und beide Skripte melden sie mit einem Hinweis mehr
(„Anfrage …: Kategorien in der Reihenfolge der JSON — 1. …“).

Die Schriften (Inter und Rethink Sans, Google Fonts, OFL) liegen in
`assets/fonts/`. Fehlt dort eine Datei, die `assets/tokens.json` nennt, bricht
das Rendern mit einem Hinweis ab — ohne sie entstünde das PDF in einer
Ersatzschrift.

## Erster Lauf

Lebenslauf, LinkedIn-Export und Portfolio in einen Ordner legen, Claude Code
dort starten:

> Mach mir daraus eine Skill Matrix im New Monday Layout

Der Skill fragt zuerst nach Sprache und Verfügbarkeit, liest dann die
Quellen und legt Auswahl und Bewertung der Attribute zur Freigabe vor,
bevor gerendert wird.
