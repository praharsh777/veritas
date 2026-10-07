"""Incident history in SQLite, isolated per anonymous browser id (X-Client-Id).

Raw submitted text is NOT stored; only the redacted preview and the structured report.
Note: the client id is an unguessable random id kept in the visitor's browser. It separates visitors from each other;
it is not authentication.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from .config import settings
from .schemas import AnalysisReport

_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(settings.database_path, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute(
        """CREATE TABLE IF NOT EXISTS incidents(
            id TEXT PRIMARY KEY, created_at TEXT, category TEXT, category_label TEXT, risk_score INTEGER,
            risk_level TEXT, confidence INTEGER, kind TEXT, preview TEXT, feedback TEXT, report_json TEXT)"""
    )
    cols = {r["name"] for r in c.execute("PRAGMA table_info(incidents)")}
    if "client_id" not in cols:  # migrate older local databases
        c.execute("ALTER TABLE incidents ADD COLUMN client_id TEXT NOT NULL DEFAULT 'anon'")
    return c


def save(report: AnalysisReport, client_id: str = "anon") -> None:
    with _lock, _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO incidents(id, created_at, category, category_label, risk_score, risk_level, confidence,"
            " kind, preview, feedback, report_json, client_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (report.id, report.created_at, report.category, report.category_label, report.risk.risk_score,
             report.risk.risk_level, report.risk.confidence_score, report.input.kind, report.input.preview,
             report.feedback, report.model_dump_json(), client_id),
        )


def list_incidents(client_id: str = "anon", limit: int = 100) -> list[dict]:
    with _lock, _conn() as c:
        rows = c.execute(
            "SELECT id, created_at, category, category_label, risk_score, risk_level, confidence, kind, preview, feedback "
            "FROM incidents WHERE client_id=? ORDER BY created_at DESC LIMIT ?", (client_id, limit)).fetchall()
    return [dict(r) for r in rows]


def get(incident_id: str, client_id: str = "anon") -> Optional[AnalysisReport]:
    with _lock, _conn() as c:
        r = c.execute("SELECT report_json, feedback FROM incidents WHERE id=? AND client_id=?",
                      (incident_id, client_id)).fetchone()
    if not r:
        return None
    rep = AnalysisReport.model_validate_json(r["report_json"])
    rep.feedback = r["feedback"]
    return rep


def set_feedback(incident_id: str, outcome: str, note: str | None, client_id: str = "anon") -> bool:
    val = outcome + (f": {note}" if note else "")
    with _lock, _conn() as c:
        cur = c.execute("UPDATE incidents SET feedback=? WHERE id=? AND client_id=?", (val, incident_id, client_id))
        return cur.rowcount > 0


def delete(incident_id: str, client_id: str = "anon") -> None:
    with _lock, _conn() as c:
        c.execute("DELETE FROM incidents WHERE id=? AND client_id=?", (incident_id, client_id))


def clear(client_id: str = "anon") -> int:
    with _lock, _conn() as c:
        return c.execute("DELETE FROM incidents WHERE client_id=?", (client_id,)).rowcount
