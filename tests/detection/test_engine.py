"""Tests for the detection engine and rule registry aggregation."""

from driftwatch.detection.engine import run_detection
from driftwatch.models import ColumnSpec, SchemaSnapshot, Severity


def test_run_detection_aggregates_events_from_multiple_rules() -> None:
    old = SchemaSnapshot(
        table_name="deals",
        columns=[
            ColumnSpec(name="id", data_type="int64", nullable=False),
            ColumnSpec(name="deal_amount", data_type="int64", nullable=True),
            ColumnSpec(name="legacy_field", data_type="string", nullable=True),
        ],
    )
    new = SchemaSnapshot(
        table_name="deals",
        columns=[
            ColumnSpec(name="id", data_type="int64", nullable=False),
            ColumnSpec(name="deal_amount", data_type="string", nullable=True),
        ],
    )

    events = run_detection(old, new)
    change_types = {event.change_type for event in events}

    assert "type_changed" in change_types
    assert "column_dropped" in change_types
    assert len(events) == 2

    by_type = {event.change_type: event for event in events}
    assert by_type["type_changed"].severity is Severity.HIGH
    assert by_type["type_changed"].column_name == "deal_amount"
    assert by_type["column_dropped"].severity is Severity.HIGH
    assert by_type["column_dropped"].column_name == "legacy_field"
