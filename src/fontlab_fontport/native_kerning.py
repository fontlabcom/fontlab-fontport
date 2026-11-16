# this_file: src/fontlab_fontport/native_kerning.py
"""Explicit key-master native pairs with a measured history precision boundary."""

from collections.abc import Mapping
from typing import Any

from .errors import UnsupportedCapability
from .groups import PREFIXES, _text
from .kerning import Pair, stage_kerning
from .native_groups import read_groups


def _read(package: Any, master: str | None = None) -> tuple[dict, dict]:
    _, routes = read_groups(package)
    names = {
        (side, native): name
        for name, (kind, native) in routes.items()
        for side, prefix in enumerate(PREFIXES)
        if kind == "kerning" and name.startswith(prefix)
    }
    values, keys = {}, {}
    pairs = package.kerning() if master is None else package.kerning(master)
    for native, value in pairs.items():
        pair = []
        key = []
        for side, obj in enumerate((native.left, native.right)):
            if obj.mode == "glyphMode":
                name = obj.id
            elif obj.mode == "groupMode":
                if (side, obj.id) not in names:
                    raise UnsupportedCapability(
                        "kerning.nativeMapping",
                        f"Unmapped native kerning group: {obj.id}",
                    )
                name = names[side, obj.id]
            else:
                raise UnsupportedCapability(
                    "kerning.nativeMapping",
                    f"Unsupported native kerning mode: {obj.mode}",
                )
            pair.append(name)
            key.append((obj.id, obj.mode))
        pair = tuple(pair)
        values[pair], keys[pair] = value, tuple(key)
    return stage_kerning(values), keys


def read_kerning(package: Any, master: str | None = None) -> dict[Pair, int | float]:
    """Read explicit presence from items(), preserving zero and fractions.

    ``master`` selects ``flPackage.kerning(master)``; None is the current master.
    """
    return _read(package, master)[0]


def target_master(package: Any) -> str | None:
    """Name font-level kerning's master: the default master, never the UI's current one."""
    name = getattr(package, "defaultMaster", None)
    return name if isinstance(name, str) else None


def _refuse_fraction(master: Any, pair: Pair, value: float) -> None:
    where = f" on {master}" if isinstance(master, str) else ""
    raise UnsupportedCapability(
        "kerning.fractionalHistory",
        f"Kerning{where}: {pair[0]} {pair[1]} = {value:g} is not a whole "
        "number; native kerning history rounds fractional values. "
        "Round that pair first; no changes applied.",
    )


def _check_other_masters(package: Any, target: str | None) -> None:
    """Native history rounds every master's fractions, so refuse any of them."""
    for name in getattr(package, "masters", ()):
        if name == target:
            continue
        try:
            values = _read(package, name)[0]
        except (TypeError, ValueError) as error:
            raise UnsupportedCapability(
                "kerning.fractionalHistory",
                f"Kerning on {name}: {error}; no changes applied.",
            ) from error
        for pair, value in values.items():
            if value != int(value):
                _refuse_fraction(name, pair, value)


def _native_pair(package: Any, pair: Pair, routes: dict) -> tuple:
    key = []
    for side, name in enumerate(pair):
        if name.startswith(PREFIXES[side]):
            if name not in routes:
                raise UnsupportedCapability(
                    "kerning.danglingNames", f"Kerning group does not exist: {name}"
                )
            key.append((routes[name][1], "groupMode"))
        else:
            glyph = package.findName(name)
            if glyph is None or glyph.isNull:
                raise UnsupportedCapability(
                    "kerning.danglingNames", f"Kerning glyph does not exist: {name}"
                )
            key.append((name, "glyphMode"))
    if any(not all(33 <= ord(char) <= 126 for char in name) for name, _ in key):
        raise UnsupportedCapability(
            "kerning.nativeMapping",
            "Native kerning names require printable ASCII without spaces",
        )
    return tuple(key)


def write_kerning(package: Any, values: Mapping, undo_name: str) -> None:
    """Replace explicit pairs after complete preflight, with first Undo/Redo.

    Native setters and history round fractions, so edits requiring fractional
    history are refused before mutation. Zero entries are seeded nonzero then
    scaled to zero; all nonzero pairs are restored inside the same checkpoint.
    The before/after history protocol adds an extra no-op history row.
    """
    if not _text(undo_name).strip():
        raise ValueError("Undo name must not be blank")
    staged = stage_kerning(values)
    target = target_master(package)
    current, existing = _read(package, target)
    _, routes = read_groups(package)
    desired = {pair: _native_pair(package, pair, routes) for pair in staged}
    _check_other_masters(package, target)
    if staged == current:
        return
    master = target or getattr(package, "master", None)
    for pair, value in (*current.items(), *staged.items()):
        if value != int(value):
            _refuse_fraction(master, pair, value)
        if not -(2**31) <= value <= 2**31 - 1:
            raise UnsupportedCapability(
                "kerning.nativeMapping",
                "Native kerning history needs signed 32-bit values",
            )
    import fontlab

    native = package.kerning() if target is None else package.kerning(target)
    package.checkInitHistoryState(0)
    history = [package, package.mastersContainer(), package.kerningContainer()]
    fontlab.flItems.notifyChangesApplied(undo_name, history)
    for pair in current.keys() - staged.keys():
        native.remove(existing[pair])
    new_zeros = [
        pair for pair, value in staged.items() if value == 0 and current.get(pair) != 0
    ]
    for pair in new_zeros:
        native.set(desired[pair], 1)
    if new_zeros:
        native.scale(0.0)
    for pair, value in staged.items():
        if value != 0 and (new_zeros or pair not in current or current[pair] != value):
            native.set(desired[pair], value)
    native.scale(1.0)
    fontlab.flItems.notifyChangesApplied(undo_name, history)
    if read_kerning(package, target) != staged:
        raise RuntimeError("Native kerning readback differs from the applied pairs")
