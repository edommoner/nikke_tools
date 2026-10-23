"""Original battle inputs/native oracle shared by CUDA and Metal."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('damage_battle_base',ROOT/'research/verify-world-heal-charge-lifetime-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
suite,cross=prior.suite,prior.cross
from portable_damage_accum_cases import fixtures
from portable_damage_accum_contracts import verify
from world_damage_accum_native import observe
from portable_damage_accum_observation import compare_final
from portable_specs import LIMITS as L,FIELDS as F

def prepare():
    rows=[]
    for c in fixtures():
        w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    seed=rows[0][1];at=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];release=at+L['DEFINITION_WORDS'];packet=L['DAMAGE_DEFINITION_BASE']+2*8
    changes=[('missing-policy',L['PROTECTION_DEFINITION_BASE']+1,0),('wrong-stat',at+F['STAT'],5),('wrong-kind',at+F['KIND'],4),('nonfinite',at+F['VALUE']+1,0x7ff80000),('periodic',at+F['INTERVAL']+1,0x3ff00000),('missing-world',L['WORLD_FRAME_INPUT_BASE'],0),('invalid-policy',L['PROTECTION_DEFINITION_BASE']+1,269),('missing-release-name',release+F['TARGET_NAME'],0xffffffff),('release-two-hits',packet+2,2),('release-gauge',packet+5,0x3ff00000)]
    for label,offset,value in changes:
        w=list(seed);assert w[offset]!=value;(w.__setitem__(offset,value));rows.append(('reject/damage-accum-'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);return dict(battle=n,skill_trace=t)
def compare(block,domain):
    expected=native_reference(domain);battle=dict(expected['battle']);observation=battle.pop('damage_accumulation')
    prior.prior.prior.prior.prior.landing.base.compare_expected(block,domain,dict(expected,battle=battle))
    compare_final(block,domain[1],observation);return expected

def validate_rejection(block,name):assert name.startswith('reject/damage-accum-') and block[0]==64,(name,block[0])
