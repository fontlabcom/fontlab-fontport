# this_file: tests/test_designspace.py
"""Actual upstream source/instance locations and mapped design coordinates."""

from types import SimpleNamespace

import pytest
from fontTools.designspaceLib import DesignSpaceDocument

from fontlab_fontport.designspace import Designspace


def document(tmp_path):
    doc = DesignSpaceDocument()
    doc.addAxisDescriptor(
        name="Weight",
        tag="wght",
        minimum=100,
        default=400,
        maximum=900,
        map=[(100, 0), (400, 50), (900, 100)],
    )
    doc.addSourceDescriptor(
        name="Regular",
        path=str(tmp_path / "regular.ufo"),
        designLocation={"Weight": 50},
    )
    doc.addSourceDescriptor(
        name="Bold", path=str(tmp_path / "missing.ufo"), designLocation={"Weight": 100}
    )
    doc.addInstanceDescriptor(name="Medium", userLocation={"Weight": 500})
    (tmp_path / "regular.ufo").mkdir()
    return doc


def test_designspace_when_reopened_then_real_axes_sources_instances_and_reset(tmp_path):
    path = tmp_path / "sample.designspace"
    document(tmp_path).write(path)
    model = Designspace.open(path)
    assert model.defaults() == {"Weight": 400}
    assert model.location({"Weight": 100}) == {"Weight": 100}
    assert model.location({"Weight": 900}) == {"Weight": 900}
    assert model.sources[0].kind == "source" and model.sources[0].available
    assert dict(model.sources[0].coordinates) == {"Weight": 400}
    assert not model.sources[1].available and model.sources[1].reason
    assert dict(model.instances[0].coordinates) == {"Weight": 500}
    assert model.instance({"Weight": 400}).kind == "instance", (
        "location alone is never a source identity"
    )
    with pytest.raises(ValueError, match="Weight"):
        model.location({"Weight": 901})
    with pytest.raises(ValueError, match="Unknown"):
        model.location({"Width": 100})


def test_designspace_when_native_snapshot_then_actual_master_axis_and_instance():
    package = SimpleNamespace(
        axes=[
            SimpleNamespace(
                name="Weight",
                shortName="wt",
                tag="wght",
                minimal=100,
                default=400,
                maximum=900,
                map={0: 100, 50: 400, 100: 900},
            )
        ],
        masters=("Regular", "Bold"),
        location=lambda name: {"wt": {"Regular": 50, "Bold": 100}[name]},
        instances=[SimpleNamespace(name="Medium", location={"wt": 60})],
    )
    model = Designspace.from_native(SimpleNamespace(_package=lambda: package))
    assert [entry.name for entry in model.sources] == ["Regular", "Bold"]
    assert dict(model.sources[1].coordinates) == {"Weight": 900}
    assert model.sources[0].available and model.instances[0].kind == "instance"
    assert dict(model.instances[0].coordinates) == {"Weight": 500}


def test_designspace_when_invalid_or_unavailable_axis_forms_then_refused(tmp_path):
    doc = document(tmp_path)
    doc.axes[0].default = float("nan")
    with pytest.raises(ValueError, match="finite"):
        Designspace(doc)
    doc.axes[0].default = 1000
    with pytest.raises(ValueError):
        Designspace(doc)
    discrete = DesignSpaceDocument()
    discrete.addAxisDescriptor(name="Italic", tag="ital", values=[0, 1], default=0)
    with pytest.raises(NotImplementedError, match="Discrete"):
        Designspace(discrete)
