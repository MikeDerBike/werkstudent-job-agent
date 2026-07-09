"""Mock-Daten fuer den Testbetrieb ohne Apify (mock_mode in config.json)."""

MOCK_ITEMS = [
    {
        "jobId": "mock-1001",
        "title": "Werkstudent Softwareentwicklung Python (m/w/d)",
        "company": "Nordstadt Software GmbH",
        "location": "Nuernberg",
        "canonicalUrl": "https://example.com/jobs/mock-1001",
        "applyUrl": "https://example.com/apply/mock-1001",
        "directApply": True,
        "descriptionMarkdown": (
            "## Deine Aufgaben\n"
            "- Entwicklung interner Tools mit Python und SQL\n"
            "- Unterstuetzung bei der Automatisierung von Testprozessen\n"
            "- Mitarbeit in einem agilen Scrum-Team\n\n"
            "## Dein Profil\n"
            "- Studium der Informatik oder vergleichbar\n"
            "- Erste Erfahrung mit Python\n"
            "- 15-20 Stunden pro Woche verfuegbar"
        ),
        "datePosted": "2026-07-01",
    },
    {
        "jobId": "mock-1002",
        "title": "Werkstudent IT-Support (m/w/d)",
        "company": "Mainwerk IT Services GmbH",
        "location": "Erlangen",
        "canonicalUrl": "https://example.com/jobs/mock-1002",
        "applyUrl": "",
        "directApply": False,
        "descriptionMarkdown": (
            "Wir suchen Unterstuetzung fuer unseren internen IT-Support am Standort Erlangen. "
            "Aufgaben: 1st-Level-Support, Geraetemanagement, Dokumentation.\n\n"
            "Bitte senden Sie Ihre Bewerbung an mailto:jobs-support@example.com"
        ),
        "datePosted": "2026-06-28",
    },
    {
        "jobId": "mock-1003",
        "title": "Working Student Data Engineering (f/m/d)",
        "company": "Bergfeld Data Solutions GmbH",
        "location": "Herzogenaurach",
        "canonicalUrl": "https://example.com/jobs/mock-1003",
        "applyUrl": "https://example.com/apply/mock-1003",
        "directApply": True,
        "descriptionMarkdown": (
            "Join our Data Platform team! You will build data pipelines with Python, "
            "SQL and Airflow, and support our analytics engineers. "
            "English-speaking team, hybrid work, 16-20h/week."
        ),
        "datePosted": "2026-07-03",
    },
    {
        "jobId": "mock-1004",
        "title": "Werkstudent Cloud Infrastructure (m/w/d)",
        "company": "Cloudwerk Systems GmbH",
        "location": "Herzogenaurach",
        "canonicalUrl": "https://example.com/jobs/mock-1004",
        "applyUrl": "",
        "directApply": False,
        "descriptionMarkdown": (
            "Unterstuetzung des Cloud-Teams bei Azure-Deployments, Terraform-Modulen "
            "und Monitoring-Dashboards. Kein Apply-Link vorhanden, Details auf der Anzeige."
        ),
        "datePosted": "2026-06-30",
    },
    {
        "jobId": "mock-1005",
        "title": "Werkstudent Informatik - Testautomatisierung (m/w/d)",
        "company": "Testfabrik Digital GmbH",
        "location": "Nuernberg",
        "canonicalUrl": "https://example.com/jobs/mock-1005",
        "applyUrl": "https://example.com/apply/mock-1005",
        "directApply": True,
        "descriptionMarkdown": (
            "Du schreibst automatisierte Tests fuer unser Netzwerk-Monitoring-Produkt, "
            "arbeitest mit Python und pytest und bringst eigene Ideen in die CI/CD-Pipeline ein."
        ),
        "datePosted": "2026-07-04",
    },
]
