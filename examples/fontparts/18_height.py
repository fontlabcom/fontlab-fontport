# this_file: examples/fontparts/18_height.py
"""Expected: A height becomes the requested value on an owned copy."""

from _owned import owned


def run(font=None):
    font = owned(font)
    glyph = font["A"]
    before = glyph.height
    expected = before + 7
    glyph.height = expected
    after = glyph.height
    return {"before": before, "after": after, "ok": after == expected}
