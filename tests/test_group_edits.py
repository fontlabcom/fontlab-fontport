# this_file: tests/test_group_edits.py
"""B06 explicit editing operations validate before a UI/native dispatch."""

from copy import deepcopy

import pytest

from fontlab_fontport.groups import edit_groups


@pytest.mark.parametrize(
    "action,kwargs,expected",
    [
        ("add", {"name": "empty"}, {"g": ("A",), "empty": ()}),
        ("rename", {"name": "g", "new_name": "new"}, {"new": ("A",)}),
        ("delete", {"name": "g"}, {}),
        ("add_members", {"name": "g", "members": ["V", "A", "V"]}, {"g": ("A", "V")}),
        ("remove_members", {"name": "g", "members": ["A"]}, {"g": ()}),
    ],
)
def test_explicit_group_edit_returns_detached_validated_mapping(
    action, kwargs, expected
):
    source = {"g": ["A"]}
    assert (
        edit_groups(source, action, available_glyphs={"A", "V"}, **kwargs) == expected
    )
    assert source == {"g": ["A"]}, "staging must not edit the borrowed source"


@pytest.mark.parametrize(
    "action,kwargs",
    [
        ("add", {"name": "g"}),
        ("add", {"name": ""}),
        ("rename", {"name": "g", "new_name": "other"}),
        ("rename", {"name": "missing", "new_name": "new"}),
        ("delete", {"name": "missing"}),
        ("add_members", {"name": "g", "members": ["missing"]}),
        ("remove_members", {"name": "g", "members": ["V"]}),
        ("unknown", {"name": "g"}),
    ],
)
def test_invalid_explicit_group_edit_does_not_change_any_group(action, kwargs):
    source = {"g": ["A"], "other": ["V"]}
    before = deepcopy(source)
    with pytest.raises((ValueError, KeyError)):
        edit_groups(source, action, available_glyphs={"A", "V"}, **kwargs)
    assert source == before, "invalid operation must preserve the whole mapping"


def test_remove_can_repair_existing_native_overlap_and_rename_same_is_noop():
    source = {"public.kern1.A": ["A"], "public.kern1.B": ["A"]}
    assert edit_groups(source, "delete", "public.kern1.A") == {"public.kern1.B": ("A",)}
    assert edit_groups({"g": ["A"]}, "rename", "g", new_name="g") == {"g": ("A",)}
