# this_file: tests/native_drivers/round10_world_steps.py
"""27.6 persistent world callbacks plus original examples on an owned fixture."""


def phases(example_names):
    yield (
        "world-register",
        "from fontParts import world\nfrom fontlab_fontport.world import register,unregister\nworld_previous=dict(world.dispatcher._registry)\nregistration=register(environment)\nresult={'equal':world.CurrentFont() is font,'all_ids':[f._backend.font_id for f in world.AllFonts()]}",
    )
    yield (
        "world-selection",
        "selection_error=None\ntry:\n    world.CurrentGlyph()\nexcept UnsupportedCapability as error:\n    selection_error={'capability':error.capability,'reason':str(error)}\nresult={'equal':selection_error is not None and selection_error['capability']=='world.selection','refusal':selection_error}",
    )
    yield (
        "world-new",
        "world_new=world.NewFont()\nowned_ids.add(world_new._backend.font_id)\nresult={'equal':world_new._backend.owns_document,'id':world_new._backend.font_id}",
    )
    yield "world-new-close", "world_new.close()\nresult={'closed':True}"
    yield (
        "world-open",
        "world_opened=world.OpenFont(str(Path(output)/'world-open.vfj'))\nowned_ids.add(world_opened._backend.font_id)\nresult={'equal':world_opened._backend.owns_document,'id':world_opened._backend.font_id}",
    )
    yield "world-open-close", "world_opened.close()\nresult={'closed':True}"
    yield (
        "world-activate-owned",
        "fontpr.call('set_active_font',font_id=backend.font_id)\nresult={'equal':world.CurrentFont() is font,'owned':font._backend.owns_document}",
    )
    for name in example_names:
        yield (
            "example-" + name,
            f"import importlib\nexample=importlib.import_module({name!r})\nresult=example.run(font)",
        )
    yield (
        "world-unregister",
        "unregister()\nresult={'equal':world.dispatcher._registry==world_previous}",
    )
