"""68 new status/recipient inputs;one shared CUDA/Metal comparison driver."""
import argparse,array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('status_short_suite','research/verify-world-actor-status.py');cross=module('status_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-actor-status-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 entries=[]
 for label,driver in [('status',suite),('recipient',suite.recipient)]:
  rows,programs,bad=driver.prepare()
  for c,(words,meta,bindings) in zip(rows,programs):
   w=list(words);w[0]=L['WORLD_ACTOR_STATUS_ABI'];entries.append((label+'/native/'+c['name'],w,(driver,c,meta,bindings)))
  for name,words in bad:
   w=list(words);w[0]=L['WORLD_ACTOR_STATUS_ABI'];entries.append((label+'/reject/'+name,w,None))
 assert len(entries)==68
 a=array.array('I',[68])
 for _,w,_ in entries:a.extend(w)
 if sys.byteorder!='little':a.byteswap()
 return entries,a.tobytes()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('cuda','metal'),default='cuda');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--from-metal',action='store_true');a=ap.parse_args();entries,data=prepare();iw=92336*4;ow=524288*4
 if a.from_metal:
  r=json.loads((ROOT/'research/portable-world-actor-status-metal.json').read_text());p=Path(r['captured']);before=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes()[:68*ow];assert data[4:]==before[4:4+68*iw] and r['passed'];evidence=r['evidence'];golden=dict(input_sha256=sha(data),output_sha256=sha(raw),source_sha256=evidence['source_sha256'],entries=[])
 else:
  golden=json.loads(GOLDEN.read_text());assert golden['input_sha256']==sha(data) and golden['source_sha256']==source_hashes(suite.SOURCE)
  for i,(name,w,_) in enumerate(entries):assert golden['entries'][i]['name']==name and golden['entries'][i]['input_sha256']==sha(data[4+i*iw:4+(i+1)*iw])
  if a.cpu_only:
   import portable_backend
   calls=dict(build=0,execute=0)
   def forbidden(name):
    def stop(*args,**kwargs):calls[name]+=1;raise AssertionError('GPU forbidden in CPU packing/oracles')
    return stop
   with patch.object(portable_backend,'build',forbidden('build')),patch.object(portable_backend,'execute',forbidden('execute')),patch.object(suite,'execute',forbidden('execute')),patch.object(suite.recipient,'execute',forbidden('execute')):
    again,repacked=prepare();assert repacked==data
    for i,(_,_,domain) in enumerate(again):
     if domain is not None:assert cross.digest(suite.recipient.state.fields.pool.observe(domain[1]))==golden['entries'][i]['native_sha256']
   result=dict(passed=True,input_count=68,native_oracles=56,input_sha256=sha(data),source_sha256=source_hashes(suite.SOURCE),gpu_calls=calls)
   (ROOT/'research/portable-world-actor-status-short-cpu.json').write_text(json.dumps(result,indent=2)+'\n');print('CPU68 inputs/native56 exact;GPU build/execute0');return
  folder=ROOT/'research/portable-build'/'world-actor-status-cuda-short';folder.mkdir(parents=True,exist_ok=False);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(suite.SOURCE,'portableEvents',data,92336,524288,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(name,w,domain) in enumerate(entries):
  block=values[i*524288:(i+1)*524288]
  if domain is None:assert block[0]==64;native=dict(status=64)
  else:
   driver,c,meta,bindings=domain;actual=driver.decoded(block,meta,c,bindings);native=suite.recipient.state.fields.pool.observe(c);assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope'),name
  results.append(dict(name=name,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(raw[i*ow:(i+1)*ow]),native_sha256=cross.digest(native)))
 generated={b:cross.normalized((ROOT/'research/portable-build'/('world_actor_status_entry.'+suffix)).read_bytes()) for b,suffix in [('cuda','cu'),('metal','metal')]}
 if a.from_metal:
  golden.update(entries=results,generated_normalized=generated);GOLDEN.write_text(json.dumps(golden,indent=2)+'\n');print('68 inputs/native56 projected from saved Metal529;GPU0');return
 answer=dict(passed=results==golden['entries'] and sha(raw)==golden['output_sha256'] and generated==golden['generated_normalized'],input_count=68,input_sha256=sha(data),output_sha256=sha(raw),entries=results,generated_normalized=generated,evidence=evidence,normal4682_reexecutions=0,old208_reexecutions=0,old285_reexecutions=0,old357_reexecutions=0,old424_reexecutions=0,old461_reexecutions=0,full_character_verified=0,canonical_world_admission=False)
 (ROOT/'research/portable-world-actor-status-short-summary.json').write_text(json.dumps(answer,indent=2)+'\n');assert answer['passed'];print('CUDA/Metal68 input/output/native56/generated exact')
if __name__=='__main__':main()
