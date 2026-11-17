# this_file: tests/test_package_boundaries.py
"""Only native guards and the deprecated feature shim may lazily import App."""

import ast
import hashlib
import subprocess
import tarfile
import tomllib
from email.parser import BytesParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STUB_SHA256 = "bdb98c7c23f9904e5f4c59332b0bbd8723f18e33c7bbfea1c526c9b0b0b9cb50"


def canonical_stub() -> bytes | None:
    """instamix's own stub bytes, from the package or a sibling checkout."""
    try:
        from fontlab_instamix import stub
    except ImportError:
        sibling = ROOT.parent / "fontlab-python-instamix" / "stub" / "install.vfpy"
        return sibling.read_bytes() if sibling.is_file() else None
    return stub.text().encode("utf-8")


SRC = ROOT / "src" / "fontlab_fontport"
ALLOWED = {
    "host.py": "fontlabapp.core.edit_guards",
    "feature_blocks.py": "fontlabapp.fontui.feature_blocks",
}


def app_imports(source):
    """Return App import names and whether each is inside a function."""
    tree = ast.parse(source)
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    found = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names = [node.module or ""]
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else getattr(node.func, "attr", "")
            )
            if name in {"__import__", "import_module"} and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    names = [value.value]
        ancestor = parents.get(node)
        lazy = False
        while ancestor is not None:
            lazy |= isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef))
            ancestor = parents.get(ancestor)
        found += [(name, lazy) for name in names if name.split(".")[0] == "fontlabapp"]
    return found


@pytest.mark.parametrize(
    "source,expected",
    [
        ("import fontlabapp.core.edit_guards", [("fontlabapp.core.edit_guards", False)]),
        ("def f():\n    from fontlabapp.core import scripting", [("fontlabapp.core", True)]),
        (
            "def f():\n    import_module('fontlabapp.fontui.feature_blocks')",
            [("fontlabapp.fontui.feature_blocks", True)],
        ),
        ("__import__('fontlabapp.core.scripting')", [("fontlabapp.core.scripting", False)]),
        ("'import fontlabapp'", []),
        ("from . import host", []),
    ],
)
def test_app_imports_when_parsed_then_scope_and_literal_imports_are_detected(
    source, expected
):
    assert app_imports(source) == expected


def test_source_when_parsed_then_only_optional_lazy_app_imports_exist():
    files = sorted(SRC.rglob("*.py"))
    assert files, "Fontport sources must exist"
    offenders = {
        str(path.relative_to(SRC)): hits
        for path in files
        if (
            hits := [
                (name, lazy)
                for name, lazy in app_imports(path.read_text())
                if name != ALLOWED.get(str(path.relative_to(SRC))) or not lazy
            ]
        )
    }
    assert not offenders, f"Unexpected or eager App imports: {offenders}"


def test_pyproject_when_read_then_app_is_only_the_fontlab_extra():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["optional-dependencies"]["fontlab"] == [
        "fontlab-fontlabapp>=1.2.0"
    ]
    requirements = list(project["dependencies"])
    for name, extra in project["optional-dependencies"].items():
        if name != "fontlab":
            requirements += extra
    assert not [
        r
        for r in requirements
        if r.lower().replace("_", "-").startswith("fontlab-fontlabapp")
    ]


def test_installer_when_read_then_app_floor_matches_fontlab_extra():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    requirements = config["tool"]["fontlab-install"]["dependencies"]
    extra = config["project"]["optional-dependencies"]["fontlab"]
    (floor,) = [r for r in extra if r.startswith("fontlab-fontlabapp")]
    assert floor in requirements, (
        "installer deps must repeat the fontlab extra's App floor"
    )


def test_sdist_when_built_then_installer_is_the_instamix_stub(tmp_path):
    """The source release carries the unchanged stub, its table and a version."""
    output = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(output), str(ROOT)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    archives = list(output.glob("*.tar.gz"))
    assert len(archives) == 1
    project = tmp_path / "source"
    project.mkdir()
    with tarfile.open(archives[0]) as archive:
        prefix = archive.getnames()[0].split("/")[0] + "/"
        for name in ("install.vfpy", "PKG-INFO", "pyproject.toml"):
            payload = archive.extractfile(prefix + name).read()
            (project / name).write_bytes(payload)
    installer = (project / "install.vfpy").read_text(encoding="utf-8")
    assert installer == (ROOT / "install.vfpy").read_text(encoding="utf-8")
    assert installer.startswith("#FLM: Install into FontLab with fontlab-instamix\n")
    assert hashlib.sha256(installer.encode("utf-8")).hexdigest() == STUB_SHA256
    assert "bootstrap.install_project(__file__)" in installer, "stub must hand off to instamix"
    canonical = canonical_stub()
    if canonical is not None:
        assert installer.encode("utf-8") == canonical, "install.vfpy must match instamix's canonical stub"
    metadata = BytesParser().parsebytes((project / "PKG-INFO").read_bytes())
    config = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["Name"] == config["project"]["name"]
    assert metadata["Version"], "instamix reads the version from PKG-INFO in an sdist"
    assert config["tool"]["fontlab-install"]["id"] == "com.fontlab.fontport"
