# this_file: tests/test_image_resources.py
"""Actual checked FontParts image byte routes and detached transactions."""

import gc
import struct
import zlib
from copy import deepcopy

import pytest
from defcon.objects.image import Image
from fontParts.base.errors import FontPartsError
from test_image_preservation import PNG, file_hashes, owned_font
from ufoLib2 import Font
from ufoLib2.objects.imageSet import ImageSet

from fontlab_fontport.errors import StaleObjectError, UnsupportedCapability
from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend


def other_png():
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes([0, 0, 255, 0, 255])))
        + chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("structure", ["package", "zip"])
@pytest.mark.parametrize(
    "route",
    [
        "same",
        "different",
        "absent",
        "missing",
        "uppercase",
        "dedup",
        "collision",
        "current_not_first",
    ],
)
def test_public_image_bytes_when_assigned_then_full_saved_font_matches_control(
    tmp_path, structure, route
):
    source = owned_font()
    value, filename = other_png(), "image.png"
    if route == "same":
        value, filename = PNG, "owned.png"
    elif route == "absent":
        source["A"].image = None
    elif route == "missing":
        source["A"].image.fileName = "missing.png"
    elif route == "uppercase":
        source.images["IMAGE.PNG"] = PNG
        source["A"].image.fileName = "IMAGE.PNG"
        filename = "image000000000000001.png"
    elif route == "dedup":
        source.images["already.png"] = value
        filename = "already.png"
    elif route == "collision":
        source.images["image.png"] = PNG
        source.images["IMAGE000000000000001.PNG"] = PNG
        filename = "image000000000000002.png"
    elif route == "current_not_first":
        source.images.clear()
        source.images["first.png"] = PNG
        source.images["owned.png"] = PNG
        value, filename = PNG, "owned.png"
    initial = tmp_path / "input.ufo"
    source.save(initial)
    hashes = file_hashes(initial)
    backend = UFOBackend(Font.open(initial, lazy=False))
    expected = Font.open(initial, lazy=False)
    checked = RFont(backend)["A"]
    expected_before = None if route in ("absent", "missing") else PNG
    assert checked.image.data == expected_before
    checked.image.data = value
    expected.images[filename] = value
    expected["A"].image.fileName = filename
    assert checked.image.data == value
    assert checked.naked().image.fileName == filename
    assert backend.font == expected
    ending = ".ufoz" if structure == "zip" else ".ufo"
    backend.save_options(tmp_path / f"actual{ending}", fileStructure=structure)
    expected.save(tmp_path / f"control{ending}", structure=structure)
    actual = Font.open(tmp_path / f"actual{ending}", lazy=False)
    assert actual == Font.open(tmp_path / f"control{ending}", lazy=False)
    assert actual.images[actual["A"].image.fileName] == value
    assert file_hashes(initial) == hashes


def test_public_image_when_shared_across_layers_then_only_target_reference_changes():
    source = owned_font()
    source["B"].image = deepcopy(source["A"].image)
    source.layers["owned.background"].insertGlyph(deepcopy(source["A"]))
    backend = UFOBackend(source)
    expected = deepcopy(source)
    font = RFont(backend)
    font.getLayer("owned.background")["A"].image.data = other_png()
    expected.images["image.png"] = other_png()
    expected.layers["owned.background"]["A"].image.fileName = "image.png"
    assert backend.font == expected
    assert font["A"].image.data == font["B"].image.data == PNG


@pytest.mark.parametrize(
    "value", [None, "not bytes", b"", b"not a PNG", bytearray(PNG)]
)
def test_public_image_when_input_invalid_then_whole_font_is_unchanged(value):
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    image = RFont(backend)["A"].image
    with pytest.raises(FontPartsError):
        image.data = value
    assert backend.font == expected
    assert dict(image.naked()) == dict(expected["A"].image)


@pytest.mark.parametrize(
    "fault",
    [
        "before_write",
        "after_write",
        "before_observer",
        "after_observer",
        "filename",
        "insert",
    ],
)
def test_public_image_when_operation_fails_then_resources_and_cached_state_restore(
    monkeypatch, fault
):
    marker = RuntimeError("owned image operation rejected")

    class Backend(UFOBackend):
        fail = True
        writes = 0

        def write_glyph(self, name, layer, source):
            self.writes += 1
            if self.fail and fault == "before_write":
                raise marker
            super().write_glyph(name, layer, source)
            if self.fail and fault == "after_write":
                raise marker

    backend = Backend(owned_font())
    expected = deepcopy(backend.font)
    glyph = RFont(backend)["A"]
    image = glyph.image
    native_image = image.naked()
    binding = glyph._live_binding

    class Observer:
        def changed(self, notification):
            if backend.fail and notification.object.image.fileName != "owned.png":
                raise marker

    observer = Observer()
    if fault == "before_observer":
        glyph.naked().removeObserver(binding, "Glyph.Changed")
        glyph.naked().addObserver(observer, "changed", "Glyph.Changed")
        glyph.naked().addObserver(binding, "changed", "Glyph.Changed")
    elif fault == "after_observer":
        glyph.naked().addObserver(observer, "changed", "Glyph.Changed")
    elif fault == "filename":
        original = Image.fileName

        def set_filename(self, name):
            if backend.fail and name == "image.png":
                raise marker
            original.fset(self, name)

        monkeypatch.setattr(Image, "fileName", property(original.fget, set_filename))
    elif fault == "insert":
        insert = ImageSet.__setitem__

        def put(self, name, data):
            insert(self, name, data)
            if backend.fail and name == "image.png":
                raise marker

        monkeypatch.setattr(ImageSet, "__setitem__", put)
    with pytest.raises(RuntimeError) as caught:
        image.data = other_png()
    assert caught.value is marker
    assert backend.font == expected
    assert image.naked() is native_image
    assert dict(image.naked()) == dict(expected["A"].image)
    assert binding.accepted == glyph.naked().getDataForSerialization()
    assert image.data == PNG
    assert tuple(image.transformation) == tuple(expected["A"].image.transformation)
    assert tuple(image.color) == (0.125, 0.25, 0.5, 0.75)
    assert backend.writes <= 1, "rollback issued a second ordinary write"
    backend.fail = False
    glyph.width = 617
    expected["A"].width = 617
    assert backend.font == expected
    assert image.data == PNG


def test_public_image_when_cleanup_fails_then_original_error_and_cleanup_are_visible(
    monkeypatch,
):
    marker = RuntimeError("owned write rejected")
    cleanup = OSError("owned cleanup rejected")

    class Backend(UFOBackend):
        def write_glyph(self, name, layer, source):
            super().write_glyph(name, layer, source)
            raise marker

    backend = Backend(owned_font())
    original = deepcopy(backend.font["A"])
    delete = ImageSet.__delitem__

    def fail_delete(self, name):
        if name == "image.png":
            raise cleanup
        delete(self, name)

    monkeypatch.setattr(ImageSet, "__delitem__", fail_delete)
    image = RFont(backend)["A"].image
    with pytest.raises(RuntimeError) as caught:
        image.data = other_png()
    assert caught.value is marker
    assert cleanup is marker.__cause__ or any(
        "cleanup" in n for n in getattr(marker, "__notes__", [])
    )
    assert backend.font["A"] == original
    assert "image.png" in backend.font.images
    assert image.naked().fileName == "owned.png"


@pytest.mark.parametrize(
    "action",
    [
        "refresh",
        "invalidate",
        "remove_glyph",
        "remove_layer",
        "backend_close",
        "font_close",
    ],
)
@pytest.mark.parametrize(
    "access",
    [
        "data",
        "transform",
        "color",
        "set_data",
        "set_transform",
        "set_color",
        "retained",
    ],
)
def test_cached_image_when_owner_stales_after_parent_gc_then_access_refuses(
    action, access
):
    source = owned_font()
    source.layers["owned.background"].insertGlyph(deepcopy(source["A"]))
    backend = UFOBackend(source)
    font = RFont(backend)
    glyph = font.getLayer("owned.background")["A"]
    image = glyph.image
    retained = image.moveBy
    del glyph
    gc.collect()
    if action in ("refresh", "invalidate"):
        getattr(font, action)()
    elif action == "remove_glyph":
        font.getLayer("owned.background").removeGlyph("A")
    elif action == "remove_layer":
        font.removeLayer("owned.background")
    elif action == "backend_close":
        backend.close()
    else:
        font.close()
    expected = deepcopy(backend.font)
    with pytest.raises(StaleObjectError):
        if access == "data":
            _ = image.data
        elif access == "transform":
            _ = image.transformation
        elif access == "color":
            _ = image.color
        elif access == "set_data":
            image.data = other_png()
        elif access == "set_transform":
            image.transformation = (1, 0, 0, 1, 99, 99)
        elif access == "set_color":
            image.color = (1, 0, 0, 1)
        else:
            retained((99, 99))
    assert backend.font == expected


def test_public_image_when_refreshed_then_payload_is_fresh_and_copy_is_parentless():
    backend = UFOBackend(owned_font())
    font = RFont(backend)
    image = font["A"].image
    copied = image.copy()
    assert copied.glyph is None and copied.font is None
    assert copied.data == PNG
    assert copied.__dict__.get("_live_binding") is None
    backend.font.images["owned.png"] = other_png()
    assert image.data == other_png(), "read was cached in the private model"
    font.refresh()
    assert font["A"].image.data == other_png()
    font.close()
    assert copied.data == PNG
    copied.data = other_png()
    assert copied.data == other_png()


def test_public_image_when_current_duplicate_not_first_then_no_write_occurs():
    class NoWrite(UFOBackend):
        def write_glyph(self, *args):
            raise AssertionError("a true image no-op reached the writer")

    source = owned_font()
    source.images.clear()
    source.images["first.png"] = PNG
    source.images["owned.png"] = PNG
    expected = deepcopy(source)
    backend = NoWrite(source)
    RFont(backend)["A"].image.data = PNG
    assert backend.font == expected


def test_public_image_when_model_cleanup_fails_then_original_operation_is_visible(
    monkeypatch,
):
    marker = RuntimeError("owned operation rejected")
    cleanup = OSError("owned model cleanup rejected")

    class Backend(UFOBackend):
        def write_glyph(self, *args):
            super().write_glyph(*args)
            raise marker

    backend = Backend(owned_font())
    expected = deepcopy(backend.font)
    glyph = RFont(backend)["A"]

    def fail_restore(state):
        raise cleanup

    monkeypatch.setattr(glyph._live_binding, "_restore_accepted", fail_restore)
    with pytest.raises(RuntimeError) as caught:
        glyph.image.data = other_png()
    assert caught.value is marker
    assert marker.__cause__ is cleanup
    assert any("rollback" in note for note in marker.__notes__)
    assert backend.font == expected


@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("operation", ["read", "write"])
def test_public_image_when_capability_missing_then_refuses_before_any_mutation(
    empty, operation
):
    class NoImages(UFOBackend):
        read_image = None
        edit_image = None

        def write_glyph(self, *args):
            raise AssertionError("missing image capability reached glyph writer")

    backend = NoImages(owned_font(not empty))
    expected = deepcopy(backend.font)
    glyph = RFont(backend)["A"]
    before = glyph.naked().getDataForSerialization()
    with pytest.raises(UnsupportedCapability, match=r"glyph\.image"):
        if operation == "read":
            _ = glyph.image.data
        else:
            glyph.image.data = other_png()
    assert backend.font == expected
    assert glyph.naked().getDataForSerialization() == before
    assert glyph.naked().font.images.fileNames == []


@pytest.mark.parametrize("operation", ["read", "write"])
def test_staged_image_bytes_when_supported_then_defers_resource_changes(operation):
    backend = UFOBackend(owned_font())
    before = deepcopy(backend.font)
    expected = deepcopy(before)
    with RFont(backend).edit_glyph("A") as staged:
        image = staged.image
        if operation == "read":
            assert image.data == PNG
        else:
            image.data = other_png()
            assert staged.image.data == other_png()
            expected.images["image.png"] = other_png()
            expected["A"].image.fileName = "image.png"
        assert backend.font == before
    del staged
    gc.collect()
    with pytest.raises(StaleObjectError):
        image.data = other_png()
    assert backend.font == expected


@pytest.mark.parametrize("structure", ["package", "zip"])
def test_public_add_image_when_called_then_returned_and_fresh_wrappers_persist(
    tmp_path, structure
):
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    glyph = RFont(backend)["A"]
    image = glyph.addImage(
        data=other_png(),
        scale=(1.1, 1.2),
        position=(13, 14),
        color=(0.25, 0.5, 0.75, 1),
    )
    assert image.data == other_png()
    assert glyph.image.data == other_png()
    expected.images["image.png"] = other_png()
    expected["A"].image.fileName = "image.png"
    expected["A"].image.transformation = (1.1, 0, 0, 1.2, 13, 14)
    expected["A"].image.color = "0.25,0.5,0.75,1"
    assert backend.font == expected
    ending = ".ufoz" if structure == "zip" else ".ufo"
    backend.save_options(tmp_path / f"actual{ending}", fileStructure=structure)
    expected.save(tmp_path / f"control{ending}", structure=structure)
    assert Font.open(tmp_path / f"actual{ending}", lazy=False) == Font.open(
        tmp_path / f"control{ending}", lazy=False
    )


def test_public_add_image_when_resource_route_unavailable_then_refuses_before_metadata():
    class NoImages(UFOBackend):
        read_image = None
        edit_image = None

    backend = NoImages(owned_font())
    expected = deepcopy(backend.font)
    font = RFont(backend)
    glyph = font["A"]
    with pytest.raises(UnsupportedCapability):
        glyph.addImage(
            data=other_png(), scale=(2, 2), position=(99, 99), color=(1, 0, 0, 1)
        )
    assert dict(glyph.naked().image) == dict(expected["A"].image)
    assert backend.font == expected


@pytest.mark.parametrize("fault", ["context", "insert", "write"])
@pytest.mark.parametrize("interrupt_type", [KeyboardInterrupt, SystemExit])
def test_image_transaction_when_interrupted_then_restores_and_reraises_same_interrupt(
    monkeypatch, fault, interrupt_type
):
    marker = interrupt_type("owned image interrupt")

    class Backend(UFOBackend):
        fail = True

        def write_glyph(self, *args):
            super().write_glyph(*args)
            if self.fail and fault == "write":
                raise marker

    backend = Backend(owned_font())
    expected = deepcopy(backend.font)
    glyph = RFont(backend)["A"]
    image = glyph.image
    if fault == "insert":
        insert = ImageSet.__setitem__

        def put(self, name, value):
            insert(self, name, value)
            if backend.fail and name == "image.png":
                raise marker

        monkeypatch.setattr(ImageSet, "__setitem__", put)
    with pytest.raises(interrupt_type) as caught:
        if fault == "context":
            with backend.edit_image("A", backend.default_layer(), other_png()):
                raise marker
        else:
            image.data = other_png()
    assert caught.value is marker
    assert backend.font == expected
    assert dict(image.naked()) == dict(expected["A"].image)
    assert image.data == PNG
    backend.fail = False
    glyph.width = 617
    expected["A"].width = 617
    assert backend.font == expected


def test_public_add_image_when_defaults_then_resets_existing_transform_and_color():
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    image = RFont(backend)["A"].addImage(data=other_png())
    expected.images["image.png"] = other_png()
    expected["A"].image.fileName = "image.png"
    expected["A"].image.transformation = (1, 0, 0, 1, 0, 0)
    expected["A"].image.color = None
    assert backend.font == expected
    assert image.data == other_png()


def test_checked_copy_data_when_source_has_image_then_resource_and_non_target_font_survive():
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    font = RFont(backend)
    destination = UFOBackend(owned_font())
    destination.remove_glyph("A", destination.default_layer())
    destination.new_glyph("A", destination.default_layer())
    target = RFont(destination)["A"]
    target.copyData(font["A"])
    assert target.image.data == PNG
    assert dict(target.naked().image) == dict(expected["A"].image)
    assert backend.font == expected
    actual = deepcopy(destination.font)
    del actual["A"]
    del expected["A"]
    assert actual == expected


@pytest.mark.parametrize(
    "invalid", ["scale", "position", "color", "path_and_data", "missing_path"]
)
def test_public_add_image_when_invalid_then_matches_upstream_error_and_keeps_full_state(
    tmp_path, invalid
):
    from fontParts.fontshell import RGlyph

    options = {"data": other_png()}
    if invalid in ("scale", "position", "color"):
        options[invalid] = "invalid owned value"
    elif invalid == "path_and_data":
        options["path"] = str(tmp_path / "absent.png")
    else:
        options = {"path": str(tmp_path / "absent.png")}
    with pytest.raises(Exception) as oracle:
        RGlyph().addImage(**options)
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    with pytest.raises(type(oracle.value)):
        RFont(backend)["A"].addImage(**options)
    assert backend.font == expected


def test_public_add_image_when_returned_wrapper_retained_then_closure_refuses_after_gc():
    backend = UFOBackend(owned_font())
    font = RFont(backend)
    glyph = font["A"]
    image = glyph.addImage(data=other_png())
    del glyph
    gc.collect()
    font.close()
    expected = deepcopy(backend.font)
    with pytest.raises(StaleObjectError):
        image.data = PNG
    with pytest.raises(StaleObjectError):
        _ = image.transformation
    assert backend.font == expected
