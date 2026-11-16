# this_file: tests/native_drivers/round10_pen_steps.py
"""27.2/27.3 one live glyph digest/bounds/FEA/designspace check per call."""


def phases(names, expected_digests=None, flatten_digest=None):
    yield (
        "pens-setup",
        "from fontlab_fontport.recipes import digest,bounds,control_bounds,flatten,parse_features\nfrom round10_pen_steps import bounds_equal\nfrom fontlab_fontport.designspace import Designspace\nresult={'imported':True}",
    )
    for name in names:
        expected = (
            f"expected_digest={expected_digests[name]!r}"
            if expected_digests is not None
            else f"expected_digest=digest(backend.read_glyph({name!r},backend.default_layer()))"
        )
        yield (
            "pens-" + name,
            f"g=font[{name!r}]\n{expected}\nnative=backend._target({name!r},backend.default_layer())[2].boundingBox\nnative_bounds=(native.left(),native.top(),native.right(),native.bottom()) if native is not None else None\nif native is not None and native.isNull() and not g.contours and not g.components:\n    native_bounds=None\nresult={{'name':{name!r},'digest_equal':digest(g)==expected_digest,'live_digest':digest(g),'ufo_digest':expected_digest,'bounds':bounds(g,font),'native_bounds':native_bounds,'control_bounds':control_bounds(g,font),'bounds_equal':bounds_equal(control_bounds(g,font),native_bounds)}}",
        )
    yield (
        "pens-designspace",
        "designspace=Designspace.from_native(backend)\nresult={'axes':[(a.name,a.tag,a.minimum,a.default,a.maximum,a.map) for a in designspace.axes],'sources':[(s.name,s.coordinates) for s in designspace.sources],'native_axes':[(a.name,a.tag,a.minimal,a.default,a.maximum,dict(a.map)) for a in backend._package().axes],'native_masters':list(backend._package().masters)}",
    )
    yield (
        "pens-features-read",
        "fea_text=font.features.text\nfea_classes=dict(font.groups)\nresult={'characters':len(fea_text),'classes':len(fea_classes)}",
    )
    yield (
        "pens-fealib",
        "document=parse_features(fea_text,font.keys(),classes=fea_classes)\nresult={'parsed':True,'statements':len(document.statements)}",
    )
    yield (
        "pens-flatten-baseline",
        "probe_name='fontport_flat'\nbefore=payload(probe_name)\nbefore_geometry=geometry_snapshot(before)\nhistory_before=history(probe_name)\nhistory_rows_before=len(glyph_history(backend,probe_name)['rows'])\nresult={'payload':before,'history':history_before}",
    )
    yield "pens-flatten", "result=edit_receipt(\"flatten(font,'A','fontport_flat')\")"
    yield (
        "pens-flatten-read",
        f"after=payload(probe_name)\nafter_geometry=geometry_snapshot(after)\nactual_digest=digest(font[probe_name])\nresult={{'payload':after,'history_before':history_before,'history_after':history(probe_name),'digest_equal':None if {flatten_digest is None!r} or not supported else actual_digest=={flatten_digest!r},'observed_digest':actual_digest,'expected_digest':{flatten_digest!r}}}",
    )
    yield (
        "pens-flatten-undo",
        "result=action('actionUndo') if supported else {'skipped':'refused'}",
    )
    yield (
        "pens-flatten-undo-read",
        "observed=payload(probe_name)\nresult={'equal':payload_equal(observed,before),'payload':observed,'expected':before,**geometry_receipt(observed,before_geometry)}",
    )
    yield (
        "pens-flatten-redo",
        "result=action('actionRedo') if supported else {'skipped':'refused'}",
    )
    yield (
        "pens-flatten-redo-read",
        "observed=payload(probe_name)\nresult={'equal':payload_equal(observed,after),'payload':observed,'expected':after,**geometry_receipt(observed,after_geometry)}",
    )


def bounds_equal(left, right):
    """Same y convention, tolerate only numeric extrema drift (1e-6 units)."""
    from math import isclose

    if left is None or right is None:
        return left is right
    return len(left) == len(right) and all(
        isclose(a, b, rel_tol=1e-9, abs_tol=1e-6)
        for a, b in zip(left, right, strict=True)
    )
