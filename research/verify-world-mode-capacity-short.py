"""Mode-capacity contracts on the existing full native battle comparator."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('mode_capacity_base',ROOT/'research/verify-world-projectile-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_mode_capacity_cases import fixtures as all_fixtures
from world_mode_capacity_native import observe
from portable_mode_capacity_contracts import verify
from portable_specs import LIMITS as L

def fixtures():return [c for c in all_fixtures() if not c['name'].startswith('mode-capacity-instant-')]
def prepare_cases(cases,*,raw_rejections):
    entries=[]
    for case in cases:
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];at=L['REFERENCE_DEFINITION_BASE']+3
    descriptor=seed[at]
    mutations=[('no-combat',3,0),('unknown-flag',at,descriptor|0x80000000),('zero-key',at,512),('key-range',at,511),('wrong-name',at,descriptor^(1<<9)),('sentinel',L['MODE_BASE']+21,1)] if raw_rejections else []
    for label,offset,value in mutations:
        words=list(seed);words[offset]=value;entries.append(('reject/mode-capacity-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def prepare():return prepare_cases(fixtures(),raw_rejections=True)
def native_reference(domain):
    case,_,_=domain;native,trace=observe(case);verify(case,native);native.pop('mode_capacity')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):
    case,metadata,bindings=domain;expected=native_reference(domain)
    actual=suite.decoded(block,metadata,case,bindings)
    changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
    assert block[0]==0 and not changed,(case['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,metadata)==expected['skill_trace'],(case['name'],'skill trace')
    return expected
def validate_rejection(block,name):
    assert name.startswith('reject/mode-capacity-') and block[0]==64
