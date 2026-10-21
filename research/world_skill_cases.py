"""Literal skill fixtures shared unchanged by native, CUDA and Metal."""
import copy,importlib.util
from pathlib import Path
from portable_specs import LIMITS as L
from portable_enemy_specs import damage_plan
from target_counter_cases import marker
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
queue=module('world_skill_queue_cases','research/characterize-world-counter-damage-queue.py')
def compile_case(physical,case):
 words,meta,bindings=physical.compile_case(case,allow_no_counter=True);words[0]=L['WORLD_SKILL_ABI'];words[L['TARGET_COUNTER_INPUT_BASE']+6]=7
 for i,e in enumerate(case['effects']):
  if e.get('type')=='damage' and damage_plan(e)[0]==2:words[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return words,meta,bindings
def fixtures(physical):
 rows=copy.deepcopy(queue.fixtures());base=copy.deepcopy(rows[0]);base['duration']=.05
 for family in ('damage','bonus_damage','burst_damage','split_damage','auto_damage','armor_break_damage','armor_break_burst_damage','sequential_damage','projectile_attachment_damage','projectile_explosion_damage','pierce_damage','core_damage'):
  c=copy.deepcopy(base);c['name']='direct-family-'+family;c['effects'][-1]['stat']=family;c['effects'][-1]['target']='boss';rows.append(c)
 c=copy.deepcopy(rows[-1]);c['name']='core-damage-normal-formula-is-skill';c['effects'][-1]['damage_formula']='normal_attack';c['effects'].append(dict(name='normal-formula-modifier',source='스킬1',type='buff',stat='normal_atk_dmg_pct',fixed_value=50,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0);rows.append(c)
 add=copy.deepcopy(queue.fixtures()[5]);add['duration']=.05
 for target in ('enemies_top_hp:2','enemies_highest_hp:2','enemies_lowest_hp:2','enemies_nearest:2','enemies_top_def:2','enemies_lowest_def:2','enemies_top_atk:2'):
  c=copy.deepcopy(add);c['name']='late-skill-rank-'+target;c['patterns'][0]['spec'].update(count=3,hp=1300,atk=114345);c['effects'][-1].update(target=target,fixed_value=100);rows.append(c)
 c=copy.deepcopy(add);c['name']='all128-late-skill-recipients';c['patterns'][0]['spec'].update(count=127,hp=1000000);c['effects'][-1]['target']='all_enemies';rows.append(c)
 c=copy.deepcopy(c);c['name']='split128-zero-damage-still-earns-skill-credit';c['effects'][-1].update(stat='split_damage',fixed_value=1);rows.append(c)
 c=copy.deepcopy(base);c['name']='multihit3-captures-amount-before-named-buff';c['effects'][-1]['stat']='bonus_damage:3';c['effects'].append(dict(name='named-attack-buff',source='스킬1',type='buff',stat='atk_pct',fixed_value=50,target='self',duration=.3,trigger=dict(timing=['hit_count:queued-child:1'],condition=[])));c['owners'].append(0);rows.append(c)
 c=copy.deepcopy(base);c['name']='late-routing-includes-add-born-after-skill-creation';c['patterns'].append(dict(id='wave',kind='summon',delay=.01,spec=dict(count=1,hp=100000)));c['effects'][-1]['target']='all_enemies';rows.append(c)
 c=copy.deepcopy(base);c['name']='nested-skill-counter-child-drains-live-queue';c['effects'].append(dict(name='nested-skill',source='스킬1',type='damage',stat='bonus_damage',fixed_value=10,target='boss',max_trigger=1,trigger=dict(timing=['event:target_counter_complete:skill-proof'],condition=[])));c['owners'].append(0);rows.append(c)
 for target in ('boss','all_enemies'):
  c=copy.deepcopy(add if target=='all_enemies' else base);c['name']='counter-free-world-skill-'+target
  kept=[(e,o) for e,o in zip(c['effects'],c['owners']) if e.get('stat')!='target_hit_counter'];c['effects']=[e for e,_ in kept];c['owners']=[o for _,o in kept]
  c['effects'][-1].update(target=target);c['effects'][-1]['trigger']['timing']=['battle_start'];c['counter_free']=True;rows.append(c)
 c=copy.deepcopy(next(c for c in physical.fixtures() if c['name']=='part-50-completion-versus-lifesteal-order'));c['name']='part-counter-enqueues-body-skill-without-extra-part-reach';c['effects'][-1]=copy.deepcopy(base['effects'][-1]);rows.append(c)
 c=copy.deepcopy(base);c['name']='zero-coefficient-does-not-enqueue-or-earn-credit';c['effects'][-1]['fixed_value']=0;rows.append(c)
 for c in rows:
  if c.get('counter_free'):continue
  skill=next(e for e in c['effects'] if e.get('type')=='damage')
  has_adds=any(p['kind']=='summon' for p in c['patterns'])
  actor=dict(kind='add' if has_adds and skill['target']=='target' and 'add-completion' not in c['name'] and 'lethal' not in c['name'] and 'queries-body' not in c['name'] and 'neutral-enemy-field' not in c['name'] else 'body',identity=0,generation=1)
  proof=marker(name='skill-proof',threshold=1,actor=actor,families=['skill']);proof['target']='boss';proof['trigger']['timing']=['battle_start'];c['effects'].append(proof);c['owners'].append(0)
 return rows
