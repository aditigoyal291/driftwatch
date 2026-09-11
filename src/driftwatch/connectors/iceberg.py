"""Connector that reads table schemas from an Iceberg catalog."""

from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.exceptions import NoSuchTableError

from driftwatch.connectors.base import Connector
from driftwatch.models import ColumnSpec, SchemaSnapshot


class IcebergConnector(Connector):
    """Fetch schemas from Iceberg tables under a fixed catalog namespace."""

    def __init__(self, catalog: SqlCatalog, namespace: str) -> None:
        self._catalog = catalog
        self._namespace = namespace

    def fetch_schema(self, table_name: str) -> SchemaSnapshot:
        identifier = f"{self._namespace}.{table_name}"
        try:
            table = self._catalog.load_table(identifier)
        except NoSuchTableError as exc:
            raise FileNotFoundError(
                f"No Iceberg table for {table_name!r}; "
                f"expected identifier {identifier!r}"
            ) from exc

        columns = [
            ColumnSpec(
                name=field.name,
                data_type=str(field.field_type),
                # Iceberg uses required=True for non-null; invert for ColumnSpec.
                nullable=not field.required,
            )
            for field in table.schema().fields
        ]
        return SchemaSnapshot(table_name=table_name, columns=columns)
