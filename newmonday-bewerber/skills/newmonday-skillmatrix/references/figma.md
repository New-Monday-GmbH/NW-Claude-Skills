# Figma-Referenz — aus der Master-Bibliothek

Beide Fassungen entstehen in Figma aus **Instanzen der veröffentlichten
Master-Bibliothek** „Portfolio - CV Master“ (fileKey `oezbaw261xDwxthPuX3ZpS`):
der lange Frame aus Kopfzeile, Hero, Rumpf und Fuß, die A4-Fassung als je eine
Instanz `Skillmatrix A4/Seite` pro PDF-Seite. Befüllt wird nur über
Component-Properties, exponierte verschachtelte Instanzen und Bild-Overrides.
Ändert jemand im Master eine Komponente, kommt die Änderung per
Bibliotheks-Update in jede Kandidatendatei – deshalb wird **nie eine Instanz
gelöst** und kein Wert von Hand gesetzt.

Keys, Property-Namen (samt `#`-Suffix), exponierte Instanzen, Bildebenen und
Mengengrenzen stehen in `assets/master-bibliothek.json`. `figma_plan.py` schlägt
jeden Namen dort nach; fehlt einer, bricht es ab, statt still nichts zu setzen.

Der rohe Weg (`references/figma-roh.md`) ist nur noch Rückfall: wenn der Vorflug
die Bibliothek nicht erreicht oder eine Fassung mehr Einträge hat, als die
Komponenten tragen.

**Vor dem ersten `use_figma`-Aufruf den Skill `figma-use` laden**, und
`skillNames: "figma-use"` an jeden Aufruf.

## Der Link

```
https://www.figma.com/design/<fileKey>/<Name>?node-id=1-32
```

`fileKey` ist der Teil nach `/design/`, `node-id` wird von `1-32` auf `1:32`
gedreht. **Nur `/design/`** — `/board/`, `/slides/`, `/make/` und `/proto/`
können keine Bibliotheks-Instanzen tragen; dann sagen, dass eine Design-Datei
gebraucht wird. Trägt der Link eine `node-id`, kommen die Frames auf deren
Seite; ohne `node-id` eine neue Seite `Skillmatrix — Vorname Nachname`. **Nie
ungefragt in eine bestehende Seite schreiben**, zu der nichts hinführt.

## Der Ablauf — vier Aufrufe und die Screenshots

Figma begrenzt die MCP-Aufrufe je Sitz. Der Weg kommt deshalb mit wenigen aus:
Vorflug, ein Upload, zwei Bauaufrufe, dazu ein Screenshot je Frame. Lesen bündeln,
nicht pro Block nachsehen.

**1. Pläne schreiben** (lokal):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py skillmatrix.json arbeit/ \
        --pdf "ausgabe/New-Monday - … - Skillmatrix.pdf" \
        --pdf-a4 "ausgabe/New-Monday - … - Skillmatrix A4.pdf"
```

Das schreibt `arbeit/figma_bibliothek.json` – je Fassung der Befüllungsplan
und unter `uploads` die Bilder in fester Reihenfolge – und daneben die rohen
Pläne für den Rückfall. Die Hinweise lesen: „sprengt die Komponenten — roh
bauen“ heißt, diese eine Fassung kommt aus `references/figma-roh.md`.

**2. Vorflug** — ein lesender Aufruf, der genau einen Import per Key probiert:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --skript vorflug arbeit/ --seite 1:32
```

Die Ausgabe ist der `code` für `use_figma`. Die Rückgabe nennt Seiten,
Zielseite, die Schnitte von Inter und Rethink Sans und `bibliothek_ok`. Ist
`bibliothek_ok` false (Datei nicht mit der Bibliothek verbunden, kein Zugriff
auf das Team), **beide Fassungen roh bauen** und das in der Übergabe sagen:
„Bibliothek nicht erreichbar (<fehler>), Frames ohne Komponentenbindung.“

**3. Bilder hochladen** — ein `upload_assets`-Aufruf für alle:
`count` = Zahl der `uploads`, `currentPageId` = Zielseite, **ohne `nodeIds`**
(die Bildebenen liegen in Instanzen, deren IDs `upload_assets` nicht annimmt).
Die zurückgegebenen URLs in derselben Reihenfolge mit den Dateien aus `uploads`
paaren, nach `arbeit/uploads.json` schreiben (`[{"url", "datei"}]`), dann:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_assets.py --paare arbeit/uploads.json --bilder arbeit/bilder.json
```

`bilder.json` trägt je Datei den `imageHash` und den Hilfsrahmen, den Figma
dafür auf die Seite gelegt hat. Die Bauaufrufe setzen die Hashes und räumen
die Hilfsrahmen weg.

**4. Die lange Fassung**:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --skript lang arbeit/ --seite 1:32 --bilder arbeit/bilder.json
```

Ein Seitenrahmen 1444 breit, vertikal, ohne Abstand und ohne Füllung, darin
die Instanzen `Skillmatrix lang/Kopfzeile`, `/Hero`, `/Rumpf`, `/Fuß` – wie
die Testbefüllung `4328:2839` im Master. Er steht rechts neben allem, was auf
der Seite liegt.

**5. Die A4-Fassung**:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/figma_plan.py --skript a4 arbeit/ --seite 1:32 --bilder arbeit/bilder.json
```

Je PDF-Seite eine Instanz `Skillmatrix A4/Seite`, rechts neben dem langen
Frame, 100 Abstand, oben bündig – liegt dort schon etwas, rückt die Reihe
hinter alles. Welcher Block auf welcher Seite steht, kommt wie im rohen Weg
aus dem A4-PDF; die Booleans der Seite (`Hero anzeigen`, `Zertifikate
anzeigen`, `Kernkompetenzen anzeigen`, `Tools anzeigen`, `Zertifikate am Ende
anzeigen`, `Fuß anzeigen`) schalten genau diese Blöcke.

**6. Prüfen.** Jeder Bauaufruf gibt zurück:

| Feld | Soll |
|---|---|
| `oben` (lang) | nur `INSTANCE …` – Kopfzeile, Hero, Rumpf, Fuß |
| `fehler` | leer. Sonst steht da, welcher Pfad oder welche Ebene fehlt – meist hat sich der Master geändert (Katalog neu auslesen) |
| `reste` | leer. Sichtbare Texte, die noch den Vorgabewert der Komponente tragen („Kompetenz“, „Zertifikatstitel“ …) – ein Treffer ist ein Fehler |
| `bilder` | so viele wie Bildebenen im Plan |
| `hoehe` (lang) | ±20 zur PDF-Höhe; mehr heißt, ein Text bricht anders um |

Dann je Frame ein `get_screenshot` und neben die PDF-Seiten legen: Gesicht frei
vom Verlauf, Bilder unverzerrt, keine leeren Slots, Fuß auf der letzten
A4-Seite unten.

`use_figma` ist atomar: Ein Skript, das wirft, hat nichts geschrieben. Die
Meldung lesen, beheben, erneut senden – nicht blind wiederholen.

## Was befüllt wird

Pfade gehen über die Namen der exponierten Instanzen (Breitensuche, je Schritt
neu aufgelöst – `setProperties` erneuert die Knoten darunter).

| Fassung | Instanz | Inhalt |
|---|---|---|
| lang | `Hero` | `Verfügbarkeit` (Badge), `Name`, `Rolle`, `Beschreibung` (Textbausteine), `Schwerpunkte` mit `Tag 1–3`, `Fotokarte` (Name, Erfahrung, Bild auf `Foto`) |
| lang | `Rumpf › Zertifikate` | Booleans `Kachel 5–12`; `Ueberschrift`; `Erklärung` (Titel, Beschreibung, `Tag 4–10`, Tags als `Tag n`); `Kachel n` (Titel, Aussteller, Bild auf `Bild`, Padding von `Buehne`) |
| lang | `Rumpf › Kernkompetenzen` | Booleans `Kategorie 2–8`; `Kategorie n` (`Label anzeigen`, `Karte 4–9`, Label-Text, `Karte n` mit Titel, Beschreibung, `Bewertung`) |
| lang | `Rumpf › Tools` | `Ueberschrift`; `Karten` wie eine Kategorie ohne Label |
| lang | `Fuß` | Ansprechpartner, Funktion, E-Mail, Telefon |
| A4 | `Seite` | die sechs Block-Booleans; `Kopfzeile` (`Badge anzeigen` nur Seite 1, `Verfügbarkeit`) |
| A4 | `Hero` | Name, Rolle, Beschreibung, `Schwerpunkte anzeigen`, `Schwerpunkt 2–4`; `Fotokarte` (`Foto anzeigen`, Bild auf `Foto`) |
| A4 | `Zertifikate` bzw. `Zertifikate (Ende)` | `Überschrift anzeigen`, `Qualifikationskarte anzeigen`, `Kacheln anzeigen`, `Kachel 2–12`; Karte (Titel, Satz, `Tag 2–10`); `Kachel n` (`Art` Bild / Platzhalter / Bündel, Titel, Aussteller, Anzahl, Bild, Padding von `Bühne`) |
| A4 | `Kernkompetenzen` | `Überschrift anzeigen` (nur auf der Seite mit dem Titel), `Kategorie 2–5`; `Kategorie n` (`Kompetenz 2–6`, `Label`, `Kompetenz n` mit Titel, Beschreibung, `Trennlinie oben anzeigen` ab der zweiten Zeile, `Bewertung`) |
| A4 | `Tools` | `Einträge` wie eine Kategorie, Label-Text aus |
| A4 | `Fuß` | Kontaktspalten `Ansprechpartner`, `Kontakt`, `Adresse` (Label, Name, Wert 1/2) |

Slots ohne eigenen Boolean (Kategorie-Karten 1–3, lange Kacheln 1–4, Tags 1–3)
werden bei weniger Einträgen per Sichtbarkeit ausgeblendet – Sichtbarkeit ist
ein Inhalt, keine Gestaltung. Ganze Reihen verschwinden über die Booleans.

## Bilder

- **Foto: FILL.** Hochgeladen wird der fertige Zuschnitt aus `kopf_ausschnitt.py`
  (SKILL.md, Schritt 1a) – lang `person.foto`, A4 der `-a4`-Zuschnitt. Er hat
  schon das Format der Bildebene und Luft über dem Haar; FILL zeigt ihn wie im
  PDF. Nicht in Figma per `imageTransform` nachschneiden.
- **Zertifikate: FIT, Größe über das Bildfeld.** Die Breite einer Instanz lässt
  sich nicht überschreiben; deshalb setzt der Plan die Paddings der Bühne
  (`Buehne` lang, `Bühne` A4) so, dass die Bildebene genau das
  Seitenverhältnis der Datei hat – dieselbe Rechnung wie im PDF
  (`zertifikate.py`).
- **Kein Hash, kein Beispielbild.** Fehlt für eine Bildebene der Upload, blendet
  der Bauaufruf sie aus und meldet es unter `fehler` – das Beispielbild der
  Komponente bleibt nie stehen.

## Mengen

Was die Komponenten tragen (`grenzen` in `master-bibliothek.json`):

| | lang | A4 |
|---|---|---|
| Kategorien | 8 | 5 je Seite |
| Karten / Kompetenzen je Kategorie | 9 | 6 |
| Tools | 9 | 6 |
| Zertifikatskacheln | 12 | 12 |
| Tags der Qualifikationskarte | 10 | 10 |
| Schwerpunkte | 3 | 4 |

Liegt eine Fassung darüber, meldet `figma_plan.py` das, und `--skript`
verweigert diese Fassung: Sie kommt roh. Die Regeln des Skills (fünf
Kategorien, sechs Skills, höchstens 924 Zertifikatssektion) liegen ohnehin
darunter – ein Überlauf heißt meist, dass die JSON nicht stimmt.

## Lücken der Bibliothek (Stand 2026-10-08)

In der Übergabe nennen, wenn sie greifen; behoben werden sie im Master:

- **Lange Kachel ohne Platzhalter- und Bündel-Variante.** Ein Zertifikat ohne
  Bild oder eine Sammelkachel steht lang mit leerer Bühne, ein „+n“ fehlt
  (A4 hat beides).
- **Rumpf ohne „Zertifikate am Ende“.** Mit `"zertifikate_position": "ende"`
  steht lang statt der Rumpf-Instanz ein Rahmen `Rumpf` mit den drei
  Sektions-Instanzen in der gewünschten Reihenfolge – Padding, Fläche und
  Linie roh aus `tokens.json`. Die einzige Stelle mit rohen Werten.
- **Langer Fuß: Adresse, Labels und Frage fest, deutsch.** Abweichende Adresse
  und englische Matrizen setzen dort nichts; die A4-Kontaktspalten haben alles
  als Property.

## Den Katalog neu auslesen

Wenn sich im Master Komponenten, Keys oder Property-Namen ändern (Abbruch
„hat keine Eigenschaft“ oder `fehler` „nicht gefunden“). Je Komponentenseite
ein lesender Aufruf im Master (`Components - Skillmatrix` `0:1`,
`Components – Skillmatrix kompakt` `4359:3572`), Rückgabe kompakt halten –
`use_figma` gibt höchstens 20 KB zurück:

```js
const page = await figma.getNodeByIdAsync("0:1");
await figma.setCurrentPageAsync(page);
const owners = page.findAllWithCriteria({ types: ["COMPONENT", "COMPONENT_SET"] })
  .filter(n => n.type === "COMPONENT_SET" || n.parent.type !== "COMPONENT_SET");
const out = [];
for (const o of owners) {
  if (!/^Skillmatrix lang\//.test(o.name)) continue;          // A4-Seite: alle
  const defs = {};
  for (const [k, v] of Object.entries(o.componentPropertyDefinitions))
    defs[k] = v.type === "VARIANT" ? "V:" + v.variantOptions.join("|")
            : v.type[0] + (v.type === "BOOLEAN" ? (v.defaultValue ? "1" : "0") : "");
  const base = o.type === "COMPONENT_SET" ? o.defaultVariant : o;
  const inst = {}, img = new Set();
  base.findAll(n => {
    if (n.type === "INSTANCE" && n.isExposedInstance) inst[n.name] = (inst[n.name] || 0) + 1;
    if ("fills" in n && Array.isArray(n.fills) && n.fills.some(f => f.type === "IMAGE"))
      img.add(n.name + ":" + n.type[0] + Math.round(n.width) + "x" + Math.round(n.height));
    return false; });
  out.push([o.name, o.id, o.key, Math.round(base.width) + "x" + Math.round(base.height), defs, inst, [...img]]);
}
return JSON.stringify(out);
```

Daraus `komponenten` in `master-bibliothek.json` nachziehen (Kurzformen:
`T` Text, `B1`/`B0` Boolean mit Vorgabe, `V:` Varianten, `I` Instanz-Tausch).
Ändert sich der Aufbau (neue Slots, andere Namen exponierter Instanzen), ziehen
`scripts/figma_bibliothek.py` und `grenzen` mit. Danach einmal beide Fassungen
in einer Testdatei bauen und gegen die Testbefüllungen im Master
(`4328:2839`, `4381:8605`) halten.

## Wenn es schiefgeht

Alles hier ist Zugabe. Die PDFs sind fertig und gehen so oder so raus — mit
einem Satz dazu, was an Figma nicht ging.

| Symptom | Was dahintersteckt |
|---|---|
| `bibliothek_ok: false` im Vorflug | Datei hat die Bibliothek nicht, Konto ohne Zugriff aufs Team – roh bauen (`figma-roh.md`) |
| „tool call limit“ | Kontingent des Sitzes erschöpft – nicht wiederholen, PDFs übergeben, Figma später nachholen |
| „hat keine Eigenschaft“ beim Planen | Property im Master umbenannt – Katalog neu auslesen |
| `fehler`: „nicht gefunden: …“ | exponierte Instanz umbenannt oder per Boolean aus dem Baum – Pfad im Master prüfen |
| `fehler`: „kein Upload für Bild …“ | `bilder.json` fehlt oder passt nicht zu `uploads` (Reihenfolge der URLs) |
| `reste` nicht leer | ein Slot sichtbar, aber nicht befüllt – Booleans im Plan prüfen |
| Zertifikatsbild beschnitten | Bühnen-Padding nicht gesetzt (Ebene im Master umbenannt) |
| `unloaded font` | Schrift der Bibliothek lokal nicht installiert – Vorflug zeigt die Schnitte |
| Upload hängt oder bricht ab | im Browser-Chat blockt der Proxy fremde Domains |
| „keine Seitenaufteilung im PDF“ | A4-PDF nicht mit `render_skillmatrix.py` gerendert – neu rendern |

## Was nicht passiert

- **Keine Instanz wird gelöst** (`detachInstance`), keine Farbe, Schrift,
  Größe oder kein Abstand von Hand – außer dem Rumpf-Rahmen der Variante
  „Zertifikate am Ende“.
- **Keine neuen Styles, Variablen oder Komponenten** in der Zieldatei; der
  Import per Key bringt nur die Bibliothekskomponenten mit.
- **Im Master wird nichts geschrieben.** Er wird nur gelesen.
- **Nichts überschreiben, verschieben oder löschen**, was schon auf der Seite
  liegt; neue Frames kommen rechts daneben.
- **Kein Vorgabeinhalt bleibt stehen** – kein Beispielbild, kein
  Platzhaltertext (`reste`).
