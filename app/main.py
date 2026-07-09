"""Werkstudent Job Agent - Dashboard (CustomTkinter).

Start:  python -m app.main
"""
import logging
import os
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from . import apify_client, dedupe, filters, normalizer, packager, texts
from .config import load_config
from .db import JobRepository

STATUS_LABELS = {
    "new": "Neu",
    "updated": "Aktualisiert",
    "known": "Bekannt",
    "package_created": "Paket erstellt",
    "applied": "Beworben",
    "ignored": "Ignoriert",
}

APP_TYPE_LABELS = {"email": "E-Mail", "portal": "Portal", "unknown": "Unbekannt"}

COLORS = {
    "bg": "#0f1218",
    "panel": "#171b23",
    "panel_alt": "#1d232d",
    "panel_soft": "#232a35",
    "border": "#2d3542",
    "border_soft": "#26303d",
    "text": "#eef2f7",
    "muted": "#a6adbb",
    "subtle": "#737d8c",
    "accent": "#d7b56d",
    "accent_hover": "#e2c77f",
    "accent_text": "#17130a",
    "danger": "#b45b5b",
    "danger_hover": "#c56b6b",
    "success": "#5d9b70",
    "success_hover": "#6bae7f",
}

STATUS_STYLES = {
    "new": ("#6f4c22", "#f7d58a"),
    "updated": ("#6f4c22", "#f7d58a"),
    "known": ("#2d3542", COLORS["muted"]),
    "package_created": ("#263b55", "#b9d7ff"),
    "applied": ("#244a31", "#a9e4b8"),
    "ignored": ("#3a3f4b", "#bcc3cf"),
}

APP_TYPE_STYLES = {
    "email": ("#4b355b", "#e7c8ff"),
    "portal": ("#263f5e", "#c7dcff"),
    "unknown": ("#353b45", "#c5cad3"),
}

PRIMARY_BUTTON = {
    "fg_color": COLORS["accent"],
    "hover_color": COLORS["accent_hover"],
    "text_color": COLORS["accent_text"],
}

SECONDARY_BUTTON = {
    "fg_color": COLORS["panel_soft"],
    "hover_color": "#303846",
    "text_color": COLORS["text"],
}

QUIET_BUTTON = {
    "fg_color": "transparent",
    "hover_color": COLORS["panel_soft"],
    "text_color": COLORS["muted"],
}


def setup_logging(logs_dir: Path) -> logging.Logger:
    logger = logging.getLogger("jobagent")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(
            logs_dir / f"{datetime.now():%Y-%m-%d}.log", encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(fh)
    return logger


def open_path(path: str):
    if path and Path(path).exists():
        os.startfile(path)  # noqa: S606 - gewollt, Windows Explorer/Standard-App


def format_date(value: str) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%d.%m.%Y")
    except ValueError:
        return value[:10]


def clamp_text(value: str, limit: int = 260) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


class JobCard(ctk.CTkFrame):
    def __init__(self, master, app, job):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        self.app = app
        self.job = dict(job)
        self._build()

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.app.set_status(f"Kopiert: {text[:60]}...")

    def _badge(self, parent, text: str, fg: str, text_color: str = "white"):
        return ctk.CTkLabel(
            parent, text=f"  {text}  ", fg_color=fg, text_color=text_color,
            corner_radius=6, font=ctk.CTkFont(size=11, weight="bold"), height=22,
        )

    def _build(self):
        j = self.job
        self.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        head.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(head, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="ew")
        title_block.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_block,
            text=j["title"],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
            wraplength=680,
        ).grid(row=0, column=0, sticky="ew")

        meta_text = (
            f"{j['company']} | {j['location']} | "
            f"gefunden: {format_date(j['first_seen_at'])}"
        )
        ctk.CTkLabel(
            title_block,
            text=meta_text,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(3, 0))

        folder = j["folder_path"]
        folder_btn = ctk.CTkButton(
            head,
            text="Ordner",
            width=82,
            height=32,
            corner_radius=8,
            command=lambda: open_path(folder),
            **SECONDARY_BUTTON,
        )
        if not folder:
            folder_btn.configure(state="disabled")
        folder_btn.grid(row=0, column=1, padx=(12, 0))

        badges = ctk.CTkFrame(self, fg_color="transparent")
        badges.grid(row=1, column=0, sticky="w", padx=16, pady=(10, 0))
        app_fg, app_text = APP_TYPE_STYLES.get(
            j["application_type"], APP_TYPE_STYLES["unknown"]
        )
        self._badge(
            badges,
            APP_TYPE_LABELS.get(j["application_type"], "Unbekannt"),
            app_fg,
            app_text,
        ).grid(row=0, column=0, padx=(0, 6))
        status_fg, status_text = STATUS_STYLES.get(
            j["status"], STATUS_STYLES["known"]
        )
        self._badge(
            badges,
            STATUS_LABELS.get(j["status"], j["status"]),
            status_fg,
            status_text,
        ).grid(row=0, column=1, padx=(0, 6))

        preview = clamp_text(j.get("description", ""))
        if preview:
            ctk.CTkLabel(
                self,
                text=preview,
                text_color=COLORS["muted"],
                anchor="w",
                justify="left",
                wraplength=820,
            ).grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 0))

        self._build_apply_row(row=3)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", padx=12, pady=(8, 12))

        cover_path = str(Path(folder) / "04_Anschreiben.pdf") if folder else ""
        job_path = str(Path(folder) / "01_Jobbeschreibung.md") if folder else ""
        items = [
            ("Anschreiben", lambda: open_path(cover_path), bool(folder)),
            ("Jobbeschreibung", lambda: open_path(job_path), bool(folder)),
            ("Beworben", lambda: self.app.change_status(j["id"], "applied"), True),
            ("Hide", lambda: self.app.change_status(j["id"], "ignored"), True),
            ("Paket neu", lambda: self.app.rebuild_package(j["id"]), True),
        ]
        for i, (label, cmd, enabled) in enumerate(items):
            style = SECONDARY_BUTTON if label in {"Beworben", "Paket neu"} else QUIET_BUTTON
            if label == "Hide":
                style = {**QUIET_BUTTON, "text_color": "#d3a0a0"}
            btn = ctk.CTkButton(
                actions,
                text=label,
                command=cmd,
                width=112 if label == "Jobbeschreibung" else 94,
                height=30,
                corner_radius=8,
                **style,
            )
            if not enabled:
                btn.configure(state="disabled")
            btn.grid(row=0, column=i, padx=3)

    def _build_apply_row(self, row: int):
        j = self.job
        frame = ctk.CTkFrame(self, fg_color=COLORS["panel_alt"], corner_radius=10)
        frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(10, 0))
        frame.grid_columnconfigure(1, weight=1)

        applicant = self.app.cfg["applicant"]

        if j["application_type"] == "email" and j["contact_email"]:
            subject = texts.email_subject(applicant)
            body = texts.email_body(j, applicant)
            self._copy_row(frame, 0, "E-Mail an:", j["contact_email"])
            self._copy_row(frame, 1, "Betreff:", subject)
            box = ctk.CTkTextbox(
                frame,
                height=104,
                fg_color=COLORS["bg"],
                text_color=COLORS["text"],
                border_width=1,
                border_color=COLORS["border"],
            )
            box.insert("1.0", body)
            box.configure(state="disabled")
            box.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(8, 0))
            ctk.CTkButton(
                frame,
                text="Mailtext kopieren",
                width=150,
                height=30,
                corner_radius=8,
                command=lambda: self._copy(body),
                **SECONDARY_BUTTON,
            ).grid(row=3, column=0, sticky="w", padx=10, pady=(8, 10))
        else:
            link = j["apply_url"] or j["canonical_url"] or ""
            label = "Portal-Link:" if j["application_type"] == "portal" else "Job-Link (Fallback):"
            if link:
                self._copy_row(frame, 0, label, link, is_link=True)
            if j["folder_path"]:
                portal_file = Path(j["folder_path"]) / "06_Portal_Antworten.txt"
                if portal_file.exists():
                    content = portal_file.read_text(encoding="utf-8")
                    box = ctk.CTkTextbox(
                        frame,
                        height=104,
                        fg_color=COLORS["bg"],
                        text_color=COLORS["text"],
                        border_width=1,
                        border_color=COLORS["border"],
                    )
                    box.insert("1.0", content)
                    box.configure(state="disabled")
                    box.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(8, 0))
                    ctk.CTkButton(
                        frame,
                        text="Portal-Antworten kopieren",
                        width=190,
                        height=30,
                        corner_radius=8,
                        command=lambda: self._copy(content),
                        **SECONDARY_BUTTON,
                    ).grid(row=3, column=0, sticky="w", padx=10, pady=(8, 10))

    def _copy_row(self, parent, row: int, label: str, value: str, is_link: bool = False):
        ctk.CTkLabel(
            parent,
            text=label,
            width=118,
            anchor="w",
            text_color=COLORS["muted"],
        ).grid(
            row=row, column=0, sticky="w", padx=(10, 4), pady=(10 if row == 0 else 4, 0)
        )
        entry = ctk.CTkEntry(
            parent,
            fg_color=COLORS["bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        entry.insert(0, value)
        entry.configure(state="readonly")
        entry.grid(row=row, column=1, sticky="ew", padx=4, pady=(10 if row == 0 else 4, 0))
        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.grid(row=row, column=2, sticky="e", padx=(0, 10), pady=(10 if row == 0 else 4, 0))
        ctk.CTkButton(
            btns,
            text="Kopieren",
            width=82,
            height=28,
            corner_radius=8,
            command=lambda: self._copy(value),
            **SECONDARY_BUTTON,
        ).grid(
            row=0, column=0, padx=2
        )
        if is_link:
            ctk.CTkButton(
                btns,
                text="Oeffnen",
                width=78,
                height=28,
                corner_radius=8,
                command=lambda: webbrowser.open(value),
                **QUIET_BUTTON,
            ).grid(row=0, column=1, padx=2)


class ArchiveJobRow(ctk.CTkFrame):
    def __init__(self, master, app, job, current_status: str):
        super().__init__(
            master,
            corner_radius=10,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        self.app = app
        self.job = dict(job)
        self.current_status = current_status
        self._build()

    def _set_status(self, status: str):
        self.app.change_status(self.job["id"], status)

    def _restore_status(self) -> str:
        return "package_created" if self.job["folder_path"] else "known"

    def _build(self):
        j = self.job
        self.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text=j["title"],
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
            wraplength=420,
        ).grid(row=0, column=0, sticky="ew")

        app_type = APP_TYPE_LABELS.get(j["application_type"], "Unbekannt")
        meta = (
            f"{j['company']} | {j['location']} | {app_type} | "
            f"gefunden: {format_date(j['first_seen_at'])}"
        )
        ctk.CTkLabel(info, text=meta, anchor="w", text_color=COLORS["muted"]).grid(
            row=1, column=0, sticky="ew", pady=(3, 0)
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e", padx=(0, 12), pady=10)

        folder = j["folder_path"]
        folder_btn = ctk.CTkButton(
            actions, text="Ordner", width=76, height=28,
            command=lambda: open_path(folder),
            corner_radius=8,
            **SECONDARY_BUTTON,
        )
        if not folder:
            folder_btn.configure(state="disabled")
        folder_btn.grid(row=0, column=0, padx=3)

        link = j["apply_url"] or j["canonical_url"] or ""
        link_btn = ctk.CTkButton(
            actions, text="Link", width=58, height=28,
            corner_radius=8,
            command=lambda: webbrowser.open(link),
            **QUIET_BUTTON,
        )
        if not link:
            link_btn.configure(state="disabled")
        link_btn.grid(row=0, column=1, padx=3)

        if self.current_status == "ignored":
            ctk.CTkButton(
                actions,
                text="Wieder anzeigen",
                width=112,
                height=28,
                corner_radius=8,
                fg_color=COLORS["success"],
                hover_color=COLORS["success_hover"],
                command=lambda: self._set_status(self._restore_status()),
            ).grid(row=0, column=2, padx=3)
            ctk.CTkButton(
                actions,
                text="Beworben",
                width=82,
                height=28,
                corner_radius=8,
                command=lambda: self._set_status("applied"),
                **SECONDARY_BUTTON,
            ).grid(row=0, column=3, padx=3)
        else:
            ctk.CTkButton(
                actions,
                text="Hide",
                width=70,
                height=28,
                corner_radius=8,
                command=lambda: self._set_status("ignored"),
                **{**QUIET_BUTTON, "text_color": "#d3a0a0"},
            ).grid(row=0, column=2, padx=3)


class ArchiveWindow(ctk.CTkToplevel):
    VIEW_TO_STATUS = {"Beworben": "applied", "Hide": "ignored"}
    STATUS_TO_VIEW = {value: key for key, value in VIEW_TO_STATUS.items()}

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_status = "applied"
        self.title("Beworbene und ausgeblendete Stellen")
        self.geometry("900x620")
        self.minsize(820, 460)
        self.configure(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        header = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Beworben / Hide",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 0))

        self.segment = ctk.CTkSegmentedButton(
            header,
            values=list(self.VIEW_TO_STATUS.keys()),
            command=self._switch_view,
            selected_color="#303846",
            selected_hover_color="#3b4656",
            unselected_color=COLORS["panel_alt"],
            unselected_hover_color="#303846",
            text_color=COLORS["text"],
            height=34,
        )
        self.segment.grid(row=0, column=1, sticky="e", padx=14, pady=(14, 0))

        self.summary_label = ctk.CTkLabel(
            header, text="", anchor="w", text_color=COLORS["muted"]
        )
        self.summary_label.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(6, 14)
        )

        self.rows = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"])
        self.rows.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.rows.grid_columnconfigure(0, weight=1)
        self.segment.set(self.STATUS_TO_VIEW[self.current_status])

    def _switch_view(self, view: str):
        self.current_status = self.VIEW_TO_STATUS[view]
        self.refresh()

    def _close(self):
        self.app.archive_window = None
        self.destroy()

    def refresh(self):
        for widget in self.rows.winfo_children():
            widget.destroy()

        jobs = self.app.repo.jobs_by_status(self.current_status)
        view = self.STATUS_TO_VIEW[self.current_status]
        self.summary_label.configure(text=f"{view}: {len(jobs)} Stellen")

        if not jobs:
            empty = (
                "Noch keine Jobs als beworben markiert."
                if self.current_status == "applied"
                else "Noch keine Jobs auf Hide/Ignorieren gestellt."
            )
            ctk.CTkLabel(self.rows, text=empty, text_color="#a6adbb").grid(
                row=0, column=0, pady=36
            )
            return

        for i, job in enumerate(jobs):
            row = ArchiveJobRow(self.rows, self.app, job, self.current_status)
            row.grid(row=i, column=0, sticky="ew", pady=5, padx=4)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Werkstudent Job Agent")
        self.geometry("1080x860")
        self.minsize(920, 640)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS["bg"])

        self.cfg = load_config()
        self.logger = setup_logging(self.cfg["logs_dir"])
        self.repo = JobRepository(self.cfg["db_path"])
        self.crawling = False
        self.archive_window = None
        self.metric_values = {}

        self._build_header()
        self.job_list = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"])
        self.job_list.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.job_list.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.refresh()

    def _metric_tile(self, parent, column: int, key: str, label: str, color: str):
        tile = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_alt"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        tile.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        tile.grid_columnconfigure(0, weight=1)
        value = ctk.CTkLabel(
            tile,
            text="0",
            text_color=color,
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        )
        value.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            tile,
            text=label,
            text_color=COLORS["muted"],
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.metric_values[key] = value

    def _build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        header.grid_columnconfigure(0, weight=1)

        title_group = ctk.CTkFrame(header, fg_color="transparent")
        title_group.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        title_group.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            title_group,
            text="Werkstudent Job Agent",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self.counter_label = ctk.CTkLabel(
            title_group,
            text="Bewerbungspakete, Status und Links an einem Ort.",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        self.counter_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=1, sticky="e", padx=16, pady=(14, 0))
        self.search_btn = ctk.CTkButton(
            controls,
            text="Jobs suchen",
            width=150,
            height=38,
            corner_radius=9,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_crawl,
            **PRIMARY_BUTTON,
        )
        self.search_btn.grid(row=0, column=0, padx=(0, 8))
        self.archive_btn = ctk.CTkButton(
            controls,
            text="Beworben / Hide",
            width=170,
            height=38,
            corner_radius=9,
            command=self.open_archive,
            **SECONDARY_BUTTON,
        )
        self.archive_btn.grid(row=0, column=1)

        metrics = ctk.CTkFrame(header, fg_color="transparent")
        metrics.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 16))
        for col in range(5):
            metrics.grid_columnconfigure(col, weight=1)
        self._metric_tile(metrics, 0, "new", "Neu / aktualisiert", "#f0c978")
        self._metric_tile(metrics, 1, "known", "Bekannt", "#cbd3df")
        self._metric_tile(metrics, 2, "packages", "Pakete", "#b9d7ff")
        self._metric_tile(metrics, 3, "applied", "Beworben", "#a9e4b8")
        self._metric_tile(metrics, 4, "ignored", "Hide", "#d4b2b2")

        initial = (
            "MOCK-MODUS aktiv: 'Jobs suchen' liefert Beispiel-Jobs (config.json: mock_mode)."
            if self.cfg.get("mock_mode") else "Bereit."
        )
        self.status_label = ctk.CTkLabel(
            self,
            text=initial,
            anchor="w",
            text_color=COLORS["muted"],
            fg_color=COLORS["panel_alt"],
            corner_radius=8,
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def refresh(self):
        counts = self.repo.counts()
        for key, label in self.metric_values.items():
            label.configure(text=str(counts[key]))
        self.counter_label.configure(text=f"Zuletzt aktualisiert: {datetime.now():%H:%M}")
        self.archive_btn.configure(
            text=f"Beworben / Hide: {counts['applied']} / {counts['ignored']}"
        )
        for widget in self.job_list.winfo_children():
            widget.destroy()
        jobs = self.repo.all_jobs()
        if not jobs:
            empty = ctk.CTkFrame(
                self.job_list,
                fg_color=COLORS["panel"],
                corner_radius=12,
                border_width=1,
                border_color=COLORS["border_soft"],
            )
            empty.grid(row=0, column=0, sticky="ew", pady=18, padx=4)
            empty.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                empty,
                text="Noch keine Jobs im Dashboard",
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=18, weight="bold"),
            ).grid(row=0, column=0, pady=(28, 4))
            ctk.CTkLabel(
                empty,
                text="Klicke auf 'Jobs suchen', um den ersten Crawl zu starten.",
                text_color=COLORS["muted"],
            ).grid(row=1, column=0, pady=(0, 28))
        for i, job in enumerate(jobs):
            card = JobCard(self.job_list, self, job)
            card.grid(row=i, column=0, sticky="ew", pady=7, padx=4)

    # --- Aktionen ---

    def change_status(self, job_id: int, status: str):
        self.repo.set_status(job_id, status)
        self.set_status(f"Status gesetzt: {STATUS_LABELS.get(status, status)}")
        self.refresh()
        self.refresh_archive()

    def open_archive(self):
        if self.archive_window is not None and self.archive_window.winfo_exists():
            self.archive_window.refresh()
            self.archive_window.lift()
            self.archive_window.focus()
            return
        self.archive_window = ArchiveWindow(self)
        self.archive_window.lift()
        self.archive_window.focus()

    def refresh_archive(self):
        if self.archive_window is not None and self.archive_window.winfo_exists():
            self.archive_window.refresh()

    def rebuild_package(self, job_id: int):
        row = self.repo.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row:
            folder = packager.create_package(self.repo, row, self.cfg)
            self.set_status(f"Paket neu erstellt: {folder}")
            self.refresh()
            self.refresh_archive()

    def start_crawl(self):
        if self.crawling:
            return
        self.crawling = True
        self.search_btn.configure(state="disabled", text="Suche laeuft...")
        self.set_status("Apify-Crawl gestartet, das kann einige Minuten dauern...")
        threading.Thread(target=self._crawl_worker, daemon=True).start()

    def _crawl_worker(self):
        try:
            items = apify_client.run_crawl(self.cfg)
            self.logger.info("Apify lieferte %d Items", len(items))
            jobs = [normalizer.normalize(item) for item in items]
            jobs = [j for j in jobs if j["title"] and j["company"]]

            # Relevanzfilter: nur Werkstudent+IT in der Region (oder remote)
            jobs, dropped = filters.split_relevant(jobs, self.cfg)
            for job, reason in dropped:
                self.logger.info(
                    "Aussortiert (%s): %s | %s", reason, job["title"], job["company"]
                )

            result = dedupe.process_jobs(self.repo, jobs)

            packages = 0
            for job_id in result["new"]:
                row = self.repo.conn.execute(
                    "SELECT * FROM jobs WHERE id = ?", (job_id,)
                ).fetchone()
                packager.create_package(self.repo, row, self.cfg)
                packages += 1

            msg = (
                f"Fertig: {len(result['new'])} neue Jobs, {result['seen']} bekannte, "
                f"{result['updated']} aktualisierte, {packages} Pakete erstellt, "
                f"{len(dropped)} aussortiert (nicht IT/Region)."
            )
            self.logger.info(msg)
            self.after(0, lambda: self._crawl_done(msg))
        except apify_client.ApifyError as e:
            self.logger.error("Apify-Fehler: %s", e)
            self.after(0, lambda: self._crawl_done(f"Fehler: {e}"))
        except Exception as e:  # noqa: BLE001 - UI soll nie abstuerzen
            self.logger.exception("Unerwarteter Fehler beim Crawl")
            self.after(0, lambda: self._crawl_done(f"Unerwarteter Fehler: {e}"))

    def _crawl_done(self, msg: str):
        self.crawling = False
        self.search_btn.configure(state="normal", text="Jobs suchen")
        self.set_status(msg)
        self.refresh()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
