"""Seal saved disjoint Metal blocks and one explicit compiled-identity bridge;GPU0."""
import array,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('sealed_projectile_suite','research/verify-world-projectile.py');real=module('sealed_projectile_real','research/verify-world-projectile-rosters.py')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(name):return json.loads((ROOT/'research'/name).read_text())
def check_origin(report):
 folder=Path(report['captured']);data=(folder/'input.bin').read_bytes();raw=(folder/'readback.bin').read_bytes();e=report['evidence'];assert e['gpu_execution_verified'] and e['backend']=='metal' and e['transport']['device']=='Apple M5' and e['transport']['command_status']=='completed';assert sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256'];return data,raw

def main():
 import portable_backend
 def stop(*a,**k):raise AssertionError('GPU/build forbidden in saved audit')
 with patch.object(portable_backend,'build',stop),patch.object(portable_backend,'execute',stop),patch.object(suite,'execute',stop):
  bridge=read('portable-world-projectile-diagnostic-preservation.json');assert bridge['passed'] and bridge['baseline_commit']=='1421ea2' and bridge['baseline_normalized']==bridge['current_normalized'] and bridge['normalization_extended'] is False and bridge['gpu_calls']==0
  assert bridge['source_sha256']==portable_backend.source_hashes(suite.SOURCE)
  base=read('portable-world-projectile-before-input-fix-metal.json');delta=read('portable-world-projectile-input-fix-metal.json');bd,br=check_origin(base);dd,dr=check_origin(delta);assert base['source_commit'].startswith('1421ea2') and delta['passed'] and delta['statuses']==[0,64]
  for p,h in base['evidence']['source_sha256'].items():assert sha(subprocess.check_output(['git','show','1421ea2:'+p]))==h
  assert delta['evidence']['source_sha256']==bridge['source_sha256']
  rows,programs,bad=suite.prepare();assert len(rows)==52 and len(bad)==11
  iw=suite.INPUT*4;ow=suite.OUTPUT*4;assert len(br)==62*ow and len(dr)==2*ow and int.from_bytes(dd[:4],'little')==2
  packed=array.array('I',[63]);blocks=[];origins=[]
  for i,(w,m,b) in enumerate(programs):
   wb=array.array('I',w).tobytes();packed.extend(w)
   if i==51:assert wb==dd[4:4+iw];block=dr[:ow];origin='input-fix/0'
   else:assert wb==bd[4+i*iw:4+(i+1)*iw];block=br[i*ow:(i+1)*ow];origin='base/'+str(i)
   blocks.append(block);origins.append(origin)
  for i,(name,w) in enumerate(bad):
   wb=array.array('I',w).tobytes();packed.extend(w)
   if i==10:assert wb==dd[4+iw:4+2*iw];block=dr[ow:2*ow];origin='input-fix/1'
   else:assert wb==bd[4+(52+i)*iw:4+(53+i)*iw];block=br[(52+i)*ow:(53+i)*ow];origin='base/'+str(52+i)
   blocks.append(block);origins.append(origin)
  checked=[]
  for c,(w,m,b),raw in zip(rows,programs,blocks):
   words=array.array('I');words.frombytes(raw);actual=suite.decoded(words,m,c,b);native,trace=suite.inspect_native(c);assert words[0]==0 and all(actual[k]==native[k] for k in native if k!='scope');actual_trace=suite.reload.charge.team.skill_trace(words,m);assert actual_trace==trace
   checked.append(dict(name=c['name'],passed=True,status=0,changed=[],actual=actual,native=native,skill_trace=actual_trace,native_skill_trace=trace))
  rejected=[]
  for (name,w),raw in zip(bad,blocks[52:]):assert int.from_bytes(raw[:4],'little')==64;rejected.append(dict(name=name,passed=True,status=64))
  data=packed.tobytes();raw=b''.join(blocks);folder=ROOT/'research/portable-build/world-projectile-sealed-combined'
  folder.mkdir(exist_ok=True)
  for name,content in [('input.bin',data),('readback.bin',raw)]:
   p=folder/name
   if p.exists():assert p.read_bytes()==content
   else:p.write_bytes(content)
  evidence=dict(backend='metal',gpu_execution_verified=True,source_sha256=bridge['source_sha256'],generated_normalized=bridge['current_normalized'],input_sha256=sha(data),output_sha256=sha(raw),aggregation_gpu_calls=0,dispatch_origins=[dict(label='base',captured=base['captured'],evidence=base['evidence']),dict(label='input-fix',captured=delta['captured'],evidence=delta['evidence'])],block_origins=origins,compiled_identity_bridge='portable-world-projectile-diagnostic-preservation.json')
  (folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
  result=dict(passed=True,cases=checked,rejected_cases=rejected,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),sealed_from_saved_blocks=True,aggregation_gpu_calls=0,raw_origin_reports_preserved=True,unchanged_gpu_retries=0,canonical_world_admission=False,full_character_verified=0,normal_ui='CPU',full_goal_complete=False)
  (ROOT/'research/portable-world-projectile-metal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  real_report=read('portable-world-projectile-rosters-metal.json');rd,rr=check_origin(real_report);assert real_report['passed'] and real_report['source_commit'].startswith('1421ea2');plan=real.prepare();expected=array.array('I',[22]);assert len(plan)==22
  for c,p,w,m in plan:expected.extend(w)
  assert rd==expected.tobytes();assert real_report['evidence']['source_sha256']==base['evidence']['source_sha256']
  for i,(c,p,w,m) in enumerate(plan):
   block=array.array('I');block.frombytes(rr[i*ow:(i+1)*ow]);native,shots=real.native_reference(c['body']);actual,events,omitted,diff=real.compare(block,p,(w,m),native,shots);assert block[0]==0 and not diff and native==real_report['cases'][i]['native'] and shots==real_report['cases'][i]['native_physical_shots']
  old_real=read('portable-world-projectile-rosters-initial-metal.json');_,old_rr=check_origin(old_real);kept_real=[]
  for i,c in enumerate(old_real['cases']):
   if c['passed']:assert old_rr[i*ow:(i+1)*ow]==rr[i*ow:(i+1)*ow];kept_real.append(i)
  assert len(kept_real)==16
  preservation=read('portable-world-projectile-old65-input-preservation.json');assert preservation['passed'] and preservation['input_count']==65
  out=dict(passed=True,native_literal_cases=52,raw_rejections=11,real_profiles=11,complete_real_battles=22,real_initial16_full_output_blocks_preserved=True,real_current_inputs_exact=True,production_generated_equal_to_fixed_1421ea2=True,compiled_identity_bridge=bridge,core_input_sha256=sha(data),core_output_sha256=sha(raw),core_actual_dispatches_used=2,aggregation_gpu_calls=0,audit_gpu_calls=0,old65_inputs_exact=True,normalization_extended=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
  (ROOT/'research/portable-world-projectile-validation.json').write_text(json.dumps(out,indent=2)+'\n');print('Saved Metal63/native52 + real22/source/Git/input/trace audited;GPU0')
if __name__=='__main__':main()
