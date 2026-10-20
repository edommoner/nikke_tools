"""77 necessary Actor checks;shared fixtures/decoder with Metal285, no normal rerun."""
import argparse,array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pool=module('short_pools','research/verify-world-actor-pools.py');actor=module('short_registry','research/verify-world-actors.py');cross=module('short_digest','research/summarize-portable-cross-gpu.py')
GOLDEN=ROOT/'research/portable-world-actor-pools-short-expected.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def prepare():
 rows,programs,bad=pool.prepare();ar=actor.cases();ap=[actor.compile_case(c) for c in ar];ab=actor.negatives(ap);entries=[]
 for c,(w,meta,bindings) in zip(rows,programs):entries.append(('pool/native/'+c['name'],w,('pool',c,meta,bindings)))
 for name,w in bad:entries.append(('pool/reject/'+name,w,('reject',)))
 for c,(w,bindings) in zip(ar,ap):
  w=list(w);w[0]=L['WORLD_ACTOR_POOL_ABI'];w.extend([0]*(L['WORLD_ACTOR_POOL_INPUT_WORDS']-len(w)));entries.append(('registry/native/'+c['name'],w,('registry',c,bindings)))
 for name,w in ab:
  w=list(w);w[0]=L['WORLD_ACTOR_POOL_ABI'];w.extend([0]*(L['WORLD_ACTOR_POOL_INPUT_WORDS']-len(w)));entries.append(('registry/reject/'+name,w,('reject',)))
 assert len(entries)==77
 a=array.array('I',[len(entries)])
 for _,w,_ in entries:a.extend(w)
 if sys.byteorder!='little':a.byteswap()
 return entries,a.tobytes()
def semantic(block,domain):
 if domain[0]=='reject':assert block[0]==64;return dict(status=64)
 assert block[0]==0,block[0]
 if domain[0]=='pool':
  _,c,meta,bindings=domain;actual=pool.manual.decoded(block,c,L,bindings) if 'actions' in c else pool.decoded(block,meta,c,bindings);native=pool.manual.native(c,L) if 'actions' in c else pool.observe(c)
  assert all(actual[k]==native[k] for k in native if k!='scope'),c['name'];return native
 _,c,bindings=domain;base=L['WORLD_ACTOR_STATE_BASE'];query=L['WORLD_ACTOR_QUERY_BASE'];actual=dict(count=block[base],queries=[list(block[query+i*8:query+(i+1)*8]) for i in range(len(c['queries']))],registry=[list(block[base+8+i*8:base+8+(i+1)*8]) for i in range(len(bindings))]);native=actor.native(c);assert actual==native,c['name'];return native

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='cuda');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--from-metal',action='store_true');args=ap.parse_args()
 entries,data=prepare();iw=L['WORLD_ACTOR_POOL_INPUT_WORDS']*4;ow=L['WORLD_ACTOR_POOL_OUTPUT_WORDS']*4
 if args.from_metal:
  r=json.loads((ROOT/'research/portable-world-actor-pools-metal.json').read_text());p=Path(r['captured']);original=(p/'input.bin').read_bytes();before=(p/'readback.bin').read_bytes();indexes=[*range(43),*range(43,77)];raw=b''.join(before[i*ow:(i+1)*ow] for i in indexes)
  assert all(data[4+j*iw:4+(j+1)*iw]==original[4+i*iw:4+(i+1)*iw] for j,i in enumerate(indexes));evidence=r['evidence']
  golden=dict(source_sha256=evidence['source_sha256'],input_sha256=sha(data),output_sha256=sha(raw),entries=[])
 else:
  golden=json.loads(GOLDEN.read_text());assert golden['source_sha256']==source_hashes(pool.SOURCE) and golden['input_sha256']==sha(data)
  for i,(name,w,_) in enumerate(entries):assert golden['entries'][i]['name']==name and golden['entries'][i]['input_sha256']==sha(data[4+i*iw:4+(i+1)*iw])
  if args.cpu_only:
   calls=dict(build=0,execute=0)
   def forbidden(name):
    def stop(*a,**kw):calls[name]+=1;raise AssertionError('GPU forbidden in CPU preflight')
    return stop
   import portable_backend
   with patch.object(portable_backend,'build',forbidden('build')),patch.object(portable_backend,'execute',forbidden('execute')),patch.object(pool,'execute',forbidden('execute')),patch.object(actor,'execute',forbidden('execute')):
    again,repacked=prepare();assert repacked==data
    for i,(_,_,domain) in enumerate(again):
     if domain[0]=='reject':continue
     if domain[0]=='pool':c=domain[1];native=pool.manual.native(c,L) if 'actions' in c else pool.observe(c)
     else:native=actor.native(domain[1])
     assert cross.digest(native)==golden['entries'][i]['native_sha256']
   out=dict(passed=True,input_count=77,input_sha256=sha(data),source_sha256=source_hashes(pool.SOURCE),native_oracles=36,gpu_calls=calls)
   (ROOT/'research/portable-world-actor-pools-short-cpu.json').write_text(json.dumps(out,indent=2)+'\n');print('CPU77 literal input +36 native oracles;GPU build/execute0');return
  folder=ROOT/'research/portable-build'/'world-actor-pools-cuda-short';folder.mkdir(parents=True,exist_ok=False);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(pool.SOURCE,'portableEvents',data,L['WORLD_ACTOR_POOL_INPUT_WORDS'],L['WORLD_ACTOR_POOL_OUTPUT_WORDS'],args.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(name,w,domain) in enumerate(entries):
  sem=semantic(values[i*ow//4:(i+1)*ow//4],domain);item=dict(name=name,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(raw[i*ow:(i+1)*ow]),native_sha256=cross.digest(sem));results.append(item)
 if args.from_metal:
  golden['entries']=results;golden['generated_normalized']={b:cross.normalized((ROOT/'research/portable-build'/('world_actor_pool_entry.'+ext)).read_bytes()) for b,ext in [('cuda','cu'),('metal','metal')]};GOLDEN.write_text(json.dumps(golden,indent=2)+'\n');print('77 CUDA comparison inputs derived byte-exactly from saved Metal285;GPU calls0');return
 generated={b:cross.normalized((ROOT/'research/portable-build'/('world_actor_pool_entry.'+ext)).read_bytes()) for b,ext in [('cuda','cu'),('metal','metal')]}
 answer=dict(passed=results==golden['entries'] and sha(raw)==golden['output_sha256'] and generated==golden['generated_normalized'],input_count=77,input_sha256=sha(data),output_sha256=sha(raw),entries=results,generated_normalized=generated,evidence=evidence,normal4682_reexecutions=0,old208_reexecutions=0,full_character_verified=0,canonical_world_admission=False)
 (ROOT/'research/portable-world-actor-pools-short-summary.json').write_text(json.dumps(answer,indent=2)+'\n');assert answer['passed'];print('CUDA/Metal77 exact input/output and36 native oracles passed')
if __name__=='__main__':main()
