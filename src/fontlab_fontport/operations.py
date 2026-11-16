# this_file: src/fontlab_fontport/operations.py
"""Detached affine previews using real fontTools pens and ufoLib2 objects."""

import math
from copy import deepcopy

from fontTools.misc.transform import Identity, Transform
from fontTools.pens.transformPen import TransformPointPen
from ufoLib2 import Font
from ufoLib2.objects import Glyph

from .batch import BatchRunner
from .recipe import Recipe, finite_number

__all__ = ["BatchRunner", "Recipe", "transform_font", "transform_glyph"]


def _transform_guideline(guide, matrix: Transform) -> None:
    x, y = guide.x or 0, guide.y or 0
    angle = guide.angle if guide.angle is not None else (0 if guide.x is None else 90)
    radians = math.radians(angle)
    dx, dy = matrix.transformVector((math.cos(radians), math.sin(radians)))
    guide.x, guide.y = matrix.transformPoint((x, y))
    guide.angle = math.degrees(math.atan2(dy, dx)) % 360


def transform_glyph(source: Glyph, recipe: Recipe) -> Glyph:
    """Copy/transform one UFO glyph with unchanged component bases.

    Anchors, guides, images and component matrices follow outlines. Advance
    widths/heights are scalar projections of transformed advance vectors;
    translation does not change spacing. Native hints are outside UFO geometry.
    """
    if not isinstance(source, Glyph):
        raise TypeError("Supply a ufoLib2 Glyph (backend.read_glyph returns one)")
    result = deepcopy(source)
    matrix = recipe.transform
    if matrix == Identity:
        return result
    result.contours.clear()
    result.components.clear()
    source.drawPoints(TransformPointPen(result.getPointPen(), matrix))
    result.width = finite_number(matrix.transformVector((source.width, 0))[0])
    result.height = finite_number(matrix.transformVector((0, source.height))[1])
    for anchor in result.anchors:
        anchor.x, anchor.y = matrix.transformPoint((anchor.x, anchor.y))
    for guide in result.guidelines:
        _transform_guideline(guide, matrix)
    if result.image.fileName is not None:
        result.image.transformation = matrix.transform(result.image.transformation)
    _check_geometry(result)
    return result


def _check_geometry(glyph: Glyph) -> None:
    for contour in glyph.contours:
        for point in contour.points:
            finite_number(point.x)
            finite_number(point.y)
    for component in glyph.components:
        for value in component.transformation:
            finite_number(value)
    for anchor in glyph.anchors:
        finite_number(anchor.x)
        finite_number(anchor.y)
    for guide in glyph.guidelines:
        for value in (guide.x, guide.y, guide.angle):
            if value is not None:
                finite_number(value)


def transform_font(source: Font, recipe: Recipe) -> Font:
    """Transform all UFO layers without editing source or double-scaling bases.

    Font metadata/features/lib/groups/kerning are retained. This is geometric
    transformation, not interpolation, metric rescaling or a font-build engine.
    """
    result = deepcopy(source)
    inverse = recipe.transform.inverse()
    for layer in result.layers:
        for name in list(layer.keys()):
            glyph = transform_glyph(layer[name], recipe)
            if recipe.transform != Identity:
                for component in glyph.components:
                    component.transformation = Transform(
                        *component.transformation
                    ).transform(inverse)
                _check_geometry(glyph)
            layer.insertGlyph(glyph, overwrite=True)
    for guide in result.guidelines:
        if recipe.transform != Identity:
            _transform_guideline(guide, recipe.transform)
    return result
