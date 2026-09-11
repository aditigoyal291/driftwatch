"""Tests for DriftWatch domain models."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from driftwatch.models import ColumnSpec, DriftEvent, SchemaSnapshot, Severity


def test_column_spec_constructs_with_valid_data() -> None:
    column = ColumnSpec(name="deal_amount", data_type="int", nullable=False)
    assert column.name == "deal_amount"
    assert column.data_type == "int"
    assert column.nullable is False


def test_schema_snapshot_constructs_with_valid_data() -> None:
    snapshot = SchemaSnapshot(
        table_name="deals",
        columns=[
            ColumnSpec(name="id", data_type="int", nullable=False),
            ColumnSpec(name="deal_amount", data_type="decimal", nullable=True),
        ],
    )
    assert snapshot.table_name == "deals"
    assert len(snapshot.columns) == 2


def test_drift_event_constructs_with_valid_data() -> None:
    event = DriftEvent(
        table_name="deals",
        column_name="deal_amount",
        change_type="type_changed",
        severity=Severity.HIGH,
        description="Column 'deal_amount' changed type from int to decimal",
    )
    assert event.table_name == "deals"
    assert event.column_name == "deal_amount"
    assert event.change_type == "type_changed"
    assert event.severity is Severity.HIGH
    assert "deal_amount" in event.description


def test_severity_rejects_invalid_string() -> None:
    with pytest.raises(ValidationError):
        DriftEvent.model_validate(
            {
                "table_name": "deals",
                "column_name": "deal_amount",
                "change_type": "type_changed",
                "severity": "CRITICAL",
                "description": "invalid severity",
            }
        )


def test_get_column_returns_column_when_present() -> None:
    amount = ColumnSpec(name="deal_amount", data_type="int", nullable=False)
    snapshot = SchemaSnapshot(table_name="deals", columns=[amount])
    found = snapshot.get_column("deal_amount")
    assert found is not None
    assert found == amount


def test_get_column_returns_none_when_absent() -> None:
    snapshot = SchemaSnapshot(
        table_name="deals",
        columns=[ColumnSpec(name="id", data_type="int", nullable=False)],
    )
    assert snapshot.get_column("missing") is None


def test_schema_snapshot_captured_at_defaults_to_now() -> None:
    before = datetime.now(UTC)
    snapshot = SchemaSnapshot(table_name="deals", columns=[])
    after = datetime.now(UTC)
    assert before - timedelta(seconds=1) <= snapshot.captured_at <= after + timedelta(
        seconds=1
    )


def test_drift_event_detected_at_defaults_to_now() -> None:
    before = datetime.now(UTC)
    event = DriftEvent(
        table_name="deals",
        column_name="deal_amount",
        change_type="type_changed",
        severity=Severity.MEDIUM,
        description="Column 'deal_amount' changed type from int to decimal",
    )
    after = datetime.now(UTC)
    assert before - timedelta(seconds=1) <= event.detected_at <= after + timedelta(
        seconds=1
    )
