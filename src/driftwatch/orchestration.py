"""Wire connectors, snapshot storage, and drift detection into one pipeline."""

from __future__ import annotations

import asyncio
import sys

from driftwatch.connectors.base import Connector
from driftwatch.detection.engine import run_detection
from driftwatch.models import DriftEvent
from driftwatch.storage import SnapshotStore


async def check_table(
    connector: Connector,
    store: SnapshotStore,
    table_name: str,
) -> list[DriftEvent]:
    """Fetch, compare, and persist schema for one table; return any drift events.

    Connector and SnapshotStore APIs are synchronous/blocking. ``asyncio.to_thread``
    runs those calls in a worker thread so they do not block the event loop while
    other tables are checked concurrently.
    """
    new_snapshot = await asyncio.to_thread(connector.fetch_schema, table_name)
    previous = await asyncio.to_thread(store.get_latest_snapshot, table_name)

    events: list[DriftEvent] = []
    if previous is not None:
        events = run_detection(previous, new_snapshot)

    # Always persist the latest schema so the next run has a baseline.
    await asyncio.to_thread(store.save_snapshot, new_snapshot)
    return events


async def check_all_tables(
    connector: Connector,
    store: SnapshotStore,
    table_names: list[str],
) -> dict[str, list[DriftEvent]]:
    """Run ``check_table`` concurrently for each table and map results by name.

    Uses ``return_exceptions=True`` so one table failing (missing file, I/O error,
    etc.) does not cancel the remaining tasks. Failed tables are recorded with an
    empty event list and reported on stderr; successful tables still return their
    drift results.
    """
    gathered = await asyncio.gather(
        *(check_table(connector, store, name) for name in table_names),
        return_exceptions=True,
    )

    results: dict[str, list[DriftEvent]] = {}
    for table_name, outcome in zip(table_names, gathered, strict=True):
        if isinstance(outcome, BaseException):
            print(
                f"ERROR: check failed for table {table_name!r}: {outcome}",
                file=sys.stderr,
            )
            results[table_name] = []
        else:
            results[table_name] = outcome
    return results
