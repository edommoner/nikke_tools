"""Capture every readback before comparison to investigate an intermittent gate.
No timing/optimization claim. The first mismatch is persisted, never retried away.
"""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as runtime
from portable_specs import LIMITS as L
spec=importlib.util.spec_from_file_location('element_reproduce',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
prior=json.loads(subprocess.check_output(['git','show','ce01fad:research/portable-combat-metal.json'],cwd=R));cases=v.fixtures();indices=list(range(len(prior['cases'])))+list(range(len(cases),len(cases)+len(prior['rejected_cases'])))
programs=[]
class Captured(BaseException):pass
def capture(p,**kwargs):programs.extend(p);raise Captured()
p=R/'research/portable-combat-metal.json';saved=p.read_bytes();v.run_programs=capture;sys.argv=[sys.argv[0],'--backend','metal']
try:
 try:v.main()
 except Captured:pass
finally:p.write_bytes(saved)
assert len(programs)==2182
stride=L['OUTPUT_WORDS']*4;directory=R/'research/portable-build/element-reproduction';directory.mkdir(exist_ok=True)
control,ce=runtime.dispatch_programs([programs[i] for i in indices],backend='metal');assert ce['output_sha256']==prior['output_sha256'];expected=[hashlib.sha256(memoryview(control)[i*stride:(i+1)*stride]).hexdigest() for i in range(2006)];del control
report=dict(passed=False,complete=False,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),diagnostic_only=True,initial_failure_not_discarded=True,old_control=ce,runs=[])
report_path=R/'research/portable-element-reproduction.json'
for sample,size in enumerate((2048,2048,1024,2048)):
 raw,e=runtime.dispatch_programs(programs,backend='metal',batch_size=size);raw_path=directory/('run-'+str(sample)+'.bin');raw_path.write_bytes(raw)
 old_sha=hashlib.sha256();changed=[]
 for oi,index in enumerate(indices):
  b=memoryview(raw)[index*stride:(index+1)*stride];old_sha.update(b)
  if hashlib.sha256(b).hexdigest()!=expected[oi]:
   (directory/('changed-'+str(sample)+'-'+str(oi)+'.bin')).write_bytes(b)
   name=prior['cases'][oi]['name'] if oi<len(prior['cases']) else prior['rejected_cases'][oi-len(prior['cases'])]['name']
   changed.append(dict(prior_index=oi,current_index=index,name=name))
 row=dict(sample=sample,batch_size=size,raw_path=str(raw_path),old_output_sha256=old_sha.hexdigest(),old_output_matches_prior=old_sha.hexdigest()==prior['output_sha256'],changed=changed,evidence=e);report['runs'].append(row)
 report_path.write_text(json.dumps(report,indent=2)+'\n');print(sample,size,'changed',len(changed),'full',e['output_sha256'],changed[:4],flush=True)
 if changed:raise RuntimeError('Captured nonmatching output; no retry')
 del raw
report.update(passed=True,complete=True,conclusion='All four diagnostic executions matched the old2006 core; initial gate mismatch remains separately documented')
report_path.write_text(json.dumps(report,indent=2)+'\n')
