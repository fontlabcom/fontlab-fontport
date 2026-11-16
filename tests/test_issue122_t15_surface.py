# this_file: tests/test_issue122_t15_surface.py
"""Fontport documents its UI migration and optional native integration floor.

Fontport's documented surface equals its code (issue 122 T15). README.md
documents ``feature_blocks``; README.md and DEPENDENCIES.md name exactly the
pyproject App floor and repeat no sentence. The UI surface test moved to
Fontlabapp with the editors (issue 201).
"""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
UI_INIT = ROOT / "src/fontlab_fontport/ui/__init__.py"
APP_FLOOR = re.compile(
    r"(?<![\w-])(?:fontlab-fontlabapp>=|App >= )(\d+\.\d+\.\d+(?:\.dev\d+)?)(?![\w.]*\d)"
)
# Any App floor mention, however spaced: every hit must also be a strict hit.
LOOSE_APP_FLOOR = re.compile(
    r"(?<![\w-])(?:fontlab-fontlabapp|App)\s*[<>=!~]=?\s*\d", re.IGNORECASE
)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _app_floor() -> str:
    """The version in pyproject's ``fontlab-fontlabapp>=`` requirement."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    (requirement,) = [
        dep
        for dep in project["optional-dependencies"]["fontlab"]
        if dep.startswith("fontlab-fontlabapp")
    ]
    return requirement.split(">=", 1)[1]


def test_app_floor_regex_when_text_is_loose_then_only_exact_floors_match() -> None:
    """Only ``fontlab-fontlabapp>=X`` and ``App >= X`` name a floor; lookalikes do not."""
    assert APP_FLOOR.findall("`fontlab-fontlabapp>=1.2.0` and App >= 1.3.0.dev4") == [
        "1.2.0",
        "1.3.0.dev4",
    ]
    for loose in (
        "App 1.2.0",
        "App > 1.2.0",
        "App>=1.2.0",
        "App  >= 1.2.0",
        "my-fontlabapp>=1.2.0",
        "my-fontlab-fontlabapp>=1.2.0",
        "MyApp >= 1.2.0",
        "fontlab-fontlabapp>=1.2.0.1",
        "fontlab-fontlabapp>=1.2",
        "fontlab-fontlabapp==1.2.0",
    ):
        assert APP_FLOOR.findall(loose) == [], f"{loose!r} must not name a floor"


def test_loose_detector_when_near_misses_then_strict_check_fails_them() -> None:
    """A near-miss is seen by the loose detector but not the strict one."""
    for near in (
        "App>=1.1.0",
        "App  >= 1.1.0",
        "fontlab-fontlabapp>=1.1.0.1",
        "fontlab-fontlabapp >= 1.1.0",
        "fontlab-fontlabapp>=1.2",
        "fontlab-fontlabapp==1.2.0",
        "App > 1.2.0",
    ):
        assert LOOSE_APP_FLOOR.findall(near), f"{near!r} must be detected"
        assert len(APP_FLOOR.findall(near)) < len(LOOSE_APP_FLOOR.findall(near))
    ok = "`fontlab-fontlabapp>=1.2.0` and App >= 1.2.0"
    assert len(APP_FLOOR.findall(ok)) == len(LOOSE_APP_FLOOR.findall(ok)) == 2


def test_ui_all_when_read_then_no_editors_are_exported() -> None:
    import fontlab_fontport.ui as ui

    assert not ui.__all__, "Fontport UI is now only a tombstone"


def test_ui_init_when_read_then_lines_fit_the_ruff_line_length() -> None:
    long = [
        number
        for number, line in enumerate(UI_INIT.read_text().splitlines(), 1)
        if len(line) > 88
    ]
    assert long == [], f"ui/__init__.py lines over 88 characters: {long}"


def test_readme_when_read_then_feature_blocks_are_documented() -> None:
    """The Fontport forwarder's names are documented; needs no App (issue 201)."""
    import fontlab_fontport.feature_blocks as feature_blocks

    readme = (ROOT / "README.md").read_text()
    for name in feature_blocks.__all__:
        assert f"`{name}" in readme, f"README.md does not document {name}"
    assert "fontlabapp.fontui.feature_blocks" in readme


def test_readme_when_read_then_ui_factories_and_feature_blocks_are_documented() -> None:
    import fontlabapp.fontui.feature_blocks as feature_blocks

    readme = (ROOT / "README.md").read_text()
    for name in feature_blocks.__all__:
        assert f"`{name}" in readme, f"README.md does not document {name}"
    assert "fontlabapp.fontui.feature_blocks" in readme


def test_docs_when_app_floor_named_then_it_is_the_pyproject_floor() -> None:
    floor = _app_floor()
    for name in ("README.md", "DEPENDENCIES.md", "AGENTS.md"):
        text = (ROOT / name).read_text()
        loose = LOOSE_APP_FLOOR.findall(text)
        assert len(loose) == len(APP_FLOOR.findall(text)), (
            f"{name} has App floor mentions the strict form does not accept"
        )
        named = set(APP_FLOOR.findall(text))
        assert named == {floor}, f"{name} names App floors {named}, floor {floor}"


def test_readme_when_read_then_no_sentence_repeats() -> None:
    prose, fenced = [], False
    for line in (ROOT / "README.md").read_text().splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced:
            prose.append(line)
    sentences = [
        s for s in SENTENCE_END.split(" ".join(" ".join(prose).split())) if len(s) > 30
    ]
    repeated = {s for s in sentences if sentences.count(s) > 1}
    assert repeated == set(), repeated
