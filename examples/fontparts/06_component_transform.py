# this_file: examples/fontparts/06_component_transform.py
"""Expected: Move the previously added A component by (30, 40)."""

from _owned import owned


def run(font=None):
    font = owned(font)
    component = font["fontport_component"].components[0]
    before = component.offset
    component.offset = (30, 40)
    after = font["fontport_component"].components[0].offset
    return {"before": before, "after": after, "ok": after == (30, 40)}
