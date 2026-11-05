"""Current common dispatch; optional Mac-only old source raw replay, never on Windows."""
import argparse,array,hashlib,importlib.util,io,json,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
from portable_specs import LIMITS as L
parser=argparse.ArgumentParser();parser.add_argument('--capture-baseline',action='store_true');parser.add_argument('--renew-source',action='store_true');custom,rest=parser.parse_known_args();sys.argv=[sys.argv[0],*rest]
s=importlib.util.spec_from_file_location('status_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
prior=json.loads(subprocess.check_output(['git','show','3f661c8:research/portable-combat-metal.json'],cwd=R));cases=v.fixtures();names=[c['name'] for c in cases]
indices=[names.index(c['name']) for c in prior['cases']]+[names.index('lazy-cache-capacity') if c['name']=='lazy-cache-capacity' else len(names)+i for i,c in enumerate(prior['rejected_cases'])]
original=portable_runtime.execute;calls=0

def execute(source,entry,packed,iw,ow,backend):
 global calls
 calls+=1;assert calls==1 and source=='gpu/event_runtime.slang' and iw==77824 and ow==102400
 prior_input=bytearray(struct.pack('<I',len(indices)));current_input=hashlib.sha256(struct.pack('<I',len(indices)));view=memoryview(packed)
 for index in indices:
  at=4+index*iw*4;words=view[at:at+iw*4];assert struct.unpack_from('<I',words)[0]==0x50455663;current_input.update(words);prior_input.extend(struct.pack('<I',0x50455662));prior_input.extend(words[4:])
 assert hashlib.sha256(prior_input).hexdigest()==prior['input_sha256'],'Every old input must match byte-for-byte except ABI, including the formerly rejected capacity input.'
 baseline=None
 if custom.capture_baseline:
  assert backend=='metal';folder=P/'portable-build/status-v52-control';folder.mkdir(parents=True,exist_ok=True)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','3f661c8','gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
  control=folder/'status_v52_control.slang';control.write_text('#include "gpu/event_runtime.slang"\n')
  baseline,control_evidence=original(control.relative_to(R).as_posix(),entry,bytes(prior_input),77824,94208,backend)
  assert control_evidence['output_sha256']==prior['output_sha256'] and control_evidence['input_sha256']==prior['input_sha256']
 raw,evidence=original(source,entry,packed,iw,ow,backend);current=hashlib.sha256();changes=[];tails_zero=True
 for offset,index in enumerate(indices):
  at=index*ow*4;chunk=raw[at:at+94208*4];current.update(chunk);tails_zero &= not any(raw[at+94208*4:at+ow*4])
  if baseline is None:continue
  old=baseline[offset*94208*4:(offset+1)*94208*4]
  if old==chunk:continue
  a=array.array('I');a.frombytes(old);b=array.array('I');b.frombytes(chunk)
  differences=[dict(word=w,old=x,new=y) for w,(x,y) in enumerate(zip(a,b)) if x!=y]
  name=prior['cases'][offset]['name'] if offset<len(prior['cases']) else prior['rejected_cases'][offset-len(prior['cases'])]['name']
  changes.append(dict(name=name,words=differences,old_status=a[0],new_status=b[0]))
 assert tails_zero
 result=dict(passed=True,backend=backend,prior_proof_commit='3f661c8',prior_inputs=len(indices),current_positive_inputs=len(names),current_inputs=struct.unpack_from('<I',packed)[0],prior_input_sha256=prior['input_sha256'],prior_output_sha256=prior['output_sha256'],current_subset_input_sha256=current_input.hexdigest(),current_subset_output_sha256=current.hexdigest(),input_normalization='ABI 0x50455663 to 0x50455662 only; the former cache-rejection input is now in the positive portion, with identical bytes.',no_output_normalization=True,old_output_prefix_words=94208,new_output_words=ow,all_added_tail_words_zero=True,source_sha256=evidence['source_sha256'],input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'])
 contract=P/'portable-status-previous-output-contract.json'
 if baseline is not None:
  result.update(control_execution=control_evidence,changed_cases=changes);contract.write_text(json.dumps(result,indent=2)+'\n');print('Prior changed cases',[(c['name'],len(c['words']),c['old_status'],c['new_status']) for c in changes],flush=True)
 else:
  expected=json.loads(contract.read_text());assert expected['passed']
  for key in ('current_subset_input_sha256','current_subset_output_sha256'):assert result[key]==expected[key],key
  if custom.renew_source:
   assert backend=='metal';expected.setdefault('verified_source_versions',[]).append(dict(source_sha256=expected['source_sha256'],scope='Old ordered subset equality only; full batch hashes apply only to current top-level source.'))
   expected.update({key:result[key] for key in ('source_sha256','input_sha256','output_sha256','current_positive_inputs','current_inputs')});contract.write_text(json.dumps(expected,indent=2)+'\n')
  else:assert result['source_sha256']==expected['source_sha256']
 (P/f'portable-status-existing-{backend}-parity.json').write_text(json.dumps(result,indent=2)+'\n');return raw,evidence
portable_runtime.execute=execute
v.main();assert calls==1
