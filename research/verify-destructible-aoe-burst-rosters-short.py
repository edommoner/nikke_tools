"""Original AoE burst and allied shield modifiers on the common skill Frame."""
import array
import copy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_aoe_burst_roster_cases import fixtures
from world_destructible_weapon_roster_native import observe
from portable_destructible_aoe_burst_contracts import verify
from portable_destructible_roster_input import compile_weapon_shield_roster
from portable_destructible_roster_skill_comparison import compare as shared_compare,prior
from portable_specs import LIMITS as L,FIELDS as F
roster,suite,cross=prior.roster,prior.suite,prior.cross


def prepare():
    rows=[]
    for case in fixtures():
        prepared=roster.engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,meta=compile_weapon_shield_roster(prepared,case['typed_bindings'],max_attacks=case['max_attacks'],skill_shields=True)
        assert len(meta['effects'])==len(prepared['effects'])==case['contract']['prepared_definitions']
        for owner,count in case['contract']['own_definitions'].items():
            assert sum(r['owner']==owner and r['effect'].get('source') in ('스킬1','스킬2','스킬3') for r in prepared['effects'])==count
        rows.append((case['name'],words,(case,meta,prepared,words)))
    _,seed,(_,meta,prepared,_)=rows[0]
    source=next(i for i,r in enumerate(prepared['effects']) if r['owner']=='누아르' and r['effect'].get('stat')=='burst_damage')
    row=meta['binding_source_indices'].index(source);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']
    for label,value in [('aoe-without-burst',seed[at]&~1),('aoe-and-single',seed[at]|8192)]:
        words=list(seed);words[at]=value;rows.append(('reject/destructible-aoe-burst/'+label,words,None))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()


def native_reference(domain):
    result,_=observe(domain[0]);verify(domain[0],result);return result


def compare(block,domain):
    return shared_compare(block,domain,native_reference(domain))


def validate_rejection(block,name):
    assert name.startswith('reject/destructible-aoe-burst/') and block[0]==64,(name,block[0])
