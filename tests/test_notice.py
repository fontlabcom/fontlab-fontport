# this_file: tests/test_notice.py
"""The relocated App code must keep its provenance in built distributions."""

import tomllib
from pathlib import Path


def test_notice_when_packages_built_then_included_in_wheel_and_sdist() -> None:
    root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((root / "pyproject.toml").read_text())
    assert "NOTICE" in config["project"]["license-files"], "wheel must carry provenance"
    assert "NOTICE" in config["tool"]["hatch"]["build"]["targets"]["sdist"]["only-include"], "sdist must carry provenance"
    notice = (root / "NOTICE").read_text()
    assert "2022 Adam" in notice and "BSD-3-Clause" in notice
    assert "feature_blocks.py" in notice and "Apache License 2.0" in notice
