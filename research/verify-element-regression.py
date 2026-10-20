"""Execute the full current core, preserving all2006 prior inputs/readbacks."""
import argparse,array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime
from portable_specs import ABI,LIMITS as L
PRIOR='ce01fad'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['metal','cuda'],default='metal');parser.add_argument('--batch-size',type=int);args=parser.parse_args()
 prior=json.loads(subprocess.check_output(['git','show',PRIOR+':research/portable-combat-metal.json'],cwd=R));assert prior['passed']
 spec=importlib.util.spec_from_file_location('element_full_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 cases=v.fixtures();names=[c['name'] for c in cases];old_names=[c['name'] for c in prior['cases']]
 assert names[:len(old_names)]==old_names
 indices=list(range(len(old_names)))+list(range(len(names),len(names)+len(prior['rejected_cases'])));assert len(indices)==2006
 original=portable_runtime.dispatch_programs;calls=0;projection=None
 def dispatch(programs,**kwargs):
  nonlocal calls,projection
  calls+=1;assert calls==1 and ABI==0x5045566B
  old_input=hashlib.sha256(struct.pack('<I',len(indices)))
  for index in indices:
   words=array.array('I',programs[index][0]);assert words[0]==ABI;words[0]=0x5045566A
   if sys.byteorder!='little':words.byteswap()
   old_input.update(words.tobytes())
  assert old_input.hexdigest()==prior['input_sha256'],'Old inputs changed beyond the ABI number'
  raw,e=original(programs,**kwargs);digest=hashlib.sha256();stride=L['OUTPUT_WORDS']*4
  for index in indices:digest.update(memoryview(raw)[index*stride:(index+1)*stride])
  assert digest.hexdigest()==prior['output_sha256'],'Every prior output word must remain unchanged'
  projection=dict(passed=True,prior_proof_commit=PRIOR,prior_inputs=2006,current_inputs=len(programs),current_positive_inputs=len(names),prior_input_sha256=prior['input_sha256'],prior_output_sha256=prior['output_sha256'],input_projection='ABI6B to6A only; same strides and every other input byte preserved',all_old_output_words_equal=True,no_output_normalization=True,source_sha256=e['source_sha256'],input_sha256=e['input_sha256'],output_sha256=e['output_sha256'],actual_dispatch_counts=[d['transport']['cases'] for d in e.get('dispatches',[e])],driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
  (P/f'portable-element-existing-{args.backend}-parity.json').write_text(json.dumps(projection,indent=2)+'\n');return raw,e
 portable_runtime.dispatch_programs=dispatch;oldargv=sys.argv;sys.argv=[sys.argv[0],'--backend',args.backend]+(['--batch-size',str(args.batch_size)] if args.batch_size is not None else [])
 try:v.main();assert calls==1
 finally:portable_runtime.dispatch_programs=original;sys.argv=oldargv
 path=P/f'portable-combat-{args.backend}.json';result=json.loads(path.read_text());assert result['passed']
 assert result['rejected_cases'][:len(prior['rejected_cases'])]==prior['rejected_cases']
 for key in prior:
  if key.endswith('_cpu_regressions') or key.startswith('known_'):assert result[key]==prior[key],key
 result['element_override_existing_parity']=projection;path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('All2006 previous inputs,output words and CPU regression groups preserved')
if __name__=='__main__':main()
