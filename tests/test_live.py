# this_file: tests/test_live.py
import gc
import sys
import traceback
from copy import deepcopy

import pytest
from fontParts.base import BaseFont, BaseInfo, BaseLayer
from fontParts.fontshell import RGlyph
from ufoLib2.objects import Glyph

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.live import RFont


def test_live_model_when_cycles_collected_then_no_destructor_errors(monkeypatch):
    gc.collect()
    errors = []
    monkeypatch.setattr(sys, "unraisablehook", errors.append)
    for _ in range(20):
        font = RFont(Backend())
        glyph = font["A"]
        glyph.width = 600
        del glyph, font
    gc.collect()
    for error in errors:
        traceback.print_exception(error.exc_value)
    assert not errors, [
        "".join(traceback.format_exception(error.exc_value)) for error in errors
    ]


class Backend:
    def __init__(self):
        self.layers = {
            n: {"A": Glyph("A", width=500, unicodes=[65])}
            for n in ("public.default", "background")
        }
        self.writes = []
        self.info = {}
        self.fail = False

    def layer_names(self):
        return tuple(self.layers)

    def default_layer(self):
        return "public.default"

    def glyph_names(self, layer):
        return tuple(self.layers[layer])

    def read_glyph(self, name, layer):
        return deepcopy(self.layers[layer][name])

    def write_glyph(self, name, layer, source):
        if self.fail:
            raise RuntimeError("write failed")
        g = Glyph(
            name,
            width=source.width,
            height=source.height,
            unicodes=list(source.unicodes),
            note=source.note,
            lib=dict(source.lib),
        )
        source.drawPoints(g.getPointPen())
        g.anchors = [dict(a) for a in source.anchors]
        g.guidelines = [dict(a) for a in source.guidelines]
        self.layers[layer][name] = g
        self.writes.append((name, layer))

    def new_glyph(self, name, layer):
        self.layers[layer][name] = Glyph(name)

    def remove_glyph(self, name, layer):
        del self.layers[layer][name]

    def get_info(self, attr):
        return self.info.get(attr)

    def get_groups(self):
        return {}

    def set_info(self, attr, value):
        self.info[attr] = value

    def path(self):
        return None

    def save(self, path):
        self.saved = path

    def close(self):
        self.closed = True


def test_objects_and_changes():
    b = Backend()
    f = RFont(b)
    assert isinstance(f, BaseFont) and isinstance(f.info, BaseInfo)
    assert len(f.layers) == 2 and isinstance(f.layers[0], BaseLayer)
    g = f["A"]
    assert isinstance(g, RGlyph) and g is f["A"]
    assert g.font is f and g.layer is f.defaultLayer
    assert "A" in f and [x.name for x in f] == ["A"]
    assert f.getCharacterMapping() == {65: ("A",)}
    g.width = 600
    assert b.layers["public.default"]["A"].width == 600
    g.appendAnchor("top", (10, 20))
    g.lib["key"] = "value"
    pen = g.getPen()
    pen.moveTo((0, 0))
    pen.lineTo((100, 0))
    pen.lineTo((100, 100))
    pen.closePath()
    g[0].points[0].x = 5
    assert b.layers["public.default"]["A"].contours[0].points[0].x == 5
    assert b.layers["public.default"]["A"].lib["key"] == "value"
    assert b.layers["public.default"]["A"].anchors[0].name == "top"
    f.info.familyName = "Test"
    assert f.info.familyName == "Test"
    f.getLayer("background").newGlyph("B")
    assert "B" in b.layers["background"]
    f.getLayer("background").removeGlyph("B")
    f.save("/tmp/live.ufo")
    assert b.saved == "/tmp/live.ufo"


def test_refresh_remove_close_and_failure():
    b = Backend()
    f = RFont(b)
    g = f["A"]
    b.fail = True
    with pytest.raises(RuntimeError, match="write failed"):
        g.width = 700
    assert g.width == 500
    b.fail = False
    b.layers["public.default"]["A"].width = 800
    f.refresh()
    assert f["A"].width == 800
    with pytest.raises(RuntimeError):
        g.width = 900
    g = f["A"]
    f.removeGlyph("A")
    f.newGlyph("A")
    with pytest.raises(RuntimeError):
        g.width = 100
    g = f["A"]
    f.close()
    with pytest.raises(RuntimeError):
        g.width = 100
    with pytest.raises(RuntimeError):
        f.keys()


def test_roundtrip_metadata_components_and_layers():
    b = Backend()
    source = b.layers["background"]["A"]
    source.height = 700
    source.note = "source note"
    source.lib["nested"] = {"values": [1, 2]}
    source.appendAnchor({"name": "top", "x": 20, "y": 30})
    source.appendGuideline({"x": 10, "y": 0, "angle": 90, "name": "vertical"})
    pen = source.getPointPen()
    pen.addComponent("base", (1, 0, 0, 1, 20, 30))
    f = RFont(b)
    g = f.getLayer("background")["A"]
    assert g.font is f and g.layer.name == "background"
    assert g.height == 700 and g.note == "source note"
    assert g.components[0].baseGlyph == "base"
    assert g.guidelines[0].name == "vertical"
    g.unicodes = [66, 67]
    g.height = 750
    assert b.layers["background"]["A"].unicodes == [66, 67]
    assert b.layers["background"]["A"].lib["nested"] == {"values": [1, 2]}
    assert b.layers["public.default"]["A"].unicodes == [65]
    old_layer = g.layer
    f.refresh()
    with pytest.raises(RuntimeError):
        old_layer.newGlyph("C")
    assert dict(f.groups) == {}, "group access must follow the new backend contract"


def test_failed_save_close_and_rename():
    class FailingBackend(Backend):
        def save(self, path):
            raise OSError("save failed")

        def close(self):
            raise OSError("close failed")

    f = RFont(FailingBackend())
    with pytest.raises(OSError, match="save failed"):
        f.save("/tmp/fail.ufo")
    with pytest.raises(OSError, match="close failed"):
        f.close()
    g = f["A"]
    with pytest.raises(RuntimeError, match="rename"):
        g.name = "B"
    assert g.name == "A"
    g.width = 650
    assert f["A"].width == 650


def test_glyph_order_tracks_native_default_layer_order():
    backend = Backend()
    font = RFont(backend)
    assert font.glyphOrder == ("A",), "A live font must expose its native glyph order"
    font.newGlyph("B")
    assert font.glyphOrder == ("A", "B"), "New glyphs must appear in native order"
    font.removeGlyph("A")
    assert font.glyphOrder == ("B",), "Removed glyphs must leave the order"
    font.close()
    with pytest.raises(RuntimeError, match="closed"):
        _ = font.glyphOrder


class GlobalBackend(Backend):
    """FontLab metadata belongs to the glyph, unlike ordinary UFO layers."""

    glyph_global_fields = ("unicodes", "note", "lib")

    def write_glyph(self, name, layer, source):
        super().write_glyph(name, layer, source)
        for glyphs in self.layers.values():
            if name in glyphs:
                for field in self.glyph_global_fields:
                    setattr(glyphs[name], field, deepcopy(getattr(source, field)))


@pytest.mark.parametrize("first", ["public.default", "background"])
def test_global_metadata_is_shared_by_preloaded_layers_and_survives_rollback(first):
    backend = GlobalBackend()
    font = RFont(backend)
    glyphs = {layer.name: layer["A"] for layer in font.layers}
    other = next(name for name in glyphs if name != first)
    a, b = glyphs[first], glyphs[other]
    a.unicodes = [66, 0x10000]
    a.note = "new global note"
    a.lib["nested"] = {"value": [1, 2]}
    assert (b.unicodes, b.note, dict(b.lib)) == (
        (66, 0x10000),
        "new global note",
        {"nested": {"value": [1, 2]}},
    ), "Already loaded sibling fields must immediately reflect accepted global edits"
    b.width = 640
    assert backend.read_glyph("A", first).note == "new global note", (
        "A width edit must preserve global metadata"
    )
    backend.fail = True
    with pytest.raises(RuntimeError, match="write failed"):
        b.lib["rejected"] = "must disappear"
    assert dict(b.lib) == dict(a.lib) == {"nested": {"value": [1, 2]}}, (
        "Rollback must use the synchronized accepted state"
    )
    backend.fail = False
    b.note = "edited through the other layer"
    a.height = 720
    for layer in backend.layers:
        state = backend.read_glyph("A", layer)
        assert (state.unicodes, state.note, state.lib) == (
            [66, 0x10000],
            "edited through the other layer",
            {"nested": {"value": [1, 2]}},
        ), "Either layer must retain the latest global state after recovery"


def _triangle(glyph, origin=(0, 0)):
    x, y = origin
    pen = glyph.getPen()
    pen.moveTo((x, y))
    pen.lineTo((x + 100, y))
    pen.lineTo((x + 100, y + 100))
    pen.closePath()


def _component_backend():
    backend = Backend()
    for glyphs in backend.layers.values():
        _triangle(glyphs["A"])
        glyphs["C"] = Glyph("C", width=500)
        glyphs["C"].getPointPen().addComponent("A", (1, 0, 0, 1, 15, 30))
        glyphs["unused"] = Glyph("unused")
    return backend


def test_component_bounds_are_lazy_and_invalidate_after_base_edits():
    backend = _component_backend()
    reads = []
    original = backend.read_glyph

    def read(name, layer):
        reads.append((name, layer))
        return original(name, layer)

    backend.read_glyph = read
    font = RFont(backend)
    dependent = font["C"]  # Request the dependent before its base.
    assert tuple(dependent.bounds) == (15, 30, 115, 130), (
        "Components must resolve their layer siblings"
    )
    assert (dependent.leftMargin, dependent.rightMargin) == (15, 385), (
        "Margins must include component geometry"
    )
    assert set(reads) == {("C", "public.default"), ("A", "public.default")}, (
        "Unrelated glyphs and layers must remain unloaded"
    )
    font["A"][0].points[0].x = -50
    assert tuple(dependent.bounds) == (-35, 30, 115, 130), (
        "Cached component bounds must observe base edits"
    )
    assert backend.writes == [("A", "public.default")], (
        "Derived bounds invalidation must not rewrite a dependent glyph"
    )
    assert tuple(font.getLayer("background")["C"].bounds) == (15, 30, 115, 130), (
        "Layers must resolve independent outlines"
    )


def test_nested_affine_and_mixed_component_bounds():
    backend = _component_backend()
    glyphs = backend.layers["public.default"]
    _triangle(glyphs["C"], (-200, -100))
    glyphs["D"] = Glyph("D", width=900)
    glyphs["D"].getPointPen().addComponent("C", (0, 2, -1, 0, 40, -10))
    font = RFont(backend)
    assert tuple(font["C"].bounds) == (-200, -100, 115, 130), (
        "Mixed bounds must include contours and components"
    )
    assert tuple(font["D"].bounds) == (-90, -410, 140, 220), (
        "Nested affine transforms must compose through upstream pens"
    )
    font["A"][0].points[1].x = 300
    assert tuple(font["D"].bounds) == (-90, -410, 140, 620), (
        "Invalidation must reach nested dependents"
    )


def test_missing_component_base_can_be_created_after_cached_empty_bounds():
    backend = _component_backend()
    del backend.layers["public.default"]["A"]
    font = RFont(backend)
    glyph = font["C"]
    assert glyph.bounds is None, (
        "Missing bases follow upstream defcon empty bounds semantics"
    )
    base = font.newGlyph("A")
    _triangle(base)
    assert tuple(glyph.bounds) == (15, 30, 115, 130), (
        "Adding a missing base must invalidate cached component bounds"
    )


def test_cyclic_dependencies_refuse_without_poisoning_cached_models():
    backend = _component_backend()
    backend.layers["public.default"]["A"].getPointPen().addComponent(
        "C", (1, 0, 0, 1, 0, 0)
    )
    font = RFont(backend)
    with pytest.raises(
        UnsupportedCapability, match=r"components.unresolvedBase.*[Cc]yclic"
    ):
        font["C"]
    backend.layers["public.default"]["A"].components.clear()
    assert tuple(font["C"].bounds) == (15, 30, 115, 130), (
        "Failed dependency loading must leave the layer usable"
    )
    with pytest.raises(
        UnsupportedCapability, match=r"components.unresolvedBase.*[Cc]yclic"
    ):
        font["A"].appendComponent("C")
    assert len(font["A"].components) == 0, (
        "Rejected component cycles must not alter accepted geometry"
    )
    with pytest.raises(
        UnsupportedCapability, match=r"components.unresolvedBase.*[Cc]yclic"
    ):
        font["C"].components[0].baseGlyph = "C"
    assert font["C"].components[0].baseGlyph == "A", (
        "Rejected retargeting must retain its previous base"
    )
    font["A"].width = 600
    assert backend.layers["public.default"]["A"].width == 600, (
        "A successful edit must remain possible after rejection"
    )


def test_component_bounds_survive_rejection_removal_and_stale_handles():
    backend = _component_backend()
    font = RFont(backend)
    old = font["C"]
    assert tuple(old.bounds) == (15, 30, 115, 130)
    backend.fail = True
    with pytest.raises(RuntimeError, match="write failed"):
        font["A"][0].points[0].x = -50
    assert tuple(old.bounds) == (15, 30, 115, 130), (
        "Rejected base edits must invalidate dependent caches after rollback"
    )
    backend.fail = False
    with pytest.raises(RuntimeError, match="rename"):
        font["A"].name = "renamed"
    assert tuple(old.bounds) == (15, 30, 115, 130), (
        "Rejected rename must preserve the shared defcon layer index"
    )
    font["A"][0].points[0].x = -50
    assert tuple(old.bounds) == (-35, 30, 115, 130)
    font.removeGlyph("A")
    assert old.bounds is None, "Deleted bases must disappear from dependent bounds"
    _triangle(font.newGlyph("A"), (20, 0))
    assert tuple(old.bounds) == (35, 30, 135, 130), (
        "Recreated bases must notify existing dependents"
    )
    font.refresh()
    with pytest.raises(RuntimeError, match="Stale"):
        old.width = 900
    with pytest.raises(RuntimeError, match="Stale"):
        old.width = 901
    with pytest.raises(RuntimeError, match="Stale"):
        _ = old.width
    assert tuple(font["C"].bounds) == (35, 30, 135, 130), (
        "Stale handles must not mutate refreshed models"
    )
