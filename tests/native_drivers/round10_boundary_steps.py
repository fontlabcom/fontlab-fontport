# this_file: tests/native_drivers/round10_boundary_steps.py
"""30.3/30.4/31.6 explicit capability and refusal receipts, no fake native pass."""


def phases():
    yield (
        "capability-catalog",
        "from fontlab_fontport.capabilities import STRUCTURED_ROUTES\nresult={'capabilities':backend.capabilities(),'structured_routes':STRUCTURED_ROUTES}",
    )
    yield (
        "both-fixture-member",
        "both_member='fontport_owned_both_member'\nfont.newGlyph(both_member)\nresult={'created':both_member}",
    )
    yield (
        "both-fixture-setup",
        "both_fixture='fontport_owned_both'\nnative_kern=backend._package().kerning()\nif both_fixture in dict(native_kern.groups.asDict()):\n    raise ValueError('Owned both-sided fixture name already exists')\ncreated_both=native_kern.addGroup(both_fixture,[both_member],kernMode='KernBothSide')\nfontlab.flItems.notifyChangesApplied('Owned both-sided fixture',[backend._package(),backend._package().kerningContainer()])\nresult={'prerequisite':bool(created_both),'name':both_fixture}",
    )
    yield (
        "both-sided-baseline",
        "both_values=backend.get_groups()\nboth_history=history()\nboth_names=[name for name,(members,mode) in backend._package().kerning().groups.items() if mode=='KernBothSide']\nresult={'prerequisite':bool(both_names),'native_both_sided':both_names,'history':both_history}",
    )
    yield (
        "both-sided-refusal",
        "from fontlab_fontport.native_groups import read_groups\nvalues,routes=read_groups(backend._package())\nkey=next((name for name,(kind,native) in routes.items() if kind=='kerning' and native in both_names and name.startswith('public.kern2.')),None)\nrefusal=None\nif key is not None:\n    values[key]=()\n    try:\n        backend.set_groups(values)\n    except UnsupportedCapability as error:\n        refusal={'capability':error.capability,'reason':str(error)}\nresult={'equal':refusal is not None and refusal['capability']=='groups.divergentBothSides' and backend.get_groups()==both_values and history()==both_history,'refusal':refusal,'prerequisite':key is not None}",
    )
    yield (
        "both-fixture-cleanup",
        "if 'created_both' in globals() and created_both:\n    backend._package().kerning().deleteGroup(both_fixture,deleteDependentKerningPairs=False)\nresult={'removed':True}",
    )
    yield (
        "legacy-fixture-setup",
        "import fontgate\nlegacy_plain=backend._package().fgPackage.groups\nlegacy_before=dict(legacy_plain.asDict())\nlegacy_fixture='fontport_owned_legacy'\nif legacy_fixture in legacy_before:\n    raise ValueError('Owned legacy fixture name already exists')\nlegacy_values=dict(legacy_before)\nlegacy_values[legacy_fixture]=fontgate.fgGroup(legacy_fixture,['A'],'KernLeftGroupMode','A')\nlegacy_plain.fromDict(legacy_values)\nfontlab.flItems.notifyChangesApplied('Owned legacy group fixture',[backend._package()])\nresult={'prerequisite':not legacy_plain[legacy_fixture].isFeaGroup(),'name':legacy_fixture,'mode':legacy_plain[legacy_fixture].mode}",
    )
    probes = {
        "single-undo": "backend.set_info_many({'openTypeNameDesigner':str(backend.get_info('openTypeNameDesigner'))+' owned'},require_single_undo=True)",
        "unset-metric": "backend.set_info_many({'capHeight':None})",
        "unicode-class": "backend.set_groups({**backend.get_groups(),'Ω_owned':('A',)})",
        "legacy-flags": "from fontlab_fontport.native_groups import write_groups\nwrite_groups(backend._package(),{**backend.get_groups(),'owned_legacy':('A',)},'Owned strict class',require_persistence=True)",
        "fractional-kerning": "backend.set_kerning({**backend.get_kerning(),('A','V'):-12.5})",
        "legacy-save": "backend.save(str(Path(output)/'refused-legacy.vfj'),require_persistence=True)",
    }
    expected = {
        "single-undo": "info.exactSingleUndo",
        "unset-metric": "info.capHeight.absent",
        "unicode-class": "groups.unicodeNames",
        "legacy-flags": "groups.legacyFlagsVfj",
        "fractional-kerning": "kerning.fractionalHistory",
        "legacy-save": "groups.legacyFlagsVfj",
    }
    for name, code in probes.items():
        yield (
            name + "-baseline",
            "history_before=history()\ninfo_before={field:backend.get_info(field) for field in ('openTypeNameDesigner','capHeight')}\ngroups_before=backend.get_groups()\nkerning_before=backend.get_kerning()\nresult={'history':history_before,'info':info_before,'groups':groups_before,'kerning':[(list(pair),v) for pair,v in kerning_before.items()]}",
        )
        yield (
            name + "-refusal",
            f"refusal=None\ntry:\n    exec({code!r},globals())\nexcept UnsupportedCapability as error:\n    refusal={{'capability':error.capability,'reason':str(error)}}\nresult={{'equal':refusal is not None and refusal['capability']=={expected[name]!r} and history()==history_before,'refusal':refusal,'history_before':history_before,'history_after':history()}}",
        )
        yield (
            name + "-unchanged",
            "result={'equal':info_before=={field:backend.get_info(field) for field in info_before} and groups_before==backend.get_groups() and kerning_before==backend.get_kerning(),'history':history()}",
        )
    yield (
        "legacy-file-absent",
        "result={'file_absent':not (Path(output)/'refused-legacy.vfj').exists()}",
    )
    yield (
        "legacy-fixture-cleanup",
        "if 'legacy_before' in globals():\n    backend._package().fgPackage.groups.fromDict(legacy_before)\nresult={'restored':True}",
    )
    structured = {
        "openTypeOS2Panose": [2, 0, 5, 3, 0, 0, 0, 0, 0, 0],
        "openTypeOS2WeightClass": 500,
        "openTypeOS2WidthClass": 6,
        "postscriptStemSnapH": [20.5, 80],
        "postscriptStemSnapV": [70.25],
        "openTypeNameRecords": [
            {
                "nameID": 256,
                "platformID": 3,
                "encodingID": 1,
                "languageID": 1033,
                "string": "Owned Ω",
            }
        ],
    }
    for field, value in structured.items():
        prefix = "structured-" + field
        yield (
            prefix + "-baseline",
            f"field={field!r}\nrequested={value!r}\nvalue_before=backend.get_info(field)\ninfo_history_before=history()\nresult={{'field':field,'before':value_before,'requested':requested,'history':info_history_before}}",
        )
        if field == "openTypeNameRecords":
            yield (
                prefix + "-refusal",
                "refusal=None\ntry:\n    backend.set_info_many({field:requested})\nexcept UnsupportedCapability as error:\n    refusal={'capability':error.capability,'reason':str(error)}\nresult={'equal':refusal is not None and refusal['capability']=='info.openTypeNameRecords.persistence' and backend.get_info(field)==value_before and history()==info_history_before,'refusal':refusal,'unchanged':backend.get_info(field)}",
            )
            continue
        yield (
            prefix + "-apply",
            "backend.set_info_many({field:requested},require_single_undo=False)\nresult={'history_before':info_history_before,'history_after':history(),'native_history_states':list(backend._package().historyStates(True)),'explicit_legacy_history':True,'has_undo_step':history()!=info_history_before}",
        )
        yield (
            prefix + "-read",
            "observed=backend.get_info(field)\nresult={'equal':observed==requested,'observed':observed,'expected':requested}",
        )
        yield prefix + "-undo", "result=action('actionUndo')"
        yield (
            prefix + "-undo-read",
            "observed=backend.get_info(field)\nresult={'equal':observed==value_before,'observed':observed,'expected':value_before}",
        )
        yield prefix + "-redo", "result=action('actionRedo')"
        yield (
            prefix + "-redo-read",
            "observed=backend.get_info(field)\nresult={'equal':observed==requested,'observed':observed,'expected':requested}",
        )
        yield (
            prefix + "-save",
            f"saved_path=str(Path(output)/{prefix + '.vfj'!r})\nfont.save(saved_path)\nresult={{'path':saved_path}}",
        )
        yield prefix + "-close", "font.close()\nresult={'closed':True}"
        yield (
            prefix + "-reopen",
            "font=environment.OpenFont(saved_path)\nbackend=font._backend\nowned_ids.add(backend.font_id)\nresult={'id':backend.font_id}",
        )
        yield (
            prefix + "-reopen-read",
            "observed=backend.get_info(field)\nresult={'equal':observed==requested,'observed':observed,'expected':requested}",
        )
