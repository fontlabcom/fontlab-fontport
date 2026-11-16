# this_file: src/fontlab_fontport/kerning_edit.py
"""B07 model actions and inspection, independent of any UI or native host."""

from collections.abc import Iterable, Mapping
from typing import Any

from fontParts.base.normalizers import normalizeKerningKey
from fontTools.ufoLib.kerning import lookupKerningValue

from .groups import PREFIXES, stage_groups
from .kerning import Pair, stage_kerning


def inspect_kerning(pairs: Mapping, groups: Mapping, pair: Pair) -> dict[str, Any]:
    """Keep explicit presence/value separate from upstream effective fallback."""
    pair = normalizeKerningKey(pair)
    values, classes = stage_kerning(pairs), stage_groups(groups)
    return {
        "explicit": pair in values,
        "value": values.get(pair),
        "effective": lookupKerningValue(pair, values, classes, fallback=None),
    }


def edit_kerning(
    pairs: Mapping,
    action: str,
    pair: Pair,
    value: Any = None,
    *,
    groups: Mapping,
    glyphs: Iterable[str],
) -> dict[Pair, int | float]:
    """Stage Apply/Delete; only Apply requires existing glyph or group keys."""
    values = stage_kerning(pairs)
    pair = normalizeKerningKey(pair)
    if action == "delete":
        del values[pair]
    elif action == "apply":
        checked = stage_kerning({pair: value})
        classes, names = stage_groups(groups), set(glyphs)
        for side, name in enumerate(pair):
            available = classes if name.startswith(PREFIXES[side]) else names
            if name not in available:
                raise ValueError(f"Unknown kerning key: {name}")
        values.update(checked)
    else:
        raise ValueError(f"Unknown kerning operation: {action}")
    return values
