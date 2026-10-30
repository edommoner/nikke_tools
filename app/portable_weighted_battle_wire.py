"""Private weighted carrier lowering and literal weights; no CPU battle input."""
import copy,math,struct
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from weighted_incoming_battle_model import WeightedIncoming
MAGIC=0x57425431
SOURCE='gpu/world_weighted_incoming_entry.slang'
LAYOUT=dict(BASE=115680,WORDS=16,INPUT=115696,OUTPUT_BASE=2032000,OUTPUT=2048912,HEADER=16,DEPTH=32,SCRATCH=16,SCRATCH_WORDS=8,SNAPSHOTS=272,SNAPSHOT_WORDS=48,CAPACITY=128,RECEIPTS=6416,RECEIPT_WORDS=32)
INPUT=LAYOUT['INPUT'];OUTPUT=LAYOUT['OUTPUT']
def shader_schema():return '// Generated from portable_weighted_battle_wire; ownership and bounds only.\n'+''.join(f'static const uint WGT_{k}={v}U;\n' for k,v in dict(MAGIC=MAGIC,BODY_ROW=10,COVER_ROW=11,**LAYOUT).items())
def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    if (root/'gpu/weighted_incoming_layout.slang').read_text()!=shader_schema():raise ValueError('Weighted incoming layout drift')
    from portable_dispatch_frames import CAPACITY
    if LAYOUT['DEPTH']!=CAPACITY or LAYOUT['OUTPUT_BASE']+LAYOUT['RECEIPTS']+128*32>OUTPUT:raise ValueError('Weighted bank bounds/depth drift')
def pack(spec,names,source_rows=None):
    WeightedIncoming(spec,names)
    words=[MAGIC,1,5,0]
    for key in ('caster_weight','other_weight','cover_weight'):words.extend(struct.unpack('<II',struct.pack('<d',spec[key])))
    if source_rows is None:return words+[0]*6
    if type(source_rows) not in (list,tuple) or len(source_rows)!=2 or len(set(source_rows))!=2 or any(type(i) is not int or not 0<=i<512 for i in source_rows):raise ValueError('Two distinct immutable marker definition rows required')
    return words+[i+1 for i in source_rows]+[0]*4
@contextmanager
def compiler_policy():
    import portable_runtime,portable_element_specs
    original=portable_runtime.validate_effect;legacy=portable_element_specs.legacy_effect
    def converted(e):
        if e.get('stat')!='received_dmg_split':return e
        if e.get('type')!='buff' or e.get('target') not in ('all_allies','self_cover') or e.get('scaling') is not None or e.get('trigger',{}).get('condition',[]) or e.get('tick_interval') or e.get('duration_bullets',-1)!=-1:raise ValueError('Weighted original marker requires plain body/independent-cover lifetime')
        return dict(e,stat='',target='self' if e['target']=='self_cover' else e['target'])
    def validate(e,*,combat=None,world_frame=False):
        if e.get('stat')=='received_dmg_split' and (combat is None or not world_frame):raise ValueError('Weighted markers require original battle context')
        return original(converted(e),combat=combat,world_frame=world_frame)
    with patch.object(portable_runtime,'validate_effect',validate),patch.object(portable_element_specs,'legacy_effect',lambda e:legacy(converted(e))):yield
def compile_weighted(prepared,case):
    from portable_coordinate_typed_input import compile_coordinate_typed
    from portable_specs import LIMITS as L,FIELDS as F
    check_schema();before=copy.deepcopy(prepared);names=[c['name'] for c in prepared['chars']];bank=pack(case['allocation'],names)
    # Keep the existing presence-carrier kind/stat. Literal definition row IDs
    # identify the two consumers without colliding with other private stats.
    with compiler_policy():
        words,meta,bindings,scene=compile_coordinate_typed(prepared,case['typed_bindings'],probe_kind=3,geometry=case['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
    if len(words)!=LAYOUT['BASE'] or prepared!=before:raise ValueError('Weighted lowering changed original program/input')
    indices=[]
    for i,r in enumerate(prepared['effects']):
        e=r['effect']
        if e.get('stat')!='received_dmg_split':continue
        at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']
        if words[at+F['KIND']]!=4 or words[at+F['STAT']]!=0:raise ValueError('Weighted placeholder changed')
        indices.append(i)
    if len(indices)!=2:raise ValueError('Exact original body and cover source rows required')
    source_rows=[meta['binding_source_indices'].index(next(i for i in indices if prepared['effects'][i]['effect']['target']==target)) for target in ('all_allies','self_cover')]
    bank=pack(case['allocation'],names,source_rows)
    if case.get('declared_burst_sequence'):meta['coordinate_original_input'].update(original_controls_preserved=False,declared_burst_sequence_applied_after_identity_check=True)
    meta.update(ordered_recipients=True,weighted_incoming=dict(input_words=INPUT,output_words=OUTPUT,definition_indices=indices,source_rows=source_rows,CPU_state_or_schedule_as_input=False,cover_is_independent=True))
    return words+bank,meta,bindings,scene
