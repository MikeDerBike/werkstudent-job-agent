# Werkstudent Job Agent (MVP)

Lokale Windows-Desktop-App, die StepStone-Werkstudentenjobs (IT, Nuernberg + 150 km) ueber
einen Apify-Actor sammelt, Duplikate erkennt, pro neuem Job ein Bewerbungspaket erstellt
und alles in einem einfachen Dashboard anzeigt.

**Wichtig:** Die App bewirbt sich NICHT automatisch. Sie bereitet nur PDFs, Texte, Links
und Ordner vor. Die Bewerbung erfolgt immer manuell.

## Setup

1. Python 3.11+ installieren.
2. Abhaengigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```
3. `.env.example` nach `.env` kopieren und `APIFY_TOKEN` eintragen
   (Apify Console -> Settings -> Integrations).
4. `config.example.json` nach `config.json` kopieren und anpassen:
   - `apify_actor_id`: die Actor-ID des StepStone.de Jobs Scrapers aus dem Apify Store
     (Format `username/actor-name`). Im Mock-Modus ist dieser Wert optional.
   - `applicant`: Name, E-Mail, Telefon, Skills usw. eintragen.
   - Optional: `location`, `radius_km`, `queries`, `max_results` anpassen.
5. Optional: eigenen Lebenslauf als `assets/lebenslauf.pdf` ablegen - dann wird dieser
   in jedes Paket kopiert statt des Platzhalter-PDFs.

## Starten

```
python run.py
```

Dann auf **"Jobs suchen"** klicken. Der Apify-Crawl kann einige Minuten dauern.
Mit `mock_mode: true` in `config.json` nutzt die App lokale Demo-Daten und benoetigt
keinen Apify-Token.

## Was passiert bei einem Crawl

1. Apify-Actor wird mit den Queries aus `config.json` gestartet.
2. Ergebnisse werden normalisiert und gegen die lokale SQLite-DB (`Bewerbungen/jobs.db`)
   auf Duplikate geprueft (jobId -> canonicalUrl -> Firma+Titel+Ort).
3. Fuer jeden **neuen** Job wird ein Ordner unter `Bewerbungen/packages/` erstellt:
   ```
   2026-07-07_Firma_Werkstudent_Rolle/
     01_Jobbeschreibung.md
     02_Stelleninfos.md
     03_Lebenslauf.pdf
     04_Anschreiben.pdf
     05_Email_Vorlage.txt
     06_Portal_Antworten.txt
     07_Status.md
   ```
4. Bekannte Jobs werden nur aktualisiert (kein neues Paket). Geaenderte Jobs bekommen den
   Status "Aktualisiert"; ein neues Paket gibt es nur per Button "Paket neu erstellen".

## Dashboard

- Oben: Button "Jobs suchen", Archiv-Button und Kennzahlen fuer neue, bekannte,
  beworbene, ausgeblendete Jobs und Pakete.
- Jobkarten mit Firma, Rolle, Ort, Status, Bewerbungsart und Kurzbeschreibung.
- Buttons: Ordner / Lebenslauf / Anschreiben / Jobbeschreibung oeffnen.
- Status: "Als beworben markieren", "Ignorieren", "Paket neu erstellen".
- Fenster "Beworben / Hide": zeigt alle beworbenen und alle ausgeblendeten Jobs.
- E-Mail-Bewerbung: Adresse, Betreff und Mailtext direkt kopierbar.
- Portal-Bewerbung: Apply-Link klick- und kopierbar, Portal-Antworten als Textbox.

## EXE bauen

```
.\build.ps1
```

Die EXE liegt danach in `dist\WerkstudentJobAgent.exe`. `config.json` und `.env` neben
die EXE legen. Der Ordner `Bewerbungen/` wird beim ersten Start automatisch erstellt.

## Datenschutz vor dem Veroeffentlichen

Diese Dateien und Ordner sind lokal und sollten nicht in ein öffentliches Repository:

- `.env` mit API-Tokens
- `config.json` mit persoenlichen Bewerbungsdaten
- `Bewerbungen/` mit SQLite-DB, Logs und Bewerbungspaketen
- `assets/lebenslauf.pdf`
- `templates/anschreiben.odt`
- `_localtest/`

Die `.gitignore` ist entsprechend vorbereitet. Fuer ein oeffentliches Repository sind
stattdessen `.env.example` und `config.example.json` gedacht.

## Struktur

```
app/
  config.py        .env + config.json laden, Ordner anlegen
  db.py            SQLite-Schema + Repository
  apify_client.py  Apify-Actor starten, Dataset laden
  normalizer.py    StepStone-Felder -> internes Job-Objekt, Portal/E-Mail-Erkennung
  dedupe.py        Duplikaterkennung
  packager.py      Bewerbungsordner + PDFs erzeugen
  texts.py         Standardtexte (Anschreiben, E-Mail, Portal-Antworten)
  main.py          Dashboard (CustomTkinter)
Bewerbungen/       Daten: jobs.db, logs/, packages/  (wird automatisch angelegt)
```
