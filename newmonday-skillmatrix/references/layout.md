# Layout der Skillmatrix — Masse, Typo, Farben

Alle Werte sind aus dem Vorlagen-PDF `Skill Matrix Wissem` nachgemessen
(1440 × 3002pt, ein Figma-Frame als eine PDF-Seite). Gemessen wurde per
Pixelanalyse und ueber Cap-Hoehen der Glyphen; die Werte in `skillmatrix.css`
sind auf glatte Zahlen gerundet. Die Vorlagen `Skill Matrix Daniel` (inhaltlich
identisch, nur anderer Hero) und `Skillmatrix Florian Feiler` (Variante ohne
Bilderraster, Zertifikate am Ende) bestaetigen dieselben Tokens.

## Seitenformat

Die Matrix ist **eine einzige lange Seite**: 1440pt breit, Hoehe nach Inhalt.
Sie bildet eine Webseite ab, kein A4-Dokument — deshalb rendert
`render_skillmatrix.py` zweimal: erst auf Vorratshoehe (12000pt), dann wird die
letzte nicht weisse Pixelzeile gemessen und die Seitenhoehe exakt gesetzt
(plus 2pt Messreserve). Darum darf **niemals** `html` oder `body` einen
Hintergrund bekommen: unterhalb des Inhalts muss die Vorratsseite weiss
bleiben, sonst ist nichts mehr zu messen.

Der Inhaltscontainer ist 1232pt breit und zentriert (Raender je 104pt).
Kopfzeile und Fusszeile laufen ueber die volle Breite; das Logo der Kopfzeile
sitzt bei 44pt und damit **nicht** auf der Containerkante — so steht es in
der Vorlage.

## Farben

| Token | Wert | Verwendung |
|---|---|---|
| `--brand` | `#009193` | Kopf- und Fussbalken, Rollenzeile, Punkte, Zertifikatskante, Icons, Jahres-Badge-Text |
| `--schwarz` | `#111111` | Name, Kartentitel, Sektionsueberschriften |
| `--grau` | `#465469` | Hero-Beschreibung, Badge-Text |
| `--grau-2` | `#64748a` | Kartenbeschreibungen, Kategorien-Labels, Chips |
| `--flaeche` | `#f8f9fb` | Hintergrund des Rumpfs (alles zwischen Hero und Fuss) |
| `--linie` | `#e2e8ef` | Hairlines, leere Bewertungspunkte, Chip- und Badge-Rahmen |
| `--badge-bg` | `#f0f4f9` | Verfuegbarkeits-Badge |
| `--gruen` | `#21c45d` | Punkt im Verfuegbarkeits-Badge |
| `--jahr-bg` | `#e6f4f4` | Jahres-Badge auf der Zertifikatskarte |

Im Vorlagen-PDF misst der Teal `#009093` — das ist derselbe Markenton wie
`#009193` aus dem CV-Skill, nur durch den Farbraum des Exports verschoben.
Verwendet wird der Haus-Token `#009193`.

## Typografie

Schrift ist **Inter**, liegt in `assets/fonts/` und wird eingebettet — nicht
durch Systemschriften ersetzen. Gemessene Groessen (Cap-Hoehe / 0,727):

| Element | Groesse | Gewicht | Sonstiges |
|---|---|---|---|
| Name und Rolle im Hero | 60pt | 700 | Zeilenabstand 1,1, Laufweite −1,8pt; Rolle in `--brand` |
| Hero-Beschreibung | 20pt | 400 | `--grau`, max. 640pt breit, Zeilenabstand 1,55 |
| Schwerpunkt-Buttons | 20pt | 600 | 2pt Rahmen `--brand`, Radius 14pt, Padding 12/22pt |
| Verfuegbarkeits-Badge | 12pt | 600 | Versalien, Laufweite 1,2pt, `--grau` |
| Sektionsueberschriften | 24pt | 700 | Icon 26pt davor |
| Zertifikatstitel | 18pt | 700 | Jahres-Badge rechts: 13pt/600 |
| „Ausgestellt von:" | 14pt | 600 | |
| Zertifikatsbeschreibung | 14pt | 400 | `--grau-2` |
| Chips | 12pt | 400 | `--grau-2`, Rahmen `--linie`, Radius 8pt |
| Kategorien-Label | 14pt | 600 | Versalien, Laufweite 0,8pt, `--grau-2`, Hairline darunter |
| Skillkartentitel | 17pt | 700 | |
| Skillkartenbeschreibung | 14pt | 400 | `--grau-2`, Zeilenabstand 1,45 |
| Name auf der Fotokarte | 24pt | 700 | Weiss |
| Erfahrung auf der Fotokarte | 15pt | 400 | Weiss |
| Fussfrage | 28pt | 700 | Weiss |

## Bausteine

- **Kopfzeile**: Teal-Balken 88pt hoch, weisse Wortmarke 166pt breit
  (`nm-logo-weiss.svg` — die eingefaerbte Fassung des CV-Logos).
- **Hero** (weiss): Badge → Name → Rolle → Beschreibung → bis zu drei
  Schwerpunkt-Buttons. Rechts die **Fotokarte** 433 × 390pt, Radius 16pt,
  Foto in Graustufen (macht `extract_input.py`), unten 190pt Teal-Verlauf
  mit Name und Erfahrung. Der Verlauf liegt ueber dem Foto — das Gesicht
  muss im oberen Kartendrittel sitzen, deshalb beschneidet
  `extract_input.py` oben buendig.
- **Rumpf** (`--flaeche`): Sektionen mit 96pt Abstand, Sektions-Padding
  80pt oben / 96pt unten.
- **Zertifikatskarte**: weiss, Radius 12pt, 5pt Teal-Kante links, Padding
  ~26/32pt, Schatten hauchduenn. Jahres-Badge oben rechts.
- **Bilderraster**: 3 Kacheln je Zeile, 395 × 284pt, Radius 8pt, Abstand
  24pt, Bilder mittig beschnitten (cover). Kommt aus `zert_bilder.py`.
- **Kernkompetenzen**: je Kategorie ein Versalien-Label mit Hairline,
  darunter Kartenzeilen zu je drei: 397pt breit, Radius 14pt, Padding
  24/26pt. Titel links, fuenf Bewertungspunkte rechts (10pt Durchmesser,
  3,5pt Abstand; voll = `--brand`, leer = `--linie`), Beschreibung darunter.
- **Fuss**: Teal, Padding 64pt oben / 56pt unten. Frage in Weiss, Hairline
  (Weiss, 25 %), darunter Logo + drei Kontaktspalten.

## Was aus welcher Quelle stammt

Die Vorlagen-PDFs sind **mitten im Fuss abgeschnitten** — sichtbar sind nur
Frage und Hairline. Der Kontaktblock darunter (Logo, Ansprechpartner Manuel
Klein/CCO, Kontakt, Adresse) folgt dem Footer des CV-Skills und ist eine
bewusste Vervollstaendigung, keine Messung. Wenn eine vollstaendige Vorlage
auftaucht, diesen Block dagegen pruefen.

Die Sektionsicons (`icon-zertifikat.svg`, `icon-kernkompetenzen.svg`) sind
Nachbauten der Vorlage (Siegel bzw. gestapelte Ebenen in `--brand`), keine
Originalexporte aus Figma.

## Renderweg

WeasyPrint zuerst, sonst headless Chrome, sonst wkhtmltopdf — dieselbe Kette
wie im CV-Skill. Das Layout ist auf WeasyPrint abgestimmt. WeasyPrint-Eigenheiten,
die hier schon eingebaut sind:

- **Kein CSS-Grid, keine `calc()`-Spielereien**: Kartenzeilen sind
  Flex-Zeilen mit festen Breiten, die das Template selbst in Dreiergruppen
  schneidet (`| batch(3)`).
- **Kein `filter: grayscale()`**: WeasyPrint kennt keine CSS-Filter. Das
  Foto kommt deshalb bereits in Graustufen aus `extract_input.py`.
- **`object-fit: cover`** faengt nur kleine Formatabweichungen — Fotos und
  Zertifikate werden vorher auf das Zielformat gebracht.
