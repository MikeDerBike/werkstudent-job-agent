"""Anschreiben aus lokaler ODT-Vorlage (templates/anschreiben.odt) fuellen und
via LibreOffice headless in PDF wandeln. Design/Layout bleibt erhalten,
nur die Platzhalter {{FIRMA}}, {{ROLLE}}, {{OPENER}}, {{FIT}} werden ersetzt."""
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def find_soffice(cfg: dict | None = None):
    """Sucht die soffice.exe (config 'soffice_path' hat Vorrang)."""
    if cfg and cfg.get("soffice_path"):
        p = Path(cfg["soffice_path"])
        if p.exists():
            return str(p)
    for c in SOFFICE_CANDIDATES:
        if Path(c).exists():
            return c
    return shutil.which("soffice") or shutil.which("libreoffice")


def _build_tokens(job: dict, applicant: dict) -> dict:
    firma = job["company"]
    rolle = job["title"]
    ort = job.get("location", "")
    opener = (
        f"mit großem Interesse habe ich Ihre Ausschreibung für die Werkstudentenstelle als "
        f"{rolle} bei {firma}" + (f" in {ort}" if ort else "") + " gelesen. Besonders reizt mich "
        "die Verbindung aus Softwareentwicklung, Automatisierung und modernen digitalen Tools."
    )
    fit = (
        f"Die Stelle bei {firma} passt deshalb sehr gut zu meinen Interessen. Ich arbeite mich "
        "schnell in neue Themen ein, denke analytisch und bringe eine hohe Lernbereitschaft mit."
    )
    return {
        "{{FIRMA}}": firma,
        "{{ROLLE}}": rolle,
        "{{OPENER}}": opener,
        "{{FIT}}": fit,
    }


def fill_template(template_odt: Path, job: dict, applicant: dict, out_odt: Path) -> Path:
    """Ersetzt die Platzhalter im content.xml und schreibt ein neues ODT."""
    with zipfile.ZipFile(template_odt) as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}

    xml = data["content.xml"].decode("utf-8")
    for token, value in _build_tokens(job, applicant).items():
        xml = xml.replace(token, escape(value))
    data["content.xml"] = xml.encode("utf-8")

    out_odt = Path(out_odt)
    if out_odt.exists():
        out_odt.unlink()
    with zipfile.ZipFile(out_odt, "w", zipfile.ZIP_DEFLATED) as z:
        # mimetype muss als erster Eintrag und unkomprimiert stehen
        z.writestr("mimetype", data["mimetype"], compress_type=zipfile.ZIP_STORED)
        for n in names:
            if n == "mimetype":
                continue
            z.writestr(n, data[n])
    return out_odt


def odt_to_pdf(soffice: str, odt_path: Path, out_dir: Path) -> Path:
    """Wandelt ODT via LibreOffice headless in PDF. Nutzt ein temporaeres
    Nutzerprofil, damit es auch klappt, wenn LibreOffice gerade offen ist."""
    odt_path = Path(odt_path)
    out_dir = Path(out_dir)
    profile = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    try:
        cmd = [
            soffice, "--headless", "--norestore", "--nologo", "--nolockcheck",
            f"-env:UserInstallation={profile.as_uri()}",
            "--convert-to", "pdf", "--outdir", str(out_dir), str(odt_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
        pdf = out_dir / (odt_path.stem + ".pdf")
        if not pdf.exists():
            raise RuntimeError(
                f"LibreOffice hat kein PDF erzeugt (rc={proc.returncode}): "
                f"{proc.stderr.decode('utf-8','ignore')[:300]}"
            )
        return pdf
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def generate(cfg: dict, job: dict, applicant: dict, folder: Path):
    """Erstellt 04_Anschreiben.odt + 04_Anschreiben.pdf aus der Vorlage.
    Gibt den PDF-Pfad zurueck oder None, wenn Vorlage/LibreOffice fehlen
    (dann faellt der Packager auf das reportlab-PDF zurueck)."""
    template = Path(cfg["root_dir"]) / "templates" / "anschreiben.odt"
    soffice = find_soffice(cfg)
    if not template.exists() or not soffice:
        return None
    odt_out = fill_template(template, job, applicant, Path(folder) / "04_Anschreiben.odt")
    return odt_to_pdf(soffice, odt_out, folder)
