"""The same authored22 weapon cases, full111 retention and shared comparator."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_weapon_shield_cases import fixtures
s=importlib.util.spec_from_file_location('weapon_shield_base',ROOT/'research/verify-destructible-hit-shield-short.py');hit=importlib.util.module_from_spec(s);s.loader.exec_module(hit)
shield=hit.base;battle=shield.battle;suite=hit.suite;cross=hit.cross

def compile_case(c):
    if c.get('enemy',{}).get('coord') is not None:raise ValueError('Weapon shield coordinate policy is not declared')
    c=dict(c,shield_interception_v1=True)
    w,domain=shield.compile_case(c,allow_weapon_only=True);w[110080]=0x48534933;w[110084]=int(c.get('hit_shield_interception_v1',False));w[110085]=1
    if w[110084]:
        for row in range(256):
            if w[109824+row]==3:w[109824+row]=4
    return w,domain

def prepare():
    rows=hit.prepare()[0];rows.extend((c['name'],*compile_case(c)) for c in fixtures());seed=rows[111][1]
    for name,offset,value in [('weapon-flag',110085,0),('hit-flag',110084,2),('reserved',110086,1),('unknown-magic',110080,0),('max-trace',109521,0)]:
        w=list(seed);w[offset]=value;rows.append(('reject/destructible-weapon-shield/'+name,w,None))
    from world_enemy_attack_cases import field
    for stat in ('lifesteal_pct','dmg_accum_dealt_atk_pct','pierce_enabled'):
        c=copy.deepcopy(fixtures()[0]);c['effects'].append(field(stat,1,'self','rejected-field'));c['owners'].append(0)
        rows.append(('reject/destructible-weapon-shield/'+stat,compile_case(c)[0],None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

native_reference=hit.native_reference
def compare(block,domain):
    observations=[];c=domain[0]
    def sources():
        names=battle.roster_names(c);answer=[]
        for row in observations[0]['attacks']:
            if 'family' in row:answer.append(None);continue
            matches=[i for i,e in enumerate(c['effects']) if e.get('name')==row['name'] and c['owners'][i]==names.index(row['caster'])];assert len(matches)==1;answer.append(matches[0])
        return answer
    with shield.scope(c,observations):
        return battle.compare(block,domain,coefficient_samples=lambda:[r['coefficient'] for r in observations[0]['attacks']],source_samples=sources,packet_samples=lambda:[r.get('weapon_mode_skill',False) for r in observations[0]['attacks']])

def validate_rejection(block,name):
    if name.startswith('reject/destructible-weapon-shield/'):assert block[0]==64,(name,block[0])
    else:hit.validate_rejection(block,name)
