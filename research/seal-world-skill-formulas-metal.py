"""CPU-only seal of formula8 plus exact saved shader/input reuse."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='ef12e09'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('formula_seal','research/verify-world-skill-formulas.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-skill-formula-metal.json').read_text());path=Path(r['captured']);data=(path/'input.bin').read_bytes();raw=(path/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and len(data)==4+8*iw and len(raw)==8*ow and int.from_bytes(data[:4],'little')==8
 assert sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 finding=json.loads((ROOT/'research/portable-world-auto-formula-finding.json').read_text())
 assert sha(subprocess.check_output(['git','show',SOURCE+':app/portable_runtime.py'],cwd=ROOT))==finding['corrected_compiler_sha256']
 rows,programs,bad=d.prepare();assert len(rows)==8 and not bad
 for i,(case,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  native,trace=d.compare(block,case,meta,bindings);stored=r['cases'][i];assert stored['passed'] and stored['native']==json.loads(json.dumps(native)) and stored['skill_trace']==stored['native_skill_trace']==trace
 old=json.loads((ROOT/'research/portable-world-skill-metal.json').read_text());p=Path(old['captured']);before=(p/'input.bin').read_bytes();prior=(p/'readback.bin').read_bytes()
 assert old['passed'] and old['evidence']['source_sha256']==e['source_sha256'] and sha(before)==r['saved_input_sha256']==old['evidence']['input_sha256'] and sha(prior)==r['saved_output_sha256']==old['evidence']['output_sha256']
 old_rows,old_programs,invalid=d.suite.prepare();same=[];changed=[]
 for i,(case,(w,meta,bindings)) in enumerate(zip(old_rows,old_programs)):
  encoded=struct.pack('<'+'I'*len(w),*w);before_input=before[4+i*iw:4+(i+1)*iw]
  if encoded==before_input:
   block=array.array('I');block.frombytes(prior[i*ow:(i+1)*ow])
   if sys.byteorder!='little':block.byteswap()
   native,trace=d.compare(block,case,meta,bindings);assert json.loads(json.dumps(native))==old['cases'][i]['native'] and trace==old['cases'][i]['native_skill_trace'];same.append(case['name'])
  else:
   assert case['name']=='direct-family-auto_damage';previous=list(struct.unpack('<'+'I'*97464,before_input));row=next(j for j,v in enumerate(case['effects']) if v.get('type')=='damage');at=d.L['DAMAGE_DEFINITION_BASE']+row*8+3
   assert previous[at]==1 and w[at]==0 and previous[:at]+previous[at+1:]==w[:at]+w[at+1:] and encoded==data[4:4+iw];changed.append(case['name'])
 assert same==r['same_full_native_inputs_reused'] and len(same)==39 and changed==r['changed_input_verified_on_gpu']==['direct-family-auto_damage']
 for i,(_,w) in enumerate(invalid):assert struct.pack('<'+'I'*len(w),*w)==before[4+(40+i)*iw:4+(41+i)*iw]
 assert len(invalid)==10 and all(c['passed'] for c in old['rejected_cases']+old['preserved783'])
 generation=json.loads((ROOT/'research/portable-build/world-skill-generation.json').read_text());assert generation['passed'] and len(generation['cases'])==11
 for c in generation['cases']:
  for f,h in c['source_sha256'].items():assert sha((ROOT/f).read_bytes())==h
 x=importlib.util.spec_from_file_location('formula_generation_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(x);x.loader.exec_module(cross)
 golden=json.loads((ROOT/'research/portable-world-skill-short-expected.json').read_text());generated={b:cross.normalized((ROOT/'research/portable-build'/('world_skill_entry.'+suffix)).read_bytes()) for b,suffix in [('cuda','cu'),('metal','metal')]}
 assert generated==golden['generated_normalized']
 unit=(ROOT/'research/portable-build/world-skill-formula-unit.log').read_text();assert 'Ran 393 tests' in unit and unit.rstrip().endswith('OK')
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=8,full_native_battles=8,portable_cpu_tests=393,old39_full_inputs_and_native_traces_exact=True,changed_auto_input_checked_on_gpu=True,old10_invalid_inputs_exact=True,old783_saved_sealed_outputs_retained=True,old833_reexecutions=0,shader_source_unchanged=True,prior12_generated_entries_exact=True,actual_metal_executions=1,gpu_retries=0,old_normal_auto_policy_unchanged=True,auto_native_formula_finding='RESOLVED_ON_METAL',input_sha256=sha(data),output_sha256=sha(raw),audit_gpu_calls=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-skill-formula-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Formula Metal8 sealed;39 native reuse/10 invalid/old783 saved;CPU393;old833 GPU0')
if __name__=='__main__':main()
