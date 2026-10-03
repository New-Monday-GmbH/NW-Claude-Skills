# newmonday-skillmatrix

Baut aus Lebenslauf, LinkedIn-Export und Portfolio eine Skill Matrix im
New-Monday-Layout.

Zurück zu [Start](../Start.md).

## Wofür

Für die Kompetenzübersicht eines Kandidaten: eine einzige lange Seite mit Hero
(Name, Rolle, Verfügbarkeit, Foto), Zertifikaten, Kernkompetenzen nach
Kategorien mit 1–5 Punkten und Tools.

## Eingang

- Lebenslauf als PDF
- LinkedIn-Export als PDF und der Link zum Profil
- Portfolio als Link oder PDF
- optional: Zertifikate als Bild oder PDF, ein Foto in guter Auflösung

Gebaut wird mit dem, was kommt. Jede fehlende Quelle macht die Belegbasis
schmaler.

## Ausgang

- ein PDF mit einer langen Seite
- auf Wunsch ein bearbeitbarer Figma-Frame

Anders als beim Lebenslauf ist Figma hier eine Frage und kein fester Teil. Im
Gesamtlauf der [Bewerbermappe](newmonday-bewerbermappe.md) entsteht der Frame
immer, wenn Figma aktiv ist.

## So startest du ihn

In Claude Code die Unterlagen dazulegen und etwa „Skill Matrix für <Name>“
schreiben. Der Skill fragt nach Sprache, Verfügbarkeit und Figma.

## Die eine Regel

**Jedes Attribut in der Matrix braucht einen Beleg im Eingang** – eine
Station, ein Projekt, ein Tool, ein Kurs. Einzige Ausnahme: Nennt der Eingang
gar keine Tools, schlägt der Skill rollentypische vor und ergänzt sie nur nach
ausdrücklichem Ja.

Auswahl und Bewertung der Attribute sind Urteile. Deshalb werden beide vor dem
Rendern mit Beleg vorgelegt und erst nach Freigabe gebaut.

## Stolpersteine

- **Die Verfügbarkeit** steht als Badge ganz oben und kommt aus deiner
  Antwort, nicht aus dem Lebenslauf.
- **Eine Sprache im ganzen Dokument.** Attribut-, Kategorie- und Toolnamen
  bleiben als Fachbegriffe englisch, übersetzt wird, was ein Satz ist.
- **Der Katalog führt die Beschreibungen nur auf Deutsch.** Für eine englische
  Matrix wird jede Beschreibung beim Bauen übersetzt und das gemeldet.
- **Das LinkedIn-Foto ist für die große Fotokarte sichtbar weich.** Ein
  richtiges Foto lohnt sich.
- **Ohne Zertifikate** entfällt die Zertifikatssektion ersatzlos.
- **Figma braucht Bearbeitungsrechte** auf der Zieldatei, Leserechte reichen
  nicht.

## Was feststeht

- Reihenfolge: Hero, Zertifikate, Kernkompetenzen, Tools, Fuß. Zertifikate am
  Ende nur auf Wunsch.
- Bewertung mit fünf Punkten, keine Prozente, Balken oder Sterne.
- Die Hero-Beschreibung steht in der Ich-Perspektive.
- Keine anonymisierte Variante, Name und Foto gehören ins Dokument.
- Kein Inhalt aus der Vorlage bleibt stehen.

## Weiterlesen

- [SKILL.md](../../newmonday-bewerber/skills/newmonday-skillmatrix/SKILL.md) – die vollständigen Regeln
- [INSTALL.md](../../newmonday-bewerber/skills/newmonday-skillmatrix/INSTALL.md) – Einrichtung
- [attribute-katalog.md](../../newmonday-bewerber/skills/newmonday-skillmatrix/references/attribute-katalog.md) – alle Attribute mit Beschreibung
- [layout.md](../../newmonday-bewerber/skills/newmonday-skillmatrix/references/layout.md) – vor jeder Layoutänderung lesen
- [figma.md](../../newmonday-bewerber/skills/newmonday-skillmatrix/references/figma.md) und [figma-vorlage.md](../../newmonday-bewerber/skills/newmonday-skillmatrix/references/figma-vorlage.md) – der Weg nach Figma
