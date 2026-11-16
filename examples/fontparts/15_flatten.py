# this_file: examples/fontparts/15_flatten.py
"""Expected: Flatten A into the existing fontport_flat glyph using a staged edit."""

from _owned import owned


def run(font=None):
    font = owned(font)
    from fly.fp.recipes import flatten

    before = len(font["fontport_flat"].contours)
    glyph = flatten(font, "A", "fontport_flat")
    return {
        "before": before,
        "after": len(glyph.contours),
        "ok": len(glyph.components) == 0 and len(glyph.contours) > before,
    }
