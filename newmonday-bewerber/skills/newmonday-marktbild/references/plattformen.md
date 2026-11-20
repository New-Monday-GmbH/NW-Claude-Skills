# PDFs auf den Plattformen tauschen

Beim Freigeben gehen die drei neuen PDFs eines Kandidaten auf jede Plattform,
auf der er ein Profil hat; die alten dieses Kandidaten werden dort gelöscht.
Adressen stehen in `~/.newmonday/marktbild.json` unter `plattformen`, nicht
hier (das Repo ist öffentlich).

**Allgemein**

- Nur über **Claude in Chrome** (`file_upload`): Der eingebaute Browser kann
  keine Dateien hochladen. `file_upload` liest nur Dateien aus dem
  Arbeitsverzeichnis – die PDFs vorher nach `<Arbeitsverzeichnis>/_upload-<datum>/`
  kopieren, danach den Ordner löschen. Ein Aufruf überträgt höchstens 10,4 MB.
- Anmelden macht immer der Nutzer. Nie ein Passwort eingeben.
- Nach jedem Speichern prüfen, ob die neuen Dateien gelistet sind und die
  alten fehlen. Andere Personen und Dateien (OnePager, Firmenprofile) bleiben.

**CRM (EspoCRM, Entität Kandidat)** – Bearbeiten-Ansicht des Kandidaten, je
Feld (New Monday CV / Portfolio / Skillset) die alte Datei mit × entfernen,
neue in den Datei-Input, Speichern. Schneller über die API der eingeloggten
Seite: die drei PDFs per `file_upload` in ein eingefügtes `<input type=file>`,
je Datei `POST api/v1/Attachment` (`role: Attachment`, `relatedType`, `field`
= cv/portfolio/skillmatrix, `file` als data-URL), dann `PUT` auf den Datensatz
mit `cvIds`/`portfolioIds`/`skillmatrixIds` = [neue ID]. Prüfen über die API
des Datensatzes.

**freelancermap** (Profilanlagen) – ein Datei-Input, eine Datei je Vorgang,
höchstens 20 Anhänge: erst die alten löschen (Knopf je Anhang-ID; die Refs
verschieben sich nach jedem Löschen, deshalb gezielt per ID), dann hochladen.

**Hays** (Profildaten pflegen) – mehrere Dateien je Vorgang; jede braucht die
Kategorie „Lebenslauf / Profil“, gesetzt per `form_input` (per JavaScript
gesetzte Werte verwirft Hays). Erfolg: Seite „Vielen Dank für Ihre
Profilpflege“. Hays benennt Dateien um.

**GULP/Randstad** (Profilverwaltung → Person → Profil bearbeiten → Reiter
Portfolio → Bearbeiten → PDF-Block bearbeiten) – höchstens 6 Dateien,
**5 MB je Datei**, und eine Datei mit gleichem Namen lehnt GULP ab – also
erst die alten im Block löschen, dann hochladen, dann Speichern. Die
verkleinerte Fassung unter dem normalen Namen hochladen. Größere vorher
verkleinern,

```
~/.newmonday/venv/bin/python -I <skill>/scripts/verkleinern.py <ein.pdf> <aus.pdf>
```

danach `verapdf --flavour ua1` und Textvergleich (`pdftotext`) gegen das
Original. Löschen mit Bestätigungsdialog. **Nie per URL neu laden** – das
beendet die Sitzung; nur innerhalb der Seite navigieren.

**etengo** (My.Etengo → Mitarbeiterverwaltung → Person → Qualifikationsprofil)
– **ein** PDF je Sprache, höchstens 6 MB; ein neues ersetzt das alte. Hochgeladen
wird ein zusammengefasstes „Qualifikationsprofil“: CV + Skill Matrix A4 +
Portfolio (verkleinerte GULP-Fassung), mit pikepdf aneinandergehängt
(`~/.newmonday/venv`), Name „New Monday - <Name> - Qualifikationsprofil.pdf“.
Sprache „Deutsch“ wählen, Datei in den Input, „Qualifikationsprofil hochladen“;
Erfolg: Meldung „Qualifikationsprofil erfolgreich hochgeladen“. Die Seite meldet
nach einiger Zeit „Sitzung läuft bald ab“ → „Angemeldet bleiben“.

**SOLCOM** (Mein Projektportal → Meine Dokumente → Hinzufügen, öffnet das
Profilformular) – eine gemeinsame Dokumentenliste des Firmenkontos, keine
Personenprofile. Nur die Dateien tauschen, die dort schon liegen (bisher CVs):
neue in „Neue Datei hinzufügen“ (lädt sofort, gleiche Namen bekommen „_0“),
alte per „Entfernen“, dann unten „Speichern“. Prüfen in der Liste
„Hochgeladene Unterlagen“.
