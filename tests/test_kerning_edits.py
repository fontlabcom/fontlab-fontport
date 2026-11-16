# this_file: tests/test_kerning_edits.py
"""B07 presentation-independent pair actions and explicit/effective inspection."""

import pytest

from fontlab_fontport.kerning_edit import edit_kerning, inspect_kerning

GROUPS = {"public.kern1.Left": ("A",), "public.kern2.Right": ("V",)}
PAIRS = {("public.kern1.Left", "public.kern2.Right"): -82}


def test_explicit_zero_is_distinct_from_effective_fallback_and_absence():
    assert inspect_kerning(PAIRS, GROUPS, ("A", "V")) == {
        "explicit": False,
        "value": None,
        "effective": -82,
    }
    values = edit_kerning(
        PAIRS, "apply", ("A", "V"), 0, groups=GROUPS, glyphs=("A", "V")
    )
    assert inspect_kerning(values, GROUPS, ("A", "V")) == {
        "explicit": True,
        "value": 0,
        "effective": 0,
    }
    assert edit_kerning(values, "delete", ("A", "V"), groups=GROUPS, glyphs=()) == PAIRS
    assert len(PAIRS) == 1, "staging never edits supplied pairs"


@pytest.mark.parametrize(
    "pair",
    [
        ("A", "V"),
        ("A", "public.kern2.Right"),
        ("public.kern1.Left", "V"),
        ("public.kern1.Left", "public.kern2.Right"),
    ],
)
def test_all_glyph_group_forms_stage_fractional_values_without_rounding(pair):
    values = edit_kerning({}, "apply", pair, -3.75, groups=GROUPS, glyphs=("A", "V"))
    assert values == {pair: -3.75}


@pytest.mark.parametrize(
    "pair,value",
    [
        (("missing", "V"), -4),
        (("public.kern1.Missing", "V"), 0),
        (("A", "V"), float("nan")),
        (("A", "public.kern1.Left"), -12),
    ],
)
def test_unknown_keys_and_invalid_numbers_never_change_the_source(pair, value):
    with pytest.raises((TypeError, ValueError)):
        edit_kerning(PAIRS, "apply", pair, value, groups=GROUPS, glyphs=("A", "V"))
    assert PAIRS == {("public.kern1.Left", "public.kern2.Right"): -82}


def test_missing_delete_and_unknown_operation_are_errors():
    with pytest.raises(KeyError):
        edit_kerning(PAIRS, "delete", ("A", "V"), groups=GROUPS, glyphs=())
    with pytest.raises(ValueError, match="operation"):
        edit_kerning(PAIRS, "unknown", ("A", "V"), 0, groups=GROUPS, glyphs=())


def test_inspector_rejects_ambiguous_groups_and_reports_no_pair_as_none():
    assert inspect_kerning({}, {}, ("A", "V"))["effective"] is None
    with pytest.raises(ValueError, match="more than one"):
        inspect_kerning(PAIRS, {**GROUPS, "public.kern1.Other": ("A",)}, ("A", "V"))
