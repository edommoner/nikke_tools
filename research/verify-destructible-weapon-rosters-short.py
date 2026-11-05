"""Complete original roster through the shared weapon-shield executable."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_weapon_roster_cases import fixtures
from world_destructible_weapon_roster_native import observe
from portable_destructible_weapon_roster_contracts import verify
from portable_destructible_roster_input import compile_weapon_shield_roster
s=importlib.util.spec_from_file_location('weapon_shield_real_comparison',ROOT/'research/verify-world-projectile-rosters.py');roster=importlib.util.module_from_spec(s);s.loader.exec_module(roster)
s=importlib.util.spec_from_file_location('weapon_shield_real_typed',ROOT/'research/verify-destructible-weapon-shield-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
suite=prior.suite;cross=prior.cross

def prepare():
    rows=[];packed=array.array('I')
    for c in fixtures():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=compile_weapon_shield_roster(p,c['typed_bindings'],max_attacks=c['max_attacks'])
        assert len(m['effects'])==len(p['effects'])==c['contract']['all_effects']
        assert sum(x['owner']==c['contract']['profile'] and x['effect'].get('source') in ('스킬1','스킬2','스킬3') for x in p['effects'])==c['contract']['own_effects']
        rows.append((c['name'],w,(c,m,p,w)))
    packed.append(len(rows))
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,_=observe(domain[0]);verify(domain[0],n);return n
def compare(block,domain):
    c,m,p,w=domain;n=native_reference(domain)
    _,_,_,diff=roster.compare(block,p,(w,m),n['battle'],n['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    decoded=prior.battle.decode(block,(c,m,()),sampled_coefficients=[r['coefficient'] for r in n['weapon_samples']],sampled_rows=[None]*len(n['weapon_samples']),sampled_packets=[r['mode_skill'] for r in n['weapon_samples']])
    assert decoded==n['typed'],(c['name'],decoded,n['typed'])
    return n
def validate_rejection(block,name):raise AssertionError('No original roster rejection rows')
