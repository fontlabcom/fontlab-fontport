# this_file: examples/fontparts/05_components.py
"""Expected: Append A component to precreated empty fontport_component."""

from _owned import owned


def run(font=None):
    font = owned(font)
    before = len(font["fontport_component"].components)
    font["fontport_component"].appendComponent("A", offset=(10, 20))
    after = font["fontport_component"].components[-1]
    return {
        "before": before,
        "after": len(font["fontport_component"].components),
        "baseGlyph": after.baseGlyph,
        "ok": len(font["fontport_component"].components) == before + 1
        and after.baseGlyph == "A",
    }
