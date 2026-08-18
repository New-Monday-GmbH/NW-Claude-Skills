# NW Claude Skills

Claude-Code-Skills der New Monday GmbH. Jeder Skill liegt in einem eigenen
Ordner und ist für sich installierbar.

| Skill | Was er macht |
|-------|--------------|
| [`rapid-redesign`](rapid-redesign/) | Erzeugt ein komplettes New-Monday-Rapid-Redesign: UX/UI- und Usability-Audit einer ganzen Website (echter Browser via Playwright) und daraus ein fertiges Folien-Deck im RR-Stil. |
| [`newmonday-cv`](newmonday-cv/) | Macht aus einem fremden Lebenslauf einen im New-Monday-Layout, als fertiges PDF. Eingang: CV als PDF, LinkedIn-Export, LinkedIn-Profil-Link oder eingefügter Profiltext. |
| [`newmonday-skillmatrix`](newmonday-skillmatrix/) | Baut aus Lebenslauf, Portfolio und LinkedIn-Export eine Skill Matrix im New-Monday-Layout: eine lange Seite mit Hero, Zertifikaten und nach Kategorien gruppierten Kompetenzen mit 1–5-Punkte-Bewertung. |

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

`newmonday-cv` braucht WeasyPrint und die passenden Systembibliotheken. Was auf
deinem Rechner fehlt, sagt dir:

```bash
python3 ~/.claude/skills/newmonday-cv/scripts/pruefe_umgebung.py
```

Auf macOS meist `brew install python-pango pango libffi gdk-pixbuf poppler potrace`
und `pip3 install weasyprint jinja2 pypdf pillow`. Ob die ganze Kette läuft,
prüft `scripts/selbsttest.py` an einem mitgelieferten Beispiel.

## Die Logobibliothek gehört allen

`newmonday-cv` legt jedes neu gefundene Firmenlogo in seinem eigenen Ordner
`newmonday-cv/assets/logos/` ab. Über den Symlink oben landet es damit direkt im
Arbeitsverzeichnis dieses Repos — also bitte committen und pushen:

```bash
cd ~/NW-Claude-Skills && git add newmonday-cv/assets/logos && git commit -m "Logos ergaenzt" && git push
```

Dann muss der nächste Kollege dasselbe Logo nicht noch einmal heraussuchen. Die
Sammlung wird mit jedem Kandidaten besser — das funktioniert aber nur, wenn sie
zurückfließt.

## Was hier NICHT hineingehört

Ergebnisse von Skill-Läufen (bei `rapid-redesign` die `audits/`-Ordner mit
Kundendaten) bleiben im jeweiligen Projekt und sind per `.gitignore`
ausgeschlossen. Dieses Repository enthält ausschließlich die Werkzeuge.
