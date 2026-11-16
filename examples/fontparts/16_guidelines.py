# this_file: examples/fontparts/16_guidelines.py
"""Expected: native glyph.guidelines refusal leaves the glyph unchanged; UFO backend adds the guide."""

from _owned import owned
from fly.fp.errors import UnsupportedCapability


def run(font=None):
    font = owned(font)
    before = len(font["fontport_probe"].guidelines)
    try:
        font["fontport_probe"].appendGuideline((0, 50), 0, name="example baseline")
    except UnsupportedCapability as error:
        return {
            "before": before,
            "after": len(font["fontport_probe"].guidelines),
            "capability": error.capability,
            "ok": error.capability == "glyph.guidelines"
            and len(font["fontport_probe"].guidelines) == before,
        }
    return {
        "before": before,
        "after": len(font["fontport_probe"].guidelines),
        "ok": len(font["fontport_probe"].guidelines) == before + 1,
    }
