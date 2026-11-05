"""CPU target-resolution timing, budgets and periodic dispatch references."""
import copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('target_lifecycle',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.E;OWNER=v.NAMES[0]
def scenarios():
 def buff(**kw):return E('random buff','buff','atk_pct',20,'allies_random:1',event='every:1s',duration=.5,**kw)
 yield 'buff-no-budget',[buff()]
 yield 'buff-budget-two',[buff(max_trigger=2)]
 yield 'exhausted-budget-no-draw',[buff(max_trigger=0)]
 yield 'list-children-no-string-probe',[{**buff(max_trigger=2),'target':['allies_random:1','allies_random:1']}]
 harm=E('harm','buff','atk_pct',-30,'all_allies',polarity='harmful')
 yield 'cleanse-budget-two',[harm,E('random cleanse','instant','debuff_cleanse',1,'allies_random_with_debuff:2',event='every:1s',max_trigger=2)]
 yield 'empty-probe-keeps-budget',[{**harm,'trigger':{'timing':['every:2s'],'condition':[]}},E('random cleanse','instant','debuff_cleanse',1,'allies_random_with_debuff:2',event='every:1s',max_trigger=1)]
 yield 'periodic-instant-no-budget',[E('periodic heal','instant','heal_hp_pct',1,'allies_random:1',tick_interval=.5,duration=3)]
 yield 'periodic-instant-lazy-budget-no-registration-probe',[E('periodic heal','instant','heal_hp_pct',1,'allies_random:1',tick_interval=.5,duration=3,max_trigger=1)]
 yield 'periodic-cleanse-eager-budget-registration-probe',[harm,E('periodic cleanse','instant','debuff_cleanse',1,'allies_random_with_debuff:2',tick_interval=.5,duration=3,max_trigger=1)]
 yield 'periodic-damage-lazy-carrier',[E('periodic damage','damage','dot_damage',100,'allies_random:1',tick_interval=.5,duration=3)]
 yield 'failed-condition-no-draw',[{**buff(),'trigger':{'timing':['every:1s'],'condition':['self_state:unregistered']}}]
 yield 'same-owner-time-lazy-targets-share-one-draw',[E('first lazy','buff','atk_pct',20,'allies_random:1'),E('second lazy','buff','crit_dmg',30,'allies_random:1')]
 yield 'removed-carrier-cache-survives-later-group',[
  E('old lazy A','buff','atk_pct',20,'allies_random:1',event='passive',condition=['self_state:gate A']),
  E('old lazy B','buff','crit_dmg',30,'allies_random:1',event='passive',condition=['self_state:gate B']),
  E('gate A','buff','',0,event='every:1s',max_trigger=1),
  E('remove first','instant','remove_named_buff',0,event='every:2s',target_effect='old lazy A',max_trigger=1),
  E('later lazy C','buff','atk_pct',50,'allies_random:1',event='every:2s',max_trigger=1),
  E('gate B','buff','',0,event='every:3s',max_trigger=1)]
