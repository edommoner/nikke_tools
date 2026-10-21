"""Explicit queries must not inherit a completion target through an empty cache."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','tests','research')]
from enemy_recipient_cases import prepare,NAMES
from enemy_recipient_runtime import current_label
from effect_runtime import state
from impact_specs import ActorHandle,EventFrame
from calculator.buff_manager import BuffManager

class EnemyQueryScopeContracts(unittest.TestCase):
 def manager(self):
  bm,boss,enemy,registry=prepare();boss.begin_frame(0,enemy);self.assertFalse(state(bm).resources.get('enemy_recipient_fields'))
  state(bm).event_stack.append(EventFrame('event:target_counter_complete:marker',NAMES[0],0,target=ActorHandle(5,1,1)))
  return bm,boss
 def test_neutral_enemy_field_cannot_change_explicit_body_damage_query(self):
  s=importlib.util.spec_from_file_location('scope_queue','research/characterize-world-counter-damage-queue.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  results=[]
  for c in m.fixtures()[-2:]:
   r=m.observe(c);results.append([e['packet']['damage'] for e in r['target_counters']['events'] if e['event']=='impact_before' and e['packet']['family']==1])
  self.assertEqual(results,[[511],[511]])
 def test_empty_enemy_fields_still_respect_explicit_body_query_and_restore_parent(self):
  bm,boss=self.manager();seen=[];original=BuffManager._build_plan
  def build(manager,*args,**kwargs):seen.append(current_label(manager));return original(manager,*args,**kwargs)
  with patch.object(BuffManager,'_build_plan',build):bm.get_buffs(NAMES[0],'__enemy__',0)
  self.assertEqual(seen,['__enemy__']);self.assertEqual(current_label(bm),boss._runs[0].adds[1].id);self.assertEqual(state(bm).enemy_query_stack,[])
 def test_nested_explicit_queries_restore_each_scope_without_enemy_carriers(self):
  bm,boss=self.manager();seen=[];original=BuffManager._build_plan;inside=False;target=boss._runs[0].adds[0].id
  def build(manager,*args,**kwargs):
   nonlocal inside
   seen.append(current_label(manager))
   if not inside:
    inside=True;manager.get_buffs(NAMES[0],target,0);seen.append(current_label(manager))
   return original(manager,*args,**kwargs)
  with patch.object(BuffManager,'_build_plan',build):bm.get_buffs(NAMES[0],'__enemy__',0)
  self.assertEqual(seen,['__enemy__',target,'__enemy__']);self.assertEqual(current_label(bm),boss._runs[0].adds[1].id);self.assertEqual(state(bm).enemy_query_stack,[])
 def test_query_exception_restores_parent_even_without_enemy_fields(self):
  bm,boss=self.manager();parent=state(bm).event_stack[-1]
  with patch.object(BuffManager,'_build_plan',side_effect=ValueError('empty-query witness')):
   with self.assertRaisesRegex(ValueError,'empty-query witness'):bm.get_buffs(NAMES[0],'__enemy__',0)
  self.assertEqual(state(bm).enemy_query_stack,[]);self.assertIs(state(bm).event_stack[-1],parent);self.assertEqual(current_label(bm),boss._runs[0].adds[1].id)
if __name__=='__main__':unittest.main()
