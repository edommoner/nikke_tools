"""Run the shared verifier once and hash every prior input/output byte in place.

New positive cases may move old cases. Reassemble only the old batch order for
hashing after the real dispatch; no old/CPU output is supplied to the GPU.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

R=Path(__file__).resolve().parents[1];P=R/'research'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
spec=importlib.util.spec_from_file_location('session_verifier',R/'scripts/verify-portable-combat.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
previous=json.loads(subprocess.check_output(['git','show','169a6a3:research/portable-combat-metal.json'],cwd=R))
current_names=[c['name'] for c in verifier.fixtures()]
assert len(current_names)==len(set(current_names))==1149
prior_names=[c['name'] for c in previous['cases']]
indices=[current_names.index(name) for name in prior_names]+list(range(len(current_names),len(current_names)+206))
original=portable_runtime.execute
calls=0

def execute(source,entry,packed,input_words,output_words,backend):
    global calls
    calls+=1;assert calls==1 and source=='gpu/event_runtime.slang'
    count,=struct.unpack_from('<I',packed)
    assert count==1355 and len(indices)==1345
    old_input=hashlib.sha256(struct.pack('<I',len(indices)))
    view=memoryview(packed)
    for i in indices:old_input.update(view[4+i*input_words*4:4+(i+1)*input_words*4])
    assert old_input.hexdigest()==previous['input_sha256']
    raw,evidence=original(source,entry,packed,input_words,output_words,backend)
    old_output=hashlib.sha256();view=memoryview(raw)
    for i in indices:old_output.update(view[i*output_words*4:(i+1)*output_words*4])
    assert old_output.hexdigest()==previous['output_sha256']
    report=dict(passed=True,previous_proof_commit='169a6a3',previous_inputs=1345,previous_positives=1139,
                current_inputs=count,current_positives=len(current_names),rejections=206,
                all_prior_input_and_output_bytes_equal=True,no_output_normalization=True,
                prior_input_sha256=old_input.hexdigest(),prior_output_sha256=old_output.hexdigest(),
                cpu_trace_used_as_gpu_input=False,backend=backend,
                source_sha256=evidence['source_sha256'],input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'])
    (P/f'portable-session-identity-existing-{backend}-parity.json').write_text(json.dumps(report,indent=2)+'\n')
    return raw,evidence

portable_runtime.execute=execute
verifier.main()
assert calls==1
