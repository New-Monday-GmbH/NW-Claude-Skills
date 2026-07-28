# Strategische Ebene: Conversion & Content

Diese Ebene liegt **über** den fünf technischen Brillen (`audit-frameworks.md`). Sie ist bewusst **weniger technisch** und beantwortet die Fragen, die Entscheider:innen wirklich interessieren: *Bringt die Seite Besucher:innen zur gewünschten Handlung? Und sagt der Text das Richtige – überzeugend?*

Formuliere Findings hier geschäftlich, nicht technisch. Statt „H2 hat 4,2:1 Kontrast" → „Der zentrale Nutzen geht optisch unter und wird überlesen". Immer: **Beobachtung → Wirkung aufs Geschäft → Empfehlung**. Belege mit Screenshots und den Daten aus `survey.json` (`ctaLabels`, `headings`, `paragraphs`).

Diese Ebene erzeugt in der Präsentation den **strategischen Teil vor den Detail-Findings** – eine Management-taugliche Einschätzung.

---

## A. Conversion – bringt die Seite zur Handlung?

Bewerte entlang des Wegs, den ein:e Besucher:in nimmt. Pro Punkt: funktioniert es, wo bricht es, was ist der Hebel?

- **Above-the-fold-Klarheit (5-Sekunden-Test):** Ist in 5 Sekunden klar, *was* das Angebot ist, *für wen* und *was man tun soll*? Value Proposition + primärer CTA sofort sichtbar?
- **Ein klares Handlungsversprechen:** Gibt es einen dominanten primären CTA – oder konkurrieren viele gleichwertige Buttons? Ist die CTA-Sprache handlungs- und nutzenorientiert („4 Wochen kostenlos testen") statt generisch („Absenden", „Mehr")? Prüfe `ctaLabels` auf Konsistenz und Klarheit.
- **Reibung & Aufwand:** Wie viele Schritte/Hürden bis zur Conversion? Formularlänge, Pflichtfelder, Registrierungszwang, unklare nächste Schritte. Jede unnötige Hürde kostet Abschlüsse.
- **Vertrauen (Trust):** Social Proof (Testimonials mit Namen/Firma/Foto), Logos, Zahlen, Zertifikate/Siegel, Garantien, Sicherheit/DSGVO. Ist Vertrauen *dort*, wo entschieden wird (nahe am CTA)?
- **Einwände entkräften:** Werden typische Kaufbedenken adressiert (Preis, Aufwand, Wechsel, Datensicherheit, „passt das zu mir?")? FAQ, Vergleiche, „So einfach ist der Umstieg".
- **Preis-Transparenz:** Ist der Weg zum Preis klar? Versteckte Preise erhöhen Absprünge. Gibt es eine erlebbare Preis-/Paketseite?
- **Konsistenz der Conversion-Pfade:** Führen Haupt-CTAs zum selben, klaren Ziel (Trial vs. Demo)? Zwei konkurrierende Primärziele verwässern.
- **Dringlichkeit/Relevanz ohne Druck:** Gibt es einen Grund, *jetzt* zu handeln (kostenlos testen, sofort startklar)?

**Conversion-Hebel formulieren:** 3–6 konkrete, priorisierte Hebel mit erwarteter Richtung der Wirkung – **ohne erfundene Prozentzahlen**. Formuliere als „Hebel → warum → Maßnahme".

---

## B. Content & Copy – performt der Text inhaltlich?

Bewerte Überschriften und Fließtexte inhaltlich, nicht nur gestalterisch. Nutze `headings` und `paragraphs` aus `survey.json` plus die Screenshots.

- **Nutzen statt Funktion (Benefit vs. Feature):** Sprechen Überschriften den *Nutzen* für die Zielgruppe an („Endlich alles an einem Ort") oder listen sie nur Funktionen? Die stärksten Headlines übersetzen Features in Ergebnisse (Zeit sparen, Überblick, weniger Tools). **Dieses Muster ist einer der häufigsten Befunde überhaupt: Seiten zeigen nur Features statt echter Lösungen.** Prüfe es deshalb **immer und pro Kernseite** explizit: Wird ein konkretes Problem der Zielgruppe benannt und die Lösung dafür erzählt (Problem → Lösung → Ergebnis) – oder muss der Besucher aus einer Funktionsliste selbst ableiten, was ihm das bringt? Wenn Letzteres: als eigenes Finding mit Beispiel-Headline festhalten.
- **Klarheit vor Cleverness:** Ist sofort verständlich, was gemeint ist? Vermeidet die Copy Buzzwords, leere Superlative und Jargon? „AI-gestützt" nur, wenn der konkrete Nutzen mitgeliefert wird.
- **Messaging-Hierarchie:** Baut die Seite eine Argumentation auf (Problem → Lösung → Beweis → Handlung)? Oder ist es eine flache Feature-Liste? Trägt jede Sektion eine klare Kernaussage?
- **Zielgruppen-Fit & Ansprache:** Passt Ton und Sprache zur Zielgruppe (hier: Dienstleister, KMU, Agenturen)? Konsequente, passende Anrede (Du/Sie)? Spricht die Copy deren konkrete Schmerzpunkte an?
- **Konkretheit & Beweis:** Werden Behauptungen belegt (Zahlen, Beispiele, Testimonials) statt nur behauptet? Konkrete Aussagen schlagen vage Versprechen.
- **Scanbarkeit:** Lässt sich die Seite überfliegen? Aussagekräftige Zwischenüberschriften (tragen sie die Botschaft auch allein?), kurze Absätze, sinnvolle Hervorhebungen.
- **Konsistenz der Botschaft:** Erzählt die Seite (und die Unterseiten) eine stimmige Geschichte, oder widersprechen sich Claims/Begriffe? Ist die zentrale Value Proposition überall wiedererkennbar?
- **Leere/Platzhalter-Wirkung:** Wirken Überschriften abgeschnitten, generisch oder wie Platzhalter? (Vgl. auch leere Headings in der WCAG-Brille.)

**Copy-Check formulieren:** Pro Kernseite ein kurzes Urteil „Was sitzt / Was schwächt" plus 2–3 konkrete Umformulierungs-Ansätze (gerne mit Beispiel-Headline). Keine Vollredaktion – die stärksten Hebel.

---

## C. Site-weite Betrachtung (mehrere Seiten)

Die strategische Ebene lebt vom Zusammenspiel der Seiten. Prüfe über die per `crawl` gefundenen Kernseiten hinweg:

- **Funnel-Logik:** Führt der Weg Startseite → Feature/Produkt → Preise → Trial/Demo schlüssig und ohne Sackgassen? Wo verliert der Funnel Menschen?
- **Konsistenz:** Value Proposition, CTA-Sprache, Ton, Preis-Botschaft und Design über die Seiten hinweg stimmig?
- **Seiten-Rollen:** Erfüllt jede Kernseite ihre Aufgabe (Startseite = überzeugen & leiten, Feature = Nutzen vertiefen, Preise = Entscheidung ermöglichen, Kontakt/Demo = Reibung minimieren)?
- **Lücken:** Fehlt eine Seite, die die Zielgruppe zur Entscheidung braucht (z. B. transparente Preise, Referenzen/Case Studies, Sicherheit/DSGVO im Detail)?

Wähle die zu prüfenden Seiten nach Conversion-Relevanz: **Startseite, Preise, zentrale Produkt-/Feature-Seite, Kontakt/Demo-Flow** – plus alles, was offensichtlich im Kaufpfad liegt. Frage den Nutzer, wenn die Prioritäten unklar sind.
