# this_file: tests/test_operations.py
"""B09 real affine geometry, inspectable recipes and reopened batch artifacts."""

import importlib
from copy import deepcopy

import pytest
from fontTools.pens.recordingPen import RecordingPointPen
from ufoLib2 import Font
from ufoLib2.objects import Component

from fontlab_fontport.operations import (
    BatchRunner,
    Recipe,
    transform_font,
    transform_glyph,
)


def fixture_font():
    font = Font()
    font.info.familyName, font.info.styleName = "Owned", "Regular"
    font.info.unitsPerEm = 1000
    glyph = font.newGlyph("A")
    glyph.width = 500
    pen = glyph.getPen()
    pen.moveTo((10, 20))
    pen.lineTo((100, 20))
    pen.lineTo((100, 200))
    pen.closePath()
    glyph.appendAnchor({"name": "top", "x": 20, "y": 200})
    glyph.appendGuideline({"x": 20, "y": 0, "angle": 90, "name": "guide"})
    font.newGlyph("C").components.append(Component("A", (1, 0, 0, 1, 30, 40)))
    font.features.text = "# Ω\n"
    font.lib["unknown"] = {"binary": b"\x00"}
    return font


def signature(glyph):
    pen = RecordingPointPen()
    glyph.drawPoints(pen)
    return pen.value


def test_recipe_when_identity_disabled_or_zero_intensity_then_identical_source():
    source = fixture_font()
    before = deepcopy(source)
    for recipe in (
        Recipe(),
        Recipe(matrix=(2, 0, 0, 2, 10, 20), enabled=False),
        Recipe(matrix=(2, 0, 0, 2, 10, 20), intensity=0),
    ):
        result = transform_glyph(source["A"], recipe)
        assert signature(result) == signature(source["A"])
        assert result.width == 500 and result.anchors == source["A"].anchors
    assert source == before, "preview transforms leave every source object untouched"


def test_affine_when_half_intensity_then_metadata_anchors_guides_and_component_geometry():
    source = fixture_font()
    recipe = Recipe(matrix=(3, 0, 0, 3, 20, 40), intensity=50)
    result = transform_font(source, recipe)
    point = result["A"].contours[0].points[0]
    assert (point.x, point.y) == (30, 60)
    assert result["A"].width == 1000
    assert (result["A"].anchors[0].x, result["A"].anchors[0].y) == (50, 420)
    assert result["A"].guidelines[0].x == 50
    assert result["C"].components[0].transformation == (1, 0, 0, 1, 60, 80), (
        "whole-font transforms conjugate components instead of scaling bases twice"
    )
    assert result.features.text == source.features.text and result.lib == source.lib
    assert source["A"].width == 500 and source["C"].components[0].transformation[
        -2:
    ] == (30, 40)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"matrix": (1, 2)},
        {"matrix": (1, 0, 0, 0, 0, 0)},
        {"matrix": (float("nan"), 0, 0, 1, 0, 0)},
        {"intensity": -1},
        {"intensity": 101},
        {"enabled": "yes"},
        {"method": "stem-preserving"},
    ],
)
def test_recipe_when_invalid_or_unavailable_then_refused(kwargs):
    with pytest.raises((ValueError, TypeError, NotImplementedError)):
        Recipe(**kwargs)


def test_recipe_when_saved_then_exact_settings_and_inspectable_script(tmp_path):
    recipe = Recipe(matrix=(1.2, 0.1, 0, 1, 10, -20), intensity=42)
    settings = tmp_path / "recipe.json"
    recipe.save(settings)
    assert Recipe.load(settings) == recipe
    assert "Recipe(" in recipe.script() and "transform_font" in recipe.script()
    namespace = {}
    exec(compile(recipe.script(), "recipe.py", "exec"), namespace)
    operations = importlib.import_module("fontlab_fontport.operations")
    assert importlib.import_module("fly.fp.operations") is operations
    assert namespace["Recipe"] is Recipe
    assert namespace["transform_font"] is transform_font
    assert namespace["recipe"] == recipe
    source = fixture_font()
    expected = transform_font(source, recipe)
    actual = namespace["run"](source)
    assert signature(actual["A"]) == signature(expected["A"])
    assert actual["A"].width == expected["A"].width
    with pytest.raises(FileExistsError):
        recipe.save(settings)
    settings.write_text('{"method":"run-python","code":"bad"}')
    with pytest.raises((TypeError, NotImplementedError)):
        Recipe.load(settings)


def test_batch_when_success_failure_cancel_then_progress_and_running_reset(tmp_path):
    source = tmp_path / "source.ufo"
    fixture_font().save(source)
    target = tmp_path / "out.ufo"
    runner = BatchRunner()
    progress = []
    results = list(
        runner.run(
            [(source, target)],
            Recipe(matrix=(2, 0, 0, 2, 0, 0)),
            progress=progress.append,
        )
    )
    assert results[0].ok and progress == results and not runner.running
    with Font.open(target) as font:
        assert font["A"].width == 1000 and font["A"].contours[0].points[0].x == 20
        assert font.lib["unknown"]["binary"] == b"\x00"
    bad = tmp_path / "bad.ufo"
    bad.mkdir()
    failures = list(runner.run([(bad, tmp_path / "bad-out.ufo")], Recipe()))
    result = failures[0]
    assert not result.ok and result.error and not runner.running
    cancelled = list(
        runner.run(
            [(source, tmp_path / "cancel.ufo")], Recipe(), cancelled=lambda: True
        )
    )
    assert (
        cancelled == []
        and not runner.running
        and not (tmp_path / "cancel.ufo").exists()
    )


def test_batch_when_missing_duplicate_or_nested_run_then_no_output(tmp_path):
    runner = BatchRunner()
    source, target = tmp_path / "source.ufo", tmp_path / "target.ufo"
    fixture_font().save(source)
    with pytest.raises(FileNotFoundError):
        list(
            runner.run(
                [(source, target), (tmp_path / "missing.ufo", tmp_path / "other.ufo")],
                Recipe(),
            )
        )
    with pytest.raises(ValueError, match="Duplicate"):
        list(runner.run([(source, target), (source, target)], Recipe()))
    assert not target.exists() and not runner.running
    jobs = runner.run([(source, target)], Recipe())
    assert next(jobs).ok and runner.running
    with pytest.raises(RuntimeError, match="running"):
        next(runner.run([(source, tmp_path / "another.ufo")], Recipe()))
    jobs.close()
    assert not runner.running
