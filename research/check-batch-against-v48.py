"""Host-only migration check against the frozen single-squad decoder/launcher."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker,detail_gpu
from gpu_selector import Cuda
previous=ROOT/'research/ports/v48-copy-carriers-verified/app/detail_gpu.py'
spec=importlib.util.spec_from_file_location('v48_single',previous)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
fixtures=json.loads((ROOT/'research/base-copy-api-fixtures.json').read_text(encoding='utf-8'))
bodies=[copy.deepcopy(row['evaluation']) for row in fixtures]
different=copy.deepcopy(bodies[0]);different['duration']=17;different['seed']=67890
bodies.insert(1,different)
files=['app/detail_gpu.py','app/evaluation-queue.mjs','app/gpu_service.py','app/detail_effects.cu','app/detail_effects-sm86.cubin',str(previous.relative_to(ROOT))]
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
before=hashes();compiled=[engine_worker.evaluate({**b,'_compile_gpu_detail':True}) for b in bodies]
device=Cuda()
try:
 actual=detail_gpu.evaluate_full_many(device,compiled,module_backend='native')
 rows=[]
 for index,(program,result) in enumerate(zip(compiled,actual)):
  expected=old.evaluate_full(device,program,module_backend='native')
  assert {k:v for k,v in result.items() if k!='compute'}=={k:v for k,v in expected.items() if k!='compute'},index
  checks={key:result['compute'][key]==expected['compute'][key] for key in ('final_hp','final_control','workspace_bytes','backend')}
  assert all(checks.values()),(index,checks)
  rows.append(dict(index=index,total=result['total_damage'],checks=checks,batch_size=result['compute'].get('batch_size',1)))
finally:device.close()
assert hashes()==before
report=dict(passed=True,cases=rows,source_sha256=before,scope='Mixed squads, seed and duration; all semantic output plus final HP/control against frozen v48 single evaluator')
(ROOT/'research/performance-archived-parity.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report),flush=True)
