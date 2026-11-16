# this_file: tests/test_migrate_app_paths.py
"""Migration boundaries and repeatability, independent of native FontLab."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def migration(tmp_path):
    """Use an owned alias oracle; never inspect the parent-owned sibling checkout."""
    path = Path(__file__).resolve().parents[1] / "tools/migrate_app_paths.py"
    spec = importlib.util.spec_from_file_location("migrate_app_paths", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path / "fontport"
    module.ROOT.mkdir()
    oracle = tmp_path / "fontlab-fontlabapp/src/fontlabapp/_legacy.py"
    oracle.parent.mkdir(parents=True)
    oracle.write_text("ALIASES = " + repr({
        "fontlabapp.scripting": "fontlabapp.core.scripting",
        "fontlabapp.masters": "fontlabapp.masters.inspect.model",
        "fontlabapp.draft_signals": "fontlabapp.core.signals.scope",
        "fontlabapp.glyph_catalog": "fontlabapp.glyphs.catalog.model",
        "fontlabapp.glyph_tree": "fontlabapp.glyphs.tree.model",
    }) + "\n")
    return module


def test_rewrite_when_paths_overlap_then_preserve_boundaries_and_bindings(migration):
    mapping = migration.load_mapping()
    source = '''from fly.ap import scripting as api
from fontlabapp import masters, draft_signals
from fontlabapp.masters.inspect import model
import fly.ap.glyph_catalog as catalog
monkeypatch.setattr("fontlabapp.scripting.capture", callback)
mock.patch('fly.ap.scripting.capture')
importlib.import_module("fontlab_remopy.control")
fly.fp.feature_blocks.read_feature_blocks(font)
fontlab_fontport.ui.fontinfo
fontlabapp.scripting_extra other.fontlabapp.scripting fly.ap.scripting_extra
fontlabapp.masters.inspect.model.capture
{"api_module": "glyph_tree", "unrelated": "glyph_tree"}
assert row["api_module"] == "glyph_tree"
'''
    expected = '''import fly.ap.core.scripting as api
import fontlabapp.masters.inspect.model as masters
import fontlabapp.core.signals.scope as draft_signals
from fontlabapp.masters.inspect import model
import fly.ap.glyphs.catalog.model as catalog
monkeypatch.setattr("fontlabapp.core.scripting.capture", callback)
mock.patch('fly.ap.core.scripting.capture')
importlib.import_module("fontlab_remopy.client")
fly.ap.fontui.feature_blocks.read_feature_blocks(font)
fontlabapp.fontui.fontinfo
fontlabapp.scripting_extra other.fontlabapp.scripting fly.ap.scripting_extra
fontlabapp.masters.inspect.model.capture
{"api_module": "glyphs.tree.model", "unrelated": "glyph_tree"}
assert row["api_module"] == "glyphs.tree.model"
'''
    rewritten = migration.rewrite(source, mapping)
    assert rewritten == expected, "Change only complete module paths; retain imported local names"
    assert migration.rewrite(rewritten, mapping) == rewritten, "Canonical paths must be stable"


def test_migrate_when_archive_present_then_leave_it_untouched(tmp_path, migration):
    for name in ("src/current.py", "src/_reference/archived.py"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("import fly.ap.scripting\n")
    assert migration.migrate(tmp_path, migration.load_mapping()) == ["src/current.py"]
    assert (tmp_path / "src/_reference/archived.py").read_text() == "import fly.ap.scripting\n"



def test_migrate_when_docs_move_then_rewrites_authored_only_and_keeps_history(migration):
    root = migration.ROOT
    names = ["src_docs/md/guides/current.md", "src_docs/md/guides/INTEGRATION.md", "docs/index.html", "README.md", "src/_reference/old.py", "src/.private.py", "src/opaque.bin"]
    for name in names:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("import fly.ap.scripting\n")
    (root / "src/link.py").symlink_to(root / "src_docs/md/guides/current.md")
    mapping = migration.load_mapping()
    expected = ["src_docs/md/guides/current.md"]
    assert migration.migrate(root, mapping, check=True) == expected
    assert (root / expected[0]).read_text() == "import fly.ap.scripting\n"
    assert migration.migrate(root, mapping) == expected
    assert (root / expected[0]).read_text() == "import fly.ap.core.scripting\n"
    for name in names[1:]:
        assert (root / name).read_text() == "import fly.ap.scripting\n"
    assert migration.migrate(root, mapping) == []


def test_cli_when_check_or_apply_then_uses_owned_oracle_and_refuses_implicit_write(migration):
    import os
    root = migration.ROOT
    tool = root / "tools/migrate_app_paths.py"
    tool.parent.mkdir()
    source = Path(__file__).resolve().parents[1] / "tools/migrate_app_paths.py"
    tool.write_bytes(source.read_bytes())
    document = root / "src_docs/md/current.md"
    document.parent.mkdir(parents=True)
    document.write_text("from fly.ap import scripting as api\n")
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", PYTHONDONTWRITEBYTECODE="1")
    check = subprocess.run([sys.executable, "-B", str(tool), "--check"], env=env, capture_output=True, text=True, timeout=20)
    assert check.returncode == 1 and "src_docs/md/current.md" in check.stdout
    assert document.read_text() == "from fly.ap import scripting as api\n"
    apply = subprocess.run([sys.executable, "-B", str(tool)], env=env, capture_output=True, text=True, timeout=20)
    assert apply.returncode == 0, apply.stderr
    assert document.read_text() == "import fly.ap.core.scripting as api\n"
