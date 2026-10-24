"""Full actual battle comparator, augmented only by private modifier lowering."""
import array,copy,importlib.util,sys,types
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_specs import LIMITS as L,FIELDS as F
from destructible_battle_runtime import typed_battle
from destructible_damage_policy import modifier_axis
from destructible_modifier_battle_cases import fixtures
s=importlib.util.spec_from_file_location('modifier_battle_base',ROOT/'research/verify-destructible-battle-short.py');battle=importlib.util.module_from_spec(s);s.loader.exec_module(battle)
suite=types.SimpleNamespace(INPUT=109824,OUTPUT=1048576);cross=battle.cross
AXES={'projectile_dmg_pct':2,'shield_dmg_pct':3}

def compile_case(c):
    lowered=copy.deepcopy(c)
    for effect in lowered['effects']:
        if modifier_axis(effect):
            effect['stat']='atk_dmg_pct'
    w,(_,meta,bindings)=battle.compile_case(lowered)
    extra=[0x444d4231]+[0]*287
    for row,index in enumerate(meta['binding_source_indices']):
        axis=AXES.get(c['effects'][index].get('stat'),0);extra[32+row]=axis
        if axis:
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];assert w[at+F['KIND']]==0
            w[at+F['KIND']]=4;w[at+F['STAT']]=0
    w.extend(extra);return w,(c,meta,bindings)

def prepare():
    rows=[(c['name'],*compile_case(c)) for c in fixtures()];seed=rows[0][1]
    for label,offset,value in [('magic',109536,0),('reserved',109537,1),('unknown-axis',109568,4),('unused-axis',109568+255,2),('axis-on-skill',109568+1,2),('numeric-carrier',L['DEFINITION_BASE']+F['KIND'],0)]:
        w=list(seed);w[offset]=value;rows.append(('reject/destructible-modifier-battle/'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    with patch.object(battle,'typed_battle',lambda bindings,**kw:typed_battle(bindings,modifier_model=True,**kw)):
        return battle.native_reference(domain)

def compare(block,domain):
    observations=[]
    @contextmanager
    def scoped(bindings,**kw):
        with typed_battle(bindings,modifier_model=True,**kw) as data:
            observations.append(data);yield data
    with patch.object(battle,'typed_battle',scoped):
        return battle.compare(block,domain,coefficient_samples=lambda:[row['coefficient'] for row in observations[0]['attacks']])

def validate_rejection(block,name):assert name.startswith('reject/destructible-modifier-battle/') and block[0]==64,(name,block[0])
