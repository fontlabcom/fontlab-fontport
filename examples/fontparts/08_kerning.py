# this_file: examples/fontparts/08_kerning.py
"""Expected: Set explicit A/V kerning to an integer, preserving other pairs."""

from _owned import owned


def run(font=None):
    font = owned(font)
    before = font.kerning.get(("A", "V"))
    expected = before - 1 if before is not None else -37
    font.kerning["A", "V"] = expected
    after = font.kerning["A", "V"]
    return {"before": before, "after": after, "ok": after == expected}
