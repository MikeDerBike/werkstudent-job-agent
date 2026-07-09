"""Apify-Client: startet den StepStone-Actor (MVP-Schema mit query/includeDetails)
und laedt die Dataset-Ergebnisse."""
import requests

APIFY_BASE = "https://api.apify.com/v2"

PROXY = {
    "useApifyProxy": True,
    "apifyProxyGroups": ["RESIDENTIAL"],
    "apifyProxyCountry": "DE",
}


def build_query_list(cfg: dict):
    return list(cfg.get("queries", []))


def build_actor_input(cfg: dict, query: str) -> dict:
    inp = {
        "query": query,
        "maxResults": int(cfg.get("max_results", 100)),
        # includeDetails=true oeffnet JEDE Job-Seite einzeln -> teuer. Standard: aus.
        "includeDetails": bool(cfg.get("include_details", False)),
        "incrementalMode": bool(cfg.get("incremental_mode", False)),
        "skipReposts": bool(cfg.get("skip_reposts", False)),
        "excludeSponsored": bool(cfg.get("exclude_sponsored", False)),
        "proxyConfiguration": PROXY,
    }
    if cfg.get("bundesland"):
        inp["bundesland"] = cfg["bundesland"]
    else:
        if cfg.get("location"):
            inp["location"] = cfg["location"]
        if cfg.get("radius_km"):
            inp["radius"] = str(cfg["radius_km"])
    if cfg.get("sort"):
        inp["sort"] = cfg["sort"]
    return inp


class ApifyError(Exception):
    pass


def run_crawl(cfg: dict, timeout_s: int = 600) -> list[dict]:
    if cfg.get("mock_mode"):
        from .mock_data import MOCK_ITEMS

        return list(MOCK_ITEMS)

    token = cfg.get("apify_token")
    actor_id = cfg.get("apify_actor_id", "")
    if not token:
        raise ApifyError("Kein APIFY_TOKEN gesetzt. Bitte .env pruefen.")
    if not actor_id or "BITTE_EINTRAGEN" in actor_id:
        raise ApifyError("Keine apify_actor_id konfiguriert. Bitte in config.json pruefen.")

    actor_path = actor_id.replace("/", "~")
    queries = build_query_list(cfg) or [""]

    # Hartes Budget pro "Jobs suchen"-Klick, aufgeteilt auf die Queries.
    # Apify (Pay-per-Event) stoppt jeden Lauf bei maxTotalChargeUsd automatisch.
    total_budget = float(cfg.get("max_charge_eur", 0) or 0)
    per_run_budget = round(total_budget / len(queries), 3) if total_budget > 0 else 0

    all_items = []
    errors = []
    for query in queries:
        payload = build_actor_input(cfg, query)
        try:
            all_items.extend(
                _run_one_async(actor_path, token, payload, query, timeout_s, per_run_budget)
            )
        except ApifyError as e:
            errors.append(str(e))  # eine Query darf den Rest nicht killen
    # Nur wenn ALLE Queries scheitern, wird ein Fehler geworfen
    if errors and not all_items:
        raise ApifyError(" | ".join(errors))
    return all_items


def _run_one_async(actor_path, token, payload, query, timeout_s, max_charge_usd=0):
    """Startet einen Actor-Lauf asynchron, pollt bis fertig, laedt dann das Dataset.
    Umgeht das 300s-Limit des run-sync-Endpoints (HTTP 408 run-timeout-exceeded)."""
    import time

    # 1) Lauf starten (kehrt sofort zurueck). maxTotalChargeUsd = harte Kostengrenze.
    run_params = {"token": token}
    if max_charge_usd and max_charge_usd > 0:
        run_params["maxTotalChargeUsd"] = max_charge_usd
    resp = requests.post(
        f"{APIFY_BASE}/acts/{actor_path}/runs",
        params=run_params,
        json=payload,
        timeout=60,
    )
    if resp.status_code == 404:
        raise ApifyError("Actor nicht gefunden. Actor-ID in config.json pruefen.")
    if resp.status_code in (401, 403):
        raise ApifyError("Apify-Token ungueltig oder keine Berechtigung.")
    if not resp.ok:
        raise ApifyError(f"Apify-Fehler {resp.status_code} bei Query '{query}': {resp.text[:300]}")

    run = resp.json()["data"]
    run_id = run["id"]
    dataset_id = run["defaultDatasetId"]

    # 2) Pollen bis Endzustand (oder lokaler Timeout)
    deadline = time.time() + timeout_s
    status = run["status"]
    while status in ("READY", "RUNNING"):
        if time.time() > deadline:
            raise ApifyError(
                f"Zeitueberschreitung: Lauf fuer Query '{query}' nicht in {timeout_s}s fertig."
            )
        time.sleep(4)
        r = requests.get(
            f"{APIFY_BASE}/actor-runs/{run_id}", params={"token": token}, timeout=60
        )
        if r.ok:
            status = r.json()["data"]["status"]

    # ABORTED passiert auch, wenn die Budget-Grenze (maxTotalChargeUsd) greift.
    # Dann sind meist schon Teil-Ergebnisse im Dataset -> die laden wir trotzdem.
    # Nur bei echten Fehlerzustaenden ohne Ergebnisse wird abgebrochen.
    # 3) Dataset-Items laden
    r = requests.get(
        f"{APIFY_BASE}/datasets/{dataset_id}/items",
        params={"token": token, "format": "json", "clean": "true"},
        timeout=120,
    )
    if not r.ok:
        raise ApifyError(f"Konnte Ergebnisse fuer '{query}' nicht laden: {r.status_code}")
    data = r.json()
    if not isinstance(data, list):
        raise ApifyError(f"Unerwartetes Antwortformat von Apify: {type(data).__name__}")
    if not data and status not in ("SUCCEEDED", "ABORTED"):
        raise ApifyError(f"Lauf fuer Query '{query}' endete mit Status {status} (keine Ergebnisse).")
    return data
