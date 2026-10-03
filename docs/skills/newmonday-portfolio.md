# newmonday-portfolio

Macht aus den Unterlagen eines Kandidaten ein Portfolio im New-Monday-Layout.

Zurück zu [Start](../Start.md).

## Wofür

Für die Arbeitsproben eines Kandidaten als 16:9-Folien: Cover, Profil,
Kundenwand, Statement, Design-Prozess, KI-Einsatz, Agenturseite,
Projektstrecken und Kontakt. Je nach Zahl der Projekte 23 bis 39 Folien.

## Eingang

- Portfolio als PDF oder Link zur Website
- Lebenslauf als PDF – auch wegen des Profilfotos
- LinkedIn-Export als PDF
- je Projekt drei bis acht einzelne Screenshots, ein Screen je Datei
- optional: Kundenlogos als SVG, ein Foto der Firmenzentrale je Kunde, ein
  paar Sätze zu jedem Kunden, ein Figma-Link

Widersprechen sich die Quellen, gilt Portfolio vor Lebenslauf vor LinkedIn.

## Ausgang

- das Portfolio als PDF
- dieselben Folien als bearbeitbare Frames in Figma

Gefragt wird nicht, ob etwas nach Figma soll, sondern nur wohin.

## So startest du ihn

In Claude Code die Unterlagen dazulegen und etwa „Bring das Portfolio ins
New-Monday-Layout“ schreiben. Der Skill fragt nach Sprache und Figma-Ziel und
bittet um das Material.

## Die eine Regel

**Inhalte werden übernommen, nicht umgeschrieben.** Fünf Stellen sind
ausgenommen und stehen immer in der Übergabe:

- der Text der KI-Folie, wenn im Material nichts dazu steht
- der Cover-Titel, abgeleitet aus der Rolle
- die Übersetzung, nur auf ausdrückliche Ansage
- die Kundenbeschreibung, nur aus belegten Quellen und mit Quellenangabe
- die Prozesstexte, wenn das Material keinen fertigen Prozess liefert

Das Statement auf Seite 4 wird erfragt, nicht geschrieben.

## Stolpersteine

- **Screens sind der Engpass.** Einzelne saubere Exporte sind am besten:
  Desktop ab 1 120 px Breite, Phone ab 520 px. Aus einem PDF geschnittene
  Mosaike taugen nicht.
- **Fehlende Bilder halten nichts auf.** Der Skill setzt beschriftete
  Platzhalter. Kommen die Bilder nach, wird nur neu gerendert.
- **NDA-Projekte:** Originalscreens dürfen nicht gezeigt werden, der Kandidat
  muss eine abgewandelte Darstellung liefern.
- **Kundentexte recherchiert der Skill selbst,** wenn der Kandidat keine
  liefert. Die Quellen stehen in der Übergabe.
- **Gebäudefotos können KI-generiert sein.** Die Übergabe nennt sie und bittet
  um Freigabe oder ein echtes Foto.
- **Markenfarben der Projekte** schlägt der Skill vor und bittet um einen
  Blick.
- **Unter drei Projekten wird es dünn, über fünf zum Katalog.** Dann schlägt
  der Skill die stärksten fünf vor.

## Was feststeht

- Die Seitenfolge und die statischen Seiten (Divider, Agenturseite, Kontakt).
- Ein Projektblock hat drei bis fünf Seiten.
- Das Profilfoto steht immer in Graustufen.
- Keine Schatten auf den Folien.
- Die Anordnung der Screens entscheidet der Skill, nicht das Material.

## Weiterlesen

- [SKILL.md](../../newmonday-bewerber/skills/newmonday-portfolio/SKILL.md) – die vollständigen Regeln
- [INSTALL.md](../../newmonday-bewerber/skills/newmonday-portfolio/INSTALL.md) – Einrichtung
- [layout.md](../../newmonday-bewerber/skills/newmonday-portfolio/references/layout.md) – vor jeder Layoutänderung lesen
- [figma.md](../../newmonday-bewerber/skills/newmonday-portfolio/references/figma.md) – der Weg nach Figma
