# this_file: src/fontlab_fontport/native_features.py
"""VFJ-equivalent feature snapshots and ordered writes; no FEA parsing/compile."""

import re
from collections.abc import Mapping
from typing import Any

from .info import _text
from .native_feature_split import split_history_text


def _copy_blocks(values: Mapping) -> dict:
    """Detach supported storage shapes for reads/writes, checking UTF-8 and tags.

    Both directions require four printable ASCII bytes, unique tags and aalt
    first. Split-back and native language-synthesis checks are write-only.
    """
    if not isinstance(values, Mapping) or set(values) != {"prefix", "features"}:
        raise ValueError("Feature blocks require exactly prefix and features")
    prefix = values["prefix"]
    _text(prefix, "prefix")
    prefix.encode("utf-8")
    if not isinstance(values["features"], (list, tuple)):
        raise TypeError("features must be an ordered list of (tag, code) pairs")
    features, seen = [], set()
    for pair in values["features"]:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("Each feature requires (tag, code)")
        tag, code = pair
        _text(tag, "feature tag")
        if len(tag) != 4 or any(not 33 <= ord(char) <= 126 for char in tag):
            raise ValueError("Native feature tags require four printable ASCII bytes")
        if tag in seen:
            raise ValueError(f"Duplicate feature tag: {tag}")
        if tag == "aalt" and features:
            raise ValueError("Native storage places aalt first; supply it first")
        _text(code, "feature code")
        code.encode("utf-8")
        seen.add(tag)
        features.append((tag, code))
    return {"prefix": prefix, "features": features}


def _check_languagesystem_prefix(prefix: str) -> None:
    """Mirror native needAddLanguagesystemInfo; refuse font-dependent synthesis.

    l_fea.cpp:3299–3357 checks a literal marker (even in comments), then an
    initial include line. Generated output depends on glyphs/build/scripts and
    feature language pairs (472–590,3015–3034), absent from this pure API.
    """
    if "languagesystem " in prefix:
        return
    # Native scans LF or lone CR; the CR in a CRLF remains in curstring.
    # xml::trimString removes only space/tab/LF (xml_write_aux.cpp:63–75).
    for line in re.split(r"\n|\r(?!\n)", prefix):
        line = line.strip(" \t\n")
        if not line or line.startswith("#"):
            continue
        if line.startswith("include"):
            return
        break
    raise ValueError(
        "Prefix block: missing native 'languagesystem ' marker; FontLab can inject "
        "'#> languagesystem' on read/save using font glyph scripts and feature "
        "language pairs. Supply an explicit languagesystem prefix or initial include."
    )


def stage_blocks(values: Mapping) -> dict:
    """Pure history split-back check; does not allocate native feature storage."""
    staged = _copy_blocks(values)
    features = staged["features"]
    try:
        restored = split_history_text(text_from_blocks(staged))
    except (ValueError, UnicodeError) as error:
        label = (
            "Prefix block"
            if not features
            else "Feature block " + ", ".join(repr(tag) for tag, _ in features)
        )
        raise ValueError(f"{label}: cannot simulate native history: {error}") from error
    if restored["prefix"] != staged["prefix"]:
        label = "Prefix block"
        if features and len(restored["prefix"]) > len(staged["prefix"]):
            label = f"Feature block {features[0][0]!r}"
        raise ValueError(f"{label}: history prefix differs after whole-text splitting")
    for index, (tag, code) in enumerate(features):
        if index >= len(restored["features"]):
            raise ValueError(f"Feature block {tag!r}: missing after history splitting")
        actual_tag, actual_code = restored["features"][index]
        if actual_tag != tag:
            raise ValueError(
                f"Feature block {tag!r}: history tag differs ({actual_tag!r})"
            )
        if actual_code != code:
            following = (
                f"; next Feature block {features[index + 1][0]!r}"
                if index + 1 < len(features)
                else ""
            )
            raise ValueError(f"Feature block {tag!r}: history code differs{following}")
    if len(restored["features"]) != len(features):
        tag = restored["features"][len(features)][0]
        raise ValueError(f"Feature block {tag!r}: extra block after history splitting")
    return staged


def blocks_from_info(info: Mapping) -> dict:
    """Parse only the VFJ writer's stored text, never binary-decompiled views.

    Call this on an externally obtained get_font_info snapshot when its large
    metadata payload cannot fit a run_python call. It does not fetch native data.
    """
    if not isinstance(info, Mapping):
        raise TypeError("get_font_info must return a mapping")
    entries = info.get("openTypeFeatures", [])
    if not isinstance(entries, (list, tuple)):
        raise TypeError("openTypeFeatures must be an array")
    prefix, features, has_prefix = "", [], False
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) - {"name", "feature"}:
            raise ValueError("Unexpected openTypeFeatures record")
        tag = entry.get("name", "")
        code = entry.get("feature", "")
        _text(code, "feature code")
        if tag == "" and code == "":
            continue  # VFJ loader ignores an entirely empty record.
        if tag == "":
            if has_prefix or features:
                raise ValueError("VFJ prefix must appear once before named features")
            prefix, has_prefix = code, True
        else:
            # VFJ omits empty valFeature text. Its loader stores an empty named
            # slot; it contributes no bytes to the whole-text history stream.
            _text(tag, "feature tag")
            if code:
                features.append((tag, code))
    return _copy_blocks({"prefix": prefix, "features": features})


def read_info(font_id: int) -> Mapping:
    """Embedded fontpr dispatches directly in-process; no recursive HTTP call."""
    import fontpr

    if fontpr.available() is not True:
        raise RuntimeError(
            "fontpr.get_font_info is unavailable; no unsafe fragment fallback"
        )
    info = fontpr.get_font_info(font_id=font_id)
    if not isinstance(info, Mapping):
        raise TypeError("fontpr.get_font_info returned a non-mapping response")
    return info


def read_blocks(font_id: int) -> dict:
    return blocks_from_info(read_info(font_id))


def text_from_blocks(blocks: Mapping) -> str:
    return blocks["prefix"] + "".join(code for tag, code in blocks["features"])


def write_blocks(package: Any, font_id: int, values: Mapping, undo_name: str) -> None:
    """Replay the VFJ loader's calls inside package/features history checkpoints.

    Group classes are not accessed or rewritten. Unexpected native failures can
    leave partial changes, as with the other native writes; no atomicity claim.
    """
    from .fontdata import _undo_name

    _undo_name(undo_name)
    staged = stage_blocks(values)
    info = read_info(font_id)
    current = blocks_from_info(info)
    if staged == current:
        return
    # Only a changing write allocates storage; existing no-storage baselines
    # and their Undo snapshots must not be checked for serializer synthesis.
    _check_languagesystem_prefix(staged["prefix"])
    for entry in info.get("openTypeFeatures", []):
        if entry.get("name") and not entry.get("feature", ""):
            raise ValueError(
                f"Current Undo baseline has empty Feature block {entry['name']!r}; "
                "whole-text history cannot preserve its tag"
            )
    try:
        stage_blocks(current)
    except ValueError as error:
        raise ValueError(f"Current Undo baseline is unsafe: {error}") from error
    import fontlab

    native = package.fgPackage.features
    history = [package, package.featuresContainer()]
    package.checkInitHistoryState(0)
    fontlab.flItems.notifyChangesApplied(undo_name, history)
    native.clear()  # clearFeaText(false): preserve the separate group classes.
    native.set_prefix(staged["prefix"])
    for tag, code in staged["features"]:
        native.set_feature(tag, code)
    fontlab.flItems.notifyFeaturesChanged(font_id, False)
    fontlab.flItems.notifyChangesApplied(undo_name, history)
