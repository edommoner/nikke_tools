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
def main():
 rows=[inspect_case(c) for c in cases.fixtures(physical)];assert len(rows)==52,len(rows)
 by={c['name']:c for c in rows}
 fatal=by['fatal-first-add-current-field-keeps-dead-actor'];assert fatal['field_activations'][0]['target']['kind']==5 and fatal['native']['enemy_fields']['carriers'][0]['actor']==[5,0,1]
 nested=by['nested-generic-field-child-uses-new-current-add']['field_activations'];assert nested[0]['target']['kind']==5 and nested[1]['target'] is None and nested[0]['targets']!=nested[1]['targets']
 fan=by['counter-field-fanout128-holds-completion-marker'];assert len(fan['field_activations'])==128 and next(c for c in fan['native']['named_state']['allied_carriers'] if c['name']=='fanout-witness')['stack']==128
 report=dict(passed=True,cases=rows,case_count=len(rows),gpu_calls=0,cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-counter-field-native-contract.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Full native counter field contracts:',len(rows),'GPU0')
if __name__=='__main__':main()
