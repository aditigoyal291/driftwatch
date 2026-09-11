"""Tests for IcebergConnector."""

from pathlib import Path

import pyarrow as pa
import pytest

from driftwatch.connectors.iceberg import IcebergConnector
from driftwatch.iceberg_catalog import get_local_catalog


def test_fetch_schema_returns_expected_snapshot(tmp_path: Path) -> None:
    catalog = get_local_catalog(
        tmp_path / "iceberg_catalog.db",
        tmp_path / "iceberg_warehouse",
    )
    catalog.create_namespace_if_not_exists("demo")
    catalog.create_table(
        "demo.deals",
        schema=pa.schema(
            [
                pa.field("deal_id", pa.int64(), nullable=False),
                pa.field("account_name", pa.string(), nullable=True),
                pa.field("deal_amount", pa.float64(), nullable=True),
            ]
        ),
        properties={"format-version": "2"},
    )

    connector = IcebergConnector(catalog, namespace="demo")
    snapshot = connector.fetch_schema("deals")

    assert snapshot.table_name == "deals"
    assert [column.name for column in snapshot.columns] == [
        "deal_id",
        "account_name",
        "deal_amount",
    ]
    assert [column.data_type for column in snapshot.columns] == [
        "long",
        "string",
        "double",
    ]
    assert [column.nullable for column in snapshot.columns] == [False, True, True]


def test_fetch_schema_raises_when_table_missing(tmp_path: Path) -> None:
    catalog = get_local_catalog(
        tmp_path / "iceberg_catalog.db",
        tmp_path / "iceberg_warehouse",
    )
    catalog.create_namespace_if_not_exists("demo")
    connector = IcebergConnector(catalog, namespace="demo")

    with pytest.raises(FileNotFoundError, match="demo.missing"):
        connector.fetch_schema("missing")
