---
name: newmonday-marktbild
description: Lernt aus den zugeschnittenen Anfrage-Läufen, was der Markt gerade sucht (Marktbild je Rollenfamilie als Excel und Bericht in SharePoint), zeigt je Kandidat die Lücken in seinen Original-Unterlagen, speist das Gefragte in eine Kopie der Original-Frames im Figma-File des Kandidaten ein und macht die Kopie nach Freigabe des Nutzers zum neuen Original – mit neuen PDFs auf allen Plattformen. Nutze diesen Skill immer, wenn das Marktbild aktualisiert, ausgewertet oder gezeigt werden soll („was sucht der Markt“, „Marktbild“, „Freitagslauf“), wenn Original-Unterlagen um Marktwissen ergänzt werden sollen („Markt einspeisen“, „Originale auf den Markt bringen“, „Lücken von <Name>“) und wenn eine Markt-Kopie freigegeben werden soll („freigeben“, „mach die Kopie zum Original“). Für eine konkrete Ausschreibung ist newmonday-anfrage zuständig; neue Kolleg:innen baut newmonday-bewerbermappe gleich mit dem Marktbild.
---

# New Monday Marktbild

Jede zugeschnittene Mappe zeigt, was ein Kunde wollte und was in unseren
Unterlagen fehlte. Dieser Skill sammelt das, damit die **Original-Unterlagen**
das Gefragte schon enthalten und nicht jedes Mal neu zugeschnitten werden
müssen. Drei Abläufe:

1. **Freitagslauf** – Marktbild und Lücken je Kandidat, ohne Rückfrage
   (geplante Aufgabe, freitags 14 Uhr). Ändert nichts in Figma.
2. **Einspeisen** – auf Zuruf: Lücken eines Kandidaten in eine Kopie seiner
   Original-Frames einarbeiten. Der Nutzer prüft die Kopie.
3. **Freigeben** – auf Zuruf: Kopie wird Original, alte Frames ins Archiv,
   PDFs neu, auf allen Plattformen getauscht.

Neue Kolleg:innen: newmonday-bewerbermappe nutzt das Marktbild schon beim
ersten Bau (dort Phase 1, „allgemeine Mappe mit Marktbild“).

## Regeln

Es gelten die Regeln von newmonday-anfrage („Die Regeln, die über allem
stehen“) – Einspeisen ist eine Anfrage mit dem Marktbild als Ausschreibung:

1. **Nichts erfinden** – keine Projekte, Kunden, Zahlen, Zertifikate.
2. **Nichts entfernen** – ergänzen und umsortieren; `vergleich.py` prüft.
3. **Methoden selbst, Technik fragen.** Methoden und Arbeitsweisen (`art:
   methode`) ergänzt der Skill selbst – aber nur, wenn sie bei Rolle,
   Seniorität und Stationen des Kandidaten sehr wahrscheinlich sind; sonst
   wird gefragt wie bei Technik. Tools, Technik, Normen und Domänen kommen nur
   mit Ja des Nutzers hinein. Jede abgeleitete Stelle steht unter „Zur
   Freigabe“.
4. **Anpassen statt neu bauen**, mit den Komponenten der Master-Bibliothek.
5. Aus dem Feedback vom 15.11.2026: Skill Matrix nur **drei** Top-Fähigkeiten,
   **nur Attribute aus dem Figma-Pool** (der Pool darf um Gefragtes erweitert
   werden, keine erfundenen Kategorien), **keine Projekt- oder Kundennamen in
   Klammern**, keine großen Lücken; Portfolio: Ergänzungen in die
   Arbeitsweise-Folien (meist 6–10) statt Zusatzfolien, wohldosiert fett;
   CV-Skillset als Themenzeilen, Sprachen „Sprache (Niveau)“.
6. **Kein Kundenwissen ins Repo.** Ausschreibungen, Job IDs, Kunden- und
   Kandidatennamen liegen nur in der Ablage und in SharePoint – das Skill-Repo
   ist öffentlich.

## Ablage und Konfiguration

`~/.newmonday/marktbild.json` (Vorlage `scripts/marktbild.config.beispiel.json`):
`ausschreibungen` (Anfrage-Läufe von newmonday-anfrage), `originale`
(Original-PDFs je Kandidat), `markt` (Arbeitsordner dieses Skills),
`sharepoint` (`drive_id`, `ordner_id`, `daten_id`), `plattformen` (Adressen,
siehe `references/plattformen.md`).

```
<markt>/
  begriffe.json          Begriff → art, synonyme (ein Vokabular für alles)
  kandidaten.json        Name → ordner (unter originale/), rollenfamilien, figma_file
  anforderungen/<Anfrage-Ordner>.json   je Ausschreibung einmal zerlegt
  antworten/<Name>.json  Technik-Antworten des Nutzers – nie doppelt fragen
  vorgaben.json          vom Nutzer gesetzte Anforderungen: [{"begriff", "rollenfamilien"?}] –
                         gelten immer als gefragt (ohne rollenfamilien in jeder Familie)
  stand-<datum>/         marktbild.xlsx, bericht.md, marktbild.json, luecken.json
```

Die lokale Ablage ist die Arbeitskopie, SharePoint der Lesestand fürs Team.
Nach jedem Lauf spiegeln (SharePoint-Connector, `conflictBehavior: "replace"`):
`marktbild.xlsx` als **„Marktbild.xlsx“** und `bericht.md` als
**„Bericht <JJJJ-MM-TT>.md“** in `ordner_id`; `begriffe.json`,
`kandidaten.json` und jede geänderte `antworten/<Name>.json` (als
„antworten-<Name>.json“) in `daten_id`. Excel als `contentBase64`, Text als
`content`. Änderungen im Team laufen über diesen Skill, nicht über die Excel.

Skripte: `scripts/marktbild.py` (Auswertung, Lücken, Antworten),
`scripts/verkleinern.py` (PDF unter Plattform-Grenze, braucht
`~/.newmonday/venv` mit pikepdf und Pillow), `scripts/selbsttest.py`.

## Freitagslauf

Läuft unbeaufsichtigt: **keine Klickboxen, nichts in Figma, keine Plattform.**

1. `python3 ${CLAUDE_SKILL_DIR}/scripts/marktbild.py offen`
2. Für jede Zeile `OFFEN` die Ausschreibung zerlegen nach
   `references/anforderungen.md` → `<markt>/anforderungen/<Ordnername>.json`;
   neue Begriffe in `begriffe.json`. Für jede Zeile `FEHLER` die Daten
   korrigieren. Wieder `offen`, bis nichts mehr gemeldet wird.
3. `python3 ${CLAUDE_SKILL_DIR}/scripts/marktbild.py auswerten` – gibt den
   Stand-Ordner und drei Zeilen für die Mitteilung aus.
4. Nach SharePoint spiegeln (siehe oben).
5. Mitteilung auf dem Mac mit Ton, die drei Zeilen als Text:
   `osascript -e 'display notification "<Zeile 1> · <Zeile 2> · <Zeile 3>" with title "Marktbild <TT.MM.>" sound name "Glass"'`
   Anführungszeichen in den Zeilen vorher entfernen.
6. Ergebnis in einer kurzen Nachricht: Stand, neue Ausschreibungen, die
   Veränderungen, je Kandidat die Zahl der Lücken („2 selbst ergänzbar,
   3 zu fragen“), Hinweise aus dem Bericht.

## Einspeisen

1. **Wer.** Genannte Kandidaten; sonst eine Klickbox (`multiSelect`) mit allen
   aus `kandidaten.json`, die im neuesten Stand Lücken haben, je Option die
   Zahl der Lücken. Ist der neueste Stand älter als 7 Tage, erst
   Freitagslauf-Schritte 1–4.
2. **Lücken lesen:** `marktbild.py luecken --kandidat "<Name>"`.
3. **Fragen – eine Sitzung für alle gewählten Kandidaten.** Je Lücke mit
   `tun` = „Nutzer fragen“ und je Methode, die für diesen Kandidaten nicht
   sehr wahrscheinlich ist, eine Frage (bis zu vier je `AskUserQuestion`):

   ```
   Frage:    Hat <Vorname> <was die Ausschreibungen damit meinen, in Worten>? So fordern es <n> Ausschreibungen (<Rollenfamilie>): „<kurzer Wortlaut aus ausschreibung.md>“.
   Header:   <Begriff, max. 12 Zeichen>
   Optionen: Ja – mit Projekt (Projekt über „Other“) | Ja – ohne Projekt | Nein | Weiß ich nicht
   ```

   **Nie den nackten Begriff fragen**, vor allem keine Domänen und
   Sammelbegriffe: „Erfahrung mit Webanwendungen?“ ist zu ungenau – gemeint
   war „Oberflächen für webbasierte Fachanwendungen (Software im Browser,
   Portale, Admin-Oberflächen), nicht reine Websites“. Den Sinn aus dem
   Wortlaut der Ausschreibungen nehmen (`anforderungen/` → Anfrage-Ordner →
   `ausschreibung.md`).

   Jede Antwort sofort ablegen: `marktbild.py antwort --kandidat … --begriff …
   --antwort ja_projekt|ja|nein|weiss_nicht [--projekt …]`. Nennt der Nutzer
   über „Other“ Projekte, ist das `ja_projekt` mit diesen Projekten; wählt er
   „Ja – mit Projekt“, ohne eins zu nennen, `ja_projekt` mit `--projekt
   "(nicht genannt – realistisch platzieren)"`. „Weiß ich nicht“ bleibt
   draußen und steht in der Übergabe als „beim Kandidaten erfragen“. Bleibt
   danach für einen Kandidaten nichts einzuspeisen, endet sein Lauf hier.
4. **Original-File** aus `kandidaten.json` → `figma_file`; fehlt es, finden
   wie newmonday-anfrage Phase 2, Punkt 2, und eintragen.
5. **Kopie** (Figma, `figma:figma-use` laden). Oft hat der Nutzer sie schon
   angelegt – je Dokument eine zweite Reihe unter den Original-Frames mit
   fortlaufenden Seitennummern (CV „Seite 5–8“ unter „Seite 1–4“), beim
   Portfolio eine zweite Section gleichen Namens daneben. Dann diese nehmen
   und nicht umbenennen. Sonst: Auf der Seite mit den aktuellen
   Original-Frames (nicht Archiv, keine früheren Kopien) jeden Frame
   duplizieren, die Kopie mit Abstand rechts daneben legen und
   „<Frame-Name> – Markt <TT.MM.JJJJ>“ nennen. Gibt es schon eine Kopie ohne
   Freigabe, fragen: *Auf der vorhandenen Kopie weiter (Empfohlen)* |
   *Neue Kopie*. Die Original-Frames bleiben unberührt.
6. **Einarbeiten – direkt in den Kopien**, mit den vorhandenen Komponenten,
   ohne JSON-Umweg (die PDFs entstehen erst beim Freigeben aus dem geprüften
   Figma-Stand). Erst alle Texte der Kopien lesen (Antwort < 20 KB,
   Nicht-ASCII maskieren), dann je Dokument in einem Aufruf ändern.
   Bei jedem ergänzten Fließtext prüfen, ob die letzte Zeile nur ein Wort
   hat – dann die letzten zwei Wörter mit U+00A0 verbinden, wenn dadurch
   keine Zeile oder Seite überläuft (wie `kein_einzelwort()` in den Skripten):
   - **Lebenslauf:** Ergänzungen in einen **passenden Stichpunkt** der
     Station, im Format „Schlagwort: Erklärung“ (newmonday-cv, „Stationen und
     Stichpunkte im UX-Layout“). Ein neuer Stichpunkt ist erlaubt, wenn die
     Seite ihn trägt. Bejaht mit Projekt: an diesem Projekt. Ohne Projekt und
     abgeleitet: an dem Projekt, dessen belegte Tätigkeit es am ehesten
     einschließt.
     **Kopien im alten Format zuerst umstellen** (seit 20.11.2026): Die
     Firma-Zeile wird zu „Zeitraum  |  Firma“ (Ebene „Zeitraum“ ausblenden),
     das Projektdatum zu 8 pt / 10 px, jeder Stichpunkt zu „Schlagwort:
     Erklärung“ mit dem Schlagwort in Inter Semi Bold, jede Einleitung zu
     einem Satz. Läuft eine Seite über, werden die Stichpunkte gekürzt, nicht
     Seiten angehängt.
     **Erst den Stand der Kopie auf den aktuellen Standard bringen**, wenn sie
     älter ist: Steht auf Seite 1 noch das alte Skillset (Listen Fähigkeiten /
     Branchen / Tools / Sprachen), es durch die Komponente „CV/Skillset
     Themen“ (B2, Key in `<skills>/newmonday-cv/assets/master-bibliothek.json`) ersetzen – im Seiten-Slot
     direkt an seiner Stelle einfügen (`findIndex` nach ID, `insertChild`),
     Einträge wörtlich übernehmen und auf die Themen verteilen, geschützte
     Leerzeichen und Trenner wie in den anderen CVs, Sprachen als
     „Sprache (Niveau)“; das alte Skillset löschen. Unter **Tools** nur
     Software – Technik wie HTML/CSS gehört zu den Fähigkeiten (Thema „KI &
     Technologie“). Jede Station (Arbeitgeber wie Projekt) trägt eine
     **Einleitung** wie die anderen (Eigenschaft „Beschreibung anzeigen“,
     ein bis zwei Sätze in der Ich-Form, nur aus Belegtem der Station).
   - **Skill Matrix:** nur Attribute aus dem Pool
     (`<skills>/newmonday-skillmatrix/references/attribute-katalog.md`, Name,
     Beschreibung und Kategorie wörtlich) und nur in Kategorien, die die
     Matrix schon hat (höchstens 5 Kategorien, 24 Kompetenzen). Passt ein
     Attribut in keine vorhandene Kategorie, bleibt es draußen und steht in
     der Übergabe. Die Sektion **Tools** ist nur für Software (Figma, Jira,
     Claude …) – Technik wie HTML/CSS oder JavaScript gehört in ihre
     Pool-Kategorie (Coding Skills); fehlt die und sind die Kategorien voll,
     das passende Attribut einer vorhandenen Kategorie nehmen (HTML/CSS →
     „Frontend-Verständnis“ unter Development Collaboration), nie eine
     Tool-Karte. Bewertung nach Beleg: bejaht ohne Projekt 3, mit Projekt 3–4.
   - **Portfolio:** in die Arbeitsweise-Folien (meist 6–10) als angehängter
     Satz; das Schlüsselwort in Semi Bold derselben Schrift. Stehen hinter den
     Arbeitsweisen noch **Zusatz-Schwerpunktfolien** (Komponente „Schwerpunkt“,
     etwa Barrierefreiheit, Handover & QA, Edge Cases), ihren Inhalt vollständig
     in die Prozess-Folien einarbeiten (Verstehen / Kreieren / Validieren, als
     eigener Absatz), sie aus der Kopie nehmen und Seitenzahlen und
     Folien-Namen neu zählen. Was beim Kürzen herausfällt, muss in CV oder
     Matrix stehen.
   - **Logos:** Jede Station im Lebenslauf trägt das Kundenlogo **mit
     Schriftzug** (nicht nur die Bildmarke), und jeder Kunde aus dem
     Lebenslauf steht auf der **Kundenwand** (Portfolio Folie 3) – einfarbig
     wie die anderen dort (meist dunkel, aus dem Farblogo als Silhouette
     erzeugen), gleich groß wirkend (ähnliche Fläche), angeordnet nach der Hausregel des Renderers (`logoraster` in render_portfolio.py): bis 5 Logos eine lockere Reihe, ab 6 bis zu 7 je Zeile von Kante zu Kante, Fläche je Logo 100² pt, Höhe ≤ 80, Breite ≤ 350 – so stimmen Figma und PDF überein. Logos aus
     `~/.newmonday/logos/`, hochladen mit `upload_assets` und den imageHash
     setzen. Größe in diesen Komponenten über Innenabstände: CV-Logo-Rahmen
     „Logo n“ = paddingLeft × paddingTop; Kundenwand-Platz „Logo n“ =
     Innenabstände um die Fläche (FILL) im 1607 × 640 großen Platz.
   - Danach jede geänderte Seite ansehen (Screenshot): nichts abgeschnitten,
     keine Seite länger als vorher.
   - Steht ein Begriff schon da und die Lückenprüfung hat ihn nicht erkannt
     (anderes Wort, etwa „Browser-Anwendungen“), das Wort als Synonym in
     `begriffe.json` ergänzen.
7. **Übergabe** – ganz oben: „Bitte die Kopie prüfen – wenn sie passt, sag
   ‚freigeben <Name>‘.“ Darunter je Dokument jede Stelle mit altem und neuem
   Wortlaut und Grund (bejaht / bejaht mit Projekt / abgeleitet: <Beleg>),
   dann was draußen blieb und warum. Spiegeln (antworten, begriffe).

## Freigeben

Nur auf ausdrückliches „freigeben“ des Nutzers für genannte Kandidaten. Der
Figma-Stand der Kopie ist dann die Wahrheit – einschließlich allem, was der
Nutzer von Hand nachgepflegt hat.

1. **Figma:** Seite „Archiv“ (eine vorhandene Seite, deren Name mit „Archiv“
   oder „Archive“ beginnt; sonst anlegen). Die bisherigen Original-Frames
   dorthin verschieben und „<TT.MM.JJJJ> alt – <Name>“ nennen. Die Kopien an
   deren Stelle rücken (gleiche x/y); ein Zusatz „ – Markt <datum>“ fällt
   weg, fortlaufende Seitennummern der Kopie (Seite 5–8) werden wieder
   Seite 1–4. Nichts löschen.
2. **PDFs aus dem Figma-Stand** – ein Subagent, nie aus Figma exportieren:
   alle freigegebenen Frames lesen (Texte, Sichtbarkeiten, Bewertungen,
   Reihenfolge, Bild-Hashes, Fettdruck-Bereiche), die JSONs für
   `newmonday-cv` (`render_cv.py`), `newmonday-skillmatrix`
   (`render_skillmatrix.py`, nur A4) und `newmonday-portfolio` genau darauf
   angleichen und rendern. Prüfen: `verapdf --flavour ua1` PASS, `pdffonts`
   alle eingebettet mit Unicode, `pdftotext` in Lesereihenfolge, gleiche
   Seitenzahl wie Figma, jede Seite als PNG gegen den Figma-Screenshot,
   Größe möglichst klein. Dann die bisherigen PDFs in `<originale>/<ordner>/`
   nach `~/.Trash/Originale-alt-<JJJJ-MM-TT>/<ordner>/` verschieben und die
   neuen dorthin legen („New Monday - <Name> - CV.pdf“, „… - Skillmatrix
   A4.pdf“, „… - Portfolio.pdf“).
3. **Plattformen:** nach `references/plattformen.md` – CRM, freelancermap,
   Hays, GULP: neue hoch, alte dieses Kandidaten löschen. Nur über
   Claude in Chrome; ist der Nutzer nicht angemeldet, darum bitten.
4. **Marktbild:** `marktbild.py auswerten` – die Lücken des Kandidaten werden
   kleiner – und spiegeln.
5. **Übergabe:** was im Archiv liegt, welche PDFs wo getauscht wurden, was
   offen blieb („Weiß ich nicht“-Begriffe).

## Neue Kandidaten

Liegen die ersten PDFs eines neuen Kandidaten unter `originale/`, ihn in
`kandidaten.json` eintragen (`ordner`, `rollenfamilien` nach
`references/rollenfamilien.md`, `figma_file`). Der Freitagslauf meldet
Ordner ohne Eintrag als Hinweis.
