# newmonday-portfolio einrichten

> **Im Team: als Plugin installieren**, nicht von Hand. In Claude Code
> `/plugin marketplace add New-Monday-GmbH/NW-Claude-Skills` und
> `/plugin install newmonday-bewerber@nw-claude-skills`, dann Auto-Update
> einschalten – siehe [README](../../README.md). Die Wege unten sind für
> Einzelinstallationen ohne Marketplace.

Dieser Skill baut aus den Unterlagen eines Kandidaten ein Portfolio im
New-Monday-Layout als PDF – 16:9-Folien, dieselbe Struktur wie die bestehenden
Portfolios.

## Wo der Ordner hingehört

```
~/.claude/skills/newmonday-portfolio/
```

Liegt daneben der Skill `newmonday-cv`, nutzen beide **dieselbe
Logobibliothek**. Ein Logo, das für einen Lebenslauf gesucht wurde, steht dann
beim nächsten Portfolio schon bereit – und umgekehrt. Neue Logos landen dabei
nie im Skill-Ordner, sondern in `~/.newmonday/logos/`, Fotos der
Firmenzentralen in `~/.newmonday/hq/` – dort überleben sie Plugin-Updates.

## Was auf dem Rechner gebraucht wird

```bash
python3 ~/.claude/skills/newmonday-portfolio/scripts/pruefe_umgebung.py
```

Der Befehl sagt, was fehlt, und nennt den passenden Installationsbefehl für dein
System. Kurzfassung für macOS:

```bash
brew install python-pango pango libffi gdk-pixbuf poppler potrace
pip3 install weasyprint pymupdf pillow pypdf
```

`weasyprint` rendert das PDF – barrierefrei als PDF/UA-1. Fehlt sie, weicht der
Skill auf Chrome aus; dieses PDF ist **nicht barrierefrei** und geht so nicht an
Kunden. `pypdf` prüft das fertige PDF auf PDF/UA und Größe. `pymupdf` und `pillow` sind zwingend: damit werden Eingangs-PDFs
ausgelesen, Fotos zugeschnitten und das fertige PDF auf Überlauf geprüft.

**Empfohlen: veraPDF** (`brew install verapdf`, bringt Java mit). Damit prüft
jedes Renderskript das fertige PDF lokal auf PDF/UA-1 – dieselben maschinell
prüfbaren Regeln wie PAC 2026 und axesCheck, ohne Upload. Ohne veraPDF bleibt
es bei der Eigenprüfung des Skills und einem Hinweis.
`potrace` ist optional und wird nur gebraucht, um zu kleine Logos zu
vektorisieren.

## Ausprobieren

Im Skill liegt ein Beispiel mit echten Inhalten:

```bash
cd ~/Desktop
python3 ~/.claude/skills/newmonday-portfolio/scripts/render_portfolio.py \
  ~/.claude/skills/newmonday-portfolio/beispiel/portfolio.json \
  portfolio-test.pdf
```

Ergebnis sind 24 Seiten: 14 feste und zwei Projektblöcke zu je fünf. Das PDF
wiegt rund 6 MB – es besteht großenteils aus den vorgerenderten Screenflächen.
Die legt der Lauf neben die verwendete `portfolio.json`, zusammen mit den
Graustufen-Fassungen der Kundenlogos, beim Beispiel also nach
`beispiel/arbeit/screens/` in den Skillordner. Rund 3 MB, reine Zwischenlage:
Der Ordner spart nur die Rechenzeit des nächsten Laufs und kann gelöscht werden.

Die Meldungen auf der Konsole gehören dazu: Sie nennen zu kleine Bilder,
gesetzte Platzhalter und Text, der aus seiner Fläche läuft. Beim Beispiel kommen
mehrere, und alle stimmen: Es führt zwei Projekte statt der üblichen drei bis
fünf, die beiden Fotos der Firmenzentralen sind für ihre Fläche zu klein, und
mehrere Screens sind schmaler, als sie auf den Flächen liegen („… ist X px
breit, liegt aber Y px breit auf der Fläche“) – gemessen wird je Screen gegen
seine tatsächlich platzierte Größe. Mehr Material liegt dem Skill nicht bei.
So sieht der Bericht aus, wenn etwas fehlt.

## Benutzen

Schick Claude die Unterlagen – Portfolio als PDF oder Link, Lebenslauf und
LinkedIn-PDF-Export – und sag, dass ein Portfolio daraus werden soll. Der Skill
fragt zuerst nach der Sprache und dem Material, dazu nach den Kundenlogos, den
Screenshots und ein paar Sätzen über jeden Kunden. Dann liest er alles aus und
fragt vor dem Bauen ein zweites Mal: welche Projekte in welcher Reihenfolge,
welche davon vertraulich sind, wie das Statement lautet und mit welchen
KI-Werkzeugen der Kandidat arbeitet.

Fehlen Bilder, baut er das PDF trotzdem und setzt beschriftete Platzhalter.
Schick die fehlenden Bilder einfach in den Chat nach – er rendert dann neu.

## Was du selbst pflegen musst

- **Die Agenturzahlen** (26 Teammitglieder, gegründet 2018, 100 %
  Kundenzufriedenheit) und den **Ansprechpartner** stehen als Konstanten oben in
  `scripts/render_portfolio.py`.
- **Das UX-Design-Awards-Badge** (`assets/marke/ux-awards-badge.png`) trägt die
  Jahreszahl im Bild. Zum Jahreswechsel gehören Badge und die drei Textzeilen
  darunter (`AGENTUR["badge"]`) zusammen aktualisiert.
- **Die vier Arbeitsweise-Bilder** in `assets/bilder/` sind in jedem Portfolio
  gleich – drei für die Prozessschritte, das vierte für die KI-Folie. Wer sie
  tauscht, tauscht sie für alle.
