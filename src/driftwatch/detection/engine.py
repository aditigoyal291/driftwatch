"""Orchestrate all registered drift rules against a snapshot pair."""

# Side-effect import: running @register_rule decorators in rules.py so they
# appear in the registry. Do not remove — looks unused but is required.
import driftwatch.detection.rules  # noqa: F401
from driftwatch.detection.registry import get_registered_rules
from driftwatch.models import DriftEvent, SchemaSnapshot


def run_detection(
    old: SchemaSnapshot, new: SchemaSnapshot
) -> list[DriftEvent]:
    """Evaluate every registered rule and return the combined DriftEvent list."""
    events: list[DriftEvent] = []
    for rule in get_registered_rules():
        events.extend(rule.evaluate(old, new))
    return events
