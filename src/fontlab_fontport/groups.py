# this_file: src/fontlab_fontport/groups.py
"""Real FontParts groups and detached, whole-map UFO validation."""

import re
from collections.abc import ItemsView, Iterator, Mapping
from typing import Any

from fontParts.base import BaseGroups

from .lifetime import OwnedAccess

PREFIXES = ("public.kern1.", "public.kern2.")


_CONTROL = re.compile("[\x00-\x1f]")


def _text(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("Group and member names must be text")
    # Kerning reads check every pair side, so this runs ~28000 times per read
    # on a large font; a regex search is about ten times faster than any(ord()).
    if not value or _CONTROL.search(value):
        raise ValueError("Group and member names must be nonempty without controls")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError("Group and member names must be valid Unicode") from exc
    return value


def stage_groups(values: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """Detach a complete mapping; enforce UFO per-side kerning membership rules.

    Plain groups retain duplicate and absent glyph names, as FontParts permits.
    An editor can require known glyphs before calling this model boundary.
    """
    if not isinstance(values, Mapping):
        raise TypeError("Groups must be a mapping")
    result, seen = {}, ({}, {})
    for name, members in values.items():
        name = _text(name)
        if not isinstance(members, (list, tuple)):
            raise TypeError(f"Group {name!r} members must be a list or tuple")
        result[name] = tuple(_text(member) for member in members)
        for side, prefix in enumerate(PREFIXES):
            if not name.startswith(prefix):
                continue
            if name == prefix:
                raise ValueError("A kerning group needs a name after its prefix")
            for member in result[name]:
                if member in seen[side]:
                    reason = (
                        "duplicate" if seen[side][member] == name else "more than one"
                    )
                    raise ValueError(
                        f"{member!r}: {reason} kerning group membership on side {side + 1}"
                    )
                seen[side][member] = name
    return result


def edit_groups(
    groups: Mapping[str, Any],
    action: str,
    name: str,
    *,
    new_name: str = "",
    members: list[str] | tuple[str, ...] = (),
    available_glyphs: Any = (),
) -> dict[str, tuple[str, ...]]:
    """Stage one B06 action; member insertion deduplicates and requires glyphs.

    No native mutation occurs. Destructive dependent-pair policy is checked by
    the backend when this complete mapping is applied. Deleting a conflicting
    imported group can repair an existing per-side membership overlap.
    """
    values = dict(groups)
    _text(name)
    if action == "add":
        if name in values:
            raise ValueError(f"Group already exists: {name}")
        values[name] = ()
    else:
        if name not in values:
            raise KeyError(name)
        match action:
            case "rename":
                _text(new_name)
                if new_name != name:
                    if new_name in values:
                        raise ValueError(f"Group already exists: {new_name}")
                    values[new_name] = values.pop(name)
            case "delete":
                del values[name]
            case "add_members" | "remove_members":
                selected = stage_groups({"members": members})["members"]
                available = (
                    set(available_glyphs)
                    if action == "add_members"
                    else set(values[name])
                )
                missing = set(selected) - available
                if missing:
                    raise ValueError(f"Unknown group members: {sorted(missing)}")
                values[name] = (
                    tuple(dict.fromkeys((*values[name], *selected)))
                    if action == "add_members"
                    else tuple(
                        member for member in values[name] if member not in selected
                    )
                )
            case _:
                raise ValueError(f"Unknown group operation: {action}")
    return stage_groups(values)


class RGroups(OwnedAccess, BaseGroups):
    """Read fresh native values; dispatch each edit as one validated mapping."""

    def _init(self, owner: Any) -> None:
        self._owner = owner
        self.font = owner

    def _snapshot(self) -> dict[str, tuple[str, ...]]:
        self._owner._check()
        return self._owner._backend.get_groups()

    def _getItem(self, key: str) -> tuple[str, ...]:
        return self._snapshot()[key]

    def _items(self) -> ItemsView[str, tuple[str, ...]]:
        return self._snapshot().items()

    def _iter(self) -> Iterator[str]:
        return iter(self._snapshot())

    def _len(self) -> int:
        return len(self._snapshot())

    def _contains(self, key: str) -> bool:
        return key in self._snapshot()

    def _setItem(self, key: str, value: tuple[str, ...]) -> None:
        values = self._snapshot()
        values[key] = value
        self.apply(values)

    def _delItem(self, key: str) -> None:
        values = self._snapshot()
        del values[key]
        self.apply(values)

    def _update(self, other: Mapping[str, tuple[str, ...]]) -> None:
        values = self._snapshot()
        values.update(other)
        self.apply(values)

    def _clear(self) -> None:
        self.apply({})

    def apply(
        self,
        values: Mapping[str, Any],
        *,
        undo_name: str = "FontParts groups",
        require_persistence: bool | None = None,
    ) -> None:
        """Replace the complete mapping after validation, in one native batch."""
        current = self._snapshot()
        if not _text(undo_name).strip():
            raise ValueError("Undo name must not be blank")
        staged = stage_groups(values)
        if staged != current:
            if require_persistence is not None:
                self._owner._backend.set_groups(
                    staged, undo_name=undo_name, require_persistence=require_persistence
                )
            else:
                self._owner._backend.set_groups(staged, undo_name=undo_name)

    def rename(self, name: str, new_name: str) -> None:
        """Rename once; a native backend may refuse dependent kerning references."""
        values = self._snapshot()
        _text(new_name)
        if name not in values:
            raise KeyError(name)
        if name == new_name:
            return
        if new_name in values:
            raise ValueError(f"Group already exists: {new_name}")
        values = {
            new_name if key == name else key: value for key, value in values.items()
        }
        self.apply(values, undo_name="FontParts rename group")
