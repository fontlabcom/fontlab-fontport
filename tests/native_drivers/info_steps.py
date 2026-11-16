# this_file: tests/native_drivers/info_steps.py
"""B05 per-field edit, first Undo/Redo and VFJ persistence; one operation per call."""

VALUES = {
    "openTypeNameDesigner": "Owned Ω\nDesigner",
    "openTypeOS2Panose": [2, 0, 5, 3, 0, 0, 0, 0, 0, 0],
    "openTypeOS2WidthClass": 5,
    "openTypeOS2WeightClass": 400,
    "openTypeNameRecords": [
        {
            "nameID": 256,
            "platformID": 3,
            "encodingID": 1,
            "languageID": 1033,
            "string": "Owned Ω",
        }
    ],
    "postscriptStemSnapH": [20.5, 80],
    "postscriptStemSnapV": [70],
}


def info_phases():
    for field, value in VALUES.items():
        prefix = "info-" + field
        yield (
            prefix + "-baseline",
            f"field = {field!r}\nrequested = {value!r}\nbefore = backend.get_info(field)\nif before == requested:\n    requested = different_info_value(requested)",
        )
        yield (
            prefix + "-apply",
            "font.info.apply({field: requested},require_single_undo=False)",
        )
        yield (
            prefix + "-readback",
            "assert backend.get_info(field) == requested\nresult = {field: backend.get_info(field)}",
        )
        yield prefix + "-undo", "action('actionUndo')"
        yield prefix + "-undo-readback", "assert backend.get_info(field) == before"
        yield prefix + "-redo", "action('actionRedo')"
        yield prefix + "-redo-readback", "assert backend.get_info(field) == requested"
        yield prefix + "-save", f"font.save(str(Path(output) / {prefix + '.vfj'!r}))"
        yield prefix + "-close", "font.close()"
        yield (
            prefix + "-reopen",
            f"font = environment.OpenFont(str(Path(output) / {prefix + '.vfj'!r}))\nbackend = font._backend",
        )
        yield (
            prefix + "-reopen-readback",
            "assert backend.get_info(field) == requested\nresult = {field: backend.get_info(field)}",
        )
