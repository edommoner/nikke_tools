"""New counter inputs only; project saved Metal blocks without GPU reruns."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('counter_short_suite','research/verify-world-target-counters.py');cross=module('counter_short_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-target-counter-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 rows,programs,bad=suite.prepare();entries=[('native/'+c['name'],w,c) for c,(w,meta) in zip(rows,programs)]
 entries.extend(('reject/'+name,w,None) for name,w in bad);assert len(entries)==32
 packed=array.array('I',[len(entries)])
 for _,w,_ in entries:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return entries,packed.tobytes()
def compare(block,case):
 native=suite.observe_case(case);wanted=suite.expected_observation(native)
 assert block[0]==0 and suite.decoded(block,case)==wanted,case['name'];return native
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('cuda','metal'),default='cuda');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--from-metal',action='store_true');a=ap.parse_args();entries,data=prepare();iw=L['TARGET_COUNTER_INPUT_WORDS']*4;ow=524288*4
 if a.from_metal:
  r=json.loads((ROOT/'research/portable-world-target-counter-metal.json').read_text());p=Path(r['captured']);before=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes()[:32*ow];assert r['passed'] and data[4:]==before[4:4+32*iw];evidence=r['evidence'];golden=dict(input_sha256=sha(data),output_sha256=sha(raw),source_sha256=evidence['source_sha256'])
 else:
  golden=json.loads(GOLDEN.read_text());assert golden['input_sha256']==sha(data) and golden['source_sha256']==source_hashes(suite.SOURCE)
  for i,(name,w,_) in enumerate(entries):assert golden['entries'][i]['name']==name and golden['entries'][i]['input_sha256']==sha(data[4+i*iw:4+(i+1)*iw])
  if a.cpu_only:
   import portable_backend
   calls=dict(build=0,execute=0)
   def forbidden(name):
    def stop(*args,**kwargs):calls[name]+=1;raise AssertionError('GPU forbidden in CPU counter packing/oracles')
    return stop
   with patch.object(portable_backend,'build',forbidden('build')),patch.object(portable_backend,'execute',forbidden('execute')),patch.object(suite,'execute',forbidden('execute')):
    again,repacked=prepare();assert data==repacked
    for i,(_,_,case) in enumerate(again):
     if case is not None:assert cross.digest(suite.observe_case(case))==golden['entries'][i]['native_sha256']
   result=dict(passed=True,input_count=32,native_oracles=10,input_sha256=sha(data),source_sha256=source_hashes(suite.SOURCE),gpu_calls=calls)
   (ROOT/'research/portable-world-target-counter-short-cpu.json').write_text(json.dumps(result,indent=2)+'\n');print('CPU32 inputs/native10/48 steps exact;GPU build/execute0');return
  folder=ROOT/'research/portable-build'/'world-target-counter-cuda-short';folder.mkdir(parents=True,exist_ok=False);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(suite.SOURCE,'portableEvents',data,L['TARGET_COUNTER_INPUT_WORDS'],524288,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(name,w,case) in enumerate(entries):
  block=values[i*524288:(i+1)*524288]
  if case is None:assert block[0]==64;native=dict(status=64)
  else:native=compare(block,case)
  results.append(dict(name=name,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(raw[i*ow:(i+1)*ow]),native_sha256=cross.digest(native)))
 generated={b:cross.normalized((ROOT/'research/portable-build'/('target_counter_entry.'+suffix)).read_bytes()) for b,suffix in [('cuda','cu'),('metal','metal')]}
 if a.from_metal:
  golden.update(entries=results,generated_normalized=generated);GOLDEN.write_text(json.dumps(golden,indent=2)+'\n');print('32 inputs/native10 projected from saved Metal622;GPU0');return
 answer=dict(passed=results==golden['entries'] and sha(raw)==golden['output_sha256'] and generated==golden['generated_normalized'],input_count=32,input_sha256=sha(data),output_sha256=sha(raw),entries=results,generated_normalized=generated,evidence=evidence,normal4682_reexecutions=0,old208_reexecutions=0,old285_reexecutions=0,old357_reexecutions=0,old424_reexecutions=0,old461_reexecutions=0,old484_reexecutions=0,old529_reexecutions=0,old590_reexecutions=0,full_character_verified=0,canonical_world_admission=False)
 (ROOT/'research/portable-world-target-counter-short-summary.json').write_text(json.dumps(answer,indent=2)+'\n');assert answer['passed'];print('CUDA/Metal32 input/output/native10/generated exact')
if __name__=='__main__':main()
