"""Combine literal ADD retirement and magazines without CPU runtime input."""
import copy
from pathlib import Path
from portable_enemy_ammo_wire import LAYOUT as E,compiler_policy,pack,validate_enemy_effects
from portable_add_self_destruct_wire import LAYOUT as S,MAGIC,compile_battle as self_battle

LAYOUT=dict(S,INPUT_WORDS=E['INPUT_WORDS'],OUTPUT_BASE=E['OUTPUT_BASE']+E['RESOURCE_BASE']+(E['RESOURCE_CAPACITY']-128)*8)


def shader_schema():
    return '// Generated from portable_enemy_ammo_self_destruct_wire; disjoint static-owned receipts.\n'+''.join(f'static const uint ASD_{k}={v}U;\n' for k,v in dict(MAGIC=MAGIC,**LAYOUT).items())


def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    if (root/'gpu/enemy_ammo_self_destruct_layout.slang').read_text()!=shader_schema():raise ValueError('Final-queue magazine layout drift')
    assert LAYOUT['OUTPUT_BASE']+LAYOUT['HEADER']+LAYOUT['ROWS']*LAYOUT['ROW_WORDS']<=E['OUTPUT_WORDS']


def compile_battle(prepared,geometry,spec):
    from calculator.boss_pattern import validate
    check_schema();before=copy.deepcopy(prepared)
    validate_enemy_effects([(r['effect'],r['owner']) for r in prepared['effects']],[c['name'] for c in prepared['chars']])
    with compiler_policy():prefix,meta,bindings,scene=self_battle(prepared,geometry)
    patterns=validate(copy.deepcopy(prepared['enemy']['patterns']),coord=True,squad_size=5)
    bank=pack(spec,patterns,bindings,allow_self_destruct=True)
    assert len(prefix)==E['BASE'] and prepared==before
    meta['enemy_ammo_declarations']=dict(input_words=E['INPUT_WORDS'],model='declared-enemy-magazine-final-queue-v1',CPU_state_or_schedule_as_input=False)
    return prefix+bank,meta,bindings,scene
