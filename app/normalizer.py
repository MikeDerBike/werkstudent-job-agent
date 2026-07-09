"""Normalizer: StepStone-/Apify-Felder -> internes Job-Objekt + Bewerbungsart-Erkennung."""
import hashlib
import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
MAILTO_RE = re.compile(r"mailto:([^\s\"'>)\]]+)")


def _first(*values) -> str:
    for v in values:
        if v:
            return str(v).strip()
    return ""


def _clean_url(url: str) -> str:
    """Verwirft nutzlose Platzhalter-URLs (nur Domain, kein echter Pfad),
    z.B. 'https://www.stepstone.de'. Nur URLs mit echtem Pfad werden behalten."""
    url = (url or "").strip()
    if not url:
        return ""
    # Pfad nach der Domain isolieren: alles ab dem 3. Slash
    m = re.match(r"^https?://[^/]+(/.*)?$", url)
    if not m:
        return url  # kein http(s)-Schema (z.B. mailto) -> unveraendert lassen
    path = m.group(1) or ""
    return url if path.strip("/") else ""


def _extract_email(*texts) -> str:
    for text in texts:
        if not text:
            continue
        m = MAILTO_RE.search(text)
        if m:
            return m.group(1).strip().rstrip(".,;")
        m = EMAIL_RE.search(text)
        if m:
            return m.group(0)
    return ""


def detect_application_type(item: dict, description: str) -> tuple[str, str]:
    """Regeln aus dem Briefing:
    - E-Mail-Bewerbung -> "email" + contact_email
    - applyUrl/portalUrl vorhanden oder directApply true -> "portal"
    - sonst "unknown" (canonicalUrl als Fallback im Dashboard)

    Bevorzugt die strukturierten E-Mail-Felder des Actors, dann Regex ueber den Text.
    """
    # 1) Strukturierte Felder des Actors
    email = _first(item.get("applyEmail"), item.get("contactEmail"))
    if not email:
        extracted = item.get("extractedEmails")
        if isinstance(extracted, list) and extracted:
            email = str(extracted[0]).strip()
    # 2) Fallback: Regex ueber Beschreibung / Textabschnitte
    if not email:
        sections = item.get("textSections")
        sections_text = " ".join(str(s) for s in sections) if sections else ""
        email = _extract_email(item.get("descriptionMarkdown"), sections_text, description)

    if email:
        return "email", email
    if item.get("applyUrl") or item.get("portalUrl") or item.get("directApply"):
        return "portal", ""
    return "unknown", ""


def norm_key(company: str, title: str, location: str) -> str:
    def n(s: str) -> str:
        return (s or "").lower().replace(" ", "")
    return f"{n(company)}|{n(title)}|{n(location)}"


def content_hash(title: str, company: str, description: str) -> str:
    snippet = (description or "")[:500]
    raw = f"{title}|{company}|{snippet}".lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize(item: dict) -> dict:
    """Wandelt ein Apify-Dataset-Item in das interne Job-Objekt um."""
    title = _first(item.get("title"))
    company = _first(item.get("company"), item.get("companyName"))
    location = _first(item.get("location"), item.get("city"))
    description = _first(
        item.get("descriptionMarkdown"),
        item.get("description"),
        item.get("textSnippet"),
    )
    app_type, email = detect_application_type(item, description)
    return {
        "source": "stepstone",
        "source_job_id": _first(item.get("jobId"), item.get("id")),
        "title": title,
        "company": company,
        "location": location,
        "canonical_url": _first(item.get("canonicalUrl"), item.get("sourceUrl"), item.get("url")),
        "apply_url": _clean_url(_first(item.get("applyUrl"), item.get("portalUrl"))),
        "application_type": app_type,
        "contact_email": email,
        "description": description,
        "content_hash": content_hash(title, company, description),
        "norm_key": norm_key(company, title, location),
    }
