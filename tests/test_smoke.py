"""Smoke tests for the DriftWatch package skeleton."""

import driftwatch


def test_version_is_set() -> None:
    assert driftwatch.__version__ == "0.1.0"
