# this_file: tests/test_native_import.py
"""UFO / designspace import wrappers over the native opener (fake application)."""

import pytest

from fontlab_fontport.native_import import import_designspace, import_ufo_native


class FakeApplication:
    def __init__(self):
        self.opened = []

    def open_font(self, path):
        self.opened.append(path)
        return 7

    def backend(self, identifier, *, owned):
        return ("backend", identifier, owned)


def test_import_ufo_when_directory_then_native_open_and_owned_backend(tmp_path):
    ufo = tmp_path / "A.ufo"
    ufo.mkdir()
    app = FakeApplication()
    assert import_ufo_native(ufo, app) == ("backend", 7, True)
    assert app.opened == [str(ufo.resolve())], "exactly the native open_font path"


def test_import_designspace_when_file_then_native_open_and_owned_backend(tmp_path):
    space = tmp_path / "A.designspace"
    space.write_text("<designspace/>")
    app = FakeApplication()
    assert import_designspace(space, app) == ("backend", 7, True)
    assert app.opened == [str(space.resolve())]


def test_import_when_wrong_suffix_or_kind_then_refused_without_opening(tmp_path):
    (tmp_path / "A.ufo").write_text("a file, not a package")
    (tmp_path / "B.designspace").mkdir()
    (tmp_path / "C.txt").write_text("x")
    app = FakeApplication()
    with pytest.raises(ValueError, match="directory"):
        import_ufo_native(tmp_path / "A.ufo", app)
    with pytest.raises(ValueError, match="file"):
        import_designspace(tmp_path / "B.designspace", app)
    with pytest.raises(ValueError, match=r"\.ufo"):
        import_ufo_native(tmp_path / "C.txt", app)
    with pytest.raises(ValueError, match=r"\.designspace"):
        import_designspace(tmp_path / "C.txt", app)
    assert app.opened == []


def test_import_when_missing_or_relative_then_refused(tmp_path):
    app = FakeApplication()
    with pytest.raises(FileNotFoundError):
        import_designspace(tmp_path / "gone.designspace", app)
    with pytest.raises(ValueError, match="absolute"):
        import_ufo_native("rel.ufo", app)
    assert app.opened == []
