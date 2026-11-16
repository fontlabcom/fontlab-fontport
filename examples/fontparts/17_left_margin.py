# this_file: examples/fontparts/17_left_margin.py
"""Expected: The flattened glyph leftMargin becomes the requested value on an owned copy."""

from _owned import owned


def run(font=None):
    font = owned(font)
    glyph = font["fontport_flat"]
    before = glyph.leftMargin
    expected = before + 3
    glyph.leftMargin = expected
    after = glyph.leftMargin
    return {"before": before, "after": after, "ok": after == expected}
