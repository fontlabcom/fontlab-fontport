# this_file: tests/test_pens.py
"""Check pen semantics against the real fontTools and UFO implementations."""

from types import SimpleNamespace

import pytest
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPointPen
from ufoLib2 import Font

from fontlab_fontport.pens import FontGatePointPen, draw_points


class NativeContour:
    def __init__(self):
        self.open = False
        self.nodes = []


class NativeNode:
    def __init__(self, kind, point, name, smooth):
        self.kind, self.point, self.name, self.smooth = kind, point, name, smooth


NATIVE = SimpleNamespace(
    fgContour=NativeContour,
    fgNode=NativeNode,
    fgPoint=lambda x, y: SimpleNamespace(x=x, y=y),
)


class NativeGlyph:
    def __init__(self):
        self.contours = []
        self.components = []
        identity = SimpleNamespace(asTuple=lambda: (1, 0, 0, 1, 0, 0))
        self.layer = SimpleNamespace(
            matrix=identity,
            shapes=[SimpleNamespace(contours=self.contours, matrix=identity)],
        )

    def __iter__(self):
        return iter(self.contours)

    def createContour(self):
        contour = NativeContour()
        self.contours.append(contour)
        return contour


@pytest.mark.parametrize("closed", [True, False])
@pytest.mark.parametrize("kind", ["curve", "qcurve"])
def test_point_pen_roundtrip_preserves_geometry_names_and_smooth(closed, kind):
    native = NativeGlyph()
    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    pen.addPoint((10, 20), "line" if closed else "move", name="start")
    pen.addPoint((30, 40))
    if kind == "curve":
        pen.addPoint((50, 60))
    pen.addPoint((70, 80), kind, smooth=True, name="end")
    pen.addPoint((90, 100), "line")
    pen.endPath()
    rec = RecordingPointPen()
    draw_points(native, rec)
    target = Font().newGlyph("A")
    rec.replay(target.getPointPen())
    points = list(target.contours[0].points)
    assert points[0].type == ("line" if closed else "move"), "open/closed start changed"
    assert points[-2].smooth and points[-2].name == "end", "point metadata lost"
    assert points[-2].type == kind, "curve degree changed"
    assert (points[-1].x, points[-1].y) == (90, 100), "coordinates changed"


def test_segment_adapter_accepts_fontpens_output():
    from fontPens.flattenPen import FlattenPen

    native = NativeGlyph()
    destination = SegmentToPointPen(FontGatePointPen(native, native=NATIVE))
    pen = FlattenPen(destination, approximateSegmentLength=20)
    pen.moveTo((0, 0))
    pen.curveTo((0, 100), (100, 100), (100, 0))
    pen.closePath()
    rec = RecordingPointPen()
    draw_points(native, rec)
    assert len(rec.value) > 5, "fontPens did not produce a flattened native contour"
    assert all(n.kind != "Curve" for n in native.contours[0].nodes), "curve remained"


def test_invalid_contour_does_not_mutate_native_glyph():
    native = NativeGlyph()
    pen = FontGatePointPen(native, native=NATIVE)
    with pytest.raises(ValueError, match="beginPath"):
        pen.addPoint((0, 0), "line")
    pen.beginPath()
    pen.addPoint((0, 0), "move")
    pen.addPoint((1, 2))
    pen.addPoint((3, 4), "curve")
    with pytest.raises((ValueError, TypeError)):
        pen.endPath()
    assert not native.contours, "malformed curve partially changed the glyph"


def test_empty_contour_and_nested_begin_fail_without_native_access():
    native = NativeGlyph()
    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    with pytest.raises(ValueError, match="active"):
        pen.beginPath()
    pen.endPath()
    assert native.contours == [], "empty native contour was created"


def test_empty_native_contour_is_safe_to_draw():
    native = NativeGlyph()
    native.contours.append(NativeContour())
    rec = RecordingPointPen()
    draw_points(native, rec)
    assert rec.value == [], "empty contours should never reach native drawPoints"


def test_identifier_is_rejected_before_data_is_lost():
    pen = FontGatePointPen(NativeGlyph(), native=NATIVE)
    with pytest.raises(NotImplementedError, match="identifier"):
        pen.beginPath(identifier="important")


def test_closed_native_segment_pen_endpoint_is_normalized():
    glyph = NativeGlyph()
    contour = NativeContour()
    contour.nodes = [
        NativeNode("Move", NATIVE.fgPoint(0, 0), "start", False),
        NativeNode("Curve", NATIVE.fgPoint(20, 20), "", False),
        NativeNode("Curve", NATIVE.fgPoint(30, 30), "", False),
        NativeNode("On", NATIVE.fgPoint(0, 0), "", True),
    ]
    glyph.contours.append(contour)
    rec = RecordingPointPen()
    draw_points(glyph, rec)
    first = rec.value[1][1]
    assert first[1:3] == ("curve", True), "closing curve and smooth flag were lost"
    assert len(rec.value) == 5, "native duplicated closing endpoint was retained"


@pytest.mark.parametrize("point", [(float("inf"), 0), (0, float("nan"))])
def test_nonfinite_point_is_rejected(point):
    pen = FontGatePointPen(NativeGlyph(), native=NATIVE)
    pen.beginPath()
    with pytest.raises(ValueError, match="finite"):
        pen.addPoint(point, "line")


def test_all_offcurve_quadratic_contour_roundtrips():
    native = NativeGlyph()
    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    for point in [(0, 0), (0, 100), (100, 100), (100, 0)]:
        pen.addPoint(point)
    pen.endPath()
    target = Font().newGlyph("Q")
    draw_points(native, target.getPointPen())
    assert len(target.contours[0].points) == 4, "implied quadratic on-curves changed"
    assert all(p.type is None for p in target.contours[0].points), "curve kind changed"


def test_all_shapes_and_their_transforms_are_drawn():
    native = NativeGlyph()
    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    pen.addPoint((10, 20), "move")
    pen.addPoint((30, 40), "line")
    pen.endPath()
    native.layer.shapes.append(
        SimpleNamespace(
            contours=native.contours,
            matrix=SimpleNamespace(asTuple=lambda: (2, 0, 0, 3, 100, -20)),
        )
    )
    rec = RecordingPointPen()
    draw_points(native, rec)
    positions = [args[0] for op, args, _ in rec.value if op == "addPoint"]
    assert positions == [(10, 20), (30, 40), (120, 40), (160, 100)], (
        "shapes lost or transform wrong"
    )


def test_component_transform_roundtrip_and_validation():
    class Components(list):
        def append(self, name, transform):
            super().append(
                SimpleNamespace(
                    drawPoints=lambda pen: pen.addComponent(name, transform)
                )
            )

    native = NativeGlyph()
    native.components = Components()
    pen = FontGatePointPen(native, native=NATIVE)
    matrix = (1, 0.25, -0.1, 0.8, 120, -30)
    pen.addComponent("A", matrix)
    rec = RecordingPointPen()
    draw_points(native, rec)
    assert rec.value == [("addComponent", ("A", matrix), {})], (
        "component affine matrix changed"
    )
    for bad in [(1, 0), (1, 0, 0, 1, float("nan"), 0)]:
        with pytest.raises(ValueError):
            pen.addComponent("bad", bad)
    assert len(native.components) == 1, "invalid component reached native API"


def test_writing_to_transformed_native_shape_uses_glyph_coordinates():
    native = NativeGlyph()
    native.layer.matrix = SimpleNamespace(asTuple=lambda: (1, 0, 0, 2, 0, -10))
    native.layer.shapes[0].matrix = SimpleNamespace(
        asTuple=lambda: (2, 0, 0, 3, 100, -20)
    )
    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    pen.addPoint((120, 70), "move")
    pen.addPoint((160, 190), "line")
    pen.endPath()
    rec = RecordingPointPen()
    draw_points(native, rec)
    positions = [args[0] for op, args, _ in rec.value if op == "addPoint"]
    assert len(positions) == 2, "transform changed the point count"
    for actual, expected in zip(positions, [(120, 70), (160, 190)], strict=True):
        assert actual == pytest.approx(expected), "transform applied twice"


def test_singular_native_transform_fails_without_mutation():
    native = NativeGlyph()
    native.layer.matrix = SimpleNamespace(asTuple=lambda: (0, 0, 0, 0, 0, 0))
    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    pen.addPoint((0, 0), "move")
    pen.addPoint((10, 10), "line")
    with pytest.raises(ValueError, match="singular"):
        pen.endPath()
    assert native.contours == [], "singular transform changed native data"


def test_import_does_not_load_native_host():
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import fontlab_fontport; "
                "assert 'fontlab' not in sys.modules; "
                "assert 'fontgate' not in sys.modules"
            ),
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
