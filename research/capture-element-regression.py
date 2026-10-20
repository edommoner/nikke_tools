"""Unmodified strict regression driver, with readback retained before its guard.

Only records evidence after GPU completion. No input/output normalization,
catch/retry, shader change or replacement of the original comparison occurs.
"""
import array,hashlib,importlib.util,json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as runtime
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('captured_element_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
prior=json.loads(subprocess.check_output(['git','show','ce01fad:research/portable-combat-metal.json'],cwd=R));positive=len(v.fixtures());indices=list(range(len(prior['cases'])))+list(range(positive,positive+len(prior['rejected_cases'])))
windows=json.loads((R/'research/windows-portable-element-v65.json').read_text());assert windows['passed']
baseline=R/'research/portable-build/element-reproduction/run-0.bin';assert baseline.exists();h=hashlib.sha256()
with baseline.open('rb') as f:
 while chunk:=f.read(8*1024*1024):h.update(chunk)
assert h.hexdigest()==windows['output_sha256']
stride=L['OUTPUT_WORDS']*4;expected=[]
with baseline.open('rb') as f:
 for index in indices:f.seek(index*stride);expected.append(hashlib.sha256(f.read(stride)).hexdigest())
original=runtime.dispatch_programs

def recorded(programs,**kwargs):
 raw,e=original(programs,**kwargs);old=hashlib.sha256();changed=[];hashes=[]
 with baseline.open('rb') as f:
  for oi,index in enumerate(indices):
   block=memoryview(raw)[index*stride:(index+1)*stride];digest=hashlib.sha256(block).hexdigest();hashes.append(digest);old.update(block)
   if digest!=expected[oi]:
    f.seek(index*stride);a=array.array('I');a.frombytes(block);b=array.array('I');b.frombytes(f.read(stride));words=[dict(word=i,current=x,baseline=y) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    name=prior['cases'][oi]['name'] if oi<len(prior['cases']) else prior['rejected_cases'][oi-len(prior['cases'])]['name']
    changed.append(dict(prior_index=oi,current_index=index,name=name,changed_words=len(words),first_words=words[:32]))
 passed=old.hexdigest()==prior['output_sha256'] and not changed
 report=dict(passed=passed,stage='readback-before-original-guard-and-native-comparisons',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),original_driver='research/verify-element-regression.py',original_driver_sha256=hashlib.sha256((R/'research/verify-element-regression.py').read_bytes()).hexdigest(),capture_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),old_output_sha256=old.hexdigest(),prior_output_sha256=prior['output_sha256'],per_old_program_sha256=hashes,baseline_full_output_sha256=windows['output_sha256'],changed=changed,evidence=e,no_gpu_retry=True,no_output_normalization=True)
 if not passed:
  path=R/'research/portable-build/element-captured-failure.bin';path.write_bytes(raw);report['failed_raw_path']=str(path)
 (R/'research/portable-element-core-readback-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
 return raw,e
runtime.dispatch_programs=recorded
s=importlib.util.spec_from_file_location('strict_element_driver',R/'research/verify-element-regression.py');driver=importlib.util.module_from_spec(s);s.loader.exec_module(driver);driver.main()
