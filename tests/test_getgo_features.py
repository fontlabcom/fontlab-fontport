# this_file: tests/test_getgo_features.py
"""Read-only regression against every GetGo VFJ in the scripting workspace."""

import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

from fontlab_fontport import native_features
from fontlab_fontport.native_features import (
    blocks_from_info,
    stage_blocks,
    write_blocks,
)


def getgo_dir() -> Path | None:
    """Prefer an existing env override, then the nearest workspace ancestor."""
    override = os.environ.get("FONTPORT_GETGO_DIR")
    candidates = [Path(override).expanduser()] if override else []
    candidates.extend(
        parent / "fontlab-python-examples" / relative
        for parent in Path(__file__).resolve().parents
        for relative in ("testdata/getgo", "lessons/src/fontlab_python_lessons/getgo/data")
    )
    return next((path for path in candidates if path.is_dir()), None)


def test_getgo_when_all_vfjs_then_identical_writes_succeed_and_only_changes_check_synthesis(
    monkeypatch,
):
    corpus = getgo_dir()
    if corpus is None:
        pytest.skip(
            "GetGo is an external workspace corpus, not distributed with Fontport"
        )
    paths = sorted(corpus.rglob("*.vfj"))
    assert len(paths) == 99, "Re-audit corpus coverage if GetGo's VFJ count changes"
    failures, with_features, without_features, synthesis_refused, identical_writes = (
        [],
        0,
        0,
        0,
        0,
    )
    for path in paths:
        document = json.loads(path.read_bytes())
        info = document.get("font", document)
        if info.get("openTypeFeatures"):
            with_features += 1
        else:
            without_features += 1
        try:
            blocks = blocks_from_info(info)
            assert stage_blocks(blocks) == blocks, "staging changed stored text blocks"
            monkeypatch.setattr(
                native_features, "read_info", lambda font_id, snapshot=info: snapshot
            )
            write_blocks(object(), 42, blocks, "GetGo identical blocks")
            identical_writes += 1
            if "languagesystem " not in blocks["prefix"]:
                changed = deepcopy(blocks)
                changed["features"] = [("kern", "feature kern {} kern;\n")]
                with pytest.raises(
                    ValueError, match=r"Prefix block.*#> languagesystem"
                ):
                    write_blocks(object(), 42, changed, "GetGo changing blocks")
                synthesis_refused += 1
        except (ValueError, TypeError, AssertionError) as error:
            failures.append(f"{path.relative_to(corpus)}: {error}")
    assert not failures, "\n".join(failures)
    assert (with_features, without_features) == (85, 14)
    assert identical_writes == 99, (
        "Every identical write must return before native calls"
    )
    assert synthesis_refused == 14, (
        "Changing writes on all missing prefixes must be checked"
    )


@pytest.mark.parametrize(
    "layout", ["fontlab-fontport", ".worktrees/issue-105-fontport"]
)
@pytest.mark.parametrize("data_layout", [
    "testdata/getgo", "lessons/src/fontlab_python_lessons/getgo/data",
])
def test_getgo_dir_when_canonical_or_worktree_layout_then_finds_workspace_corpus(
    tmp_path, monkeypatch, layout, data_layout
):
    workspace = tmp_path / "workspace"
    corpus = workspace / "fontlab-python-examples" / data_layout
    corpus.mkdir(parents=True)
    monkeypatch.delenv("FONTPORT_GETGO_DIR", raising=False)
    monkeypatch.setitem(
        globals(), "__file__", str(workspace / layout / "tests/test_getgo_features.py")
    )
    assert getgo_dir() == corpus


def test_getgo_dir_when_nested_workspaces_then_first_ancestor_wins(
    tmp_path, monkeypatch
):
    inner = tmp_path / "workspace"
    for root in (tmp_path, inner):
        (root / "fontlab-python-examples/testdata/getgo").mkdir(parents=True)
    monkeypatch.delenv("FONTPORT_GETGO_DIR", raising=False)
    monkeypatch.setitem(
        globals(),
        "__file__",
        str(inner / "fontlab-fontport/tests/test_getgo_features.py"),
    )
    assert getgo_dir() == inner / "fontlab-python-examples/testdata/getgo"


def test_getgo_dir_when_env_override_then_takes_priority(tmp_path, monkeypatch):
    monkeypatch.setenv("FONTPORT_GETGO_DIR", str(tmp_path))
    assert getgo_dir() == tmp_path


def test_getgo_dir_when_no_candidate_then_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("FONTPORT_GETGO_DIR", str(tmp_path / "absent"))
    monkeypatch.setitem(
        globals(), "__file__", str(tmp_path / "isolated/tests/test_getgo_features.py")
    )
    # tmp_path can sit inside a real workspace; ignore real folders above it.
    real_is_dir = Path.is_dir
    monkeypatch.setattr(
        Path, "is_dir", lambda path: tmp_path in path.parents and real_is_dir(path)
    )
    assert getgo_dir() is None


def test_getgo_dir_when_override_absent_but_ancestor_exists_then_does_not_skip(
    tmp_path, monkeypatch
):
    corpus = tmp_path / "fontlab-python-examples/testdata/getgo"
    corpus.mkdir(parents=True)
    monkeypatch.setenv("FONTPORT_GETGO_DIR", str(tmp_path / "absent"))
    monkeypatch.setitem(
        globals(),
        "__file__",
        str(tmp_path / "fontlab-fontport/tests/test_getgo_features.py"),
    )
    assert getgo_dir() == corpus
