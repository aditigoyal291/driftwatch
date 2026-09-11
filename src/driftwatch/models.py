"""Core domain models for DriftWatch schema drift detection."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Impact level for a detected schema change, used to prioritize response."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ColumnSpec(BaseModel):
    """A single column's schema as observed at a point in time."""

    name: str
    data_type: str
    nullable: bool


class SchemaSnapshot(BaseModel):
    """Point-in-time capture of a table's schema for later drift comparison."""

    table_name: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    columns: list[ColumnSpec]

    def get_column(self, name: str) -> ColumnSpec | None:
        """Return the column with the given name, or None if it is absent."""
        for column in self.columns:
            if column.name == name:
                return column
        return None


class DriftEvent(BaseModel):
    """A single detected schema change on a table, ready for diagnosis or alerting."""

    table_name: str
    column_name: str
    change_type: str
    severity: Severity
    description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
