# this_file: tests/test_staged_image_resources.py
"""Owned real-library deferred staging, final-state and lifetime oracles."""

import gc
import struct
import zlib
from copy import deepcopy

import pytest
from fontParts import fontshell
from fontParts.base.errors import FontPartsError
from test_image_preservation import PNG, file_hashes, owned_font
from test_image_resources import other_png
from ufoLib2 import Font

from fontlab_fontport.errors import StaleObjectError, UnsupportedCapability
from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend


def third_png():
    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes([0, 0, 0, 255, 255])))
        + chunk(b"IEND", b"")
    )


class CountingBackend(UFOBackend):
    def __init__(self, font):
        super().__init__(font)
        self.writes = 0

    def write_glyph(self, *args):
        self.writes += 1
        super().write_glyph(*args)


@pytest.mark.parametrize("structure", ["package", "zip"])
@pytest.mark.parametrize(
    "route",
    [
        "n_clear",
        "n_m",
        "n_clear_add",
        "clear_n",
        "clear_false",
        "clear_true",
        "metadata",
        "same",
        "absent",
        "missing",
        "uppercase",
        "collision",
        "clear_absent",
        "caught_invalid",
        "add_defaults",
        "add_path",
    ],
)
def test_stage_when_ordered_intent_then_only_final_full_font_commits(
    tmp_path, structure, route
):
    source = owned_font()
    if route in ("absent", "clear_absent"):
        source["A"].image = None
    elif route == "missing":
        source["A"].image.fileName = "missing.png"
    elif route == "uppercase":
        source.images["IMAGE.PNG"] = PNG
        source["A"].image.fileName = "IMAGE.PNG"
    elif route == "collision":
        source.images["image.png"] = PNG
        source.images["IMAGE000000000000001.PNG"] = PNG
    elif route == "same":
        source.images.clear()
        source.images["first.png"] = PNG
        source.images["owned.png"] = PNG
    initial = tmp_path / "input.ufo"
    source.save(initial)
    hashes = file_hashes(initial)
    backend = CountingBackend(Font.open(initial, lazy=False))
    before = deepcopy(backend.font)
    expected = deepcopy(before)
    font = RFont(backend)
    value = other_png()
    name = (
        "image000000000000002.png"
        if route == "collision"
        else "image000000000000001.png"
        if route == "uppercase"
        else "image.png"
    )
    with font.edit_glyph("A") as staged:
        cached = staged.image
        assert cached.data == (
            None if route in ("absent", "clear_absent", "missing") else PNG
        )
        assert backend.font == before and backend.writes == 0
        if route in ("same", "clear_absent"):
            if route == "same":
                staged.image.data = PNG
            else:
                staged.clearImage()
        elif route in ("clear_n",):
            staged.clearImage()
            assert not staged.image and cached.data is None
            staged.image.data = value
            expected["A"].image = None
            expected.images[name] = value
            expected["A"].image.fileName = name
        elif route in ("add_defaults", "add_path"):
            options = {"data": value}
            if route == "add_path":
                path = tmp_path / "owned.png"
                path.write_bytes(value)
                options = {"path": str(path)}
            staged.addImage(**options)
            expected["A"].image = None
            expected.images[name] = value
            expected["A"].image.fileName = name
        else:
            staged.image.data = value
            assert cached.data == staged.image.data == value
            assert backend.font == before and backend.writes == 0
            if route in ("n_clear", "clear_true"):
                if route == "n_clear":
                    staged.clearImage()
                else:
                    staged.clear(
                        contours=False,
                        components=False,
                        anchors=False,
                        guidelines=False,
                        image=True,
                    )
                expected["A"].image = None
                assert cached.data is None and not staged.image
            elif route == "n_clear_add":
                staged.clearImage()
                value = third_png()
                staged.addImage(
                    data=value,
                    scale=(1.2, 0.8),
                    position=(25, -30),
                    color=(0.5, 0.25, 0.75, 0.8),
                )
                expected["A"].image.transformation = (1.2, 0, 0, 0.8, 25, -30)
                expected["A"].image.color = "0.5,0.25,0.75,0.8"
            elif route == "n_m":
                value = third_png()
                staged.image.data = value
            elif route == "clear_false":
                staged.clear(
                    contours=True,
                    components=False,
                    anchors=False,
                    guidelines=False,
                    image=False,
                )
                expected["A"].contours.clear()
            elif route == "metadata":
                staged.image.color = None
                staged.image.transformation = (0.9, 0.1, -0.2, 1.3, 27.5, -40)
                staged.width = 617
                staged[0].points[0].x = 9
                expected["A"].image.color = None
                expected["A"].image.transformation = (0.9, 0.1, -0.2, 1.3, 27.5, -40)
                expected["A"].width = 617
                expected["A"].contours[0].points[0].x = 9
                assert cached.color is None and staged.image.color is None
            elif route == "caught_invalid":
                for invalid in (None, b"not png", "invalid"):
                    with pytest.raises(FontPartsError):
                        staged.image.data = invalid
                    assert cached.data == staged.image.data == value
            if route not in ("n_clear", "clear_true"):
                expected.images[name] = value
                expected["A"].image.fileName = name
        assert backend.font == before and backend.writes == 0
        assert cached.data == staged.image.data
    assert backend.font == expected
    assert backend.writes == (0 if route in ("same", "clear_absent") else 1)
    ending = ".ufoz" if structure == "zip" else ".ufo"
    backend.save_options(tmp_path / f"actual{ending}", fileStructure=structure)
    expected.save(tmp_path / f"control{ending}", structure=structure)
    assert Font.open(tmp_path / f"actual{ending}", lazy=False) == Font.open(
        tmp_path / f"control{ending}", lazy=False
    )
    assert file_hashes(initial) == hashes


@pytest.mark.parametrize("structure", ["package", "zip"])
def test_staged_color_when_assigned_then_fresh_wrappers_and_saved_font_agree(
    tmp_path, structure
):
    backend = CountingBackend(owned_font())
    expected = deepcopy(backend.font)
    before = deepcopy(backend.font)
    with RFont(backend).edit_glyph("A") as glyph:
        cached = glyph.image
        cached.color = (1, 0, 0, 0.5)
        assert tuple(glyph.image.color) == tuple(cached.color) == (1, 0, 0, 0.5)
        assert backend.font == before and backend.writes == 0
    expected["A"].image.color = "1,0,0,0.5"
    assert backend.font == expected
    ending = ".ufoz" if structure == "zip" else ".ufo"
    backend.save_options(tmp_path / f"actual{ending}", fileStructure=structure)
    expected.save(tmp_path / f"control{ending}", structure=structure)
    assert Font.open(tmp_path / f"actual{ending}", lazy=False) == Font.open(
        tmp_path / f"control{ending}", lazy=False
    )


@pytest.mark.parametrize("interrupt", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_stage_when_body_aborts_then_backend_is_untouched_and_handles_end(interrupt):
    backend = CountingBackend(owned_font())
    expected = deepcopy(backend.font)
    font = RFont(backend)
    marker = interrupt("owned body abort")
    with pytest.raises(interrupt) as caught, font.edit_glyph("A") as glyph:
        image = glyph.image
        image.data = other_png()
        image.color = (1, 0, 0, 1)
        glyph.width = 617
        raise marker
    assert caught.value is marker
    assert backend.font == expected and backend.writes == 0
    with pytest.raises(StaleObjectError):
        _ = glyph.width
    with pytest.raises(StaleObjectError):
        _ = image.data


@pytest.mark.parametrize(
    "fault",
    [
        "write_before",
        "write_after",
        "refresh_before",
        "refresh_after",
        "metadata_after",
        "clear_after",
    ],
)
def test_stage_when_commit_fails_then_complete_backend_restores_without_cache_resurrection(
    monkeypatch, fault
):
    marker = RuntimeError("owned commit rejected")

    class Backend(CountingBackend):
        def write_glyph(self, *args):
            if fault == "write_before":
                raise marker
            super().write_glyph(*args)
            if fault in ("write_after", "metadata_after", "clear_after"):
                raise marker

    backend = Backend(owned_font())
    expected = deepcopy(backend.font)
    font = RFont(backend)
    old = font["A"]
    cache = font._layers
    if fault in ("refresh_before", "refresh_after"):
        refresh = type(font).refresh

        def failing_refresh():
            if fault == "refresh_after":
                refresh(font)
            raise marker

        monkeypatch.setattr(font, "refresh", failing_refresh)
    with pytest.raises(RuntimeError) as caught, font.edit_glyph("A") as staged:
        staged.width = 617
        if fault == "clear_after":
            staged.clearImage()
        elif fault != "metadata_after":
            staged.image.data = other_png()
    assert caught.value is marker
    assert backend.font == expected
    assert backend.writes <= 1
    if fault == "refresh_after":
        assert font._layers is not cache
        with pytest.raises(StaleObjectError):
            _ = old.width
    with pytest.raises(StaleObjectError):
        _ = staged.width


@pytest.mark.parametrize(
    "change",
    [
        "refresh",
        "invalidate",
        "close",
        "backend_close",
        "glyph_removed",
        "layer_removed",
        "target_changed",
        "resource_changed",
    ],
)
def test_stage_when_source_stales_then_never_recreates_or_overwrites_external_state(
    change,
):
    source = owned_font()
    source.layers["owned.background"].insertGlyph(deepcopy(source["A"]))
    backend = CountingBackend(source)
    font = RFont(backend)
    with (
        pytest.raises(StaleObjectError),
        font.edit_glyph("A", layer="owned.background") as staged,
    ):
        image = staged.image
        staged.width = 617
        if change in ("refresh", "invalidate", "close"):
            getattr(font, change)()
        elif change == "backend_close":
            backend.close()
        elif change == "glyph_removed":
            backend.remove_glyph("A", "owned.background")
        elif change == "layer_removed":
            backend.remove_layer("owned.background")
        elif change == "target_changed":
            backend.font.layers["owned.background"]["A"].width = 777
        else:
            backend.font.images["owned.png"] = other_png()
        external = deepcopy(backend.font)
    assert backend.font == external and backend.writes == 0
    with pytest.raises(StaleObjectError):
        image.color = (1, 0, 0, 1)


@pytest.mark.parametrize(
    "access",
    [
        "glyph",
        "data",
        "color",
        "transform",
        "bool",
        "set_data",
        "set_color",
        "set_transform",
        "retained",
    ],
)
def test_stage_when_success_ends_and_parents_collected_then_public_access_is_stale(
    access,
):
    backend = CountingBackend(owned_font())
    font = RFont(backend)
    with font.edit_glyph("A") as glyph:
        image = glyph.image
        retained = image.moveBy
        glyph.width = 617
    gc.collect()
    expected = deepcopy(backend.font)
    with pytest.raises(StaleObjectError):
        if access == "glyph":
            _ = glyph.width
        elif access == "data":
            _ = image.data
        elif access == "color":
            _ = image.color
        elif access == "transform":
            _ = image.transformation
        elif access == "bool":
            bool(image)
        elif access == "set_data":
            image.data = other_png()
        elif access == "set_color":
            image.color = (1, 0, 0, 1)
        elif access == "set_transform":
            image.transformation = (1, 0, 0, 1, 99, 99)
        else:
            retained((99, 99))
    assert backend.font == expected


def test_stage_when_normal_cache_populates_then_remains_valid_and_copy_independent():
    backend = CountingBackend(owned_font())
    font = RFont(backend)
    with font.edit_glyph("A") as glyph:
        font.getLayer("owned.background")
        assert font["B"].width == 420
        glyph.image.data = other_png()
        glyph.image.color = (0.5, 0.25, 0.75, 1)
        copied = glyph.image.copy()
        assert copied.glyph is None and copied.data == other_png()
        assert copied.__dict__.get("_staged_image_resources") is None
    font.close()
    assert copied.data == other_png()
    assert tuple(copied.color) == (0.5, 0.25, 0.75, 1)


@pytest.mark.parametrize("partial", ["read", "edit", "neither"])
def test_stage_when_resources_unavailable_then_metadata_uses_named_writer_without_resource_calls(
    partial,
):
    class Backend(CountingBackend):
        read_image = None
        edit_image = None

        def forbidden(self, *args):
            raise AssertionError("unsupported resource method called")

        def write_glyph_named(self, name, layer, source, *, undo_name):
            self.undo_name = undo_name
            self.input = deepcopy(source.naked().getDataForSerialization())
            self.write_glyph(name, layer, source)

    if partial == "read":
        Backend.read_image = Backend.forbidden
    elif partial == "edit":
        Backend.edit_image = Backend.forbidden
    backend = Backend(owned_font())
    expected = deepcopy(backend.font)
    font = RFont(backend)
    with font.edit_glyph("A", undo_name="Owned staged metadata") as glyph:
        with pytest.raises(UnsupportedCapability):
            _ = glyph.image.data
        with pytest.raises(UnsupportedCapability):
            glyph.image.data = other_png()
        glyph.width = 617
        glyph.image.color = (1, 0, 0, 1)
        glyph.image.transformation = (1, 0, 0, 1, 30, 40)
    expected["A"].width = 617
    expected["A"].image.color = "1,0,0,1"
    expected["A"].image.transformation = (1, 0, 0, 1, 30, 40)
    assert backend.font == expected and backend.writes == 1
    assert backend.undo_name == "Owned staged metadata"


@pytest.mark.parametrize(
    "fault", ["insert", "notification_before", "notification_after"]
)
def test_stage_when_insert_or_observer_fails_then_no_new_resource_or_target_leaks(
    monkeypatch, fault
):
    from ufoLib2.objects.imageSet import ImageSet

    marker = RuntimeError("owned stage resource rejected")

    class Backend(CountingBackend):
        post = False
        model = None

        def write_glyph(self, *args):
            super().write_glyph(*args)
            self.post = True
            if fault == "notification_after":
                self.model.image.postNotification("Owned.AfterWrite")

    backend = Backend(owned_font())
    expected = deepcopy(backend.font)
    if fault == "insert":
        insert = ImageSet.__setitem__

        def put(self, name, data):
            insert(self, name, data)
            if name == "image.png":
                raise marker

        monkeypatch.setattr(ImageSet, "__setitem__", put)

    with (
        pytest.raises(RuntimeError) as caught,
        RFont(backend).edit_glyph("A") as glyph,
    ):
        backend.model = glyph.naked()
        if fault != "insert":
            native_image = backend.model.image
            notify = native_image.postNotification

            def notification_error(notification, data=None):
                notify(notification, data=data)
                if native_image.fileName == "image.png" and (
                    fault == "notification_before" or backend.post
                ):
                    raise marker

            monkeypatch.setattr(native_image, "postNotification", notification_error)
        glyph.image.data = other_png()
    assert caught.value is marker
    assert backend.font == expected and backend.writes <= 1
    with pytest.raises(StaleObjectError):
        _ = glyph.image


@pytest.mark.parametrize("mode", ["bytes", "metadata", "clear"])
@pytest.mark.parametrize("interrupt", [KeyboardInterrupt, SystemExit])
def test_stage_when_actual_write_is_interrupted_then_restores_complete_target(
    mode, interrupt
):
    marker = interrupt("owned staged write interrupted")

    class Backend(CountingBackend):
        def write_glyph(self, *args):
            super().write_glyph(*args)
            raise marker

    backend = Backend(owned_font())
    expected = deepcopy(backend.font)
    with (
        pytest.raises(interrupt) as caught,
        RFont(backend).edit_glyph("A") as glyph,
    ):
        glyph.width = 617
        if mode == "bytes":
            glyph.image.data = other_png()
        elif mode == "clear":
            glyph.clearImage()
    assert caught.value is marker
    assert backend.font == expected and backend.writes == 1
    with pytest.raises(StaleObjectError):
        _ = glyph.width


def test_stage_when_resource_cleanup_fails_then_actual_failure_is_visible(monkeypatch):
    from ufoLib2.objects.imageSet import ImageSet

    marker = RuntimeError("owned staged write rejected")
    cleanup = OSError("owned staged cleanup rejected")

    class Backend(CountingBackend):
        def write_glyph(self, *args):
            super().write_glyph(*args)
            raise marker

    backend = Backend(owned_font())
    original = deepcopy(backend.font["A"])
    delete = ImageSet.__delitem__

    def reject_delete(self, name):
        if name == "image.png":
            raise cleanup
        delete(self, name)

    monkeypatch.setattr(ImageSet, "__delitem__", reject_delete)
    with (
        pytest.raises(RuntimeError) as caught,
        RFont(backend).edit_glyph("A") as glyph,
    ):
        glyph.image.data = other_png()
    assert caught.value is marker and marker.__cause__ is cleanup
    assert backend.font["A"] == original and "image.png" in backend.font.images
    assert any("rollback" in note for note in marker.__notes__)
    with pytest.raises(StaleObjectError):
        _ = glyph.width


@pytest.mark.parametrize("after_invalidation", [False, True])
def test_stage_when_noop_refresh_fails_then_no_target_resource_mutation(
    monkeypatch, after_invalidation
):
    backend = CountingBackend(owned_font())
    expected = deepcopy(backend.font)
    font = RFont(backend)
    marker = RuntimeError("owned noop refresh rejected")

    def fail():
        if after_invalidation:
            type(font).refresh(font)
        raise marker

    monkeypatch.setattr(font, "refresh", fail)
    with pytest.raises(RuntimeError) as caught, font.edit_glyph("A") as glyph:
        glyph.image.data = PNG
    assert caught.value is marker
    assert backend.font == expected and backend.writes == 0
    with pytest.raises(StaleObjectError):
        _ = glyph.width


def test_stage_when_aliasing_provider_is_read_then_preimages_and_body_are_independent():
    class AliasingBackend(CountingBackend):
        def read_glyph(self, name, layer):
            return self.font.layers[layer][name]

    backend = AliasingBackend(owned_font())
    before = deepcopy(backend.font)
    expected = deepcopy(before)
    with RFont(backend).edit_glyph("A") as glyph:
        glyph.lib["owned"]["nested"].append(99)
        glyph.note = "Owned staged note"
        assert backend.font == before and backend.writes == 0
    expected["A"].lib["owned"]["nested"].append(99)
    expected["A"].note = "Owned staged note"
    assert backend.font == expected and backend.writes == 1


def test_stage_when_capability_disappears_then_commit_refuses_without_write():
    backend = CountingBackend(owned_font())
    expected = deepcopy(backend.font)
    with (
        pytest.raises(UnsupportedCapability),
        RFont(backend).edit_glyph("A") as glyph,
    ):
        glyph.image.data = other_png()
        backend.edit_image = None
    assert backend.font == expected and backend.writes == 0


@pytest.mark.parametrize("structure", ["package", "zip"])
def test_stage_when_affine_methods_and_color_change_then_matches_actual_upstream(
    tmp_path, structure
):
    backend = CountingBackend(owned_font())
    before = deepcopy(backend.font)
    expected = deepcopy(before)
    oracle = fontshell.RImage()
    oracle.transformation = tuple(expected["A"].image.transformation)
    with RFont(backend).edit_glyph("A") as glyph:
        image = glyph.image
        image.data = other_png()
        for obj in (image, oracle):
            obj.offset = (12.5, -27.75)
            obj.scale = (1.1, 0.9)
            obj.moveBy((2.25, -1.5))
            obj.scaleBy((0.8, 1.2))
            obj.rotateBy(15)
            obj.skewBy(5)
            obj.round()
        assert (
            tuple(image.transformation)
            == tuple(glyph.image.transformation)
            == tuple(oracle.transformation)
        )
        image.color = (0.25, 0.5, 0.75, 1)
        assert tuple(glyph.image.color) == (0.25, 0.5, 0.75, 1)
        assert backend.font == before
    expected.images["image.png"] = other_png()
    expected["A"].image.fileName = "image.png"
    expected["A"].image.transformation = tuple(oracle.transformation)
    expected["A"].image.color = "0.25,0.5,0.75,1"
    ending = ".ufoz" if structure == "zip" else ".ufo"
    backend.save_options(tmp_path / f"actual{ending}", fileStructure=structure)
    expected.save(tmp_path / f"control{ending}", structure=structure)
    assert Font.open(tmp_path / f"actual{ending}", lazy=False) == Font.open(
        tmp_path / f"control{ending}", lazy=False
    )


def test_stage_when_shared_name_in_other_layer_then_only_requested_target_changes():
    source = owned_font()
    source["B"].image = deepcopy(source["A"].image)
    source.layers["owned.background"].insertGlyph(deepcopy(source["A"]))
    backend = CountingBackend(source)
    expected = deepcopy(source)
    with RFont(backend).edit_glyph("A", layer="owned.background") as glyph:
        glyph.image.data = other_png()
        glyph.image.color = (1, 0, 0, 1)
        assert backend.font == source
    expected.images["image.png"] = other_png()
    expected.layers["owned.background"]["A"].image.fileName = "image.png"
    expected.layers["owned.background"]["A"].image.color = "1,0,0,1"
    assert backend.font == expected


def test_stage_when_copying_then_image_independent_and_glyph_matches_upstream_limit():
    backend = CountingBackend(owned_font())
    font = RFont(backend)
    reference = fontshell.RFont()
    oracle = reference.newGlyph("A")
    oracle.addImage(data=other_png(), color=(0.5, 0.25, 0.75, 1), position=(23, -17))
    oracle_copy = oracle.copy()
    with font.edit_glyph("A") as glyph:
        glyph.addImage(data=other_png(), color=(0.5, 0.25, 0.75, 1), position=(23, -17))
        image = glyph.image
        image_copy = image.copy()
        copied_data = type(image)()
        copied_data.copyData(image)
        copied_glyph = glyph.copy()
        for obj in (copied_glyph, oracle_copy):
            assert obj.font is None
            assert obj.image.data is None and obj.image.color is None
            assert obj.naked().image.fileName is None
        assert tuple(copied_glyph.image.transformation) == tuple(
            oracle_copy.image.transformation
        )
    font.close()
    for copied in (image_copy, copied_data):
        assert copied.font is None and copied.glyph is None
        assert copied.data == other_png() and tuple(copied.color) == (
            0.5,
            0.25,
            0.75,
            1,
        )
        assert copied.__dict__.get("_staged_image_resources") is None


def test_stage_when_ended_then_record_releases_owner_cache_and_preimages():
    backend = CountingBackend(owned_font())
    with RFont(backend).edit_glyph("A") as glyph:
        image = glyph.image
        state = object.__getattribute__(image, "__dict__")["_staged_image_resources"]
        assert len(state) == 11
        glyph.width = 617
    assert state["active"] is False
    for key in ("owner", "cache", "source", "initial_model", "source_data", "data"):
        assert state[key] is None
    with pytest.raises(StaleObjectError):
        image.color = (1, 0, 0, 1)


@pytest.mark.parametrize("reference", ["existing", "missing", "absent"])
@pytest.mark.parametrize("structure", ["package", "zip"])
def test_stage_when_metadata_only_then_preserves_reference_without_resource_decision(
    tmp_path, reference, structure
):
    source = owned_font()
    if reference == "missing":
        source["A"].image.fileName = "missing.png"
    elif reference == "absent":
        source["A"].image = None
    backend = CountingBackend(source)
    expected = deepcopy(source)
    with RFont(backend).edit_glyph("A") as glyph:
        glyph.width = 617
    expected["A"].width = 617
    assert backend.font == expected
    ending = ".ufoz" if structure == "zip" else ".ufo"
    backend.save_options(tmp_path / f"actual{ending}", fileStructure=structure)
    expected.save(tmp_path / f"control{ending}", structure=structure)
    assert Font.open(tmp_path / f"actual{ending}", lazy=False) == Font.open(
        tmp_path / f"control{ending}", lazy=False
    )


def test_metadata_context_when_none_is_explicit_then_keeps_existing_invalid_domain():
    backend = CountingBackend(owned_font())
    expected = deepcopy(backend.font)
    with (
        pytest.raises(FontPartsError),
        backend.edit_image("A", backend.default_layer(), None),
    ):
        raise AssertionError("invalid explicit None entered metadata-only mode")
    assert backend.font == expected and backend.writes == 0
    with backend.edit_image("A", backend.default_layer()) as filename:
        assert filename is None
    assert backend.font == expected


def test_stage_when_copying_into_independent_checked_target_then_source_stays_deferred():
    backend = CountingBackend(owned_font())
    before = deepcopy(backend.font)
    destination = UFOBackend(owned_font())
    destination.remove_glyph("A", destination.default_layer())
    destination.new_glyph("A", destination.default_layer())
    target = RFont(destination)["A"]
    with RFont(backend).edit_glyph("A") as glyph:
        glyph.image.data = other_png()
        glyph.image.color = (1, 0, 0, 0.5)
        target.copyData(glyph)
        assert target.image.data == other_png()
        assert tuple(target.image.color) == (1, 0, 0, 0.5)
        assert backend.font == before and backend.writes == 0
    assert destination.font.images[target.naked().image.fileName] == other_png()
    assert backend.font.images[backend.font["A"].image.fileName] == other_png()
