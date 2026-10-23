"""Shared caster-owned stage contracts and strict raw descriptor rejection."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('squad_stage_base',ROOT/'research/verify-world-ally-burst-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_squad_stage_cases import fixtures
from portable_squad_stage_contracts import verify
from world_ally_burst_native import observe
from portable_specs import LIMITS as L


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[2][1]
    event=next(L['EVENT_BASE']+i*L['EVENT_WORDS'] for i in range(len(entries[2][2][0]['effects'])) if seed[L['EVENT_BASE']+i*L['EVENT_WORDS']]==41)
    for label,at,value in [('stage0',event+7,0),('stage4',event+7,4),('stage-negative',event+7,0xffffffff),('threshold-mismatch',event+2,0x40000000),('counter-mode',event+3,1),('named-tag',event+4,0),('value',event+5,1),('passive',event+6,1),('no-world',L['WORLD_FRAME_INPUT_BASE'],0),('no-combat',3,0),('reserved-stage-bit',L['WEAPON_BASE']+3,0x801),('invalid-logical-stage',L['WEAPON_BASE']+3,0x305),('auto-on-fixed-stage',L['WEAPON_BASE']+3,0x301),('auto-with-explicit',L['WEAPON_BASE']+3,0x704)]:
        assert seed[at]!=value,('Raw rejection must change its seed',label)
        words=list(seed);words[at]=value;entries.append(('reject/squad-stage-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native);native.pop('ally_burst_events');return dict(battle=native,skill_trace=trace)


def compare(block,domain):
    case,metadata,bindings=domain;expected=native_reference(domain);actual=suite.decoded(block,metadata,case,bindings)
    changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
    assert block[0]==0 and not changed,(case['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,metadata)==expected['skill_trace'],(case['name'],'full skill trace')
    return expected


def validate_rejection(block,name):assert name.startswith('reject/squad-stage-') and block[0]==64
