"""Opt-in independent cover bases; no simulated state or attacker snapshots in input."""
import copy,struct
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from cover_defense_battle_model import normalize
MAGIC=0x43444231
STAT=93
SOURCE='gpu/world_cover_defense_entry.slang'
LAYOUT=dict(BASE=115680,WORDS=24,INPUT_WORDS=115704,OUTPUT_BASE=2032000,HEADER=16,SNAPSHOT_BASE=16,SNAPSHOT_WORDS=16,DEPTH=32,RECEIPT_BASE=528,RECEIPTS=512,RECEIPT_WORDS=32,OUTPUT_WORDS=2048912)
INPUT=LAYOUT['INPUT_WORDS'];OUTPUT=LAYOUT['OUTPUT_WORDS']

def shader_schema():return '// Generated from portable_cover_defense_wire; declarations and receipt ownership only.\n'+''.join(f'static const uint CDF_{k}={v}U;\n' for k,v in dict(MAGIC=MAGIC,STAT=STAT,**LAYOUT).items())
def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    if (root/'gpu/cover_defense_layout.slang').read_text()!=shader_schema():raise ValueError('Cover DEF declaration schema drift')
    assert LAYOUT['OUTPUT_BASE']+LAYOUT['RECEIPT_BASE']+LAYOUT['RECEIPTS']*LAYOUT['RECEIPT_WORDS']==OUTPUT

def pack(spec,names):
    values=normalize(spec,names);words=[MAGIC,1,5,0,0,0,0,0]
    for name in names:words.extend(struct.unpack('<II',struct.pack('<d',values[name])))
    return words+[0]*6

def validate(words,names):
    if len(words)!=24 or any(type(w) is not int or not 0<=w<=0xffffffff for w in words):raise ValueError('Exact uint32 cover bank required')
    if words[:3]!=[MAGIC,1,5] or any(words[3:8]+words[18:]):raise ValueError('Invalid cover declaration header/reserved words')
    rows=[dict(name=n,base_defense=struct.unpack('<d',struct.pack('<II',*words[8+i*2:10+i*2]))[0]) for i,n in enumerate(names)]
    normalize(rows,names);return rows

@contextmanager
def compiler_policy():
    """Validate only an unscaled private buff; reuse legacy trigger/value lowering."""
    import portable_runtime,portable_element_specs
    original_validate=portable_runtime.validate_effect;original_effect=portable_element_specs.legacy_effect
    def eligible(effect):return effect.get('stat')=='cover_def_pct'
    def check(effect,*,combat=None,world_frame=False):
        if eligible(effect):
            if effect.get('type')!='buff' or effect.get('scaling') is not None or effect.get('tick_interval') or combat is None or not world_frame:raise ValueError('Cover DEF requires an unscaled private combat buff')
            return original_validate(dict(effect,stat=''),combat=combat,world_frame=world_frame)
        return original_validate(effect,combat=combat,world_frame=world_frame)
    def lower(effect):return original_effect(dict(effect,stat='') if eligible(effect) else effect)
    with patch.object(portable_runtime,'validate_effect',check),patch.object(portable_element_specs,'legacy_effect',lower):yield

def compile_cover(prepared,case):
    from portable_coordinate_typed_input import compile_coordinate_typed
    from portable_specs import LIMITS as L,FIELDS as F
    check_schema();before=copy.deepcopy(prepared)
    names=[c['name'] for c in prepared['chars']];bank=pack(case['cover_defense'],names);validate(bank,names)
    with compiler_policy():
        words,meta,bindings,scene=compile_coordinate_typed(prepared,case['typed_bindings'],probe_kind=case['catalogue_profile']['kind'],geometry=case['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
    if len(words)!=LAYOUT['BASE'] or prepared!=before:raise ValueError('Original prefix/source changed during cover lowering')
    indices=[i for i,row in enumerate(prepared['effects']) if row['effect'].get('stat')=='cover_def_pct']
    if not indices:raise ValueError('Original cover DEF effect required')
    # No effect or authored value is replaced. The scoped-inert legacy placeholder
    # retains all trigger/value/recipient fields; only the dedicated stat is set.
    for i in indices:
        at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']
        if words[at+F['KIND']]!=4 or words[at+F['STAT']]!=0:raise ValueError('Original named cover placeholder kind changed')
        words[at+F['KIND']]=0
        words[at+F['STAT']]=STAT
    if case.get('declared_manual_sequences'):meta['coordinate_original_input'].update(original_controls_preserved=False,declared_manual_sequences_applied_after_identity_check=True)
    meta.update(ordered_recipients=True,cover_defense_declarations=dict(model='declared-independent-cover-defense-v1',input_words=INPUT,output_words=OUTPUT,CPU_state_or_schedule_as_input=False,definition_indices=indices))
    return words+bank,meta,bindings,scene
