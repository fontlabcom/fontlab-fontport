# this_file: examples/live_font.py
"""Run inside FontLab on an explicitly owned fixture document only.

MCP font_id is package.fgId, not package.id. Run every mutating verification
through workspace verification/issue-104/fl-native.sh --mutating.
"""

from fly.fp.host import NativeFontBackend
from fly.fp.live import RFont


def edit_owned_fixture(font_id: int, destination: str) -> None:
    """Change an owned fixture, save a native copy, and close its document.

    Whole glyph deletion, native Undo, image/guideline editing, fractional
    anchors and outline edits on hinted/shared/transformed shapes are refused.
    An unexpected native assignment exception can leave partial changes.
    Native JSON reload may normalize lib integer values to equal-valued floats;
    bytes/dates and numbers outside the exact JSON range are refused.
    """
    font = RFont(NativeFontBackend(font_id, owns_document=True))
    glyph = font["A"]
    glyph.width = 650
    glyph.note = "Edited through FontParts"
    glyph.lib["example"] = {"text": "owned fixture"}
    font.save(destination)
    font.close()
