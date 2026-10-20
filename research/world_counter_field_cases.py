"""Authored enemy fields from captured counter completions; no battle replay."""
import copy
from portable_specs import LIMITS as L

def compile_case(physical,case):
 words,meta,bindings=physical.compile_case(case);words[0]=L['COUNTER_FIELD_ABI'];words[L['TARGET_COUNTER_INPUT_BASE']+6]=5;return words,meta,bindings

def fixtures(physical):
 source={c['name']:c for c in physical.fixtures()};rows=[]
 def field(stat,value,target='target',name='counter-field',timing='event:target_counter_complete:marker',duration=.3,condition=()):
  return dict(type='buff',name=name,source='스킬1',stat=stat,fixed_value=value,target=target,duration=duration,trigger=dict(timing=[timing],condition=list(condition)))
 def make(base,stat,value,target):
  c=copy.deepcopy(source[base]);c.update(name=base+'-'+stat+'-'+target,duration=.15,observe_enemy_fields=True,observe_named_state=True)
  c['allow_shared_enemy_fields']=any(p['kind']=='summon' for p in c['patterns'])
  c['effects'][-1]=field(stat,value,target)
  for a in c['environment']['allies']:a['base_defense']=30
  rows.append(c);return c
 for base in ('body-completion-versus-lifesteal-order','add-completion-versus-lifesteal-order','add-survives-completion-versus-lifesteal-order','part-50-completion-versus-lifesteal-order'):
  for stat,value in [('def_pct',-30),('def_caster_based_pct',-40),('received_dmg_pct',25)]:
   for target in ('target','boss','all_enemies'):make(base,stat,value,target)
 for target in ('enemies_top_hp:2','enemies_highest_hp:2','enemies_lowest_hp:2','enemies_nearest:2','enemies_top_def:2','enemies_lowest_def:2','enemies_top_atk:2'):
  c=make('add-survives-completion-versus-lifesteal-order','received_dmg_pct',25,target);c['patterns'][0]['spec'].update(count=3,hp=1200,atk=114345)
 c=make('add-completion-versus-lifesteal-order','received_dmg_pct',25,'target');c['name']='fatal-first-add-current-field-keeps-dead-actor';c['patterns'][0]['spec']['count']=2
 c=copy.deepcopy(c);c['name']='nested-generic-field-child-uses-new-current-add';c['effects'].append(field('def_pct',-20,'target','nested-field','event:counter-field'));c['owners'].append(0);rows.append(c)
 c=make('add-survives-completion-versus-lifesteal-order','received_dmg_pct',25,'all_enemies');c['name']='counter-field-fanout128-holds-completion-marker';c['patterns'][0]['spec'].update(count=127,hp=1000000)
 child=field('atk_pct',0,'self','fanout-witness','event:counter-field',condition=['self_stack_above:marker:1']);child['max_stack']=128;c['effects'].append(child);c['owners'].append(0)
 c=make('part-50-completion-versus-lifesteal-order','received_dmg_pct',25,'target');c['name']='part-counter-field-logical-root-with-captured-part-damage'
 for duration in (-1,.3):
  c=make('add-survives-completion-versus-lifesteal-order','received_dmg_pct',25,'target');c['name']='field-condition-marker-lifecycle-'+str(duration);c['effects'][-1].update(duration=duration);c['effects'][-1]['trigger']['condition']=['self_stack_above:marker:1']
 c=make('body-completion-versus-lifesteal-order','received_dmg_pct',25,'boss');c['name']='counter-field-expires-with-named-end-child';c['effects'][-1]['duration']=.05;c['effects'].append(field('atk_pct',0,'self','expiry-witness','event:state_end:counter-field'));c['owners'].append(0)
 c=make('add-survives-completion-versus-lifesteal-order','received_dmg_pct',25,'target');c['name']='counter-refresh-child-retains-new-epoch-and-field';c['effects'][-1]['max_stack']=3
 refresh=copy.deepcopy(c['effects'][2]);refresh['trigger']['timing']=['event:target_counter_complete:marker'];refresh['max_trigger']=1;c['effects'].append(refresh);c['owners'].append(0)
 c=make('nonowner-fatal-add-death-still-completes','received_dmg_pct',25,'target');c['name']='nonowner-death-counter-field-caster-and-target-are-independent'
 return rows
