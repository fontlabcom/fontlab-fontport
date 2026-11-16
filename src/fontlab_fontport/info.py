# this_file: src/fontlab_fontport/info.py
"""Validation for the bounded native font-information update boundary."""

import math
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from fontTools.ufoLib import validateFontInfoVersion3ValueForAttribute

from .errors import UnsupportedCapability

TEXT_FIELDS = frozenset(
    (
        "familyName",
        "styleName",
        "note",
        "copyright",
        "trademark",
        "openTypeNameDesigner",
        "openTypeNameDesignerURL",
        "openTypeNameManufacturer",
        "openTypeNameManufacturerURL",
        "openTypeNameLicense",
        "openTypeNameLicenseURL",
    )
)
INTEGER_FIELDS = frozenset(("unitsPerEm", "versionMajor", "versionMinor"))
METRIC_FIELDS = frozenset(
    ("ascender", "descender", "capHeight", "xHeight", "italicAngle")
)
STRUCTURED_FIELDS = frozenset(
    (
        "openTypeOS2Panose",
        "openTypeOS2WeightClass",
        "openTypeOS2WidthClass",
        "openTypeNameRecords",
        "postscriptStemSnapH",
        "postscriptStemSnapV",
    )
)
INFO_FIELDS = TEXT_FIELDS | INTEGER_FIELDS | METRIC_FIELDS | STRUCTURED_FIELDS
# OS/2 typo, hhea and Windows vertical metrics: readable from native info, not writable here.
READ_ONLY_FIELDS = frozenset(
    (
        "openTypeOS2TypoAscender",
        "openTypeOS2TypoDescender",
        "openTypeOS2TypoLineGap",
        "openTypeHheaAscender",
        "openTypeHheaDescender",
        "openTypeHheaLineGap",
        "openTypeOS2WinAscent",
        "openTypeOS2WinDescent",
    )
)
# Native setters that disable Edit > Undo/Redo once the document has history (Issue 250 N3).
STEM_SNAP_FIELDS = frozenset(("postscriptStemSnapH", "postscriptStemSnapV"))
NATIVE_INT_MAX = 2**31 - 1


def _text(value: Any, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} requires Unicode text")
    if "\x00" in value:
        raise ValueError(f"{name} cannot contain NUL")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} requires valid Unicode text") from exc


def stage_info(values: Mapping[str, Any], undo_name: str) -> dict[str, Any]:
    """Detach and validate every field before native storage/history changes.

    FontLab master metrics are concrete doubles, with no unset representation.
    None is refused explicitly rather than silently storing a zero metric.
    Integer fields are bounded by the host's signed native-int binding.
    """
    if not isinstance(values, Mapping):
        raise TypeError("Font info updates require a mapping")
    _text(undo_name, "undo_name")
    if not undo_name.strip():
        raise ValueError("undo_name must be nonempty text")
    staged = deepcopy(dict(values))
    for attr, value in staged.items():
        if attr not in INFO_FIELDS:
            raise UnsupportedCapability(
                f"info.{attr}", f"Native info field unsupported: {attr}"
            )
        if value is None and attr not in METRIC_FIELDS:
            raise UnsupportedCapability(
                "info.unset", f"Native {attr} has no unset representation"
            )
        if attr == "unitsPerEm" and isinstance(value, float) and math.isfinite(value):
            if not value.is_integer():
                raise UnsupportedCapability(
                    "info.unitsPerEm.fractional",
                    "Native UPM storage is integral; no write/history changed",
                )
            value = staged[attr] = int(value)
        if (
            attr in ("openTypeOS2WeightClass", "openTypeOS2WidthClass")
            and isinstance(value, int)
            and not isinstance(value, bool)
        ):
            value = staged[attr] = int(value)
        if attr in TEXT_FIELDS:
            _text(value, attr)
        elif attr in INTEGER_FIELDS:
            minimum = 1 if attr == "unitsPerEm" else 0
            if type(value) is not int or not minimum <= value <= NATIVE_INT_MAX:
                raise ValueError(
                    f"{attr} requires an integer in {minimum}..{NATIVE_INT_MAX}"
                )
        elif attr in STRUCTURED_FIELDS:
            _structured(value, attr)
        else:
            _metric(value, attr)
    return staged


def _structured(value: Any, attr: str) -> None:
    if not validateFontInfoVersion3ValueForAttribute(attr, value):
        raise ValueError(f"Invalid UFO structured value for {attr}")
    _native_values(value, attr)
    if attr == "openTypeOS2Panose" and any(
        type(v) is not int or not 0 <= v <= 255 for v in value
    ):
        raise ValueError("Panose requires ten bytes in 0..255")
    if attr == "openTypeNameRecords":
        for record in value:
            if any(
                type(record[key]) is not int or not 0 <= record[key] <= 65535
                for key in ("nameID", "platformID", "encodingID", "languageID")
            ):
                raise ValueError("Name record identifiers require unsigned16 integers")


def _native_values(value: Any, attr: str) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _native_values(item, attr)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _native_values(item, attr)
    elif isinstance(value, str):
        _text(value, attr)
    else:
        _metric(value, attr)
        if (
            isinstance(value, int)
            and not -NATIVE_INT_MAX - 1 <= value <= NATIVE_INT_MAX
        ):
            raise ValueError(f"{attr} exceeds the native integer range")


def normalize_info(attr: str, value: Any) -> Any:
    """Detach native structured readback, including tuple/QVariant containers."""
    if attr not in STRUCTURED_FIELDS or value is None:
        return deepcopy(value)
    if attr in ("openTypeOS2WeightClass", "openTypeOS2WidthClass"):
        return value
    values = list(value)
    return (
        [dict(record) for record in values] if attr == "openTypeNameRecords" else values
    )


def _metric(value: Any, attr: str) -> None:
    if value is None:
        raise UnsupportedCapability(
            f"info.{attr}.absent", f"FontLab cannot unset the native {attr} metric"
        )
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{attr} requires a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{attr} requires a finite native double")
