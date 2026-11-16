# this_file: tests/native_drivers/round10_lifecycle_steps.py
"""27.7 external closure of an owned font; cached public reads must be stale."""


def phases():
    yield (
        "lifecycle-cache",
        "cached_font=font\ncached_glyph=font['A']\ncached_info=font.info\ncached_layer=font.defaultLayer\nsaved_path=str(Path(output)/'lifecycle.vfj')\nresult={'glyph':cached_glyph.name,'path':saved_path}",
    )
    yield "lifecycle-save", "font.save(saved_path)\nresult={'path':saved_path}"
    yield (
        "lifecycle-external-close",
        "fontpr.call('close_font',font_id=backend.font_id,save=False)\nresult={'closed':True}",
    )
    yield (
        "lifecycle-stale-reads",
        "from fontlab_fontport.errors import StaleObjectError\nobserved=[]\nfor name,read in [('font',lambda:cached_font.keys()),('glyph',lambda:cached_glyph.width),('layer',lambda:cached_layer.name),('info',lambda:cached_info.familyName)]:\n    try:\n        read()\n        observed.append({'object':name,'stale':False})\n    except StaleObjectError as error:\n        observed.append({'object':name,'stale':True,'message':str(error)})\nresult={'equal':all(row['stale'] for row in observed),'reads':observed}",
    )
    yield (
        "lifecycle-reopen",
        "font=environment.OpenFont(saved_path)\nbackend=font._backend\nowned_ids.add(backend.font_id)\nresult={'equal':font.path==saved_path,'path':font.path}",
    )
