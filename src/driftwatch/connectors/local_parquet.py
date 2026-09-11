"""Connector that reads table schemas from local Parquet files."""

from pathlib import Path

import pyarrow.parquet as pq

from driftwatch.connectors.base import Connector
from driftwatch.models import ColumnSpec, SchemaSnapshot


class LocalParquetConnector(Connector):
    """Fetch schemas from ``{table_name}.parquet`` files under a data directory."""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)

    def fetch_schema(self, table_name: str) -> SchemaSnapshot:
        path = self._data_dir / f"{table_name}.parquet"
        if not path.exists():
            raise FileNotFoundError(
                f"No Parquet file for table {table_name!r}; expected file at {path}"
            )

        # Metadata-only read — does not materialize row data.
        schema = pq.read_schema(path)
        columns = [
            ColumnSpec(
                name=field.name,
                data_type=str(field.type),
                nullable=field.nullable,
            )
            for field in schema
        ]
        return SchemaSnapshot(table_name=table_name, columns=columns)
