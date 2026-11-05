"""Literal periodic programs shared by CPU, CUDA and Metal, including aliases."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('periodic_native_contract',ROOT/'research/characterize-world-dot-skills.py');contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)
suite=contract.suite;L=suite.L
def compile_case(case):
 w,m,b=suite.compile_case(case);w[0]=L['WORLD_PERIODIC_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=11;return w,m,b
def fixtures():
 rows=copy.deepcopy(contract.fixtures());base=rows[0]
 c=copy.deepcopy(base);c['name']='periodic-all128';c['effects'][0]['target']='all_enemies';c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=127,hp=1000000)));rows.append(c)
 c=copy.deepcopy(rows[3]);c['name']='periodic-alias-union-freezes-existing-tick';e=copy.deepcopy(c['effects'][0]);e['trigger']['timing']=['every:0.2s'];c['effects'].append(e);c['owners'].append(0);rows.append(c)
 c=copy.deepcopy(base);c['name']='periodic-does-not-rebind-reopened-generation';c['effects'][0]['target']='all_enemies';c['patterns'].append(dict(id='wave',kind='summon',after=['start','wave'],repeat=0,until=dict(time=.1),spec=dict(count=1,hp=10000)));rows.append(c)
 for target in ('enemies_top_hp:2','enemies_highest_hp:2','enemies_lowest_hp:2','enemies_nearest:2','enemies_top_def:2','enemies_lowest_def:2','enemies_top_atk:2'):
  c=copy.deepcopy(base);c['name']='periodic-captured-rank-'+target;c['effects'][0]['target']=target;c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=3,hp=10000)));rows.append(c)
 for family in ('bonus_damage','burst_damage','sequential_damage:3'):
  c=copy.deepcopy(base);c['name']='non-dot-periodic-'+family;c['effects'][0]['stat']=family;rows.append(c)
 c=copy.deepcopy(base);c['name']='periodic-normal-formula-is-skill-family';c['effects'][0]['damage_formula']='normal_attack';c['effects'].append(dict(name='normal-boost',source='스킬1',type='buff',stat='normal_atk_dmg_pct',fixed_value=50,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0);rows.append(c)
 c=copy.deepcopy(base);c['name']='periodic-dot-counter-before-child-damage';e=copy.deepcopy(c['effects'][0]);e.update(name='dot-counter-child',stat='bonus_damage');e.pop('tick_interval');e.pop('duration');e['trigger']['timing']=['event:target_counter_complete:dot-marker']
 # Counter and ordinary child use the same target-event executor as pending.
 from target_counter_cases import marker
 counter=marker(name='dot-marker',threshold=1,actor=dict(kind='body',identity=0,generation=1),families=['dot']);counter['trigger']['timing']=['battle_start'];counter['target']='boss'
 c['effects'].extend([counter,e]);c['owners'].extend([0,0]);rows.append(c)
 c=copy.deepcopy(base);c['name']='periodic-reference-stack-snapshot';c['effects'][0].update(scaling='stack_count',scaling_ref='Reference');c['effects'].append(dict(name='reference',source='스킬1',type='instant',stat='gauge_charge',fixed_value=2,target='self',gauge_id='Reference',trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0);rows.append(c)
 c=copy.deepcopy(rows[3]);c['name']='periodic-target-state-body-initial-and-late';c['duration']=.25;c['patterns'][0]['until']={'time':.25};c['observe_named_state']=True;c['state_queries']=[(0,0,0,1,'dot'),(0,5,0,1,'dot'),(0,5,1,1,'dot')];rows.append(c)
 c=copy.deepcopy(rows[13]);c['name']='periodic-target-state-reopened-generation';c['duration']=.25;c['patterns'][0]['until']={'time':.25};c['observe_named_state']=True;c['state_queries']=[(0,0,0,1,'dot'),(0,5,0,3,'dot')];rows.append(c)
 c=copy.deepcopy(base);c['name']='periodic-live-runtime-target-state';c['effects'].append(dict(name='runtime-dot-condition',source='스킬1',type='buff',stat='atk_pct',fixed_value=50,target='self',duration=-1,trigger=dict(timing=['passive'],condition=['target_state:dot'])));c['owners'].append(0);rows.append(c)
 for index,label in [(2,'lethal'),(4,'surviving')]:
  c=copy.deepcopy(suite.fixtures()[index]);c.update(name='periodic-'+label+'-add-counter-and-recovery',duration=.45,observe_authored_effect_lookup=True);c['patterns'][0]['until']={'time':.45};e=next(e for e in c['effects'] if e.get('type')=='damage');e.update(stat='dot_damage',duration=.35,tick_interval=.1,tick_start='immediate');rows.append(c)
 for row in rows:row['observe_periodic_skills']=True
 return rows
