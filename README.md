# Werkstudent Job Agent

Lokale Windows-Desktop-App, die StepStone-Werkstudentenjobs (IT, Nuernberg + 150 km) ueber
einen Apify-Actor sammelt, Duplikate erkennt, pro neuem Job ein Bewerbungspaket erstellt
und alles in einem einfachen Dashboard anzeigt.

**Wichtig:** Die App bewirbt sich NICHT automatisch. Sie bereitet nur PDFs, Texte, Links
und Ordner vor. Die Bewerbung erfolgt immer manuell.

Kurz: Ja, andere Nutzer koennen das Projekt klonen, ihre eigene `config.json`
anlegen, Location und Suchbegriffe einstellen, einen eigenen Apify-Actor nutzen,
ihren Lebenslauf ablegen und optional ein eigenes Anschreiben-Template verwenden.

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

## Schnellstart ohne API

So kann man die App direkt testen:

```powershell
git clone https://github.com/MikeDerBike/werkstudent-job-agent.git
cd werkstudent-job-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config.example.json config.json
python run.py
```

Solange in `config.json` der Wert `"mock_mode": true` steht, nutzt die App lokale
Demo-Daten aus `app/mock_data.py`. Dafuer braucht man keinen API-Key.

## Echte Jobs mit Apify crawlen

1. `.env.example` nach `.env` kopieren:

   ```powershell
   Copy-Item .env.example .env
   ```

2. In `.env` den eigenen Apify-Token eintragen:

   ```env
   APIFY_TOKEN=dein_token
   ```

3. In `config.json` mindestens diese Felder anpassen:

   ```json
   {
     "mock_mode": false,
     "apify_actor_id": "dein-apify-user/dein-actor",
     "location": "Nuernberg",
     "radius_km": 150,
     "queries": ["Werkstudent IT"],
     "max_results": 25
   }
   ```

4. Danach `python run.py` starten und im Fenster `Jobs suchen` klicken.

Je nach Actor und Einstellungen koennen Apify-Kosten entstehen. `max_charge_eur`,
`max_results` und `include_details` sollten deshalb bewusst gesetzt werden.

## Eigene Bewerbungsdaten

Alle persoenlichen Daten stehen lokal in `config.json` unter `applicant`:

```json
"applicant": {
  "name": "Max Mustermann",
  "email": "max.mustermann@example.com",
  "phone": "+49 000 0000000",
  "address": "Musterstrasse 1, 90402 Nuernberg",
  "city": "Nuernberg",
  "study": "Informatik",
  "weekly_hours": "15-20 Stunden",
  "available_from": "ab sofort",
  "skills": ["Python", "SQL", "Automatisierung", "APIs"],
  "project_summary": "Kurzer Satz zu deinem Profil oder Projekt."
}
```

`config.json` ist in `.gitignore` und sollte nicht veroeffentlicht werden.

## Eigenen Lebenslauf nutzen

Den eigenen Lebenslauf als PDF hier ablegen:

```text
assets/lebenslauf.pdf
```

Wenn diese Datei existiert, kopiert die App sie in jedes Bewerbungspaket als
`03_Lebenslauf.pdf`. Wenn sie fehlt, erzeugt die App einen einfachen
Platzhalter-Lebenslauf.

## Eigenes Anschreiben-Template nutzen

Optional kann ein ODT-Template hier abgelegt werden:

```text
templates/anschreiben.odt
```

Die Vorlage kann diese Platzhalter enthalten:

```text
{{FIRMA}}
{{ROLLE}}
{{OPENER}}
{{FIT}}
```

Wenn LibreOffice installiert ist, erzeugt die App daraus automatisch
`04_Anschreiben.odt` und `04_Anschreiben.pdf`. Wenn kein Template oder kein
LibreOffice gefunden wird, nutzt die App ein einfaches PDF-Fallback.

## Eigenen Scraper oder Actor verwenden

Ein eigener Apify-Actor funktioniert, wenn er aehnliche Felder liefert. Die App
liest aktuell diese moeglichen Output-Felder:

```text
title
company / companyName
location / city
descriptionMarkdown / description / textSnippet
jobId / id
canonicalUrl / sourceUrl / url
applyUrl / portalUrl
directApply
applyEmail / contactEmail / extractedEmails
```

Wenn dein Scraper andere Feldnamen nutzt, passe die Zuordnung in
`app/normalizer.py` an. Wenn dein Actor andere Input-Parameter erwartet, passe
`app/apify_client.py` an. Die App sendet aktuell unter anderem `query`,
`maxResults`, `includeDetails`, `incrementalMode`, `location`, `radius`,
`bundesland` und `sort`.

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
     08_Bewerbung_komplett.pdf
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

Diese Dateien und Ordner sind lokal und sollten nicht in ein oeffentliches Repository:

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
assets/            optionaler lokaler Lebenslauf
templates/         optionales lokales Anschreiben-Template
Bewerbungen/       Daten: jobs.db, logs/, packages/  (wird automatisch angelegt)
```
