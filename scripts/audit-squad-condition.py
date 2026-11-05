"""Independent CPU references for the next squad-composition predicate port."""
import copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('squad_cpu',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.buff_manager import BuffManager,_NIKKE

def scenarios():
 for timing,duration in [('battle_start',-1),('passive',-1),('burst_cast',5),('every:1s',.5),('on_attack_count:3',.4),('passive',1)]:
  yield timing+'-'+str(duration),[v.E('squad probe','buff','atk_pct',30,'all_allies',event=timing,duration=duration,condition=['squad_ally_exists'])]
 yield 'lazy-random-permanent-passive',[v.E('squad probe','buff','atk_pct',30,'allies_random:1',event='passive',condition=['squad_ally_exists'])]
 yield 'mixed-runtime-gate',[v.E('squad probe','buff','atk_pct',30,'all_allies',event='passive',condition=['squad_ally_exists','self_state:gate']),v.E('gate','buff','',0,event='every:1s',max_trigger=1)]
