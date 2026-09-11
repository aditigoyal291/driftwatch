"""Concrete structural schema drift rules."""

from driftwatch.detection.base import DriftRule
from driftwatch.detection.registry import register_rule
from driftwatch.models import DriftEvent, SchemaSnapshot, Severity


@register_rule
class TypeChangedRule(DriftRule):
    """Detect columns whose data_type differs between snapshots."""

    def evaluate(
        self, old: SchemaSnapshot, new: SchemaSnapshot
    ) -> list[DriftEvent]:
        events: list[DriftEvent] = []
        for old_column in old.columns:
            new_column = new.get_column(old_column.name)
            if new_column is None:
                continue
            if old_column.data_type != new_column.data_type:
                events.append(
                    DriftEvent(
                        table_name=new.table_name,
                        column_name=old_column.name,
                        change_type="type_changed",
                        severity=Severity.HIGH,
                        description=(
                            f"Column '{old_column.name}' changed type from "
                            f"'{old_column.data_type}' to '{new_column.data_type}'"
                        ),
                    )
                )
        return events


@register_rule
class ColumnDroppedRule(DriftRule):
    """Detect columns present in the old snapshot but missing from the new one."""

    def evaluate(
        self, old: SchemaSnapshot, new: SchemaSnapshot
    ) -> list[DriftEvent]:
        events: list[DriftEvent] = []
        for old_column in old.columns:
            if new.get_column(old_column.name) is None:
                events.append(
                    DriftEvent(
                        table_name=new.table_name,
                        column_name=old_column.name,
                        change_type="column_dropped",
                        severity=Severity.HIGH,
                        description=f"Column '{old_column.name}' was dropped",
                    )
                )
        return events


@register_rule
class ColumnAddedRule(DriftRule):
    """Detect columns present in the new snapshot but missing from the old one."""

    def evaluate(
        self, old: SchemaSnapshot, new: SchemaSnapshot
    ) -> list[DriftEvent]:
        events: list[DriftEvent] = []
        for new_column in new.columns:
            if old.get_column(new_column.name) is None:
                events.append(
                    DriftEvent(
                        table_name=new.table_name,
                        column_name=new_column.name,
                        change_type="column_added",
                        severity=Severity.LOW,
                        description=f"New column '{new_column.name}' was added",
                    )
                )
        return events
