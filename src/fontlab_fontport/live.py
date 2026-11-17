# this_file: src/fontlab_fontport/live.py
"""Real FontParts objects with synchronous defcon change notifications."""

from collections.abc import Mapping
from contextlib import contextmanager, nullcontext
from copy import deepcopy
from typing import Any

from defcon import Component, Font, Layer
from fontParts.base import BaseFont, BaseInfo, BaseLayer

from .backend import FontBackend
from .errors import StaleObjectError, UnsupportedCapability
from .fontdata import RFeatures, RLib
from .groups import RGroups
from .kerning import RKerning
from .lifetime import AdapterIdentity, OwnedAccess, once_per_entry, public_access
from .live_objects import RGlyph


class _Unsupported:
    def raiseNotImplementedError(self):
        import sys

        method = sys._getframe(1).f_code.co_name
        raise UnsupportedCapability(
            f"{type(self).__name__}.{method}",
            "Fontport has no native primitive for this operation",
        )


class _Component(Component):
    """Reject cycles before defcon installs recursive base-glyph observers."""

    # defcon 0.12 observes base edits but its bounds factories omit this event
    # from their destructive notifications. Extend the upstream cache contract.
    representationFactories = deepcopy(Component.representationFactories)
    for _factory in representationFactories.values():
        _factory["destructiveNotifications"] += ("Component.BaseGlyphDataChanged",)

    def _beginLayerObservations(self):
        super()._beginLayerObservations()
        self.layer.addObserver(self, "layerGlyphDeleted", "Layer.GlyphDeleted")

    def _endLayerObservations(self):
        super()._endLayerObservations()
        self.layer.removeObserver(self, "Layer.GlyphDeleted")

    def layerGlyphDeleted(self, notification):
        if notification.data["name"] == self.baseGlyph:
            self.postNotification("Component.BaseGlyphDataChanged")

    def layerGlyphAddedNotificationCallback(self, notification):
        super().layerGlyphAddedNotificationCallback(notification)
        if notification.data["name"] == self.baseGlyph:
            self.postNotification("Component.BaseGlyphDataChanged")

    def _set_baseGlyph(self, value):
        if (
            self.glyph is not None
            and value is not None
            and not getattr(self.glyph, "_live_restoring", False)
        ):
            layer = self.layer._live_layer
            if (
                getattr(layer._owner._backend, "requires_complete_contours", False)
                and value not in layer._keys()
            ):
                raise UnsupportedCapability(
                    "components.unresolvedBase",
                    f"Component base missing in layer: {value}",
                )
            layer._load_dependencies(value, (self.glyph.name,))
        super()._set_baseGlyph(value)

    baseGlyph = property(Component._get_baseGlyph, _set_baseGlyph)


class _ModelLayer(Layer):
    def endSelfGlyphNotificationObservation(self, glyph):
        # Removed public handles must still dispatch to their invalid binding.
        # End layer/base observations, retaining child mutation notifications.
        for notification in (
            "Glyph.Changed",
            "Glyph.NameChanged",
            "Glyph.UnicodesChanged",
        ):
            glyph.removeObserver(self, notification)
        for component in glyph.components:
            component.endSelfBaseGlyphNotificationObservation()


class _ModelFont(Font):
    def endSelfLayersNotificationObservation(self):
        # Cyclic GC can finalize defcon's LayerSet before its Font. Its native
        # endSelfNotificationObservation clears _layers; there are then no
        # child observers left to disconnect. Do not iterate that torn-down set.
        if self._layers is not None and self._layers._layers is not None:
            super().endSelfLayersNotificationObservation()


class _Binding:
    def __init__(self, layer, name, source):
        self.layer = layer
        self.name = name
        self.valid = True
        self._restoring = False
        self.pending_geometry = False
        # All siblings share defcon's component resolver and dispatcher. Retain
        # its font strongly even when the public layer invalidates this handle.
        self.owner = layer._model_owner
        self.model = self.owner.newGlyph(name)
        source.drawPoints(self.model.getPointPen())
        for attr in ("width", "height", "unicodes", "note", "lib"):
            setattr(self.model, attr, deepcopy(getattr(source, attr)))
        self.model.anchors = [dict(x) for x in source.anchors]
        self.model.guidelines = [dict(x) for x in source.guidelines]
        self.model.image = deepcopy(dict(source.image))
        self.accepted = deepcopy(self.model.getDataForSerialization())
        self.glyph = RGlyph(self.model)
        self.glyph._live_binding = self
        self.glyph.layer = layer
        self.model.addObserver(self, "changed", "Glyph.Changed")

    def changed(self, notification):
        if self._restoring:
            return
        try:
            self.layer._check()
            backend = self.layer._owner._backend
            if not self.valid or self.model.name != self.name:
                raise RuntimeError("Stale glyph binding or unsupported glyph rename")
            if hasattr(backend, "check_glyph"):
                backend.check_glyph(self.name, self.layer._name)
            elif self.name not in self.layer._keys():
                raise StaleObjectError("Stale glyph binding")
            if self.model.getDataForSerialization() == self.accepted:
                # Base-outline invalidation also emits Glyph.Changed. Bounds
                # caches need it; the native dependent glyph needs no write.
                return
            from .pens import edit_geometry_ready

            if getattr(
                backend, "requires_complete_contours", False
            ) and not edit_geometry_ready(self.model):
                self.pending_geometry = True
                self.accepted = deepcopy(self.model.getDataForSerialization())
                return
            self.layer._owner._backend.write_glyph(
                self.name, self.layer.name, self.model
            )
        except Exception as error:
            try:
                self._restore_accepted(self.accepted)
            except Exception as cleanup:
                error.add_note(f"Glyph rollback failed: {cleanup!r}")
                raise error from cleanup
            raise
        self.pending_geometry = False
        self.accepted = deepcopy(self.model.getDataForSerialization())
        self.layer._owner._sync_globals(self)

    def _restore_accepted(self, state: dict) -> None:
        renamed = self.model.name
        self._restoring = True
        self.model._live_restoring = True
        try:
            self.model.disableNotifications()
            try:
                self.model.setDataFromSerialization(deepcopy(state))
            finally:
                self.model.enableNotifications()
            if renamed != self.name:
                self.model.postNotification(
                    "Glyph.NameChanged",
                    data={"oldValue": renamed, "newValue": self.name},
                )
            # Rollback rebuilds children. Invalidate dependent representations.
            self.model.postNotification("Glyph.ContoursChanged")
            self.model.postNotification("Glyph.ComponentsChanged")
        finally:
            self.model._live_restoring = False
            self._restoring = False

    def read_image_data(self, file_name: str | None) -> bytes | None:
        self.glyph._check_live()
        read = getattr(self.layer._owner._backend, "read_image", None)
        if not callable(read):
            raise UnsupportedCapability("glyph.image", "Image storage is unavailable")
        return read(file_name)

    def write_image_data(self, data: bytes) -> None:
        self.glyph._check_live()
        edit = getattr(self.layer._owner._backend, "edit_image", None)
        if not callable(edit):
            raise UnsupportedCapability("glyph.image", "Image storage is unavailable")
        accepted = deepcopy(self.accepted)
        try:
            with edit(self.name, self.layer.name, data) as file_name:
                self.model.image.fileName = file_name
        except BaseException as error:
            self.accepted = accepted
            try:
                if self.model.getDataForSerialization() != accepted:
                    self._restore_accepted(accepted)
            except BaseException as cleanup:
                error.add_note(f"Image model rollback failed: {cleanup!r}")
                raise error from cleanup
            raise


class RInfo(OwnedAccess, _Unsupported, BaseInfo):
    """FontParts info properties delegated to the native boundary."""

    def _init(self, owner):
        self._owner = owner
        self.font = owner

    def _getAttr(self, attr):
        self._owner._check()
        return self._owner._backend.get_info(attr)

    def _setAttr(self, attr, value):
        self._owner._check()
        self._owner._backend.set_info(attr, value)

    def apply(
        self,
        values: Mapping[str, Any],
        *,
        undo_name: str = "FontParts font info",
        require_single_undo: bool | None = None,
    ) -> None:
        """Apply a staged mapping as one validated native info operation."""
        self._owner._check()
        if require_single_undo is not None:
            return self._owner._backend.set_info_many(
                values, undo_name=undo_name, require_single_undo=require_single_undo
            )
        self._owner._backend.set_info_many(values, undo_name=undo_name)


class RLayer(OwnedAccess, _Unsupported, BaseLayer):
    """Named layer retaining the owner required by weak FontParts parents."""

    def _init(self, owner, name):
        self._owner = owner
        self._name = name
        self._valid = True
        self._bindings = {}
        self._model_owner = _ModelFont(
            layerClass=_ModelLayer, glyphComponentClass=_Component
        )
        self._model_owner.layers.defaultLayer._live_layer = self
        self.font = owner

    @once_per_entry
    def _check(self):
        self._owner._check()
        backend = self._owner._backend
        exists = (
            backend.has_layer(self._name)
            if hasattr(backend, "has_layer")
            else self._name in backend.layer_names()
        )
        if not self._valid or not exists:
            raise StaleObjectError("Stale layer binding")

    def _get_name(self):
        self._check()
        return self._name

    def _set_name(self, value):
        self._check()
        backend = self._owner._backend
        if not hasattr(backend, "rename_layer"):
            raise UnsupportedCapability("layer.rename", "No safe native rename route")
        backend.rename_layer(self._name, value)
        self._owner._layers.pop(self._name, None)
        self._owner._layers[value] = self
        self._name = value

    def _keys(self):
        self._check()
        return self._owner._backend.glyph_names(self._name)

    def _contains(self, name):
        # One native lookup instead of listing every glyph in the font: on a
        # 3000-glyph font each `name in layer` and `layer[name]` cost ~60 ms.
        self._check()
        has_glyph = getattr(self._owner._backend, "has_glyph", None)
        if callable(has_glyph):
            return has_glyph(name, self._name)
        return name in self._keys()

    def _getItem(self, name):
        self._check()
        if name not in self._bindings:
            self._load_dependencies(name)
        return self._bindings[name].glyph

    def _dependency_sources(self, name, ancestors, sources):
        if name in ancestors:
            raise UnsupportedCapability(
                "components.unresolvedBase",
                f"Cyclic component dependency: {' -> '.join((*ancestors, name))}",
            )
        if name in sources or not self._contains(name):
            return
        binding = self._bindings.get(name)
        source = (
            binding.model
            if binding
            else self._owner._backend.read_glyph(name, self.name)
        )
        for component in source.components:
            self._dependency_sources(component.baseGlyph, (*ancestors, name), sources)
        sources[name] = source

    def _load_dependencies(self, name, ancestors=()):
        sources = {}
        self._dependency_sources(name, ancestors, sources)
        # Postorder ensures bases exist before defcon attaches observers. Only
        # this transitive dependency graph is loaded, never the complete font.
        for key, source in sources.items():
            if key not in self._bindings:
                self._bindings[key] = _Binding(self, key, source)

    def _newGlyph(self, name):
        self._check()
        self._owner._backend.new_glyph(name, self._name)
        return self._getItem(name)

    def _removeGlyph(self, name):
        self._check()
        self._owner._backend.remove_glyph(name, self._name)
        binding = self._bindings.pop(name, None)
        if binding is not None:
            binding.valid = False
            del self._model_owner[binding.name]

    def _get_defaultLayer(self):
        return self._owner.defaultLayer

    def copy(self):
        self._check()
        raise UnsupportedCapability(
            "layer.copy",
            "Use explicit detached UFO staging; orphan native layers have no owner",
        )


class RFont(AdapterIdentity, _Unsupported, BaseFont):
    """A FontParts font whose supported mutations synchronously reach backend."""

    def _init(self, pathOrObject: FontBackend, showInterface=True):
        self._backend = pathOrObject
        self._closed = False
        self._layers = {}
        self._info = RInfo(self)
        self._groups = RGroups(self)
        self._kerning = RKerning(self)
        self._features = RFeatures(self)
        self._lib = RLib(self)

    @once_per_entry
    def _check(self):
        if self._closed:
            raise StaleObjectError("Font is closed")
        if hasattr(self._backend, "check_open"):
            self._backend.check_open()

    def __getattribute__(self, name):
        getter = super().__getattribute__
        if name in (
            "invalidate",
            "capabilities",
        ) or "_closed" not in object.__getattribute__(self, "__dict__"):
            return getter(name)
        return public_access(
            self, name, getter, object.__getattribute__(self, "_check")
        )

    def copy(self):
        self._check()
        raise UnsupportedCapability(
            "font.copy",
            "Use explicit UFO export/import; implicit native document creation is refused",
        )

    def _interpolate(self, *args, **kwargs):
        raise UnsupportedCapability(
            "font.interpolate",
            "Native master replacement must not delete layers before interpolation preflight",
        )

    def _newLayer(self, name, color=None):
        self._check()
        if not hasattr(self._backend, "new_layer"):
            raise UnsupportedCapability(
                "layer.create", "No safe native master creation route"
            )
        self._backend.new_layer(name, color=color)
        return self.getLayer(name)

    def _removeLayer(self, name):
        self._check()
        if not hasattr(self._backend, "remove_layer"):
            raise UnsupportedCapability(
                "layer.delete", "No safe native master deletion route"
            )
        self._backend.remove_layer(name)
        layer = self._layers.pop(name, None)
        if layer is not None:
            layer._valid = False

    @contextmanager
    def edit_glyph(self, name, *, layer=None, undo_name="FontParts glyph edit"):
        """Stage a complete pen operation, then issue exactly one backend write.

        Native history semantics still depend on the backend. A successful
        commit invalidates loaded handles; fetch the glyph again afterwards.
        """
        self._check()
        self._check_pending()
        from defcon import Glyph

        layer = layer or self.defaultLayerName
        original = deepcopy(self._backend.read_glyph(name, layer))
        model = Glyph()
        original.drawPoints(model.getPointPen())
        for field in ("name", "width", "height", "unicodes", "note", "lib"):
            setattr(model, field, deepcopy(getattr(original, field)))
        model.anchors = [dict(a) for a in original.anchors]
        model.guidelines = [dict(g) for g in original.guidelines]
        model.image = deepcopy(dict(original.image))
        staged = RGlyph(model)
        resource_capable = callable(
            getattr(self._backend, "read_image", None)
        ) and callable(getattr(self._backend, "edit_image", None))
        data = (
            self._backend.read_image(original.image.fileName)
            if resource_capable
            else None
        )
        data = bytes(data) if data is not None else None
        stage = {
            "owner": self,
            "cache": self._layers,
            "name": name,
            "layer": layer,
            "active": True,
            "source": original,
            "initial_model": deepcopy(model.getDataForSerialization()),
            "resource_capable": resource_capable,
            "source_data": data,
            "data": data,
            "data_assigned": False,
        }
        staged._staged_image_resources = stage
        try:
            yield staged
            self._commit_image_stage(stage, staged, undo_name)
        finally:
            stage["active"] = False
            for key in (
                "owner",
                "cache",
                "source",
                "initial_model",
                "source_data",
                "data",
            ):
                stage[key] = None

    def _check_image_stage(self, stage: dict, *, check_source: bool = False) -> None:
        if not stage["active"]:
            raise StaleObjectError("Staged glyph edit has ended")
        self._check()
        if stage["owner"] is not self or self._layers is not stage["cache"]:
            raise StaleObjectError("Staged glyph owner has been invalidated")
        backend = self._backend
        name, layer = stage["name"], stage["layer"]
        if layer not in backend.layer_names() or name not in backend.glyph_names(layer):
            raise StaleObjectError("Staged glyph or layer has been removed")
        if check_source and stage["resource_capable"]:
            if not callable(getattr(backend, "read_image", None)) or not callable(
                getattr(backend, "edit_image", None)
            ):
                raise UnsupportedCapability(
                    "glyph.image", "Image storage is unavailable"
                )
            if (
                backend.read_glyph(name, layer) != stage["source"]
                or backend.read_image(stage["source"].image.fileName)
                != stage["source_data"]
            ):
                raise StaleObjectError("Staged glyph source changed during editing")

    def _commit_image_stage(self, stage: dict, staged: RGlyph, undo_name: str) -> None:
        self._check_image_stage(stage, check_source=True)
        model = staged.naked()
        if (
            model.getDataForSerialization() == stage["initial_model"]
            and stage["data"] == stage["source_data"]
        ):
            self.refresh()
            return
        name, layer = stage["name"], stage["layer"]
        assign_data = stage["data_assigned"] and stage["data"] is not None
        transaction = nullcontext()
        if stage["resource_capable"]:
            transaction = (
                self._backend.edit_image(name, layer, stage["data"])
                if assign_data
                else self._backend.edit_image(name, layer)
            )
        with transaction as file_name:
            if assign_data:
                model.image.fileName = file_name
            if hasattr(self._backend, "write_glyph_named"):
                self._backend.write_glyph_named(
                    name, layer, staged, undo_name=undo_name
                )
            else:
                self._backend.write_glyph(name, layer, staged)
            self.refresh()

    def _sync_globals(self, source):
        fields = getattr(self._backend, "glyph_global_fields", ())
        for layer in self._layers.values():
            target = layer._bindings.get(source.name)
            if target is None or target is source:
                continue
            target.model.disableNotifications()
            try:
                for field in fields:
                    setattr(target.model, field, deepcopy(getattr(source.model, field)))
                    target.accepted[field] = deepcopy(source.accepted[field])
            finally:
                target.model.enableNotifications()

    def _get_layers(self):
        self._check()
        result = []
        for name in self._backend.layer_names():
            if name not in self._layers:
                self._layers[name] = RLayer(self, name)
            result.append(self._layers[name])
        return tuple(result)

    def _get_defaultLayerName(self):
        self._check()
        return self._backend.default_layer()

    def _get_defaultLayer(self):
        # FontParts validates the name against layerOrder and then scans every
        # layer, and both list layers across the whole font. Every `font[name]`
        # goes through here, so resolve the default layer by name directly.
        self._check()
        name = self._backend.default_layer()
        if name not in self._layers:
            self._layers[name] = RLayer(self, name)
        return self._layers[name]

    def _get_layerOrder(self):
        self._check()
        return self._backend.layer_names()

    def _keys(self):
        return self.defaultLayer.keys()

    def _contains(self, name):
        return self.defaultLayer._contains(name)

    def _get_glyphOrder(self):
        """Expose the order supplied by the native default layer."""
        return tuple(self._keys())

    def _get_base_info(self):
        return self._get_info()

    def _get_info(self):
        self._check()
        return self._info

    def _get_groups(self):
        self._check()
        return self._groups

    def _get_base_groups(self):
        return self._get_groups()

    def _get_kerning(self):
        self._check()
        return self._kerning

    def _get_base_kerning(self):
        return self._get_kerning()

    def _get_path(self):
        self._check()
        return self._backend.path()

    def _get_base_features(self):
        self._check()
        return self._features

    def _get_base_lib(self):
        self._check()
        return self._lib

    def _save(self, path, showProgress, formatVersion, fileStructure, **kwargs):
        self._check()
        self._check_pending()
        if hasattr(self._backend, "save_options"):
            return self._backend.save_options(
                path, formatVersion=formatVersion, fileStructure=fileStructure
            )
        if formatVersion is not None or fileStructure is not None:
            raise UnsupportedCapability(
                "font.save.ufoOptions",
                "Native saves accept VFJ/VFC, not UFO format/structure options",
            )
        self._backend.save(path)

    @property
    def images(self):
        raise UnsupportedCapability(
            "glyph.image", "Native image storage is unavailable"
        )

    def _check_pending(self):
        if any(
            binding.pending_geometry
            for layer in self._layers.values()
            for binding in layer._bindings.values()
        ):
            raise UnsupportedCapability(
                "glyph.incompleteContours",
                "Finish or remove provisional point edits before saving or invalidating cached handles",
            )

    def invalidate(self):
        """Drop cached bindings, including after external document closure."""
        self._check_pending()
        self._invalidate()

    def glyph_summaries(self, layer=None):
        """Return ``(name, unicodes, width)`` for every glyph on ``layer``.

        ``layer`` defaults to the default layer. Reads the backend in one pass
        without loading outlines, so a whole-font scan stays cheap.
        """
        self._check()
        name = self._backend.default_layer() if layer is None else layer
        method = getattr(self._backend, "glyph_summaries", None)
        if callable(method):
            return tuple((n, tuple(u), w) for n, u, w in method(name))
        target = self.getLayer(name)
        return tuple((n, tuple(target[n].unicodes), target[n].width) for n in target.keys())  # noqa: SIM118 - RLayer iteration yields glyph objects.

    def capabilities(self):
        """Return backend capability evidence without requiring a live document."""
        from copy import deepcopy

        method = getattr(self._backend, "capabilities", None)
        return deepcopy(method()) if method else {}

    def refresh(self):
        """Invalidate all existing layer/glyph handles before reading fresh data."""
        self._check()
        self._check_pending()
        self._invalidate()

    def _invalidate(self):
        for layer in self._layers.values():
            layer._valid = False
        self._layers = {}

    def _close(self, **kwargs):
        self._check()
        if any(
            binding.pending_geometry
            for layer in self._layers.values()
            for binding in layer._bindings.values()
        ):
            import warnings

            warnings.warn(
                "glyph.incompleteContours: closing discards unfinished point edits",
                RuntimeWarning,
                stacklevel=2,
            )
        self._backend.close()
        self._invalidate()
        self._closed = True
