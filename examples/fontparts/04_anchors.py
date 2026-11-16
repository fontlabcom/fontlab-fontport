# this_file: examples/fontparts/04_anchors.py
"""Expected: Append named integral top anchor at (50, 700)."""

from _owned import owned


def run(font=None):
    font = owned(font)
    before = len(font["fontport_probe"].anchors)
    font["fontport_probe"].appendAnchor("top", (50, 700))
    anchor = font["fontport_probe"].anchors[-1]
    return {
        "before": before,
        "after": len(font["fontport_probe"].anchors),
        "position": anchor.position,
        "ok": len(font["fontport_probe"].anchors) == before + 1
        and anchor.position == (50, 700),
    }
