"""Capture the complete current common verifier input without GPU execution.
This only proves static wire equivalence, never GPU or battle correctness.
"""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime
sp=importlib.util.spec_from_file_location('removal_wire_verifier',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
class Captured(Exception):pass
report={}
def capture(source,entry,packed,input_words,output_words,backend):
 old=json.loads((ROOT/'research/portable-removal-legacy-packing-input.json').read_text());h=hashlib.sha256(packed).hexdigest();assert h==old['input_sha256']
 count=struct.unpack_from('<I',packed)[0];positive=len(v.fixtures());assert (count,positive,count-positive)==(1287,1092,195)
 report.update(passed=True,gpu_execution_verified=False,scope='Typed full positive/rejection input construction only; GPU execution deliberately not performed',positive_inputs=positive,rejection_inputs=count-positive,batched_inputs=count,input_sha256=h,input_words=input_words,output_words=output_words,legacy_input_bytes_equal=True,source=source,entry=entry)
 raise Captured()
portable_runtime.execute=capture
sys.argv=[str(ROOT/'scripts/verify-portable-combat.py'),'--backend','metal']
try:v.main()
except Captured:pass
else:raise RuntimeError('Expected wire capture did not intercept GPU invocation')
(ROOT/'research/portable-removal-wire-preflight.json').write_text(json.dumps(report,indent=2)+'\n');print('Full 1287-input wire exactly retained; no GPU run',flush=True)
