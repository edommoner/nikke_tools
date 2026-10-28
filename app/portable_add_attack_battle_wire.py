"""ADD attack payloads lower beside the unchanged logical world prefix."""
import copy,struct
from pathlib import Path
from portable_specs import LIMITS as L
from portable_world_schedule_specs import number

MAGIC=0x41444231
LAYOUT=dict(BASE=115680,HEADER=16,ROWS=32,ROW_WORDS=24,ROW_BASE=16,WORDS=784,INPUT_WORDS=116464,
            OUTPUT_BASE=1867648,OUTPUT_HEADER=16,BODY_BASE=16,STATE_BASE=80,MAP_BASE=336,MAP_ROWS=2048,OUTPUT_WORDS=2032000)


def shader_schema():
    return '// Generated from portable_add_attack_battle_wire; declaration addresses only.\n'+''.join(f'static const uint ADB_{k}={v}U;\n' for k,v in dict(MAGIC=MAGIC,**LAYOUT).items())


def check_schema(root=None):
    if (Path(root or Path(__file__).resolve().parents[1])/'gpu/world_add_attack_battle_layout.slang').read_text()!=shader_schema():raise ValueError('ADD battle declaration schema drift')


def pack(patterns,bindings,authored):
    from portable_enemy_target_specs import target_rule
    words=[0]*LAYOUT['WORDS'];words[:4]=[MAGIC,1,len(patterns),len(bindings)]
    for p in patterns:
        if p.summon is None or p.summon.attack is None:continue
        if p.summon.self_destruct:raise ValueError('Self-destruct launch/retirement is not connected')
        a=p.summon.attack
        if a.debuffs:raise ValueError('ADD attack debuffs are not connected')
        if a.hits>0x7fffffff:raise ValueError('ADD shot count exceeds exact integer range')
        raw=authored[p.idx]['spec']['attack']
        payload=[32,0,0,int(a.pierce),0,0,0,0,*number(a.atk),*number(a.coeff),*target_rule({k:raw[k] for k in ('target','ignore_taunt') if k in raw})]
        at=LAYOUT['ROW_BASE']+p.idx*24
        words[at:at+24]=[p.summon.count,a.hits,*number(a.interval),0,0,0,0,*payload]
    return words


def compile_battle(prepared,geometry):
    from calculator.boss_pattern import validate
    from portable_logical_geometry_wire import compile_logical_geometry
    check_schema();before=copy.deepcopy(prepared);lowered=copy.deepcopy(prepared)
    patterns=validate(copy.deepcopy(prepared['enemy']['patterns']),squad_size=5,coord=True)
    for p,raw in zip(patterns,lowered['enemy']['patterns'],strict=True):
        if p.summon is not None and p.summon.attack is not None:raw['spec'].pop('attack')
    prefix,meta,bindings,scene=compile_logical_geometry(lowered,geometry)
    bank=pack(patterns,bindings,prepared['enemy']['patterns'])
    assert len(prefix)==LAYOUT['BASE'] and prepared==before
    meta['add_attack_battle']=dict(input_words=LAYOUT['INPUT_WORDS'],model='original-scheduled-ADD-attacks-v1',CPU_schedule_as_input=False)
    return prefix+bank,meta,bindings,scene
