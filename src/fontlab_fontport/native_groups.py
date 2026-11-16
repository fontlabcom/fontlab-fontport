# this_file: src/fontlab_fontport/native_groups.py
"""Separate native feature groups and key-master kerning classes safely."""

from collections.abc import Mapping
from typing import Any

from .errors import UnsupportedCapability
from .groups import PREFIXES, _text, stage_groups

MODES = {"KernLeft": (0,), "KernRight": (1,), "KernBothSide": (0, 1)}


def check_persistence(package: Any) -> None:
    """Refuse known legacy font-global class modes that VFJ drops on save."""
    legacy = [
        name
        for name, group in package.fgPackage.groups.items()
        if not group.isFeaGroup()
    ]
    if legacy:
        raise UnsupportedCapability(
            "groups.legacyFlagsVfj",
            f"Legacy native group flags have no lossless VFJ route: {legacy!r}; no write/history changed",
        )


def read_groups(package: Any) -> tuple[dict, dict]:
    """Return fresh UFO values and their concrete native storage routes."""
    values, routes = {}, {}
    for name, group in package.fgPackage.groups.items():
        if group.isFeaGroup():
            if name.startswith(PREFIXES):
                raise UnsupportedCapability(
                    "groups.nativeMapping",
                    f"Feature class uses a reserved kerning name: {name}",
                )
            values[name], routes[name] = tuple(group), ("feature", name)
    for name, (members, mode) in package.kerning().groups.items():
        if mode not in MODES:
            raise UnsupportedCapability(
                "groups.nativeMapping",
                f"Native kerning class mode unsupported: {name}: {mode}",
            )
        for side in MODES[mode]:
            prefix = PREFIXES[side]
            key = name if name.startswith(prefix) else prefix + name
            if key in values:
                raise UnsupportedCapability(
                    "groups.nativeMapping", f"Ambiguous native group mapping: {key}"
                )
            values[key], routes[key] = tuple(members), ("kerning", name)
    return values, routes


def _plan(package: Any, staged: dict, current: dict, routes: dict) -> dict:
    kerning = {}
    for name, members in staged.items():
        side = next(
            (i for i, prefix in enumerate(PREFIXES) if name.startswith(prefix)), None
        )
        if side is None:
            if (
                package.fgPackage.groups.has_key(name)
                and not package.fgPackage.groups[name].isFeaGroup()
            ):
                raise UnsupportedCapability(
                    "groups.nativeMapping",
                    f"Native group is not an editable feature class: {name}",
                )
            continue
        for member in members:
            glyph = package.findName(member)
            if glyph is None or glyph.isNull:
                raise UnsupportedCapability(
                    "kerning.danglingNames",
                    f"Kerning group member does not exist: {member}",
                )
        native = routes[name][1] if name in routes else name
        if native in kerning and kerning[native][0] != members:
            raise UnsupportedCapability(
                "groups.divergentBothSides",
                f"Native both-sided class needs identical members: {native}",
            )
        flags = kerning.get(native, (members, set()))[1]
        flags.add(side)
        kerning[native] = members, flags
    removed = {
        routes[name][1]
        for name in current.keys() - staged.keys()
        if routes[name][0] == "kerning"
    }
    references = {
        obj.id
        for pair in package.kerning().keys()  # noqa: SIM118 - native fgKerning is not a dict
        for obj in (pair.left, pair.right)
        if obj.mode == "groupMode"
    }
    dependent = removed & references
    if dependent:
        raise UnsupportedCapability(
            "groups.dependentKerning",
            f"Remove dependent kerning pairs before renaming/deleting groups: {sorted(dependent)}",
        )
    return {
        name: (
            members,
            next(mode for mode, sides in MODES.items() if set(sides) == flags),
        )
        for name, (members, flags) in kerning.items()
    }


def write_groups(
    package: Any, values: Mapping, undo_name: str, *, require_persistence: bool = False
) -> None:
    """Validate a complete replacement, then capture native first Undo/Redo.

    Dependent-pair rename/delete is refused before mutation. Current-key-master
    classes are edited; other masters and opaque native groups stay untouched.
    The native before/after protocol adds an extra no-op history checkpoint.
    """
    if not _text(undo_name).strip():
        raise ValueError("Undo name must not be blank")
    try:
        staged = stage_groups(values)
    except ValueError as error:
        if "kerning group membership on side" not in str(error):
            raise
        raise UnsupportedCapability(
            "groups.multiMembership",
            f"Native classes exceed UFO per-side membership: {error}; no write/history changed",
        ) from error
    current, routes = read_groups(package)
    desired = _plan(package, staged, current, routes)
    if staged == current:
        return
    if any(not name.isascii() for name in staged):
        raise UnsupportedCapability(
            "groups.unicodeNames",
            "FontLab cannot store this group name losslessly through VFJ; no write/history changed",
        )
    if require_persistence:
        check_persistence(package)
    import fontgate
    import fontlab
    import fontpr

    plain = package.fgPackage.groups
    feature_values = dict(plain.asDict())
    for name in current:
        if routes[name][0] == "feature" and name not in staged:
            del feature_values[name]
    for name, members in staged.items():
        if not name.startswith(PREFIXES) and current.get(name) != members:
            feature_values[name] = fontgate.fgGroup(
                name, list(members), "FeaClassGroupMode", members[0] if members else ""
            )
            if feature_values[name].name != name:
                raise UnsupportedCapability(
                    "groups.nativeMapping",
                    f"FontLab cannot store this group name: {name!r}",
                )
    native = package.kerning()
    existing = dict(native.groups.asDict())
    feature_changed = {
        k: v for k, v in current.items() if not k.startswith(PREFIXES)
    } != {k: v for k, v in staged.items() if not k.startswith(PREFIXES)}
    if feature_changed:
        # fromDict's native key parser rejects these names even when they
        # already exist in an imported font. Refuse before replacing its data.
        for name in feature_values:
            if fontgate.fgGroup(name, [], "FeaClassGroupMode", "").name != name:
                raise UnsupportedCapability(
                    "groups.nativeMapping",
                    f"Cannot safely replace native feature groups containing: {name!r}",
                )
    for name in desired.keys() - existing.keys():
        if fontgate.fgGroup(name, [], "FeaClassGroupMode", "").name != name:
            raise UnsupportedCapability(
                "groups.nativeMapping",
                f"FontLab cannot store this class name: {name!r}",
            )
    package.checkInitHistoryState(0)
    history = [package, package.mastersContainer(), package.kerningContainer()]
    fontlab.flItems.notifyChangesApplied(undo_name, history)
    if feature_changed:
        plain.fromDict(feature_values)
    for name in existing.keys() - desired.keys():
        native.deleteGroup(name, deleteDependentKerningPairs=False)
    for name, (members, mode) in desired.items():
        if name not in existing:
            if not native.addGroup(name, list(members), kernMode=mode):
                raise RuntimeError(f"Native class creation failed: {name}")
        elif (tuple(existing[name][0]), existing[name][1]) != (members, mode):
            sides = MODES[mode]
            fontpr.call(
                "set_kerning_class",
                font_id=package.fgId,
                class_name=name,
                glyph_names=list(members),
                left=0 in sides,
                right=1 in sides,
                undo=False,
            )
    fontlab.flItems.notifyChangesApplied(undo_name, history)
    if read_groups(package)[0] != staged:
        raise RuntimeError("Native groups readback differs from the applied mapping")
