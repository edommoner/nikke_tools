"""Existing shared healing/landing code, with actual native recipient receipts."""
import array,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_body_heal_share_cases import fixtures
from world_destructible_heal_share_native import observe
from portable_destructible_roster_input import compile_weapon_shield_roster
from portable_destructible_roster_skill_comparison import compare as shared_compare,prior
from portable_damage_accum_observation import compare_final
roster,suite,cross=prior.roster,prior.suite,prior.cross
def prepare():
    rows=[]
    for c in fixtures():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True))
        w,m=compile_weapon_shield_roster(p,c['typed_bindings'],max_attacks=c['max_attacks'],skill_shields=True,body_lifesteal=True,body_accumulation=True)
        assert len(m['effects'])==len(p['effects']);rows.append((c['name'],w,(c,m,p,w)))
    data=array.array('I',[len(rows)])
    for _,w,_ in rows:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()
def native_reference(domain):
    c=domain[0];n,_=observe(c);assert n['typed']['finished'] and n['healing_recipients']
    plans=[e for e in n['heal_share_events'] if e['kind']=='plan'];assert any(len(e['weights'])>=3 for e in plans)
    assert any(e['weights']==[(1,1),(2,1),(3,1)] for e in plans)
    if c['contract']['duration']==30:
        # Rem + two RL members have two links after Rem's party-wide burst
        # carrier joins the original three-member carrier: 2/8 vs 1/8.
        assert any(e['weights']==[(0,1),(1,2),(2,2),(3,2),(4,1)] for e in plans)
    if c['contract']['mode'] in ('hp','hit'):
        assert not any(168<=round(e['time']*60)<192 for e in n['body_lifesteal'])
    assert any(r['after']>r['before'] for r in n['healing_recipients'])
    # Body clamping returns before the caller assigns HP and synchronizes edges.
    portions=[e for e in n['heal_share_events'] if e['kind']=='portion-return']
    assert [(e['owner'],e['time'],e['amount'],e['after']) for e in portions]==[(e['owner'],e['time'],e['amount'],e['after']) for e in n['healing_recipients']]
    return n
def compare(block,domain):
    n=native_reference(domain);shared_compare(block,domain,n);compare_final(block,domain[1],n['damage_accumulation']);return n
