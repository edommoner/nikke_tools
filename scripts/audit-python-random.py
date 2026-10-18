"""Synthetic CPython PRNG references for a future GPU random-target port.
Only a seeded initial state may initialize GPU execution. Observed random draws
and selected recipients are oracle outputs, never simulation inputs.
"""
import hashlib,inspect,json,platform,random
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 cases=[]
 for seed in (0,1,12345,4294967295):
  rng=random.Random(seed);initial=list(rng.getstate()[1])
  assert len(initial)==625 and initial[-1]==624
  words=[rng.getrandbits(32) for _ in range(1300)]
  bits=[{'bits':k,'value':rng.getrandbits(k)} for k in [0,1,2,3,5,7,16,31,32]*8]
  below=[{'n':n,'value':rng._randbelow(n)} for n in [1,2,3,4,5]*30]
  samples=[{'pool':list(range(n)),'k':k,'result':rng.sample(list(range(n)),k)} for n in range(6) for k in range(n+1) for _ in range(3)]
  cases.append({'seed':seed,'initial_state':initial,'words':words,'bits':bits,'below':below,'samples':samples,'final_state':list(rng.getstate()[1])})
 source=Path(random.__file__)
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'cpu_reference_only':True,'gpu_implemented':False,'python_version':platform.python_version(),
         'scope':'Seeded integer MT state, word/twist boundaries, getrandbits, small-pool _randbelow rejection and ordered sample; not full random gameplay parity',
         'gpu_initialization_inputs':['seed','initial_state'],'oracle_outputs_only':['words','bits','below','samples','final_state'],
         'sample_source':inspect.getsource(random.Random.sample),'randbelow_source':inspect.getsource(random.Random._randbelow_with_getrandbits),
         'stdlib_source':str(source),'stdlib_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':cases}
 (ROOT/'research/detail-python-random-cpu-references.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'python':report['python_version'],'seeds':len(cases),'words_per_seed':1300,'samples_per_seed':len(samples),'gpu_implemented':False}))
if __name__=='__main__':main()
