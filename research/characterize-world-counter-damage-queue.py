"""Native creation/landing timing and damage basis for completion damage children."""
import copy,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from effect_runtime import state
from world_frame_native import observe
s=importlib.util.spec_from_file_location('damage_queue_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
def fixtures():
 sources={c['name']:c for c in physical.fixtures()};rows=[]
 for source in ('body-completion-versus-lifesteal-order','add-completion-versus-lifesteal-order','add-survives-completion-versus-lifesteal-order'):
  for duration in (.01,.15):
   c=copy.deepcopy(sources[source]);c.update(name=source+'-damage-child-duration-'+str(duration),duration=duration)
   c['effects'][-1]=dict(name='queued-child',source='스킬1',type='damage',stat='bonus_damage',fixed_value=25,target='target',trigger=dict(timing=['event:target_counter_complete:marker'],condition=[]));rows.append(c)
 base=copy.deepcopy(rows[-1])
 for target in ('boss','target'):
  c=copy.deepcopy(base);c['name']='completion-damage-body-basis-field-'+target
  c['effects'].insert(-1,dict(name='basis-field',source='스킬1',type='buff',stat='received_dmg_pct',fixed_value=25,target=target,duration=.3,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[])));c['owners'].insert(-1,0);rows.append(c)
 c=copy.deepcopy(rows[2]);c['name']='named-skill-hit-child-inherits-lethal-add-completion-target'
 c['effects'].append(dict(name='queued-context-probe',source='스킬1',type='buff',stat='lifesteal_pct',fixed_value=40,target='self',duration=.3,trigger=dict(timing=['hit_count:queued-child:1'],condition=['target_is_add'])));c['owners'].append(0);rows.append(c)
 c=copy.deepcopy(rows[2]);c['name']='queued-skill-allied-runtime-condition-queries-body'
 c['effects'].insert(-1,dict(name='body-query-attack',source='스킬1',type='buff',stat='atk_pct',fixed_value=100,target='self',duration=-1,trigger=dict(timing=['passive'],condition=['target_state:marker'])));c['owners'].insert(-1,0);rows.append(c)
 c=copy.deepcopy(c);c['name']='queued-skill-body-query-with-neutral-enemy-field'
 c['effects'].insert(0,dict(name='query-scope-witness',source='스킬1',type='buff',stat='received_dmg_pct',fixed_value=0,target='boss',duration=.3,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].insert(0,0);rows.append(c)
 return rows
def main():
 from calculator.buff_manager import BuffManager
 from calculator.timeline import DT
 result=[]
 for case in fixtures():
  created=[];condition_rows=[];original=BuffManager.notify;original_condition=BuffManager._condition_ok
  def condition(manager,conditions,caster,t,eff=None):
   accepted=original_condition(manager,conditions,caster,t,eff)
   if eff is not None and eff.get('name')=='queued-context-probe':
    frame=state(manager).event_stack[-1];condition_rows.append(dict(event=frame.event,target_kind=int(frame.target.kind) if frame.target else None,accepted=accepted))
   return accepted
  def notify(manager,event,t,caster,*args,**kwargs):
   if event=='hit_count:queued-child':
    frames=state(manager).event_stack;parent=frames[-1] if frames else None
    created.append(dict(time=t,parent=parent.event if parent else None,parent_target_kind=int(parent.target.kind) if parent and parent.target else None))
   return original(manager,event,t,caster,*args,**kwargs)
  with patch.object(BuffManager,'notify',notify),patch.object(BuffManager,'_condition_ok',condition):native=observe(case)
  impacts=[e for e in native['target_counters']['events'] if e['event']=='impact_before' and e['packet']['family']==1]
  assert len(created)==len(impacts)==1 and created[0]['time']==0
  assert impacts[0]['time']==min(case['duration'],DT)
  result.append(dict(name=case['name'],creation_notifications=created,named_hit_predicates=condition_rows,skill_impacts=impacts,native=native))
 by={r['name']:r for r in result}
 assert by['completion-damage-body-basis-field-boss']['skill_impacts'][0]['packet']['damage']>by['completion-damage-body-basis-field-target']['skill_impacts'][0]['packet']['damage']
 # The lethal add is the predicate/completion target, but queued damage resolves
 # the live aim at landing and therefore hits the body after that add died.
 fatal=by['add-completion-versus-lifesteal-order-damage-child-duration-0.01']
 assert fatal['creation_notifications'][0]['parent_target_kind']==5 and fatal['skill_impacts'][0]['packet']['target']['kind']==0
 named=by['named-skill-hit-child-inherits-lethal-add-completion-target']['named_hit_predicates'];assert named==[dict(event='hit_count:queued-child',target_kind=5,accepted=True)]
 unscoped=by['queued-skill-allied-runtime-condition-queries-body']['skill_impacts'][0]['packet']['damage'];scoped=by['queued-skill-body-query-with-neutral-enemy-field']['skill_impacts'][0]['packet']['damage']
 assert unscoped==fatal['skill_impacts'][0]['packet']['damage'] and scoped>unscoped
 report=dict(passed=True,cases=result,case_count=11,gpu_calls=0,typed_damage_gpu_connected=False,native_query_scope_finding=dict(status='OPEN',without_enemy_field_damage=unscoped,with_neutral_enemy_field_damage=scoped,cause='enemy_recipient_runtime.buffs only pushes explicit body query scope when enemy_recipient_fields is nonempty; allied runtime target predicates otherwise inherit the parent completion target',resolution_required_before_typed_skill_admission=True),findings=['Completion predicates and enemy field recipients retain the immutable Actor','Damage children queue at creation and land at next frame drain or final duration drain','Direct skill amounts query body modifiers once; recipient routing occurs later','A lethal add completion can enqueue a target skill that later lands on current body aim','Named hit_count child notifications inherit completion targets; compiler wire49 must be included for the skill phase','Neutral enemy field changes explicit body-query runtime predicates in native; resolve sparse query adapter inconsistency before porting'],full_goal_complete=False)
 (ROOT/'research/portable-world-counter-damage-queue-native-contract.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Counter damage queue native11:creation/landing/named hits;query-scope inconsistency preserved;GPU0')
if __name__=='__main__':main()
