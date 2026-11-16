# this_file: src/fontlab_fontport/recipes.py
"""Small recipes using the real fontPens and fontTools implementations."""

from io import StringIO

from fontPens.digestPointPen import DigestPointPen
from fontPens.flattenPen import FlattenPen
from fontTools.feaLib.parser import Parser
from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen


def digest(glyph):
    pen = DigestPointPen()
    glyph.drawPoints(pen)
    return pen.getDigest()


def bounds(glyph, glyph_set=None):
    pen = BoundsPen(glyph_set)
    glyph.draw(pen)
    return pen.bounds


def control_bounds(glyph, glyph_set=None):
    """FontLab boundingBox includes off-curve controls, not just curve extrema."""
    pen = ControlBoundsPen(glyph_set)
    glyph.draw(pen)
    return pen.bounds


def flatten(font, source, destination, *, approximate_segment_length=10):
    """Commit once on the integer grid; <=0.5-unit error per coordinate.

    Uses fontTools otRound (nearest integer, ties toward positive infinity).
    Width is preserved. Curves/components are flattened before rounding.
    """
    recording = DecomposingRecordingPen(font)
    font[source].draw(recording)
    width = font[source].width
    with font.edit_glyph(destination, undo_name="FontParts flatten outlines") as glyph:
        glyph.clearContours()
        glyph.clearComponents()
        pen = FlattenPen(
            RoundingPen(glyph.getPen()),
            approximateSegmentLength=approximate_segment_length,
        )
        recording.replay(pen)
        glyph.width = width
    return font[destination]


def transform_into(font, source, destination, transformation):
    recording = RecordingPen()
    font[source].draw(recording)
    with font.edit_glyph(
        destination, undo_name="FontParts transformed outlines"
    ) as glyph:
        glyph.clearContours()
        glyph.clearComponents()
        recording.replay(TransformPen(glyph.getPen(), transformation))


def parse_features(text, glyph_names, *, classes=None):
    """Parse native code with separate native OT classes; never mutate code.

    Group names/members are glyph-name tokens accepted by feaLib. Errors and
    unsupported syntax propagate with source locations, not a fake success.
    """
    from fontTools.feaLib.ast import GlyphName

    declarations = []
    for name, members in (classes or {}).items():
        if name.startswith(("public.kern1.", "public.kern2.")):
            continue
        name = name.removeprefix("@")
        declarations.append(
            "@"
            + name
            + " = ["
            + " ".join(GlyphName(g).asFea() for g in members)
            + "];\n"
        )
    return Parser(
        StringIO("".join(declarations) + text),
        glyphNames=glyph_names,
        followIncludes=False,
    ).parse()
