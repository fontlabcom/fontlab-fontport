# this_file: examples/fontparts/03_clear_contours.py
"""Expected: Clear triangle contours; preserve anchors/components."""

from _owned import owned


def run(font=None):
    font = owned(font)
    before = len(font["fontport_probe"].contours)
    with font.edit_glyph("fontport_probe", undo_name="Example clear contours") as glyph:
        glyph.clearContours()
    after = len(font["fontport_probe"].contours)
    return {"before": before, "after": after, "ok": after == 0}
