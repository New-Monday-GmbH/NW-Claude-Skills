# Vorlage · Matching-Auswertung

Jede Auswertung hat diesen Aufbau, in dieser Reihenfolge. Abschnitte ohne Inhalt
bleiben mit einem Satz stehen („Keine Datenlücken gefunden.“), damit jede
Auswertung gleich lesbar ist.

Abgelegt wird sie im **internen Vault**, nie in diesem Repo.

Zurück zu [SKILL.md](../SKILL.md).

---

```markdown
---
tags: [matching, <rolle>, <domäne>, <vermittler>]
kontext: arbeit
stand: JJJJ-MM-TT
anfrage_nr: <CRM-Nummer>
referenz: "<Referenz des Vermittlers>"
vermittler: "<Firma>"
endkunde: "<Endkunde, falls bekannt>"
datenbasis: "<Pool: n Kandidaten · JOIN: n Volltexte, Stand TT.MM.JJJJ>"
praemisse: "<z. B. Wir stellen ein – Bewerberstatus ist kein Ausschluss>"
ergebnis: "<ein Satz>"
---

# Matching · <Rolle> · <Vermittler> <Referenz>

## 🔴 Vorweg            ← nur wenn nötig: Datenbasis veraltet, Rolle nicht im Bestand o. Ä.

## Die Anforderung

| Achse | Gefordert | Muss / Kann |
|---|---|---|
| Rolle | | |
| Seniorität | | |
| Skills | | |
| Fachdomäne | | |
| Sprache | | |
| Start · Ort · Satz | | |

**Ausschlusskriterien (K.o.):** …
**Offene Fragen an den Vermittler:** … (vor allem: Muss oder Wunsch?)

## Methode

Pool: Quote nach `matching.py`, Schwelle 70 %.
JOIN: Filter und Gewichte offen nennen.

| Filter | übrig |
|---|---:|
| Bestand gesamt | |
| nach K.o. | |
| x−2 von x Muss | |
| x−1 von x Muss | |
| **x von x Muss** | |

## Kandidaten

### 🥇 1 · <Name> — <ein Satz, warum>
Quote/Score · Status · Ort · verfügbar ab

| | Kriterium | Beleg (Station, Zeitraum) |
|---|---|---|
| 🟢 | | |
| 🟡 | | |
| 🔴 | | |

### 🥈 2 · …

## Wer trotz hohem Score nicht vorne steht

| Name | Warum nicht (Scheintreffer, Domäne, Vita) |
|---|---|

## Ehrlich zum Risiko     ← wenn es den 100-%-Treffer nicht gibt: Gründe in Reihenfolge

## Vita-Prüfung

Bestanden / nicht bestanden je empfohlenem Kandidaten, mit Begründung.

## 📋 Empfehlung

Treffer · beschaffbar · absagen – genau eins. Ein Profil, außer der Vermittler
fragt ausdrücklich nach mehreren.

### Vor der Einreichung

| | |
|---|---|
| 1 | Verfügbarkeit und Satz |
| 2 | Deutschniveau, falls nicht belegt |
| 3 | Vertragsgrundlage (JOIN-Bewerber) |
| 4 | Portfolio / NDA |
| 5 | Was ins Anschreiben nach vorn gehört |

## Datenlücken

Was im CRM fehlt oder falsch steht und nachgepflegt werden muss.

## Nächste Schritte

- [ ] …
```
