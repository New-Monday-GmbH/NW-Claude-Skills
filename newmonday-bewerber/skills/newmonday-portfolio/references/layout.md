# Layout-Referenz

Alle Werte hier sind aus den bestehenden Portfolios gemessen (Ansgar Rolfes und
Michael Gottscheck, beide 2026, 21 Seiten, strukturgleich), nicht geschätzt.
Gegengelesen wurden zwei ältere Fassungen (Carolin Reis, Freia Schwertfeger);
wo sie abweichen, steht das dabei.

Die Folie „KI-Einsatz" und die Seiten der Projektstrecke sind aus dem
Referenzportfolio gemessen (Paul Hecker, 2026, 29 Seiten). Gerechnet wurde auf
dem 1200-px-Export mit 1,6 pt je Pixel.

## Einheiten

Die Folien sind **1920 × 1080 pt** – Querformat 16:9, kein A4. Im CSS deshalb
durchgehend `pt`. Wer die Werte als `px` übernimmt, baut das Dokument um ein
Viertel zu klein.

## Seitenraster

| Wert | |
|---|---|
| Seite | 1920 × 1080 pt |
| Linker Randstreifen | 0 – 72 pt, volle Höhe |
| Linke Textkante | 193 pt |
| Cover und Divider | 160 pt |
| Kontaktseite | 240 pt |
| Wortmarke oben rechts | x 1712 – 1860, y 60 – 75 (148 × 15 pt) |
| Wortmarke auf dem Cover | x 160, y 160, 335,5 pt breit |
| Seitenzahl | rechts 60 pt, unten 46 pt, 21,8 pt fett |

**Der Streifen ist die Sektionsmarke.** Petrol heißt „hier beginnt etwas" – die
erste Seite eines Abschnitts und jede Projekt-Kopfseite. Nebelblau heißt „das
läuft weiter". Auf der Statementseite nimmt er die Farbe der rechten Hälfte an.
Die Abschlussseite eines Projekts hat keinen: Sie ist randlos, und ein Streifen
darauf wäre ein Rand.

**Cover und Divider tragen keine Seitenzahl.** Die Zahl ist die tatsächliche
Blattnummer, nicht eine eigene Zählung: Seite 12 zeigt „12".

### Wo die Bildkante liegt

| Seitentyp | Bild beginnt bei | gemessen im Original |
|---|---|---|
| Arbeitsweise und KI-Einsatz | 1011 pt | in der Referenz 1011,2 durchgehend |
| Summary (Foto der Firmenzentrale) | 900 pt | 888 / 900 / 816 / 900, in der Referenz 931 / 960 / 1040 |
| Lösung (Markenfläche) | 900 pt | in der Referenz viermal 870 |
| Statement (Fläche, kein Bild) | 798 pt | 798 |
| Projekt-Kopfseite | kein Bild mehr | – |
| Abschlussseite | randlos, 0 pt | 0 |

Die Vorlage ist an dieser Stelle nicht ganz sauber – im Template sind die Werte
vereinheitlicht. Die Bildbreiten stehen in `render_portfolio.py` als
`FLAECHENBREITE` und dienen zugleich der Auflösungsprüfung.

## Farben

| Token | Wert | Einsatz |
|---|---|---|
| `--brand` | `#009193` | Cover, Divider, Panels, Balken, Verweise |
| `--brand-dark` | `#265d60` | nur die Eyebrow-Zeile über den Überschriften |
| `--ink` | `#111111` | Überschriften, Labels, Seitenzahl |
| `--body` | `#485758` | Fließtext |
| `--mist` | `#ebf2f5` | Streifen, Kontaktband, Statementfläche, inaktive Schrittbalken |
| `--line` | `#dedede` | Kartenrahmen, Trennlinien |
| `--warm` | `#f4ece8` | Fläche hinter dem Profilfoto |

Die Markenfarben der Projekte kommen aus dem Kundenlogo und gehören nicht in
diese Liste – siehe `scripts/markenfarbe.py`.

## Typografie (Inter)

| Element | Größe | Schnitt | Zeilenhöhe |
|---|---|---|---|
| Seitentitel, Cover-Titel, große Zahlen | 96 pt | 800 | 1.2 |
| Name auf der Profilseite | 72 pt | 800 | – |
| Zitat auf der Statementseite | 52 pt | 400 | 1.4 |
| Cover-Name, Jahr | 48 pt | 700 / 400 | – |
| Prozess-Spaltentitel | 42 pt | 800 | 1.31 |
| Rolle (Cover und Profil) | 40 pt | 400 | – |
| Kontakt-Überschrift | 32 pt | 700 | – |
| Kartentitel, Kontakt-Fließtext, Prozesstext | 24 pt | 700 / 400 | 1.5 |
| Labels, Schrittbeschriftung, Subline | 21 pt | 700 | – |
| Fließtext, Listen, Kartenzeilen | 20 pt | 400 | 1.35 |
| Eyebrow (Versalien, 1.2 pt Laufweite) | 20 pt | 700 | – |
| Badge-Text | 18 pt | 600 | 1.35 |

Überschriften laufen mit −2 pt Laufweite, der Name auf der Profilseite mit
−1,6 pt.

## Maße einzelner Seiten

**Profilseite.** Foto 363 × 445 pt bei x 65 / y 144, Graustufen, `cover`.
Name x 500 / y 117, Rolle y 219. Karten x 500, Breite 834: Top-Kenntnisse
y 305, Kenntnisse y 511 – die 36 pt Luft dazwischen sind Absicht: bei y 475
klebten die beiden Rahmen aneinander, und genau das kam als Rückmeldung
zurück (August 2026, Paul-Deck). Der Preis dafür ist eine Zeile: die Karte
trägt seither **sechs bis sieben** Einträge statt acht. Rechtes Petrol-Panel
x 1393, 527 breit; Karten darin x 1453, 407 breit, bei y 223 / 516 / 792.
Die Kenntnisse-Zeilen laufen im 63-pt-Takt mit Trennlinie.

Die Connect-Karte führt ihre Einträge **als petrolfarbene Pfeil-Links**
(„LinkedIn Profil →“) – ohne schwarzen Titel, ohne „Anzeigen“-Link, ohne
Trennlinie zwischen den Einträgen. So steht es in der Referenz (Paul, S. 2),
und diese Karte bleibt immer in diesem Muster; die frühere Form mit fettem
Titel und „Anzeigen“ darunter kam als Abweichung zurück. Die Linktitel sind
**sprechende Labels** („Portfolio“, „LinkedIn Profil“), nie die nackte
Domain – „paulhecker.com →“ kam als Fehler zurück. Gleiches Prinzip bei den
Sprachen: Niveau im Klartext („Business Niveau“, „Muttersprache“), nicht als
Kürzel wie „C2“.

**Design-Prozess.** Immer drei Spalten bei x 193 / 682 / 1171, Balken
323 × 12 pt bei y 434, Titel darunter, Text ab y 544. Eine frühere Fassung
hängte bei vorhandener KI-Folie „KI-Einsatz" als vierte Spalte an – gestrichen
nach Rückmeldung (August 2026): KI läuft in allen Phasen mit und ist kein
Schritt nach der Umsetzung; als letzte Spalte sah sie aus wie einer. Die
KI-Folie bleibt als eigene Arbeitsweise-Seite, taucht aber weder auf Seite 6
noch in der Schrittleiste auf.

**Arbeitsweise.** Eyebrow y 120, Überschrift y 155 (800 pt breit), Text
darunter mit 105 pt Abstand – bei einer Zeile ab y 375, bei dreien ab y 606.
Die Zeilenzahl rechnet `kopfzeilen()` aus der Schriftdatei; geschätzt wäre sie
irgendwann um eine Zeile daneben und der Text stünde in der Überschrift. Braucht
ein Titel bei 96 pt mehr als drei Zeilen, setzt `kopfmass()` ihn mit 84, 72 oder
64 pt und meldet das: Kürzen hieße Inhalt wegwerfen, und vier Zeilen zu 115 pt
liefen in den Fließtext.
Schrittleiste unten: drei Balken im Takt der Prozessseite, 323 × 12 pt bei
x 193 / 682 / 1171, y 960, Beschriftung y 992. Der dritte liegt auf dem Bild
und ist dort weiß; ein Verlauf über die unteren 298 pt hält die weiße Schrift
lesbar.

Wortmarke und Seitenzahl richten sich auch hier nach dem Motiv, nicht nach
einer festen Farbe: `arbeitsweise-3.jpg` ist unten rechts fast schwarz, eine
dunkle Seitenzahl verschwände darin spurlos.

**KI-Einsatz.** Dieselbe Seite wie die Arbeitsweise, mit zwei Unterschieden.
Unter dem Text stehen die Werkzeuglogos: in p-10 fünf Kacheln zu 80 × 80 pt im
102,4-pt-Takt, in p-08 vier im selben Maß, ab x 193, Grund `--mist`, das Logo
darin freigestellt. Die Fünferreihe misst so 489,6 pt (5 × 80 + 4 × 22,4) und
endet auf 826 pt.

Die Kacheln messen **immer 80 pt**, egal wie viele es sind; wenige stehen als
kurze Reihe am selben Platz, Unterkante 826 pt, der Fließtext endet 11 pt über
der Reihe. Eine frühere Fassung ließ ein bis drei Kacheln auf 120 pt wachsen –
damit begann die Reihe höher und die Kacheln saßen sichtbar anders als in der
Referenz: genau das kam als „verrutscht" zurück. Sieben Kacheln zu 80 pt wären
694 pt und ragten aus der 640 pt breiten Textspalte; mehr als sechs zeigt die
Seite deshalb nicht, und das Skript sagt, welche es weggelassen hat.

Der Fließtext dieser Seite steht durchgehend mager: `**fett**` wird vom
Renderskript entfernt, nicht gesetzt – in den Referenzen trägt die Folie
keinen Fettdruck, und markierte Halbsätze lasen sich dort wie Claims.

Die Seite trägt **keine Schrittleiste**. Eine frühere Fassung zählte
„KI-Einsatz" dort als vierten Balken mit – gestrichen nach Rückmeldung
(August 2026): KI ist kein Prozessschritt, sondern läuft in allen Phasen mit,
und als vierter Balken las sie sich wie einer.

**Agenturseite.** Überschrift y 116, Subline y 386, Kundenwand ab y 500
(665 pt breit), Badge x 1120 / y 707 (110 pt), Badge-Text y 885. Statuskarten
im Panel bei y 227 / 482 / 737.

**Projekt-Kopfseite.** Kundenlogo x 193 / y 121, flächengleich skaliert wie
auf der Wand (`LOGO_PROJEKT_MASS` 105, Deckel 80 pt Höhe / 420 pt Breite).
Feste 61 pt Höhe standen hier einmal – damit wirkte eine breite Wortmarke
(norisbank) doppelt so wuchtig wie eine kompakte Bildmarke; in der Referenz
(p-13/18/23) wirken alle Kundenlogos gleich schwer: die Samsung-Wortmarke
~32 pt hoch, das kompakte OSMR-Zeichen ~90 pt. Überschrift y 252, 1534 pt
breit – ohne Aufmacherbild steht die ganze Blattbreite offen, und „Opel,
Peugeot und Citroën" misst bei 96 pt schon 1200 pt. Zwei gleich breite
Spalten, Oberkante y 451. Bricht der Kundenname um, rücken beide Spalten um
eine Zeile nach unten; stünden sie fest, liefe die zweite Überschriftzeile
über die Labels. Ein Bild gibt es hier nicht mehr.

Die Spalten stehen im Referenzmaß: 575 pt bei x 193 und x 916, rechts der
Kundenspalte bleibt Weißraum wie in p-13/18/23. **„Meine Rolle" folgt dem
Textfluss der linken Spalte** – 56 pt unter dem Projekttext, dann Label und
Stichpunkte. Die frühere Fassung ließ den Block von der Blattkante nach oben
wachsen (Unterkante 1034 pt) und zog dafür die Spalten auf 693 pt auseinander;
bei kurzen Texten klebte der Block sichtbar allein am unteren Rand – genau das
kam als Rückmeldung zurück (August 2026). In der Referenz sitzt „Meine Rolle"
immer direkt unter dem Projekttext.

Gemessen trägt die Kundenspalte so rund 100 Wörter, die Projektspalte neben
einem Rollen-Stichpunkt rund 75, neben dreien rund 60 (drei Absätze,
einzeiliger Projektname). Mehr als drei Stichpunkte sieht die Vorlage nicht
vor: Unter „Meine Rolle" stehen Rollenbezeichnungen wie in der Referenz
(„Lead UI/UX Designer"), keine Aufgabenlisten – das Renderskript meldet
Überzahl. Der Überlauf läuft über die normale Zonenprüfung (Unterkante
1010 pt); einen eigenen Höhenrechner für den Rolle-Block braucht es nicht
mehr.

**Summary.** Rechts ab 900 pt über die volle Höhe das Foto der Firmenzentrale,
`cover`. Links Kundenlogo, Überschrift y 252, Text ab y 452 (575 pt breit).

**Lösungsseite.** Rechts ab 900 pt die Markenfläche mit den Screens. Links
Kundenlogo, dann `titel` als fette Einleitungszeile an der Stelle des alten
Labels (y 256), darunter der Inhalt ab y 300, beides 575 pt breit. In der
Referenz beginnt die Zeile bei y 226, der Fließtext bei y 310, die Stichpunkte
bei y 430.

Die Einleitungszeile ersetzt das feste Label „Die Lösung", sie schafft es nicht
ab: Ohne `titel` steht das Label wieder dort. Der Platz ist derselbe, einzeilig
wie zweizeilig – der Text darunter fließt nach.

**Abschlussseite.** Die Markenfläche randlos über die ganze Folie, kein
Streifen, kein Text. Es bleiben Wortmarke, Seitenzahl und der NDA-Hinweis
(gemessen y 1016–1034).

**Kontaktseite.** Nebelblaues Band ab y 413. Adresse x 240 / y 101, Aufruf
x 752 / y 102 (749 pt). Weiße Box x 240 / y 609 (657 × 264). Person x 1360 /
y 516, Bild 359 × 320, darunter der Petrol-Block mit Name und Titel.

## Absolut positioniert — und was WeasyPrint dabei anstellt

Die Seiten sind mit `position: absolute` gebaut, nicht im Textfluss. Das ist bei
einem Foliendokument richtig: Jede Fläche hat eine feste Stelle, und es gibt
keine Umbrüche, die zu erhalten wären. Vier Fallen gehören dazu:

- **Jedes absolut positionierte Textelement braucht eine gesetzte Breite.**
  Ohne `width` greift Shrink-to-fit viel zu eng, und „UI/UX Design Portfolio"
  bricht mitten im Titel um. Wer ein neues Textelement anlegt, setzt die Breite
  mit.
- **`nth-of-type` zählt alle Geschwister desselben Tags**, nicht die mit der
  Klasse. Streifen, Eyebrow, Logo und Seitenzahl sind alles `div`, also trifft
  `.prozess-spalte:nth-of-type(1)` daneben. Die Spalten- und Schrittpositionen
  setzt deshalb das Renderskript direkt als `style="left:…"`.
- **Flex-Umbruch reagiert auf Zehntelpunkte.** Vier Kacheln zu 401,8 pt sind
  1607,2 pt und brechen in einem 1607 pt breiten Kasten auf drei je Zeile um.
  Die Zellbreite wird deshalb abgerundet.
- **`justify-content` wirkt nicht.** Ein Logo, das per Flex in seiner Kachel
  zentriert werden soll, hängt in WeasyPrint linksbündig – so kamen die
  Kundenwand und die Werkzeugkacheln der KI-Folie als „verschoben" zurück
  (August 2026). Zentriert wird deshalb über gerechnetes Padding aus dem
  Renderskript; `align-items` und der Zeilenfluss von `flex-wrap`
  funktionieren dagegen.
- **Der Rest eines zu hohen Blocks steht auf der Folgeseite.** Ein absolut
  positionierter Kasten wächst über die Blattkante hinaus, statt abgeschnitten
  zu werden; WeasyPrint bricht ihn um und legt den Rest in die Textebene der
  nächsten Seite. Zu sehen ist er dort nicht – die Folie ist gegen ihn
  beschnitten –, im PDF steht er trotzdem, und auf der eigentlichen Folie fehlen
  die Sätze. Genau deshalb misst `pruefe_ueberlauf()` das fertige PDF nach,
  statt sich auf das Layout zu verlassen.

## Die Markenflächen sind vorgerenderte Bilder

Auf Lösungs- und Abschlussseite liegen die Screens schräg und laufen über die
Kanten hinaus. Im Browser wäre das eine Handvoll `transform` – **WeasyPrint
setzt Transformationen nicht brauchbar um**. Deshalb baut `scripts/screens.py`
die Fläche als Bild, bevor gerendert wird, und das Template setzt nur noch ein
`<img>` ein. Zwei Größen, doppelt aufgelöst gegen die Punktmaße der Folie:
`panel` 2040 × 2160 px für die rechte Fläche (1020 × 1080 pt), `voll`
3840 × 2160 px für die ganze Folie. Gesichert wird als JPEG: Die Fläche ist
ein Foto aus Fotos, und PNG speichert davon vor allem Rauschen. Ohne
`markenfarbe` bleibt der Grund `--mist`-nah – dieselbe Logik wie bei den
Bildplatzhaltern.

**Die Anordnung ist die gestalterische Entscheidung des Skills** (seit
August 2026): Das Kandidatenmaterial liefert die Screens, nicht ihre Lage.
Fest bleiben nur die Grundfläche selbst und die HQ-Fotos der Summary-Seiten.
Sechs Vorgänger sind bewusst verworfen – die Zufallsstreuung mit Perspektive
(„unscharf und komisch überlappt“), das per PyMuPDF aus Pauls Portfolio 2026
vermessene 15-Grad-Raster, ein flaches Editorial- und ein Showcase-Raster
(alle: „sieht immer noch komisch aus“), die **Bühne** aus Stand 7
(Markenverlauf mit Lichtschein, Fassungen, Überlapp-Paar – Screens klein und
mittig auf leerer Fläche) sowie die **Kachelwand** aus Stand 8: viele kleine
Kacheln in Versatz-Spalten auf einer zu 88 % Richtung Weiß aufgehellten
Markenfläche. Im fertigen Deck (Enrico Meermeier, August 2026) wirkten diese
Flächen „random rumfliegend“ – dunkle Karten schwebten auf fahlem Grau,
und keine der vier Referenzen zeigt eine Wand aus kleinen Kacheln.

Seit `LAYOUT_STAND` 9 ist die Fläche eine **diagonale Kaskade**, gemessen an
den Referenzportfolios (Gottscheck S. 14/15/18/19, Lenz S. 14/15/18/19/22/23,
New-Monday-Fassung Enrico Meermeier S. 15–24, Rolfes S. 14/18):

- **Satter, dunkler Grund.** Die Markenfarbe steht voll gesättigt
  (Gottscheck: Royalblau/Azur, Rolfes: Navy und sattes Orange). Nur zu
  helle Töne (Luminanz > 0,55) werden Richtung Schwarz gezogen, bis sie
  bei ≤ 0,42 tragen – Lenz legt selbst rote Marken auf Schwarz, hell wird
  in keiner Referenz gearbeitet. Ohne Markenfarbe ein dunkles Petrol
  (`NEUTRAL` #103537) in der Familie von `--brand`.
- **Wenige, große Screens.** Ein Panel trägt 1–3 Desktop-Screens (bis 6
  Hochformate), die volle Folie 2–6 (bis 8 Hochformate) – Vorlagen je
  Anzahl und Mehrheitsformat (`KASKADE_QUER`, `KASKADE_HOCH`, ab drei
  Phones auf der vollen Fläche der „Kamm“ aus Lenz S. 14/15: eine Reihe
  großer Phones, abwechselnd nach oben und unten versetzt). In den
  Referenzen misst ein Desktop-Screen 45–60 % der Folienbreite; die
  Desktop-Slots bleiben unter 1 920 px, damit ein gewöhnlicher
  1 920er-Export jede Lage ohne Hochrechnen trägt. Der erste Screen der
  JSON bekommt den Hero-Platz – die Reihenfolge im Material ist die
  Reihenfolge der Stärke.
- **Diagonale mit Anschnitt.** Der obere Screen blutet über die obere (und
  linke) Kante, der untere über rechts und unten (Gottscheck-Geometrie);
  ein einzelner Hero liegt groß und rechts-unten angeschnitten (Enrico
  S. 19). Die Komposition hängt an den Kanten, nichts schwebt frei in der
  Mitte; der Grund zeigt sich als Negativraum der Diagonale, nicht als
  Rand um jede Kachel. Eine Deckungs- oder Lückenprüfung gibt es deshalb
  nicht mehr – sichtbarer Grund ist hier gewollt.
- **Ein gemeinsamer Kippwinkel.** Die ganze Kaskade liegt um 8° gegen den
  Uhrzeigersinn gekippt (Referenzen: 5–12°). Kein Screen wird einzeln
  gedreht – komponiert wird auf einer übergroßen Leinwand bei 0°, diese
  wird genau einmal gedreht (BICUBIC) und aufs Folienmaß beschnitten.
  Jeder Screen wird genau einmal skaliert (LANCZOS).
- **Keine Fassungen.** Kacheln sind Karten mit leicht gerundeten Ecken
  (3 % der kürzeren Kante, 20–56 px) und weichem, flachem Schatten
  (Deckkraft 34/255, kaum Versatz). Browser-Chrome, Geräterahmen und
  Ampelpunkte gibt es nicht – so halten es Gottscheck und Lenz.
- **Schleier unter den Möbeln.** Wortmarke (oben rechts) und Seitenzahl/NDA
  (unten rechts) können auf Screens liegen. Unter ihren Ecken liegt ein
  weicher, elliptischer Verlaufsschleier in der um 68 % abgedunkelten
  Markenfarbe (voll deckend bis 380/470 px, aus bei 830/1000 px, 70 px
  Gauß) – nur dort, wo wirklich Kacheln liegen. Die Kontrastmessung des
  Renderers (`ecke_dunkel`) entscheidet unverändert über helle oder dunkle
  Wortmarke.
- **Komposit-Zerleger.** Ein Quellbild, das mehrere getrennte, rechteckige
  Screens auf einheitlichem Grund zeigt, zerfällt vor der Kaskade in
  einzelne Karten; ein einzelner Screen auf viel Grund wird auf den Inhalt
  beschnitten (Farbabstands-Maske statt Kantendetektor – Punktmuster im
  Grund täuschen den Kantendetektor). Echte Screenshots tragen Inhalt bis an
  die Kanten und passieren unverändert; zerlegt wird nur, wenn rundum
  freier Saum liegt (≥ 2,5 % je Seite) und die Teile groß genug bleiben
  (≥ 500/900 px). Überlappend montierte Screens lassen sich nicht trennen
  und bleiben ganz.

Schärfe misst `screens.py` je Screen gegen die tatsächlich platzierte Breite
in Pixeln (2 px je Punkt). Als Maß fürs Material: ein Desktop-Screen liegt
auf der vollen Folie 1 450 bis 1 920 px breit, auf dem Panel 1 220 bis
1 920 px; ein Phone liegt 620 bis 780 px breit. Ein 1 920er-Export trägt
damit jede Lage.

Das Qualitäts-Gate (`WEICH_MIN` 0,75) platziert nicht, was deutlich
hochgerechnet würde: Eine zu weiche Lage schrumpft zuerst in ihrem Platz
(bis `SCHRUMPF_MIN` 0,5 der Zielbreite – eine kleinere, aber scharfe Lage
ist besser als eine blanke Fläche), erst darunter fliegt der Screen raus
und die Kaskade wird mit einem Screen weniger neu gelegt. Bleibt nichts
übrig, schreibt `screens.py` die reine Grundfläche und meldet es; die
Übergabe bittet dann um Originalexporte. Leicht hochgerechnete Screens
(0,75–0,98) bleiben stehen und werden je Datei gemeldet.

## Logos

**Gleiche Fläche statt gleicher Höhe.** Über die Höhe skaliert wirkt eine
kompakte Bildmarke doppelt so schwer wie ein breiter Schriftzug. Das
Renderskript liest das Seitenverhältnis aus der Datei (SVG: `viewBox`, sonst
Dateikopf) und rechnet:

```
Breite = Größe × √Verhältnis      Höhe = Größe / √Verhältnis
```

**Die Kundenwand passt ihr Raster an die Menge an.** Wenige Logos dürfen groß
stehen, viele müssen enger – sonst wird die Wand entweder leer oder unlesbar:

| Logos | Spalten |
|---|---|
| bis 5 | eine Reihe |
| bis 6 | 3 |
| bis 12 | 4 |
| bis 15 | 5 |
| bis 24 | 6 |
| bis 28 | 7 |
| darüber | 8 |

Bis fünf Logos stehen nebeneinander: p-03 zeigt vier in einer Reihe, und eine
Restzeile mit einem einzelnen Logo sieht nach Versehen aus. Darüber gemessen in
den Vorlagen: 6 Logos in 3 Spalten (Gottscheck, Reis), 22 in 8 (Freia),
24 in 6 (Rolfes).

Die Reihe und das Raster laufen mit verschiedenen Grenzen:

- **Eine Reihe (bis 5 Logos)** steht exakt im Referenzmaß von p-03 (Paul
  Hecker): `LOGO_MASS_REIHE` 160 pt, `LOGO_HOEHE_REIHE` 128 pt, Zellfaktor
  0,46 – und tiefer als das Raster: Reihenmitte ~717 pt (`REIHE_OBEN` 397 pt
  bei 640 pt Wandhöhe) statt 620 pt. Die Rückmeldung „Größe und Position wie
  bei Paul" (August 2026) bezog sich genau auf diesen Fall.
- **Das Raster (ab 6 Logos)** bleibt eine Stufe darunter: `LOGO_MASS_MAX`
  132 pt, `LOGO_HOEHE_MAX` 104 pt, Zellfaktor 0,40. Mit den Referenzwerten kam
  eine volle Wand (12 Logos, Freia-Portfolio, Seite 3) als zu wuchtig zurück –
  die Verkleinerung von damals galt dem Raster, nicht der Reihe.

Der Höhendeckel ist jeweils nötig, weil der Flächendeckel über die Fläche
wirkt – eine quadratische Bildmarke wüchse sonst auf das volle Maß.

## Wortmarke und Seitenzahl wechseln die Farbe

Auf Projektseiten reicht das Bild bis in die rechte obere und untere Ecke. Ob
Wortmarke und Seitenzahl dort weiß oder schwarz stehen, hängt am Motiv – in den
Vorlagen wechselt es von Seite zu Seite. Das ist kein Schönheitsdetail: Auf
einem dunklen Screenshot ist eine schwarze Wortmarke unsichtbar.

`ecke_dunkel()` misst nicht die ganze Bildecke, sondern nur `MOEBELFELD` – die
Stelle, an der Wortmarke und Seitenzahl tatsächlich liegen. Eine ganze Ecke
mittelt Himmel und Fassade zusammen und entscheidet dann für einen Punkt, an dem
nichts steht. Gemessen wird außerdem der Ausschnitt, der auf der Folie zu sehen
ist: Die Flächen sind `object-fit: cover` und rechtsbündig, ein abgeschnittener
Dateirand darf nicht mitentscheiden. Wo der Verlauf aus `.bildschatten` liegt,
wird er mitgerechnet (`SCHATTEN_HOCH`, `SCHATTEN_TIEF`) – er macht die untere
Ecke dunkel, egal wie hell das Foto ist. Die Schwelle ist `TINTENWECHSEL`.

Bei den Markenflächen misst `marken_moebel()` zuerst genauso die fertige, schon
zusammengesetzte Fläche; `hell(markenfarbe)` ist nur der Rückfall, wenn nichts
zu messen ist. Umgekehrt wäre es falsch: Ein Screen, der bis in die Ecke reicht,
entscheidet dort über die Lesbarkeit, nicht die Farbe darunter. `screens.py`
hält diese Ecken über `SPERRE_OBEN` und `SPERRE_UNTEN` frei – in der Referenz
bleibt dort immer Markenfarbe stehen.

Ein Fall bleibt, den keine Tinte löst: Liegt das Möbelfeld halb auf Hellem und
halb auf Dunklem, verschwindet ein Stück Wortmarke, egal wie entschieden wird.
`ecke_dunkel()` zählt deshalb die widersprechenden Pixel und meldet ab
`FELD_UNRUHE`, dass das Motiv zu wechseln ist.

## Was aus den Vorlagen bewusst nicht übernommen wurde

- **Freias Variante** ohne Aufmacherbild auf der Kopfseite ist inzwischen der
  Normalfall: Die Kopfseite hat gar kein Bild mehr, beide Textspalten sind gleich
  breit.
- **Reis' Projektseiten** mit „Der Kunde" statt „Projekt / Kunde / Meine Rolle"
  sind eine ältere Fassung und nicht nachgebaut.
- **Freias Gründungsjahr 2019** ist ein Fehler; drei von vier Vorlagen und der
  Satz „Seit 2018 verlängern 100 %…" sagen 2018.
- **Freias Vollbildseiten** mit Fließtext über einer Bildcollage kommen nur bei
  ihr vor und sind nicht Teil des Standards.
