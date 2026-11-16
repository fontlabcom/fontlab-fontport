# this_file: tests/test_world.py
"""Explicit world dispatch, identity, safe ownership and stale documents."""

import pytest
from fontParts import world
from test_live import Backend

from fontlab_fontport.world import FontWorld, register


class Host:
    def __init__(self):
        self.backends = {1: Backend(), 2: Backend()}
        self.active = 1

    def font_ids(self):
        return tuple(self.backends)

    def current_font_id(self):
        return self.active

    def backend(self, identifier, *, owned):
        backend = self.backends[identifier]
        backend.owned = owned
        return backend

    def open_font(self, path):
        identifier = max(self.backends, default=0) + 1
        self.backends[identifier] = Backend()
        return identifier

    def new_font(self, family, style):
        return self.open_font(None)


def test_world_when_open_current_all_then_identity_and_ownership(tmp_path):
    host = Host()
    env = FontWorld(host)
    font = env.CurrentFont()
    assert env.AllFonts()[0] is font
    opened = env.OpenFont(str(tmp_path / "owned.vfj"))
    assert opened._backend.owned and env.AllFonts()[2] is opened
    assert not font._backend.owned, "existing documents must stay borrowed"
    new = env.NewFont(familyName="Ω", styleName="Regular")
    assert new._backend.owned and env.AllFonts()[-1] is new
    opened.close()
    assert env.AllFonts()[2] is not opened, "closing a binding must not return it again"
    del host.backends[1]
    env.AllFonts()
    with pytest.raises(RuntimeError, match="closed"):
        font.keys()
    host.active = None
    assert env.CurrentFont() is None


def test_world_when_registered_then_restores_upstream_even_after_error(tmp_path):
    env = FontWorld(Host())
    before = (
        world.dispatcher["CurrentFont"]
        if world.dispatcher._registry["CurrentFont"]
        else None
    )
    originals = dict(world.dispatcher._registry)
    with pytest.raises(ValueError, match="sentinel"), register(env):
        assert world.CurrentFont() is env.CurrentFont()
        assert world.AllFonts()[0] is env.CurrentFont()
        assert world.NewFont()._backend.owned
        assert world.OpenFont(str(tmp_path / "owned.vfj"))._backend.owned
        assert world.RFont(env.CurrentFont()) is env.CurrentFont()
        assert world.RFont()._backend.owned
        with register(FontWorld(Host())):
            assert world.CurrentFont() is not env.CurrentFont()
        assert world.CurrentFont() is env.CurrentFont()
        raise ValueError("sentinel")
    assert world.dispatcher._registry == originals
    assert world.dispatcher._registry["CurrentFont"] is before


def test_world_when_hidden_interface_or_invalid_name_then_no_native_calls():
    env = FontWorld(Host())
    with pytest.raises(NotImplementedError, match="showInterface"):
        env.OpenFont("owned.vfj", showInterface=False)
    with pytest.raises(NotImplementedError, match="showInterface"):
        env.NewFont(showInterface=False)
    with pytest.raises(TypeError):
        env.NewFont(familyName=12)
    assert len(env.AllFonts()) == 2


def test_world_invalidates_external_closed_backends_without_refreshing_them():
    from fontlab_fontport.errors import StaleObjectError
    from fontlab_fontport.memory import UFOBackend

    host = Host()
    backend = UFOBackend()
    host.backends = {1: backend}
    environment = FontWorld(host)
    font = environment.CurrentFont()
    backend.close()
    host.backends.clear()
    host.active = None
    assert not environment.AllFonts()
    with pytest.raises(StaleObjectError):
        font.keys()


def test_world_discards_owned_allocation_when_backend_wrapping_fails():
    class BrokenHost(Host):
        def backend(self, identifier, *, owned):
            raise ValueError("wrapper failed")

        def close_font(self, identifier):
            self.backends.pop(identifier)

    host = BrokenHost()
    environment = FontWorld(host)
    with pytest.raises(ValueError, match="wrapper failed"):
        environment.NewFont()
    assert set(host.backends) == {1, 2}


def test_native_application_when_open_new_list_then_document_identity(
    monkeypatch, tmp_path
):
    import sys
    from types import SimpleNamespace

    from fontlab_fontport.application import NativeApplication

    rows, calls = [], []

    def call(tool, **kwargs):
        calls.append((tool, kwargs))
        if tool == "list_fonts":
            return {"fonts": list(rows)}
        if tool == "get_active_font":
            return rows[-1]
        if tool in ("new_font", "open_font"):
            rows.append({"id": len(rows) + 1})
            return {"status": "ok"}
        raise AssertionError(tool)

    monkeypatch.setitem(sys.modules, "fontpr", SimpleNamespace(call=call))
    app = NativeApplication()
    assert app.current_font_id() is None
    assert app.new_font("Ω", "Italic") == 1 and app.current_font_id() == 1
    source = tmp_path / "owned.vfj"
    source.write_text("owned")
    assert app.open_font(str(source)) == 2
    assert ("open_font", {"path": str(source.resolve())}) in calls
    before = list(calls)
    with pytest.raises(FileNotFoundError):
        app.open_font(str(tmp_path / "missing.vfj"))
    assert calls == before, "missing input never reaches the host"
