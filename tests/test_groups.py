# this_file: tests/test_groups.py
"""Actual FontParts groups dispatch and validation before native mutation."""

from copy import deepcopy

import pytest
from fontParts.base import BaseGroups

from fontlab_fontport.groups import stage_groups
from fontlab_fontport.live import RFont


class Backend:
    def __init__(self):
        self.groups = {"original": ("A",)}
        self.writes = []

    def get_groups(self):
        return deepcopy(self.groups)

    def set_groups(self, values, *, undo_name="FontParts groups"):
        self.groups = stage_groups(values)
        self.writes.append((deepcopy(self.groups), undo_name))

    def close(self):
        pass


def test_groups_mapping_uses_actual_fontparts_and_independent_values():
    backend = Backend()
    font = RFont(backend)
    groups = font.groups
    assert isinstance(groups, BaseGroups) and groups.font is font
    groups["Unicode Ω"] = ["A", "V", "A"]
    assert groups["Unicode Ω"] == ("A", "V", "A"), (
        "plain groups retain order/duplicates"
    )
    returned = list(groups["Unicode Ω"])
    returned.clear()
    assert len(groups["Unicode Ω"]) == 3, "returned values must be detached"
    assert groups.findGlyph("V") == ["Unicode Ω"]
    assert len(groups) == 2 and "original" in groups
    del groups["original"]
    assert list(groups) == ["Unicode Ω"]


def test_groups_update_validates_the_whole_mapping_before_dispatch():
    backend = Backend()
    font = RFont(backend)
    with pytest.raises((TypeError, ValueError)):
        font.groups.update({"valid": ["V"], "": ["A"]})
    assert backend.groups == {"original": ("A",)} and not backend.writes


def test_groups_batch_and_rename_and_clear_are_single_dispatches():
    backend = Backend()
    font = RFont(backend)
    font.groups.apply({"empty": [], "old": ["A"]}, undo_name="Group batch")
    assert backend.writes[-1][1] == "Group batch"
    font.groups.rename("old", "new")
    assert dict(font.groups) == {"empty": (), "new": ("A",)}
    assert len(backend.writes) == 2, "rename must be a single complete operation"
    font.groups.clear()
    assert dict(font.groups) == {} and len(backend.writes) == 3


def test_groups_duplicate_rename_and_missing_delete_are_immutable():
    backend = Backend()
    font = RFont(backend)
    font.groups["other"] = []
    before = deepcopy(backend.groups)
    count = len(backend.writes)
    with pytest.raises(ValueError, match="exists"):
        font.groups.rename("original", "other")
    with pytest.raises(KeyError):
        del font.groups["missing"]
    assert backend.groups == before and len(backend.writes) == count


def test_valid_update_is_one_batch_and_identical_changes_are_noops():
    backend = Backend()
    font = RFont(backend)
    font.groups.update({"new": ["V"], "empty": []})
    assert len(backend.writes) == 1 and len(font.groups) == 3
    font.groups.rename("new", "new")
    font.groups["new"] = ["V"]
    assert len(backend.writes) == 1, (
        "identical values and same-name rename add no batch"
    )
    with pytest.raises(KeyError):
        font.groups.rename("missing", "new-name")
    for bad in (None, "", "  "):
        with pytest.raises((TypeError, ValueError)):
            font.groups.apply({}, undo_name=bad)
    assert len(backend.writes) == 1, "bad operation names must not reach the backend"


def test_retained_groups_refuse_a_closed_font_before_backend_access():
    backend = Backend()
    font = RFont(backend)
    groups = font.groups
    font.close()
    with pytest.raises(RuntimeError, match="closed"):
        groups["new"] = ["A"]
    with pytest.raises(RuntimeError, match="closed"):
        dict(groups)
    assert not backend.writes


@pytest.mark.parametrize(
    "values",
    [
        None,
        [],
        "groups",
        {"": []},
        {"bad\x00": []},
        {"bad\ud800": []},
        {"g": "A"},
        {"g": [None]},
        {"g": ["bad\x00"]},
        {"public.kern1.": []},
        {"public.kern2.": []},
    ],
)
def test_invalid_groups_are_refused_without_mutating_the_input(values):
    before = deepcopy(values)
    with pytest.raises((TypeError, ValueError)):
        stage_groups(values)
    assert values == before, "validation must not rewrite the supplied mapping"


def test_same_side_kerning_groups_cannot_overlap_but_opposite_sides_can():
    with pytest.raises(ValueError, match="more than one"):
        stage_groups({"public.kern1.A": ["A"], "public.kern1.B": ["A"]})
    values = {"public.kern1.A": ["A"], "public.kern2.A": ["A"]}
    assert stage_groups(values) == {k: tuple(v) for k, v in values.items()}


def test_kerning_group_duplicate_members_are_refused_and_plain_groups_preserved():
    with pytest.raises(ValueError, match="duplicate"):
        stage_groups({"public.kern1.A": ["A", "A"]})
    assert stage_groups({"plain": ["A", "A"]}) == {"plain": ("A", "A")}
