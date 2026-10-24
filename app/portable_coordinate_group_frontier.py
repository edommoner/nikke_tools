"""Real current writer conflicts and a capacity-preserving static relocation plan.

The proposal does not enable groups or change a shader address. Consumer and
receipt integration are deliberately reported as remaining implementation.
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
    assert len(allowed)==2 and all(output not in [int(v.strip()) for v in row.split(',')] for row in allowed)
    sources['app/portable_backend.py']=hashlib.sha256(transport.encode()).hexdigest()
    return dict(schema=1,passed=True,classification='gpu_port_gap',scope='Static current writer/caller audit and unimplemented relocation proposal',
                current=current,proposal=proposal,proposed_group_compact_begin=relocated,
                proposed_group_compact_end=end,group_compact_words_retained=ag['COMPACT_WORDS'],
                group_enabled_with_coordinate_physical=False,proposed_addresses_implemented=False,
                proposed_transport_stride_registered=False,
                physical_group_receipts_connected=False,add_sharing_connected=False,
                remaining=['relocate actual group compact declarations/readers/writers',
                           'bound coordinate initialization clear before relocated group writer',
                           'connect coordinate physical packet receipts to group producer/delivery',
                           'bind ADD/actor sharing and notifications before admitting combined worlds',
                           'register complete relocated strides in host transport and validation wrappers'],
                source_sha256=sources,gpu_calls=0,native_battle_calls=0,calculation_verified=False,public_gpu_admitted=False)
