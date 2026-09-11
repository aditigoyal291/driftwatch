"""Run DriftWatch schema checks against local Parquet demo tables."""

from __future__ import annotations

import asyncio
from pathlib import Path

from driftwatch.connectors.local_parquet import LocalParquetConnector
from driftwatch.models import DriftEvent
from driftwatch.orchestration import check_all_tables
from driftwatch.storage import SnapshotStore

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "snapshots.db"
TABLE_NAMES = ["deals", "contacts"]


def _print_table_summary(
    table_name: str,
    events: list[DriftEvent],
    *,
    had_baseline: bool,
) -> None:
    print(f"\n=== {table_name} ===")
    if not had_baseline:
        print("No previous snapshot — baseline recorded")
        return
    if not events:
        print("No drift detected")
        return
    print(f"Detected {len(events)} drift event(s):")
    for event in events:
        print(f"  [{event.severity}] {event.change_type}: {event.description}")


async def _async_main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connector = LocalParquetConnector(DATA_DIR)

    with SnapshotStore(DB_PATH) as store:
        # Snapshot presence before the run distinguishes first-run vs no-drift
        # (both yield an empty event list from check_table).
        had_baseline = {
            name: store.get_latest_snapshot(name) is not None for name in TABLE_NAMES
        }
        results = await check_all_tables(connector, store, TABLE_NAMES)

    print("DriftWatch check complete")
    print(f"Data dir: {DATA_DIR.resolve()}")
    print(f"Snapshot DB: {DB_PATH.resolve()}")
    for table_name in TABLE_NAMES:
        _print_table_summary(
            table_name,
            results.get(table_name, []),
            had_baseline=had_baseline[table_name],
        )


def main() -> None:
    """Entry point for ``python scripts/run_check.py``."""
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
