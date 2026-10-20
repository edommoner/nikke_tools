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
def main():
 rates=['0','5','10','20','30','33.3333','50','100'];rows=[expected(['prob:'+r]) for r in rates]
 assert [x['event'] for x in rows[rates.index('10')]['events'] if x['passed']]==[11,21,31]
 assert [x['event'] for x in rows[rates.index('20')]['events'] if x['passed']]==list(range(5,41,5))
 assert not any(x['passed'] for x in rows[0]['events']);assert all(x['passed'] for x in rows[-1]['events'])
 ordered=[expected(c) for c in [['self_state:absent','prob:20'],['prob:20','self_state:absent'],['prob:50','prob:50'],['prob:10','prob:100']]]
 assert all(x['accumulator']==0 for x in ordered[0]['events']);assert any(x['accumulator']!=0 for x in ordered[1]['events']);assert not any(x['passed'] for x in ordered[2]['events'])
 # Each declared instance/caster has its own accumulator, even if display names
 # coincide. No Python object address is serialized into this characterization.
 bm=manager([effect(['prob:50']),effect(['prob:50'])],[0,0]);bm.state['rng_expected']=True;identities=[]
 for ei,(e,_) in enumerate(bm._effects):
  for owner in (0,4):
   passed=[bm._condition_ok(['prob:50'],NAMES[owner],i/60,e) for i in range(2)];assert passed==[False,True];identities.append(dict(effect_index=ei,owner=owner,passed=passed))
 actual=[]
 for p in (0,20,100):
  conditions=['prob:'+str(p)];bm=manager([effect(conditions)]);e=bm._effects[0][0];rolls=[0,.199999999,.2,.999999999];used=[]
  def random_value():v=rolls[len(used)];used.append(v);return v
  with patch.object(buff_manager.random,'random',side_effect=random_value):observed=[bm._condition_ok(conditions,NAMES[0],i,e) for i in range(4)]
  assert len(used)==4;assert observed==[r<p/100 for r in rolls];actual.append(dict(percent=p,rolls=used,passed=observed,draws=len(used)))
 files=['app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','tests/test_target_counter_runtime.py','research/characterize-probability.py']
 result=dict(passed=True,cpu_only=True,gpu_execution_performed=False,gpu_admission_enabled=False,expected_mode=rows,ordered_conditions=ordered,instance_caster_independence=identities,actual_random_boundaries=actual,rules=['Expected mode uses binary64 accumulator per(effect instance,caster), not integer percent arithmetic','All probability conditions in one effect share that accumulator and retain list short-circuit order','10percent first triggers on event11 due to native floating-point accumulation','Runtime queries do not re-roll or advance probability','Actual mode draws even at0 or100percent; equality of roll and probability fails'],source_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in files})
 (R/'research/portable-probability-native-characterization.json').write_text(json.dumps(result,indent=2)+'\n');print('Native probability expected/shared-order/instance/runtime/random boundary rules verified')
if __name__=='__main__':main()
