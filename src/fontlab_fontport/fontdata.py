# this_file: src/fontlab_fontport/fontdata.py
"""Exact feature text and plist data over real FontParts base objects."""

import math
import plistlib
from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any

from fontParts.base import BaseFeatures, BaseLib
from fontParts.base.normalizers import normalizeLibKey, normalizeLibValue

from .info import _text
from .lifetime import OwnedAccess


def _finite(value: Any) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _finite(item)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Lib numbers must be finite")
    elif isinstance(value, datetime) and (
        value.tzinfo is not None or value.microsecond
    ):
        raise ValueError(
            "XML plist dates require naive UTC with whole-second precision"
        )


def stage_lib(values: Mapping[str, Any]) -> dict[str, Any]:
    """Detach supported XML plist values; invalid batches reach no backend."""
    if not isinstance(values, Mapping):
        raise TypeError("Lib data must be a mapping")
    values = dict(values)
    for key, value in values.items():
        normalizeLibKey(key)
        normalizeLibValue(value)
    _finite(values)
    plistlib.dumps(
        values, sort_keys=False
    )  # Validate serialization without parsing text back.
    return _arrays(values)


def _arrays(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _arrays(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_arrays(item) for item in value]
    return deepcopy(value)


def changed_lib(
    current: Mapping[str, Any],
    values: Mapping[str, Any],
    *,
    value_validator: Callable[[Any], None] | None = None,
) -> dict[str, Any]:
    """Validate changed leaves; unchanged foreign values remain opaque at depth.

    Array entries are matched by index. A moved foreign value is a new write
    and must validate, just like an inserted mapping member.
    """
    if not isinstance(values, Mapping):
        raise TypeError("Lib data must be a mapping")
    missing = object()

    def stage(before, after):
        if before is not missing and same_lib(before, after):
            return deepcopy(after)
        if isinstance(before, Mapping) and isinstance(after, Mapping):
            result = {}
            for key, value in after.items():
                normalizeLibKey(key)
                result[key] = stage(before.get(key, missing), value)
            return result
        if isinstance(before, (list, tuple)) and isinstance(after, (list, tuple)):
            return [
                stage(before[i] if i < len(before) else missing, value)
                for i, value in enumerate(after)
            ]
        value = stage_lib({"value": after})["value"]
        if value_validator is not None:
            value_validator(value)
        return value

    return stage(current, values)


def same_lib(left: Any, right: Any) -> bool:
    """Compare typed values; JSON true, integer 1 and real 1.0 are distinct."""
    if type(left) is not type(right):
        return False
    if isinstance(left, Mapping):
        return left.keys() == right.keys() and all(
            same_lib(left[key], right[key]) for key in left
        )
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(
            same_lib(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _undo_name(value: str) -> None:
    _text(value, "undo_name")
    if not value.strip():
        raise ValueError("Undo name must not be blank")


class RFeatures(OwnedAccess, BaseFeatures):
    """Text setters dispatch synchronously; no compilation is implied."""

    def _init(self, owner):
        self._owner = owner
        self.font = owner

    def _get_text(self):
        self._owner._check()
        return self._owner._backend.get_features()

    def _set_text(self, value):
        self.apply(value)

    def get_blocks(self) -> dict:
        """Return detached native {prefix, features: [(tag, code), ...]} data."""
        self._owner._check()
        return self._owner._backend.get_feature_blocks()

    def set_blocks(
        self, values: Mapping, *, undo_name: str = "FontParts features"
    ) -> None:
        """Replace structured native blocks without guessing whole-text splits."""
        self._owner._check()
        self._owner._backend.set_feature_blocks(values, undo_name=undo_name)

    def apply(self, text: str | None, *, undo_name: str = "FontParts features") -> None:
        self._owner._check()
        _undo_name(undo_name)
        if text is not None:
            _text(text, "features")
        if text != self.text:
            self._owner._backend.set_features(text, undo_name=undo_name)


class RLib(OwnedAccess, BaseLib):
    """Changed-value validation and detached reads of native/FontParts data.

    Reassign a nested value to persist its edits. Mutating a returned dictionary
    or array alone does not silently mutate a native document. Unchanged foreign
    leaves (including native null) survive edits to their siblings. New foreign
    values and array elements moved to a different index must validate.
    """

    # Reads may contain foreign native JSON nulls. Writes are validated by
    # changed_lib instead of applying FontParts' plist normalizer to neighbours.
    valueNormalizer = None

    def _init(self, owner):
        self._owner = owner
        self.font = owner

    def _snapshot(self):
        self._owner._check()
        return deepcopy(self._owner._backend.get_lib())

    def _getItem(self, key):
        return self._snapshot()[key]

    def _items(self):
        return self._snapshot().items()

    def _contains(self, key):
        return key in self._snapshot()

    def _setItem(self, key, value):
        values = self._snapshot()
        values[key] = value
        self.apply(values)

    def _delItem(self, key):
        values = self._snapshot()
        del values[key]
        self.apply(values)

    def _update(self, other):
        values = self._snapshot()
        values.update(other)
        self.apply(values)

    def _clear(self):
        self.apply({})

    def apply(
        self, values: Mapping[str, Any], *, undo_name: str = "FontParts lib"
    ) -> None:
        current = self._snapshot()
        _undo_name(undo_name)
        staged = changed_lib(current, values)
        if not same_lib(staged, current):
            self._owner._backend.set_lib(staged, undo_name=undo_name)


class FeatureEdit:
    """B08 editor state: typing is detached; Apply/Revert are explicit."""

    def __init__(self, features: BaseFeatures) -> None:
        self.features = features
        self.revert()

    @property
    def dirty(self) -> bool:
        return self.text != self._baseline

    def revert(self) -> None:
        self.text = self._baseline = self.features.text

    def apply(self) -> None:
        if self.text is not None:
            _text(self.text, "features")
        self.features.text = self.text
        self.revert()
