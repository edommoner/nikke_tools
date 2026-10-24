"""One input table and comparator for default projectile and shield Frames."""
import array,copy,importlib.util,sys,types
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from destructible_damage_policy import modifier_axis
from destructible_battle_runtime import typed_battle
from destructible_shield_policy import BOSS
from destructible_skill_specs import coefficient
from destructible_shield_battle_cases import fixtures as shields
from destructible_modifier_battle_cases import fixtures as modifiers
from portable_specs import LIMITS as L,FIELDS as F
s=importlib.util.spec_from_file_location('shield_battle_base',ROOT/'research/verify-destructible-battle-short.py');battle=importlib.util.module_from_spec(s);s.loader.exec_module(battle)
suite=types.SimpleNamespace(INPUT=110112,OUTPUT=1048576);cross=battle.cross

def fixtures():
    return [*battle.fixtures(),*modifiers(),*[dict(c,shield_interception_v1=True) for c in shields()]]

def compile_case(c):
    lowered=copy.deepcopy(c);routes={}
    for index,effect in enumerate(lowered['effects']):
        if modifier_axis(effect):effect['stat']='atk_dmg_pct'
        if effect.get('target')=='all_projectiles':routes[index]=2
        elif c.get('shield_interception_v1') and effect.get('target')=='boss' and effect.get('type')=='damage':
            # Validate the same plain skill contract before any target exists.
            coefficient(dict(effect,target='all_projectiles'),dict(name=battle.roster_names(c)[c['owners'][index]],skill_levels=battle.skill_levels(c)[c['owners'][index]]));routes[index]=3
    if not routes:raise ValueError('At least one routed plain skill required')
    primary=next(iter(routes))
    lowered['effects'][primary]['target']='all_projectiles'
    w,(_,meta,bindings)=battle.compile_case(lowered)
    extra=[0]*576;extra[0]=0x444d4231;extra[544:548]=[0x48534931,0,0,1]
    for row,index in enumerate(meta['binding_source_indices']):
        axis=modifier_axis(c['effects'][index]);extra[32+row]=axis;extra[288+row]=routes.get(index,0)
        if axis:
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];assert w[at+F['KIND']]==0
            w[at+F['KIND']]=4;w[at+F['STAT']]=0
    w.extend(extra);assert len(w)==suite.INPUT
    return w,(c,meta,bindings)

def prepare():
    rows=[(c['name'],*compile_case(c)) for c in fixtures()];seed=next(w for n,w,c in rows if n.endswith('/shield-factor-keeps-physical-body'))
    for name,words,domain in battle.prepare()[0]:
        if domain is not None:continue
        extra=[0]*576;extra[0]=0x444d4231;extra[544:548]=[0x48534931,0,0,1]
        row=words[109520]
        if row<256:extra[288+row]=2
        rows.append((name,words+extra,None))
    spec=importlib.util.spec_from_file_location('shield_prior_modifier',ROOT/'research/verify-destructible-modifier-battle-short.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
    for name,words,domain in prior.prepare()[0]:
        if domain is not None:continue
        extra=[0]*288;extra[words[109520]]=2;extra[256:260]=[0x48534931,0,0,1]
        rows.append((name,words+extra,None))
    for label,offset,value in [('magic',109536,0),('reserved',109537,1),('unknown-axis',109568,4),('route-kind',109825,4),('route-on-carrier',109824,3),('unused-route',109824+255,3),('owner-magic',110080,0),('owner-kind',110081,5),('owner-id',110082,1),('owner-generation',110083,2),('owner-reserved',110084,1)]:
        w=list(seed);w[offset]=value;rows.append(('reject/destructible-shield-battle/'+label,w,None))
    # Keep all44 original dispatch indices as well as names; scratch contains
    # absolute output addresses, so moving a case obscures byte retention.
    order=[r[0] for r in battle.prepare()[0]]+[r[0] for r in prior.prepare()[0]]
    by_name={r[0]:r for r in rows};assert len(by_name)==len(rows)
    rows=[by_name[n] for n in order]+[r for r in rows if r[0] not in order]
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

@contextmanager
def scope(c,observations):
    def observed(bindings,**kw):
        @contextmanager
        def capture():
            with typed_battle(bindings,modifier_model=True,shield_owner=BOSS if c.get('shield_interception_v1') else None,hit_shields=c.get('hit_shield_interception_v1',False),**kw) as data:
                observations.append(data);yield data
        return capture()
    with patch.object(battle,'typed_battle',observed):yield

def native_reference(domain):
    with scope(domain[0],[]):return battle.native_reference(domain)

def compare(block,domain):
    observations=[];c=domain[0]
    def sources():
        names=battle.roster_names(c);answer=[]
        for attack in observations[0]['attacks']:
            matches=[i for i,e in enumerate(c['effects']) if e.get('name')==attack['name'] and c['owners'][i]==names.index(attack['caster'])]
            assert len(matches)==1,'Unambiguous native source required';answer.append(matches[0])
        return answer
    with scope(c,observations):
        return battle.compare(block,domain,coefficient_samples=lambda:[r['coefficient'] for r in observations[0]['attacks']],source_samples=sources)

def validate_rejection(block,name):assert name.startswith(('reject/destructible-shield-battle/','reject/destructible-battle/','reject/destructible-modifier-battle/')) and block[0]==64,(name,block[0])
