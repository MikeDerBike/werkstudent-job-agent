"""Paket-Generator: erstellt pro Job einen Bewerbungsordner mit allen Dateien."""
import re
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from pypdf import PdfReader, PdfWriter

from . import odt_letter, texts
from .db import JobRepository, now_iso


def safe_folder_name(company: str, title: str, max_len: int = 80) -> str:
    """Windows-sicherer Ordnername: Sonderzeichen raus, Leerzeichen -> Unterstrich, kuerzen."""
    raw = f"{date.today().isoformat()}_{company}_{title}"
    raw = re.sub(r"[<>:\"/\\|?*]", "", raw)
    raw = re.sub(r"\s+", "_", raw.strip())
    raw = re.sub(r"_+", "_", raw)
    return raw[:max_len].rstrip("._")


def _merge_pdfs(sources: list[Path], out_path: Path):
    """Haengt mehrere PDFs zu einem zusammen (Reihenfolge = Liste)."""
    writer = PdfWriter()
    for src in sources:
        src = Path(src)
        if not src.exists():
            continue
        for page in PdfReader(str(src)).pages:
            writer.add_page(page)
    with open(out_path, "wb") as f:
        writer.write(f)


def _write_pdf(path: Path, title: str, body: str):
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 16)]
    for para in body.split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 10))
    doc.build(story)


def _cv_pdf(path: Path, applicant: dict):
    """Einfacher CV-Platzhalter. Spaeter durch einen eigenen Lebenslauf ersetzen."""
    skills = ", ".join(applicant.get("skills", []))
    body = (
        f"{applicant['name']}\n"
        f"{applicant['city']} | {applicant['email']} | {applicant['phone']}\n\n"
        "Profil\n\n"
        f"Werkstudent im IT-Bereich, verfuegbar {applicant['available_from']}, "
        f"{applicant['weekly_hours']} pro Woche.\n\n"
        "Skills\n\n"
        f"{skills}\n\n"
        "Hinweis: Dies ist ein automatisch erstellter Platzhalter-Lebenslauf. "
        "Bitte durch die finale Version ersetzen (assets/lebenslauf.pdf wird bevorzugt verwendet)."
    )
    _write_pdf(path, "Lebenslauf", body)


def create_package(repo: JobRepository, job_row, cfg: dict) -> Path:
    """Erstellt den Bewerbungsordner mit den 7 Dateien aus dem Briefing."""
    job = dict(job_row)
    applicant = cfg["applicant"]
    folder = Path(cfg["packages_dir"]) / safe_folder_name(job["company"], job["title"])
    folder.mkdir(parents=True, exist_ok=True)

    # 01 Jobbeschreibung
    (folder / "01_Jobbeschreibung.md").write_text(
        f"# {job['title']}\n\n**Firma:** {job['company']}\n\n"
        f"**Link:** {job['canonical_url']}\n\n---\n\n{job['description']}\n",
        encoding="utf-8",
    )

    # 02 Stelleninfos
    (folder / "02_Stelleninfos.md").write_text(
        f"# Stelleninfos\n\n"
        f"- **Firma:** {job['company']}\n"
        f"- **Rolle:** {job['title']}\n"
        f"- **Ort:** {job['location']}\n"
        f"- **Quelle:** {job['source']}\n"
        f"- **Apply-Link:** {job['apply_url'] or '-'}\n"
        f"- **Job-Link:** {job['canonical_url'] or '-'}\n"
        f"- **E-Mail:** {job['contact_email'] or '-'}\n"
        f"- **Bewerbungsart:** {job['application_type']}\n"
        f"- **Gefunden am:** {job['first_seen_at']}\n",
        encoding="utf-8",
    )

    # 03 Lebenslauf: vorhandenes Template aus assets/ bevorzugen, sonst Platzhalter
    cv_path = folder / "03_Lebenslauf.pdf"
    template_cv = Path(cfg.get("base_dir")).parent / "assets" / "lebenslauf.pdf"
    if template_cv.exists():
        cv_path.write_bytes(template_cv.read_bytes())
    else:
        _cv_pdf(cv_path, applicant)

    # 04 Anschreiben: bevorzugt aus lokaler ODT-Vorlage via LibreOffice,
    # sonst Fallback auf einfaches reportlab-PDF.
    cover_path = folder / "04_Anschreiben.pdf"
    try:
        pdf = odt_letter.generate(cfg, job, applicant, folder)
    except Exception:  # noqa: BLE001 - Paketerstellung darf nie abbrechen
        pdf = None
    if pdf is None:
        _write_pdf(cover_path, f"Anschreiben - {job['company']}", texts.cover_letter_text(job, applicant))

    # 08 Komplette Bewerbung: Anschreiben + Lebenslauf zusammen als ein PDF
    combined_path = folder / "08_Bewerbung_komplett.pdf"
    try:
        _merge_pdfs([cover_path, cv_path], combined_path)
    except Exception:  # noqa: BLE001
        combined_path = None

    # 05 E-Mail-Vorlage
    email_path = folder / "05_Email_Vorlage.txt"
    email_path.write_text(
        f"Betreff: {texts.email_subject(applicant)}\n\n{texts.email_body(job, applicant)}\n",
        encoding="utf-8",
    )

    # 06 Portal-Antworten
    portal_path = folder / "06_Portal_Antworten.txt"
    portal_path.write_text(texts.portal_answers(job, applicant), encoding="utf-8")

    # 07 Status
    (folder / "07_Status.md").write_text(
        f"# Status\n\n- Paket erstellt: {now_iso()}\n- Beworben am: \n- Antwort: \n\n## Notizen\n\n",
        encoding="utf-8",
    )

    repo.set_folder(job["id"], str(folder))
    repo.add_application(
        job["id"],
        {
            "cv_pdf": str(cv_path),
            "cover_pdf": str(cover_path),
            "email_text": str(email_path),
            "portal_answers": str(portal_path),
        },
    )
    return folder
