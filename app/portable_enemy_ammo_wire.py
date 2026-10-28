"""Declared magazines beside the actual ADD battle wire, never CPU timelines."""
import copy,struct
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from enemy_ammo_model import normalize,validate_enemy_effects

MAGIC=0x45414d31
LAYOUT=dict(BASE=116464,HEADER=16,ORDER_BASE=16,ROWS=128,ROW_BASE=144,ROW_WORDS=8,WORDS=1168,INPUT_WORDS=117632,
            OUTPUT_BASE=1872080,STATE_BASE=16,STATE_WORDS=8,HISTORY_BASE=1040,HISTORIES=512,HISTORY_WORDS=12,
            EVENT_BASE=7184,EVENTS=2048,EVENT_WORDS=16,RESOURCE_BASE=39952,RESOURCE_CAPACITY=4096,OUTPUT_WORDS=2032000)


def shader_schema():
    return '// Generated from portable_enemy_ammo_wire; declared resources only.\n'+''.join(f'static const uint EAM_{k}={v}U;\n' for k,v in dict(MAGIC=MAGIC,**LAYOUT).items())


def check_schema(root=None):
    if (Path(root or Path(__file__).resolve().parents[1])/'gpu/enemy_ammo_layout.slang').read_text()!=shader_schema():raise ValueError('Enemy ammo declaration schema drift')


def enemy_percentage(effect):
    return effect.get('type')=='instant' and effect.get('stat')=='ammo_charge_pct' and effect.get('target')=='all_enemies'


@contextmanager
def compiler_policy():
    import portable_runtime
    original=portable_runtime.validate_effect
    def validate(effect,*,combat=None,world_frame=False):
        if enemy_percentage(effect):
            if combat is None or not world_frame:raise ValueError('Enemy ammo requires the private actor world')
            # Validation only. Actual definition/selector/name/value lowering
            # retains the complete original effect and canonical compiler row.
            return original(dict(effect,target='self'),combat=combat,world_frame=world_frame)
        return original(effect,combat=combat,world_frame=world_frame)
    with patch.object(portable_runtime,'validate_effect',validate):yield


def pack(spec,patterns,bindings):
    rules=normalize(spec);slots={b.label:i for i,b in enumerate(bindings)};declared={r['label'] for r in rules}
    words=[0]*LAYOUT['WORDS'];words[:4]=[MAGIC,1,len(rules),len(bindings)]
    for index,row in enumerate(rules):
        slot=slots.get(row['label'])
        if slot is None or int(bindings[slot].kind) not in (0,5):raise ValueError('Magazine must bind a real BODY/ADD actor')
        words[LAYOUT['ORDER_BASE']+index]=slot+1
        at=LAYOUT['ROW_BASE']+slot*8
        words[at:at+8]=[1,row['capacity'],row['initial'],int(row['cancel_on_full']),*struct.unpack('<II',struct.pack('<d',row['reload_seconds'])),0,0]
    for p in patterns:
        if p.kind=='attack' and '__enemy__' not in declared:raise ValueError('Every body attack needs its declared magazine')
        if p.summon is not None and p.summon.attack is not None:
            if p.summon.self_destruct:raise ValueError('Self-destruct enemy magazines are not connected')
            if any(b.label not in declared for b in bindings if int(b.kind)==5 and b.run==p.idx):raise ValueError('Every attacking ADD needs its declared magazine')
    return words


def compile_enemy_ammo(prepared,geometry,spec):
    from calculator.boss_pattern import validate
    from portable_add_attack_battle_wire import compile_battle
    check_schema();before=copy.deepcopy(prepared)
    validate_enemy_effects([(r['effect'],r['owner']) for r in prepared['effects']],[c['name'] for c in prepared['chars']])
    with compiler_policy():prefix,meta,bindings,scene=compile_battle(prepared,geometry)
    patterns=validate(copy.deepcopy(prepared['enemy']['patterns']),coord=True,squad_size=5)
    bank=pack(spec,patterns,bindings)
    assert len(prefix)==LAYOUT['BASE'] and prepared==before
    meta['enemy_ammo_declarations']=dict(input_words=LAYOUT['INPUT_WORDS'],model='declared-enemy-magazine-attempt-v1',CPU_state_or_schedule_as_input=False)
    return prefix+bank,meta,bindings,scene
