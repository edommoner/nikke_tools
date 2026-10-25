"""Real current writer conflicts and a capacity-preserving static relocation plan.

The legacy entry keeps dormant overlapping compaction. A separate complete
coordinate-group entry relocates the full arena and uses actual packet receipts.
"""
import hashlib,re
from pathlib import Path
from portable_arena_specs import Region,regions,audit_regions,attack_group_layout
from portable_coordinate_physical_specs import LAYOUT as PHYSICAL,audit_arena
from portable_coordinate_cache_specs import LAYOUT as CACHE
from portable_coordinate_aim_wire import LAYOUT as AIM,INPUT_WORDS,OUTPUT_WORDS,check_schema
from portable_coordinate_core_specs import BASE_INPUT as CORE_BASE,INPUT as CORE_WORDS


def verify(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);check_schema(root);audit_arena(root)
    ag=attack_group_layout();base_rows,_,_=regions('combined-v1')
    # The composed declarations include a broad group compaction writer. The
    # coordinate physical/cache/aim profile is safe only while it is dormant.
    live=[Region('output','physical-scratch',PHYSICAL['BASE'],PHYSICAL['END']-PHYSICAL['BASE']),
          Region('output','aim-state',AIM['STATE'],AIM['STATE_WORDS']),
          Region('output','geometry-cache',CACHE['BASE'],CACHE['END']-CACHE['BASE'])]
    input_extensions=[Region('input','coordinate-live-core',CORE_BASE,CORE_WORDS),
                      Region('input','coordinate-authored-aim',AIM['BASE_INPUT'],AIM['INPUT'])]
    current=audit_regions([*base_rows,*input_extensions,*live],INPUT_WORDS,OUTPUT_WORDS)
    assert not current['address_plan_verified']
    expected={('attack-group-compact',r.name) for r in live}
    assert {(r['first'],r['second']) for r in current['overlaps']}==expected
    # Retain every old group word and coordinate capacity; append compaction
    # after the old output stride. Coordinate clearing must remain bounded.
    relocated=OUTPUT_WORDS;end=relocated+ag['COMPACT_WORDS'];output=((end+65535)//65536)*65536
    proposal_rows=[r for r in base_rows if r.name!='attack-group-compact']+input_extensions+live+[Region('output','attack-group-compact',relocated,ag['COMPACT_WORDS'])]
    proposal=audit_regions(proposal_rows,INPUT_WORDS,output)
    assert proposal['address_plan_verified']
    consumers={
        'gpu/coordinate_physical_runtime.slang':['commands[s.inputBase+104402]!=0','slot*8]==62)return false'],
        'gpu/world_coordinate_physical_entry.slang':['#define WEAPON_TYPED_PELLET(s,w,who,when,output,hit,amount) true','#define WEAPON_BODY_SUPPRESSED(s,who,hit) true'],
        'gpu/world_coordinate_area_entry.slang':['for(uint i=CP_BASE;i<P_OUTPUT_WORDS;i++)results[output+i]=0;'],
        'gpu/combat_runtime.slang':['if(deliverAttackGroupShot(s,who,when,output,landedAmount,landedCount)) return;']}
    sources={}
    for name,snippets in consumers.items():
        text=(root/name).read_text()
        assert all(text.count(s)==1 for s in snippets),'Coordinate/group consumer drift: '+name
        sources[name]=hashlib.sha256(text.encode()).hexdigest()
    transport=(root/'app/portable_backend.py').read_text()
    allowed=re.findall(r'output_words not in \(([^)]+)\)',transport)
    assert len(allowed)==2 and all(output in [int(v.strip()) for v in row.split(',')] for row in allowed)
    sources['app/portable_backend.py']=hashlib.sha256(transport.encode()).hexdigest()
    from portable_coordinate_group_wire import check_schema as group_schema
    relocated=group_schema(root)
    for name,tokens in {
        'gpu/coordinate_physical_runtime.slang':['bool grouped=beginCoordinatePhysicalGroup(s,who,when,count*packets);','if(grouped)agCollect(s,results[agHead(s)+3]-1,slot,generation);','if(grouped)finishCoordinatePhysicalGroup(s,who,when,s.resourceOutput);','actorSetCapture(s,33,setIndex,0,128,0,who NAMED_ENEMY_ARGUMENT(0));'],
        'gpu/attack_group_runtime.slang':['#include "attack_group_open.slang"','#include "attack_group_seal.slang"'],
        'scripts/run-metal-probe.swift':['outputWords == 1507328'],
    }.items():
        text=(root/name).read_text();assert all(token in text for token in tokens),'Relocated group consumer drift: '+name
        sources[name]=hashlib.sha256(text.encode()).hexdigest()
    return dict(schema=1,passed=True,classification='gpu_port_gap',scope='Legacy guarded overlap and separate implemented private group profile; no calculation proof',
                current=current,proposal=proposal,proposed_group_compact_begin=OUTPUT_WORDS,
                proposed_group_compact_end=end,group_compact_words_retained=ag['COMPACT_WORDS'],
                group_enabled_with_coordinate_physical=True,proposed_addresses_implemented=True,
                proposed_transport_stride_registered=True,
                physical_group_receipts_connected=True,add_sharing_connected=True,
                add_sharing_scope='Shared Actor pool and frozen group handles; weighted allocation not verified',
                proportional_add_sharing_verified=False,
                relocated_profile=relocated,legacy_default_profile_group_guard_retained=True,
                remaining=['current CUDA execution/cache proof','additional RNG, mixed scene and original definition coverage'],
                source_sha256=sources,gpu_calls=0,native_battle_calls=0,calculation_verified=False,public_gpu_admitted=False)
