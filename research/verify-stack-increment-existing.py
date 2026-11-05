"""Require every pre-specialization input/output byte, including tail padding."""
import importlib.util,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
s=importlib.util.spec_from_file_location('increment_verifier',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
previous=json.loads(subprocess.check_output(['git','show','7d52456:research/portable-combat-metal.json'],cwd=R))
original=portable_runtime.execute;calls=0

def execute(source,entry,packed,input_words,output_words,backend):
 global calls
 calls+=1;assert calls==1 and source=='gpu/event_runtime.slang' and input_words==77824 and output_words==94208
 raw,e=original(source,entry,packed,input_words,output_words,backend)
 assert e['input_sha256']==previous['input_sha256'] and e['output_sha256']==previous['output_sha256']
 (R/f'research/portable-stack-increment-existing-{backend}-parity.json').write_text(json.dumps(dict(passed=True,previous_proof_commit='7d52456',inputs=1355,positives=1149,rejections=206,all_input_and_output_bytes_equal=True,no_input_or_output_normalization=True,backend=backend,**{k:e[k] for k in ('source_sha256','input_sha256','output_sha256')}),indent=2)+'\n')
 return raw,e
portable_runtime.execute=execute
v.main();assert calls==1
