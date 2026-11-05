"""Enemy attack fields: literal full-native programs shared by GPU transports."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('enemy_attack_fields_suite',ROOT/'research/verify-world-actor-fields.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
def field(stat='atk_caster_based_pct',value=-10,target='boss',name='enemy-attack',timing='battle_start',duration=-1,condition=(),**kw):
 return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target=target,duration=duration,trigger=dict(timing=[timing],condition=list(condition)),**kw)
def fixtures():
 base=copy.deepcopy(suite.fixtures()[0]);base.update(duration=.45,observe_enemy_fields=True,observe_enemy_attack_fields=True,observe_named_state=True,allow_shared_enemy_fields=True,observe_counter_field_memberships=True,observe_actor_status=True)
 for a in base['environment']['allies']:a['base_hp']=10000
 base['patterns']=[dict(id='attack',kind='attack',delay=.05,spec=dict(atk=300,coeff=100,target='all',hits=4,interval=.1))]
 rows=[]
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners if owners is not None else [0]*len(effects));rows.append(c);return c
 add('enemy-attack-baseline',[field(stat='atk_pct',value=0,target='self',name='baseline-zero')])
 for stat in ('atk_pct','atk_caster_based_pct'):
  for target in ('boss','target','all_enemies'):
   add(stat+'-'+target,[field(stat=stat,target=target)])
 add('caster-flat-positive',[field(value=10)])
 add('caster-flat-clamped-below-zero',[field(value=-100)])
 add('caster-flat-expiry',[field(duration=.2)])
 add('caster-flat-refresh-stack',[field(max_stack=3,timing='on_attack',duration=.2)])
 add('caster-flat-two-independent-owners',[field(),field()],owners=[0,1])
 add('caster-flat-same-name-alias',[field(),field(value=-20)])
 add('caster-flat-uses-base-not-buffed-caster',[field(),field(stat='atk_pct',value=100,target='self',name='caster-boost')])
 for condition in ('self_hp_above:99','self_hp_below:99','enemy_count_above:2'):
  add('caster-flat-runtime-'+condition,[field(condition=[condition])])
 add('caster-flat-finite-condition-latches',[field(duration=.4,condition=['self_hp_above:99'])])
 for target in ('enemies_top_hp:2','enemies_highest_hp:2','enemies_lowest_hp:2','enemies_nearest:2','enemies_top_def:2','enemies_lowest_def:2','enemies_top_atk:2'):
  c=add('caster-flat-rank-'+target,[field(target=target)])
  c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=3,hp=100000,atk=301)))
 c=add('caster-flat-128-recipients',[field(target='all_enemies')]);c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=127,hp=1000000)))
 c=add('caster-flat-no-late-wave-retarget',[field(target='all_enemies')]);c['patterns'].append(dict(id='late',kind='summon',delay=.2,spec=dict(count=1,hp=100000)))
 c=add('caster-flat-does-not-rebind-reopened-generation',[field(target='all_enemies')]);c['patterns'].append(dict(id='wave',kind='summon',after=['start','wave'],until=dict(time=.1),repeat=0,spec=dict(count=1,hp=100000)))
 for c in rows:c['state_queries']=[(0,0,0,1,c['effects'][0]['name'])]
 return rows
