# NW Claude Skills

Claude-Code-Skills der New Monday GmbH. Jeder Skill liegt in einem eigenen
Ordner und ist für sich installierbar.

| Skill | Was er macht |
|-------|--------------|
| [`rapid-redesign`](rapid-redesign/) | Erzeugt ein komplettes New-Monday-Rapid-Redesign: UX/UI- und Usability-Audit einer ganzen Website (echter Browser via Playwright) und daraus ein fertiges Folien-Deck im RR-Stil. |
| [`newmonday-cv`](newmonday-bewerber/skills/newmonday-cv/) | Macht aus einem fremden Lebenslauf einen im New-Monday-Layout – als PDF und als bearbeitbare Frames in Figma, jeweils vollständig und anonymisiert. Eingang: CV als PDF, LinkedIn-Export, LinkedIn-Profil-Link oder eingefügter Profiltext. |
| [`newmonday-skillmatrix`](newmonday-bewerber/skills/newmonday-skillmatrix/) | Baut aus Lebenslauf, Portfolio und LinkedIn-Export eine Skill Matrix im New-Monday-Layout: eine lange Seite mit Hero, Zertifikaten und nach Kategorien gruppierten Kompetenzen mit 1–5-Punkte-Bewertung. |
| [`newmonday-portfolio`](newmonday-bewerber/skills/newmonday-portfolio/) | Baut aus Portfolio, Lebenslauf und LinkedIn-Export ein fertiges Portfolio im New-Monday-Layout als PDF: 16:9-Folien mit Profilseite, Kundenwand, Design-Prozess, Projektstrecken und Kontaktseite. |
| [`newmonday-bewerbermappe`](newmonday-bewerber/skills/newmonday-bewerbermappe/) | Baut alle drei Dokumente eines Kandidaten in einem Lauf: fragt Sprache, Figma, Material und Anfrage einmal, prüft vorab, was fehlt und ob ein bestandenes Profilmatching vorliegt, richtet alle drei Dokumente auf die Anforderungstabelle aus `newmonday-matching` aus (Gewichtung, nie Beleg), bündelt alle Entscheidungen und lässt dann `newmonday-cv`, `newmonday-skillmatrix` und `newmonday-portfolio` nacheinander bauen – PDFs plus Frames auf einer Figma-Seite je Kandidat. |
| [`newmonday-anfrage`](newmonday-bewerber/skills/newmonday-anfrage/) | Passt die bestehenden Unterlagen der passendsten Kandidaten auf eine Ausschreibung an: holt das Matching-Artifact aus Claude Chat, liest den Bestand aus dem Original-Figma, schmückt Bestehendes aus, ergänzt erwartbare Methoden, fragt Technik nach, entfernt nichts und erfindet keine Projekte – PDFs unter `Bewerberunterlagen/`, ein neues Figma-File je Anfrage. |
| [`newmonday-matching`](newmonday-matching/) | Profilmatching nach einem festen Verfahren: zerlegt eine Projektanfrage, gleicht sie gegen den Pool im EspoCRM (Quote, Schwelle 70 %) und den JOIN-Bestand (Trichter über K.-o.- und Muss-Kriterien) ab, prüft Domäne und Vita und schreibt eine einheitliche Auswertung mit Empfehlung. Schreibt nichts ins CRM oder nach JOIN. |

Die drei Dokument-Skills und der Gesamtlauf liegen zusammen im Plugin
[`newmonday-bewerber`](newmonday-bewerber/). Es wird über den Plugin-Marketplace
dieses Repos installiert und aktualisiert sich selbst – für alle, auch mit
privatem Claude-Account. `rapid-redesign` und `newmonday-matching` werden
(noch) per Symlink installiert, siehe unten.

## newmonday-bewerber installieren (alle)

In Claude Code (Terminal, Desktop-App im Code-Tab oder IDE) zwei Befehle:

```
/plugin marketplace add New-Monday-GmbH/NW-Claude-Skills
/plugin install newmonday-bewerber@nw-claude-skills
```

Danach Claude Code neu starten. Die Skills heißen dann
`newmonday-bewerber:newmonday-cv`, `…:newmonday-skillmatrix`,
`…:newmonday-portfolio` und `…:newmonday-bewerbermappe`; ausgelöst werden sie
wie bisher einfach durch die Bitte („Mach aus diesem Lebenslauf …“). Ein
Claude-Account in der Organisation ist nicht nötig, und das Repo ist öffentlich –
es braucht keinen GitHub-Zugang. Im claude.ai-Chat (Browser) stehen
Plugins nicht zur Verfügung, nur in Claude Code.

### Auto-Update einschalten (einmal pro Person)

Für Marketplaces von GitHub ist Auto-Update ab Werk aus. Einschalten:
`/plugin` → **Marketplaces** → `nw-claude-skills` → **Enable auto-update**.

Oder in `~/.claude/settings.json` eintragen (macht beides – Marketplace und
Auto-Update – in einem Schritt):

```json
{
  "extraKnownMarketplaces": {
    "nw-claude-skills": {
      "source": { "source": "github", "repo": "New-Monday-GmbH/NW-Claude-Skills" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "newmonday-bewerber@nw-claude-skills": true }
}
```

Claude Code holt Updates beim Start. Das Plugin hat bewusst **keine
Versionsnummer**: jeder Commit auf `main` ist ein Update, niemand muss etwas
hochzählen. Von Hand aktualisieren: `/plugin marketplace update nw-claude-skills`.

Für Mitglieder der claude.ai-Organisation kann der Owner denselben
`extraKnownMarketplaces`-Block (mit `"autoUpdate": true`) und `enabledPlugins` in
die Managed Settings legen – dann ist das Plugin samt Auto-Update für alle
gesetzt. Wer mit privatem Account arbeitet, macht den Schritt oben einmal selbst.

### Was der Rechner braucht

`newmonday-cv` braucht WeasyPrint und die passenden Systembibliotheken. Was
fehlt, sagt der Skill beim ersten Lauf selbst (`scripts/pruefe_umgebung.py`).
Auf macOS meist `brew install python-pango pango libffi gdk-pixbuf poppler potrace`
und `pip3 install weasyprint jinja2 pypdf pillow`. Ob die ganze Kette läuft,
prüft `scripts/selbsttest.py` je Skill an einem mitgelieferten Beispiel.

## Für die Pfleger: Symlink oder Plugin, nie beides

Wer am Repo arbeitet, kann die Skills weiter per Symlink aus dem Checkout
nutzen – Änderungen wirken dann sofort, ohne Commit. **Symlinks und Plugin
dürfen nicht gleichzeitig aktiv sein**, sonst stehen alle Skills doppelt da
(`newmonday-cv` und `newmonday-bewerber:newmonday-cv`) und Claude greift mal zum
einen, mal zum anderen. Also entweder

```bash
# Plugin nutzen: Symlinks entfernen
rm ~/.claude/skills/newmonday-cv ~/.claude/skills/newmonday-skillmatrix \
   ~/.claude/skills/newmonday-portfolio ~/.claude/skills/newmonday-bewerbermappe
```

oder das Plugin nicht installieren (bzw. mit `/plugin uninstall
newmonday-bewerber@nw-claude-skills` wieder entfernen) und bei den Symlinks
bleiben:

```bash
git clone https://github.com/New-Monday-GmbH/NW-Claude-Skills.git ~/NW-Claude-Skills
ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-cv ~/.claude/skills/newmonday-cv
ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-skillmatrix ~/.claude/skills/newmonday-skillmatrix
ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-portfolio ~/.claude/skills/newmonday-portfolio
ln -s ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-bewerbermappe ~/.claude/skills/newmonday-bewerbermappe
```

## rapid-redesign und newmonday-matching (Symlink)

```bash
ln -s ~/NW-Claude-Skills/rapid-redesign ~/.claude/skills/rapid-redesign
ln -s ~/NW-Claude-Skills/newmonday-matching ~/.claude/skills/newmonday-matching
```

Ein Symlink statt einer Kopie sorgt dafür, dass ein `git pull` im Repo den
Skill direkt aktualisiert. `rapid-redesign` braucht Playwright samt Chromium:

```bash
bash ~/.claude/skills/rapid-redesign/scripts/setup.sh
```

## Die Logobibliothek gehört allen

Der Grundstock liegt im Repo unter
`newmonday-bewerber/skills/newmonday-cv/assets/logos/` und kommt mit jedem
Update zu allen. Neu gefundene Logos legen `newmonday-cv` und
`newmonday-portfolio` dagegen in **`~/.newmonday/logos/`** ab (Fotos der
Firmenzentralen in `~/.newmonday/hq/`): Den Plugin-Ordner ersetzt jedes Update,
dieser Ordner bleibt. Gesucht wird zuerst dort, dann im Grundstock.

Damit ein neues Logo bei allen ankommt, nennt die Übergabe jedes Laufs die
neuen Logos. Ein Pfleger holt sie in den Grundstock – von seinem eigenen Rechner
oder nachdem ihm jemand den Inhalt von `~/.newmonday/logos/` geschickt hat:

```bash
python3 ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-cv/scripts/logos_uebernehmen.py ~/NW-Claude-Skills --uebernehmen
```

Das Skript verschiebt die Dateien in den Checkout, führt `aliase.json`
zusammen und nennt den Commit-Befehl. Die Fotos der Firmenzentralen bleiben
lokal (Bildrechte, Quellen in `~/.newmonday/hq/quellen.json`).

Umzug für alle, die bisher per Symlink gearbeitet haben: Fotos der
Firmenzentralen lagen in `newmonday-cv/assets/hq/` (nie im Repo). Einmal
mitnehmen:

```bash
mkdir -p ~/.newmonday && cp -Rn ~/NW-Claude-Skills/newmonday-bewerber/skills/newmonday-cv/assets/hq ~/.newmonday/
```

## Was hier NICHT hineingehört

Ergebnisse von Skill-Läufen (bei `rapid-redesign` die `audits/`-Ordner mit
Kundendaten, bei `newmonday-matching` die Auswertungen, CSVs und die
`matching.config.json` mit dem CRM-Schlüssel) bleiben im jeweiligen Projekt und sind per `.gitignore`
ausgeschlossen. Dieses Repository enthält ausschließlich die Werkzeuge.
