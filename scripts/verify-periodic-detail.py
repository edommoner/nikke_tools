"""Independent full-squad CPU/GPU differential checks for timer and bullet lifetimes."""
import sys,json,hashlib,copy,importlib.util
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,a
spec=importlib.util.spec_from_file_location('periodic_full_oracle',ROOT/'scripts/verify-extended-detail.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
NAMES=['리타','크라운','앨리스','모더니아','N102']
def effect(name,kind,stat,value,target='self',event='battle_start',condition=None,**kw):
 e={'source':'스킬1','name':name,'type':kind,'stat':stat,'fixed_value':value,'target':target,'trigger':{'timing':[event],'condition':condition or []}}
 if kind=='buff':e['duration']=-1
 return {**e,**kw}
def missing_hp():return effect('room for healing','buff','max_hp_only_pct',100,'all_allies')
def scenarios():
 cases=[]
 for immediate in (False,True):
  es=[effect('dot amplification','buff','dot_dmg_pct',33),effect('boundary atk','buff','atk_pct',300,duration=2),effect('periodic dot','damage','dot_damage',100,'target',tick_interval=.5,duration=2,**({'tick_start':'immediate'} if immediate else {}))]
  cases.append((f'dot-expiry-{immediate}',{NAMES[0]:es},4,{'damage_ticks':4}))
 es=[effect('phase preserved','damage','dot_damage',50,'target',event='on_attack_count:3',tick_interval=.5,duration=1),effect('phase restarted','damage','auto_damage',100,'target',event='on_attack_count:3',tick_interval=.5,duration=1)]
 cases.append(('refresh-dot-preserves-auto-restarts',{NAMES[0]:es},4,{'damage_ticks_min':1}))
 es=[effect('reference stack','buff','atk_pct',1,event='every:0.5s',max_stack=6),effect('captured dot','damage','dot_damage',100,'target',event='burst_cast',scaling='stack_count',scaling_ref='reference stack',max_stack=20,tick_interval=.5,duration=3),effect('remove ref','instant','remove_named_buff',0,event='burst_cast',target_effect='reference stack'),effect('removed triggers buff','buff','atk_dmg_pct',50,event='event:state_end:reference stack',duration=3)]
 cases.append(('dot-captures-reference-before-removal',{NAMES[0]:es},8,{'damage_ticks_min':5}))
 es=[effect('own stacks','damage','dot_damage',50,'target',event='on_attack_count:30',scaling='stack_count',max_stack=10,tick_interval=.5,duration=2)]
 cases.append(('dot-own-stack-refresh',{NAMES[0]:es},6,{'damage_ticks_min':5}))
 es=[effect('same dot','damage','dot_damage',100,'target',event='burst_cast',tick_interval=.5,duration=3),effect('same dot','damage','dot_damage',200,'target',tick_interval=.5,duration=5)]
 cases.append(('same-named-dot-keeps-first-live-definition',{NAMES[0]:es},8,{'damage_ticks_min':5}))
 es=[missing_hp(),effect('heal window','buff','crit_dmg',0,duration=1),effect('infinite conditional heal','instant','heal_hp_pct',1,'all_allies',condition=['self_state:heal window'],tick_interval=.5,duration=-1),effect('finite latched heal','instant','heal_hp_pct',2,'all_allies',condition=['self_state:heal window'],tick_interval=.5,duration=3),effect('reopen window','buff','crit_dmg',0,event='burst_cast',duration=1)]
 cases.append(('periodic-heal-finite-latch-infinite-runtime',{NAMES[0]:es},8,{'instant_ticks_min':4}))
 es=[missing_hp(),effect('defined first starts second','instant','heal_hp_pct',1,event='on_attack',tick_interval=.5,duration=2,scaling='max_hp',max_trigger=1),effect('defined second starts first','instant','heal_hp_pct',2,tick_interval=.5,duration=2,scaling='max_hp'),effect('heal changes next base','buff','max_hp_only_pct',20,event='event:heal_received',max_stack=20)]
 cases.append(('timer-creation-order-and-synchronous-heal-events',{NAMES[0]:es},3,{'instant_ticks_min':4}))
 es=[effect('drain','instant','current_hp_reduce',10,'all_allies',tick_interval=.5,duration=3),effect('periodic refill','instant','heal_hp_pct',5,'all_allies',tick_interval=.5,duration=3,scaling='max_hp')]
 cases.append(('periodic-drain-then-heal',{NAMES[0]:es},5,{'instant_ticks_min':4}))
 es=[effect('three shots','buff','atk_pct',100,'all_allies',duration_bullets=3),effect('stacked one shot','buff','atk_dmg_pct',5,'all_allies',event='on_attack_count:3',duration_bullets=1,max_stack=5),effect('bullet end notification','buff','crit_dmg',10,event='event:state_end:three shots',max_stack=10)]
 cases.append(('bullet-counters-and-stacks-per-recipient',{NAMES[0]:es},8,{'bullet_changes_min':5}))
 es=[effect('lazy one shot','buff','crit_dmg',100,'allies_top_atk:1',event='on_attack_count:1',duration_bullets=1)]
 cases.append(('lazy-bullet-target-consumed-by-recipient',{NAMES[0]:es},8,{'bullet_changes_min':1}))
 es=[effect('before shot','buff','charge_dmg_pct',100,event='full_charge',duration_bullets=1),effect('after shot','buff','atk_dmg_pct',50,event='full_charge_fire',duration_bullets=1)]
 cases.append(('charge-before-versus-after-bullet-bound',{NAMES[2]:es},8,{'bullet_changes_min':2}))
 es=[effect('limited timer','damage','damage:2',100,'target',event='on_attack_count:1',tick_interval=.5,duration=2,max_trigger=1)]
 cases.append(('timer-budget-counts-registration-not-ticks',{NAMES[0]:es},5,{'damage_ticks':4}))
 es=[effect('normal skill','damage','damage:2',200,'target',tick_interval=.5,duration=3,damage_formula='normal_attack'),effect('normal skill normal factor','buff','normal_atk_dmg_pct',30),effect('normal skill crit','buff','normal_atk_crit_rate',35),effect('normal skill explosion','buff','projectile_explosion_dmg_pct',50)]
 cases.append(('periodic-normal-attack-formula',{NAMES[4]:es},5,{'damage_ticks_min':4}))
 es=[effect('cancel this dot','damage','dot_damage',100,'target',tick_interval=.5,duration=10),effect('cancel dot','instant','remove_named_buff',0,event='burst_cast',target_effect='cancel this dot'),effect('dot cancelled event','buff','atk_pct',100,event='event:state_end:cancel this dot')]
 cases.append(('named-removal-cancels-dot-timer',{NAMES[0]:es},8,{'damage_ticks_min':3}))
 es=[effect('one round','buff','max_ammo_flat',-1000),effect('last charge speed','buff','charge_speed_pct',100,event='last_bullet_fire',duration_bullets=2),effect('last charge damage','buff','charge_dmg_pct',100,event='last_bullet_fire',duration_bullets=2)]
 cases.append(('charge-last-fire-at-charge-start',{NAMES[2]:es},12,{'last_fire_min':2}))
 es=[effect('lazy shield','buff','shield_from_max_hp_pct',50,'allies_lowest_hp:1',duration=10),effect('eager shield','buff','shield_from_max_hp_pct',50,'all_allies',event='burst_cast',duration=2),effect('shield predicate','buff','atk_pct',200,condition=['during_shield'])]
 cases.append(('lazy-versus-eager-shield-cpu-compatibility',{NAMES[0]:es},8,{'shield_true':True,'shield_false':True}))
 return cases

@contextmanager
def custom_effects(effects):
 from calculator import buff_manager,timeline
 Original=buff_manager.BuffManager;observed={'damage_ticks':0,'instant_ticks':0,'bullet_changes':0,'last_fire':0,'shield_true':False,'shield_false':False,'damage_times':[],'instant_times':[]}
 class Custom(Original):
  def char_effects(self,name):return copy.deepcopy(effects.get(name,[]))
  def get_buffs(self,caster,*args,**kwargs):
   result=super().get_buffs(caster,*args,**kwargs)
   if caster==NAMES[0] and any(e.get('name')=='lazy shield' for e in effects.get(caster,[])):
    active=self.has_shield(caster);observed['shield_true']|=active;observed['shield_false']|=not active
   return result
  def notify(self,event,t,caster,**ctx):
   if event=='last_bullet_fire':observed['last_fire']+=1
   return super().notify(event,t,caster,**ctx)
  def register_damage_handler(self,fn):
   def handler(eff,caster,t):
    if eff.get('tick_interval'):observed['damage_ticks']+=1;observed['damage_times'].append([eff['name'],round(t,6)])
    return fn(eff,caster,t)
   return super().register_damage_handler(handler)
  def _dispatch_instant(self,eff,caster,t,*,from_tick=False):
   if from_tick:observed['instant_ticks']+=1;observed['instant_times'].append([eff['name'],round(t,6)])
   return super()._dispatch_instant(eff,caster,t,from_tick=from_tick)
  def consume_bullet_buffs(self,caster,t=0):
   before={ab.uid:dict(ab.bullets_per_target) for ab in self._active if ab.effect.get('duration_bullets',-1)>=0}
   result=super().consume_bullet_buffs(caster,t)
   after={ab.uid:dict(ab.bullets_per_target) for ab in self._active if ab.effect.get('duration_bullets',-1)>=0}
   observed['bullet_changes']+=sum(values!=after.get(uid) for uid,values in before.items());return result
 buff_manager.BuffManager=timeline.BuffManager=Custom
 try:yield observed
 finally:buff_manager.BuffManager=timeline.BuffManager=Original
