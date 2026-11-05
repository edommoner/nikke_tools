"""One shared header/Frame path; CPU event traces are observation only."""
import array,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_body_lifesteal_cases import fixtures
from world_destructible_lifesteal_native import observe
from portable_destructible_body_lifesteal_contracts import verify
from portable_destructible_roster_input import compile_weapon_shield_roster
from portable_destructible_roster_skill_comparison import compare as shared_compare,prior
roster,suite,cross=prior.roster,prior.suite,prior.cross

def prepare():
    rows=[]
    for case in fixtures():
        p=roster.engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,meta=compile_weapon_shield_roster(p,case['typed_bindings'],max_attacks=case['max_attacks'],skill_shields=True,body_lifesteal=True)
        assert len(meta['effects'])==len(p['effects'])
        rows.append((case['name'],words,(case,meta,p,words)))
    for label,at,value in [('old-skill-header',110080,0x48534934),('body-policy-missing',110086,0),('body-policy-unknown',110086,2)]:
        words=list(rows[0][1]);words[at]=value;rows.append(('reject/destructible-body-lifesteal/'+label,words,None))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    result,_=observe(domain[0]);verify(domain[0],result);return result

def compare(block,domain):return shared_compare(block,domain,native_reference(domain))

def validate_rejection(block,name):assert name.startswith('reject/destructible-body-lifesteal/') and block[0]==64,(name,block[0])
