# this_file: tests/test_issue241_writeback.py
# SPDX-License-Identifier: Apache-2.0
"""Issue 241 Task 7: UFO anchor/guideline write-back and narrow multi-shape writes."""

from types import SimpleNamespace as NS

import pytest
from ufoLib2.objects import Glyph

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend


def _ufo_glyph_with_marks():
    backend = UFOBackend()
    glyph = backend.font.newGlyph("A")
    glyph.width = 500
    glyph.appendAnchor(
        {"name": "top", "x": 250, "y": 700, "color": "1,0,0,1", "identifier": "a1"}
    )
    glyph.appendGuideline(
        {
            "x": 10,
            "y": 20,
            "angle": 45,
            "name": "g",
            "color": "0,0,1,1",
            "identifier": "g1",
        }
    )
    return backend


def test_ufo_write_glyph_when_anchors_and_guidelines_then_round_trips():
    backend = _ufo_glyph_with_marks()
    font = RFont(backend)
    with font.edit_glyph("A", undo_name="Edit width") as glyph:
        glyph.width = 600
    written = backend.font["A"]
    assert written.width == 600, "Width edit was not written"
    anchor = written.anchors[0]
    assert (anchor.name, anchor.x, anchor.y, anchor.color, anchor.identifier) == (
        "top",
        250,
        700,
        "1,0,0,1",
        "a1",
    ), "Anchor fields did not round-trip"
    guide = written.guidelines[0]
    assert (
        guide.name,
        guide.x,
        guide.y,
        guide.angle,
        guide.color,
        guide.identifier,
    ) == ("g", 10, 20, 45, "0,0,1,1", "g1"), "Guideline fields did not round-trip"


def test_ufo_write_glyph_when_fontparts_glyph_then_marks_copied():
    backend = _ufo_glyph_with_marks()
    font = RFont(backend)
    source = font["A"]
    backend.write_glyph("B", backend.default_layer(), source)
    written = backend.font["B"]
    assert [a.name for a in written.anchors] == ["top"]
    assert [g.angle for g in written.guidelines] == [45]


# --- Limit B: host fakes for a layer with several native shapes -------------


class FakeTransform:
    def __init__(self, identity=True):
        self.identity = identity

    def isIdentity(self):
        return self.identity


class FakeShape:
    """Native flShape stand-in that records every mutation."""

    def __init__(
        self,
        contours=(),
        *,
        component=None,
        transformed=False,
        composite=False,
        image=False,
        refs=1,
    ):
        self.contours = list(contours)
        self.isComponent = component is not None
        self.isComposite = composite
        self.transform = FakeTransform(not transformed)
        self.image = NS(isNull=lambda: not image)
        self.shapeData = NS(
            componentGlyph=component, referenceCount=refs, changed=self._data_changed
        )
        self.calls = []

    def _data_changed(self):
        self.calls.append("data")

    def assign(self, native):
        self.contours = list(native.contours)

    def clone(self):
        twin = FakeShape(self.contours)
        twin.cloned_from = self
        return twin

    def clearContours(self):
        self.calls.append("clear")
        self.contours = []

    def addContours(self, contours, _flag):
        self.calls.append("add")
        self.contours.extend(contours)

    def changed(self):
        self.calls.append("changed")


def _layer(shapes, *, transformed=False):
    layer = NS(
        shapes=list(shapes),
        transform=FakeTransform(not transformed),
        hasHints=False,
        hasTTData=False,
        hasTTH=False,
        name="Regular",
        glyph=NS(name="A"),
    )
    layer.removeShape = lambda s: layer.shapes.remove(s)
    layer.insertShape = lambda i, s: layer.shapes.insert(i, s)
    layer.addShape = lambda s: layer.shapes.append(s)
    return layer


def _glyph(contour_x, component_dx=0):
    glyph = Glyph("A")
    pen = glyph.getPen()
    pen.moveTo((contour_x, 0))
    pen.lineTo((contour_x + 100, 0))
    pen.lineTo((contour_x, 100))
    pen.closePath()
    glyph.getPen().addComponent("B", (1, 0, 0, 1, component_dx, 0))
    return glyph


@pytest.fixture
def native(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "fontlab", NS(flShape=FakeShape))
    monkeypatch.setitem(sys.modules, "PythonQt", NS(QtGui=NS(QTransform=tuple)))
    return NS(staged=NS(layer=NS(shapes=[NS(contours=["new"])])))


def _several_shapes():
    component = FakeShape(component="B")
    image = FakeShape(image=True, transformed=True)
    shared_empty = FakeShape(refs=2)
    carrier = FakeShape(["old"])
    return [component, image, carrier, shared_empty], carrier


def test_stage_shapes_when_one_contour_shape_among_several_then_only_it_changes(native):
    shapes, carrier = _several_shapes()
    layer = _layer(shapes)
    staged = NativeFontBackend._stage_shapes(
        None, layer, native.staged, _glyph(50), True, _glyph(0)
    )
    assert all(not s.isComponent for s in staged), (
        "Contours-only staging built components"
    )
    NativeFontBackend._own_shapes(layer)
    NativeFontBackend._apply_shapes(layer, staged)
    others = [s for s in shapes if s is not carrier]
    assert layer.shapes[2] is not carrier, "Carrier was not copied before mutation"
    owned = layer.shapes[2]
    assert owned.cloned_from is carrier and owned.contours == ["new"], (
        "Contours not written"
    )
    assert owned.calls == ["clear", "data", "add"]
    assert carrier.contours == ["old"], "Undo snapshot shape was mutated"
    assert [layer.shapes[i] for i in (0, 1, 3)] == others, "Other shapes were replaced"
    assert all(not s.calls for s in others), "Another shape was mutated"


def test_write_glyph_named_when_several_shapes_then_writes_carrier_once(
    native, monkeypatch
):
    import sys

    import fontlab_fontport.host as host

    shapes, carrier = _several_shapes()
    layer = _layer(shapes)
    layer.anchors = []
    layer.advanceWidth = 0
    events = []
    package = NS(checkInitHistoryState=lambda _: events.append("history"))
    glyph = NS(name="A")
    sys.modules["fontlab"].flItems = NS(
        notifyChangesApplied=lambda *a: events.append("notify")
    )
    monkeypatch.setitem(sys.modules, "fontgate", NS(fgGlyph=lambda: native.staged))
    monkeypatch.setitem(sys.modules, "PythonQt", NS(QtCore=NS(), QtGui=NS()))
    monkeypatch.setattr(host, "write_glyph", lambda *a: None)
    monkeypatch.setattr(
        host, "_edit_guards", lambda: NS(require_history_scope=lambda *a, **k: None)
    )
    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._target = lambda *a: (package, glyph, layer)
    current = _glyph(0)
    current.width = 0
    backend.read_glyph = lambda *a: current
    source = _glyph(50)
    source.width = 0
    backend.write_glyph_named("A", "Regular", source, undo_name="Edit contours")
    assert events == ["history", "notify", "notify"]
    assert layer.shapes[2].contours == ["new"]
    assert [layer.shapes[i] for i in (0, 1, 3)] == [
        s for s in shapes if s is not carrier
    ]


@pytest.mark.parametrize(
    ("shapes", "current", "reason"),
    [
        (
            [FakeShape(["a"]), FakeShape(["b"])],
            _glyph(0),
            "Contours spread over several",
        ),
        (
            [FakeShape(["a"], transformed=True), FakeShape()],
            _glyph(0),
            "transformed native contour",
        ),
        ([FakeShape(["a"], refs=2), FakeShape()], _glyph(0), "shared native contour"),
        (
            [FakeShape(["a"], image=True), FakeShape()],
            _glyph(0),
            "image native contour",
        ),
        ([FakeShape(["a"]), FakeShape(composite=True)], _glyph(0), "composite"),
        ([FakeShape(), FakeShape()], _glyph(0), "no native shape holds contours"),
        (
            [FakeShape(["a"]), FakeShape()],
            _glyph(0, component_dx=9),
            "Changing components",
        ),
        ([FakeShape(["a"]), FakeShape()], None, "Changing components"),
    ],
)
def test_stage_shapes_when_unproven_several_shape_edit_then_named_refusal(
    native, shapes, current, reason
):
    layer = _layer([FakeShape(component="B"), *shapes])
    with pytest.raises(UnsupportedCapability, match=reason) as error:
        NativeFontBackend._stage_shapes(
            None, layer, native.staged, _glyph(50), True, current
        )
    assert error.value.capability == "glyph.geometry"
    assert "several shapes" in str(error.value)
    assert all(not s.calls for s in layer.shapes), "Refusal mutated a shape"


@pytest.mark.parametrize(
    ("shape", "reason"),
    [
        (FakeShape(["a"], transformed=True), "transformed native shape"),
        (FakeShape(["a"], composite=True), "composite native shape"),
        (FakeShape(["a"], image=True), "image native shape"),
        (FakeShape(["a"], refs=2), "shared native shape"),
    ],
)
def test_stage_shapes_when_single_unproven_shape_then_named_refusal(
    native, shape, reason
):
    with pytest.raises(UnsupportedCapability, match=reason):
        NativeFontBackend._stage_shapes(
            None, _layer([shape]), native.staged, _glyph(50), True, _glyph(0)
        )


def test_stage_shapes_when_layer_transformed_then_refused(native):
    layer = _layer([FakeShape(["a"]), FakeShape()], transformed=True)
    with pytest.raises(UnsupportedCapability, match="transformed native layers"):
        NativeFontBackend._stage_shapes(
            None, layer, native.staged, _glyph(50), True, _glyph(0)
        )


def test_stage_shapes_when_layer_hinted_then_refused_even_with_one_carrier(native):
    layer = _layer([FakeShape(["a"]), FakeShape()])
    layer.hasHints = True
    with pytest.raises(UnsupportedCapability, match="hinted"):
        NativeFontBackend._stage_shapes(
            None, layer, native.staged, _glyph(50), True, _glyph(0)
        )


def test_own_shapes_when_one_outline_with_components_then_all_owned():
    shapes = [FakeShape(component="B"), FakeShape(["a"])]
    layer = _layer(shapes)
    NativeFontBackend._own_shapes(layer)
    assert [s.cloned_from for s in layer.shapes] == shapes, (
        "Single-outline ownership changed"
    )
