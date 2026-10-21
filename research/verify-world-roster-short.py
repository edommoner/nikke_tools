"""One bounded CUDA run; Metal golden is projected from saved readback only."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_backend import source_hashes,execute
from portable_runtime import decode

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('world_roster_suite',ROOT/'research/verify-world-roster.py');cross=module('world_roster_digest',ROOT/'research/summarize-portable-cross-gpu.py')
GOLDEN=ROOT/'research/portable-world-roster-short-expected.json'
def sha(x):return hashlib.sha256(x).hexdigest()
def prepare():
 cases=suite.prepare();entries=[('native/'+c['name'],w,(c,p,m)) for c,p,w,m in cases]+[('reject/'+name,w,None) for name,w in suite.negative_inputs(cases)]
 p=array.array('I',[len(entries)])
 for name,w,domain in entries:p.extend(w)
 if sys.byteorder!='little':p.byteswap()
 return entries,p.tobytes()
def main():
 a=argparse.ArgumentParser();a.add_argument('--from-metal',action='store_true');a.add_argument('--cpu-only',action='store_true');a.add_argument('--backend',default='cuda',choices=('cuda','metal'));o=a.parse_args();entries,data=prepare();iw=suite.INPUT_WORDS*4;ow=suite.OUTPUT_WORDS*4
 def native_hash(domain):return cross.digest(suite.reference.native_reference(domain[0]['body'])) if domain else cross.digest(dict(status=64))
 generated=lambda:{b:cross.normalized((ROOT/'research/portable-build'/('world_roster_entry.'+suffix)).read_bytes()) for b,suffix in [('cuda','cu'),('metal','metal')]}
 if o.from_metal:
  r=json.loads((ROOT/'research/portable-world-roster-metal.json').read_text());folder=Path(r['captured']);assert r['passed'] and (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();golden=dict(input_sha256=sha(data),output_sha256=sha(raw),source_sha256=r['evidence']['source_sha256']);assert golden['source_sha256']==source_hashes(suite.SOURCE)
 else:
  golden=json.loads(GOLDEN.read_text());assert golden['input_sha256']==sha(data) and golden['source_sha256']==source_hashes(suite.SOURCE)
  if o.cpu_only:
   import portable_backend
   def stop(*a,**k):raise AssertionError('GPU forbidden in CPU preflight')
   with patch.object(portable_backend,'build',stop),patch.object(portable_backend,'execute',stop),patch.object(suite,'execute',stop):
    for i,(name,w,domain) in enumerate(entries):assert golden['entries'][i]['native_sha256']==native_hash(domain)
   report=dict(passed=True,input_count=10,native_oracles=6,input_sha256=sha(data),source_sha256=source_hashes(suite.SOURCE),gpu_calls=0)
   (ROOT/'research/portable-world-roster-short-cpu.json').write_text(json.dumps(report,indent=2)+'\n');print('CPU10 inputs/native6 exact;GPU0');return
  folder=ROOT/'research/portable-build/world-roster-cuda-short';folder.mkdir(parents=True,exist_ok=False);(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(suite.SOURCE,'portableEvents',data,suite.INPUT_WORDS,suite.OUTPUT_WORDS,o.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 results=[]
 for i,(name,w,domain) in enumerate(entries):
  part=raw[i*ow:(i+1)*ow];block=array.array('I');block.frombytes(part)
  if sys.byteorder!='little':block.byteswap()
  if domain:
   c,p,m=domain;actual=decode(block[:159744],m);native=suite.reference.native_reference(c['body']);assert block[0]==0 and not suite.reference.compare_native_result(actual,p,native,program=(w,m)),name
  else:assert block[0]==64,name
  results.append(dict(name=name,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(part),native_sha256=native_hash(domain)))
 if o.from_metal:
  golden.update(entries=results,generated_normalized=generated());GOLDEN.write_text(json.dumps(golden,indent=2)+'\n');print('Saved Metal10 input/output/native6 projected;GPU0');return
 report=dict(passed=results==golden['entries'] and sha(raw)==golden['output_sha256'] and generated()==golden['generated_normalized'],input_count=10,native_oracles=6,input_sha256=sha(data),output_sha256=sha(raw),entries=results,generated_normalized=generated(),evidence=e,normal4682_reexecutions=0,previous_world1063_reexecutions=0,previous_reload65_reexecutions=0,unchanged_gpu_retries=0,canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-roster-short-summary.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'];print('CUDA/Metal10 full output/input/native6/generated exact')
if __name__=='__main__':main()
