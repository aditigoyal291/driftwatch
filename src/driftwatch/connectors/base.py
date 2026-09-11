"""Abstract connector contract for DriftWatch data sources."""

from abc import ABC, abstractmethod

from driftwatch.models import SchemaSnapshot


class Connector(ABC):
    """Contract that every data-source connector must implement.

    Callers depend only on this interface so the rest of DriftWatch stays
    independent of any specific storage technology (Parquet, Iceberg, etc.).
    """

    @abstractmethod
    def fetch_schema(self, table_name: str) -> SchemaSnapshot:
        """Return the current schema for ``table_name`` as a snapshot."""
