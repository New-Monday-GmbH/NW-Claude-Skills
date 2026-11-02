---
name: newmonday-matching
description: Profilmatching der New Monday GmbH – gleicht eine Projektanfrage (Vermittler-Ausschreibung, Direktanfrage, Anforderungsprofil) nach einem festen Verfahren gegen den Kandidatenpool im EspoCRM und den JOIN-Bewerberbestand ab und schreibt eine einheitliche Matching-Auswertung mit Empfehlung. Nutze diesen Skill immer, wenn ein Matching, ein Abgleich, eine Trefferliste, „wer passt auf diese Anfrage“, „haben wir jemanden für …“, eine Kandidatenauswahl oder eine Einreichungsempfehlung gefragt ist – auch wenn nur eine Ausschreibung eingefügt wird und das Wort „Matching“ nicht fällt. Gilt ebenso für den Nachlauf nach einer Kundenabsage. Für die Dokumente danach sind newmonday-cv, newmonday-skillmatrix und newmonday-portfolio zuständig.
---

# New Monday Profilmatching

Eine Anfrage, ein Verfahren, eine Auswertung im immer gleichen Aufbau – egal wer
das Matching macht. Der Skill **liest und rechnet**. Er schreibt nichts ins CRM
und nichts nach JOIN, und er schickt keine E-Mail.

Das Verfahren ist aus den Matchings von September und Oktober 2026 entstanden.
Was dort gelernt wurde, steht in `references/erkenntnisse.md` und ist hier
bereits eingearbeitet.

## 🔒 Regeln, die über allem stehen

1. **In JOIN wird nichts ohne Manuels Bestätigung verändert.**
2. **Es geht keine E-Mail und keine Einreichung ohne Manuels Freigabe raus.**
3. **Unter 70 % Abdeckung wird niemand angesprochen.** Kein Anruf, keine Mail,
   keine Rückfrage zu fehlenden Skills. Festgelegt von Manuel Klein am 22.09.2026.
4. **Nie einreichen, wenn eine Muss-Lücke dokumentiert ist.** Eine bekannte Lücke
   verbraucht beim Vermittler genau das Vertrauen, das den Kanal trägt.
5. **Ein Profil, außer der Vermittler fragt ausdrücklich nach mehreren.** Dann
   zwei, jedes mit eigener Begründung. Das Problem ist das ungefragte Nachlegen.
6. **Keine Kandidatendaten in dieses Repo.** Auswertungen gehören in den
   internen Vault bzw. ins CRM, nie hierher.

## Die zwei Quellen

| Quelle | Was drin ist | Wie abgeglichen wird |
|---|---|---|
| **Pool im EspoCRM** (`CKandidat`) | Angestellte und Freelancer mit Vertragsgrundlage, gepflegte Felder | `scripts/matching.py` – Quote in Prozent nach festen Gewichten |
| **JOIN-Bewerberbestand** (Volltext-Export) | alle Lebensläufe aus JOIN-Bewerbungen, mehrere Tausend | Trichter über Ausschlusskriterien und „x von n Muss“, danach Lesen |

Immer **zuerst der Pool**, dann JOIN. Ein Pool-Treffer ist sofort einreichbar,
ein JOIN-Bewerber braucht erst eine Vertragsgrundlage.

**Datenstand immer angeben.** Ist der JOIN-Export älter als ein paar Tage, steht
das ganz oben in der Auswertung, mit dem Datum. Aktualisiert wird er auf dem Mac
über den JOIN-Connector („CV-Export starten“).

## Ablauf

### Schritt 1 · Anfrage zerlegen

Aus der Ausschreibung eine Anforderungstabelle machen, in den Achsen und mit dem
Vokabular aus `references/vokabular.md`:

| Achse | An der Anfrage |
|---|---|
| Rolle | genau eine Hauptrolle |
| Seniorität | Junior · Mid · Senior · Principal |
| Skills | **Muss** und **Kann** getrennt, Werte aus dem Vokabular |
| Fachdomäne | nur, wenn die Anfrage sie fordert |
| Sprache | Deutschniveau, ggf. Englisch |
| Zeit und Geld | Start, Auslastung, Ort und Präsenztage, Kundensatz |

Dann ausdrücklich festlegen und in die Auswertung schreiben:

- **Ausschlusskriterien (K.o.)** – was einen Kandidaten ganz rausnimmt.
  Immer: Deutsch unter dem geforderten Niveau, Status *ausgeschieden* oder
  *nicht verfügbar*, Mindestsatz über Kundensatz. Dazu alles, was die Anfrage
  oder ein Kundenfeedback als hart markiert.
- **Prämisse des Laufs** – z. B. „Wir stellen ein: Bewerberstatus und früheres
  REJECTED in JOIN sind kein Ausschluss“. Ohne genannte Prämisse gilt: nur
  Kandidaten mit Vertragsgrundlage oder klarer Einstellungsabsicht.
- **Offene Fragen an den Vermittler** – vor allem „Ist X Muss oder Wunsch?“.
  Davon hängt oft das ganze Ergebnis ab, also früh fragen statt raten.

Liegt ein **Kundenfeedback zu einer Absage** vor, ist das die wertvollste Quelle:
jede dort benannte Lücke wird zum harten Ausschlusskriterium des nächsten Laufs.

### Schritt 2 · Pool abgleichen (EspoCRM)

```bash
python3 scripts/matching.py                      # offene Anfragen mit ID
python3 scripts/matching.py --anfrage <ID>       # Abgleich
python3 scripts/matching.py --anfrage <ID> --alle --csv
```

Einrichtung: `scripts/matching.config.beispiel.json` nach
`scripts/matching.config.json` kopieren, CRM-Adresse und Schlüssel eintragen.
Die Kopie ist per `.gitignore` ausgeschlossen und geht nie in Teams, SharePoint
oder eine Mail. Ohne gepflegtes Anforderungsprofil an der Anfrage bricht das
Skript mit Hinweis ab – das ist Absicht.

**So wird gerechnet** (bewusst einfach, jede Quote ist nachvollziehbar):

| Regel | Wirkung |
|---|---|
| Muss-Skill in *Skills (geprüft)* | zählt 1,0 |
| Muss-Skill nur in *Skills (erkannt)* | zählt 0,5, Kennzeichnung „ungeprüft“ |
| Kann-Skill | zählt 0,33 (ungeprüft 0,165) |
| Fachdomäne getroffen (falls gefordert) | zählt wie ein Muss-Skill |
| Rolle benachbart | −20 % |
| Rolle passt nicht | −60 % |
| Seniorität zu niedrig | −30 % (zu hoch kostet nichts) |
| frei erst nach Projektstart | −15 % |

Ausgabe in **zwei Zuständen**, einen Grenzfall gibt es nicht:

- **●** ab 70 % – vorstellen und die Person ansprechen
- **·** darunter – nicht ansprechen, absagen oder sourcen

Benachbarte Rollen (mit Abschlag statt Volltreffer): UX/UI Design → Product
Owner / PM · Frontend ↔ Fullstack ↔ Backend · DevOps / Cloud ↔ Infrastruktur ·
Data / BI → Backend.

⚠️ Die Quote rechnet gegen **gepflegte** Felder. Bei dünn gepflegten Profilen
sagt eine niedrige Quote mehr über die Datenqualität als über die Person – das
gehört dann als Datenlücke in die Auswertung, nicht als Absage an den Menschen.

### Schritt 3 · JOIN-Bestand abgleichen (Trichter)

Wenn der Pool keinen Treffer ≥ 70 % liefert, oder zusätzlich, wenn die Anfrage
mehrere Profile verlangt:

1. **Hart filtern** auf Rolle und alle K.-o.-Kriterien aus Schritt 1.
2. **Muss-Kriterien zählen**: „x von n“. Den Trichter mit Zahlen in die
   Auswertung schreiben (Bestand → nach K.o. → 6 von 8 → 7 von 8 → 8 von 8).
3. **Gewichten, wo nötig.** Bei vielen Treffern ein Score über die Kriterien der
   Anfrage, mit offen genannten Gewichten. Faustregel: Rolle am höchsten, dann
   Domäne, dann die fachlichen Kernaufgaben, dann Sprache, dann Methoden.
   Beispiel eines BA-Laufs: Rolle 30 · Domäne 22 · Spezifikation 18 ·
   Prozessanalyse 16 · Test/QS 14 · Deutsch 12 · Stakeholder 10 · Englisch 8 ·
   Agil 6.
4. **Die Spitzengruppe einzeln lesen.** Das Scoring findet Kandidaten, es
   beurteilt sie nicht.

Die 70-%-Regel gilt hier sinngemäß: Wer ein Muss-Kriterium nicht belegt, wird
nicht angesprochen.

### Schritt 4 · Domäne prüfen – Scheintreffer aussortieren

Ein Begriff im Lebenslauf ist noch keine Domänenpraxis. Typische Scheintreffer:

- **Kunde in der Kundenliste, aber andere Tätigkeit** (Energieversorger als
  Auftraggeber eines Werbefilms ist keine Energiewirtschaft).
- **Gleiches Wort, andere Branche** („Payment“ als E-Commerce-Checkout ist kein
  Banking-Zahlungsverkehr).
- **Tool-Liste statt Projekt** („GPT, Gemini, Claude“ in der Skill-Liste ist
  kein belegter KI-Einsatz im Designprozess).
- **Vorgestellt ist nicht gearbeitet.** Eine frühere Einreichung bei einer
  Krankenkasse macht niemanden zur GKV-Expertin.

Ein hoher Score ohne die richtige Domäne führt genau zu der Absage „punktuelle
Erfahrung, aber keine tiefe Praxis“. Deshalb: Wer nur über einen Scheintreffer
auf die Quote kommt, steht nicht vorne – egal wie hoch der Score ist.

### Schritt 5 · Vita-Prüfung (K.o. vor jeder Empfehlung)

Jeder empfohlene Kandidat muss sie bestehen:

- Stationen mit **Arbeitgeber, Zeitraum und Rolle**.
- **Jedes Muss-Kriterium durch bezahlte Projektarbeit belegt.**
- Weiterbildung, Kurs oder Eigenprojekt zählen **nicht** als Erfahrungsnachweis.
  Ausnahme: ein eigenes Produkt, das nachweislich in Produktion läuft – dann
  ausdrücklich als solches kennzeichnen.

Was nur im Lebenslauf steht und nicht im CRM als *geprüft*, ist bis zur
Bestätigung „ungeprüft“ – vor der Einreichung durchsehen und die zutreffenden
Skills in *Skills (geprüft)* übernehmen lassen.

### Schritt 6 · Entscheidung

Genau eine von drei:

| Ergebnis | Handlung |
|---|---|
| **Treffer** | Profil(e) empfehlen, Klärpunkte vor Einreichung auflisten, Freigabe einholen |
| **Kein Treffer, aber beschaffbar** | Sourcing mit Frist vorschlagen (z. B. eigene JOIN-Ausschreibung, wenn der Bestand die Rolle gar nicht enthält) |
| **Kein Treffer, nicht beschaffbar** | **sofort absagen**, mit Verlustgrund – eine schnelle Absage ist beim Vermittler mehr wert als Schweigen |

**Vor jeder Einreichung klären** (als Checkliste in die Auswertung):
Verfügbarkeit · Satzvorstellung · Deutschniveau, wenn nicht belegt ·
Vertragsgrundlage bei JOIN-Bewerbern · Ort und Präsenztage · Portfolio
(bei NDA anfordern).

**Im Anschreiben** das nach vorn, wonach der Kunde gefragt hat – bei KI-Praxis
mit Modellnamen und Einsatzzweck, nicht als Schlagwort.

**Nach jeder Absage im Beziehungskanal nachfragen:** „Woran hat es konkret
gelegen – Profil, Satz oder Timing?“ Die Antwort geht als K.o.-Kriterium in den
nächsten Lauf.

## Die Auswertung

Immer im Aufbau von `references/auswertung-vorlage.md`, abgelegt im internen
Vault unter `05 Recruiting/` als
`00 Matching - <Rolle> (<Vermittler> <Referenz>) <TT.MM.JJJJ>.md`.

Kurz und ehrlich: Wenn es den 100-%-Treffer nicht gibt, steht das in einem
eigenen Abschnitt mit den Gründen in Reihenfolge (fehlende Domäne, fehlende
Geografie, falsche Grundgesamtheit …) – nicht versteckt unter den Kandidaten.

## Datenqualität ist Teil des Ergebnisses

Jeder Lauf zeigt auch, wo die Daten fehlen: Kandidaten mit ein bis zwei
gepflegten Skills, fehlende Fachdomäne, Deutschniveau „unbekannt“, Skills, die
im Lebenslauf stehen, aber nicht im Profil. Solche Funde kommen als eigener
kurzer Abschnitt „Datenlücken“ in die Auswertung, damit sie nachgepflegt werden.
