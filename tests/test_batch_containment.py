# this_file: tests/test_batch_containment.py
"""Eager all-input containment with real UFOs and exact input preservation."""
import base64
import hashlib
import os
import stat
from copy import deepcopy
from pathlib import Path

import pytest
from test_operations import fixture_font
from ufoLib2 import Font
from ufoLib2.objects import Image

from fontlab_fontport.batch import BatchRunner
from fontlab_fontport.recipe import Recipe

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=="
)


def file_tree(path: Path) -> dict:
    rows = {}
    for item in [path, *sorted(path.rglob("*"))]:
        row = {"mode": stat.S_IMODE(item.lstat().st_mode)}
        if item.is_symlink():
            row.update(kind="symlink", target=os.readlink(item))
        elif item.is_dir():
            row.update(kind="directory")
        else:
            data = item.read_bytes()
            row.update(kind="file", bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        rows[str(item.relative_to(path))] = row
    return rows


@pytest.fixture
def owned(tmp_path):
    base = tmp_path / "Outer.ufo"
    base.mkdir()
    paths = [base / "A.ufo", base / "B.ufo"]
    for index, path in enumerate(paths):
        font = fixture_font()
        font.info.familyName = f"Owned containment {index}"
        font.info.ascender, font.info.descender = 800, -200
        font["A"].width += index * 17
        font["A"].height = 900 + index
        font["A"].unicodes = [65 + index]
        font["A"].note = f"Owned note {index}"
        font["A"].lib["nested"] = {"values": [True, index, "Ω"]}
        font.groups["public.kern1.owned"] = ["A"]
        font.kerning[("A", "C")] = -25 - index
        font.images["owned.png"] = PNG
        font.data["owned/payload.bin"] = bytes([0, index, 255])
        font["A"].image = Image("owned.png", (1.25, .2, -.1, .9, 13.5, -17.75), ".1,.2,.3,.4")
        layer = font.layers.newLayer("owned.background")
        layer.color = "0.1,0.2,0.3,1"
        layer.lib["owned"] = {"index": index}
        layer.insertGlyph(deepcopy(font["A"]))
        try:
            font.save(path)
        finally:
            font.close()
        (path / "unrelated.txt").write_bytes(b"unrelated\x00" + bytes([index]))
        (path / "unrelated.txt").chmod(0o640)
        (path / "unrelated-link").symlink_to("unrelated.txt")
    source_alias = base / "source-alias.ufo"
    source_alias.symlink_to(paths[0], target_is_directory=True)
    destination_alias = base / "destination-parent"
    destination_alias.symlink_to(paths[1], target_is_directory=True)
    before_files = [file_tree(p) for p in paths]
    with Font.open(paths[0], lazy=False) as first, Font.open(paths[1], lazy=False) as second:
        try:
            yield base, paths[0], paths[1], source_alias, destination_alias
        finally:
            assert [file_tree(p) for p in paths] == before_files, "complete input trees changed"
            with Font.open(paths[0], lazy=False) as after_first, Font.open(paths[1], lazy=False) as after_second:
                assert first == after_first and second == after_second, "complete reopened input models changed"


@pytest.mark.parametrize("case", ["later-input", "reversed-order", "direct-self", "deep-self", "other-direct", "source-alias", "destination-parent-alias", "both-aliases"])
def test_run_when_target_inside_any_input_then_eagerly_refuses(owned, case):
    base, a, b, alias, dest_alias = owned
    plans = {
        "later-input": [(a, b / "new/result.ufo"), (b, base / "safe.ufo")],
        "reversed-order": [(b, base / "safe.ufo"), (a, b / "new/result.ufo")],
        "direct-self": [(a, a / "result.ufo")],
        "deep-self": [(a, a / "new/deep/result.ufo")],
        "other-direct": [(a, b / "result.ufo"), (b, base / "safe.ufo")],
        "source-alias": [(alias, a / "result.ufo")],
        "destination-parent-alias": [(a, dest_alias / "new/result.ufo"), (b, base / "safe.ufo")],
        "both-aliases": [(alias, dest_alias / "result.ufo"), (b, base / "safe.ufo")],
    }
    jobs = plans[case]
    assert all(not target.exists() for _, target in jobs)
    runner, progress, iterator = BatchRunner(), [], None
    assert not runner.running
    try:
        with pytest.raises(ValueError, match="outside every source UFO"):
            iterator = runner.run(iter(jobs), Recipe(), progress=progress.append)
    finally:
        if iterator is not None:
            iterator.close()  # Also release the precise unexpected iterator on RED.
        assert not runner.running and not progress
        assert not any(target.exists() for _, target in jobs)


@pytest.mark.parametrize("case", ["equal-self", "equal-other", "containing-existing", "existing-file", "existing-directory", "duplicate", "duplicate-alias", "missing-later", "relative", "empty", "over-limit"])
def test_run_when_existing_validation_refuses_then_no_reservation_or_write(owned, case):
    base, a, b, alias, _ = owned
    existing_file = base / "existing-file.ufo"
    existing_file.write_bytes(b"retained")
    existing_dir = base / "existing-dir.ufo"
    existing_dir.mkdir()
    target = base / "new.ufo"
    target_parent_alias = base / "parent-alias"
    target_parent_alias.symlink_to(base, target_is_directory=True)
    cases = {
        "equal-self": ([(a, a)], FileExistsError),
        "equal-other": ([(a, b)], FileExistsError),
        "containing-existing": ([(a, base)], FileExistsError),
        "existing-file": ([(a, existing_file)], FileExistsError),
        "existing-directory": ([(a, existing_dir)], FileExistsError),
        "duplicate": ([(a, target), (b, target)], ValueError),
        "duplicate-alias": ([(a, target), (alias, target_parent_alias / "new.ufo")], ValueError),
        "missing-later": ([(a, target), (base / "missing.ufo", base / "other.ufo")], FileNotFoundError),
        "relative": ([(a, Path("relative.ufo"))], ValueError),
        "empty": ([], ValueError),
        "over-limit": ([(a, base / f"out-{i}.ufo") for i in range(257)], ValueError),
    }
    jobs, expected = cases[case]
    runner, progress = BatchRunner(), []
    with pytest.raises(expected):
        runner.run(jobs, Recipe(), progress=progress.append)
    assert not runner.running and not progress and not target.exists()
    assert existing_file.read_bytes() == b"retained" and existing_dir.is_dir()


@pytest.mark.parametrize("case", ["ancestor-directory-siblings", "textual-prefix-sibling"])
def test_run_when_targets_outside_inputs_then_outputs_reopen_and_inputs_match(owned, case):
    base, a, b, _, _ = owned
    folder = base if case == "ancestor-directory-siblings" else base / "A.ufo-sibling"
    targets = [folder / "A-transformed.ufo", folder / "B-transformed.ufo"]
    runner, progress = BatchRunner(), []
    iterator = runner.run(zip([a, b], targets, strict=False), Recipe(matrix=(2, 0, 0, 2, 10, 20)), progress=progress.append)
    assert runner.running
    try:
        results = list(iterator)
    finally:
        iterator.close()
    assert all(r.ok for r in results) and len(results) == 2 and progress == results and not runner.running
    for index, target in enumerate(targets):
        with Font.open(target, lazy=False) as out, Font.open([a, b][index], lazy=False) as original:
            assert out["A"].width == (500 + index * 17) * 2
            assert (out["A"].contours[0].points[0].x, out["A"].contours[0].points[0].y) == (30, 60)
            assert out["A"].anchors[0].x == 50 and out["A"].anchors[0].y == 420
            assert out["C"].components[0].transformation == (1, 0, 0, 1, 60, 80)
            assert out.layers["owned.background"]["A"].width == (500 + index * 17) * 2
            assert out.features == original.features and out.info == original.info
            assert out.groups == original.groups and out.kerning == original.kerning and out.lib == original.lib
            assert dict(out.data) == dict(original.data) and dict(out.images) == dict(original.images)


def test_close_when_old_iterator_reclosed_then_new_reservation_survives(owned):
    base, a, _, _, _ = owned
    runner = BatchRunner()
    old = runner.run([(a, base / "unused.ufo")], Recipe())
    assert runner.running
    old.close()
    assert not runner.running
    current = runner.run([(a, base / "unused2.ufo")], Recipe())
    try:
        old.close()
        assert runner.running
        with pytest.raises(RuntimeError):
            runner.run([(a, base / "unused3.ufo")], Recipe())
    finally:
        current.close()
    assert not runner.running and not list(base.glob("unused*.ufo"))


@pytest.mark.parametrize("case", ["cancel", "per-item-read-failure"])
def test_run_when_cancelled_or_item_fails_then_reservation_released(owned, case):
    base, a, _, _, _ = owned
    bad = base / "malformed.ufo"
    bad.mkdir()
    runner, progress = BatchRunner(), []
    iterator = runner.run([(a if case == "cancel" else bad, base / "out.ufo")], Recipe(), progress=progress.append, cancelled=lambda: case == "cancel")
    try:
        results = list(iterator)
    finally:
        iterator.close()
    assert not runner.running
    if case == "cancel":
        assert results == [] and progress == [] and not (base / "out.ufo").exists()
    else:
        assert len(results) == 1 and not results[0].ok and results[0].error and progress == results


@pytest.mark.parametrize("names", [("CaseInput.ufo", "caseinput.ufo"), ("Café.ufo", "Cafe\u0301.ufo")], ids=["case", "unicode"])
@pytest.mark.parametrize("reverse", [False, True], ids=["later-input", "reversed"])
def test_run_when_existing_ancestor_is_filesystem_alias_then_refuses_without_advance(owned, names, reverse, record_property):
    import shutil

    base, a, b, _, _ = owned
    actual, alternate = (base / name for name in names)
    shutil.copytree(b, actual, symlinks=True)
    same = alternate.exists() and alternate.samefile(actual)
    record_property("filesystem_alias", same)
    record_property("literal_names", repr(names))
    if not same:
        alternate.mkdir()
        assert not alternate.samefile(actual)
    targets = [alternate / "new/result.ufo", base / "safe-alias-control.ufo"]
    jobs = list(zip([a, actual], targets, strict=False))
    if reverse:
        jobs.reverse()
    before = [file_tree(path) for path in (a, actual)]
    runner, progress, iterator = BatchRunner(), [], None
    with Font.open(a, lazy=False) as first, Font.open(actual, lazy=False) as second:
        try:
            if same:
                with pytest.raises(ValueError, match="outside every source UFO"):
                    iterator = runner.run(jobs, Recipe(), progress=progress.append)
            else:
                iterator = runner.run(jobs, Recipe(), progress=progress.append)
                results = list(iterator)
                assert len(results) == 2 and all(result.ok for result in results)
                assert progress == results
                for source, target in jobs:
                    with Font.open(source, lazy=False) as original, Font.open(target, lazy=False) as output:
                        assert original == output
        finally:
            if iterator is not None:
                iterator.close()  # Close the exact unexpected RED iterator; never advance it.
            assert not runner.running
            if same:
                assert not progress and not any(target.exists() for target in targets)
            assert [file_tree(path) for path in (a, actual)] == before
            with Font.open(a, lazy=False) as after_first, Font.open(actual, lazy=False) as after_second:
                assert first == after_first and second == after_second


def test_run_when_deep_output_ancestor_is_file_then_error_stays_per_item(owned):
    base, a, _, _, _ = owned
    blocker = base / "ordinary-file"
    blocker.write_bytes(b"retained")
    target = blocker / "missing/result.ufo"
    runner, progress = BatchRunner(), []
    iterator = runner.run([(a, target)], Recipe(), progress=progress.append)
    assert runner.running
    try:
        results = list(iterator)
    finally:
        iterator.close()
    assert len(results) == 1 and not results[0].ok and results[0].error
    assert progress == results and not runner.running
    assert blocker.read_bytes() == b"retained" and not target.exists()
