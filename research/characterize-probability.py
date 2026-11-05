"""Native probability semantics only; no GPU admission or efficiency claim."""
import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES
from calculator import buff_manager

def effect(conditions):return dict(name='chance',type='buff',source='스킬1',stat='atk_pct',fixed_value=1,target='self',duration=-1,max_stack=1000,trigger=dict(timing=['on_attack'],condition=conditions))
def expected(conditions,n=40):
 bm=manager([effect(conditions)]);bm.state['rng_expected']=True;e=bm._effects[0][0];rows=[]
 for i in range(n):
  passed=bm._condition_ok(conditions,NAMES[0],i/60,e)
  value=bm.state.get('rng_acc',{}).get(('prob',id(e),NAMES[0]),0)
  rows.append(dict(event=i+1,passed=passed,accumulator=value))
 before=dict(bm.state.get('rng_acc',{}));runtime=bm._runtime_condition_ok(conditions,NAMES[0],NAMES[0],'__enemy__',1)
 assert before==bm.state.get('rng_acc',{}),'Runtime query must not roll or accumulate probability'
 return dict(conditions=conditions,events=rows,runtime_condition_result=runtime)
