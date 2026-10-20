"""Authored counter completion predicates; shared native/GPU fixture inputs."""
import copy
from portable_specs import LIMITS as L

def compile_case(physical,case):
 words,meta,bindings=physical.compile_case(case);words[0]=L['COUNTER_CONTEXT_ABI'];words[L['TARGET_COUNTER_INPUT_BASE']+6]=2;return words,meta,bindings

def fixtures(physical):
 sources={c['name']:c for c in physical.fixtures()};rows=[]
 variants=[
  ('body-completion-versus-lifesteal-order',0,'boss'),
  ('add-completion-versus-lifesteal-order',5,'add'),
  ('add-survives-completion-versus-lifesteal-order',5,'add'),
  ('part-50-completion-versus-lifesteal-order',1,'boss'),
  ('nonowner-fatal-add-death-still-completes',5,'add'),
  ('unbreakable-part-extra-hit-keeps-hp-dealt-zero',1,'boss'),
 ]
 for source,kind,logical in variants:
  for predicate in ('target_is_boss','target_is_add'):
   c=copy.deepcopy(sources[source]);child=c['effects'][-1];child['name']='context-probe';child['trigger']['condition']=[predicate]
   c.update(name=source+'-'+predicate,context_expect=dict(kind=kind,condition=predicate,accepted=predicate=='target_is_'+logical));rows.append(c)
 for source in ('body-completion-versus-lifesteal-order','add-completion-versus-lifesteal-order','part-50-completion-versus-lifesteal-order'):
  for predicate,accepted in [('self_state:marker',False),('not_self_state:marker',True),('self_stack_above:marker:1',True)]:
   c=copy.deepcopy(sources[source]);child=c['effects'][-1];child['name']='context-probe';child['trigger']['condition']=[predicate]
   c.update(name=source+'-'+predicate,context_expect=dict(kind=c['effects'][-2]['target_counter']['actor']['kind'],condition=predicate,accepted=accepted));rows.append(c)
 for source in ('body-completion-versus-lifesteal-order','add-completion-versus-lifesteal-order'):
  c=copy.deepcopy(sources[source]);child=c['effects'][-1];child['name']='named-parent'
  child.update(stat='atk_pct',fixed_value=0)
  probe=copy.deepcopy(child);probe.update(name='context-probe',stat='lifesteal_pct',fixed_value=40)
  probe['trigger']=dict(timing=['event:named-parent'],condition=['target_is_add'])
  c['effects'].append(probe);c['owners'].append(c['owners'][-1])
  # Generic named children do not inherit the completion target. In the fatal
  # add case, current aiming has already returned to the body.
  c.update(name=source+'-generic-named-child-clears-target',context_expect=dict(kind=None,condition='target_is_add',accepted=False));rows.append(c)
 for source,kind,present in [('body-completion-versus-lifesteal-order',0,True),('add-completion-versus-lifesteal-order',5,False),('add-survives-completion-versus-lifesteal-order',5,False),('part-50-completion-versus-lifesteal-order',1,True)]:
  for predicate,accepted in [('target_state:marker',present),('not_target_state:marker',not present),('target_stack_above:marker:1',present),('target_stack_above:marker:0',True)]:
   c=copy.deepcopy(sources[source]);child=c['effects'][-1];child['name']='context-probe';child['trigger']['condition']=[predicate]
   c.update(name=source+'-'+predicate,context_expect=dict(kind=kind,condition=predicate,accepted=accepted));rows.append(c)
 for predicate,accepted in [('target_is_add',True),('self_state:marker',False),('self_stack_above:marker:1',True)]:
  c=copy.deepcopy(sources['add-completion-versus-lifesteal-order']);c['effects'][2]['target_counter']['threshold']=100
  child=c['effects'][-1];child['name']='context-probe';child['trigger']['condition']=[predicate]
  c.update(name='fatal-death-completion-without-impact-'+predicate,context_expect=dict(kind=5,condition=predicate,accepted=accepted,impact=False));rows.append(c)
 c=copy.deepcopy(sources['add-survives-completion-versus-lifesteal-order']);child=c['effects'][-1];child['name']='named-parent';child.update(stat='atk_pct',fixed_value=0)
 probe=copy.deepcopy(child);probe.update(name='context-probe',stat='lifesteal_pct',fixed_value=40);probe['trigger']=dict(timing=['event:named-parent'],condition=['target_is_add']);c['effects'].append(probe);c['owners'].append(0)
 c.update(name='surviving-add-generic-child-uses-current-aim',context_expect=dict(kind=None,condition='target_is_add',accepted=True));rows.append(c)
 for source,kind in [('body-completion-versus-lifesteal-order',0),('add-survives-completion-versus-lifesteal-order',5),('part-50-completion-versus-lifesteal-order',1)]:
  c=copy.deepcopy(sources[source]);child=c['effects'][-1];child['name']='context-probe';child['trigger']['condition']=['target_state:marker'];child['duration']=-1
  c.update(name='runtime-query-after-counter-retirement-'+source,context_expect=dict(kind=kind,condition='target_state:marker',accepted=kind!=5));rows.append(c)
 for source,kind,predicate in [('body-completion-versus-lifesteal-order',0,'target_state:marker'),('add-completion-versus-lifesteal-order',5,'self_stack_above:marker:1'),('part-50-completion-versus-lifesteal-order',1,'target_state:marker')]:
  c=copy.deepcopy(sources[source]);child=c['effects'][-1];child['name']='context-probe';child['trigger']['condition']=[predicate];child['duration']=.3
  c.update(name='finite-condition-latches-before-counter-retirement-'+source,context_expect=dict(kind=kind,condition=predicate,accepted=True));rows.append(c)
 return rows
