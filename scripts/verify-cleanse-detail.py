"""Independent complete battles from authored cleanse inputs only."""
import copy,hashlib,importlib.util,json,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('cleanse_cases',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

@contextmanager
def injected_effects(effects):
 from calculator import buff_manager,timeline
 original=buff_manager.BuffManager
 class Injected(original):
  def char_effects(self,name):return copy.deepcopy(super().char_effects(name))+copy.deepcopy(effects.get(name,[]))
 buff_manager.BuffManager=timeline.BuffManager=Injected
 try:yield
 finally:buff_manager.BuffManager=timeline.BuffManager=original

def real_cases():
 before=json.loads((ROOT/'research/detail-coverage-burst-stage.json').read_text(encoding='utf-8'))
 after=json.loads((ROOT/'research/detail-coverage-cleanse.json').read_text(encoding='utf-8'))
 was={r['character'] for r in before['results'] if r['supported']}
 for entry in after['results']:
  if not entry['supported'] or entry['character'] in was:continue
  who=entry['character'];names=[who]+[n for n in v.NAMES if n!=who][:4]
  operations=[('character',None)]
  if who=='크러스트':operations=[('authored-tap',{who:{'tap_fire':{'rate':3.6,'release':.03}}}),('authored-hold',{who:{'sequence':[{'t':0,'action':'hold','until':3},{'t':4,'action':'hold','until':7},{'t':8,'action':'hold','until':11}]}})]
  for operation,controls in operations:
   for mode in ('fixed','accumulate'):
    body=v.c.body_for(names,35,True);body['burst_gauge_mode']=mode;body['shooting_policy']='character'
    yield who+'-'+operation+'-'+mode,body,{names[1]:[v.E('verification harm','buff','atk_pct',-20,'all_allies',polarity='harmful')]},controls
