"""SQLite database initialization and session management."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.core.config import settings

def resolve_database_path(database_url: str) -> Path:
    """Resolve relative SQLite URLs against the backend directory, not process CWD."""
    path = Path(database_url.removeprefix("sqlite:///")).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return path.resolve()


DB_PATH = resolve_database_path(settings.database_url)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    request TEXT NOT NULL,
    intent TEXT,
    entities TEXT,
    evidence TEXT,
    reasoning TEXT,
    proposed_actions TEXT,
    policy_result TEXT,
    risk_level TEXT,
    autonomy_decision TEXT,
    execution_results TEXT,
    verification_results TEXT,
    final_response TEXT,
    status TEXT DEFAULT 'PENDING',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS actions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    arguments TEXT,
    reason TEXT,
    evidence_ids TEXT,
    risk_level TEXT,
    requires_approval INTEGER DEFAULT 0,
    status TEXT DEFAULT 'PENDING',
    execution_result TEXT,
    verification_result TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'PENDING',
    decided_by TEXT,
    decided_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES runs(id),
    FOREIGN KEY (action_id) REFERENCES actions(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    data TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
"""


def init_db() -> None:
    """Create database and tables if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def get_db():
    """Yield a sqlite3 connection with row_factory set."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
