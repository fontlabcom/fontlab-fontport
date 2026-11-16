# this_file: tests/native_drivers/round10_history.py
"""Observe the glyph history graph used by native Undo, not package-only state."""


def glyph_history(backend, name):
    glyph = backend._package().findName(name)
    if glyph is None or glyph.isNull:
        return {"index": 0, "rows": [], "objects": []}
    objects = [("glyph", glyph)]
    for layer in glyph.layers:
        objects.append(
            ("layer:" + layer.name if hasattr(layer, "name") else "layer", layer)
        )
        for shape in layer.shapes:
            objects.append(("shape", shape))
            objects.append(("shapeData", shape.shapeData))
    observed = []
    rows = set()
    index = 0
    for kind, obj in objects:
        current = int(obj.currentHistoryState())
        states = [int(v) for v in obj.historyStates(True) if int(v) > 0]
        rows.update(states)
        index = max(index, current)
        observed.append({"kind": kind, "index": current, "rows": states})
    return {"index": index, "rows": sorted(rows), "objects": observed}


def package_history(backend):
    """Creation belongs to package history, even when glyph history is empty."""
    package = backend._package()
    index = int(package.currentHistoryState())
    rows = sorted({int(v) for v in package.historyStates(True) if int(v) > 0})
    return {"index": index, "rows": rows, "objects": [{"kind": "package", "index": index, "rows": rows}]}
