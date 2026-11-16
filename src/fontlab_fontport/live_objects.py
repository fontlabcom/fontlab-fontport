# this_file: src/fontlab_fontport/live_objects.py
"""Fontshell subclasses that check owner lifetime even on cached child reads."""

from fontParts import fontshell

from .errors import StaleObjectError, UnsupportedCapability
from .lifetime import once_per_entry, public_access


class _Checked:
    def raiseNotImplementedError(self):
        import sys

        method = sys._getframe(1).f_code.co_name
        raise UnsupportedCapability(
            f"{type(self).__name__}.{method}",
            "No native primitive implements this FontParts operation",
        )

    def _native_identifiers(self):
        current = self
        seen = set()
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            state = object.__getattribute__(current, "__dict__")
            binding = state.get("_live_binding")
            if binding is not None:
                return getattr(
                    binding.layer._owner._backend, "requires_complete_contours", False
                )
            reference = state.get("_glyph") or state.get("_contour")
            current = reference() if callable(reference) else None
        return False

    def _getIdentifier(self):
        if self._native_identifiers():
            raise UnsupportedCapability(
                "identifiers", "Native UFO identifiers cannot be persisted"
            )
        return super()._getIdentifier()

    def _getIdentifierForPoint(self, point):
        if self._native_identifiers():
            raise UnsupportedCapability(
                "identifiers", "Native point identifiers cannot be persisted"
            )
        return super()._getIdentifierForPoint(point)

    def _setIdentifier(self, value):
        if self._native_identifiers():
            raise UnsupportedCapability(
                "identifiers", "Native UFO identifiers cannot be persisted"
            )
        return super()._setIdentifier(value)

    @once_per_entry
    def _check_live(self):
        state = object.__getattribute__(self, "__dict__")
        stage = state.get("_staged_image_resources")
        if stage is not None:
            if not stage["active"]:
                raise StaleObjectError("Staged glyph edit has ended")
            stage["owner"]._check_image_stage(stage)
        binding = state.get("_live_binding")
        if binding is not None:
            binding.layer._check()
            if not binding.valid:
                raise StaleObjectError("Stale glyph binding")
            backend = binding.layer._owner._backend
            if hasattr(backend, "check_glyph"):
                backend.check_glyph(binding.name, binding.layer._name)
            elif binding.name not in binding.layer._keys():
                raise StaleObjectError("Glyph has been removed")
        else:
            for key in ("_glyph", "_contour"):
                reference = state.get(key)
                if reference is not None:
                    parent = reference()
                    if parent is not None and isinstance(parent, _Checked):
                        parent._check_live()

    def __getattribute__(self, name):
        return public_access(
            self,
            name,
            super().__getattribute__,
            object.__getattribute__(self, "_check_live"),
        )

    def __setattr__(self, name, value):
        if not name.startswith("_"):
            self._check_live()
        super().__setattr__(name, value)


class RPoint(_Checked, fontshell.RPoint):
    pass


class RSegment(_Checked, fontshell.RSegment):
    pass


class RBPoint(_Checked, fontshell.RBPoint):
    pass


class RContour(_Checked, fontshell.RContour):
    pointClass = RPoint
    segmentClass = RSegment
    bPointClass = RBPoint


class RAnchor(_Checked, fontshell.RAnchor):
    pass


class RComponent(_Checked, fontshell.RComponent):
    pass


class RGuideline(_Checked, fontshell.RGuideline):
    pass


class RLib(_Checked, fontshell.RLib):
    pass


class RImage(_Checked, fontshell.RImage):
    """Keep image bytes on their checked detached backend, not defcon caches."""

    def _get_data(self) -> bytes | None:
        stage = self.__dict__.get("_staged_image_resources")
        if stage is not None:
            if not stage["resource_capable"]:
                raise UnsupportedCapability(
                    "glyph.image", "Image storage is unavailable"
                )
            return stage["data"]
        binding = self.__dict__.get("_live_binding")
        if binding is not None:
            return binding.read_image_data(self.naked().fileName)
        return super()._get_data()

    def _set_data(self, value: bytes) -> None:
        stage = self.__dict__.get("_staged_image_resources")
        if stage is not None:
            if not stage["resource_capable"]:
                raise UnsupportedCapability(
                    "glyph.image", "Image storage is unavailable"
                )
            from .memory import _validate_image_data

            _validate_image_data(value)
            stage["data"] = bytes(value)
            stage["data_assigned"] = True
            return
        binding = self.__dict__.get("_live_binding")
        if binding is not None:
            return binding.write_image_data(value)
        return super()._set_data(value)

    def _get_color(self) -> tuple | None:
        if self.__dict__.get("_staged_image_resources") is not None:
            color = self.naked().color
            return tuple(color) if color is not None else None
        return super()._get_color()

    def _set_color(self, value: tuple | None) -> None:
        if self.__dict__.get("_staged_image_resources") is not None:
            self.naked().color = value
            return
        super()._set_color(value)


class RGlyph(_Checked, fontshell.RGlyph):
    contourClass = RContour
    anchorClass = RAnchor
    componentClass = RComponent
    guidelineClass = RGuideline
    libClass = RLib
    imageClass = RImage

    def _get_image(self) -> RImage | None:
        image = super()._get_image()
        if image is not None:
            image._live_binding = self.__dict__.get("_live_binding")
            image._staged_image_resources = self.__dict__.get("_staged_image_resources")
        return image

    def _clearImage(self) -> None:
        stage = self.__dict__.get("_staged_image_resources")
        if stage is not None:
            self._check_live()
            stage["data"] = None
            stage["data_assigned"] = True
        super()._clearImage()

    def _addImage(self, data: bytes, transformation=None, color=None) -> RImage:
        image = self.image
        image.data = data
        image.transformation = transformation
        image.color = color
        return image

    def _get_lib(self):
        lib = super()._get_lib()
        lib._live_binding = self.__dict__.get("_live_binding")
        return lib

    def _get_tempLib(self):
        lib = super()._get_tempLib()
        lib._live_binding = self.__dict__.get("_live_binding")
        return lib

    def removeLayer(self, layer):
        if self.__dict__.get("_live_binding") is not None:
            raise UnsupportedCapability(
                "glyph.removeLayer.retainedHandle",
                "Use font.getLayer(name).removeGlyph(name); native handles become stale after removal rather than orphaned",
            )
        return super().removeLayer(layer)

    def _set_name(self, value):
        binding = self.__dict__.get("_live_binding")
        if binding is None:
            return super()._set_name(value)
        binding.layer._check()
        backend = binding.layer._owner._backend
        if not hasattr(backend, "rename_glyph"):
            raise UnsupportedCapability(
                "glyph.rename", "Backend has no safe rename route"
            )
        old = binding.name
        backend.rename_glyph(old, value, binding.layer.name)
        binding._restoring = True
        binding.name = value
        try:
            self.naked().name = value
        finally:
            binding._restoring = False
        binding.layer._bindings.pop(old)
        binding.layer._bindings[value] = binding
        binding.accepted = self.naked().getDataForSerialization()
