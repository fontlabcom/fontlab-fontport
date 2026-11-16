# this_file: tests/test_transfer.py
"""Real UFO/FontParts glue tests; the boundary fake is not native proof."""

import copy
import plistlib
import sys
from types import SimpleNamespace
from xml.etree import ElementTree

import defcon
import pytest
from fontParts.fontshell import RGlyph
from fontTools.pens.recordingPen import RecordingPointPen
from test_pens import NATIVE, NativeContour
from ufoLib2 import Font
from ufoLib2.objects import Anchor, Glyph

from fontlab_fontport.transfer import to_fontparts, to_ufo_glyph, write_glyph


class Sequence(list):
    def clean(self):
        self.clear()


class Components(Sequence):
    def append(self, name, matrix):
        super().append(
            SimpleNamespace(drawPoints=lambda pen: pen.addComponent(name, matrix))
        )


class Lib:
    """Native fgLib has methods, no mapping protocol; update replaces."""

    def __init__(self, **data):
        self.data = data

    def keys(self):
        return self.data.keys()

    def get(self, key):
        return self.data.get(key)

    def update(self, data):
        self.data = copy.deepcopy(data)

    def clear(self):
        self.data.clear()

    def items(self):
        return {
            key: (
                value
                if key == "note"
                else ElementTree.tostring(
                    ElementTree.fromstring(plistlib.dumps(value))[0], encoding="unicode"
                )
            )
            for key, value in self.data.items()
        }

    def __bool__(self):
        return bool(self.data)


def lib_values(lib):
    keys = lib.keys()
    return {key: lib.get(key) for key in keys}


class NativeGlyph:
    def __init__(self, name="target"):
        self.name, self.width, self.height = name, 100, 200
        self.unicodes, self.lib = [65], Lib(old=[1], note="old")
        identity = SimpleNamespace(asTuple=lambda: (1, 0, 0, 1, 0, 0))
        self.layer = SimpleNamespace(
            matrix=identity,
            shapes=[
                SimpleNamespace(matrix=identity, contours=Sequence(), style=object())
            ],
            anchors=Sequence(),
        )
        self.layers = [self.layer, object()]
        self.components = Components()
        self.hints = object()
        self.dict = NativeDict(self)

    @property
    def note(self):
        return self.lib.get("note") or ""

    @note.setter
    def note(self, value):
        self.lib.data["note"] = value

    @property
    def anchors(self):
        return self.layer.anchors

    def createContour(self):
        contour = NativeContour()
        self.layer.shapes[0].contours.append(contour)
        return contour


class NativeDict:
    def __init__(self, owner):
        self.owner = owner

    @property
    def lib(self):
        owner = self.owner

        class RawMap:
            def __setitem__(self, key, value):
                owner.lib.data[key] = plistlib.loads(
                    ("<plist>" + value + "</plist>").encode()
                )

        return RawMap()

    @lib.setter
    def lib(self, values):
        raise AssertionError("native whole-dict assignment corrupts values")


@pytest.fixture(autouse=True)
def native_module(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "fontgate",
        SimpleNamespace(
            **vars(NATIVE),
            fgGlyph=NativeGlyph,
            fgAnchor=lambda name, x, y: SimpleNamespace(
                name=name, position=SimpleNamespace(x=x, y=y)
            ),
        ),
    )


def source_glyph(kind="ufo"):
    glyph = Glyph(
        name="source",
        width=532,
        height=891,
        unicodes=[65, 0x10400],
        note="Transfer",
        lib={"nested": {"list": [1, True, b"bytes"]}},
    )
    pen = glyph.getPointPen()
    for kind_ in ("curve", "qcurve"):
        pen.beginPath()
        pen.addPoint((10, 20), "move", name="start")
        pen.addPoint((30, 40))
        if kind_ == "curve":
            pen.addPoint((50, 60))
        pen.addPoint((70, 80), kind_, smooth=True, name="finish")
        pen.endPath()
    pen.addComponent("base", (1, 0.25, -0.1, 0.8, 120, -30))
    glyph.anchors.append(Anchor(25, 600, name="top"))
    if kind == "ufo":
        return glyph
    raw = defcon.Glyph()
    glyph.drawPoints(raw.getPointPen())
    for field in ("name", "width", "height", "unicodes", "note"):
        setattr(raw, field, getattr(glyph, field))
    raw.lib.update(glyph.lib)
    raw.appendAnchor(dict(glyph.anchors[0]))
    return RGlyph(raw) if kind == "fontparts" else raw


def recording(glyph):
    pen = RecordingPointPen()
    glyph.drawPoints(pen)
    return pen.value


@pytest.mark.parametrize("kind", ["ufo", "fontparts", "defcon"])
def test_write_and_detached_exports_preserve_content(kind):
    source, native = source_glyph(kind), NativeGlyph()
    other_layer, hints = native.layers[1], native.hints
    style = native.layer.shapes[0].style
    write_glyph(source, native)
    assert native.name == "target", "explicit destination was renamed"
    for exported in (to_ufo_glyph(native), to_fontparts(native)):
        assert recording(exported) == recording(source), (
            "geometry or point metadata lost"
        )
        for field in ("width", "height", "note"):
            assert getattr(exported, field) == getattr(source, field), field
        assert list(exported.unicodes) == list(source.unicodes), (
            "Unicode values changed"
        )
        assert dict(exported.lib) == {**dict(source.lib), "note": source.note}, (
            "plist values changed"
        )
        assert exported.anchors[0].name == "top", "anchor name lost"
        anchor = exported.anchors[0]
        assert (anchor.x, anchor.y) == (25, 600), "anchor coordinates changed"
    assert isinstance(to_fontparts(native), RGlyph), "not real FontParts"
    assert isinstance(to_ufo_glyph(native), Glyph), "not real ufoLib2"
    assert to_fontparts(native).font is None, "export is not detached"
    assert native.layers[1] is other_layer and native.hints is hints, (
        "unknown native state changed"
    )
    assert native.layer.shapes[0].style is style, "shape style changed"
    exported = to_ufo_glyph(native)
    exported.lib["nested"]["list"].append("detached")
    assert native.lib.get("nested")["list"] == [1, True, b"bytes"], "lib was aliased"
    write_glyph(source, native)
    assert len(native.layer.shapes[0].contours) == 2, "replace appended outlines"


@pytest.mark.parametrize(
    "field",
    ["point", "contour", "component", "anchor", "color", "guideline", "image", "lib"],
)
def test_unsupported_data_fails_before_destination_mutation(field):
    source, native = source_glyph(), NativeGlyph()
    if field == "point":
        source.contours[0].points[0].identifier = "point-id"
    elif field == "contour":
        source.contours[0].identifier = "contour-id"
    elif field == "component":
        source.components[0].identifier = "component-id"
    elif field == "anchor":
        source.anchors[0].identifier = "anchor-id"
    elif field == "color":
        source.anchors[0].color = "1,0,0,1"
    elif field == "guideline":
        source.appendGuideline({"x": 10, "y": 20, "angle": 0})
    elif field == "image":
        source.image.fileName = "example.png"
    else:
        source.lib["bad"] = object()
    before = copy.deepcopy(
        (
            native.width,
            native.height,
            native.unicodes,
            native.note,
            lib_values(native.lib),
        )
    )
    with pytest.raises((NotImplementedError, TypeError, ValueError)):
        write_glyph(source, native)
    assert (
        native.width,
        native.height,
        native.unicodes,
        native.note,
        lib_values(native.lib),
    ) == before, "metadata partially changed"
    assert not native.layer.shapes[0].contours and not native.components, (
        "geometry partially changed"
    )
    assert not native.anchors, "anchors partially changed"


def test_complex_target_is_refused_before_mutation():
    native = NativeGlyph()
    native.layer.shapes.append(copy.copy(native.layer.shapes[0]))
    with pytest.raises(NotImplementedError, match="shape"):
        write_glyph(source_glyph(), native)
    assert native.width == 100 and native.note == "old", "complex target changed"


def test_reopened_ufo_retains_export(tmp_path):
    native = NativeGlyph()
    write_glyph(source_glyph(), native)
    font = Font()
    font.addGlyph(to_ufo_glyph(native))
    path = tmp_path / "transfer.ufo"
    font.save(path)
    with Font.open(path) as reopened:
        assert recording(reopened["target"]) == recording(source_glyph()), (
            "saved UFO outline changed"
        )
        assert reopened["target"].lib["nested"]["list"] == [1, True, b"bytes"], (
            "saved lib changed"
        )


@pytest.mark.parametrize("kind", ["ufo", "fontparts", "defcon"])
def test_empty_source_clears_only_owned_fields(kind):
    native = NativeGlyph()
    write_glyph(source_glyph(kind), native)
    source = Glyph(name="empty") if kind == "ufo" else defcon.Glyph()
    if kind == "fontparts":
        source = RGlyph(source)
    write_glyph(source, native)
    assert not native.layer.shapes[0].contours, "empty outlines did not replace target"
    assert (
        not native.components
        and not native.anchors
        and lib_values(native.lib) == {"note": ""}
    ), "empty data did not replace target"
    assert native.note == "" and native.width == 0, "empty metadata was not normalized"


def test_cyclic_quadratic_and_closed_contour_transfer():
    source = source_glyph()
    pen = source.getPointPen()
    pen.beginPath()
    for position in ((0, 0), (100, 0), (100, 100)):
        pen.addPoint(position)
    pen.endPath()
    pen.beginPath()
    pen.addPoint((10, 20), "line")
    pen.addPoint((20, 40), "line", name="corner")
    pen.endPath()
    native = NativeGlyph()
    write_glyph(source, native)
    assert recording(to_ufo_glyph(native)) == recording(source), (
        "closed contour or implied qcurve changed"
    )


@pytest.mark.parametrize("field", ["width", "height", "anchor"])
def test_invalid_coordinates_do_not_mutate_destination(field):
    source, native = source_glyph(), NativeGlyph()
    if field == "anchor":
        source.anchors[0].x = float("nan")
    else:
        setattr(source, field, float("inf"))
    with pytest.raises(ValueError, match="finite"):
        write_glyph(source, native)
    assert native.note == "old" and not native.components, (
        "invalid coordinates changed target"
    )


def test_late_geometry_error_keeps_destination_unchanged():
    source, native = source_glyph(), NativeGlyph()
    source.contours[-1].points[-1].type = "curve"
    with pytest.raises(ValueError, match="two control"):
        write_glyph(source, native)
    assert native.note == "old" and not native.layer.shapes[0].contours, (
        "staging error changed target"
    )


def test_native_anchor_construction_error_keeps_destination_unchanged(monkeypatch):
    def bad_anchor(*args):
        raise TypeError("native rejected anchor")

    monkeypatch.setattr(sys.modules["fontgate"], "fgAnchor", bad_anchor)
    native = NativeGlyph()
    with pytest.raises(TypeError, match="native rejected"):
        write_glyph(source_glyph(), native)
    assert native.note == "old" and not native.layer.shapes[0].contours, (
        "native staging error changed target"
    )


def test_transformed_target_is_refused_before_mutation():
    native = NativeGlyph()
    native.layer.matrix = SimpleNamespace(asTuple=lambda: (2, 0, 0, 2, 0, 0))
    with pytest.raises(NotImplementedError, match="transformed"):
        write_glyph(source_glyph(), native)
    assert native.note == "old", "transformed target changed"


def test_selected_layer_anchors_do_not_read_body_alias():
    class BodyAliasGlyph(NativeGlyph):
        @property
        def anchors(self):
            raise AssertionError("body-layer anchor alias accessed")

    native = BodyAliasGlyph()
    write_glyph(source_glyph(), native)
    assert to_ufo_glyph(native).anchors[0].name == "top", "selected layer anchor lost"


@pytest.mark.parametrize("value", [-1, 0x110000, 0xD800])
def test_invalid_unicode_is_rejected_before_mutation(value):
    source, native = source_glyph(), NativeGlyph()
    source.unicodes = [value]
    with pytest.raises(ValueError, match="Unicode"):
        write_glyph(source, native)
    assert native.unicodes == [65] and native.note == "old", (
        "Unicode error mutated target"
    )


def test_import_transfer_does_not_import_native_modules():
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import fontlab_fontport.transfer; "
                "assert 'fontgate' not in sys.modules; assert 'fontlab' not in sys.modules"
            ),
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()


def test_native_lib_replacement_keeps_explicit_note_and_removes_old_keys():
    source, native = source_glyph(), NativeGlyph()
    source.lib["note"] = "conflicting lib note"
    write_glyph(source, native)
    assert native.note == "Transfer", "lib replacement erased explicit glyph note"
    assert native.lib.get("old") is None, "native lib replacement retained old key"
    assert native.lib.get("note") == "Transfer", (
        "explicit note did not win reserved key"
    )
    exported = to_ufo_glyph(native)
    assert exported.note == "Transfer" and exported.lib["note"] == "Transfer", (
        "native note not exported"
    )


def test_native_plain_text_note_is_not_misparsed_as_a_plist():
    class RawNoteLib(Lib):
        def get(self, key):
            if key == "note":
                raise RuntimeError("plist parsing errorexpected <")
            return super().get(key)

    class RawNoteGlyph(NativeGlyph):
        @property
        def note(self):
            return self.lib.data["note"]

    native = RawNoteGlyph()
    native.lib = RawNoteLib(note="Native note – Żółć", nested={"values": [1, 2]})
    exported = to_ufo_glyph(native)
    assert exported.note == "Native note – Żółć", "plain text note was lost"
    assert exported.lib["nested"] == {"values": [1, 2]}, "other data changed"
