# this_file: tests/test_upstream_environment.py
"""The actual installed upstream test IDs are the yardstick, not lookalikes."""

import json
from pathlib import Path

import pytest

from fontlab_fontport.memory import UFOBackend
from fontlab_fontport.testing import ObjectGenerator, run_test, upstream_tests

EXCLUSIONS = frozenset(
    json.loads(
        (Path(__file__).parent / "data/fontparts-1.1.1-unsupported.json").read_text()
    )
)


@pytest.mark.parametrize("surface", ["fontshell", "memory"])
@pytest.mark.parametrize("case", upstream_tests(), ids=lambda case: case.id())
def test_upstream_environment(case, surface):
    row = run_test(
        case,
        ObjectGenerator(
            fontshell=surface == "fontshell",
            backend_factory=UFOBackend if surface == "memory" else None,
        ),
    )
    assert row["status"] in ("pass", "UnsupportedCapability", "upstream-skip"), row
    if surface == "fontshell":
        assert row["status"] in ("pass", "upstream-skip"), row
    elif row["status"] == "UnsupportedCapability":
        assert case.id() in EXCLUSIONS, "New exclusion requires review: " + repr(row)


def test_runner_preserves_an_unclassified_assertion():
    import unittest

    class Mismatch(unittest.TestCase):
        def runTest(self):
            self.assertEqual(
                1,
                2,
                "retain this evidence: UnsupportedCapability must not classify an assertion",
            )

    row = run_test(Mismatch(), ObjectGenerator(fontshell=True))
    assert row["status"] == "unclassified"
    assert "retain this evidence" in row["errors"][0]
