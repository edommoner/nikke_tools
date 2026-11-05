from detail_gpu import compile_effects
"""Independent reach-part lifecycle and complete-squad CPU/GPU parity."""
import argparse,copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('parts_periodic','scripts/verify-periodic-detail.py');raw=module('parts_raw','scripts/verify-cleanse-detail.py');oracle=module('parts_oracle','scripts/verify-detail.py')
from detail_world import packed_enemy
E=p.effect
NAMES=['리타','크라운','앨리스','모더니아','맥스웰']



def parts():return [dict(name='tier'+str(i),hp=5 if i==1 else 0,reach=i) for i in range(1,6)]

def scenarios():
 owner=NAMES[2]
 pierce=E('pierce','buff','pierce_enabled',1)
 witness=E('destroy response','buff','atk_pct',17,'all_allies',event='event:part_destroy',max_stack=32)
 yield 'timed-pierce-range',NAMES,owner,[pierce,E('wide pierce','buff','pierce_range',100,event='every:2s',duration=1.5),witness],2,False
 yield 'stacked-pierce-range',NAMES,owner,[pierce,E('wide stacks','buff','pierce_range',20,event='full_charge_fire',duration=10,max_stack=5),witness],2,False
 rl=NAMES[:4]+['N102'];rocket='N102'
 yield 'timed-explosion-range',rl,rocket,[E('wide explosion','buff','explosion_range',100,event='every:2s',duration=1.5),witness],4,False
 yield 'negative-explosion-range',rl,rocket,[E('narrow explosion','buff','explosion_range',-100),witness],3,False
 yield 'pierce-skill-multiple-hits',NAMES,owner,[E('pierce skill','damage','pierce_damage:2',250,'target',event='every:0.5s'),E('skill range','buff','pierce_range',100),witness],2,False
 yield 'explosion-skill-multiple-hits',NAMES,owner,[E('explosion skill','damage','projectile_explosion_damage:3',250,'target',event='every:0.5s'),E('skill range','buff','explosion_range',100),witness],4,False
 yield 'parts-skill-and-base-presence',NAMES,owner,[E('parts skill','damage','damage:2',250,'all_enemies',event='every:1s',hits_parts=True),E('part power','buff','part_dmg_pct',35),witness],5,True
 yield 'deferred-b3-bonus-parts',NAMES,owner,[E('burst bonus parts','damage','bonus_damage:2',1000,'all_enemies',event='burst_cast',hits_parts=True),witness],5,False
 yield 'dot-part-snapshots',NAMES,owner,[E('parts dot','damage','dot_damage',100,'target',event='every:3s',tick_interval=.5,duration=2,hits_parts=True),witness],5,False
 yield 'normal-formula-rocket-skill',rl,rocket,[E('normal skill','damage','damage:2',250,'target',event='every:0.5s',damage_formula='normal_attack'),E('wide explosion','buff','explosion_range',100),witness],4,False
 yield 'part-lifesteal-ordered-recipients',NAMES,owner,[pierce,E('wide pierce','buff','pierce_range',100),E('health room','buff','max_hp_only_pct',100,'all_allies'),E('lifesteal','buff','lifesteal_pct',5,'all_allies'),E('heal trigger','buff','atk_pct',5,event='event:heal_received',max_stack=10),witness],2,False
