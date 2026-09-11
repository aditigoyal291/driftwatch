"""Tests for LocalParquetConnector."""

import re
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from driftwatch.connectors.local_parquet import LocalParquetConnector


def _write_deals_parquet(path: Path) -> None:
    schema = pa.schema(
        [
            pa.field("deal_id", pa.int64(), nullable=False),
            pa.field("account_name", pa.string(), nullable=True),
            pa.field("deal_amount", pa.float64(), nullable=True),
        ]
    )
    table = pa.table(
        {
            "deal_id": pa.array([1, 2], type=pa.int64()),
            "account_name": pa.array(["Acme", "Globex"], type=pa.string()),
            "deal_amount": pa.array([1000.0, None], type=pa.float64()),
        },
        schema=schema,
    )
    pq.write_table(table, path)


def test_fetch_schema_returns_expected_snapshot(tmp_path: Path) -> None:
    _write_deals_parquet(tmp_path / "deals.parquet")
    connector = LocalParquetConnector(tmp_path)

    snapshot = connector.fetch_schema("deals")

    assert snapshot.table_name == "deals"
    assert [column.name for column in snapshot.columns] == [
        "deal_id",
        "account_name",
        "deal_amount",
    ]
    assert [column.data_type for column in snapshot.columns] == [
        "int64",
        "string",
        "double",
    ]
    assert [column.nullable for column in snapshot.columns] == [False, True, True]


def test_fetch_schema_raises_when_parquet_missing(tmp_path: Path) -> None:
    connector = LocalParquetConnector(tmp_path)
    expected = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError, match=re.escape(str(expected))):
        connector.fetch_schema("missing")
