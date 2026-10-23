"""Shared partial-charge controls and all native contracts, plus raw negatives."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('partial_charge_base',ROOT/'research/verify-world-ally-burst-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_nonfull_charge_cases import fixtures
from portable_nonfull_charge_contracts import verify
from world_nonfull_charge_native import observe
from portable_specs import LIMITS as L
from portable_charge_control_specs import CLICK_BASE
from portable_partial_charge_state import validate_state


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];p=L['WORLD_CONTROL_INPUT_BASE'];row=p+CLICK_BASE;event=L['EVENT_BASE']+L['EVENT_WORDS']
    assert seed[event]==40 and seed[p+1]==2 and seed[row]==1
    bad=[('old-version',[(p+1,1)]),('zero-mask',[(p+5,0)]),('version3',[(p+1,3)]),('wrong-owner-mask',[(p+5,2)]),('unknown-mode',[(row,5)]),('hold-zero',[(row+6,0),(row+7,0)]),('hold-nan',[(row+7,0x7ff80000)]),('charge-negative',[(row+9,0xbff00000)]),('release-infinite',[(row+11,0x7ff00000)]),('post-negative',[(row+13,0xbff00000)]),('full-interval-nan',[(row+15,0x7ff80000)]),('threshold-zero',[(event+1,0),(event+2,0)]),('threshold-fraction',[(event+1,0),(event+2,0x3ff80000)]),('counter-mode',[(event+3,0)]),('named-tag',[(event+4,0)]),('event-value',[(event+5,1)]),('passive',[(event+6,1)]),('invalid-stage',[(event+7,0)]),('no-world',[(L['WORLD_FRAME_INPUT_BASE'],0)]),('no-combat',[(3,0)]),('tap-burst-chain',[(row+1,2)]),('tap-after-own-fb',[(row+1,4)])]
    for name,changes in bad:
        words=list(seed)
        for at,value in changes:words[at]=value
        assert words!=seed,name
        entries.append(('reject/partial-charge-'+name,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native);native.pop('nonfull_charge');return dict(battle=native,skill_trace=trace)


def compare(block,domain):
    case,metadata,bindings=domain;validate_state(block,metadata['_control_policy']);expected=native_reference(domain);actual=suite.decoded(block,metadata,case,bindings)
    changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
    assert block[0]==0 and not changed,(case['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,metadata)==expected['skill_trace'],(case['name'],'full skill trace')
    return expected


def validate_rejection(block,name):assert name.startswith('reject/partial-charge-') and block[0]==64
