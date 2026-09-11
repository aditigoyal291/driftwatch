"""Unit tests for individual drift detection rules."""

from driftwatch.detection.rules import (
    ColumnAddedRule,
    ColumnDroppedRule,
    TypeChangedRule,
)
from driftwatch.models import ColumnSpec, SchemaSnapshot, Severity


def _snapshot(table_name: str, columns: list[ColumnSpec]) -> SchemaSnapshot:
    return SchemaSnapshot(table_name=table_name, columns=columns)


def test_type_changed_rule_detects_type_difference() -> None:
    old = _snapshot(
        "deals",
        [ColumnSpec(name="deal_amount", data_type="int64", nullable=True)],
    )
    new = _snapshot(
        "deals",
        [ColumnSpec(name="deal_amount", data_type="string", nullable=True)],
    )

    events = TypeChangedRule().evaluate(old, new)

    assert len(events) == 1
    event = events[0]
    assert event.change_type == "type_changed"
    assert event.severity is Severity.HIGH
    assert event.column_name == "deal_amount"
    assert event.description == (
        "Column 'deal_amount' changed type from 'int64' to 'string'"
    )


def test_type_changed_rule_returns_empty_when_types_match() -> None:
    column = ColumnSpec(name="deal_amount", data_type="int64", nullable=True)
    old = _snapshot("deals", [column])
    new = _snapshot("deals", [column.model_copy()])

    assert TypeChangedRule().evaluate(old, new) == []


def test_column_dropped_rule_detects_missing_column() -> None:
    old = _snapshot(
        "deals",
        [
            ColumnSpec(name="id", data_type="int64", nullable=False),
            ColumnSpec(name="legacy_field", data_type="string", nullable=True),
        ],
    )
    new = _snapshot(
        "deals",
        [ColumnSpec(name="id", data_type="int64", nullable=False)],
    )

    events = ColumnDroppedRule().evaluate(old, new)

    assert len(events) == 1
    event = events[0]
    assert event.change_type == "column_dropped"
    assert event.severity is Severity.HIGH
    assert event.column_name == "legacy_field"
    assert event.description == "Column 'legacy_field' was dropped"


def test_column_dropped_rule_returns_empty_when_no_drops() -> None:
    columns = [ColumnSpec(name="id", data_type="int64", nullable=False)]
    old = _snapshot("deals", columns)
    new = _snapshot("deals", [columns[0].model_copy()])

    assert ColumnDroppedRule().evaluate(old, new) == []


def test_column_added_rule_detects_new_column() -> None:
    old = _snapshot(
        "deals",
        [ColumnSpec(name="id", data_type="int64", nullable=False)],
    )
    new = _snapshot(
        "deals",
        [
            ColumnSpec(name="id", data_type="int64", nullable=False),
            ColumnSpec(name="discount_pct", data_type="double", nullable=True),
        ],
    )

    events = ColumnAddedRule().evaluate(old, new)

    assert len(events) == 1
    event = events[0]
    assert event.change_type == "column_added"
    assert event.severity is Severity.LOW
    assert event.column_name == "discount_pct"
    assert event.description == "New column 'discount_pct' was added"


def test_column_added_rule_returns_empty_when_no_adds() -> None:
    columns = [ColumnSpec(name="id", data_type="int64", nullable=False)]
    old = _snapshot("deals", columns)
    new = _snapshot("deals", [columns[0].model_copy()])

    assert ColumnAddedRule().evaluate(old, new) == []
