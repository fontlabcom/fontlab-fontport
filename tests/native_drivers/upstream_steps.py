# this_file: tests/native_drivers/upstream_steps.py
"""One upstream unittest per call; cleanup one owned document per later call."""

import sys
from time import monotonic


class PhaseDeadline(RuntimeError):
    pass


def run_one(identifier, generator, cases):
    from fontlab_fontport.testing import run_test

    deadline = monotonic() + 2.5
    previous = sys.gettrace()

    def guard(frame, event, arg):
        if monotonic() >= deadline:
            raise PhaseDeadline(
                "Upstream test exceeded 2.5 s Python budget; split this test in C4 ticket"
            )
        return guard

    try:
        sys.settrace(guard)
        row = run_test(cases[identifier], generator, cleanup=False)
    finally:
        sys.settrace(previous)
    return row


def close_one(generator):
    """Finally-path cleanup, including an allocation whose wrapper failed."""
    import fontpr

    if generator.owned:
        font = generator.owned[-1]
        identifier = font._backend.font_id
        if not font._closed:
            font.close()
        generator.owned.pop()
        if identifier in generator.pending_ids:
            generator.pending_ids.remove(identifier)
    elif generator.pending_ids:
        fontpr.call("close_font", font_id=generator.pending_ids[-1], save=False)
        generator.pending_ids.pop()
    return {"remaining": len(generator.owned) + len(generator.pending_ids)}
