# this_file: tests/test_info_backend.py
"""Batch validation and live info dispatch; native acceptance is separate."""

import copy
import sys
from types import SimpleNamespace

import pytest

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.live import RInfo

VALUES = {
    "familyName": "Family Ω",
    "styleName": "Italic",
    "unitsPerEm": 2048,
    "ascender": 800.5,
    "descender": -250.25,
    "capHeight": 710,
    "xHeight": 505.5,
    "italicAngle": -12.5,
    "versionMajor": 2,
    "versionMinor": 123,
    "note": "Unicode Ω\nsecond line",
    "copyright": "Copyright © 2026",
}


@pytest.fixture
def native(monkeypatch):
    events = []
    info = SimpleNamespace(**{**VALUES, "familyName": "Before"})
    package = SimpleNamespace(
        isNull=False,
        fgId=5,
        info=info,
        checkInitHistoryState=lambda index: events.append(("prepare", index)),
        currentHistoryState=lambda: 0,
        getProperty=lambda name: None,  # a clean document (no unsaved history)
        mastersContainer=lambda: "masters",
    )
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flWorkspace=SimpleNamespace(
                instance=lambda: SimpleNamespace(
                    findPackageId=lambda identifier: package,
                    currentPackage=package,  # the active document
                )
            ),
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda title, objects: events.append(
                    (title, copy.deepcopy(vars(info)), objects)
                )
            ),
        ),
    )
    return NativeFontBackend(5), package, events


def test_info_batch_applies_all_fields_with_package_and_master_checkpoints(native):
    backend, package, events = native
    backend.set_info_many(
        VALUES, undo_name="Edit complete info", require_single_undo=False
    )
    assert vars(package.info) == VALUES, "every staged field must reach native info"
    assert events[0] == ("prepare", 0), "prepare native initial state before mutation"
    assert events[-1][0] == "Edit complete info", "the whole batch needs one name"
    assert events[-1][2] == [package, "masters"], "capture package and master info"
    assert events[1][1]["familyName"] == "Before", "initial checkpoint precedes changes"
    assert len(events) == 3, "fresh package needs baseline plus changed-state capture"
    assert {name: backend.get_info(name) for name in VALUES} == VALUES


@pytest.mark.parametrize(
    "field,value",
    [
        ("unknown", 1),
        ("unitsPerEm", 0),
        ("unitsPerEm", -1),
        ("unitsPerEm", 1000.5),
        ("unitsPerEm", True),
        ("unitsPerEm", 2**31),
        ("versionMajor", -1),
        ("versionMinor", 1.5),
        ("versionMinor", False),
        ("versionMinor", 2**31),
        ("ascender", float("nan")),
        ("descender", float("inf")),
        ("italicAngle", -float("inf")),
        ("capHeight", None),
        ("xHeight", "500"),
        ("ascender", True),
        ("ascender", 10**1000),
        ("note", b"text"),
        ("familyName", "bad\x00name"),
        ("note", "bad\ud800text"),
    ],
)
def test_invalid_last_field_leaves_entire_batch_and_history_untouched(
    native, field, value
):
    backend, package, events = native
    before = vars(package.info).copy()
    with pytest.raises((ValueError, TypeError, NotImplementedError)):
        backend.set_info_many({"familyName": "Must not apply", field: value})
    assert vars(package.info) == before, "validation failure must apply no fields"
    assert not events, "validation failure must not add a native history step"


def test_info_empty_batch_and_identical_values_do_not_create_history(native):
    backend, package, events = native
    backend.set_info_many({})
    backend.set_info_many({"familyName": package.info.familyName})
    assert not events, "empty/no-op edits must not add Undo history"


def test_opt_in_strict_info_batch_refuses_extra_history_row_before_any_mutation(native):
    from fontlab_fontport.errors import UnsupportedCapability

    backend, package, events = native
    with pytest.raises(UnsupportedCapability, match=r"info.exactSingleUndo"):
        backend.set_info_many({"familyName": "After"}, require_single_undo=True)
    assert package.info.familyName == "Before" and not events
    backend.set_info_many({"familyName": "Before"}, require_single_undo=True)
    assert not events


@pytest.mark.parametrize("undo_name", [None, "", "  ", "bad\x00title"])
def test_info_invalid_operation_name_is_rejected_before_mutation(native, undo_name):
    backend, package, events = native
    with pytest.raises((ValueError, TypeError)):
        backend.set_info_many({"familyName": "After"}, undo_name=undo_name)
    assert package.info.familyName == "Before" and not events


@pytest.mark.parametrize("values", [None, [], [("familyName", "After")], "text"])
def test_info_requires_mapping_before_mutation(native, values):
    backend, package, events = native
    with pytest.raises(TypeError, match="mapping"):
        backend.set_info_many(values)
    assert package.info.familyName == "Before" and not events


def test_individual_info_setter_uses_the_batch_boundary(native):
    backend, package, events = native
    backend.set_info("unitsPerEm", 4096, require_single_undo=False)
    assert package.info.unitsPerEm == 4096
    assert events[-1][0] == "FontParts font info"


def test_existing_native_history_still_captures_package_globals_before_edit(native):
    backend, package, events = native
    package.currentHistoryState = lambda: 1
    backend.set_info_many({"familyName": "After"}, require_single_undo=False)
    assert len(events) == 3, (
        "nonzero history does not prove a restorable package baseline"
    )
    assert events[-1][1]["familyName"] == "After"


def test_rinfo_apply_forwards_one_explicit_batch_after_lifetime_check():
    events = []
    backend = SimpleNamespace(
        set_info_many=lambda values, *, undo_name: events.append((values, undo_name))
    )
    owner = SimpleNamespace(_backend=backend, _check=lambda: events.append("checked"))
    info = RInfo(owner)
    info.apply(VALUES, undo_name="Staged info")
    assert events[-1] == (VALUES, "Staged info")
    assert events[:-1] and all(event == "checked" for event in events[:-1])


def test_rinfo_apply_refuses_a_stale_binding_before_native_dispatch():
    def stale():
        raise RuntimeError("closed")

    info = RInfo(SimpleNamespace(_check=stale))
    with pytest.raises(RuntimeError, match="closed"):
        info.apply(VALUES)


def test_structured_info_when_valid_then_detached_native_batch(native):
    from fontlab_fontport.info import stage_info

    backend, package, events = native
    values = {
        "openTypeOS2Panose": [2, 0, 5, 3, 0, 0, 0, 0, 0, 0],
        "openTypeOS2WidthClass": 5,
        "openTypeOS2WeightClass": 400,
        "postscriptStemSnapH": [20.5, 80],
        "postscriptStemSnapV": [70],
        "openTypeNameDesigner": "Designer Ω",
        "trademark": "Trade\nmark",
    }
    for key, value in values.items():
        setattr(package.info, key, [] if isinstance(value, list) else "")
    package.panose = "0 0 0 0 0 0 0 0 0 0"
    package.weight_value = 200
    package.width_value = 3
    staged = stage_info(values, "Structured info")
    staged["openTypeOS2Panose"][0] = 1
    assert values["openTypeOS2Panose"][0] == 2
    backend.set_info_many(values, require_single_undo=False)
    assert all(backend.get_info(key) == value for key, value in values.items())
    assert events[-1][0] == "FontParts font info"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("openTypeOS2Panose", [1]),
        ("openTypeOS2Panose", [65536] * 10),
        ("openTypeOS2WidthClass", 0),
        ("openTypeOS2WeightClass", -1),
        ("postscriptStemSnapH", [float("nan")]),
        ("postscriptStemSnapV", [1] * 13),
        ("openTypeNameRecords", [{"nameID": 1}]),
        ("trademark", None),
    ],
)
def test_structured_info_when_invalid_then_whole_batch_refused(native, field, value):
    backend, package, events = native
    with pytest.raises((TypeError, ValueError, NotImplementedError)):
        backend.set_info_many({"familyName": "Must not apply", field: value})
    assert package.info.familyName == "Before" and not events


def test_default_info_batch_preserves_v1_editing_contract(native):
    backend, package, events = native
    backend.set_info_many({"familyName": "After"})
    assert package.info.familyName == "After" and events


VERTICAL = {
    "openTypeOS2TypoAscender": 800.0,
    "openTypeOS2TypoDescender": -200.0,
    "openTypeOS2TypoLineGap": 90.0,
    "openTypeHheaAscender": 950.0,
    "openTypeHheaDescender": -250.0,
    "openTypeHheaLineGap": 0.0,
    "openTypeOS2WinAscent": 1000.0,
    "openTypeOS2WinDescent": 300.0,
}


def test_get_info_when_vertical_metrics_then_integers_from_native_package(native):
    backend, package, _ = native
    for name, value in VERTICAL.items():
        setattr(package.info, name, value)
    values = {name: backend.get_info(name) for name in VERTICAL}
    assert values == {name: int(value) for name, value in VERTICAL.items()}
    assert all(type(value) is int for value in values.values()), "UFO 3 wants integers"


def test_get_info_when_vertical_metric_is_fractional_then_value_kept(native):
    backend, package, _ = native
    package.info.openTypeHheaAscender = 950.5
    assert backend.get_info("openTypeHheaAscender") == 950.5


def test_info_when_vertical_metric_or_unknown_field_then_write_and_read_refused(native):
    backend, package, _ = native
    with pytest.raises(UnsupportedCapability, match=r"unsupported|Unsupported|unknown"):
        backend.get_info("openTypeOS2Bogus")
    with pytest.raises(UnsupportedCapability, match=r"info\.openTypeHheaAscender"):
        backend.set_info("openTypeHheaAscender", 1)
    assert not hasattr(package.info, "openTypeHheaAscender")


def test_get_info_when_field_outside_vertical_metrics_is_integral_float_then_stays_float(native):
    backend, package, _ = native
    package.info.italicAngle = 0.0
    value = backend.get_info("italicAngle")
    assert type(value) is float, "only the eight vertical metrics are converted to int"


def test_get_info_when_integer_fields_are_integral_floats_then_ints(native):
    backend, package, _ = native
    package.info.unitsPerEm = 1000.0
    package.info.versionMajor = 2.0
    package.info.versionMinor = 5.0
    values = {n: backend.get_info(n) for n in ("unitsPerEm", "versionMajor", "versionMinor")}
    assert values == {"unitsPerEm": 1000, "versionMajor": 2, "versionMinor": 5}
    assert all(type(v) is int for v in values.values()), "UFO 3 integer fields"


def test_get_info_when_unitsperem_is_fractional_then_value_kept(native):
    backend, package, _ = native
    package.info.unitsPerEm = 1000.5
    assert backend.get_info("unitsPerEm") == 1000.5


def test_get_info_when_unitsperem_is_int_then_unchanged(native):
    backend, package, _ = native
    package.info.unitsPerEm = 2048
    value = backend.get_info("unitsPerEm")
    assert value == 2048 and type(value) is int
