from detail_gpu import EVENT
"""Per-timing descriptors and high event IDs against independent CPU execution."""
import copy,hashlib,importlib.util,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for

def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
oracle=load('descriptor_oracle','verify-detail.py');periodic=load('descriptor_full','verify-periodic-detail.py');E=periodic.effect
NAMES=periodic.NAMES

def primitives():
 cases=[]
 def build(name,es,events,checks):
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[0]) for e in es]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
  commands=[(t,0,code,arg) for t,code,arg in events]+[(t,2,0,i) for i,(t,value) in enumerate(checks)]
  for t,op,code,arg in sorted(commands,key=lambda x:(x[0],x[1])):script.append([t,op,code,0,arg if op==0 else -1,arg if op==2 else -1,0,0])
  cases.append((name,p,script,[v for t,v in checks]))
 def mixed(timings,**kw):
  e=E('mixed','buff','atk_pct',10,max_stack=100,**kw);e['trigger']['timing']=timings;return e
 build('same-event-cpu-indexed-activation-multiplicity',[mixed(['on_attack_count:2','on_attack_count:3'])],[(i/10,7,0) for i in range(1,7)],[(i/10,v) for i,v in enumerate([0,20,40,60,60,80],1)])
 build('high-received-hit-counter-and-alias',[mixed(['received_hit_count:2','received_hit:3'])],[(i/10,32,0) for i in range(1,7)],[(.6,80)])
 high=['received_hit','enemy_death','event:part_destroy','event:projectile_destroy','event:cover_hit','event:lethal_hit','event:self_down']
 build('high-event-notifications-without-incoming-damage',[mixed(high)],[(i/10,EVENT[e],0) for i,e in enumerate(high,1)],[(.7,70)])
 build('stage-specific-cumulative-counters',[mixed(['burst_enter_count:1:2','burst_enter_count:3:3'])],[(.1,4,1),(.2,4,3),(.3,4,1),(.4,4,3),(.5,4,1),(.6,4,3)],[(.2,0),(.4,10),(.6,30)])
 build('core-pellet-and-full-charge-aliases',[mixed(['core_hit:2','pellet_hit:3','full_charge_count:2'])],[(.1,23,0),(.2,23,0),(.3,20,0),(.4,20,0),(.5,20,0),(.6,11,0),(.7,11,0)],[(.7,30)])
 es=[E('a','buff','crit_dmg',0),E('b','buff','crit_dmg',0,event='on_attack',max_stack=2),mixed(['stack_reach:a:1','stack_reach:b:2'])]
 build('two-named-stack-reach-tags',es,[(.1,7,0),(.2,7,0)],[(.2,20)])
 es=[E('a','buff','crit_dmg',0,duration=.5),E('b','buff','crit_dmg',0,duration=1),mixed(['event:state_end:a','event:state_end:b'])]
 build('two-named-end-tags',es,[],[(.6,10),(1.1,20)])
 es=[mixed(['every_stack:fuel:2','every_stack:fuel:3']),E('charge','instant','gauge_charge',6,gauge_id='fuel',gauge_max=10)]
 build('multiple-gauge-boundaries-deduplicated',es,[],[(.1,80)])
 es=[mixed(['battle_start','passive'],condition=['during_full_burst']),E('passive first','buff','atk_pct',20,condition=['during_full_burst'])]
 es[1]['trigger']['timing']=['passive','battle_start']
 build('first-matching-passive-semantics',es,[(.5,1,0)],[(.1,0),(.6,20)])
 es=[E('gate','buff','crit_dmg',0),mixed(['on_attack_count:2','on_attack_count:3'],condition=['self_state:gate']),E('remove gate','instant','remove_named_buff',0,event='stack_reach:mixed:1',target_effect='gate'),E('gate removed witness','buff','atk_pct',1,event='event:state_end:gate'),E('must not reach two','buff','atk_pct',50,event='stack_reach:mixed:2')]
 build('repeat-reevaluates-condition-after-synchronous-chain',es,[(i/10,7,0) for i in range(1,7)],[(.6,1)])
 build('exact-and-cumulative-share-latched-notification-count',[mixed(['full_burst_start_exact:2','full_burst_start_count:2'])],[(.1,1,0),(.2,1,0),(.3,1,0)],[(.1,0),(.2,20),(.3,40)])
 build('shared-budget-with-overlapping-thresholds',[mixed(['on_attack_count:2','on_attack_count:3'],max_trigger=2)],[(i/10,7,0) for i in range(1,7)],[(.6,20)])
 return cases

def synthetic_squads():
 n=NAMES
 e=E('mixed attacks','buff','atk_pct',5,max_stack=20);e['trigger']['timing']=['on_attack_count:2','on_attack_count:3']
 yield 'full-auto-overlapping-attack-thresholds',{n[0]:[e]},12
 e=E('stage observer','buff','charge_dmg_pct',15,max_stack=10);e['trigger']['timing']=['burst_enter_count:1:2','burst_enter_count:3:2']
 yield 'full-stage-counters',{n[2]:[e]},45
 e=E('both reloads','buff','atk_dmg_pct',10,max_stack=20);e['trigger']['timing']=['event:load A','event:load B']
 yield 'full-two-ammo-named-events',{n[0]:[E('load A','instant','ammo_charge_pct',10,event='every:1s'),E('load B','instant','ammo_charge_pct',20,event='every:1s'),e]},8
 e=E('boundaries','buff','atk_pct',10,max_stack=20);e['trigger']['timing']=['every_stack:fuel:2','every_stack:fuel:3']
 yield 'full-overlapping-gauge-boundaries',{n[0]:[E('fuel','instant','gauge_charge',6,event='every:1s',gauge_id='fuel',gauge_max=60),e]},8
 e=E('shotgun mixed','buff','atk_pct',10,condition=['self_state:gate'],max_stack=20);e['trigger']['timing']=['pellet_hit_in_shot:5','pellet_hit_in_shot:3']
 yield 'full-shotgun-threshold-order',{'메어리':[E('gate','buff','crit_dmg',0),e,E('close gate','instant','remove_named_buff',0,event='stack_reach:shotgun mixed:1',target_effect='gate'),E('gate end witness','buff','atk_dmg_pct',20,event='event:state_end:gate')]},8
