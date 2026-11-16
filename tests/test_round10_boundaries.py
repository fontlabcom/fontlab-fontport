# this_file: tests/test_round10_boundaries.py
import pytest

from fontlab_fontport.capabilities import NATIVE_CAPABILITIES, STRUCTURED_ROUTES
from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.info import STRUCTURED_FIELDS
from fontlab_fontport.testing import FAMILIES, ObjectGenerator, generator_context


def test_native_orphan_contract_is_named_without_importing_a_host():
    for family in (
        "info",
        "groups",
        "kerning",
        "features",
        "lib",
        "layer",
        "glyph",
        "contour",
        "segment",
        "bPoint",
        "point",
        "component",
        "anchor",
        "guideline",
        "image",
    ):
        generator = ObjectGenerator()
        with pytest.raises(UnsupportedCapability, match=r"testing.nativeOrphan"):
            generator(family)
        assert not generator.owned and not generator.pending_ids


def test_unicode_glyph_name_refusal_precedes_any_host_import():
    backend = NativeFontBackend.__new__(NativeFontBackend)
    with pytest.raises(UnsupportedCapability, match=r"glyph.name.unicodeVfj"):
        backend.new_glyph("Ω", "Regular")
    with pytest.raises(UnsupportedCapability, match=r"glyph.name.unicodeVfj"):
        backend.write_glyph("Ω", "Regular", None)


def test_save_refuses_preexisting_unicode_glyph_before_native_write(tmp_path):
    from types import SimpleNamespace

    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._package = lambda: SimpleNamespace(fgPackage=[SimpleNamespace(name="Ω")])
    with pytest.raises(UnsupportedCapability, match=r"glyph.name.unicodeVfj"):
        backend.save(str(tmp_path / "refused.vfj"), require_persistence=True)
    assert not (tmp_path / "refused.vfj").exists()


def test_vfj_save_refuses_preexisting_legacy_group_flags_before_native_write(tmp_path):
    from types import SimpleNamespace

    from test_native_groups import Feature, Groups

    class NativeData(list):
        groups = Groups({"legacy": Feature(["A"], False)})

    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._package = lambda: SimpleNamespace(
        fgPackage=NativeData([SimpleNamespace(name="A")])
    )
    with pytest.raises(UnsupportedCapability, match=r"groups.legacyFlagsVfj"):
        backend.save(str(tmp_path / "refused.vfj"), require_persistence=True)
    assert not (tmp_path / "refused.vfj").exists()


def test_explicit_capability_catalog_has_all_structured_native_routes():
    assert set(STRUCTURED_ROUTES) == STRUCTURED_FIELDS
    assert all(
        row["bound"] in ((True, "key-master") if "native_source" in row else ("unknown",))
        and (row["write"] is None or row["write"].startswith("flPackage."))
        for row in STRUCTURED_ROUTES.values()
    )
    assert not NATIVE_CAPABILITIES["glyph.externalChangeNotifications"]["supported"]
    assert not NATIVE_CAPABILITIES["info.exactSingleUndo"]["supported"]


def test_generator_closes_multiple_owners_by_identity_without_naked_equality():
    from fontlab_fontport.memory import UFOBackend

    generator = ObjectGenerator(backend_factory=UFOBackend)
    first, _ = generator("font")
    second, _ = generator("font")
    generator.close()
    assert first._closed and second._closed and not generator.owned


@pytest.mark.parametrize("family", FAMILIES)
def test_attached_factory_exercises_actual_live_families_over_ufo_backend(family):
    from fontlab_fontport.memory import UFOBackend

    generator = ObjectGenerator(backend_factory=UFOBackend, native_attached=True)
    with generator_context(generator):
        if family == "image":
            with pytest.raises(UnsupportedCapability, match=r"glyph.image"):
                generator(family)
        else:
            result, parents = generator(family)
            assert result is not None
            owner = generator.owned[0]
            assert owner is result if family == "font" else owner in parents
    assert not generator.owned
