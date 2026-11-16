# this_file: examples/fontparts/10_lib.py
"""Expected: Persist a reassigned nested plist value."""

from _owned import owned


def run(font=None):
    font = owned(font)
    before = font.lib.get("org.fontlab.fontport.example")
    font.lib["org.fontlab.fontport.example"] = {"points": [1, 2, 3], "label": "Ω"}
    after = font.lib["org.fontlab.fontport.example"]
    return {"before": before, "after": after, "ok": after["points"] == [1, 2, 3]}
