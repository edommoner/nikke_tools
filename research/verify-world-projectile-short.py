"""One short shared63 CUDA dispatch; golden projects saved Metal blocks, GPU0."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
suite=module('projectile_short_suite','research/verify-world-projectile.py');cross=module('projectile_short_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-projectile-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 rows,programs,bad=suite.prepare();entries=[('native/'+c['name'],w,(c,m,b)) for c,(w,m,b) in zip(rows,programs)];entries.extend(('reject/'+n,w,None) for n,w in bad);assert len(entries)==63
 packed=array.array('I',[len(entries)])
 for _,w,_ in entries:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return entries,packed.tobytes()
def compare(block,domain):
 c,m,b=domain;native,trace=suite.inspect_native(c);actual=suite.decoded(block,m,c,b);assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope'),c['name'];assert suite.reload.charge.team.skill_trace(block,m)==trace;assert not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]);return dict(battle=native,skill_trace=trace)
def development_entries():
 from portable_readiness_cases import fixtures
 rows=fixtures();entries=[]
 for c in rows:
  w,m,b=suite.compile_case(c);entries.append(('development/'+c['name'],w,(c,m,b)))
 seed=entries[0][1]
 from portable_specs import FIELDS as F
 for name,offset,value in [('lost-hp-invalid-stat',F['STAT'],0),('lost-hp-invalid-kind',F['KIND'],4)]:
  w=list(seed);w[L['DEFINITION_BASE']+offset]=value;entries.append(('reject/'+name,w,None))
 direct=entries[4][1]
 for name in ('direct-health-unknown-flag','direct-health-non-health'):
  w=list(direct)
  if name.endswith('unknown-flag'):w[L['DEFINITION_BASE']+F['FLAGS']] |= 512
  else:w[L['HEALTH_DEFINITION_BASE']+1]=0
  entries.append(('reject/'+name,w,None))
 return entries

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('cuda','metal'),default='cuda');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--from-metal',action='store_true');a=ap.parse_args();entries,data=prepare();iw=suite.INPUT*4;ow=suite.OUTPUT*4
 if a.from_metal:
  r=json.loads((ROOT/'research/portable-world-projectile-metal.json').read_text());p=Path(r['captured']);assert r['passed'] and (p/'input.bin').read_bytes()==data;raw=(p/'readback.bin').read_bytes();assert sha(data)==r['evidence']['input_sha256'] and sha(raw)==r['evidence']['output_sha256'];assert r['evidence']['source_sha256']==source_hashes(suite.SOURCE);golden=dict(input_sha256=sha(data),output_sha256=sha(raw),source_sha256=r['evidence']['source_sha256'])
 else:
  golden=json.loads(GOLDEN.read_text());assert golden['input_sha256']==sha(data) and golden['source_sha256']==source_hashes(suite.SOURCE)
  for i,(n,w,_) in enumerate(entries):assert golden['entries'][i]['name']==n and golden['entries'][i]['input_sha256']==sha(data[4+i*iw:4+(i+1)*iw])
  if a.cpu_only:
   import portable_backend
   calls=dict(build=0,execute=0)
   def stop(name):
    def forbidden(*a,**k):calls[name]+=1;raise AssertionError('GPU forbidden in packing/native preflight')
    return forbidden
   with patch.object(portable_backend,'build',stop('build')),patch.object(portable_backend,'execute',stop('execute')),patch.object(suite,'execute',stop('execute')):
    again,repacked=prepare();assert data==repacked
    for i,(n,w,domain) in enumerate(again):
     native=dict(status=64) if domain is None else dict(zip(('battle','skill_trace'),suite.inspect_native(domain[0])))
     assert cross.digest(native)==golden['entries'][i]['native_sha256']
   report=dict(passed=True,input_count=63,native_oracles=52,input_sha256=sha(data),source_sha256=source_hashes(suite.SOURCE),gpu_calls=calls)
   (ROOT/'research/portable-world-projectile-short-cpu.json').write_text(json.dumps(report,indent=2)+'\n');print('CPU63 inputs/native52 exact;GPU0');return
  folder=ROOT/'research/portable-build/world-projectile-cuda-short';folder.mkdir(parents=True,exist_ok=False);(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(suite.SOURCE,'portableEvents',data,suite.INPUT,suite.OUTPUT,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw);values.byteswap() if sys.byteorder!='little' else None;results=[]
 for i,(name,w,domain) in enumerate(entries):
  block=values[i*suite.OUTPUT:(i+1)*suite.OUTPUT]
  if domain is None:assert block[0]==64;native=dict(status=64)
  else:native=compare(block,domain)
  results.append(dict(name=name,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(raw[i*ow:(i+1)*ow]),native_sha256=cross.digest(native)))
 generated={b:cross.normalized((ROOT/'research/portable-build'/('world_projectile_entry.'+suffix)).read_bytes()) for b,suffix in [('cuda','cu'),('metal','metal')]}
 if a.from_metal:
  assert generated==r['evidence']['generated_normalized'];golden.update(entries=results,generated_normalized=generated);GOLDEN.write_text(json.dumps(golden,indent=2)+'\n');print('Saved Metal63/native52 projected;GPU0');return
 result=dict(passed=results==golden['entries'] and sha(raw)==golden['output_sha256'] and generated==golden['generated_normalized'],input_count=63,native_oracles=52,input_sha256=sha(data),output_sha256=sha(raw),entries=results,generated_normalized=generated,evidence=e,normal4682_reexecutions=0,old1063_reexecutions=0,old_reload65_reexecutions=0,old_real22_reexecutions=0,unchanged_gpu_retries=0,full_character_verified=0,canonical_world_admission=False,full_goal_complete=False)
 (ROOT/'research/portable-world-projectile-short-summary.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'];print('CUDA/Metal63 full input/output/native52/generated exact')
if __name__=='__main__':main()
