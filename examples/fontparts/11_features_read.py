# this_file: examples/fontparts/11_features_read.py
"""Expected: Read complete native feature text without decompilation or panel-class duplication."""

from _owned import owned


def run(font=None):
    font = owned(font)
    before = font.features.text
    after = font.features.text
    return {"before": before, "after": after, "ok": before == after}
