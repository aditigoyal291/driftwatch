"""Self-registering registry for DriftRule implementations.

Important: the registry only contains rules from modules that have actually
been imported somewhere. Defining a ``@register_rule`` class in a file that
is never imported will leave that rule unregistered with no error — import
``driftwatch.detection.rules`` (or your rule module) before calling
``get_registered_rules()``.
"""

from typing import TypeVar

from driftwatch.detection.base import DriftRule

_REGISTERED_RULES: list[DriftRule] = []

T = TypeVar("T", bound=DriftRule)


def register_rule(cls: type[T]) -> type[T]:
    """Instantiate ``cls``, add it to the registry, and return ``cls`` unchanged."""
    _REGISTERED_RULES.append(cls())
    return cls


def get_registered_rules() -> list[DriftRule]:
    """Return all rule instances registered so far in this process."""
    return list(_REGISTERED_RULES)
