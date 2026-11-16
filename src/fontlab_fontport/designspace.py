# this_file: src/fontlab_fontport/designspace.py
"""Read-only B09 source/instance inspection through fontTools designspaceLib."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from fontTools.designspaceLib import DesignSpaceDocument, DiscreteAxisDescriptor

from .errors import UnsupportedCapability
from .info import _text
from .recipe import finite_number


@dataclass(frozen=True)
class Location:
    kind: str
    name: str
    coordinates: tuple[tuple[str, float], ...]
    available: bool = True
    reason: str | None = None


class Designspace:
    """Continuous-axis inspection; selection does not interpolate or mutate fonts.

    Coordinates exposed to controls are user coordinates. Upstream axis maps
    convert source design locations. Discrete axes, anisotropic locations and
    multi-axis mappings are explicitly unavailable in this bounded adapter.
    """

    def __init__(self, document: DesignSpaceDocument, *, native: bool = False) -> None:
        self._document = deepcopy(document)
        self.axes = tuple(deepcopy(document.axes))
        if document.axisMappings:
            raise UnsupportedCapability(
                "designspace.axisMappings", "Multi-axis mappings are unavailable"
            )
        names, tags = set(), set()
        for axis in self.axes:
            if isinstance(axis, DiscreteAxisDescriptor):
                raise UnsupportedCapability(
                    "designspace.discreteAxes",
                    "Discrete designspace axes are unavailable",
                )
            _text(axis.name, "axis name")
            _text(axis.tag, "axis tag")
            if (
                not axis.name
                or axis.name in names
                or axis.tag in tags
                or len(axis.tag) != 4
            ):
                raise ValueError("Axes require unique names and four-character tags")
            names.add(axis.name)
            tags.add(axis.tag)
            lo, default, hi = (
                finite_number(v) for v in (axis.minimum, axis.default, axis.maximum)
            )
            if not lo <= default <= hi:
                raise ValueError(f"Axis bounds are invalid: {axis.name}")
            self._check_map(axis)
        self.sources = tuple(
            self._source(source, native) for source in self._document.sources
        )
        self.instances = tuple(
            self._instance(instance) for instance in self._document.instances
        )

    @staticmethod
    def _check_map(axis) -> None:
        points = axis.map
        if not points:
            return
        for user, design in points:
            finite_number(user)
            finite_number(design)
        if any(a[0] >= b[0] or a[1] >= b[1] for a, b in pairwise(points)):
            raise ValueError("Axis maps must increase in user and design coordinates")

    @classmethod
    def open(cls, path: str | Path) -> "Designspace":
        return cls(DesignSpaceDocument.fromfile(path))

    @classmethod
    def from_native(cls, backend) -> "Designspace":
        """Snapshot registered package axes, master locations and instances.

        Native routing follows pyflaxis/pyflpackage/pyfllocation bindings. This
        does not switch the current master or retain native wrapper pointers.
        """
        package = backend._package()
        axes = tuple(package.axes)
        document = DesignSpaceDocument()
        for axis in axes:
            # Echopy flAxis exposes map as QMap<double,double>, bounds and
            # separate designMin/Def/Max; fgAxis exposes Point maps. The native
            # flAxis::setMap/design2user implementation confirms keys=design,
            # values=user. fontTools requires the opposite direction.
            mapping = sorted((user, design) for design, user in dict(axis.map).items())
            document.addAxisDescriptor(
                name=axis.name,
                tag=axis.tag,
                minimum=axis.minimal,
                default=axis.default,
                maximum=axis.maximum,
                map=mapping if len(mapping) > 1 else [],
            )

        def location(raw):
            values = {}
            for axis in axes:
                value = raw[axis.shortName]
                if value is not None:
                    values[axis.name] = value
            return values

        for master in package.masters:
            document.addSourceDescriptor(
                name=master, designLocation=location(package.location(master))
            )
        for instance in package.instances:
            document.addInstanceDescriptor(
                name=instance.name, designLocation=location(instance.location)
            )
        return cls(document, native=True)

    @property
    def document(self) -> DesignSpaceDocument:
        """A private copy of the document, safe to hand to a writer."""
        return deepcopy(self._document)

    def defaults(self) -> dict[str, float]:
        return {axis.name: axis.default for axis in self.axes}

    def location(self, values: Mapping[str, float]) -> dict[str, float]:
        if not isinstance(values, Mapping):
            raise TypeError("Location must be a mapping")
        result = self.defaults()
        unknown = set(values) - set(result)
        if unknown:
            raise ValueError(f"Unknown design axes: {sorted(unknown)}")
        result.update(values)
        for axis in self.axes:
            value = finite_number(result[axis.name])
            if not axis.minimum <= value <= axis.maximum:
                raise ValueError(f"Location outside {axis.name} bounds")
        return result

    def instance(self, values: Mapping[str, float], name: str = "Instance") -> Location:
        return Location("instance", name, tuple(self.location(values).items()))

    def _source(self, source, native: bool) -> Location:
        coordinates = self._document.map_backward(
            source.getFullDesignLocation(self._document)
        )
        available = (
            native
            or source.font is not None
            or (source.path is not None and Path(source.path).exists())
        )
        return Location(
            "source",
            source.name or "Unnamed source",
            tuple(self.location(coordinates).items()),
            bool(available),
            None if available else "Source file is unavailable",
        )

    def _instance(self, instance) -> Location:
        return self.instance(
            instance.getFullUserLocation(self._document),
            instance.name or "Unnamed instance",
        )
