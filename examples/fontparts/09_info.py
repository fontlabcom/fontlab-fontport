# this_file: examples/fontparts/09_info.py
"""Expected: Apply Unicode designer text with one batch call (native extra checkpoint documented)."""

from _owned import owned


def run(font=None):
    """Expected: the requested edit succeeds in the default editing mode."""
    font = owned(font)
    before = font.info.openTypeNameDesigner
    font.info.apply({"openTypeNameDesigner": "Fontport owned Ω"})
    after = font.info.openTypeNameDesigner
    return {"before": before, "after": after, "ok": after == "Fontport owned Ω"}
