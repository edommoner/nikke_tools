"""Inspect installed native predicates with full battles; never execute a GPU."""
import dataclasses,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from effect_runtime import state
from world_frame_native import observe,roster_names
import world_counter_context_cases as cases
s=importlib.util.spec_from_file_location('counter_context_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)

def inspect_case(case):
 from calculator.buff_manager import BuffManager
 original=BuffManager._condition_ok;rows=[];names=roster_names(case)
 def condition(manager,conditions,caster,t,eff=None):
  result=original(manager,conditions,caster,t,eff)
  if eff is not None and eff.get('name')=='context-probe':
   frames=state(manager).event_stack;frame=frames[-1] if frames else None
   rows.append(dict(time=t,conditions=list(conditions),accepted=result,caster=names.index(caster),event=frame.event if frame else None,target=dataclasses.asdict(frame.target) if frame and frame.target else None,impact=dataclasses.asdict(frame.impact) if frame and frame.impact else None,completion_actor=dataclasses.asdict(frame.completion.actor) if frame and frame.completion else None))
  return result
 with patch.object(BuffManager,'_condition_ok',condition):native=observe(case)
 words,meta,bindings=cases.compile_case(physical,case)
 payload=struct.pack('<'+'I'*len(words),*words)
 expected=case['context_expect'];assert rows,case['name']
 activation=rows[0];kind=expected['kind'];kind={'body':0,'part':1,'add':5}.get(kind,kind)
 assert (activation['target']['kind'] if activation['target'] else None)==kind and activation['accepted']==expected['accepted'],(case['name'],activation,expected)
 if expected.get('impact') is False:assert activation['impact'] is None
 assert all(row['conditions']==[expected['condition']] for row in rows)
 return dict(name=case['name'],input_sha256=hashlib.sha256(payload).hexdigest(),expected=expected,condition_observations=rows,native=native)

def main():
 rows=[inspect_case(c) for c in cases.fixtures(physical)]
 report=dict(passed=True,cases=rows,case_count=len(rows),gpu_calls=0,cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-counter-context-native-contract.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('Full native counter context contracts:',len(rows),'GPU0')
if __name__=='__main__':main()
