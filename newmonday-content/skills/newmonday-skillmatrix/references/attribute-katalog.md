# Attribut-Katalog — Skills, Kategorien und Standardbeschreibungen

Der Katalog spiegelt **1:1 den Figma-Frame `Skill Matrix Pool Refactored`** in
der Datei `Portfolio - CV Master` (Section „SKill Matrix Pool"). Er ist der
**Wortschatz** der Skillmatrix: Steht ein Attribut hier, werden Name und
Beschreibung **woertlich** uebernommen — so tragen alle Matrizen fuer denselben
Skill denselben Text, und die Dokumente bleiben ueber Kandidaten hinweg
vergleichbar. Nur was hier fehlt, wird neu formuliert, im selben Stil
(Muster am Ende).

**Der Pool ist die Quelle, diese Datei die Kopie.** Bei Abweichung gewinnt
Figma. Erzeugt wird sie mit `scripts/katalog_aus_pool.py` — nicht von Hand
nachgepflegt.

## Die harten Regeln

- **Ab drei Punkten, sonst gar nicht.** Ein Skill kommt nur in die Matrix, wenn
  die Bewertung **mindestens 3** ergibt. Alles darunter wird **nicht
  angezeigt** — nicht abgewertet, nicht in Klammern, nicht kleiner gesetzt:
  weggelassen. Eine Skillmatrix ist ein Verkaufsdokument; was schwach belegt
  ist, gehoert nicht hinein.
- **Hoechstens 24 Kernkompetenzen.** Die Sektion traegt maximal **vier
  Kategorien zu je sechs Skills**, gesetzt als **drei Karten pro Reihe, zwei
  Reihen** je Kategorie.
- **`Tools` ist eine eigene Sektion**, keine Kategorie. Sie bekommt eine eigene
  Ueberschrift mit Icon wie „Kernkompetenzen" und steht **davor**; ein
  Kategorielabel innerhalb der Sektion entfaellt. Sie zaehlt nicht gegen die
  24. `Coding Skills` ist dagegen eine gewoehnliche Kategorie innerhalb der
  Kernkompetenzen und ersetzt dann eine der vier.
- **Attributnamen sind englisch**, Beschreibungen deutsch. Eine Spalte, keine
  zweite. Fuer eine englische Matrix wird beim Bauen uebersetzt und in der
  Uebergabe gemeldet.
- **Keine Bindestriche in Attributnamen.** „Microinteractions", nicht
  „Micro-interactions"; „Data Driven Design", nicht „Data-Driven Design".
- **Produktnamen so, wie der Hersteller sie schreibt.** Belegbare
  Eigenschreibung schlaegt jede Zuruf-Variante — „Fullstory", nicht
  „FullStory"; „Hotjar", nicht „HotJar"; „UXPin", nicht „UxPin". Im Zweifel
  auf der Herstellerseite nachsehen und die Abweichung in der Uebergabe
  nennen, statt sie stillschweigend zu uebernehmen.
- **Jeder Name kommt genau einmal vor**, ueber alle Kategorien hinweg.

## Die Kategorien

1. **UX Strategy & Product Discovery** (9)
2. **User Research & Insights** (13)
3. **Interaction & Visual Design** (11)
4. **UI Design & Visual Systems** (8)
5. **Design Systems & Scaling** (8)
6. **Usability Testing & Evaluation** (10)
7. **Accessibility & Inclusive Design** (3)
8. **Agile Product Delivery** (7)
9. **Stakeholder Management & Facilitation** (8)
10. **Development Collaboration** (7)
11. **AI & Emerging Tech** (11)
12. **Tools** (11)
13. **Coding Skills** (10)

Eine Matrix nimmt **drei bis vier** Kategorien als Kernkompetenzen — die, die das Profil belegt, die staerkste zuerst — und dazu optional `Tools`.

---

## UX Strategy & Product Discovery

| Attribut | Beschreibung |
|---|---|
| User Centered Design | Lösungen basierend auf echten Nutzerbedürfnissen und -verhalten erstellen. |
| End to End UX Design | Komplette Nutzererlebnisse von der Idee bis zur Auslieferung gestalten. |
| Product Discovery | Probleme identifizieren und die richtige Produktstrategie festlegen. |
| UX Strategy | Langfristige UX-Vision und Prinzipien definieren. |
| Experience Vision | Einen klaren Zielzustand für zukünftige Nutzererlebnisse schaffen. |
| UX Principles & Guidelines | Regeln für konsistente Designentscheidungen festlegen. |
| Business to UX Translation | Geschäftliche Anforderungen in nutzerorientierte Lösungen umsetzen. |
| Product Thinking | Ergebnisorientierte, nutzerzentrierte Produkte entwickeln. |
| UX Roadmapping | UX-Initiativen über die Zeit planen. |

## User Research & Insights

| Attribut | Beschreibung |
|---|---|
| UX Research | Planung und Durchführung qualitativer und quantitativer Studien. |
| Qualitative Research | Tiefgehende Erkenntnisse durch Interviews und Beobachtungen gewinnen. |
| Quantitative Research | Analyse des Nutzerverhaltens durch Daten und Umfragen. |
| Data Driven Design | Designentscheidungen auf Basis von Nutzungsdaten und Tests treffen. |
| User Interviews & Testing | Moderierte und unmoderierte Sitzungen durchführen. |
| Stakeholder Interviews | Geschäftsperspektiven und Einschränkungen verstehen. |
| Persona Creation | Modellierung wichtiger Nutzergruppen. |
| Jobs to be Done | Verstehen der Nutzermotivationen und Ziele. |
| Journey Mapping | Visualisierung der Nutzerreise von Anfang bis Ende. |
| Pain Point Analysis | Identifikation von Nutzerproblemen und Chancen. |
| Competitive Analysis | Bewertung von Markt- und Wettbewerberlösungen. |
| Behavioral Analysis | Interpretation realer Nutzungsdaten. |
| Research Synthesis | Daten in umsetzbare Empfehlungen umwandeln. |

## Interaction & Visual Design

| Attribut | Beschreibung |
|---|---|
| Interaction Design | Gestaltung der Nutzerinteraktion mit Produkten. |
| Information Architecture | Komplexe Informationen klar strukturieren. |
| User Flows | Nutzerreisen Schritt für Schritt abbilden. |
| Wireframing & Prototyping | Von Low Fidelity Wireframes bis zu interaktiven High Fidelity Prototypen. |
| Microinteractions | Gestaltung kleiner interaktiver Details. |
| Responsive Web Design | Benutzerfreundlichkeit auf allen Geräten sicherstellen. |
| Mobile First Design | Design für mobile Geräte als Hauptplattform. |
| Conversion Optimization | Nutzerwege verbessern, um Ergebnisse zu steigern. |
| UX Writing | Klare und hilfreiche Interfacetexte verfassen. |
| Emotional Design | Emotionale Ansprache der Zielgruppe. |
| Ideation | Erste Ansätze zur Erstellung oder Überarbeitung von Anwendungen. |

## UI Design & Visual Systems

| Attribut | Beschreibung |
|---|---|
| UI Design | Gestaltung von User Interfaces für digitale Produkte. |
| Scalable UI Concepts | Wiederverwendbare und anpassbare UI-Patterns erstellen. |
| Design Guide | Layouts, Farben und Typografie festlegen. |
| Consistent Interfaces | Visuelle und funktionale Konsistenz sicherstellen. |
| Component Based Design | Gestaltung modularer UI-Elemente. |
| UI & Pattern Libraries | Aufbau wiederverwendbarer Designkomponenten. |
| Figma Component Systems | Pflege von Komponenten, Varianten und Variablen. |
| UI Quality Assurance | Prüfung und Verbesserung der visuellen Qualität. |

## Design Systems & Scaling

| Attribut | Beschreibung |
|---|---|
| Design Systems | Aufbau skalierbarer und barrierefreier Komponentenbibliotheken. |
| Design Tokens | Pflege zentraler Designvariablen wie Farben und Spacing. |
| Product Systemization | Standardisierung von Designpatterns im Produkt. |
| Component Standards | Festlegung wiederverwendbarer UI-Bausteine. |
| Design Governance | Sicherung der Konsistenz über Teams hinweg. |
| Documentation | Erstellung klarer Designrichtlinien. |
| Cross Platform Consistency | Einheitliche Erlebnisse über Plattformen hinweg sicherstellen. |
| UX/UI Scaling | Ausweitung des Designs auf große Ökosysteme. |

## Usability Testing & Evaluation

| Attribut | Beschreibung |
|---|---|
| Usability Testing | Produkte mit echten Nutzern testen. |
| Remote Testing | Tests online durchführen. |
| Test Planning | Usabilitystudien strukturiert aufsetzen. |
| Test Moderation | Nutzer durch Testsitzungen führen. |
| Prototype Validation | Konzepte vor der Entwicklung testen. |
| Heuristic Evaluation | UX anhand von Best Practices prüfen. |
| UX Audits | Gesamtqualität des Nutzererlebnisses bewerten. |
| Accessibility Audits | Einhaltung von Accessibilitystandards prüfen. |
| A/B Testing | Designvarianten vergleichen. |
| Insight Reporting | Testergebnisse als umsetzbare Empfehlungen aufbereiten. |

## Accessibility & Inclusive Design

| Attribut | Beschreibung |
|---|---|
| Accessible Design | Gestaltung für Nutzer mit Behinderungen. |
| Inclusive Design | Gestaltung für vielfältige Nutzergruppen. |
| Regulatory Compliance | Erfüllung gesetzlicher Barrierefreiheitsanforderungen. |

## Agile Product Delivery

| Attribut | Beschreibung |
|---|---|
| Agile UX Collaboration | Zusammenarbeit in agilen Produktteams. |
| Scrum / Kanban | Anwendung agiler Frameworks. |
| Design Sprints | Workshops zur schnellen Lösungsfindung. |
| Backlog Refinement | Schärfen von Produktanforderungen im Backlog. |
| Sprint Support | Begleitung der Entwicklungszyklen. |
| MVP Delivery | Launch früher Produktversionen. |
| Iterative Improvement | Laufende Optimierung von Produkten. |

## Stakeholder Management & Facilitation

| Attribut | Beschreibung |
|---|---|
| Stakeholder Management | Abstimmung von Business und Produktteams. |
| Workshop Facilitation | Leitung gemeinsamer Arbeitssessions. |
| Teamlead | Aufbau und Führung von Designteams. |
| Design Presentation | Klare Vermittlung von Designideen. |
| Decision Facilitation | Begleitung von Produktentscheidungen. |
| Cross Team Alignment | Verbindung von UX, Business und Tech. |
| Conflict Resolution | Auflösung von Differenzen zwischen Stakeholdern. |
| Consulting | Beratung von Teams und Kunden. |

## Development Collaboration

| Attribut | Beschreibung |
|---|---|
| Dev Collaboration | Enge Zusammenarbeit mit Entwicklern. |
| Design Handoff | Aufbereitung von Designs für die Entwicklung. |
| UX Specifications | Erstellung umsetzungsreifer Dokumentation. |
| Frontend Understanding | Kenntnis technischer Rahmenbedingungen. |
| Design QA | Sicherstellung der korrekten Umsetzung. |
| Feasibility Assessment | Einschätzung der technischen Machbarkeit. |
| Design to Code | Überführung von Designs in produktiven Code. |

## AI & Emerging Tech

| Attribut | Beschreibung |
|---|---|
| AI Powered UX | Gestaltung KI-getriebener Nutzererlebnisse. |
| Conversational Design | Gestaltung von Chat- und Voiceinterfaces. |
| Generative AI UX | Gestaltung von Erlebnissen mit KI-generierten Inhalten. |
| Prompt Design | Strukturierung wirksamer Prompts für KI-Systeme. |
| AI in Research | Auswertung von Nutzerdaten mit KI. |
| Personalization with AI | Gestaltung adaptiver Nutzererlebnisse. |
| Human AI Interaction | Gestaltung der Interaktion zwischen Nutzern und KI. |
| Explainable AI | KI-Entscheidungen nachvollziehbar machen. |
| Ethical AI Design | Umgang mit Bias, Fairness und Vertrauen. |
| AI Prototyping | Schnellere Konzeptentwicklung mit KI. |
| AI Integration | Einbindung von KI in Produkte. |

## Tools

| Attribut | Beschreibung |
|---|---|
| Figma / FigJam | Auto-Layout, Komponenten, Varianten und Variablen. |
| Claude | KI-gestützte Konzeption, Analyse und Automatisierung von Designaufgaben. |
| ChatGPT | Ideation, Textarbeit und Recherche mit generativer KI. |
| Gemini | Multimodale Analyse und Ideation mit generativer KI. |
| Adobe CC | Photoshop, Illustrator und After Effects. |
| Fullstory | Session Replays und Click Paths auswerten. |
| Dovetail | Research zentral dokumentieren, clustern und teilen. |
| Google Analytics | Nutzungsdaten und Conversion Funnels auswerten. |
| Hotjar | Heatmaps und Nutzeraufzeichnungen auswerten. |
| Git | Versionierung und Zusammenarbeit im Repository. |
| UXPin | Interaktive Prototypen mit echten Frontendkomponenten bauen. |

## Coding Skills

| Attribut | Beschreibung |
|---|---|
| HTML / CSS | Umsetzung funktionaler Prototypen und Brücke zur Entwicklung. |
| JavaScript | Interaktive Funktionalität im Frontend umsetzen. |
| TypeScript | Typsichere Frontendentwicklung in größeren Codebasen. |
| React | Komponentenbasierte Oberflächen entwickeln. |
| Angular | Komponentenbasierte Anwendungen im Enterpriseumfeld. |
| Vue.js | Komponentenbasierte Oberflächen mit Vue entwickeln. |
| Next.js | Serverseitig gerenderte React Anwendungen aufsetzen. |
| Tailwind CSS | Utility First Styling für schnelle Umsetzung. |
| SQL | Datenabfragen für Analysen und Prototypen schreiben. |
| Python | Skripte für Datenaufbereitung und Automatisierung. |

---

## Neue Attribute formulieren

Wenn der Eingang etwas belegt, das im Katalog fehlt (eine Branche, ein Tool,
eine Spezialitaet), wird ein neues Attribut im Katalogstil angelegt:

- **Name**: englisch, kurz, wie ein Fachbegriff — kein Satz, **kein
  Bindestrich**. Produktnamen in der Eigenschreibung des Herstellers.
- **Beschreibung**: deutsch, eine Zeile, hoechstens etwa 90 Zeichen. Sachlich
  beschreiben, was die Person damit tut — kein „exzellent", „langjaehrig",
  „leidenschaftlich". Die Bewertung machen die Punkte, nicht das Adjektiv.
  Punkt am Ende.
- **Pruefen, ob es das schon gibt.** „UX Research" und „Qualitative Research"
  nebeneinander auf einer Matrix sagen zweimal dasselbe.

Beispiele fuer den Ton: „Strukturierung komplexer Informationen." /
„Produkte mit echten Nutzern testen." / „Photoshop, Illustrator und After Effects."

**Ein neues Attribut gehoert in den Figma-Pool**, nicht nur in diese Datei.
Sonst faellt es beim naechsten Lauf wieder heraus.
