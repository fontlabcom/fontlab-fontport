# this_file: examples/fontparts/02_geometry.py
"""Expected: Replace fontport_probe contours with one triangle, one staged write."""

from _owned import owned


def run(font=None):
    font = owned(font)
    with font.edit_glyph("fontport_probe", undo_name="Example triangle") as glyph:
        glyph.clearContours()
        pen = glyph.getPen()
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.lineTo((0, 100))
        pen.closePath()
    count = len(font["fontport_probe"].contours)
    return {"before": "owned empty probe", "after": count, "ok": count == 1}
