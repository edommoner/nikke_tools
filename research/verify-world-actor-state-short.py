"""67 new named-state checks from composed Metal424;one shared driver for both GPU backends."""
import argparse,array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('state_short_suite','research/verify-world-actor-state.py');cross=module('state_short_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-actor-state-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 rows,programs,bad=suite.prepare();entries=[]
 for c,(w,meta,bindings) in zip(rows,programs):entries.append(('native/'+c['name'],w,(c,meta,bindings)))
 for name,w in bad:entries.append(('reject/'+name,w,None))
 assert len(entries)==67
 a=array.array('I',[67])
 for _,w,_ in entries:a.extend(w)
 if sys.byteorder!='little':a.byteswap()
 return entries,a.tobytes()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('cuda','metal'),default='cuda');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--from-metal',action='store_true');a=ap.parse_args();entries,data=prepare();iw=92336*4;ow=262144*4
 if a.from_metal:
  r=json.loads((ROOT/'research/portable-world-actor-state-metal.json').read_text());p=Path(r['captured']);before=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes()[:67*ow];assert data[4:]==before[4:4+67*iw] and r['passed'];evidence=r['evidence'];golden=dict(input_sha256=sha(data),output_sha256=sha(raw),source_sha256=evidence['source_sha256'],entries=[])
 else:
  golden=json.loads(GOLDEN.read_text());assert golden['input_sha256']==sha(data) and golden['source_sha256']==source_hashes(suite.SOURCE)
  for i,(name,w,_) in enumerate(entries):assert golden['entries'][i]['name']==name and golden['entries'][i]['input_sha256']==sha(data[4+i*iw:4+(i+1)*iw])
  if a.cpu_only:
   import portable_backend
   calls=dict(build=0,execute=0)
   def forbidden(name):
    def stop(*args,**kwargs):calls[name]+=1;raise AssertionError('GPU forbidden in CPU packing/oracles')
    return stop
   with patch.object(portable_backend,'build',forbidden('build')),patch.object(portable_backend,'execute',forbidden('execute')),patch.object(suite,'execute',forbidden('execute')),patch.object(suite.fields.pool,'execute',forbidden('execute')):
    again,repacked=prepare();assert repacked==data
    for i,(_,_,domain) in enumerate(again):
     if domain is not None:assert cross.digest(suite.fields.pool.observe(domain[0]))==golden['entries'][i]['native_sha256']
   result=dict(passed=True,input_count=67,native_oracles=49,input_sha256=sha(data),source_sha256=source_hashes(suite.SOURCE),gpu_calls=calls)
   (ROOT/'research/portable-world-actor-state-short-cpu.json').write_text(json.dumps(result,indent=2)+'\n');print('CPU67 inputs/native49 exact;GPU build/execute0');return
  folder=ROOT/'research/portable-build'/'world-actor-state-cuda-short';folder.mkdir(parents=True,exist_ok=False);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(suite.SOURCE,'portableEvents',data,92336,262144,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(name,w,domain) in enumerate(entries):
  block=values[i*262144:(i+1)*262144]
  if domain is None:assert block[0]==64;native=dict(status=64)
  else:
   c,meta,bindings=domain;actual=suite.decoded(block,meta,c,bindings);native=suite.fields.pool.observe(c);assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope'),name
  results.append(dict(name=name,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(raw[i*ow:(i+1)*ow]),native_sha256=cross.digest(native)))
 generated={b:cross.normalized((ROOT/'research/portable-build'/('world_actor_state_entry.'+suffix)).read_bytes()) for b,suffix in [('cuda','cu'),('metal','metal')]}
 if a.from_metal:
  golden.update(entries=results,generated_normalized=generated);GOLDEN.write_text(json.dumps(golden,indent=2)+'\n');print('67 inputs and49 native expectations projected from saved Metal424;GPU calls0');return
 answer=dict(passed=results==golden['entries'] and sha(raw)==golden['output_sha256'] and generated==golden['generated_normalized'],input_count=67,input_sha256=sha(data),output_sha256=sha(raw),entries=results,generated_normalized=generated,evidence=evidence,normal4682_reexecutions=0,old208_reexecutions=0,old285_reexecutions=0,old357_reexecutions=0,full_character_verified=0,canonical_world_admission=False)
 (ROOT/'research/portable-world-actor-state-short-summary.json').write_text(json.dumps(answer,indent=2)+'\n');assert answer['passed'];print('CUDA/Metal67 input/output/native49/generated exact')
if __name__=='__main__':main()
