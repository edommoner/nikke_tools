"""Nested cleanse during creation/refresh, without changing real source skills."""
import hashlib,importlib.util,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('nested_cleanse',ROOT/'scripts/verify-cleanse-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.v.E;NAMES=v.v.NAMES
def scenarios():
 owner=NAMES[0]
 for label,target,timing in [('shield-stack-partial','self','stack_reach:nested harm:1'),('shield-event-complete','all_allies','event:nested harm')]:
  yield label,{owner:[E('shield gate','buff','atk_pct',100,'all_allies',event='passive',condition=['during_shield']),E('nested harm','buff','shield_from_max_hp_pct',50,'all_allies',polarity='harmful'),E('nested cleanse','instant','debuff_cleanse',1,target,event=timing)]}
 effects={n:[E('named recipient probe','buff','atk_pct',7,event='event:stacking harm',max_stack=100)] for n in NAMES}
 effects[owner]+=[E('stacking harm','buff','atk_pct',-10,'all_allies',polarity='harmful',event='every:1s',max_stack=3,event_scope='recipients'),E('nested cleanse','instant','debuff_cleanse',1,'self',event='stack_reach:stacking harm:2')]
 yield 'refresh-updates-named-recipient-audience',effects
 yield 'max-hp-creation-partial',{owner:[E('hp harm','buff','max_hp_only_pct',100,'all_allies',polarity='harmful'),E('nested cleanse','instant','debuff_cleanse',1,'self',event='stack_reach:hp harm:1'),E('below hp probe','buff','atk_pct',50,'all_allies',event='passive',condition=['self_hp_below:80'])]}
