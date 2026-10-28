"""Static final-shot retirement declarations on the common ADD battle wire."""
import copy
from pathlib import Path
from portable_add_attack_battle_wire import LAYOUT as A
from portable_world_schedule_specs import number

LAYOUT=dict(OUTPUT_BASE=1872080,HEADER=16,ROWS=2048,ROW_WORDS=12,OUTPUT_WORDS=A['OUTPUT_WORDS'],INPUT_WORDS=A['INPUT_WORDS'])
MAGIC=0x41534431


def shader_schema():
    return '// Generated from portable_add_self_destruct_wire; no CPU runtime state.\n'+''.join(f'static const uint ASD_{k}={v}U;\n' for k,v in dict(MAGIC=MAGIC,**LAYOUT).items())


def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    if (root/'gpu/add_self_destruct_layout.slang').read_text()!=shader_schema():raise ValueError('ADD self-destruct schema drift')
    assert LAYOUT['OUTPUT_BASE']==A['OUTPUT_BASE']+A['MAP_BASE']+A['MAP_ROWS']*2
    assert LAYOUT['OUTPUT_BASE']+LAYOUT['HEADER']+LAYOUT['ROWS']*LAYOUT['ROW_WORDS']<=A['OUTPUT_WORDS']


def compile_battle(prepared,geometry):
    from calculator.boss_pattern import validate
    from portable_add_attack_battle_wire import compile_battle as common
    check_schema();before=copy.deepcopy(prepared);lowered=copy.deepcopy(prepared)
    patterns=validate(copy.deepcopy(prepared['enemy']['patterns']),squad_size=5,coord=True)
    for p,raw in zip(patterns,lowered['enemy']['patterns'],strict=True):
        if p.summon is None or p.summon.attack is None:continue
        if p.summon.self_destruct and p.summon.attack.hits==0:raise ValueError('Finite self-destruct shot count required')
        # The common prefix owns only the graph and actor pool. Preserve the
        # original literal attack rank after its payload is moved to the bank.
        raw['spec'].pop('self_destruct',None);raw['spec'].pop('attack_at',None)
        raw['spec']['atk']=p.summon.atk
    words,meta,bindings,scene=common(lowered,geometry)
    for p in patterns:
        if p.summon is None or p.summon.attack is None:continue
        at=A['BASE']+A['ROW_BASE']+p.idx*A['ROW_WORDS']
        words[at+4]=int(p.summon.self_destruct);words[at+5:at+7]=number(p.summon.attack_at)
    assert prepared==before
    meta['add_self_destruct']=dict(model='canonical-final-shot-retirement-v1',CPU_schedule_as_input=False)
    return words,meta,bindings,scene
