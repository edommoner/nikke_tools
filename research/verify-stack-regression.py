"""One current dispatch; optional Mac-only old-source replay for raw delta audit.

The verification itself is backend-independent. --capture-baseline is an explicit
extra control dispatch, never an automatic GPU retry and never used on Windows.
"""
import argparse,array,hashlib,importlib.util,io,json,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
from portable_specs import LIMITS as L
parser=argparse.ArgumentParser();parser.add_argument('--capture-baseline',action='store_true');parser.add_argument('--renew-source',action='store_true');custom,rest=parser.parse_known_args();sys.argv=[sys.argv[0],*rest]
s=importlib.util.spec_from_file_location('stack_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
prior_bytes=subprocess.check_output(['git','show','029aa07:research/portable-combat-metal.json'],cwd=R);prior=json.loads(prior_bytes)
fixtures=v.fixtures();names=[c['name'] for c in fixtures];assert len(names)==len(set(names))
indices=[names.index(c['name']) for c in prior['cases']]+list(range(len(names),len(names)+len(prior['rejected_cases'])))
original=portable_runtime.execute;calls=0

def execute(source,entry,packed,input_words,output_words,backend):
 global calls
 calls+=1;assert calls==1 and source=='gpu/event_runtime.slang' and input_words==77824 and output_words==94208
 old_input=bytearray(struct.pack('<I',len(indices)));view=memoryview(packed);current_input=hashlib.sha256(struct.pack('<I',len(indices)))
 for index in indices:
  at=4+index*input_words*4;program=view[at:at+input_words*4];assert struct.unpack_from('<I',program)[0]==0x50455662
  current_input.update(program);old_input.extend(struct.pack('<I',0x50455661));old_input.extend(program[4:])
 assert hashlib.sha256(old_input).hexdigest()==prior['input_sha256']
 baseline=None
 if custom.capture_baseline:
  assert backend=='metal','The explicit control is intended only for the Mac development host'
  folder=P/'portable-build'/'stack-v50-control';folder.mkdir(parents=True,exist_ok=True)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','029aa07','gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
  control=folder/'stack_v50_control.slang';control.write_text('#include "gpu/event_runtime.slang"\n')
  baseline,control_evidence=original(control.relative_to(R).as_posix(),entry,bytes(old_input),input_words,output_words,backend)
  assert control_evidence['output_sha256']==prior['output_sha256'] and control_evidence['input_sha256']==prior['input_sha256']
 raw,evidence=original(source,entry,packed,input_words,output_words,backend)
 current=hashlib.sha256();changes=[]
 for offset,index in enumerate(indices):
  start=index*output_words*4;chunk=raw[start:start+output_words*4];current.update(chunk)
  if baseline is None:continue
  old=baseline[offset*output_words*4:(offset+1)*output_words*4]
  if old==chunk:continue
  a=array.array('I');a.frombytes(old);b=array.array('I');b.frombytes(chunk)
  words=[]
  for word,(x,y) in enumerate(zip(a,b)):
   if x==y:continue
   delta=word-L['CARRIER_STATE_BASE'];is_time=0<=delta<L['CARRIERS']*L['CARRIER_WORDS'] and delta%L['CARRIER_WORDS'] in (7,8)
   words.append(dict(word=word,old=x,new=y,field='carrier.activated' if is_time else 'other'))
  changes.append(dict(name=prior['cases'][offset]['name'] if offset<len(prior['cases']) else prior['rejected_cases'][offset-len(prior['cases'])]['name'],words=words))
 result=dict(passed=True,prior_proof_commit='029aa07',prior_inputs=len(indices),current_positive_inputs=len(names),current_inputs=struct.unpack_from('<I',packed)[0],
  prior_input_sha256=prior['input_sha256'],prior_output_sha256=prior['output_sha256'],current_subset_input_sha256=current_input.hexdigest(),current_subset_output_sha256=current.hexdigest(),
  input_normalization='ABI word 0x50455662 to 0x50455661 only for prior-input audit',no_output_normalization=True,cpu_trace_used_as_gpu_input=False,
  source_sha256=evidence['source_sha256'],input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'],backend=backend)
 contract=P/'portable-stack-previous-output-contract.json'
 if baseline is not None:
  result.update(control_execution=control_evidence,changed_cases=changes,all_non_activation_timestamp_words_equal=all(w['field']=='carrier.activated' for c in changes for w in c['words']))
  contract.write_text(json.dumps(result,indent=2)+'\n');print('Prior raw delta cases',len(changes),'non-timestamp',sum(w['field']!='carrier.activated' for c in changes for w in c['words']),flush=True)
 else:
  expected=json.loads(contract.read_text());assert expected['passed']
  for key in ('current_subset_input_sha256','current_subset_output_sha256'):assert result[key]==expected[key],key
  if custom.renew_source:
   assert backend=='metal'
   expected.setdefault('verified_source_versions',[]).append(dict(source_sha256=expected['source_sha256'],scope='Old ordered subset equality only; full batch hashes apply only to the current top-level source.'));expected.update({key:result[key] for key in ('source_sha256','input_sha256','output_sha256','current_positive_inputs','current_inputs')});contract.write_text(json.dumps(expected,indent=2)+'\n')
  else:assert result['source_sha256']==expected['source_sha256']
 (P/f'portable-stack-existing-{backend}-parity.json').write_text(json.dumps(result,indent=2)+'\n')
 return raw,evidence
portable_runtime.execute=execute
v.main();assert calls==1
