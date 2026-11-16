# this_file: tests/test_coverage_ledger.py
"""Native coverage ledger uses observed per-ID classifications, never Pending."""

import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def coverage_tool():
    spec = importlib.util.spec_from_file_location(
        "coverage_tool",
        Path(__file__).resolve().parents[1] / "tools/fontparts-coverage.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_receipts_preserve_named_capabilities_and_harness(
    coverage_tool, tmp_path
):
    rows = [
        {"id": "test.a", "status": "pass"},
        {
            "id": "test.b",
            "status": "UnsupportedCapability",
            "errors": [
                "Traceback\nfontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: missing route\n"
            ],
        },
        {
            "id": "test.c",
            "status": "HarnessExclusion",
            "capability": "testing.nativeAttached.parents",
        },
    ]
    run = tmp_path / "run"
    run.mkdir()
    (run / "receipts.jsonl").write_text(
        "\n".join(json.dumps({"result": row}) for row in rows)
    )
    (run / "result.json").write_text(
        json.dumps(
            {
                "ok": True,
                "failures": [],
                "upstream_counts": {
                    "pass": 1,
                    "UnsupportedCapability": 1,
                    "HarnessExclusion": 1,
                },
            }
        )
    )
    ledger = coverage_tool.load_native(tmp_path, {"test.a", "test.b", "test.c"})
    assert ledger == {
        "test.a": "pass",
        "test.b": "capability: RFont.<lambda>",
        "test.c": "harness exclusion: testing.nativeAttached.parents",
    }
    with pytest.raises(ValueError, match="ID"):
        coverage_tool.load_native(tmp_path, {"test.a"})


def test_native_capability_must_be_named(coverage_tool):
    with pytest.raises(ValueError, match="named"):
        coverage_tool.native_status(
            {
                "id": "bad",
                "status": "UnsupportedCapability",
                "errors": ["NotImplementedError"],
            }
        )
    with pytest.raises(ValueError, match="Unclassified"):
        coverage_tool.native_status({"id": "bad", "status": "unclassified"})


def test_documented_native_ledger_has_every_observed_id_and_counts():
    from collections import Counter

    text = (
        Path(__file__).resolve().parents[1] / "src_docs/md/guides/FONTPARTS-COVERAGE.md"
    ).read_text()
    rows = [
        line.split("|")
        for line in text.splitlines()
        if line.startswith("| `fontParts.test.")
    ]
    assert len(rows) == 1797 and len({row[1] for row in rows}) == 1797
    for column, expected in (
        (5, {"pass": 432, "capability": 1365}),
        (6, {"pass": 1087, "capability": 638, "harness exclusion": 72}),
    ):
        cells = [row[column].strip() for row in rows]
        assert Counter(cell.split(":", 1)[0] for cell in cells) == expected
        assert all(
            cell == "pass" or (": " in cell and cell.split(": ", 1)[1]) for cell in cells
        )
