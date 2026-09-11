"""Local SQLite persistence for schema snapshots."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Self

from driftwatch.models import SchemaSnapshot

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS snapshots (
    table_name TEXT PRIMARY KEY,
    snapshot_json TEXT NOT NULL,
    last_updated TEXT NOT NULL
)
"""

_UPSERT_SQL = """
INSERT INTO snapshots (table_name, snapshot_json, last_updated)
VALUES (?, ?, ?)
ON CONFLICT(table_name) DO UPDATE SET
    snapshot_json = excluded.snapshot_json,
    last_updated = excluded.last_updated
"""

_SELECT_SQL = """
SELECT snapshot_json FROM snapshots WHERE table_name = ?
"""


class SnapshotStore:
    """Persist the latest SchemaSnapshot per table in a local SQLite database.

    Only the most recent snapshot for each table_name is kept. Saving again for
    the same table overwrites the previous row — this store intentionally does
    not retain historical versions.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute(_CREATE_TABLE_SQL)
        self._conn.commit()

    def save_snapshot(self, snapshot: SchemaSnapshot) -> None:
        """Upsert ``snapshot`` keyed by its ``table_name``."""
        last_updated = datetime.now(UTC).isoformat()
        self._conn.execute(
            _UPSERT_SQL,
            (snapshot.table_name, snapshot.model_dump_json(), last_updated),
        )
        self._conn.commit()

    def get_latest_snapshot(self, table_name: str) -> SchemaSnapshot | None:
        """Return the stored snapshot for ``table_name``, or None if missing."""
        cursor = self._conn.execute(_SELECT_SQL, (table_name,))
        row = cursor.fetchone()
        if row is None:
            return None
        return SchemaSnapshot.model_validate_json(row[0])

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
