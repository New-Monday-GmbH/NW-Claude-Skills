# Zuordnung · Matching-Vokabular → Attribut-Katalog

Das Profilmatching (`newmonday-matching`) beschreibt Anfragen im Vokabular des
CRM (`newmonday-matching/references/vokabular.md`), die Skill Matrix spricht
die Sprache ihres Katalogs (`attribute-katalog.md`, die Kopie des Figma-Pools).
Diese Tabelle übersetzt das eine ins andere – damit eine Anfrage mit „Muss:
Barrierefreie Frontend-Entwicklung“ die richtige Kategorie nach vorn holt.

Zurück zu [SKILL.md](../SKILL.md) · [Attribut-Katalog](attribute-katalog.md)

## Was diese Tabelle ist und was nicht

- **Eine Übersetzung, kein Teil des Katalogs.** Die beiden Wortschätze bleiben
  getrennt: Der Katalog wird nur aus dem Figma-Pool erzeugt
  (`scripts/katalog_aus_pool.py`), das Vokabular nur über die CRM-Werteliste
  gepflegt. **Bei Abweichung gewinnt Figma** – steht ein Katalogname hier anders
  als im Katalog, gilt der Katalog, und diese Datei wird nachgezogen.
- **Gewichtung, nie Beleg.** Eine Zuordnung sagt nur, welche Kategorie ein
  Kriterium der Anfrage trifft. Ob das Attribut in die Matrix kommt,
  entscheidet allein der Beleg im Eingang (SKILL.md, „Die eine Regel“). Ein
  Muss-Kriterium ohne Beleg kommt in die Freigabe, nicht ins Dokument.
- **Art der Zuordnung:**
  - **gleich** – dasselbe Thema, das Katalog-Attribut ist gemeint.
  - **teilweise** – berührt das Attribut, deckt es aber nicht ab. Ordnet die
    Kategorie, das Attribut braucht trotzdem seinen eigenen Beleg.
  - **kein Gegenstück** – ordnet nichts. Belegt der Eingang den Wert, kann er
    nach „Neue Attribute formulieren“ im Katalog neu angelegt werden.
  - **Vorsicht** – gleiches Wort, anderes Thema (Scheintreffer). Zählt nicht,
    außer der Eingang belegt genau das Katalog-Thema.

## Fachdomänen

Die 15 Fachdomänen des Vokabulars sind **keine Katalog-Attribute**. Eine Domäne
ist belegt, wenn der Kandidat in ihr gearbeitet hat – nicht, wenn ein Kunde aus
ihr im Lebenslauf steht. Belegt, darf sie Hero-Beschreibung und Schwerpunkte
mitbestimmen oder als neues Attribut angelegt werden; unbelegt kommt sie nach
`anfrage_luecken` mit `art: domaene`.

## Skills

Aus den Blöcken, die im Vokabular stehen. Werte ohne UX-Bezug sind je Block in
einer Zeile zusammengefasst.

| Vokabular | Katalog-Attribut | Kategorie | Art |
|---|---|---|---|
| **Datenbanken und Daten** | | | |
| SQL | SQL | Coding Skills | gleich |
| Power BI · Tableau | – | – | kein Gegenstück (Tool, neu anlegen) |
| PL/SQL · T-SQL · Oracle Datenbank · PostgreSQL · MySQL / MariaDB · MS SQL Server · SQLWindows / Gupta / OpenText Team Developer · Datenmodellierung · ETL · Data Warehouse · SAS · Data Engineering · Datenmigration | – | – | kein Gegenstück |
| **SAP** | | | |
| SAP Fiori / UI5 | UI Design | UI Design & Visual Systems | teilweise – nur bei gestalteten Fiori-Oberflächen |
| ABAP · SAP S/4HANA · SAP FI/CO · SAP IS-U · SAP BW · SAP HCM · SAP MM/SD | – | – | kein Gegenstück |
| **Mainframe und Legacy** | | | |
| alle Werte | – | – | kein Gegenstück |
| **Backend und Architektur** | | | |
| REST-API · GraphQL · Schnittstellenentwicklung | Frontend Understanding | Development Collaboration | teilweise |
| Spring / Spring Boot · Node.js · PHP · Kotlin · Rust · Microservices · Kafka / Message Queues · Softwarearchitektur · Domain Driven Design | – | – | kein Gegenstück |
| **Frontend** | | | |
| HTML / CSS | HTML / CSS | Coding Skills | gleich |
| SCSS / Tailwind | Tailwind CSS | Coding Skills | teilweise – nur Tailwind |
| Next.js | Next.js | Coding Skills | gleich |
| Svelte | – | Coding Skills | kein Gegenstück (neu anlegen) |
| Web Components | Component Based Design | UI Design & Visual Systems | teilweise |
| Storybook | UI & Pattern Libraries | UI Design & Visual Systems | teilweise |
| Barrierefreie Frontend-Entwicklung | Accessible Design | Accessibility & Inclusive Design | teilweise – Entwicklung, nicht Gestaltung |
| WebRTC | – | – | kein Gegenstück |
| Jest / Testing Library · Cypress / Playwright | – | – | Vorsicht – Softwaretest, kein Usability-Testing |
| **Cloud, DevOps, Infrastruktur** | | | |
| GitLab / GitHub Actions | Git | Tools | teilweise |
| Google Cloud · Docker · Terraform · CI/CD · Linux · Windows Server · Monitoring / Observability · Datenbankadministration | – | – | kein Gegenstück |
| **Security und Compliance** | | | |
| IT-Compliance · DSGVO / Datenschutz | Regulatory Compliance | Accessibility & Inclusive Design | Vorsicht – der Katalog meint Barrierefreiheitsrecht |
| IT-Sicherheit · ISO 27001 · BSI-Grundschutz · Penetrationstest · IAM / Berechtigungsmanagement · Notfallmanagement / BCM | – | – | kein Gegenstück |
| **Methoden und Rollen** | | | |
| Kanban | Scrum / Kanban | Agile Product Delivery | gleich |
| Scrum Master | Scrum / Kanban | Agile Product Delivery | teilweise – die Rolle ist mehr als die Methode |
| SAFe | Agile UX Collaboration | Agile Product Delivery | teilweise |
| Product Owner | Backlog Refinement · Product Thinking | Agile Product Delivery · UX Strategy & Product Discovery | teilweise |
| Anforderungsmanagement | Business to UX Translation · UX Specifications | UX Strategy & Product Discovery · Development Collaboration | teilweise |
| Business Analyse | Business to UX Translation | UX Strategy & Product Discovery | teilweise |
| Prozessmodellierung / BPMN | User Flows | Interaction & Visual Design | Vorsicht – Geschäftsprozesse sind keine Nutzerflüsse |
| Projektleitung | Stakeholder Management | Stakeholder Management & Facilitation | teilweise |
| Schulung / Wissenstransfer | Workshop Facilitation | Stakeholder Management & Facilitation | teilweise |
| Technische Dokumentation | Documentation · UX Specifications | Design Systems & Scaling · Development Collaboration | teilweise |
| Aufwandsschätzung | Feasibility Assessment | Development Collaboration | teilweise |
| Testmanagement · Testkonzeption | Test Planning | Usability Testing & Evaluation | Vorsicht – nur, wenn Usability-Tests gemeint sind |
| Agile Coaching · ITIL · Change Management · Produktionssupport / 2nd Level | – | – | kein Gegenstück |
| **Fachliche Kenntnisse** | | | |
| Regulatorik / Meldewesen | Regulatory Compliance | Accessibility & Inclusive Design | Vorsicht – Bankenaufsicht, nicht Barrierefreiheit |
| alle übrigen Werte | – | – | kein Gegenstück – Domänenwissen, siehe „Fachdomänen“ |

## Die 101 Grundwerte

Die ursprünglichen 101 Werte stehen nur in der Werteliste des CRM-Felds
*Skills*, nicht im Repo – darunter die meisten UX-Werte. Bis sie hier stehen,
gilt für sie:

- **Gleicher oder fast gleicher Name** wie ein Katalog-Attribut, auch als Teil
  eines Sammelnamens („Figma“ → `Figma / FigJam`): **gleich**.
- **Sonst:** in der Freigabe (2e) als „ohne Zuordnung“ nennen, mit der
  Kategorie, die der Skill für richtig hält – und die Zeile danach hier
  nachtragen, damit der nächste Lauf sie kennt.

## Pflege

Ändert sich das Vokabular (neue CRM-Werte) oder der Figma-Pool (neue
Attribute), wird diese Tabelle im selben Zug nachgezogen. Sie enthält nur
Begriffe, nie Kandidaten, Kunden oder Anfragen.
