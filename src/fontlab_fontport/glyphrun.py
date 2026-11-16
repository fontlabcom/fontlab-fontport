# this_file: src/fontlab_fontport/glyphrun.py
"""Read-only glyph sequence placement for preview controls.

This is Unicode assignment lookup and UFO pair/group kerning, not shaping.
fontTools supplies the kerning fallback rules; no parallel implementation is
maintained here. Missing input remains an explicit occurrence for the UI.
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from math import isfinite
from typing import Any, Literal

from fontTools.ufoLib.kerning import glyphsToGroups, lookupKerningValue

Direction = Literal["ltr", "rtl"]


@dataclass(frozen=True)
class Occurrence:
    index: int
    label: str
    name: str | None
    x: float
    advance: float


@dataclass(frozen=True)
class GlyphRun:
    glyphs: tuple[Occurrence, ...]
    advance: float
    direction: Direction

    @property
    def diagnostics(self) -> tuple[str, ...]:
        return tuple(
            f"Missing glyph for {g.label!r}" for g in self.glyphs if g.name is None
        )


def _finite(value: Any) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError("Glyph advances and kerning must be finite numbers")
    return number


def _missing_advance(font: Any) -> float:
    value = getattr(font.info, "unitsPerEm", None)
    upm = 1000.0 if value is None else _finite(value)
    if upm <= 0:
        raise ValueError("unitsPerEm must be positive")
    return upm / 2


def _kerning_lookup(font: Any, enabled: bool) -> Callable[[tuple[str, str]], float]:
    pairs = dict(font.kerning.items()) if enabled else {}
    groups = dict(font.groups.items()) if enabled else {}
    first, second = glyphsToGroups(groups)
    return partial(
        lookupKerningValue,
        kerning=pairs,
        groups=groups,
        glyphToFirstGroup=first,
        glyphToSecondGroup=second,
    )


def _place(
    font: Any, tokens: list[tuple[str, str | None]], kerning: bool, direction: Direction
) -> GlyphRun:
    if direction not in ("ltr", "rtl"):
        raise ValueError("direction must be 'ltr' or 'rtl'")
    if not tokens:
        return GlyphRun((), 0.0, direction)
    lookup = _kerning_lookup(font, kerning)
    missing_advance = _missing_advance(font)
    cursor, previous, result = 0.0, None, []
    for index, (label, name) in enumerate(tokens):
        width = _finite(font[name].width) if name is not None else missing_advance
        adjustment = _finite(lookup((previous, name))) if previous and name else 0
        cursor = _finite(
            cursor + (adjustment if direction == "ltr" else -adjustment - width)
        )
        result.append(Occurrence(index, label, name, cursor, width))
        cursor = _finite(cursor + (width if direction == "ltr" else 0))
        previous = name
    return GlyphRun(tuple(result), abs(cursor), direction)


def _unicode_rows(font: Any):
    """``(name, unicodes)`` per glyph in model-key order.

    A live font reads all of them in one native pass (``glyph_summaries``);
    asking ``font[name]`` for each glyph would load every outline.
    """
    summaries = getattr(font, "glyph_summaries", None)
    if callable(summaries):
        return [(name, codes) for name, codes, _ in summaries()]
    # UFO model iteration yields glyphs, not names.
    return [(name, font[name].unicodes) for name in font.keys()]  # noqa: SIM118


def layout_text(
    font: Any, text: str, *, kerning: bool = True, direction: Direction = "ltr"
) -> GlyphRun:
    """Place characters by assigned Unicode, taking the first model-key match."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return _place(font, [], kerning, direction)
    mapping: dict[int, str] = {}
    for name, codes in _unicode_rows(font):
        for code in codes:
            mapping.setdefault(code, name)
    return _place(
        font, [(char, mapping.get(ord(char))) for char in text], kerning, direction
    )


def layout_names(
    font: Any, text: str, *, kerning: bool = True, direction: Direction = "ltr"
) -> GlyphRun:
    """Place whitespace-separated slash tokens such as '/A /V /Aacute'."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    tokens = text.split()
    if any(not token.startswith("/") or len(token) == 1 for token in tokens):
        raise ValueError("Use slash-prefixed glyph names separated by whitespace")
    return _place(
        font,
        [(token, token[1:] if token[1:] in font else None) for token in tokens],
        kerning,
        direction,
    )
