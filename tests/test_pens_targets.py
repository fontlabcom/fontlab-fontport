# this_file: tests/test_pens_targets.py
"""Where the glyph-level pen adapter writes when the layer has no element."""

from types import SimpleNamespace

from fontTools.pens.recordingPen import RecordingPointPen
from test_pens import NATIVE, NativeContour

from fontlab_fontport.pens import FontGatePointPen, draw_points


def matrix(*values):
    return SimpleNamespace(asTuple=lambda: values)


def square(pen, origin):
    x, y = origin
    pen.beginPath()
    pen.addPoint((x, y), "move", name="start")
    pen.addPoint((x + 10, y), "line", smooth=True)
    pen.endPath()


def test_layerless_glyph_when_written_then_native_create_contour_gets_glyph_points():
    created = []
    glyph = SimpleNamespace(layer=None, components=[])

    def create_contour():
        created.append(NativeContour())
        return created[-1]

    glyph.createContour = create_contour
    square(FontGatePointPen(glyph, native=NATIVE), (5, 7))
    assert len(created) == 1 and created[0].open, "contour not created once, open"
    nodes = [(n.kind, n.point.x, n.point.y, n.name, n.smooth) for n in created[0].nodes]
    assert nodes == [("Move", 5, 7, "start", False), ("On", 15, 7, "", True)], (
        "layerless write must keep identity mapping and node metadata"
    )


def test_layer_without_element_when_written_then_one_new_element_holds_all_contours():
    native = SimpleNamespace(
        **vars(NATIVE),
        fgShape=lambda: SimpleNamespace(contours=[], matrix=matrix(1, 0, 0, 1, 0, 0)),
    )
    layer = SimpleNamespace(matrix=matrix(2, 0, 0, 2, 100, 0), shapes=[])
    glyph = SimpleNamespace(layer=layer, components=[])
    pen = FontGatePointPen(glyph, native=native)
    square(pen, (100, 0))
    square(pen, (120, 40))
    assert len(layer.shapes) == 1, "a session must reuse one new element"
    assert len(layer.shapes[0].contours) == 2
    stored = [(n.point.x, n.point.y) for n in layer.shapes[0].contours[0].nodes]
    assert stored == [(0, 0), (5, 0)], "layer matrix inverse not applied"
    rec = RecordingPointPen()
    draw_points(glyph, rec)
    points = [args[0] for op, args, _ in rec.value if op == "addPoint"]
    assert points == [(100, 0), (110, 0), (120, 40), (130, 40)], "round trip moved"


def test_adapter_when_imported_then_uses_only_public_fontlab_pens_names():
    import ast
    from pathlib import Path

    import fontlab_pens

    import fontlab_fontport.pens as adapter

    tree = ast.parse(Path(adapter.__file__).read_text(encoding="utf-8"))
    imported = [
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("fontlab_pens")
        for alias in node.names
    ]
    private = [
        (module, name)
        for module, name in imported
        if name.startswith("_") or any(part.startswith("_") for part in module.split("."))
    ]
    assert not private, f"Fontport must use only public fontlab_pens names: {private}"
    top_level = [name for module, name in imported if module == "fontlab_pens"]
    missing = [name for name in top_level if name not in fontlab_pens.__all__]
    assert not missing, f"names imported from fontlab_pens must be in its __all__: {missing}"


def test_adapter_pen_when_constructed_then_runs_the_staging_initialiser():
    from fontlab_pens import StagingPointPen

    from fontlab_fontport.pens import FontGatePointPen

    pen = FontGatePointPen(None)
    assert isinstance(pen, StagingPointPen), "adapter must build on the public StagingPointPen"
    assert pen._points is None, "StagingPointPen.__init__ must have run"
