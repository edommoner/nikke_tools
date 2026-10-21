"""Literal definitions/metadata for the private physical counter entry; GPU0."""
import copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_specs import ABI,LIMITS as L
from portable_target_counter_specs import pack_battle
from portable_target_counter_program import compiler_effects,patch_program
from portable_world_schedule_specs import compile_schedule
from world_frame_native import authored_metadata,roster_names
s=importlib.util.spec_from_file_location('counter_battle_stack','research/verify-world-actor-stacks.py');stack=importlib.util.module_from_spec(s);s.loader.exec_module(stack)
import world_target_counter_battle_cases as cases
PHYSICAL_ABI=L['COUNTER_LANDING_ABI'];PENDING_ABI=PHYSICAL_ABI
def fixtures():return cases.fixtures(stack)
def compile_case(case, *, allow_no_counter=False):
 c=copy.deepcopy(case);c['effects']=compiler_effects(case['effects']);words,meta,bindings=stack.compile_case(c)
 names=roster_names(case);metadata=authored_metadata(case);chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=metadata[n]) for n in names]
 patch_program(words,meta,chars,[(e,names[o]) for e,o in zip(case['effects'],case['owners'])])
 _,patterns=compile_schedule(dict(patterns=case['patterns'],clock='accumulated',duration=case['duration']),notice_payload=True)
 words[0]=PENDING_ABI;words.extend(pack_battle([(e,o) for e,o in zip(case['effects'],case['owners'])],words[2],names,meta['states'],bindings,patterns,allow_no_counter=allow_no_counter))
 assert len(words)==97464;return words,meta,bindings
if __name__=='__main__':
 for c in fixtures():compile_case(c)
 print('Physical counter definitions/part reach packed',len(fixtures()),'private entry input;GPU0')
