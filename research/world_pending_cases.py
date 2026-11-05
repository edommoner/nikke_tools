"""One literal pending fixture table shared by CPU, CUDA and Metal."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('pending_contract_cases',ROOT/'research/characterize-world-pending-skills.py');contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)
suite=contract.suite;L=suite.L
def compile_case(case):
 w,m,b=suite.compile_case(case);w[0]=L['WORLD_PENDING_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=9;return w,m,b
def fixtures():
 rows=copy.deepcopy(contract.fixtures());base=rows[0]
 def append(c,e):c['effects'].append(e);c['owners'].append(0)
 c=copy.deepcopy(base);c['name']='pending-does-not-drain-fullburst-ordinary-child';e=copy.deepcopy(c['effects'][1]);e.update(name='ordinary',stat='burst_damage');e['trigger']['timing']=['full_burst_start'];append(c,e);rows.append(c)
 c=copy.deepcopy(rows[6]);c['name']='pending-counter-child-stays-in-next-frame-ordinary-queue';e=copy.deepcopy(c['effects'][1]);e['name']='ordinary-child';e['trigger']['timing']=['event:target_counter_complete:pending-counter'];append(c,e);rows.append(c)
 c=copy.deepcopy(base);c['name']='pending-all128';c['effects'][1]['target']='all_enemies';c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=127,hp=1000000)));rows.append(c)
 for target in ('enemies_top_hp:2','enemies_highest_hp:2','enemies_lowest_hp:2','enemies_nearest:2','enemies_top_def:2','enemies_lowest_def:2','enemies_top_atk:2'):
  c=copy.deepcopy(rows[5]);c['name']='pending-ranked-'+target;c['effects'][1]['target']=target;rows.append(c)
 c=copy.deepcopy(rows[5]);c['name']='pending-kills-two-adds';c['patterns'][-1]['spec']['hp']=100;rows.append(c)
 c=copy.deepcopy(base);c['name']='pending-recovery-after-counter-publication';append(c,contract.buff('leech','lifesteal_pct',50,timing='battle_start'));append(c,dict(name='reduce-before-pending',source='스킬3',type='instant',stat='current_hp_reduce',fixed_value=50,target='self',trigger=dict(timing=['full_burst_start'],condition=[])));rows.append(c)
 c=copy.deepcopy(rows[6]);c['name']='pending-two-different-amounts-before-first-counter-child';c['effects'][2]['fixed_value']=50;rows.append(c)
 for value in (None,0,2):
  c=copy.deepcopy(base);c['name']='pending-reference-'+str(value);c['effects'][1].update(scaling='stack_count',scaling_ref='Reference')
  if value is not None:append(c,dict(name='initial-reference',source='스킬1',type='instant',stat='gauge_charge',fixed_value=value,gauge_id='Reference',target='self',trigger=dict(timing=['battle_start'],condition=[])))
  rows.append(c)
 c=copy.deepcopy(base);c['name']='pending-three-named-hits';c['effects'][1]['target']='same_target:reference-attack';e=copy.deepcopy(c['effects'][1]);e.update(name='reference-attack',stat='sequential_damage:3',fixed_value=10,target='boss');e['trigger']['timing']=['battle_start'];append(c,e);rows.append(c)
 for row in rows:row['observe_pending_skills']=True
 return rows
