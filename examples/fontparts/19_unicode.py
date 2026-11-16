# this_file: examples/fontparts/19_unicode.py
"""Expected: A unicodes becomes the requested value on an owned copy."""

from _owned import owned


def run(font=None):
    font = owned(font)
    glyph = font["A"]
    before = list(glyph.unicodes)
    glyph.unicodes = [0xE123]
    after = list(glyph.unicodes)
    expected = [0xE123]
    return {"before": before, "after": after, "ok": after == expected}
