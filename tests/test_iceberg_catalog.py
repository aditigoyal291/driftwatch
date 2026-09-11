"""Integration tests for local Iceberg catalog wiring."""

from pathlib import Path

import pyarrow as pa

from driftwatch.iceberg_catalog import get_local_catalog


def test_get_local_catalog_create_and_load_table(tmp_path: Path) -> None:
    catalog = get_local_catalog(
        tmp_path / "iceberg_catalog.db",
        tmp_path / "iceberg_warehouse",
    )
    catalog.create_namespace_if_not_exists("demo")

    schema = pa.schema(
        [
            pa.field("id", pa.int64(), nullable=False),
            pa.field("name", pa.string(), nullable=True),
        ]
    )
    catalog.create_table(
        "demo.simple",
        schema=schema,
        properties={"format-version": "2"},
    )

    loaded = catalog.load_table("demo.simple")
    field_names = [field.name for field in loaded.schema().fields]

    assert field_names == ["id", "name"]
    assert catalog.table_exists("demo.simple")
