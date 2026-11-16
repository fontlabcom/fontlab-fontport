# this_file: tests/test_native_groups.py
"""Native storage planning refuses ambiguous or destructive edits before writes."""

from types import SimpleNamespace

import pytest

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.native_groups import _plan, read_groups


class Feature(list):
    def __init__(self, members=(), feature=True):
        super().__init__(members)
        self.feature = feature

    def isFeaGroup(self):
        return self.feature


class Groups(dict):
    def has_key(self, name):
        return name in self


def package(features=None, classes=None, references=()):
    pairs = [
        SimpleNamespace(
            left=SimpleNamespace(id=name, mode="groupMode"),
            right=SimpleNamespace(id="V", mode="glyphMode"),
        )
        for name in references
    ]
    kern = SimpleNamespace(groups=classes or {}, keys=lambda: pairs)
    return SimpleNamespace(
        fgPackage=SimpleNamespace(groups=Groups(features or {})),
        kerning=lambda: kern,
        findName=lambda name: SimpleNamespace(isNull=name not in {"A", "B", "V"}),
    )


def test_native_read_projects_real_both_sided_classes_without_using_opaque_flags():
    p = package(
        {"plain": Feature(["A"]), "opaque": Feature(["B"], False)},
        {"LeftRight": (["V"], "KernBothSide"), "public.kern1.A": (["A"], "KernLeft")},
    )
    values, routes = read_groups(p)
    assert values == {
        "plain": ("A",),
        "public.kern1.LeftRight": ("V",),
        "public.kern2.LeftRight": ("V",),
        "public.kern1.A": ("A",),
    }
    assert routes["public.kern2.LeftRight"] == ("kerning", "LeftRight")
    assert "opaque" not in values, (
        "font-global legacy flags are not live kerning classes"
    )


@pytest.mark.parametrize(
    "p,message",
    [
        (
            package(
                classes={
                    "A": (["A"], "KernLeft"),
                    "public.kern1.A": (["B"], "KernLeft"),
                }
            ),
            "Ambiguous",
        ),
        (package(features={"public.kern1.A": Feature(["A"])}), "reserved"),
        (package(classes={"A": (["A"], "NoKerningMode")}), "mode unsupported"),
    ],
)
def test_native_mapping_refuses_ambiguity_without_reinterpreting_it(p, message):
    with pytest.raises(NotImplementedError, match=message):
        read_groups(p)


def test_both_sided_membership_cannot_diverge_but_one_side_can_be_removed():
    p = package(classes={"Both": (["A"], "KernBothSide")})
    current, routes = read_groups(p)
    with pytest.raises(NotImplementedError, match="identical"):
        _plan(p, {**current, "public.kern1.Both": ("B",)}, current, routes)
    assert _plan(p, {"public.kern2.Both": ("A",)}, current, routes) == {
        "Both": (("A",), "KernRight")
    }


def test_dependent_native_group_delete_and_rename_are_refused_with_references():
    p = package(classes={"Left": (["A"], "KernLeft")}, references=["Left"])
    current, routes = read_groups(p)
    for staged in ({}, {"public.kern1.Renamed": ("A",)}):
        with pytest.raises(
            UnsupportedCapability,
            match=r"groups.dependentKerning.*dependent kerning.*Left",
        ):
            _plan(p, staged, current, routes)
    assert _plan(p, {"public.kern1.Left": ("B",)}, current, routes) == {
        "Left": (("B",), "KernLeft")
    }


def test_native_plan_refuses_unknown_kerning_member_and_preserves_opaque_group():
    p = package(features={"opaque": Feature([], False)})
    with pytest.raises(
        UnsupportedCapability, match=r"kerning.danglingNames.*does not exist"
    ):
        _plan(p, {"public.kern1.A": ("missing",)}, {}, {})
    with pytest.raises(NotImplementedError, match="not an editable feature"):
        _plan(p, {"opaque": ("A",)}, {}, {})


def test_native_plan_keeps_names_distinct_for_new_left_and_right_classes():
    p = package()
    assert _plan(p, {"public.kern1.A": ("A",), "public.kern2.A": ("V",)}, {}, {}) == {
        "public.kern1.A": (("A",), "KernLeft"),
        "public.kern2.A": (("V",), "KernRight"),
    }


def test_opt_in_strict_native_group_write_refuses_legacy_flag_loss_before_any_history():
    from fontlab_fontport.errors import UnsupportedCapability
    from fontlab_fontport.native_groups import write_groups

    p = package(features={"plain": Feature(["A"]), "legacy": Feature(["A"], False)})
    with pytest.raises(UnsupportedCapability, match=r"groups.legacyFlagsVfj"):
        write_groups(p, {"plain": ("V",)}, "strict opt-in", require_persistence=True)
    assert read_groups(p)[0] == {"plain": ("A",)}
    write_groups(p, {"plain": ("A",)}, "identical default")
