# this_file: examples/fontparts/01_metrics.py
"""Expected: Increase A advance by 10; keep outlines unchanged."""

from _owned import owned


def run(font=None):
    font = owned(font)
    before = font["A"].width
    font["A"].width = before + 10
    after = font["A"].width
    return {"before": before, "after": after, "ok": after == before + 10}
