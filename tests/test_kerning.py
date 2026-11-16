# this_file: tests/test_kerning.py
"""Actual FontParts explicit pairs, inherited fallback and whole-map staging."""

from copy import deepcopy

import pytest
from fontParts.base import BaseKerning

from fontlab_fontport.kerning import stage_kerning
from fontlab_fontport.live import RFont


class Backend:
    def __init__(self):
        self.pairs = {("public.kern1.Left", "public.kern2.Right"): -81.5}
        self.writes = []

    def get_groups(self):
        return {"public.kern1.Left": ("A", "B"), "public.kern2.Right": ("V", "W")}

    def get_kerning(self):
        return deepcopy(self.pairs)

    def set_kerning(self, values, *, undo_name="FontParts kerning"):
        self.pairs = stage_kerning(values)
        self.writes.append((deepcopy(self.pairs), undo_name))

    def close(self):
        pass


def test_kerning_mapping_is_real_fontparts_and_reads_fresh_values():
    backend = Backend()
    font = RFont(backend)
    pairs = font.kerning
    assert isinstance(pairs, BaseKerning) and pairs.font is font
    assert pairs.find(("A", "V")) == -81.5
    assert ("A", "V") not in pairs and pairs.get(("A", "V")) is None
    backend.pairs[("A", "V")] = 0
    assert pairs.find(("A", "V")) == 0 and pairs[("A", "V")] == 0
    assert len(pairs) == 2 and len(list(pairs)) == 2
    assert len(list(pairs.items())) == 2 and len(list(pairs.values())) == 2


def test_zero_exception_and_all_fallback_levels_have_distinct_presence():
    backend = Backend()
    pairs = RFont(backend).kerning
    pairs[("A", "public.kern2.Right")] = -45.25
    pairs[("public.kern1.Left", "V")] = -30
    assert pairs.find(("A", "V")) == -45.25, "glyph/group wins over group/glyph"
    assert pairs.find(("B", "V")) == -30
    assert pairs.find(("B", "W")) == -81.5
    pairs[("A", "V")] = 0
    assert pairs.find(("A", "V")) == 0
    assert pairs.pop(("A", "V")) == 0
    assert pairs.find(("A", "V")) == -45.25
    assert pairs.find(("missing", "V"), 123) == 123


def test_update_and_apply_dispatch_once_and_preserve_input():
    backend = Backend()
    pairs = RFont(backend).kerning
    values = {("A", "V"): -3.75, ("B", "W"): 0}
    pairs.update(values)
    assert len(backend.writes) == 1 and len(pairs) == 3
    pairs.apply(values, undo_name="B07 complete pairs")
    assert len(backend.writes) == 2 and dict(pairs) == values
    assert backend.writes[-1][1] == "B07 complete pairs"
    pairs.apply(values)
    pairs[("A", "V")] = -3.75
    assert len(backend.writes) == 2, "identical writes are history-free"
    assert values == {("A", "V"): -3.75, ("B", "W"): 0}
    pairs.clear()
    assert not pairs and len(backend.writes) == 3


@pytest.mark.parametrize(
    "value", [None, "20", True, float("nan"), float("inf"), -float("inf"), 2**54]
)
def test_invalid_value_refuses_the_complete_update_before_dispatch(value):
    backend = Backend()
    pairs = RFont(backend).kerning
    before = dict(pairs)
    with pytest.raises((TypeError, ValueError)):
        pairs.update({("A", "V"): -12, ("B", "W"): value})
    assert dict(pairs) == before and not backend.writes


@pytest.mark.parametrize(
    "values",
    [
        None,
        [],
        {("", "V"): 2},
        {("A",): 2},
        {("public.kern2.Wrong", "V"): 2},
        {("A", "public.kern1.Wrong"): 2},
        {("A\x00", "V"): 2},
        {("A", "\ud800"): 2},
        {("public.kern1.", "V"): 2},
    ],
)
def test_bad_pairs_are_refused_before_mutation(values):
    with pytest.raises((TypeError, ValueError)):
        stage_kerning(values)


def test_missing_delete_and_invalid_history_name_do_not_dispatch():
    backend = Backend()
    pairs = RFont(backend).kerning
    with pytest.raises(KeyError):
        del pairs[("missing", "V")]
    for name in (None, "", "  ", "bad\x00"):
        with pytest.raises((TypeError, ValueError)):
            pairs.apply({}, undo_name=name)
    assert len(pairs) == 1 and not backend.writes


def test_kerning_handle_refuses_closed_font_before_backend_access():
    backend = Backend()
    font = RFont(backend)
    pairs = font.kerning
    font.close()
    with pytest.raises(RuntimeError, match="closed"):
        dict(pairs)
    with pytest.raises(RuntimeError, match="closed"):
        pairs[("A", "V")] = 0
    assert not backend.writes
