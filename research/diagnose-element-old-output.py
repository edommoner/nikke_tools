"""Diagnose full-cohort versus isolated-old-core readbacks; never seals proof."""
import array,hashlib,importlib.util,json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as runtime
from portable_specs import LIMITS as L
spec=importlib.util.spec_from_file_location('element_diagnostic',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
old=json.loads(subprocess.check_output(['git','show','ce01fad:research/portable-combat-metal.json'],cwd=R));positive=len(v.fixtures());indices=list(range(len(old['cases'])))+list(range(positive,positive+len(old['rejected_cases'])))
original=runtime.dispatch_programs

def dispatch(programs,**kwargs):
 raw,e=original(programs,**kwargs);control,ce=original([programs[i] for i in indices],backend=kwargs['backend']);stride=L['OUTPUT_WORDS']*4
 directory=R/'research/portable-build/element-output-diagnostic';directory.mkdir(exist_ok=True)
 changed=[]
 for oi,index in enumerate(indices):
  a=memoryview(raw)[index*stride:(index+1)*stride];b=memoryview(control)[oi*stride:(oi+1)*stride]
  if a==b:continue
  aw=array.array('I');aw.frombytes(a);bw=array.array('I');bw.frombytes(b)
  words=[dict(word=j,current=x,control=y) for j,(x,y) in enumerate(zip(aw,bw)) if x!=y]
  name=old['cases'][oi]['name'] if oi<len(old['cases']) else old['rejected_cases'][oi-len(old['cases'])]['name']
  changed.append(dict(prior_index=oi,current_index=index,name=name,changed_words=len(words),first_words=words[:24],current_sha256=hashlib.sha256(a).hexdigest(),control_sha256=hashlib.sha256(b).hexdigest()))
  if len(changed)<=4:(directory/(str(oi)+'-current.bin')).write_bytes(a);(directory/(str(oi)+'-control.bin')).write_bytes(b)
 report=dict(passed=False,diagnostic_only=True,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),prior_proof='ce01fad',cohort_programs=len(programs),old_programs=len(indices),isolated_old_output_matches_prior=ce['output_sha256']==old['output_sha256'],isolated_control=ce,current=e,changed=changed)
 (R/'research/portable-element-old-output-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print('changed',len(changed),'isolated matches prior',report['isolated_old_output_matches_prior'],[(c['name'],c['changed_words']) for c in changed[:8]],flush=True)
 return raw,e
runtime.dispatch_programs=dispatch;sys.argv=[sys.argv[0],'--backend','metal']
v.main()
