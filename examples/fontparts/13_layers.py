# this_file: examples/fontparts/13_layers.py
"""Expected: native layer.create refusal leaves layerOrder unchanged; UFO backend adds the layer."""

from _owned import owned
from fly.fp.errors import UnsupportedCapability


def run(font=None):
    font = owned(font)
    before = font.layerOrder
    try:
        font.newLayer("fontport_sketch")
    except UnsupportedCapability as error:
        return {
            "before": before,
            "after": font.layerOrder,
            "capability": error.capability,
            "ok": error.capability == "layer.create" and font.layerOrder == before,
        }
    return {
        "before": before,
        "after": font.layerOrder,
        "ok": "fontport_sketch" in font.layerOrder,
    }
