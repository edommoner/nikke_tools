"""Real complete squads, shared CUDA/Metal input and unmodified CPU oracle."""
import argparse,array,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker
from detail_coverage import body_for
from portable_world_roster_input import compile_world_battle,SOURCE,INPUT_WORDS,OUTPUT_WORDS
from portable_runtime import decode
from portable_backend import execute,source_hashes
s=importlib.util.spec_from_file_location('real_squad_oracle',ROOT/'scripts/verify-portable-real-battle.py');reference=importlib.util.module_from_spec(s);s.loader.exec_module(reference)

def prepare():
 cases=[]
 for duration,grown,last in [(3,False,'드레이크'),(30,False,'드레이크'),(180,False,'드레이크'),(180,True,'드레이크'),(30,False,'브리드'),(30,True,'브리드')]:
  names=['미란다','도라','N102','메어리',last]
  b=dict(body_for(names,duration,grown),burst_gauge_mode='accumulate');p=engine_worker.evaluate(dict(b,_portable_static_inputs=True));w,m=compile_world_battle(p)
  cases.append((dict(name=f'{last}-{duration}-{grown}',body=b),p,w,m))
 return cases

def negative_inputs(cases):
 from portable_specs import LIMITS as L,FIELDS as F
 changes=[('old-reload-abi',0,L['WORLD_RELOAD_ABI']),('old-reload-mode',L['TARGET_COUNTER_INPUT_BASE']+6,22),('unknown-kind',L['DEFINITION_BASE']+F['KIND'],99),('reload-reserved',L['WORLD_RELOAD_INPUT_BASE']+3,1)]
 bad=[]
 for name,at,value in changes:
  w=list(cases[0][2]);w[at]=value;bad.append((name,w))
 return bad

def run(backend='metal',replay=None,cpu_only=False):
 cases=prepare();bad=negative_inputs(cases);packed=array.array('I',[len(cases)+len(bad)])
 for _,_,w,_ in cases:packed.extend(w)
 for _,w in bad:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();hashes=source_hashes(SOURCE)
 if cpu_only:
  native=[reference.native_reference(c['body']) for c,p,w,m in cases]
  print('Real squads',len(cases),'native',len(native),'GPU0');return
 if replay:
  folder=Path(replay);assert (folder/'input.bin').read_bytes()==data
  raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==hashes
 else:
  folder=ROOT/'research/portable-build'/('world-roster-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,INPUT_WORDS,OUTPUT_WORDS,backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=hashes),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 assert len(raw)==(len(cases)+len(bad))*OUTPUT_WORDS*4
 rows=[]
 for i,(c,p,w,m) in enumerate(cases):
  block=array.array('I');block.frombytes(raw[i*OUTPUT_WORDS*4:(i+1)*OUTPUT_WORDS*4])
  if sys.byteorder!='little':block.byteswap()
  row=dict(**c,status=block[0],passed=False,prepared_effects=len(p['effects']),bound_effects=len(m['effects']),input_sha256=hashlib.sha256(data[4+i*INPUT_WORDS*4:4+(i+1)*INPUT_WORDS*4]).hexdigest(),output_sha256=hashlib.sha256(raw[i*OUTPUT_WORDS*4:(i+1)*OUTPUT_WORDS*4]).hexdigest())
  try:
   actual=decode(block[:159744],m);native=reference.native_reference(c['body']);diff=reference.compare_native_result(actual,p,native,program=(w,m));row.update(actual=actual,native=native,differences=diff,passed=block[0]==0 and not diff)
  except (AssertionError,ValueError,KeyError,IndexError) as error:row['error']=repr(error)
  from portable_specs import LIMITS as L
  row['diagnostic_history'] = {kind: dict(retained=block[L['WORLD_'+kind.upper()+'_HEAD_BASE']+1],omitted=block[L['WORLD_'+kind.upper()+'_HEAD_BASE']+offset]) for kind,offset in [('team',5),('fraction',3)]}
  rows.append(row)
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(cases)+i)*OUTPUT_WORDS*4:(len(cases)+i)*OUTPUT_WORDS*4+4],'little')) for i,(name,_) in enumerate(bad)]
 for r in rejected:r['passed']=r['status']==64
 report=dict(passed=all(x['passed'] for x in rows+rejected),cases=rows,rejected_cases=rejected,evidence=e,captured=str(folder),input_sha256=hashlib.sha256(data).hexdigest(),readback_sha256=hashlib.sha256(raw).hexdigest(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False,cpu_trace_used_as_gpu_input=False,unchanged_gpu_retries=0,scope='Six complete real five-member simple-boss squads at 3/30/180 seconds including real growth/skill levels; no full catalog/variant certification')
 (ROOT/f'research/portable-world-roster-{backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print([(x['name'],x['status'],x['passed'],len(x.get('differences',[])),x.get('error')) for x in rows]);assert report['passed']
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--backend',choices=('metal','cuda'),default='metal');a.add_argument('--replay');a.add_argument('--cpu-only',action='store_true');o=a.parse_args();run(o.backend,o.replay,o.cpu_only)
