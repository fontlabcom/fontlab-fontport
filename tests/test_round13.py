# this_file: tests/test_round13.py
"""Regressions from C4 round-12 native receipts, without FontLab."""

import json
from enum import IntEnum
from types import SimpleNamespace

import pytest
from fontTools.pens.recordingPen import RecordingPointPen

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.info import stage_info


def test_empty_outline_marks_shape_data_changed_for_undo():
    calls = []
    data = SimpleNamespace(changed=lambda: calls.append("data"))
    shape = SimpleNamespace(
        isComponent=False, shapeData=data, clearContours=lambda: calls.append("clear")
    )
    NativeFontBackend._apply_shapes(SimpleNamespace(shapes=[shape]), [])
    assert calls == ["clear", "data"]


def test_component_transform_marks_shape_changed_for_undo():
    calls = []
    old = SimpleNamespace(
        isComponent=True, transform=(10, 20), changed=lambda: calls.append("shape")
    )
    new = SimpleNamespace(isComponent=True, transform=(30, 40))
    NativeFontBackend._apply_shapes(SimpleNamespace(shapes=[old]), [new])
    assert old.transform == (30, 40) and calls == ["shape"]


def test_width_class_accepts_exported_int_enum_but_refuses_bool():
    class Width(IntEnum):
        NORMAL = 5

    assert (
        stage_info({"openTypeOS2WidthClass": Width.NORMAL}, "Import")[
            "openTypeOS2WidthClass"
        ]
        == 5
    )
    assert (
        type(
            stage_info({"openTypeOS2WidthClass": Width.NORMAL}, "Import")[
                "openTypeOS2WidthClass"
            ]
        )
        is int
    )
    with pytest.raises((TypeError, ValueError)):
        stage_info({"openTypeOS2WidthClass": True}, "Import")


def test_nonintegral_upm_refuses_by_name():
    for value in (2000.1, 2000.125):
        with pytest.raises(UnsupportedCapability) as error:
            stage_info({"unitsPerEm": value}, "Edit")
        assert error.value.capability == "info.unitsPerEm.fractional"


def test_pending_edits_prevent_invalidation_and_close_without_losing_handle():
    from defcon import Contour
    from test_round12 import StrictGeometryBackend

    from fontlab_fontport.live import RFont

    font = RFont(StrictGeometryBackend())
    glyph = font.newGlyph("A")
    glyph.naked().appendContour(Contour())
    contour = glyph.contours[0]
    contour.appendPoint((0, 0), "move")
    contour.appendPoint((10, 20), "offcurve")
    for action in (font.invalidate, font.refresh):
        with pytest.raises(UnsupportedCapability) as error:
            action()
        assert error.value.capability == "glyph.incompleteContours"
        assert not font._closed and glyph.name == "A"
    contour.appendPoint((20, 20), "qcurve")
    font.close()


def test_all_offcurve_closed_contour_roundtrips():
    from test_pens import NATIVE, NativeGlyph

    from fontlab_fontport.pens import FontGatePointPen, draw_points

    native = NativeGlyph()
    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    for xy in ((0, 0), (100, 0), (100, 100), (0, 100)):
        pen.addPoint(xy)
    pen.endPath()
    observed = RecordingPointPen()
    draw_points(native, observed)
    assert len(native.contours) == 1 and not native.contours[0].open
    assert [args[1] for op, args, _ in observed.value if op == "addPoint"] == [None] * 4


def test_payload_comparison_ignores_only_empty_geometry_and_layer_ui_state(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(
        str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers")
    )
    from round10_payloads import COMPARISON_NOTES, payload_equal

    before = {
        "layers": [
            {
                "name": "Roman",
                "active": True,
                "advanceWidth": 500,
                "elements": [{"elementData": {}}],
            }
        ]
    }
    after = {"layers": [{"name": "Roman", "advanceWidth": 500}]}
    assert payload_equal(before, after)
    assert any("fontlab.lastModified" in note for note in COMPARISON_NOTES)
    after["layers"][0]["advanceWidth"] = 501
    assert not payload_equal(before, after)
    assert before["layers"][0]["elements"]  # Never mutate raw evidence.


def test_transport_frames_large_unicode_data_below_native_limit(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(
        str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers")
    )
    from round10_transfer import chunk, decode, frame

    value = {"glif": 'Ωქართული"\\\n' * 20000}
    storage = {}
    header = frame(value, storage)
    parts = []
    for offset in range(0, header["_fontport_transfer"]["length"], 8192):
        part = chunk(storage, header["_fontport_transfer"]["id"], offset)
        assert len(json.dumps(part).encode()) < 16000
        parts.append(part["data"])
    assert decode(header, parts) == value


def test_history_counter_observes_geometry_rows_instead_of_package(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(
        str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers")
    )
    from round10_history import glyph_history

    def obj(ix, rows, **kwargs):
        return SimpleNamespace(
            currentHistoryState=lambda: ix,
            historyStates=lambda accepted: rows,
            **kwargs,
        )

    data = obj(8, [0, 4, 8])
    shape = obj(8, [0, 4, 8], shapeData=data)
    layer = obj(4, [0, 4], shapes=[shape])
    glyph = obj(8, [0, 4, 8], isNull=False, layers=[layer])
    backend = SimpleNamespace(
        _package=lambda: SimpleNamespace(
            findName=lambda name: glyph, currentHistoryState=lambda: 0
        )
    )
    observed = glyph_history(backend, "A")
    assert observed["index"] == 8 and observed["rows"] == [4, 8]
    assert len(observed["objects"]) == 4


def test_flatten_rounds_coordinates_before_the_single_write():
    from fontlab_fontport.live import RFont
    from fontlab_fontport.memory import UFOBackend
    from fontlab_fontport.recipes import flatten

    font = RFont(UFOBackend())
    source = font.newGlyph("A")
    pen = source.getPen()
    pen.moveTo((-0.7, 0.2))
    pen.curveTo((10.2, 100.3), (90.7, 100.7), (100.2, 0.1))
    pen.endPath()
    font.newGlyph("flat")
    result = flatten(font, "A", "flat")
    assert all(
        p.x == int(p.x) and p.y == int(p.y) for c in result.contours for p in c.points
    )
    assert result.contours[0].points[0].position == (-1, 0)
    font.close()


def test_pending_close_warns_by_name_and_closes_owned_binding():
    from defcon import Contour
    from test_round12 import StrictGeometryBackend

    from fontlab_fontport.live import RFont

    font = RFont(StrictGeometryBackend())
    glyph = font.newGlyph("A")
    glyph.naked().appendContour(Contour())
    glyph.contours[0].appendPoint((0, 0), "move")
    glyph.contours[0].appendPoint((10, 10), "offcurve")
    with pytest.warns(RuntimeWarning, match="glyph.incompleteContours"):
        font.close()
    assert font._closed


def test_closing_history_notification_runs_after_a_partial_mutation_failure(
    monkeypatch,
):
    import sys

    from ufoLib2.objects import Glyph

    import fontlab_fontport.host as host

    events = []

    class Target:
        anchors = ()
        _width = 500

        @property
        def advanceWidth(self):
            return self._width

        @advanceWidth.setter
        def advanceWidth(self, value):
            self._width = value
            raise RuntimeError("injected mutation failure")

    target = Target()
    glyph = SimpleNamespace()
    package = SimpleNamespace(checkInitHistoryState=lambda _: None)
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
                notifyChangesApplied=lambda name, items: events.append(
                    (target.advanceWidth, items)
                )
            )
        ),
    )
    monkeypatch.setattr(host, "write_glyph", lambda *a: None)
    with pytest.raises(RuntimeError, match="injected mutation failure"):
        backend.write_glyph_named("A", "Roman", Glyph("A", width=600))
    assert events == [(500, [target, glyph]), (600, [target, glyph])]


def test_real_driver_wire_chunks_large_export_and_reassembles_without_recursion(
    monkeypatch, tmp_path
):
    import builtins
    import importlib
    from pathlib import Path

    drivers = Path(__file__).resolve().parents[1] / "tests" / "native_drivers"
    monkeypatch.syspath_prepend(str(drivers))
    driver = importlib.import_module("round10")
    sizes = []

    class Client:
        def run(self, wire, **kwargs):
            scope = dict(kwargs)
            exec(wire, scope)
            sizes.append(len(json.dumps(scope["result"]).encode()))
            return SimpleNamespace(value=scope["result"])

    run = driver.Run(Client(), tmp_path, [str(drivers)])
    try:
        result = run.step("export-next", "result={'glif':'ქართულიΩ'*25000}")
        assert result["glif"] == "ქართულიΩ" * 25000
        assert len(sizes) > 2 and max(sizes) < 32768
        assert not builtins._fontport_round10_runs[run.key]["_reply_transfers"]
        assert not run.failures
    finally:
        builtins._fontport_round10_runs.pop(run.key, None)
