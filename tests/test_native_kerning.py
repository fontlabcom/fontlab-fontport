# this_file: tests/test_native_kerning.py
"""Native pair routing and complete validation before history or mutation."""

from types import SimpleNamespace

import pytest

from fontlab_fontport.native_kerning import read_kerning, target_master, write_kerning


class NativePairs:
    def __init__(self):
        self.groups = {
            "Left": (["A"], "KernLeft"),
            "public.kern2.Right": (["V"], "KernRight"),
        }
        self.pairs = {(("Left", "groupMode"), ("public.kern2.Right", "groupMode")): -82}
        self.writes = []

    def items(self):
        return [
            (
                SimpleNamespace(
                    left=SimpleNamespace(id=k[0][0], mode=k[0][1]),
                    right=SimpleNamespace(id=k[1][0], mode=k[1][1]),
                ),
                v,
            )
            for k, v in self.pairs.items()
        ]

    def set(self, key, value):
        self.writes.append((key, value))
        self.pairs[key] = value

    def remove(self, key):
        self.writes.append((key, None))
        del self.pairs[key]

    def scale(self, factor):
        self.pairs = {key: value * factor for key, value in self.pairs.items()}


@pytest.fixture
def native(monkeypatch):
    kern, events = NativePairs(), []
    package = SimpleNamespace(
        fgPackage=SimpleNamespace(groups={}),
        kerning=lambda: kern,
        findName=lambda name: SimpleNamespace(isNull=name not in {"A", "V"}),
        checkInitHistoryState=lambda index: events.append(("init", index)),
        mastersContainer=lambda: "masters",
        kerningContainer=lambda: "kerning",
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "fontlab",
        SimpleNamespace(
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda name, objects: events.append(
                    (name, objects)
                )
            )
        ),
    )
    return package, kern, events


def test_native_read_maps_raw_and_prefixed_class_names_by_side(native):
    p, _, _ = native
    assert read_kerning(p) == {("public.kern1.Left", "public.kern2.Right"): -82}


def test_native_batch_preserves_explicit_zero_and_integer_value(native):
    p, kern, events = native
    values = {("public.kern1.Left", "public.kern2.Right"): -11, ("A", "V"): 0}
    write_kerning(p, values, "B07 batch")
    assert read_kerning(p) == values
    assert kern.pairs[(("A", "glyphMode"), ("V", "glyphMode"))] == 0
    assert len(events) == 3 and events[0] == ("init", 0)
    assert events[1] == events[2], "one before/after protocol encloses the whole batch"
    assert events[1][1] == [p, "masters", "kerning"]
    assert len(kern.writes) == 2


def test_native_remove_drops_only_pairs_and_identical_batch_is_a_noop(native):
    p, kern, events = native
    before = read_kerning(p)
    write_kerning(p, before, "unchanged")
    assert not events and not kern.writes
    write_kerning(p, {}, "delete")
    assert read_kerning(p) == {} and len(kern.writes) == 1
    assert len(kern.groups) == 2, "class definitions must survive pair removal"


@pytest.mark.parametrize(
    "values",
    [
        {("A", "V"): -4, ("missing", "V"): 0},
        {("A", "V"): -4, ("public.kern1.Missing", "V"): 0},
        {("A", "V"): float("nan")},
        {("public.kern2.Right", "V"): -2},
        {("A", "V"): -81.5},
        {("A", "V"): 2**31},
    ],
)
def test_native_bad_batch_does_not_create_history_or_partial_pairs(native, values):
    p, kern, events = native
    before = dict(kern.pairs)
    with pytest.raises((TypeError, ValueError, NotImplementedError)):
        write_kerning(p, values, "refuse")
    assert kern.pairs == before and not kern.writes and not events


def test_native_existing_fractional_values_are_read_exactly_but_not_rewritten(native):
    p, kern, events = native
    key = next(iter(kern.pairs))
    kern.pairs[key] = -81.5
    assert read_kerning(p)[("public.kern1.Left", "public.kern2.Right")] == -81.5
    write_kerning(p, read_kerning(p), "unchanged fraction")
    assert not kern.writes and not events
    with pytest.raises(NotImplementedError, match="fractional"):
        write_kerning(p, {("A", "V"): -12}, "would round history")
    assert kern.pairs[key] == -81.5 and not kern.writes and not events


def test_native_fractional_refusal_names_the_pair_and_value(native):
    p, kern, events = native
    key = next(iter(kern.pairs))
    kern.pairs[key] = -81.5
    with pytest.raises(NotImplementedError) as caught:
        write_kerning(p, {("A", "V"): -12}, "would round history")
    text = str(caught.value)
    assert "public.kern1.Left public.kern2.Right = -81.5 is not a whole number" in text, text
    assert "no changes applied" in text, text
    assert not kern.writes and not events


def test_native_fractional_refusal_when_master_known_then_names_it(native):
    p, _kern, _ = native
    p.master = "Bold"
    with pytest.raises(NotImplementedError, match=r"Kerning on Bold: A V = 0\.5 "):
        write_kerning(p, {("A", "V"): 0.5}, "staged fraction")


def test_native_unsupported_pair_mode_is_never_guessed_as_a_glyph(native):
    p, kern, _ = native
    kern.pairs = {(("A", "unknownMode"), ("V", "glyphMode")): 2}
    with pytest.raises(NotImplementedError, match="mode"):
        read_kerning(p)


def test_native_unknown_group_in_existing_pair_is_an_explicit_refusal(native):
    p, kern, _ = native
    kern.pairs = {(("Missing", "groupMode"), ("V", "glyphMode")): 2}
    with pytest.raises(NotImplementedError, match="group"):
        read_kerning(p)


def test_native_ignored_setter_cannot_report_success(native):
    p, kern, _ = native
    kern.set = lambda key, value: None
    with pytest.raises(RuntimeError, match="readback"):
        write_kerning(p, {("A", "V"): -12}, "ignored native setter")


def test_native_bad_history_label_fails_before_any_mutation(native):
    p, kern, events = native
    with pytest.raises(ValueError, match="blank"):
        write_kerning(p, {}, "  ")
    assert len(kern.pairs) == 1 and not kern.writes and not events


@pytest.mark.parametrize("name", ["glyph Ω", "has space", "bad\x7f"])
def test_native_unrepresentable_existing_glyph_name_is_refused_before_history(
    native, name
):
    p, kern, events = native
    p.findName = lambda key: SimpleNamespace(isNull=False)
    before = dict(kern.pairs)
    with pytest.raises(NotImplementedError, match="name"):
        write_kerning(p, {(name, "V"): -12}, "unsupported native name")
    assert kern.pairs == before and not kern.writes and not events


@pytest.fixture
def masters(native):
    """Package whose current master (Bold) differs from its default (Light)."""
    p, _, events = native
    per = {"Light": NativePairs(), "Bold": NativePairs()}
    calls = []

    def kerning(*master):
        calls.append(master)
        return per[master[0] if master else "Bold"]

    p.kerning, p.master = kerning, "Bold"
    p.defaultMaster, p.masters = "Light", ("Light", "Bold")
    return p, per, calls, events


def test_native_write_when_current_master_is_not_default_then_targets_default(masters):
    p, per, calls, _ = masters
    key = next(iter(per["Light"].pairs))
    write_kerning(p, {("public.kern1.Left", "public.kern2.Right"): -90}, "default master")
    assert per["Light"].pairs[key] == -90, "default master written"
    assert per["Bold"].pairs[key] == -82, "current master untouched"
    assert not per["Bold"].writes, "current master never written"
    assert ("Light",) in calls, "pairs read and written through the default master"


def test_native_read_when_current_master_is_not_default_then_reads_default(masters):
    p, per, _calls, _ = masters
    per["Light"].pairs = {k: 5 for k in per["Light"].pairs}
    assert target_master(p) == "Light", "font-level target is the default master"
    assert set(read_kerning(p, target_master(p)).values()) == {5}


def test_native_fraction_on_non_target_master_when_writing_then_refused_naming_it(masters):
    p, per, _, events = masters
    key = next(iter(per["Bold"].pairs))
    per["Bold"].pairs[key] = -56.5
    with pytest.raises(NotImplementedError) as caught:
        write_kerning(p, {("A", "V"): -12}, "other master fraction")
    text = str(caught.value)
    assert "Kerning on Bold: public.kern1.Left public.kern2.Right = -56.5 is not a whole number" in text, text
    assert not per["Light"].writes and not per["Bold"].writes and not events


def test_native_nonfinite_on_other_master_when_writing_then_refused_naming_it(masters):
    p, per, _, events = masters
    key = next(iter(per["Bold"].pairs))
    per["Bold"].pairs[key] = float("nan")
    with pytest.raises(NotImplementedError, match=r"Kerning on Bold: .*finite"):
        write_kerning(p, {("A", "V"): -12}, "other master nan")
    assert not per["Light"].writes and not events


def test_native_unchanged_staged_when_other_master_fractional_then_still_refused(masters):
    p, per, _, _ = masters
    key = next(iter(per["Bold"].pairs))
    per["Bold"].pairs[key] = 0.5
    same = read_kerning(p)
    with pytest.raises(NotImplementedError, match="Kerning on Bold"):
        write_kerning(p, same, "no-op must not hide a fraction")


def test_backend_get_kerning_when_current_master_is_not_default_then_reads_default(
    masters,
):
    from fontlab_fontport.host import NativeFontBackend

    p, per, _calls, _ = masters
    per["Light"].pairs = {k: 5 for k in per["Light"].pairs}
    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._package = lambda: p
    assert set(backend.get_kerning().values()) == {5}, "default master's pairs"
    assert set(per["Bold"].pairs.values()) != {5}, "current master differs"
