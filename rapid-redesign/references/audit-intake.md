# Intake – das Audit vor dem Start konfigurieren

Bevor der Audit losläuft, wird **interaktiv geklärt, wofür er gemacht wird**. Das ist der „Chatbot"-Schritt: ein kurzer, geführter Dialog (per `AskUserQuestion`, sonst als normale Rückfragen), der Zielgruppe und Umfang festlegt. Erst danach beginnt die Bewertung/der Website-Bau – die Antworten steuern **Schwerpunkt, Sektionsauswahl und Sprache**.

Führe das Intake **immer zu Beginn** (SKILL.md Schritt 2). Ausnahme: Der Nutzer hat Zielgruppe und Umfang bereits klar vorgegeben – dann nur kurz bestätigen.

## Die drei Intake-Fragen

### 1) Zielgruppe (Pflicht, Einzelauswahl)
Wem stellen wir das Audit vor? → bestimmt den Schwerpunkt. Optionen und Wirkung siehe `audience-profiles.md`:
- **Marketing / Growth** → Fokus Conversion & Wirkung
- **Entscheider / GF** → Business-Impact, Risiko, Priorisierung
- **Tech / Engineering** → Konsole, Performance, WCAG mit Werten, code-nah
- **Design / Product** → Heuristiken, visuelle Konsistenz, Flows

Default, wenn nichts genannt: **Entscheider / gemischt**.

### 2) Sektions-Umfang – **standardmäßig ALLES, keine Checklisten-Abfrage**
Es wird immer das **volle Programm** gebaut — alle Sektionen unten sind gesetzt. **Keine Mehrfachauswahl-Fragen mehr**; stattdessen im Intake nur der Einzeiler: *„Ich baue das komplette Deck (Personas, Jobs to be done, Positionierung, Erkenntnisse, Wettbewerber & Inspiration, Wireframes, Next Steps, Projektablauf, Detail-Findings) — sag Bescheid, falls etwas rausfallen soll."* Nur wenn der Nutzer einschränkt, wird weggelassen.

Das volle Programm umfasst:
- **Zielgruppe / Persona** – **2–3 Personas**; eine ist die **Fokus-Persona** (voll ausgeklappt), die anderen als kompakte Karten. Welche der Fokus ist, wählt der Nutzer (siehe Folge-Rückfrage — das bleibt die einzige Pflicht-Rückfrage neben der Zielgruppe).
- **Jobs To Be Done** – direkt nach den Personas: funktionale + emotionale Jobs der Fokus-Persona (je 3, RR-Vorlage 1:1)
- **Positionierung** – Markenpositionierung (Fokus, Merkmale, Zusatznutzen)
- **Strategische Erkenntnisse** – Herzstück: Zielsatz-Folie + je Erkenntnis eine Folie + „Was gut funktioniert"
- **Wettbewerber & Inspiration** – je Wettbewerber eine Folie (gut/schlechter) + Inspiration (nur Bilder)
- **Unser Vorschlag (Wireframes)** – mindestens zwei Skizzen (Startseite + wichtigste Unterseite)
- **Next Steps / Angebot** – „Komplettes Redesign aus einer Hand" (inkl. Dauer & Investition)
- **Projektablauf** – 3-Phasen-Folie
- **Detail-Findings (technisch)** – aufklappbares Accordion auf der Scope-Folie

**Wettbewerber ohne Rückfrage:** Alle relevanten Wettbewerber **selbst recherchieren und ALLE erfassen** (echte Screenshots der Startseiten) — keine Auswahl-Bestätigung. Die erfasste Liste im Ergebnis transparent nennen; im Admin lässt sich jede Wettbewerber-Folie löschen.

Immer dabei: Cover, Intro-Sequenz (Slides 3–7), Executive Summary, Scope, Roadmap, Abschluss.

> **Immer enthalten (nicht abfragen):** Cover, **Agenda/Inhalt** und die feste RR-Intro-Sequenz **Über New Monday → Referenzen & Expertise → Über das Projekt → Unser Redesign-Fokus → Unser Vorgehen** (RR-Slides 3–7). „Über das Projekt" und „Redesign-Fokus" bekommen **projektspezifischen** Text; die übrigen Intro-Slides sind agentur-generisch. Details: `website-build.md` → Sektions-Katalog.

## Folge-Rückfragen (nur wenn nötig)
- **Persona/Zielgruppe gewählt – Fokus-Persona bestätigen (Pflicht bei dieser Sektion):** Leite aus dem Audit **2–3 Personas** ab (Rollen/Entscheidungswege der Website-Besucher) und lege sie dem Nutzer **vor dem Bau** per `AskUserQuestion` vor: **„Welche ist die Fokus-Persona?"** – mit der Option, eine Persona **zu ändern/anzupassen** (Name, Rolle, Ziele). Die gewählte Fokus-Persona **zieht sich durch das Deck**: die Zielsatz-Divider, die strategischen Erkenntnisse und der Redesign-Fokus argumentieren aus **ihrer** Sicht (ihre Ziele/Frustrationen), sodass erkennbar wird, dass das Projekt **auf sie zugeschnitten** ist. Die übrigen Personas bleiben als kompakte Karten sichtbar (bewusst nachgeordnet). **Wichtig: JEDE Persona mit Volldaten UND `kurz` texten** (siehe `deck-content-schema.md`) – und für die persona-geprägten Folien (Zielsatz-Divider, Redesign-Fokus, Erkenntnis-Divider) **`personaVarianten` mitschreiben**. Dann lässt sich die Fokus-Persona später im **Admin-Modus überall** (Toolbar) per Klick umschalten, und die Persona-Folie **und die Varianten-Texte wechseln mit** – sichtbar zugeschnitten. Folien ohne Varianten behalten ihren Text (im Admin direkt editierbar). **Merke:** Die Zielgruppe aus Frage 1 (Publikum der Präsentation) bleibt davon unberührt – sie steuert Sprache/Reihenfolge, nicht die Persona-Texte.
- **Wettbewerber:** KEINE Auswahl-Rückfrage. Alle relevanten Wettbewerber recherchieren und **alle** mit `audit_capture.py shot … --fold` als echte Screenshots erfassen (keine erfundenen Screens); die Liste im Ergebnis nennen. Nur nachfragen, wenn die Recherche keinen klaren Markt ergibt.
- **Wireframes gewählt:** klären, welche Seite(n) (Default: Startseite). Skizzen als echte HTML/CSS-Blöcke bauen, klar als „Vorschlag/Wireframe" gekennzeichnet – nicht als fertiges Design ausgeben.
- **Sehr große Website (> 40 Seiten):** klären, ob repräsentative Vertreter je Seitentyp genügen (siehe SKILL.md Schritt 3).

## Mapping Antworten → Bau
- Zielgruppe → Reihenfolge/Gewichtung/Sprache (`audience-profiles.md`) + Hero-Untertitel („Fokus: …").
- Gewählte Sektionen → nur diese Blöcke aus dem Katalog in `website-build.md` bauen, in RR-Reihenfolge.
- Nicht gewählte optionale Sektionen weglassen (keine leeren Platzhalter).

## Beispiel (dieser worksdone-Lauf)
Zielgruppe **Marketing**; Strategie: Conversion & Copy, Zielgruppe/Personas, Positionierung, Wettbewerber & Inspiration; Abschluss: Unser Vorschlag (Wireframes), Next Steps, Über das Projekt, Agenda → **volle RR-Präsentation mit Conversion-Schwerpunkt**.
