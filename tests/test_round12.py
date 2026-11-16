# this_file: tests/test_round12.py
"""C4 native-ticket regressions reproduced without a native host."""

import sys
from types import SimpleNamespace

import pytest
from fontTools.pens.recordingPen import RecordingPointPen

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.info import stage_info
from fontlab_fontport.pens import FontGatePointPen
from fontlab_fontport.testing import ObjectGenerator, run_test, upstream_tests


@pytest.mark.parametrize(
    "field",
    ["familyName", "styleName", "openTypeOS2WeightClass", "openTypeOS2WidthClass"],
)
def test_unset_info_has_named_capability(field):
    with pytest.raises(UnsupportedCapability) as error:
        stage_info({field: None}, "Unset")
    assert error.value.capability == "info.unset"


def test_upm_accepts_integral_native_double_but_not_fraction():
    assert stage_info({"unitsPerEm": 1000.0}, "Import")["unitsPerEm"] == 1000
    with pytest.raises(UnsupportedCapability, match=r"info\.unitsPerEm\.fractional"):
        stage_info({"unitsPerEm": 1000.5}, "Import")


def test_identifiers_are_named_before_pen_mutation():
    with pytest.raises(UnsupportedCapability) as error:
        FontGatePointPen(None).beginPath(identifier="id")
    assert error.value.capability == "identifiers"


def test_native_lib_hides_only_internal_key_and_normalizes_arrays(monkeypatch):
    package = SimpleNamespace(
        packageLib={
            "com.fontlab.kerningClassesInMainMaster": True,
            "x": ("A", {"nested": (1, 2)}),
        }
    )
    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._package = lambda: package
    assert backend.get_lib() == {"x": ["A", {"nested": [1, 2]}]}
    package.checkInitHistoryState = lambda _: None
    package.mastersContainer = lambda: "masters"
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(flItems=SimpleNamespace(notifyChangesApplied=lambda *a: None)),
    )
    backend.set_lib({"x": ["new"]})
    assert package.packageLib == {
        "com.fontlab.kerningClassesInMainMaster": True,
        "x": ["new"],
    }


def test_attached_contour_fixture_is_empty_like_upstream():
    from fontlab_fontport.memory import UFOBackend

    generator = ObjectGenerator(backend_factory=UFOBackend, native_attached=True)
    try:
        contour, _ = generator("contour")
        assert len(contour.points) == 0
        contour.appendPoint((0, 0), "move")
        contour.appendPoint((100, 0), "line")
        assert contour.open and len(contour.points) == 2
    finally:
        generator.close()


def test_empty_contour_pen_is_safe_noop():
    pen = FontGatePointPen(None)
    pen.beginPath()
    pen.endPath()


def test_attached_parent_expectation_is_separate_harness_exclusion():
    from fontlab_fontport.memory import UFOBackend

    case = next(
        case
        for case in upstream_tests()
        if case.id().endswith("test_anchor.TestAnchor.test_get_index_noParent")
    )
    row = run_test(
        case, ObjectGenerator(backend_factory=UFOBackend, native_attached=True)
    )
    assert row["status"] == "HarnessExclusion"
    assert row["capability"] == "testing.nativeAttached.parents"
    assert row["fixtures"] == []


def test_controls_and_open_contours_roundtrip_valid_native_points():
    from test_pens import NATIVE, NativeGlyph

    from fontlab_fontport.pens import draw_points

    for kind, controls in [
        ("line", []),
        ("curve", [(10, 20), (30, 40)]),
        ("qcurve", [(10, 20)]),
    ]:
        glyph = NativeGlyph()
        pen = FontGatePointPen(glyph, native=NATIVE)
        pen.beginPath()
        pen.addPoint((0, 0), "move")
        for point in controls:
            pen.addPoint(point)
        pen.addPoint((50, 60), kind)
        pen.endPath()
        result = RecordingPointPen()
        draw_points(glyph, result)
        assert result.value[1][1][1] == "move"
        assert result.value[-2][1][1] == kind


def test_glyph_history_checkpoints_bracket_write_in_one_layer_glyph_list(monkeypatch):
    from ufoLib2.objects import Glyph

    import fontlab_fontport.host as host

    events = []
    target = SimpleNamespace(advanceWidth=500, anchors=[])
    glyph = SimpleNamespace()
    package = SimpleNamespace(
        checkInitHistoryState=lambda _: events.append(("prepare", target.advanceWidth))
    )
    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend.read_glyph = lambda *a: Glyph("A", width=500)
    backend._target = lambda *a: (package, glyph, target)
    backend._stage_shapes = lambda *a: []
    monkeypatch.setitem(
        sys.modules, "fontgate", SimpleNamespace(fgGlyph=lambda: object())
    )
    monkeypatch.setitem(sys.modules, "PythonQt", SimpleNamespace(QtCore=object()))
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda name, objects: events.append(
                    (name, target.advanceWidth, objects)
                )
            )
        ),
    )
    monkeypatch.setattr(host, "write_glyph", lambda *a: None)
    backend.write_glyph_named(
        "A", "Regular", Glyph("A", width=600), undo_name="One glyph"
    )
    assert events[0] == ("prepare", 500)
    assert [(e[1], e[2]) for e in events[1:]] == [
        (500, [target, glyph]),
        (600, [target, glyph]),
    ]


def test_structured_values_use_persistent_master_storage_and_refuse_names_prewrite(
    monkeypatch,
):
    events = []
    package = SimpleNamespace(
        info=SimpleNamespace(
            openTypeOS2Panose=[0] * 10,
            openTypeOS2WeightClass=400,
            openTypeOS2WidthClass=5,
            openTypeNameRecords=[],
        ),
        panose="0 0 0 0 0 0 0 0 0 0",
        weight_value=400.0,
        width_value=5.0,
        checkInitHistoryState=lambda _: events.append("prepare"),
        mastersContainer=lambda: "masters",
    )
    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._package = lambda: package
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda *a: events.append(
                    (package.weight_value, package.panose)
                )
            )
        ),
    )
    backend.set_info_many(
        {
            "openTypeOS2WeightClass": 500,
            "openTypeOS2WidthClass": 6,
            "openTypeOS2Panose": [2] * 10,
        }
    )
    assert package.weight_value == 500 and package.width_value == 6
    assert package.panose == "2 2 2 2 2 2 2 2 2 2"
    assert (
        package.info.openTypeOS2WeightClass == 400
    )  # Never write the transient fgFont style cache.
    assert backend.get_info("openTypeOS2WeightClass") == 500
    assert backend.get_info("openTypeOS2Panose") == [2] * 10
    assert len(events) == 3 and events[1][0] == 400 and events[2][0] == 500
    events.clear()
    with pytest.raises(UnsupportedCapability) as error:
        backend.set_info_many(
            {
                "familyName": "Must not write",
                "openTypeNameRecords": [
                    {
                        "nameID": 256,
                        "platformID": 3,
                        "encodingID": 1,
                        "languageID": 1033,
                        "string": "Owned",
                    }
                ],
            }
        )
    assert error.value.capability == "info.openTypeNameRecords.persistence"
    assert events == []


class StrictGeometryBackend:
    """Factory for a real UFO backend that validates the actual native point pen."""

    def __new__(cls):
        from test_pens import NATIVE, NativeGlyph

        from fontlab_fontport.memory import UFOBackend

        class Strict(UFOBackend):
            requires_complete_contours = True

            def write_glyph(self, name, layer, source):
                native = NativeGlyph()
                native.components = SimpleNamespace(append=lambda *a: None)
                source.drawPoints(FontGatePointPen(native, native=NATIVE))
                return super().write_glyph(name, layer, source)

        return Strict()


@pytest.mark.parametrize(
    "case",
    [
        case
        for case in upstream_tests()
        if any(
            ".test_" + name + "." in case.id()
            for name in ("contour", "bPoint", "segment", "point")
        )
    ],
    ids=lambda case: case.id(),
)
def test_upstream_point_mutation_against_native_pen(case):
    row = run_test(
        case,
        ObjectGenerator(backend_factory=StrictGeometryBackend, native_attached=True),
    )
    assert row["status"] in ("pass", "UnsupportedCapability", "HarnessExclusion"), row
    if row["status"] == "UnsupportedCapability":
        assert all(
            any(
                f"UnsupportedCapability: {capability}:" in trace
                for capability in ("identifiers", "glyph.image")
            )
            for trace in row["errors"]
        ), row


def test_provisional_contour_is_not_written_or_silently_saved(tmp_path):
    from fontlab_fontport.live import RFont

    backend = StrictGeometryBackend()
    font = RFont(backend)
    glyph = font.newGlyph("A")
    from defcon import Contour

    glyph.naked().appendContour(Contour())
    contour = glyph.contours[0]
    contour.appendPoint((0, 0), "move")
    contour.appendPoint((10, 20), "offcurve")
    # The host still has the last valid move-only geometry.
    assert len(backend.read_glyph("A", backend.default_layer()).contours[0].points) == 1
    with pytest.raises(UnsupportedCapability) as error:
        font.save(str(tmp_path / "unfinished.ufo"))
    assert error.value.capability == "glyph.incompleteContours"
    contour.appendPoint((20, 30), "offcurve")
    contour.appendPoint((40, 50), "curve")
    assert len(backend.read_glyph("A", backend.default_layer()).contours[0].points) == 4
    font.save(str(tmp_path / "finished.ufo"))
    font.close()


def test_live_anchor_identifier_refuses_before_defcon_mutation():
    from fontlab_fontport.live import RFont

    font = RFont(StrictGeometryBackend())
    glyph = font.newGlyph("A")
    glyph.appendAnchor("top", (10, 700))
    with pytest.raises(UnsupportedCapability) as error:
        glyph.anchors[0].getIdentifier()
    assert error.value.capability == "identifiers"
    assert glyph.anchors[0].identifier is None
    font.close()


def test_dangling_kerning_names_are_named_before_native_calls():
    from fontlab_fontport.native_kerning import _native_pair

    package = SimpleNamespace(findName=lambda name: None)
    for pair in [("missing", "A"), ("public.kern1.missing", "A")]:
        with pytest.raises(UnsupportedCapability) as error:
            _native_pair(package, pair, {})
        assert error.value.capability == "kerning.danglingNames"


def test_native_geometry_probe_never_allocates_components_and_missing_base_is_named():
    from ufoLib2.objects import Glyph

    from fontlab_fontport.live import RFont
    from fontlab_fontport.pens import edit_geometry_ready

    detached = Glyph("comp")
    detached.getPointPen().addComponent("A", (1, 0, 0, 1, 0, 0))
    assert edit_geometry_ready(detached)
    font = RFont(StrictGeometryBackend())
    glyph = font.newGlyph("A")
    with pytest.raises(UnsupportedCapability) as error:
        glyph.appendComponent("missing")
    assert error.value.capability == "components.unresolvedBase"
    assert not glyph.components
    font.newGlyph("B")
    glyph.appendComponent("B")
    assert len(glyph.components) == 1
    font.close()


@pytest.mark.parametrize("cycle", [False, True])
def test_native_ufo_import_unresolved_component_refuses_named_before_allocation(cycle):
    from ufoLib2 import Font

    from fontlab_fontport.interchange import preflight_import

    source = Font()
    glyph = source.newGlyph("A")
    glyph.getPointPen().addComponent("A" if cycle else "missing", (1, 0, 0, 1, 0, 0))
    with pytest.raises(UnsupportedCapability) as error:
        list(preflight_import(source, native=True))
    assert error.value.capability == "components.unresolvedBase"
