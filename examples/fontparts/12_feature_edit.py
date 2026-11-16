# this_file: examples/fontparts/12_feature_edit.py
"""Expected: Append a comment to the first stored tag; preserve other blocks/classes."""

from _owned import owned
from fly.fp.errors import UnsupportedCapability


def run(font=None):
    font = owned(font)
    blocks = font.features.get_blocks()
    if not blocks["features"]:
        raise UnsupportedCapability(
            "examples.features", "Choose a GetGo copy with stored features"
        )
    tag, code = blocks["features"][0]
    blocks["features"][0] = (tag, code + "# Fontport example edit\n")
    font.features.set_blocks(blocks)
    after = font.features.get_blocks()
    return {"before": code, "after": after["features"][0][1], "ok": after == blocks}
