"""One authored CPU/Metal/CUDA table for named handler completion."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('chain_damage_prior',ROOT/'research/verify-world-damage-accum-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
suite,cross=prior.suite,prior.cross
from portable_projectile_chain_cases import fixtures
from portable_projectile_chain_contracts import verify
from world_projectile_chain_native import observe
from portable_specs import LIMITS as L,FIELDS as F

def prepare():
    rows=[]
    for c in fixtures():
        if c['contract'].get('reference_model_gap'):
            try:suite.compile_case(c)
            except ValueError:continue
            raise AssertionError('Reference model gap must remain statically rejected: '+c['name'])
        w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    seed=rows[0][1];source=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];listener=source+L['DEFINITION_WORDS'];event=L['EVENT_BASE']+2*L['EVENT_WORDS']
    for label,offset,value in [('source-kind',source+F['KIND'],4),('source-pending',L['DAMAGE_DEFINITION_BASE']+8+6,1),('event-world',L['WORLD_FRAME_INPUT_BASE'],0),('event-threshold',event+2,0x3ff00000),('event-mode',event+3,1),('event-name',event+4,0xffffffff),('event-payload',event+5,1),('event-stage',event+7,1)]:
        w=list(seed);assert w[offset]!=value;w[offset]=value;rows.append(('reject/projectile-chain-'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);return dict(battle=n,skill_trace=t)
def compare(block,domain):
    expected=native_reference(domain);bare=dict(expected['battle']);bare.pop('projectile_chain')
    prior.prior.prior.prior.prior.prior.landing.base.compare_expected(block,domain,dict(expected,battle=bare));return expected
def validate_rejection(block,name):assert name.startswith('reject/projectile-chain-') and block[0]==64,(name,block[0])
