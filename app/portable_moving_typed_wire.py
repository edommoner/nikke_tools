"""Disjoint typed/logical/motion banks; live quantities are never inputs."""
import copy
from pathlib import Path
from portable_enemy_movement_wire import shader_schema as movement_schema,movement_bank,lower_effects
from coordinate_moving_typed_geometry import normalize

SOURCE='gpu/world_moving_typed_entry.slang'
TYPED_BASE=109968;LOGICAL_BASE=115680;MOVEMENT_BASE=121392;INPUT=123188
MOVEMENT_OUT=2032000;AIM_BASE=2164624;AIM_WORDS=512;OUTPUT=AIM_BASE+AIM_WORDS

def shader_schema():
    return movement_schema(base=MOVEMENT_BASE,out=MOVEMENT_OUT,output=OUTPUT)+''.join('static const uint '+k+'='+str(v)+'U;\n' for k,v in dict(TMR_LAG_BASE=LOGICAL_BASE,TMR_AIM_BASE=AIM_BASE,TMR_AIM_WORDS=AIM_WORDS).items())

def check_schema(root=None):
    path=Path(root or Path(__file__).resolve().parents[1])/'gpu/moving_typed_layout.slang'
    if path.read_text()!=shader_schema():raise ValueError('Moving typed composed layout drift')

def output_regions():
    from portable_arena_specs import Region
    return [Region('output','coordinate',0,1769856),Region('output','typed-header-and-targets',1769856,3568),
        Region('output','shared-complete-skill-history',1773424,92160),Region('output','logical-pellet-scratch',1865584,2048),
        Region('output','logical-shot-header',1867632,16),Region('output','typed-receipts-scratch-and-history',1867648,164352),
        Region('output','movement-header',MOVEMENT_OUT,16),Region('output','movement-state',MOVEMENT_OUT+16,1536),
        Region('output','movement-frames',MOVEMENT_OUT+1552,65536),Region('output','movement-segments',MOVEMENT_OUT+67088,65536),
        Region('output','frozen-typed-aim-centers',AIM_BASE,AIM_WORDS)]

def compile_battle(prepared,case):
    from portable_coordinate_typed_input import compile_coordinate_typed
    from portable_logical_geometry_wire import pack,validate
    check_schema();before=copy.deepcopy(prepared);rules=normalize(case['typed_attachment'],case['enemy_movement'])
    if prepared.get('typed_actor_policy')!={'mode':'logical-owned-current-fields-v1'}:raise ValueError('Moving typed geometry needs exact logical owners')
    lowered,tags=lower_effects(prepared)
    prefix,meta,actors,scene=compile_coordinate_typed(lowered,case['typed_bindings'],probe_kind=case['typed_bindings'][0]['kind'],max_attacks=case['max_attacks'],geometry=case['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True,coordinate_logical_owners=True)
    if len(prefix)!=LOGICAL_BASE:raise ValueError('Complete typed bank required before logical geometry')
    geometry=pack(case['logical_geometry'],actors);validate(geometry,prefix[:TYPED_BASE],actors);prefix+=geometry
    actor_ids={b.label:b.identity for b in actors if int(b.kind)==5};links={r['typed_label']:r['actor_label'] for r in rules['bindings']};seen=set()
    for binding in case['typed_bindings']:
        label=links.get(binding['label']);owner=binding.get('owner')
        if label is not None:
            if owner is None or owner[:2]!=[5,actor_ids.get(label)]:raise ValueError('Attachment cannot replace a typed owner')
            seen.add(binding['label'])
        elif owner is not None and owner[0]==5:raise ValueError('Every ADD-owned typed binding needs an explicit attachment')
    if seen!=set(links):raise ValueError('Unknown typed attachment label')
    bank=movement_bank(prefix,meta,actors,case['logical_geometry'],case['enemy_movement'],tags,logical_base=LOGICAL_BASE);bank[6]=1
    if prepared!=before or len(prefix)+len(bank)!=INPUT:raise ValueError('Original prepared input changed or composed stride differs')
    meta['moving_typed_geometry']=dict(policy=rules,input_words=INPUT,output_words=OUTPUT,precomputed_positions=False,gpu_admitted=False)
    return prefix+bank,meta,actors,scene
