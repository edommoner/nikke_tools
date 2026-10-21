"""Shared formula witnesses; reuse frozen identical shader/input readbacks on Mac."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
import world_skill_formula_cases as cases
suite=cases.suite;physical=suite.physical;SOURCE=suite.SOURCE;inspect_native=suite.inspect_native;skill_trace=suite.skill_trace
def fixtures():return cases.fixtures()
def prepare():
 rows=fixtures();return rows,[suite.compile_case(c) for c in rows],[]
def compare(block,case,meta,bindings):
 native,trace=inspect_native(case);actual=physical.decoded(block,meta,case,bindings)
 assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
 assert skill_trace(block)==trace and not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]),case['name']
 return native,trace
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');a=ap.parse_args()
 rows,programs,_=prepare();assert len(rows)==8
 native=[inspect_native(c) for c in rows]
 if a.cpu_only:print('Native formula8;GPU0');return
 old=json.loads((ROOT/'research/portable-world-skill-metal.json').read_text());seal=json.loads((ROOT/'research/portable-world-skill-validation.json').read_text());folder=Path(old['captured']);before=(folder/'input.bin').read_bytes();prior=(folder/'readback.bin').read_bytes();iw=97464*4;ow=524288*4
 assert old['passed'] and seal['passed'] and seal['metal_inputs']==833 and int.from_bytes(before[:4],'little')==833 and len(before)==4+833*iw and len(prior)==833*ow
 assert sha(before)==seal['input_sha256']==old['evidence']['input_sha256'] and sha(prior)==seal['output_sha256']==old['evidence']['output_sha256']
 assert source_hashes(SOURCE)==old['evidence']['source_sha256'] and all(c['passed'] for c in old['cases']+old['rejected_cases']+old['preserved783'])
 # Same shader and same full input words permit saved readback reuse. Any
 # changed old input must appear in the actual new GPU batch, without masking.
 base_rows,base_programs,bad=suite.prepare();assert len(base_rows)==40 and len(bad)==10
 same=[];changed=[]
 for i,(case,(w,meta,bindings)) in enumerate(zip(base_rows,base_programs)):
  encoded=struct.pack('<'+'I'*len(w),*w);old_input=before[4+i*iw:4+(i+1)*iw]
  if encoded==old_input:
   block=array.array('I');block.frombytes(prior[i*ow:(i+1)*ow])
   if sys.byteorder!='little':block.byteswap()
   n,t=compare(block,case,meta,bindings);assert json.loads(json.dumps(n))==old['cases'][i]['native'] and t==old['cases'][i]['native_skill_trace'];same.append(case['name'])
  else:
   assert case['name']=='direct-family-auto_damage'
   previous=list(struct.unpack('<'+'I'*97464,old_input));row=next(j for j,e in enumerate(case['effects']) if e.get('type')=='damage');at=L['DAMAGE_DEFINITION_BASE']+row*8+3
   assert previous[at]==1 and w[at]==0 and previous[:at]+previous[at+1:]==w[:at]+w[at+1:]
   assert any(encoded==struct.pack('<'+'I'*len(p[0]),*p[0]) for p in programs);changed.append(case['name'])
 for i,(_,w) in enumerate(bad):assert struct.pack('<'+'I'*len(w),*w)==before[4+(40+i)*iw:4+(41+i)*iw]
 assert len(same)==39 and changed==['direct-family-auto_damage']
 packed=array.array('I',[8])
 for w,_,_ in programs:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();path=ROOT/'research/portable-build'/('world-skill-formula-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));path.mkdir();(path/'input.bin').write_bytes(data)
 try:raw,evidence=execute(SOURCE,'portableEvents',data,97464,524288,a.backend)
 except Exception as error:(path/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
 (path/'readback.bin').write_bytes(raw);(path/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 checks=[]
 for i,(c,(_,meta,bindings),(n,t)) in enumerate(zip(rows,programs,native)):
  block=values[i*524288:(i+1)*524288]
  try:actual,trace=compare(block,c,meta,bindings);passed=True;error=None
  except Exception as e:actual=physical.decoded(block,meta,c,bindings);trace=skill_trace(block);passed=False;error=repr(e)
  checks.append(dict(name=c['name'],passed=passed,status=block[0],native=n,native_skill_trace=t,actual=actual,skill_trace=trace,error=error))
 r=dict(passed=all(c['passed'] for c in checks),cases=checks,captured=str(path),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),shader_source_unchanged=True,saved_input_sha256=sha(before),saved_output_sha256=sha(prior),same_full_native_inputs_reused=same,changed_input_verified_on_gpu=changed,old10_invalid_inputs_exact=True,old783_saved_sealed_outputs_retained=True,old833_reexecutions=0,actual_gpu_inputs=8,unchanged_gpu_retries=0,cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-skill-formula-{a.backend}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');assert r['passed'],[c['name'] for c in checks if not c['passed']];print('Formula8 full native+trace;39 native/10 invalid/old783 saved exact;GPU old833 reruns0')
if __name__=='__main__':main()
