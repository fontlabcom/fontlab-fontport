# this_file: src/fontlab_fontport/kerning.py
"""Real FontParts kerning with explicit presence and validated whole batches."""

from collections.abc import ItemsView, Iterator, Mapping
from math import isfinite
from typing import Any

from fontParts.base import BaseKerning
from fontParts.base.normalizers import normalizeKerningKey

from .groups import PREFIXES, _text
from .lifetime import OwnedAccess

Pair = tuple[str, str]
MAX_VALUE = 2**53


def stage_kerning(values: Mapping[Pair, Any]) -> dict[Pair, int | float]:
    """Detach explicit pairs without rounding or conflating zero with absence.

    FontParts supplies key normalization and effective fallback. Values must
    remain finite and within the exact integer range of the native double.
    """
    if not isinstance(values, Mapping):
        raise TypeError("Kerning must be a mapping")
    result = {}
    for pair, value in values.items():
        pair = normalizeKerningKey(pair)
        for name in pair:
            _text(name)
            if name in PREFIXES:
                raise ValueError("A kerning group needs a name after its prefix")
        if type(value) not in (int, float):
            raise TypeError("Kerning values must be numbers, excluding booleans")
        if abs(value) > MAX_VALUE or not isfinite(value):
            raise ValueError("Kerning must be finite and within the exact double range")
        result[pair] = value
    return result


class RKerning(OwnedAccess, BaseKerning):
    """Fresh explicit pairs; inherited find uses the real fontTools fallback."""

    def _init(self, owner: Any) -> None:
        self._owner = owner
        self.font = owner

    def _snapshot(self) -> dict[Pair, int | float]:
        self._owner._check()
        return self._owner._backend.get_kerning()

    def _getItem(self, key: Pair) -> int | float:
        return self._snapshot()[key]

    def _items(self) -> ItemsView[Pair, int | float]:
        return self._snapshot().items()

    def _iter(self) -> Iterator[Pair]:
        return iter(self._snapshot())

    def _len(self) -> int:
        return len(self._snapshot())

    def _contains(self, key: Pair) -> bool:
        return key in self._snapshot()

    def _setItem(self, key: Pair, value: float) -> None:
        values = self._snapshot()
        values[key] = value
        self.apply(values)

    def _delItem(self, key: Pair) -> None:
        values = self._snapshot()
        del values[key]
        self.apply(values)

    def _update(self, other: Mapping[Pair, int | float]) -> None:
        values = self._snapshot()
        values.update(other)
        self.apply(values)

    def _clear(self) -> None:
        self.apply({})

    def apply(
        self, values: Mapping[Pair, Any], *, undo_name: str = "FontParts kerning"
    ) -> None:
        """Replace every explicit pair in one validated operation."""
        current = self._snapshot()
        if not _text(undo_name).strip():
            raise ValueError("Undo name must not be blank")
        staged = stage_kerning(values)
        if staged != current:
            self._owner._backend.set_kerning(staged, undo_name=undo_name)
