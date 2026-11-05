"""Full-native periodic timing, ownership and live numeric sampling; GPU0."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('dot_native_suite',ROOT/'research/verify-world-skills.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
def fixtures():
 c=copy.deepcopy(next(c for c in suite.fixtures() if c['name']=='counter-free-world-skill-boss'));c.update(name='dot-default',duration=.65,observe_authored_effect_lookup=True);c['patterns']=[dict(id='idle',kind='idle',until={'time':.65})]
 c['effects']=[dict(name='dot',source='스킬1',type='damage',stat='dot_damage',fixed_value=25,target='boss',duration=.35,tick_interval=.1,trigger=dict(timing=['battle_start'],condition=[]))];c['owners']=[0];rows=[c]
 for start in ('immediate','delayed'):
  q=copy.deepcopy(c);q['name']='dot-'+start;q['effects'][0]['tick_start']=start;rows.append(q)
 q=copy.deepcopy(c);q['name']='dot-membership-excludes-late-wave';q['effects'][0]['target']='all_enemies';q['patterns'].extend([dict(id='early',kind='summon',spec=dict(count=1,hp=10000)),dict(id='late',kind='summon',delay=.2,spec=dict(count=1,hp=10000))]);rows.append(q)
 for stacks in (1,3):
  q=copy.deepcopy(c);q['name']='dot-reapplication-stacks-'+str(stacks);q['effects'][0]['trigger']['timing'].append('every:0.2s');q['effects'][0]['max_stack']=stacks
  if stacks==3:q['effects'][0]['scaling']='stack_count'
  rows.append(q)
 for stat,target,timing in [('atk_pct','self','every:0.2s'),('received_dmg_pct','boss','battle_start')]:
  q=copy.deepcopy(c);q['name']='dot-live-'+stat;q['effects'].append(dict(name='numeric-change',source='스킬1',type='buff',stat=stat,fixed_value=50,target=target,duration=-1,trigger=dict(timing=[timing],condition=[])));q['owners'].append(0);rows.append(q)
 for start in ('immediate','delayed'):
  q=copy.deepcopy(suite.fixtures()[0]);q.update(name='dot-created-by-shot-counter-'+start,duration=.65,observe_authored_effect_lookup=True);q['patterns'][0]['until']={'time':.65}
  e=next(e for e in q['effects'] if e.get('type')=='damage');e.update(stat='dot_damage',duration=.35,tick_interval=.1,tick_start=start);rows.append(q)
 q=copy.deepcopy(rows[-2]);q['name']='dot-immediate-samples-after-counter-buff';q['effects'].append(dict(name='after-dot-apply',source='스킬1',type='buff',stat='atk_pct',fixed_value=50,target='self',duration=-1,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[])));q['owners'].append(0);rows.append(q)
 return rows
