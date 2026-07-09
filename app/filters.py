"""Relevanzfilter: sortiert nach dem Crawl lokal aus (kostet keine Apify-Laeufe).

Regeln:
1. Titel muss eine Studenten-Rolle sein (Werkstudent / studentische Hilfskraft / HiWi ...).
2. IT-Bezug darf auch aus Beschreibung, Skills, Branche oder Snippets kommen.
3. Bei bundesland=bayern muss ein Bayern-Standort erkennbar sein.

Konfigurierbar in config.json unter "filter" (require_title_any, locations_any, allow_remote).
"""
import re
import unicodedata

DEFAULT_FILTER = {
    "require_title_any": [
        "werkstud",            # werkstudent, werkstudentin, werkstudierende
        "working student",
        "student assistant",
        "studentische hilfskraft",
        "studentische aushilfe",
        "studentische mitarbeit",
        "studentischer mitarbeit",
        "wissenschaftliche hilfskraft",
        "hiwi",
    ],
    "locations_any": [
        "nuernberg", "nurnberg", "nuremberg", "fuerth", "erlangen",
        "herzogenaurach", "schwabach", "roth", "ansbach", "bamberg",
        "forchheim", "neumarkt", "amberg", "regensburg", "ingolstadt",
        "wuerzburg", "bayreuth", "schweinfurt", "coburg",
        "lauf", "zirndorf", "stein", "hersbruck", "altdorf", "weiden",
    ],
    "allow_remote": True,
}

# IT-Bezug: laengere Begriffe duerfen als Teilstring matchen ...
IT_STRONG = [
    "software", "informatik", "informationstechnik", "data", "daten",
    "analytics", "business intelligence", "cloud", "devops", "develop",
    "entwickl", "engineer", "digital", "system", "web", "cyber",
    "security", "automatisier", "automation", "netzwerk", "network",
    "frontend", "backend", "fullstack", "full stack", "python", "java",
    "kotlin", "script", "programmier", "datenbank", "database", "robot",
    "iot", "kuenstliche intelligenz", "kunstliche intelligenz",
    "artificial intelligence", "machine learning", "data science", "tech",
    "computer", "coding", "app-entwickl", "e-commerce", "ecommerce",
    "business analyst", "requirements", "it-support", "support",
]
# ... kurze/mehrdeutige Begriffe nur als eigenstaendiges Wort (Token).
IT_WORDS = {
    "it", "ki", "ai", "qa", "sap", "erp", "ml", "bi", "abap", "c#",
    "c++", ".net", "sql", "llm",
}

REMOTE_WORDS = ("remote", "home office", "homeoffice", "hybrid")


def get_filter_cfg(cfg: dict) -> dict:
    f = dict(DEFAULT_FILTER)
    for key, value in cfg.get("filter", {}).items():
        if isinstance(f.get(key), list) and isinstance(value, list):
            merged = list(f[key])
            for item in value:
                if item not in merged:
                    merged.append(item)
            f[key] = merged
        else:
            f[key] = value
    return f


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = (
        text.replace("Ã¤", "ae")
        .replace("Ã¶", "oe")
        .replace("Ã¼", "ue")
        .replace("ÃŸ", "ss")
    )
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _tokens(text: str) -> set:
    """Woerter aus Text (behaelt # + . fuer c#, .net, c++)."""
    return set(re.findall(r"[a-z0-9#.+]+", text.lower()))


def has_it_relevance(text: str) -> bool:
    low = normalize_text(text)
    if any(normalize_text(k) in low for k in IT_STRONG):
        return True
    return bool(_tokens(low) & IT_WORDS)


def is_relevant(job: dict, cfg: dict) -> tuple[bool, str]:
    """Prueft einen normalisierten Job. Rueckgabe: (relevant, Grund bei Ablehnung)."""
    f = get_filter_cfg(cfg)
    title = normalize_text(job.get("title", ""))
    company = job.get("company", "")
    location_raw = job.get("location", "")

    if not any(normalize_text(w) in title for w in f["require_title_any"]):
        return False, "keine Studenten-Rolle im Titel"

    if not has_it_relevance(f"{job.get('title', '')} {company} {job.get('description', '')} {job.get('textSnippet', '')}"):
        return False, "kein IT-Bezug"

    if not cfg.get("use_actor_radius"):
        location_low = str(location_raw or "").lower()
        if f["locations_any"] and not any(w in location_low for w in f["locations_any"]):
            if not (f.get("allow_remote", True) and any(w in location_low for w in REMOTE_WORDS)):
                return False, f"nicht Region: {location_raw[:60]}"

    return True, ""


def split_relevant(jobs: list[dict], cfg: dict) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Teilt Jobs in (relevante, aussortierte-mit-Grund)."""
    keep, dropped = [], []
    for job in jobs:
        ok, reason = is_relevant(job, cfg)
        (keep if ok else dropped).append(job if ok else (job, reason))
    return keep, dropped
