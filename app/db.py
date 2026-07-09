"""SQLite-Datenmodell und Repository-Funktionen."""
import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    source TEXT,
    source_job_id TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    canonical_url TEXT,
    apply_url TEXT,
    application_type TEXT,
    contact_email TEXT,
    description TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    status TEXT,
    folder_path TEXT,
    content_hash TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY,
    job_id INTEGER,
    cv_pdf_path TEXT,
    cover_pdf_path TEXT,
    email_text_path TEXT,
    portal_answers_path TEXT,
    created_at TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_source_job_id ON jobs(source, source_job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_canonical_url ON jobs(canonical_url);
CREATE INDEX IF NOT EXISTS idx_jobs_content_hash ON jobs(content_hash);
"""


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class JobRepository:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # --- Suche fuer Duplikaterkennung ---

    def find_by_source_id(self, source: str, source_job_id: str):
        if not source_job_id:
            return None
        cur = self.conn.execute(
            "SELECT * FROM jobs WHERE source = ? AND source_job_id = ?",
            (source, source_job_id),
        )
        return cur.fetchone()

    def find_by_canonical_url(self, url: str):
        if not url:
            return None
        cur = self.conn.execute("SELECT * FROM jobs WHERE canonical_url = ?", (url,))
        return cur.fetchone()

    def find_by_norm_key(self, norm_key: str):
        """norm_key = normalisierte Kombination company|title|location (in content_hash-Spalte
        wird der Hash gespeichert; der Fallback-Vergleich laeuft ueber diese Query)."""
        cur = self.conn.execute(
            """SELECT * FROM jobs WHERE
               LOWER(REPLACE(company,' ','')) || '|' ||
               LOWER(REPLACE(title,' ','')) || '|' ||
               LOWER(REPLACE(location,' ','')) = ?""",
            (norm_key,),
        )
        return cur.fetchone()

    # --- Schreiben ---

    def insert_job(self, job: dict) -> int:
        ts = now_iso()
        cur = self.conn.execute(
            """INSERT INTO jobs (source, source_job_id, title, company, location,
                canonical_url, apply_url, application_type, contact_email, description,
                first_seen_at, last_seen_at, status, folder_path, content_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                job["source"], job["source_job_id"], job["title"], job["company"],
                job["location"], job["canonical_url"], job["apply_url"],
                job["application_type"], job["contact_email"], job["description"],
                ts, ts, "new", "", job["content_hash"],
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def touch_job(self, job_id: int, changed: bool = False):
        """Job wieder gesehen: last_seen_at aktualisieren, Status NICHT zuruecksetzen.
        Bei inhaltlicher Aenderung nur markieren, kein neues Paket."""
        if changed:
            self.conn.execute(
                "UPDATE jobs SET last_seen_at = ?, status = CASE WHEN status = 'new' THEN 'new' ELSE 'updated' END WHERE id = ?",
                (now_iso(), job_id),
            )
        else:
            self.conn.execute(
                "UPDATE jobs SET last_seen_at = ? WHERE id = ?", (now_iso(), job_id)
            )
        self.conn.commit()

    def set_status(self, job_id: int, status: str):
        self.conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        self.conn.commit()

    def set_folder(self, job_id: int, folder_path: str):
        self.conn.execute(
            "UPDATE jobs SET folder_path = ?, status = 'package_created' WHERE id = ?",
            (folder_path, job_id),
        )
        self.conn.commit()

    def add_application(self, job_id: int, paths: dict):
        self.conn.execute(
            """INSERT INTO applications (job_id, cv_pdf_path, cover_pdf_path,
                email_text_path, portal_answers_path, created_at)
               VALUES (?,?,?,?,?,?)""",
            (
                job_id,
                paths.get("cv_pdf", ""),
                paths.get("cover_pdf", ""),
                paths.get("email_text", ""),
                paths.get("portal_answers", ""),
                now_iso(),
            ),
        )
        self.conn.commit()

    # --- Lesen fuers Dashboard ---

    def all_jobs(self):
        cur = self.conn.execute(
            "SELECT * FROM jobs WHERE status != 'ignored' ORDER BY first_seen_at DESC"
        )
        return cur.fetchall()

    def jobs_by_status(self, status: str):
        cur = self.conn.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY first_seen_at DESC",
            (status,),
        )
        return cur.fetchall()

    def counts(self) -> dict:
        cur = self.conn.execute(
            """SELECT
                 SUM(CASE WHEN status IN ('new','updated') THEN 1 ELSE 0 END) AS new_jobs,
                 SUM(CASE WHEN status NOT IN ('new','ignored') THEN 1 ELSE 0 END) AS known_jobs,
                 SUM(CASE WHEN folder_path != '' AND status != 'ignored' THEN 1 ELSE 0 END) AS packages,
                 SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) AS applied_jobs,
                 SUM(CASE WHEN status = 'ignored' THEN 1 ELSE 0 END) AS ignored_jobs
               FROM jobs"""
        )
        row = cur.fetchone()
        return {
            "new": row["new_jobs"] or 0,
            "known": row["known_jobs"] or 0,
            "packages": row["packages"] or 0,
            "applied": row["applied_jobs"] or 0,
            "ignored": row["ignored_jobs"] or 0,
        }
