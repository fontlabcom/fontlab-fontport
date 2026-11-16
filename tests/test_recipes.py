# this_file: tests/test_recipes.py
from fontPens.marginPen import MarginPen
from fontPens.transformPointPen import TransformPointPen

from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend
from fontlab_fontport.recipes import (
    bounds,
    digest,
    flatten,
    parse_features,
    transform_into,
)


def test_real_pens_on_live_glyphs_match_ufo_export():
    from test_interchange import source_font

    backend = UFOBackend(source_font())
    font = RFont(backend)
    assert digest(font["A"]) == digest(backend.font["A"])
    assert bounds(font["A"], font) == tuple(font["A"].bounds)
    font.newGlyph("flat")
    assert digest(flatten(font, "A", "flat")) == digest(font["A"])
    font.newGlyph("shifted")
    transform_into(font, "A", "shifted", (1, 0, 0, 1, 50, 100))
    assert bounds(font["shifted"], font) == (50, 100, 100, 200)
    pen = MarginPen(font, 20, isHorizontal=False)
    font["A"].draw(pen)
    assert pen.getMargins() is not None
    with font.edit_glyph("shifted") as target:
        target.clearContours()
        font["A"].drawPoints(
            TransformPointPen(target.getPointPen(), (1, 0, 0, 1, 20, 30))
        )
    assert bounds(font["shifted"], font) == (20, 30, 70, 130)


def test_fealib_parses_native_text_with_separate_classes():
    document = parse_features(
        "feature liga { sub @test A by V; } liga;\n",
        ["A", "V"],
        classes={"test": ["A"]},
    )
    assert document.statements[-1].name == "liga"
