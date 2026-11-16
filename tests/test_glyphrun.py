# this_file: tests/test_glyphrun.py
"""Sequence placement uses upstream UFO kerning without mutating its model."""

import pickle

import pytest
from ufoLib2 import Font

from fontlab_fontport.glyphrun import layout_names, layout_text


def fixture_font():
    font = Font()
    font.info.unitsPerEm = 1000
    for name, code in (("A", 65), ("V", 86)):
        glyph = font.newGlyph(name)
        glyph.width = 600
        glyph.unicodes = [code]
    font.groups["public.kern1.A"] = ["A"]
    font.groups["public.kern2.V"] = ["V"]
    font.kerning[("public.kern1.A", "public.kern2.V")] = -80
    return font


def test_text_uses_advances_and_group_kerning_without_mutation():
    font = fixture_font()
    before = pickle.dumps(font)
    run = layout_text(font, "AVA")
    assert [(g.name, g.x) for g in run.glyphs] == [("A", 0), ("V", 520), ("A", 1120)]
    assert run.advance == 1720 and run.diagnostics == ()
    assert [g.index for g in run.glyphs] == [0, 1, 2], (
        "Repeated glyphs need distinct occurrence identities"
    )
    assert [g.x for g in layout_text(font, "AVA", kerning=False).glyphs] == [
        0,
        600,
        1200,
    ]
    assert pickle.dumps(font) == before, (
        "Preview placement must leave the complete font unchanged"
    )


def test_explicit_zero_exception_and_removed_exception_use_ufo_fallback():
    font = fixture_font()
    font.kerning[("A", "V")] = 0
    assert layout_text(font, "AV").glyphs[1].x == 600, (
        "Explicit zero overrides group fallback"
    )
    del font.kerning[("A", "V")]
    assert layout_text(font, "AV").glyphs[1].x == 520, (
        "Deleting an exception restores its group pair"
    )


def test_rtl_changes_positions_and_keeps_positive_glyph_advances():
    run = layout_text(fixture_font(), "AVA", direction="rtl")
    assert [g.x for g in run.glyphs] == [-600, -1120, -1720]
    assert all(g.advance == 600 for g in run.glyphs), (
        "Direction must not mirror outlines"
    )
    assert run.advance == 1720


def test_exact_name_tokens_and_unknown_unicode_have_visible_placeholders():
    font = fixture_font()
    run = layout_names(font, "/V /A /missing")
    assert [g.name for g in run.glyphs] == ["V", "A", None]
    assert run.glyphs[-1].label == "/missing" and run.glyphs[-1].advance == 500
    assert "missing" in run.diagnostics[0]
    run = layout_text(font, "AΩ")
    assert run.glyphs[1].name is None and run.glyphs[1].label == "Ω"
    assert "Ω" in run.diagnostics[0] and run.advance == 1100
    assert layout_text(font, "").glyphs == ()
    with pytest.raises(ValueError, match="slash"):
        layout_names(font, "A V")


def test_invalid_direction_or_nonfinite_width_is_rejected():
    font = fixture_font()
    with pytest.raises(ValueError, match="direction"):
        layout_text(font, "A", direction="vertical")
    font["A"].width = float("nan")
    with pytest.raises(ValueError, match="finite"):
        layout_text(font, "A")


def test_nonfinite_kerning_and_accumulated_overflow_are_rejected():
    font = fixture_font()
    font.kerning[("A", "V")] = float("inf")
    with pytest.raises(ValueError, match="finite"):
        layout_text(font, "AV")
    font["A"].width = 1e308
    with pytest.raises(ValueError, match="finite"):
        layout_text(font, "AA", kerning=False)


def test_kerning_disabled_does_not_access_unsupported_backend_properties():
    font = fixture_font()

    class NoKerning:
        info = font.info

        def keys(self):
            return font.keys()

        def __getitem__(self, name):
            return font[name]

        @property
        def kerning(self):
            raise NotImplementedError("Kerning not supported")

    assert layout_text(NoKerning(), "AV", kerning=False).advance == 1200
    with pytest.raises(NotImplementedError, match="Kerning"):
        layout_text(NoKerning(), "AV")


def test_placeholder_uses_default_upm_but_refuses_invalid_upm():
    font = fixture_font()
    font.info.unitsPerEm = None
    assert layout_text(font, "Ω").advance == 500
    font.info.unitsPerEm = 0
    with pytest.raises(ValueError, match="positive"):
        layout_text(font, "Ω")


@pytest.mark.parametrize("layout", [layout_text, layout_names])
def test_empty_preview_needs_no_model_and_none_is_not_silently_empty(layout):
    assert layout(None, "").glyphs == ()
    with pytest.raises(TypeError, match="string"):
        layout(None, None)


@pytest.mark.parametrize("backend", ["defcon", "fontparts"])
def test_upstream_models_supply_the_same_placement(backend):
    if backend == "defcon":
        from defcon import Font as Model
    else:
        from fontParts.fontshell import RFont as Model
    font = Model()
    for name, code in (("A", 65), ("V", 86)):
        glyph = font.newGlyph(name)
        glyph.width = 500
        glyph.unicodes = [code]
    font.kerning[("A", "V")] = -60
    assert [g.x for g in layout_text(font, "AV").glyphs] == [0, 440]
