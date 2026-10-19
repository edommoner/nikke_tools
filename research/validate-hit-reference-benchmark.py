"""Audit measured normal-workload output bytes and actual final damage.
Run after timing variants; this GPU invocation is a readback audit, not a sample.
"""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import decode
from portable_backend import execute
from portable_specs import LIMITS as L
sp=importlib.util.spec_from_file_location('reference_benchmark_verifier',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
f=ROOT/'tests/fixtures/portable-hit-reference-benchmark.json';words,meta=v.compile_case(json.loads(f.read_text()));count=64;packed=struct.pack('<'+'I'*(1+count*L['INPUT_WORDS']),count,*(words*count))
raw,evidence=execute('gpu/event_runtime.slang','portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend='metal');data=struct.unpack('<'+'I'*(count*L['OUTPUT_WORDS']),raw);rows=[]
for i in range(count):
 a=decode(data[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],meta)
 assert a['status']==0 and a['frames']==3601 and a['trace_total']==1200 and a['body_damage']==[1200,0,0,0,0]
 assert a['resource_queries'][0]['present'] and a['resource_queries'][0]['value']==1
 rows.append(dict(status=a['status'],frames=a['frames'],packets=a['trace_total'],body_damage=a['body_damage'],resource_value=a['resource_queries'][0]['value']))
for variant in ('before','after'):
 report=json.loads((ROOT/f'research/portable-hit-reference-benchmark-{variant}.json').read_text())
 for sample in report['samples']:
  for k in ('input_sha256','output_sha256'):assert sample[k]==evidence[k],(variant,k)
report=dict(passed=True,gpu_execution_verified=True,timing_sample=False,scope='Post-sample readback audit. Final body damage and packet count verified in all 64 programs; bytes match every saved normal-frequency timing sample. Optional query list is empty in this workload and is not the damage proof.',rows=rows,execution=evidence,validation_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [f,Path(__file__).resolve()]})
(ROOT/'research/portable-hit-reference-benchmark-readback.json').write_text(json.dumps(report,indent=2)+'\n');print('All 64 final-damage readbacks match all normal timing sample output hashes')
