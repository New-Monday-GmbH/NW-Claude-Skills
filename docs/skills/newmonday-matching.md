# newmonday-matching

Gleicht eine Projektanfrage nach einem festen Verfahren gegen den Kandidatenpool
und den JOIN-Bestand ab und schreibt eine Auswertung im immer gleichen Aufbau.

Zurück zu [Start](../Start.md).

## Wofür

Damit jedes Matching gleich geprüft wird, egal wer es macht: dieselben Achsen,
dasselbe Vokabular, dieselbe 70-%-Schwelle, dieselbe Vita-Prüfung und dieselbe
Auswertung.

## Eingang

- die Ausschreibung oder Anfrage (Text, PDF oder CRM-ID)
- falls vorhanden: das Feedback des Kunden zu einer früheren Absage

## Ausgang

- eine Matching-Auswertung als Markdown für den internen Vault
- eine Empfehlung: Treffer, beschaffbar oder absagen

Der Skill schreibt nichts ins CRM und nichts nach JOIN und schickt keine Mail.

## So startest du ihn

In Claude Code die Ausschreibung einfügen und etwa „Matching für diese Anfrage“
schreiben. Für den Pool-Abgleich braucht das Skript einmalig
`scripts/matching.config.json` mit CRM-Adresse und Schlüssel (Vorlage liegt
daneben, die Datei selbst wird nie committet).

## Die Regeln in einem Satz je Regel

- Unter 70 % Abdeckung wird niemand angesprochen.
- Nie mit dokumentierter Muss-Lücke einreichen.
- Ein Profil, außer der Vermittler fragt ausdrücklich nach mehreren.
- Das Scoring findet Kandidaten, es beurteilt sie nicht – die Spitzengruppe wird gelesen.
- Jedes Muss-Kriterium muss durch bezahlte Projektarbeit belegt sein.

Die vollständigen Regeln stehen in der [SKILL.md](../../newmonday-matching/SKILL.md),
das Vokabular in [vokabular.md](../../newmonday-matching/references/vokabular.md),
der Aufbau der Auswertung in
[auswertung-vorlage.md](../../newmonday-matching/references/auswertung-vorlage.md)
und die Herleitung in
[erkenntnisse.md](../../newmonday-matching/references/erkenntnisse.md).
