# this_file: tests/native_drivers/round10_glyph_steps.py
"""27.1 edits/refusals, payload equality after separate Undo/Redo/save calls."""

from round10_common_steps import mutation_phases


def phases():
    yield from mutation_phases(
        "glyph-create", "font.newGlyph('fontport_created')", name="fontport_created", history_scope="package"
    )
    operations = {
        "contours": "with font.edit_glyph(probe_name,undo_name='Owned triangle') as g:\n    p=g.getPen()\n    p.moveTo((0,0))\n    p.lineTo((100,0))\n    p.lineTo((0,100))\n    p.closePath()",
        "live-pen": "p=font[probe_name].getPen()\np.moveTo((20,20))\np.lineTo((90,20))\np.lineTo((20,90))\np.closePath()",
        "appendPoint": "font[probe_name].contours[0].appendPoint((30,40),'line')",
        "width": "font[probe_name].width=777",
        "clearContours": "with font.edit_glyph(probe_name,undo_name='Owned clear contours') as g:\n    g.clearContours()",
        "integral-anchor": "font[probe_name].appendAnchor('owned_top',(20,700))",
        "fractional-anchor": "font[probe_name].appendAnchor('owned_fraction',(20.5,700.25))",
        "guideline": "font[probe_name].appendGuideline((0,20),0,name='owned guide')",
        "component-add": "font[probe_name].appendComponent('A',offset=(10,20))",
        "component-transform": "font[probe_name].components[0].offset=(30,40)",
        "component-replace": "font[probe_name].components[0].baseGlyph='V'",
        "glyph-rename": "font[probe_name].name='fontport_renamed'",
        "unicode-name": "font.newGlyph('Ω')",
        "glyph-delete": "font.removeGlyph(probe_name)",
        "layer-create": "font.newLayer('owned_sketch')",
        "layer-rename": "font.defaultLayer.name='owned_renamed'",
        "layer-delete": "font.removeLayer(font.defaultLayerName)",
    }
    refusals = {
        "fractional-anchor": "glyph.anchor.precision",
        "guideline": "glyph.guidelines",
        "component-replace": "glyph.geometry",
        "glyph-rename": "glyph.rename",
        "unicode-name": "glyph.name.unicodeVfj",
        "glyph-delete": "glyph.delete.master",
        "layer-create": "layer.create",
        "layer-rename": "layer.rename",
        "layer-delete": "layer.delete",
    }
    for name, code in operations.items():
        yield from mutation_phases(
            "glyph-" + name, code, expected_capability=refusals.get(name),
            require_geometry_change=name in {"contours", "live-pen", "appendPoint", "clearContours", "component-add", "component-transform"}
        )


def hinted_phases(names):
    """One candidate per RPC; C4 chooses a hinted GetGo fixture for positive proof."""
    yield "hinted-search-start", "hinted_name=None\nresult={'ready':True}"
    for name in names:
        yield (
            "hinted-search-" + name,
            f"candidate={name!r}\nif hinted_name is None:\n    target=backend._target(candidate,backend.default_layer())[2]\n    if target.hasHints or target.hasTTData or target.hasTTH:\n        hinted_name=candidate\n    target=None\nresult={{'candidate':candidate,'hinted':hinted_name}}",
        )
    yield (
        "hinted-baseline",
        "hinted_before=payload(hinted_name) if hinted_name else None\nhinted_history=history(hinted_name) if hinted_name else history()\nresult={'prerequisite':hinted_name is not None,'name':hinted_name,'payload':hinted_before,'history':hinted_history}",
    )
    yield (
        "hinted-refusal",
        "refusal=None\nif hinted_name is not None:\n    try:\n        with font.edit_glyph(hinted_name,undo_name='Owned hinted refusal') as g:\n            p=g.getPen()\n            p.moveTo((1,2))\n            p.lineTo((7,2))\n            p.lineTo((1,9))\n            p.closePath()\n    except UnsupportedCapability as error:\n        refusal={'capability':error.capability,'reason':str(error)}\nresult={'prerequisite':hinted_name is not None,'equal':refusal is not None and refusal['capability']=='glyph.geometry' and history(hinted_name)==hinted_history,'refusal':refusal}",
    )
    yield (
        "hinted-unchanged",
        "result={'equal':hinted_name is not None and payload_equal(payload(hinted_name),hinted_before) and history(hinted_name)==hinted_history,'payload':payload(hinted_name) if hinted_name else None}",
    )
