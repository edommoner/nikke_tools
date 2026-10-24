"""Original skill selectors and burst flags on the shared typed Frame."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_skill_roster_cases import fixtures
from world_destructible_weapon_roster_native import observe
from portable_destructible_skill_roster_contracts import verify
from portable_destructible_roster_input import compile_weapon_shield_roster
from destructible_skill_shield_policy import skill
from portable_specs import LIMITS as L,FIELDS as F
s=importlib.util.spec_from_file_location('skill_roster_prior',ROOT/'research/verify-destructible-weapon-rosters-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
roster,suite,cross=prior.roster,prior.suite,prior.cross

def prepare():
    rows=[]
    for c in fixtures():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=compile_weapon_shield_roster(p,c['typed_bindings'],max_attacks=c['max_attacks'],skill_shields=True)
        assert len(m['effects'])==len(p['effects'])==c['contract']['prepared_definitions']
        rows.append((c['name'],w,(c,m,p,w)))
    seed=rows[1][1];row=rows[1][2][1]['binding_source_indices'].index(1);definition=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];damage=L['DAMAGE_DEFINITION_BASE']+row*8
    mutations=[('weapon-flag',110085,0),('old-header',110080,0x48534933),('reserved',110086,1),('hit-flag',110084,2),('unknown-route',109824+row,5),('random-selector',damage,10),('inherited-selector',damage,0),('zero-count',damage+1,0),('over-count',damage+1,129),('multi-hit',damage+2,2),('normal-formula',damage+3,1),('pierce-family',definition+F['DAMAGE_FLAGS'],64)]
    for label,at,value in mutations:
        w=list(seed);w[at]=value;rows.append(('reject/destructible-skill-rosters/'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    n,_=observe(domain[0]);verify(domain[0],n);return n

def compare(block,domain):
    c,m,p,w=domain;n=native_reference(domain)
    _,_,_,diff=roster.compare(block,p,(w,m),n['battle'],n['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    names=c['body']['squad'];case=dict(c,names=names,effects=[r['effect'] for r in p['effects']],owners=[names.index(r['owner']) for r in p['effects']])
    chars={r['name']:r for r in p['chars']};metadata=[]
    for packet,sample in zip(n['packet_samples'],n['shield_samples'],strict=True):
        source=packet['source']
        if source is None:metadata.append(None);continue
        e=p['effects'][source];plan=skill(e['effect'],chars[e['owner']]);flags=sample['family_flags']
        bits=int(flags['is_burst_damage'])|4096*int(flags['is_aoe_burst'])|8192*int(flags['is_single_burst'])
        metadata.append([1,2,plan['route'],bits,128 if plan['route']==2 else plan['count']])
    decoded=prior.prior.battle.decode(block,(case,m,()),sampled_coefficients=[r['coefficient'] for r in n['packet_samples']],sampled_rows=[r['source'] for r in n['packet_samples']],sampled_packets=[r['mode_skill'] for r in n['packet_samples']],sampled_skill_metadata=metadata)
    assert decoded==n['typed'],(c['name'],decoded,n['typed'])
    assert not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]),'Typed counter context leaked'
    return n

def validate_rejection(block,name):assert name.startswith('reject/destructible-skill-rosters/') and block[0]==64,(name,block[0])
