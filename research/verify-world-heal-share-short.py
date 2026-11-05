"""All43 native share contracts through the existing full-battle decoder."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('heal_world_storage',ROOT/'research/verify-world-healing-storage-short.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
base=storage.base;suite,cross=base.suite,base.cross
from portable_heal_share_contracts import verify
from world_heal_share_native import observe

def fixtures():
    from portable_heal_share_cases import fixtures as a
    from portable_heal_share_extra_cases import fixtures as b
    from portable_heal_share_target_cases import fixtures as c
    from portable_heal_share_lifesteal_cases import fixtures as d
    return a()+b()+c()+d()
def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    assert len(entries)==43
    from portable_specs import LIMITS as L,FIELDS as F
    seed=entries[1][1];at=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];health=L['HEALTH_DEFINITION_BASE']+L['HEALTH_DEFINITION_WORDS']
    raw=[('kind',at+F['KIND'],6),('nan',at+F['VALUE']+1,0x7ff80000),('infinite',at+F['VALUE']+1,0x7ff00000),
         ('health-scaling',health,1),('allied-flags',health+1,1),('enemy',health+3,1),('damage-flags',at+F['DAMAGE_FLAGS'],1),
         ('quantity-flags',L['DEFINITION_EXTRA_BASE']+L['DEFINITION_EXTRA_WORDS']+3,1),
         ('query-resolve',L['RECIPIENT_BASE']+8+7,seed[L['RECIPIENT_BASE']+8+7]|4),('no-combat',3,0)]
    for name,offset,value in raw:
        words=list(seed);words[offset]=value;entries.append(('reject/heal-share-'+name,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    case,_,_=domain;native,trace=observe(case);verify(case,native)
    # The optional profiling stream has no existing battle serializer. Keep
    # every native battle field and the unchanged full skill trace; a separate
    # diagnostic suite will compare plan/portion/original-notification order.
    native.pop('heal_share_events')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):
    case,metadata,bindings=domain;expected=native_reference(domain)
    return compare_expected(block,domain,expected)
def compare_expected(block,domain,expected):
    case,metadata,bindings=domain
    actual=suite.decoded(block,metadata,case,bindings)
    actual['healing_storage']=storage.decoded_storage(block,metadata,case)
    changed=[key for key in expected['battle'] if key!='scope' and actual[key]!=expected['battle'][key]]
    assert block[0]==0 and not changed,(case['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,metadata)==expected['skill_trace'],(case['name'],'skill trace')
    return expected
def validate_rejection(block,name):
    assert name.startswith('reject/heal-share-') and block[0]==64
