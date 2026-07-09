"""Konfiguration: laedt .env und config.json, stellt Pfade bereit."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Projektwurzel = Ordner ueber app/
ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "mock_mode": False,
    "base_dir": "Bewerbungen",
    "apify_actor_id": "",
    "location": "Nuernberg",
    "radius_km": 150,
    "bundesland": "bayern",
    "use_actor_radius": True,
    "max_results": 100,
    "age_days": 14,
    "state_key": "werkstudent-it-nuernberg",
    "queries": ["Werkstudent IT"],
    "applicant": {
        "name": "<Name>",
        "email": "<E-Mail>",
        "phone": "<Telefon>",
        "city": "Nuernberg",
        "weekly_hours": "15-20 Stunden",
        "available_from": "ab sofort",
        "skills": ["Python", "SQL", "Automation", "APIs"],
        "project_summary": (
            "Aktuell arbeite ich an einem eigenen Softwareprojekt zur strukturierten "
            "Datenerfassung und Automatisierung wiederkehrender Arbeitsablaeufe."
        ),
    },
}


def load_config() -> dict:
    load_dotenv(ROOT_DIR / ".env")
    cfg = dict(DEFAULT_CONFIG)
    cfg_path = ROOT_DIR / "config.json"
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))

    cfg["root_dir"] = ROOT_DIR
    base_dir = Path(cfg["base_dir"])
    if not base_dir.is_absolute():
        base_dir = ROOT_DIR / base_dir
    cfg["base_dir"] = base_dir
    cfg["packages_dir"] = base_dir / "packages"
    cfg["logs_dir"] = base_dir / "logs"
    cfg["db_path"] = base_dir / "jobs.db"

    for d in (base_dir, cfg["packages_dir"], cfg["logs_dir"]):
        d.mkdir(parents=True, exist_ok=True)

    cfg["apify_token"] = os.getenv("APIFY_TOKEN", "")
    return cfg
