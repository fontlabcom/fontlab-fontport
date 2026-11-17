# this_file: tests/test_fast_reads.py
"""Direct glyph lookups and bulk summaries agree with full per-glyph reads."""

import pytest
from test_live import Backend
from ufoLib2 import Font

from fontlab_fontport.errors import StaleObjectError
from fontlab_fontport.glyphrun import layout_text
from fontlab_fontport.groups import _text
from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend


def ufo_font():
    font = Font()
    font.info.unitsPerEm = 1000
    for name, codes, width in (("A", [65], 600), ("V", [86, 118], 550), ("x", [], 0)):
        glyph = font.newGlyph(name)
        glyph.width = width
        glyph.unicodes = codes
    font.newLayer("background").newGlyph("B").width = 300
    font.groups["public.kern1.A"] = ["A"]
    font.groups["public.kern2.V"] = ["V"]
    font.kerning[("public.kern1.A", "public.kern2.V")] = -80
    return font


class CountingBackend(UFOBackend):
    """Memory backend that records which read paths a caller used.

    ``check_glyph`` mirrors the native backend, whose glyph liveness check is a
    direct lookup; without it, liveness falls back to listing every name.
    """

    def __init__(self, font=None):
        super().__init__(font)
        self.calls = []

    def glyph_names(self, layer):
        self.calls.append(("glyph_names", layer))
        return super().glyph_names(layer)

    def check_glyph(self, name, layer):
        if not self.has_glyph(name, layer):
            raise StaleObjectError("Glyph has been removed")


class PlainBackend(Backend):
    """Fake backend with neither has_glyph nor glyph_summaries."""

    def __init__(self):
        super().__init__()
        self.calls = []

    def glyph_names(self, layer):
        self.calls.append(("glyph_names", layer))
        return super().glyph_names(layer)


def test_memory_has_glyph_when_names_vary_then_matches_layer_contents():
    backend = UFOBackend(ufo_font())
    assert backend.has_glyph("A", "public.default")
    assert not backend.has_glyph("B", "public.default")
    assert backend.has_glyph("B", "background")
    assert not backend.has_glyph("A", "background")
    assert not backend.has_glyph("A", "missing-layer"), "Unknown layer is absent"


def test_memory_glyph_summaries_when_read_then_match_each_glyph():
    backend = UFOBackend(ufo_font())
    rows = {row[0]: row for row in backend.glyph_summaries("public.default")}
    assert rows == {
        "A": ("A", (65,), 600),
        "V": ("V", (86, 118), 550),
        "x": ("x", (), 0),
    }
    assert all(isinstance(row[1], tuple) for row in rows.values())
    assert list(backend.glyph_summaries("background")) == [("B", (), 300)]


@pytest.mark.parametrize("make", [lambda: RFont(UFOBackend(ufo_font())), lambda: RFont(PlainBackend())])
def test_contains_when_present_or_missing_then_agrees_with_keys(make):
    font = make()
    names = set(font.keys())
    for name in (*names, "missing", "B"):
        assert (name in font) == (name in names), name
        assert (name in font.defaultLayer) == (name in names), name
    for layer in font.layers:
        layer_names = set(layer.keys())
        for name in (*layer_names, "missing", "A", "B"):
            assert (name in layer) == (name in layer_names), (layer.name, name)
    for name in names:
        assert font[name].name == name
    with pytest.raises(KeyError):
        font["missing"]


def test_contains_when_backend_has_glyph_then_no_full_name_listing():
    backend = CountingBackend(ufo_font())
    font = RFont(backend)
    backend.calls.clear()
    assert "A" in font and "missing" not in font
    assert "B" in font.getLayer("background")
    glyph = font["A"]
    assert ("glyph_names", "public.default") not in backend.calls, backend.calls
    assert glyph.width == 600


def test_contains_when_backend_lacks_has_glyph_then_falls_back_to_keys():
    backend = PlainBackend()
    font = RFont(backend)
    backend.calls.clear()
    assert "A" in font and "missing" not in font
    assert ("glyph_names", "public.default") in backend.calls


def test_default_layer_when_resolved_twice_then_same_cached_layer():
    font = RFont(UFOBackend(ufo_font()))
    assert font.defaultLayer is font.defaultLayer
    assert font.defaultLayer.name == "public.default"
    assert font.defaultLayer is font.getLayer("public.default")


@pytest.mark.parametrize("make", [lambda: RFont(UFOBackend(ufo_font())), lambda: RFont(PlainBackend())])
def test_glyph_summaries_when_read_then_match_per_glyph_reads(make):
    font = make()
    expected = {(g.name, tuple(g.unicodes), g.width) for g in font}
    summaries = font.glyph_summaries()
    assert isinstance(summaries, tuple)
    assert set(summaries) == expected and len(summaries) == len(expected)
    for layer in font.layers:
        rows = {(g.name, tuple(g.unicodes), g.width) for g in layer}
        assert set(font.glyph_summaries(layer.name)) == rows, layer.name


@pytest.mark.parametrize("value", ["", "a\x00b", "tab\there", "\x1f"])
def test_group_text_when_empty_or_control_then_value_error(value):
    with pytest.raises(ValueError):
        _text(value)


@pytest.mark.parametrize("value", [None, 1, b"A"])
def test_group_text_when_not_str_then_type_error(value):
    with pytest.raises(TypeError):
        _text(value)


def test_group_text_when_ordinary_then_returned():
    assert _text("public.kern1.A") == "public.kern1.A"
    assert _text("A\x7f") == "A\x7f", "Only C0 controls are rejected"


def test_layout_text_when_summaries_available_then_same_run_as_per_glyph():
    with_summaries = RFont(UFOBackend(ufo_font()))

    class NoSummaries(RFont):
        glyph_summaries = None

    without = NoSummaries(UFOBackend(ufo_font()))
    for text in ("AVA", "AvxQ", ""):
        a, b = layout_text(with_summaries, text), layout_text(without, text)
        assert [(g.name, g.x, g.index) for g in a.glyphs] == [
            (g.name, g.x, g.index) for g in b.glyphs
        ], text
        assert a.advance == b.advance and a.diagnostics == b.diagnostics, text


def native_backend():
    from types import SimpleNamespace as NS

    from fontlab_fontport import host

    widths = {("A", "Regular"): 600, ("V", "Regular"): 550, ("A", "aux"): 610}
    calls = []

    def find_name(name):
        def find_layer(layer):
            if (name, layer) not in widths:
                return None
            return NS(isNull=False, advanceWidth=widths[name, layer])

        return NS(findLayer=find_layer, layers=[NS(name="Regular"), NS(name="aux")])

    package = NS(
        masters=["Regular"],
        fgPackage=[NS(name="A", unicodes=[65]), NS(name="V", unicodes=[86, 118])],
        findName=find_name,
    )
    backend = host.NativeFontBackend.__new__(host.NativeFontBackend)
    backend._package = lambda: package

    def target(name, layer):
        if (name, layer) not in widths:
            raise KeyError(name)
        return package, None, None

    def layer_names():
        calls.append("layer_names")
        return ("Regular", "aux")

    backend._target = target
    backend.layer_names = layer_names
    return backend, calls


def test_native_summaries_when_master_or_layer_then_rows_and_names_agree():
    backend, calls = native_backend()
    assert backend.glyph_summaries("Regular") == (("A", (65,), 600), ("V", (86, 118), 550))
    assert backend.glyph_names("Regular") == ("A", "V")
    assert calls == [], "A master layer skips the font-wide layer scan"
    assert backend.glyph_summaries("aux") == (("A", (65,), 610),)
    assert backend.glyph_names("aux") == ("A",)
    with pytest.raises(KeyError):
        backend.glyph_names("missing")
    with pytest.raises(KeyError):
        backend.glyph_summaries("missing")


def test_native_has_glyph_when_target_missing_then_false():
    backend, _ = native_backend()
    assert backend.has_glyph("A", "aux")
    assert not backend.has_glyph("V", "aux")
    assert not backend.has_glyph("missing", "Regular")
