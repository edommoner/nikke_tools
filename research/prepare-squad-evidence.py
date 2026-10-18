import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker as a
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={'코코아':'누아르','리타':'루주'}
def rename(v):
 if isinstance(v,dict):return {mapping.get(k,k):rename(x) for k,x in v.items()}
 if isinstance(v,list):return [rename(x) for x in v]
 return mapping.get(v,v) if isinstance(v,str) else v
body=rename(read('research/detail-random-api-fixture.json'));body['shooting_policy']='character'
compiled=a.evaluate({**body,'_compile_gpu_detail':True});write('research/detail-squad-api-fixture.json',body)
ui=rename(read('research/detail-random-ui-fixture.json'));ui['snapshot']['snapshot_id']='synthetic-squad-v21';ui.setdefault('settings',{})['shooting-policy']='character';write('research/detail-squad-ui-fixture.json',ui)
n=read('research/detail-expansion-next.json');n['generated_at']=datetime.now(timezone.utc).isoformat();n['objective_complete']=False
n['current_work']=dict(feature='v21 immutable squad affiliation predicate',abi='detail_random_v20',abi_unchanged=True,compiler_change_only=True,
 compile_coverage=119,favorite_contexts_compiled=467,native_diagnostic_passed=80,expected_main_cases=160,expected_python_tests=120,
 regression_session=26394,regression_log='research/detail-squad-tests.log',regression_status='running',api_fixture='research/detail-squad-api-fixture.json',ui_fixture='research/detail-squad-ui-fixture.json',
 notes='Current host/kernel/verifiers frozen while full120 and formal160 run. V20 checkpoint is historical after additive host change. Native diagnostic52250 terminal0 all80 passed. Kernel/layout/binaries unchanged. Ram positive test removes unsupported Rem skills explicitly; negative Ram and both Noir compositions retain all raw skills. API/UI pending; owned4332 server79284 caches v20 host and needs safe restart. Never kill user4317. All-character goal active.')
write('research/detail-expansion-next.json',n)
print(json.dumps(dict(rows=len(compiled['program']['effects']),squad=body['squad'],abi='detail_random_v20'),ensure_ascii=True))
