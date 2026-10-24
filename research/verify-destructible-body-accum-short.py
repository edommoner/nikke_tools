"""Fixed amounts use the same GPU landing lifecycle and typed receipts."""
import array,copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_body_accum_cases import fixtures
from world_destructible_accum_native import observe
from portable_destructible_roster_input import compile_weapon_shield_roster
from portable_destructible_roster_skill_comparison import compare as shared_compare,prior
from portable_damage_accum_observation import compare_final
roster,suite,cross=prior.roster,prior.suite,prior.cross
def prepare():
    rows=[]
    for c in fixtures():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True))
        for effect in c.get('declared_effects',[]):p['effects'].append(dict(owner=c['body']['squad'][0],effect=copy.deepcopy(effect)))
        w,m=compile_weapon_shield_roster(p,c['typed_bindings'],max_attacks=c['max_attacks'],skill_shields=True,body_lifesteal=True,body_accumulation=True)
        assert len(m['effects'])==len(p['effects']);rows.append((c['name'],w,(c,m,p,w)))
    for label,at,value in [('old-lifesteal-header',110080,0x48534935),('missing-accum-policy',110087,0),('unknown-accum-policy',110087,2),('missing-body-policy',110086,0)]:
        w=list(rows[0][1]);w[at]=value;rows.append(('reject/destructible-body-accum/'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,_=observe(domain[0]);assert n['typed']['finished']
    assert not any(e.get('row',-1)<0 for e in n['damage_accumulation']['events'] if 'row' in e)
    c=domain[0]
    if c.get('declared_effects'):
        emits=[e for e in n['damage_accumulation']['events'] if e['kind']=='emission'];assert len(emits)==1
        quantities=[(p,a) for p,a in zip(n['packet_samples'],n['typed']['attacks'],strict=True) if p.get('quantity_only')];assert len(quantities)==1
        expected=emits[0]['amount'];assert quantities[0][1]['damage']==expected
        assert (expected==0)==(c['contract']['label']=='declared-zero-integer')
    return n
def compare(block,domain):
    n=native_reference(domain);shared_compare(block,domain,n);compare_final(block,domain[1],n['damage_accumulation']);return n
def validate_rejection(block,name):assert name.startswith('reject/destructible-body-accum/') and block[0]==64,(name,block[0])
