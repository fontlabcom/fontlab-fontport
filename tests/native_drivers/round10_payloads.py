# this_file: tests/native_drivers/round10_payloads.py
"""Narrow semantic equivalences; raw receipts remain untouched."""

from copy import deepcopy

COMPARISON_NOTES = [
    "fontlab.lastModified: root save/edit timestamp is excluded from equality",
    "fontlab.save.emptyShape: a bare empty elementData has no outlines",
    "fontlab.layer.activeUIState: layer active is UI selection, not font data",
]


def canonical_payload(value):
    value = deepcopy(value)
    if not isinstance(value, dict):
        return value
    value.pop("lastModified", None)
    for layer in value.get("layers", []):
        layer.pop("active", None)
        if "elements" in layer:
            layer["elements"] = [
                element
                for element in layer["elements"]
                if element != {"elementData": {}}
            ]
            if not layer["elements"]:
                layer.pop("elements")
    return value


READBACK_ATOL = 1e-3
"""FontLab read-backs are float32 after Redo (10.4 -> 10.3999996); drift measured
at ~1.6e-5, up to 5e-4 after save and reopen, as App's COORDINATE_TOLERANCE."""


def _number(token):
    try:
        return float(token)
    except ValueError:
        return None


def values_close(left, right, atol=READBACK_ATOL):
    """Structural equality where numbers, also inside node strings, match within atol."""
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            values_close(left[key], right[key], atol) for key in left
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(
            values_close(a, b, atol) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, str) and isinstance(right, str):
        a, b = left.split(), right.split()
        return len(a) == len(b) and all(
            x == y
            or (_number(x) is not None and _number(y) is not None
                and abs(_number(x) - _number(y)) <= atol)
            for x, y in zip(a, b, strict=True)
        )
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(left - right) <= atol
    return left == right


def payload_equal(left, right):
    return values_close(canonical_payload(left), canonical_payload(right))


def geometry_snapshot(value):
    """Freeze MCP contour/point/component records, separately from UI metadata."""
    import json

    canonical = canonical_payload(value)
    layers = None if canonical is None else [
        {"name": layer.get("name"), "elements": layer.get("elements", [])}
        for layer in canonical.get("layers", [])
    ]
    return json.dumps(layers, sort_keys=True, ensure_ascii=True)


def geometry_receipt(observed, expected):
    """Compare fresh MCP geometry with a frozen baseline, retaining both."""
    import hashlib
    import json

    actual = geometry_snapshot(observed)
    return {
        "geometry_equal": values_close(json.loads(actual), json.loads(expected)),
        "observed_geometry": actual,
        "expected_geometry": expected,
        "observed_geometry_sha256": hashlib.sha256(actual.encode()).hexdigest(),
        "expected_geometry_sha256": hashlib.sha256(expected.encode()).hexdigest(),
    }
