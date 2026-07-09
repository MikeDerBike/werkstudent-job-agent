"""Duplikaterkennung nach Briefing-Prioritaet:
1. source_job_id, 2. canonicalUrl, 3. normalisierte company+title+location.
Wiedergesehene Jobs: last_seen_at aktualisieren, Status nicht zuruecksetzen.
Geaenderte Jobs: als "updated" markieren, kein neues Paket."""
from .db import JobRepository


def find_existing(repo: JobRepository, job: dict):
    row = repo.find_by_source_id(job["source"], job["source_job_id"])
    if row:
        return row
    row = repo.find_by_canonical_url(job["canonical_url"])
    if row:
        return row
    return repo.find_by_norm_key(job["norm_key"])


def process_jobs(repo: JobRepository, jobs: list[dict]) -> dict:
    """Verarbeitet normalisierte Jobs. Rueckgabe: {"new": [job_ids], "seen": n, "updated": n}."""
    result = {"new": [], "seen": 0, "updated": 0}
    for job in jobs:
        existing = find_existing(repo, job)
        if existing is None:
            job_id = repo.insert_job(job)
            result["new"].append(job_id)
        else:
            changed = bool(job["content_hash"]) and existing["content_hash"] != job["content_hash"]
            repo.touch_job(existing["id"], changed=changed)
            if changed:
                result["updated"] += 1
            else:
                result["seen"] += 1
    return result
