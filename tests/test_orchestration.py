"""Tests for the orchestration pipeline."""

from pathlib import Path

import pytest

from driftwatch.connectors.base import Connector
from driftwatch.models import ColumnSpec, DriftEvent, SchemaSnapshot
from driftwatch.orchestration import check_all_tables, check_table
from driftwatch.storage import SnapshotStore


class StubConnector(Connector):
    """Test double that returns hand-built snapshots by table name."""

    def __init__(self, snapshots: dict[str, SchemaSnapshot]) -> None:
        self._snapshots = snapshots

    def fetch_schema(self, table_name: str) -> SchemaSnapshot:
        try:
            return self._snapshots[table_name]
        except KeyError as exc:
            raise FileNotFoundError(f"No stub snapshot for {table_name!r}") from exc


def _snapshot(table_name: str, columns: list[ColumnSpec]) -> SchemaSnapshot:
    return SchemaSnapshot(table_name=table_name, columns=columns)


@pytest.mark.asyncio
async def test_check_table_first_run_saves_baseline_and_returns_empty(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "snapshots.db"
    snapshot = _snapshot(
        "deals",
        [ColumnSpec(name="id", data_type="int64", nullable=False)],
    )
    connector = StubConnector({"deals": snapshot})

    with SnapshotStore(db_path) as store:
        events = await check_table(connector, store, "deals")
        saved = store.get_latest_snapshot("deals")

    assert events == []
    assert saved is not None
    assert saved == snapshot


@pytest.mark.asyncio
async def test_check_table_second_run_detects_drift(tmp_path: Path) -> None:
    db_path = tmp_path / "snapshots.db"
    old = _snapshot(
        "deals",
        [
            ColumnSpec(name="id", data_type="int64", nullable=False),
            ColumnSpec(name="deal_amount", data_type="int64", nullable=True),
        ],
    )
    new = _snapshot(
        "deals",
        [
            ColumnSpec(name="id", data_type="int64", nullable=False),
            ColumnSpec(name="deal_amount", data_type="string", nullable=True),
        ],
    )

    with SnapshotStore(db_path) as store:
        store.save_snapshot(old)
        connector = StubConnector({"deals": new})
        events = await check_table(connector, store, "deals")
        saved = store.get_latest_snapshot("deals")

    assert len(events) == 1
    assert events[0].change_type == "type_changed"
    assert events[0].column_name == "deal_amount"
    assert saved == new


@pytest.mark.asyncio
async def test_check_table_no_drift_when_snapshots_match(tmp_path: Path) -> None:
    db_path = tmp_path / "snapshots.db"
    snapshot = _snapshot(
        "deals",
        [ColumnSpec(name="id", data_type="int64", nullable=False)],
    )

    with SnapshotStore(db_path) as store:
        store.save_snapshot(snapshot)
        connector = StubConnector({"deals": snapshot.model_copy(deep=True)})
        events = await check_table(connector, store, "deals")

    assert events == []


@pytest.mark.asyncio
async def test_check_all_tables_maps_results_by_table_name(tmp_path: Path) -> None:
    db_path = tmp_path / "snapshots.db"
    deals_old = _snapshot(
        "deals",
        [ColumnSpec(name="id", data_type="int64", nullable=False)],
    )
    deals_new = _snapshot(
        "deals",
        [
            ColumnSpec(name="id", data_type="int64", nullable=False),
            ColumnSpec(name="discount_pct", data_type="double", nullable=True),
        ],
    )
    contacts = _snapshot(
        "contacts",
        [ColumnSpec(name="contact_id", data_type="int64", nullable=False)],
    )

    connector = StubConnector({"deals": deals_new, "contacts": contacts})

    with SnapshotStore(db_path) as store:
        store.save_snapshot(deals_old)
        store.save_snapshot(contacts)
        results = await check_all_tables(
            connector, store, ["deals", "contacts"]
        )

    assert set(results) == {"deals", "contacts"}
    assert results["contacts"] == []
    assert len(results["deals"]) == 1
    assert results["deals"][0].change_type == "column_added"
    assert isinstance(results["deals"][0], DriftEvent)
