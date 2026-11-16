# this_file: tests/test_round15.py
"""C4 driver comparison regressions; preserve real geometry and metric failures."""

import importlib
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from defcon import Glyph


@pytest.fixture
def drivers(monkeypatch):
    monkeypatch.syspath_prepend(
        str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers")
    )
    return importlib.import_module("round10_payloads")


def glyph():
    g = Glyph()
    g.width = 500
    p = g.getPen()
    p.moveTo((0, 0))
    p.lineTo((100, 0))
    p.lineTo((0, 100))
    p.closePath()
    return g


def test_interchange_empty_note_and_numeric_types_keep_raw_evidence(drivers):
    from round10_interchange_steps import glyph_receipt

    expected, observed = glyph(), glyph()
    expected.note, observed.note = None, ""
    expected.height = 0
    observed = SimpleNamespace(
        **{
            key: getattr(observed, key)
            for key in ("width", "unicodes", "note", "lib", "anchors", "drawPoints")
        },
        height=0.0,
    )
    receipt = glyph_receipt(expected, observed)
    assert receipt["equal"]
    assert receipt["expected"]["note"] is None and receipt["observed"]["note"] == ""
    assert type(receipt["expected"]["height"]) is int
    assert type(receipt["observed"]["height"]) is float


@pytest.mark.parametrize("field", ["width", "height", "note", "outline"])
def test_interchange_rejects_real_value_and_outline_changes(drivers, field):
    from round10_interchange_steps import glyph_receipt

    expected, observed = glyph(), glyph()
    if field == "outline":
        observed[0][0].x += 1
    else:
        setattr(
            observed,
            field,
            "real note" if field == "note" else getattr(observed, field) + 1,
        )
    assert not glyph_receipt(expected, observed)["equal"]


def test_timestamp_ignore_is_root_only_and_keeps_real_differences(drivers):
    before = {
        "lastModified": "old",
        "layers": [
            {
                "name": "Regular",
                "advanceWidth": 500,
                "elements": [
                    {"elementData": {"contours": [{"nodes": ["0 0 l", "100 0 l"]}]}}
                ],
            }
        ],
    }
    after = deepcopy(before)
    after["lastModified"] = "new"
    assert drivers.payload_equal(before, after)
    assert before["lastModified"] == "old" and after["lastModified"] == "new"
    after["layers"][0]["advanceWidth"] = 501
    assert not drivers.payload_equal(before, after)
    after["layers"][0]["advanceWidth"] = 500
    after["layers"][0]["elements"][0]["elementData"]["contours"][0]["nodes"][0] = (
        "1 0 l"
    )
    assert not drivers.payload_equal(before, after)
    assert not drivers.payload_equal(
        {"lib": {"lastModified": "old"}}, {"lib": {"lastModified": "new"}}
    )


def test_creation_observes_package_history_instead_of_empty_glyph_history(drivers):
    from round10_history import package_history

    package = SimpleNamespace(
        currentHistoryState=lambda: 9, historyStates=lambda accepted: [0, 3, 9]
    )
    receipt = package_history(SimpleNamespace(_package=lambda: package))
    assert receipt["index"] == 9 and receipt["rows"] == [3, 9]
    from round10_glyph_steps import phases

    steps = dict(phases())
    assert "history_scope='package'" in steps["glyph-create-baseline"]
    assert "history_scope='glyph'" in steps["glyph-contours-baseline"]
    assert "geometry_receipt" in steps["glyph-create-undo-read"]
    assert "geometry_receipt" in steps["glyph-create-redo-read"]
    assert "geometry_receipt" in steps["glyph-create-reopen-read"]


def test_creation_edit_receipt_uses_package_rows_with_empty_glyph_history(drivers):
    import ast

    from round10_common_steps import SETUP
    from round10_history import package_history

    from fontlab_fontport.errors import UnsupportedCapability

    definitions = [
        node
        for node in ast.parse(SETUP).body
        if isinstance(node, ast.FunctionDef)
        and node.name in ("history", "edit_receipt")
    ]
    package = SimpleNamespace(
        currentHistoryState=lambda: 9, historyStates=lambda accepted: [0, 3, 9]
    )

    def wrong_history(*args):
        pytest.fail("Creation must not inspect the empty glyph history")

    state = {
        "history_scope": "package",
        "backend": SimpleNamespace(_package=lambda: package),
        "package_history": package_history,
        "glyph_history": wrong_history,
        "probe_name": "new",
        "history_before": 3,
        "history_rows_before": 1,
        "UnsupportedCapability": UnsupportedCapability,
    }
    exec(
        compile(
            ast.Module(body=definitions, type_ignores=[]), "<creation-receipt>", "exec"
        ),
        state,
    )
    receipt = state["edit_receipt"]("pass")
    assert receipt["history_scope"] == "package"
    assert receipt["one_history_row"] and receipt["history_protocol_matches"]
    assert receipt["history"] == 9 and receipt["rows_after"] == 2
