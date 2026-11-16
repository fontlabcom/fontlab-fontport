# this_file: examples/fontparts/14_bounds.py
"""Expected: Compare upstream BoundsPen to the live defcon bounds."""

from _owned import owned


def run(font=None):
    font = owned(font)
    from fly.fp.recipes import bounds

    before = tuple(font["A"].bounds) if font["A"].bounds is not None else None
    after = bounds(font["A"], font)
    return {"before": before, "after": after, "ok": before == after}
