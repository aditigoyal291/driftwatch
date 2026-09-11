"""Tests for SnapshotStore SQLite persistence."""

from pathlib import Path

from driftwatch.models import ColumnSpec, SchemaSnapshot
from driftwatch.storage import SnapshotStore


def _sample_snapshot(
    table_name: str = "deals",
    *,
    data_type: str = "int",
) -> SchemaSnapshot:
    return SchemaSnapshot(
        table_name=table_name,
        columns=[
            ColumnSpec(name="id", data_type="int", nullable=False),
            ColumnSpec(name="deal_amount", data_type=data_type, nullable=True),
        ],
    )


def test_save_and_retrieve_returns_equal_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "snapshots.db"
    snapshot = _sample_snapshot()

    store = SnapshotStore(db_path)
    try:
        store.save_snapshot(snapshot)
        loaded = store.get_latest_snapshot("deals")
    finally:
        store.close()

    assert loaded is not None
    assert loaded == snapshot


def test_get_latest_snapshot_returns_none_when_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "snapshots.db"

    with SnapshotStore(db_path) as store:
        assert store.get_latest_snapshot("unknown_table") is None


def test_save_overwrites_previous_snapshot_for_same_table(tmp_path: Path) -> None:
    db_path = tmp_path / "snapshots.db"
    first = _sample_snapshot(data_type="int")
    second = _sample_snapshot(data_type="decimal")

    with SnapshotStore(db_path) as store:
        store.save_snapshot(first)
        store.save_snapshot(second)
        loaded = store.get_latest_snapshot("deals")

    assert loaded is not None
    assert loaded == second
    amount = loaded.get_column("deal_amount")
    assert amount is not None
    assert amount.data_type == "decimal"


def test_store_works_as_context_manager(tmp_path: Path) -> None:
    db_path = tmp_path / "snapshots.db"
    snapshot = _sample_snapshot(table_name="tickets")

    with SnapshotStore(db_path) as store:
        store.save_snapshot(snapshot)
        loaded = store.get_latest_snapshot("tickets")

    assert loaded == snapshot

    # Connection should be closed after exiting the context.
    with SnapshotStore(db_path) as store:
        assert store.get_latest_snapshot("tickets") == snapshot
