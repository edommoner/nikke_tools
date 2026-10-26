"""CPU-only full106 live-parent regression; never a new capture or seal."""
import ast,contextlib,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parent
ROOT=BASE/'parent-reuse-v1-package'
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('proof_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
from portable_parent_oracles import ParentOracles,provider
from portable_coordinate_parent_check import method_shapes,key
source=BASE/'metal-v3-wire';baseline=BASE/'sealed-v1-package'
out=BASE/'parent-reuse-cpu-v1';out.mkdir(exist_ok=False)
def write(name,value):
 with (out/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
try:
 with cli.forbid_gpu(),contextlib.ExitStack() as stack:
  current=cli.verify_package(ROOT);old=cli.verify_saved_package(baseline);execution=cli.verify_saved_package(BASE/'package-v4-wire')
  assert current['golden']==old['golden']==json.loads((BASE/'golden-v2.json').read_text())
  independent=json.loads((BASE/'independent-v2.json').read_text());assert independent['calculation_verified'] and independent['input_count']==106 and independent['native_cases']==63 and independent['output_sha256']==current['golden']['output_sha256']
  claim=json.loads((BASE/'package-v4-wire/gpu-claimed-metal.json').read_text());assert claim['package_id']==execution['package_id'] and Path(claim['capture']).resolve()==source.resolve()
  assert json.loads((source/'result.json').read_text())['calculation_verified']
  before={r['path']:r['sha256'] for r in old['files']};after={r['path']:r['sha256'] for r in current['files']}
  changed={n for n in before if before[n]!=after.get(n)}
  assert changed=={'app/portable_parent_oracles.py','research/verify-coordinate-resident-arc-short.py','tests/test_coordinate_resident_arc.py','tests/test_portable_parent_oracles.py'},changed
  script='research/verify-coordinate-resident-arc-short.py';assert method_shapes(baseline/script)==method_shapes(ROOT/script)
  cli_names=('native_value','cpu_preflight','compare_readback','forbid_gpu','audit_capture','audited_comparison')
  assert method_shapes(baseline/'scripts/nikke_gpu.py',cli_names)==method_shapes(ROOT/'scripts/nikke_gpu.py',cli_names)
  anchors=cli.file_records(source,['artifacts.json','evidence.json','run.json','comparison.json'])
  adapter=cli.open_suite(current);rows,_=adapter.prepare();targets={}
  for _,_,domain in rows:
   if domain is None:continue
   target=provider(adapter,domain);assert target is not None and target[4]=='reference' and target[3] is domain
   owner,name,fn,_,_=target
   item=targets.setdefault((id(owner),name),dict(owner=owner,name=name,fn=fn,keys=set()));item['keys'].add(key(domain))
  counts=dict(preflight=0,comparison=0);phase=['preflight']
  for item in targets.values():
   def witnessed(domain,entry=item):
    if key(domain) in entry['keys']:
     counts[phase[0]]+=1
     if phase[0]=='comparison':raise AssertionError('Repeated native call during live-parent comparison')
    return entry['fn'](domain)
   stack.enter_context(patch.dict(item['owner'],{item['name']:witnessed}))
  fixture=out/'read-only-fixture';fixture.mkdir()
  for name in ('readback.bin','generated.cu','generated.metal','evidence.json','runtime.json','run.json','generation-cache.json','phases.jsonl'):
   os.link(source/name,fixture/name)
  stack.enter_context(patch.object(cli,'open_suite',return_value=adapter))
  live=ParentOracles(current,fixture)
  try:
   started=time.perf_counter();cpu=cli.cpu_preflight(current,parent_oracles=live,input_capture=fixture);cpu_seconds=time.perf_counter()-started
   assert live.usable and counts['preflight']==63
   write('cpu.json',cpu);phase[0]='comparison'
   started=time.perf_counter();comparison=cli.compare_readback(current,fixture,parent_oracles=live);comparison_seconds=time.perf_counter()-started
   assert comparison['calculation_verified'] and comparison['input_count']==106 and comparison['native_oracles']==63 and counts['comparison']==0
   assert comparison['parent_oracles']['reused_native_cases']==63 and comparison['parent_oracles']['fresh_native_cases']==0
   original=json.loads((source/'comparison.json').read_text())
   for name in ('entries','input_sha256','output_sha256','generated_normalized'):assert comparison[name]==original[name],name
   write('comparison.json',comparison)
  finally:live.close()
  cli.check_records(source,anchors);cli.verify_package(ROOT)
  result=dict(schema='resident-parent-reuse-cpu-v1',passed=True,mode='saved-raw-fixture-regression',inputs=106,native_cases=63,preflight_native_calls=counts['preflight'],additional_comparison_native_calls=counts['comparison'],preflight_seconds=cpu_seconds,comparison_seconds=comparison_seconds,parent_oracles=comparison['parent_oracles'],all_comparison_entries_equal_original=True,original_independent_receipt_sha256=hashlib.sha256((BASE/'independent-v2.json').read_bytes()).hexdigest(),package_id=current['package_id'],changed_files=sorted(changed),gpu_calls=0,new_gpu_capture=False,independent_audit=False,calculation_verified=False,scope='Fresh same-process CPU preflight plus exact full106 comparison against original independently sealed Metal raw; no GPU execution or file cache of native values')
  write('result.json',result);print(json.dumps(result,indent=2))
except BaseException as error:
 write('failure.json',dict(error=type(error).__name__+': '+str(error),gpu_calls=0,passed=False));raise
