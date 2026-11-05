"""Whole battles and final MT state, without CPU draws/choices as GPU inputs."""
import copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('random_lifecycle',ROOT/'scripts/audit-random-target-lifecycle.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.E;OWNER=v.OWNER

def extra_cases():
 for count in range(6):
  yield 'random-count-'+str(count),[E('random stat','buff','atk_pct',20,'allies_random:'+str(count),event='every:1s',duration=.7)]
 yield 'ordered-list-duplicates',[E('ordered refill','instant','ammo_charge_flat',1,['allies_random:2','self','allies_random:2'],event='every:1s')]
 yield 'one-bullet-lazy',[E('random bullet','buff','atk_pct',100,'allies_random:2',event='on_attack_count:3',duration_bullets=1)]
 yield 'refresh-lazy-target',[E('random refresh','buff','atk_pct',5,'allies_random:2',event='every:1s',duration=3,max_stack=4)]
 yield 'singleton-harmful-pool-consumes-rng',[E('harm','buff','atk_pct',-20,'self',polarity='harmful'),E('clean','instant','debuff_cleanse',0,'allies_random_with_debuff:1',event='every:1s')]
 yield 'irremovable-sampled-but-retained',[E('permanent harm','buff','atk_pct',-20,'all_allies',polarity='harmful_irremovable'),E('clean','instant','debuff_cleanse',0,'allies_random_with_debuff:3',event='every:1s')]
 yield 'shared-lazy-harmful-stats',[E('harm','buff','atk_pct',-20,'allies_random:2',polarity='harmful'),E('same group','buff','crit_dmg',40,'allies_random:2'),E('clean','instant','debuff_cleanse',0,'allies_random_with_debuff:2',event='every:1s')]
 yield 'unread-inert-random-at-fullburst-snapshot',[E('unread','buff','',0,'allies_random:1',duration=7)]
 yield 'unread-dot-at-fullburst-snapshot',[E('unread dot','damage','dot_damage',100,'allies_random:1',tick_interval=.5,duration=7)]
 yield 'caster-atk-special-lazy-target',[E('special random','buff','atk_caster_based_pct',20,'allies_random:2')]
 yield 'hp-conversion-special-lazy-target',[E('special random hp','buff','atk_from_hp_pct',5,'allies_random:2')]


def real_cases():
 names=['코코아']+[n for n in v.v.NAMES if n!='코코아'][:4]
 for seed in (0,12345,4294967295):
  for mode in ('fixed','accumulate'):
   body=v.v.c.body_for(names,35,True);body.update(seed=seed,_debug_random_state=True,burst_gauge_mode=mode,shooting_policy='character')
   yield 'real-cocoa-positive-cleanse',body,{names[1]:[E('renewed verification harm','buff','atk_pct',-20,'all_allies',event='every:2s',polarity='harmful')]}
