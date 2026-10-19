"""Current shared dispatch, preserving all1709 prior inputs and output words."""
import hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
s=importlib.util.spec_from_file_location('protection_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
prior=json.loads(subprocess.check_output(['git','show','b8ae1c7:research/portable-combat-metal.json'],cwd=R));cases=v.fixtures();names=[c['name'] for c in cases];old_names=[c['name'] for c in prior['cases']]
indices=[names.index(n) for n in old_names]+list(range(len(names),len(names)+len(prior['rejected_cases'])))
original=portable_runtime.execute;calls=0

def execute(source,entry,packed,iw,ow,backend):
 global calls
 calls+=1;assert calls==1 and source=='gpu/event_runtime.slang' and (iw,ow)==(86016,159744)
 old_input=hashlib.sha256(struct.pack('<I',len(indices)));view=memoryview(packed)
 for index in indices:
  words=view[4+index*iw*4:4+(index+1)*iw*4];assert struct.unpack_from('<I',words)[0]==0x50455666
  old_input.update(struct.pack('<I',0x50455665));old_input.update(words[4:81920*4]);assert not any(words[81920*4:]),'old input extension must be zero'
 assert old_input.hexdigest()==prior['input_sha256'],'Old inputs changed beyond ABI and zero extension'
 raw,e=original(source,entry,packed,iw,ow,backend);old_output=hashlib.sha256()
 for index in indices:
  chunk=memoryview(raw)[index*ow*4:(index+1)*ow*4];old_output.update(chunk[:135168*4]);assert not any(chunk[135168*4:]),'old output extension must remain zero'
 assert old_output.hexdigest()==prior['output_sha256'],'Every old output word must match without normalization'
 report=dict(passed=True,prior_proof_commit='b8ae1c7',prior_inputs=len(indices),current_inputs=struct.unpack_from('<I',packed)[0],current_positive_inputs=len(names),prior_input_sha256=prior['input_sha256'],prior_output_sha256=prior['output_sha256'],input_projection='ABI66 to65 and remove4096 zero words only',no_output_normalization=True,all_old_output_words_equal=True,all_added_old_output_tail_words_zero=True,current_input_words=iw,current_output_words=ow,**e)
 (P/f'portable-split-existing-{backend}-parity.json').write_text(json.dumps(report,indent=2)+'\n');return raw,e
portable_runtime.execute=execute
v.main();assert calls==1
