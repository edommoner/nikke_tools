"""Full native field recipients from completion contexts, including dead Actors."""
import dataclasses,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from effect_runtime import state
from world_frame_native import observe,roster_names
import world_counter_field_cases as cases
s=importlib.util.spec_from_file_location('counter_field_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)

def inspect_case(case):
 from calculator.buff_manager import BuffManager
 original=BuffManager._apply_enemy_carrier;rows=[];names=roster_names(case)
 def apply(manager,effect,targets,caster,t,*args,**kwargs):
  if effect.get('name') not in ('counter-field','nested-field'):return original(manager,effect,targets,caster,t,*args,**kwargs)
  frames=state(manager).event_stack;frame=frames[-1] if frames else None
  rows.append(dict(time=t,name=effect['name'],caster=names.index(caster),targets=list(targets or ()),event=frame.event if frame else None,target=dataclasses.asdict(frame.target) if frame and frame.target else None))
  return original(manager,effect,targets,caster,t,*args,**kwargs)
 with patch.object(BuffManager,'_apply_enemy_carrier',apply):native=observe(case)
 words,_,_=cases.compile_case(physical,case)
 return dict(name=case['name'],input_sha256=hashlib.sha256(struct.pack('<'+'I'*len(words),*words)).hexdigest(),field_activations=rows,native=native)
