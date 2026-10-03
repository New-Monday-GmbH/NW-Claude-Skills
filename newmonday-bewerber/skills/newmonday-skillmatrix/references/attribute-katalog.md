# Attribut-Katalog — Skills, Kategorien und Standardbeschreibungen

Der Katalog spiegelt **1:1 den Figma-Frame `Skill Matrix Pool Refactored`** in
der Datei `Portfolio - CV Master` (Section „SKill Matrix Pool"). Er ist der
**Wortschatz** der Skillmatrix: Steht ein Attribut hier, werden Name,
Beschreibung und Kategorie **woertlich** uebernommen — so tragen alle Matrizen
fuer denselben Skill denselben Text am selben Ort, und die Dokumente bleiben
ueber Kandidaten hinweg vergleichbar. Nur was hier fehlt, wird neu formuliert,
im selben Stil (Muster am Ende).

**Der Pool ist die Quelle, diese Datei die Kopie.** Bei Abweichung gewinnt
Figma. Erzeugt wird sie mit `scripts/katalog_aus_pool.py` — nicht von Hand
nachgepflegt. Einzige Zutat des Skills ist die Spalte „deutsch“: Sie steht im
Skript (`DEUTSCH`, `GRENZFAELLE`), nicht im Pool.

## Die harten Regeln

- **Ab drei Punkten, sonst gar nicht.** Ein Skill kommt nur in die Matrix, wenn
  die Bewertung **mindestens 3** ergibt. Alles darunter wird **nicht
  angezeigt** — nicht abgewertet, nicht in Klammern, nicht kleiner gesetzt:
  weggelassen. Eine Skillmatrix ist ein Verkaufsdokument; was schwach belegt
  ist, gehoert nicht hinein.
- **Hoechstens 24 Kernkompetenzen.** Die Sektion traegt hoechstens **sechs
  Skills je Kategorie**, gesetzt als **drei Karten pro Reihe, zwei Reihen**,
  und hoechstens **fuenf Kategorien**, ueblich sind drei bis vier.
- **`Tools` ist eine eigene Sektion**, keine Kategorie. Sie bekommt eine eigene
  Ueberschrift mit Tools-Icon wie „Kernkompetenzen" und steht **danach**; ein
  Kategorielabel innerhalb der Sektion entfaellt. Sie traegt hoechstens sechs
  Tools, die der Eingang nennt, und zaehlt nicht gegen die 24. Nennt der
  Eingang keine, fragt der Skill in der Freigabe, ob rollentypische Tools
  ergaenzt werden sollen. Ein Tool steht nur dort und nicht noch einmal
  als Skill in den Kernkompetenzen. `Coding Skills` ist dagegen eine
  gewoehnliche Kategorie innerhalb der Kernkompetenzen.
- **Namen: Fachbegriffe englisch, Uebersetzungen deutsch.** Kategorienamen
  sind immer englisch. Ein Attributname bleibt in einer deutschen Matrix nur
  englisch, wenn er ein eingefuehrter Fachbegriff ist, den man im deutschen
  UX-Alltag so sagt (Wireframing & Prototyping, Design Systems, Information
  Architecture, Journey Mapping, alle KI-Begriffe wie AI Prototyping). Ist der
  englische Name nur eine Uebersetzung,
  traegt die deutsche Matrix die Form aus der Spalte „deutsch“ („Frontend
  Understanding“ → „Frontend-Verständnis“). Leer heisst: bleibt englisch.
  *Grenzfall* heisst: bleibt englisch, die deutsche Alternative steht daneben.
  Eine englische Matrix traegt immer die englischen Namen. Beschreibungen sind
  deutsch; fuer eine englische Matrix wird beim Bauen uebersetzt und in der
  Uebergabe gemeldet.
- **Keine Bindestriche in englischen Attributnamen.** „Microinteractions",
  nicht „Micro-interactions"; „Data Driven Design", nicht „Data-Driven Design".
  Deutsche Formen folgen der deutschen Rechtschreibung und koppeln englische
  Teile mit Bindestrich („Pain-Point-Analyse“).
- **Produktnamen so, wie der Hersteller sie schreibt.** Belegbare
  Eigenschreibung schlaegt jede Zuruf-Variante — „Fullstory", nicht
  „FullStory"; „Hotjar", nicht „HotJar"; „UXPin", nicht „UxPin". Im Zweifel
  auf der Herstellerseite nachsehen und die Abweichung in der Uebergabe
  nennen, statt sie stillschweigend zu uebernehmen.
- **Jeder Name kommt genau einmal vor**, ueber alle Kategorien hinweg.
- **Ein Attribut steht in seiner Kategorie.** In der Matrix steht jedes
  Attribut unter der Kategorie, unter der es hier gefuehrt wird, wenn die in
  der Matrix vorkommt — auch wenn eine alte Matrix des Kandidaten es anderswo
  einsortiert hatte. Fehlt sie, steht es in der inhaltlich naechsten Kategorie
  der Matrix (Tabelle `VERWANDT` in `scripts/render_skillmatrix.py`), nie in
  einer fachfremden. Das Renderskript meldet beides.

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

Eine Matrix nimmt **drei bis vier** Kategorien als Kernkompetenzen, hoechstens fuenf — die, die das Profil belegt, eine KI-Kategorie zuerst, danach die staerkste — und dazu optional `Tools`.

---

## UX Strategy & Product Discovery

| Attribut | deutsch | Beschreibung |
|---|---|---|
| User Centered Design | *Grenzfall, bleibt englisch (dt. „Nutzerzentriertes Design“)* | Lösungen basierend auf echten Nutzerbedürfnissen und -verhalten erstellen. |
| End to End UX Design |  | Komplette Nutzererlebnisse von der Idee bis zur Auslieferung gestalten. |
| Product Discovery |  | Probleme identifizieren und die richtige Produktstrategie festlegen. |
| UX Strategy | UX-Strategie | Langfristige UX-Vision und Prinzipien definieren. |
| Experience Vision | *Grenzfall, bleibt englisch (dt. „Zielbild für das Nutzererlebnis“)* | Einen klaren Zielzustand für zukünftige Nutzererlebnisse schaffen. |
| UX Principles & Guidelines | UX-Prinzipien & Guidelines | Regeln für konsistente Designentscheidungen festlegen. |
| Business to UX Translation | *Grenzfall, bleibt englisch (dt. „Anforderungen in UX übersetzen“)* | Geschäftliche Anforderungen in nutzerorientierte Lösungen umsetzen. |
| Product Thinking |  | Ergebnisorientierte, nutzerzentrierte Produkte entwickeln. |
| UX Roadmapping |  | UX-Initiativen über die Zeit planen. |

## User Research & Insights

| Attribut | deutsch | Beschreibung |
|---|---|---|
| UX Research |  | Planung und Durchführung qualitativer und quantitativer Studien. |
| Qualitative Research |  | Tiefgehende Erkenntnisse durch Interviews und Beobachtungen gewinnen. |
| Quantitative Research |  | Analyse des Nutzerverhaltens durch Daten und Umfragen. |
| Data Driven Design | *Grenzfall, bleibt englisch (dt. „Datengetriebenes Design“)* | Designentscheidungen auf Basis von Nutzungsdaten und Tests treffen. |
| User Interviews & Testing |  | Moderierte und unmoderierte Sitzungen durchführen. |
| Stakeholder Interviews |  | Geschäftsperspektiven und Einschränkungen verstehen. |
| Persona Creation | Persona-Erstellung | Modellierung wichtiger Nutzergruppen. |
| Jobs to be Done |  | Verstehen der Nutzermotivationen und Ziele. |
| Journey Mapping |  | Visualisierung der Nutzerreise von Anfang bis Ende. |
| Pain Point Analysis | Pain-Point-Analyse | Identifikation von Nutzerproblemen und Chancen. |
| Competitive Analysis | Wettbewerbsanalyse | Bewertung von Markt- und Wettbewerberlösungen. |
| Behavioral Analysis | Verhaltensanalyse | Interpretation realer Nutzungsdaten. |
| Research Synthesis | Research-Synthese | Daten in umsetzbare Empfehlungen umwandeln. |

## Interaction & Visual Design

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Interaction Design |  | Gestaltung der Nutzerinteraktion mit Produkten. |
| Information Architecture |  | Komplexe Informationen klar strukturieren. |
| User Flows |  | Nutzerreisen Schritt für Schritt abbilden. |
| Wireframing & Prototyping |  | Von Low Fidelity Wireframes bis zu interaktiven High Fidelity Prototypen. |
| Microinteractions | *Grenzfall, bleibt englisch (dt. „Mikrointeraktionen“)* | Gestaltung kleiner interaktiver Details. |
| Responsive Web Design |  | Benutzerfreundlichkeit auf allen Geräten sicherstellen. |
| Mobile First Design |  | Design für mobile Geräte als Hauptplattform. |
| Conversion Optimization | Conversion-Optimierung | Nutzerwege verbessern, um Ergebnisse zu steigern. |
| UX Writing |  | Klare und hilfreiche Interfacetexte verfassen. |
| Emotional Design |  | Emotionale Ansprache der Zielgruppe. |
| Ideation |  | Erste Ansätze zur Erstellung oder Überarbeitung von Anwendungen. |

## UI Design & Visual Systems

| Attribut | deutsch | Beschreibung |
|---|---|---|
| UI Design |  | Gestaltung von User Interfaces für digitale Produkte. |
| Scalable UI Concepts | Skalierbare UI-Konzepte | Wiederverwendbare und anpassbare UI-Patterns erstellen. |
| Design Guide |  | Layouts, Farben und Typografie festlegen. |
| Consistent Interfaces | Konsistente Interfaces | Visuelle und funktionale Konsistenz sicherstellen. |
| Component Based Design | Komponentenbasiertes Design | Gestaltung modularer UI-Elemente. |
| UI & Pattern Libraries |  | Aufbau wiederverwendbarer Designkomponenten. |
| Figma Component Systems | Figma-Komponentensysteme | Pflege von Komponenten, Varianten und Variablen. |
| UI Quality Assurance | UI-Qualitätssicherung | Prüfung und Verbesserung der visuellen Qualität. |

## Design Systems & Scaling

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Design Systems |  | Aufbau skalierbarer und barrierefreier Komponentenbibliotheken. |
| Design Tokens |  | Pflege zentraler Designvariablen wie Farben und Spacing. |
| Product Systemization | *Grenzfall, bleibt englisch (dt. „Systematisierung im Produkt“)* | Standardisierung von Designpatterns im Produkt. |
| Component Standards | Komponentenstandards | Festlegung wiederverwendbarer UI-Bausteine. |
| Design Governance |  | Sicherung der Konsistenz über Teams hinweg. |
| Documentation | Dokumentation | Erstellung klarer Designrichtlinien. |
| Cross Platform Consistency | Plattformübergreifende Konsistenz | Einheitliche Erlebnisse über Plattformen hinweg sicherstellen. |
| UX/UI Scaling | UX/UI-Skalierung | Ausweitung des Designs auf große Ökosysteme. |

## Usability Testing & Evaluation

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Usability Testing |  | Produkte mit echten Nutzern testen. |
| Remote Testing |  | Tests online durchführen. |
| Test Planning | Testplanung | Usabilitystudien strukturiert aufsetzen. |
| Test Moderation | Testmoderation | Nutzer durch Testsitzungen führen. |
| Prototype Validation | Prototyp-Validierung | Konzepte vor der Entwicklung testen. |
| Heuristic Evaluation | Heuristische Evaluation | UX anhand von Best Practices prüfen. |
| UX Audits |  | Gesamtqualität des Nutzererlebnisses bewerten. |
| Accessibility Audits |  | Einhaltung von Accessibilitystandards prüfen. |
| A/B Testing |  | Designvarianten vergleichen. |
| Insight Reporting | *Grenzfall, bleibt englisch (dt. „Aufbereitung von Testergebnissen“)* | Testergebnisse als umsetzbare Empfehlungen aufbereiten. |

## Accessibility & Inclusive Design

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Accessible Design | *Grenzfall, bleibt englisch (dt. „Barrierefreies Design“)* | Gestaltung für Nutzer mit Behinderungen. |
| Inclusive Design |  | Gestaltung für vielfältige Nutzergruppen. |
| Regulatory Compliance | Regulatorische Anforderungen | Erfüllung gesetzlicher Barrierefreiheitsanforderungen. |

## Agile Product Delivery

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Agile UX Collaboration | Zusammenarbeit in agilen Teams | Zusammenarbeit in agilen Produktteams. |
| Scrum / Kanban |  | Anwendung agiler Frameworks. |
| Design Sprints |  | Workshops zur schnellen Lösungsfindung. |
| Backlog Refinement |  | Schärfen von Produktanforderungen im Backlog. |
| Sprint Support | Sprint-Begleitung | Begleitung der Entwicklungszyklen. |
| MVP Delivery | *Grenzfall, bleibt englisch (dt. „MVP-Entwicklung“)* | Launch früher Produktversionen. |
| Iterative Improvement | Iterative Verbesserung | Laufende Optimierung von Produkten. |

## Stakeholder Management & Facilitation

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Stakeholder Management |  | Abstimmung von Business und Produktteams. |
| Workshop Facilitation |  | Leitung gemeinsamer Arbeitssessions. |
| Teamlead | *Grenzfall, bleibt englisch (dt. „Teamleitung“)* | Aufbau und Führung von Designteams. |
| Design Presentation | Designpräsentation | Klare Vermittlung von Designideen. |
| Decision Facilitation | *Grenzfall, bleibt englisch (dt. „Entscheidungen begleiten“)* | Begleitung von Produktentscheidungen. |
| Cross Team Alignment | Teamübergreifende Abstimmung | Verbindung von UX, Business und Tech. |
| Conflict Resolution | Konfliktlösung | Auflösung von Differenzen zwischen Stakeholdern. |
| Consulting | *Grenzfall, bleibt englisch (dt. „Beratung“)* | Beratung von Teams und Kunden. |

## Development Collaboration

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Dev Collaboration | Zusammenarbeit mit Entwicklern | Enge Zusammenarbeit mit Entwicklern. |
| Design Handoff |  | Aufbereitung von Designs für die Entwicklung. |
| UX Specifications | UX-Spezifikationen | Erstellung umsetzungsreifer Dokumentation. |
| Frontend Understanding | Frontend-Verständnis | Kenntnis technischer Rahmenbedingungen. |
| Design QA |  | Sicherstellung der korrekten Umsetzung. |
| Feasibility Assessment | Machbarkeitsprüfung | Einschätzung der technischen Machbarkeit. |
| Design to Code |  | Überführung von Designs in produktiven Code. |

## AI & Emerging Tech

| Attribut | deutsch | Beschreibung |
|---|---|---|
| AI Powered UX |  | Gestaltung KI-getriebener Nutzererlebnisse. |
| Conversational Design |  | Gestaltung von Chat- und Voiceinterfaces. |
| Generative AI UX |  | Gestaltung von Erlebnissen mit KI-generierten Inhalten. |
| Prompt Design |  | Strukturierung wirksamer Prompts für KI-Systeme. |
| AI in Research |  | Auswertung von Nutzerdaten mit KI. |
| Personalization with AI |  | Gestaltung adaptiver Nutzererlebnisse. |
| Human AI Interaction |  | Gestaltung der Interaktion zwischen Nutzern und KI. |
| Explainable AI |  | KI-Entscheidungen nachvollziehbar machen. |
| Ethical AI Design |  | Umgang mit Bias, Fairness und Vertrauen. |
| AI Prototyping |  | Schnellere Konzeptentwicklung mit KI. |
| AI Integration |  | Einbindung von KI in Produkte. |

## Tools

| Attribut | deutsch | Beschreibung |
|---|---|---|
| Figma / FigJam |  | Auto-Layout, Komponenten, Varianten und Variablen. |
| Claude |  | KI-gestützte Konzeption, Analyse und Automatisierung von Designaufgaben. |
| ChatGPT |  | Ideation, Textarbeit und Recherche mit generativer KI. |
| Gemini |  | Multimodale Analyse und Ideation mit generativer KI. |
| Adobe CC |  | Photoshop, Illustrator und After Effects. |
| Fullstory |  | Session Replays und Click Paths auswerten. |
| Dovetail |  | Research zentral dokumentieren, clustern und teilen. |
| Google Analytics |  | Nutzungsdaten und Conversion Funnels auswerten. |
| Hotjar |  | Heatmaps und Nutzeraufzeichnungen auswerten. |
| Git |  | Versionierung und Zusammenarbeit im Repository. |
| UXPin |  | Interaktive Prototypen mit echten Frontendkomponenten bauen. |

## Coding Skills

| Attribut | deutsch | Beschreibung |
|---|---|---|
| HTML / CSS |  | Umsetzung funktionaler Prototypen und Brücke zur Entwicklung. |
| JavaScript |  | Interaktive Funktionalität im Frontend umsetzen. |
| TypeScript |  | Typsichere Frontendentwicklung in größeren Codebasen. |
| React |  | Komponentenbasierte Oberflächen entwickeln. |
| Angular |  | Komponentenbasierte Anwendungen im Enterpriseumfeld. |
| Vue.js |  | Komponentenbasierte Oberflächen mit Vue entwickeln. |
| Next.js |  | Serverseitig gerenderte React Anwendungen aufsetzen. |
| Tailwind CSS |  | Utility First Styling für schnelle Umsetzung. |
| SQL |  | Datenabfragen für Analysen und Prototypen schreiben. |
| Python |  | Skripte für Datenaufbereitung und Automatisierung. |

---

## Neue Attribute formulieren

Wenn der Eingang etwas belegt, das im Katalog fehlt (eine Branche, ein Tool,
eine Spezialitaet), wird ein neues Attribut im Katalogstil angelegt:

- **Name**: englisch, kurz, wie ein Fachbegriff — kein Satz, **kein
  Bindestrich**. Produktnamen in der Eigenschreibung des Herstellers. Ist der
  englische Name kein eingefuehrter Fachbegriff, bekommt er dazu eine deutsche
  Form fuer deutsche Matrizen (`DEUTSCH` in `scripts/katalog_aus_pool.py`).
- **Kategorie**: die Katalog-Kategorie, zu der es inhaltlich gehoert — keine
  neue.
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
