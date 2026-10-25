"""Complete coordinate-group stride and real writer ownership, no packing policy."""
from pathlib import Path
from portable_coordinate_aim_wire import INPUT_WORDS,check_schema as check_aim
OUTPUT_WORDS=1507328
COMPACT=1310720
COMPACT_WORDS=186528

def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);check_aim(root)
    from portable_arena_specs import regions,Region,audit_regions
    from portable_coordinate_group_frontier import PHYSICAL,CACHE,AIM,CORE_BASE,CORE_WORDS
    rows,_,_=regions('combined-v1')
    rows=[r for r in rows if r.name!='attack-group-compact']
    rows += [Region('input','coordinate-live-core',CORE_BASE,CORE_WORDS),Region('input','coordinate-authored-aim',AIM['BASE_INPUT'],AIM['INPUT']),Region('output','physical-scratch',PHYSICAL['BASE'],PHYSICAL['END']-PHYSICAL['BASE']),Region('output','aim-state',AIM['STATE'],AIM['STATE_WORDS']),Region('output','geometry-cache',CACHE['BASE'],CACHE['END']-CACHE['BASE']),Region('output','attack-group-compact',COMPACT,COMPACT_WORDS)]
    plan=audit_regions(rows,INPUT_WORDS,OUTPUT_WORDS);assert plan['address_plan_verified']
    text=(root/'gpu/composed_arena_layout.slang').read_text();assert 'static const uint AG_COMPACT=1310720,AG_COMPACT_WORDS=186528;' in text
    assert 'static const uint P_OUTPUT_WORDS = 1507328U;' in (root/'gpu/portable_schema.slang').read_text()
    assert 'for(uint i=CP_BASE;i<AG_COMPACT;i++)results[output+i]=0;' in (root/'gpu/world_coordinate_area_entry.slang').read_text()
    assert 'outputWords == 1507328' in (root/'scripts/run-metal-probe.swift').read_text(), 'Metal consumer must admit the complete group wire'
    return plan
