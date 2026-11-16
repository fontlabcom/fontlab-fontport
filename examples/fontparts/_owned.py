# this_file: examples/fontparts/_owned.py
"""Examples accept only documents explicitly owned by their caller."""

from fly.fp.errors import UnsupportedCapability
from fontParts.world import CurrentFont


def owned(font=None):
    font = CurrentFont() if font is None else font
    if font is None or not getattr(font._backend, "owns_document", False):
        raise UnsupportedCapability(
            "examples.ownership",
            "Open an owned GetGo copy through FontWorld before running",
        )
    return font
