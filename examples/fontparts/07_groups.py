# this_file: examples/fontparts/07_groups.py
"""Expected: Add an ASCII feature class containing A and V."""

from _owned import owned


def run(font=None):
    """Expected: the requested edit succeeds in the default editing mode."""
    font = owned(font)
    before = font.groups.get("fontport_example")
    font.groups["fontport_example"] = ("A", "V")
    after = font.groups["fontport_example"]
    return {"before": before, "after": after, "ok": after == ("A", "V")}
