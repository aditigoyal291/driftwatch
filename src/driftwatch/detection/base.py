"""Strategy interface for schema drift detection rules."""

from abc import ABC, abstractmethod

from driftwatch.models import DriftEvent, SchemaSnapshot


class DriftRule(ABC):
    """Strategy interface for a single kind of schema drift check.

    Each rule independently inspects the difference between two snapshots of
    the same table and returns zero or more DriftEvents for the changes it
    knows how to detect.
    """

    @abstractmethod
    def evaluate(
        self, old: SchemaSnapshot, new: SchemaSnapshot
    ) -> list[DriftEvent]:
        """Compare ``old`` and ``new`` and return any matching drift events."""
