# this_file: src/fontlab_fontport/capabilities.py
"""Named native limitations that UI clients can show without probing a write."""

from .info import STRUCTURED_FIELDS

NATIVE_CAPABILITIES = {
    "glyph.externalChangeNotifications": {
        "supported": False,
        "reason": "Native edits/Undo/Redo do not notify the defcon snapshot; reload with font.refresh() and reacquire handles",
    },
    "glyph.anchor.precision": {
        "supported": False,
        "reason": "Fractional anchors are refused before write; native anchor/history storage rounds",
    },
    "kerning.fractionalHistory": {
        "supported": False,
        "reason": "Fractional current or staged kerning is refused before changing history",
    },
    "info.exactSingleUndo": {
        "supported": False,
        "reason": "Strict changing batches refuse: the package/master protocol adds an extra no-op checkpoint; require_single_undo=False is the D18 editing default",
    },
    "info.postscriptStemSnap.history": {
        "supported": False,
        "reason": "Changing postscriptStemSnapH/V is refused unless the font is the active document without unsaved history: the native setter records no Undo row for a non-active document, disables Edit > Undo/Redo and can leave the change unrecorded",
    },
    "info.clearOptionalMetric": {
        "supported": False,
        "reason": "Master metrics have concrete double storage; None is refused rather than converted to zero",
    },
    "groups.unicodeNames": {
        "supported": False,
        "reason": "Native group key/VFJ preservation is not lossless; changing Unicode names is refused",
    },
    "groups.divergentBothSides": {
        "supported": False,
        "reason": "One native both-sided group has one member list; divergent sides are refused",
    },
    "groups.legacyFlagsVfj": {
        "supported": False,
        "reason": "Strict writes/VFJ saves containing opaque legacy font-global groups refuse; require_persistence=False is the D18 baseline-compatible default",
    },
}

STRUCTURED_ROUTES = {
    field: {
        "read": f"flPackage.info.{field}",
        "write": f"flPackage.info.{field}",
        "bound": "unknown",
        "native_roundtrip_verified": False,
        "history": "package + mastersContainer, extra no-op row",
    }
    for field in sorted(STRUCTURED_FIELDS)
}

_SETTER_LINES = {
    "openTypeNameRecords": 2031,
    "openTypeOS2Panose": 2263,
    "openTypeOS2WeightClass": 2724,
    "openTypeOS2WidthClass": 2748,
    "postscriptStemSnapH": 3197,
    "postscriptStemSnapV": 3237,
}
for _field, _line in _SETTER_LINES.items():
    STRUCTURED_ROUTES[_field]["bound"] = True
    STRUCTURED_ROUTES[_field]["native_source"] = (
        f"Proteus/pygate/pyflpackage.cpp:{_line}"
    )


# Master-backed storage routes: the info.* setters modify a regenerated fg::Style.
for _field, _property, _line in (
    ("openTypeOS2Panose", "panose", 1512),
    ("openTypeOS2WeightClass", "weight_value", 949),
    ("openTypeOS2WidthClass", "width_value", 951),
):
    STRUCTURED_ROUTES[_field].update(
        read=f"flPackage.{_property}",
        write=f"flPackage.{_property}",
        native_source=f"Proteus/pygate/pyflpackage.cpp:{_line}",
        persistence_source="Proteus/common/model/flpackage.cpp:5830-5875",
        native_roundtrip_verified=False,
    )
STRUCTURED_ROUTES["openTypeNameRecords"].update(
    write=None,
    write_supported=False,
    reason="info.openTypeNameRecords.persistence: setLocalizedNames has no Python binding; the info setter changes regenerated data",
    persistence_source="Proteus/common/model/flpackage.cpp:16806-16836",
)


# C4 measured a pre-change no-op row in addition to the restoring edit row.
NATIVE_CAPABILITIES["glyph.exactSingleUndo"] = {
    "supported": False,
    "reason": "Native pre/post checkpoints produce two rows; the first Undo must restore geometry, the second is a no-op",
    "native_evidence": "glyport-matrix/probe_undo_cloned_shape.json",
}
NATIVE_CAPABILITIES["groups.multiMembership"] = {
    "supported": False,
    "reason": "Changing mappings with multiple kerning memberships per side refuse before native writes",
}
for _field in (
    "openTypeOS2Panose", "openTypeOS2WeightClass", "openTypeOS2WidthClass",
    "postscriptStemSnapH", "postscriptStemSnapV",
):
    STRUCTURED_ROUTES[_field]["bound"] = "key-master"
    NATIVE_CAPABILITIES["info." + _field] = {
        "supported": True,
        "bound": "key-master",
        "reason": "Writes affect the current key master only; no per-master argument is exposed",
        "native_source": STRUCTURED_ROUTES[_field]["native_source"],
    }
