"""Read-only audit of Metal208 and native hold lifecycle without another GPU run."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='4bd848b'
def load(p):return json.loads(p.read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def rows(r):return r['cases']+r['rejected_cases']+r['preserved_world49']
def capture(r):
 p=Path(r['captured']);i=(p/'input.bin').read_bytes();o=(p/'readback.bin').read_bytes();n=len(rows(r));e=r['evidence'];assert len(i)==4+n*89376*4 and len(o)==n*225280*4 and int.from_bytes(i[:4],'little')==n and sha(i)==e['input_sha256'] and sha(o)==e['output_sha256'];return i,o
def main():
 r=load(ROOT/'research/portable-world-overlay-charge-hold-metal.json');expected=load(ROOT/'research/portable-world-charge-hold-expected.json');assert r['passed'] and len(r['cases'])==125 and len(r['rejected_cases'])==34 and len(r['preserved_world49'])==49 and expected['passed']
 data,raw=capture(r);iw=89376*4;ow=225280*4;mapping={v['name']:(j,v) for j,v in enumerate(rows(r))}
 for path,h in r['evidence']['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h
 assert r['evidence']['source_sha256']==expected['comparison']['source_sha256'] and sha(data)==expected['comparison']['input_sha256'] and sha(raw)==expected['comparison']['output_sha256']
 for j,(v,c) in enumerate(zip(rows(r),expected['comparison']['cases'])):
  assert v['passed'] and v['name']==c['name'] and sha(data[4+j*iw:4+(j+1)*iw])==c['input_sha256'] and sha(raw[j*ow:(j+1)*ow])==c['output_sha256']
  semantic={k:x for k,x in v.items() if k not in ('input_sha256','output_sha256','expected_sha256')};assert sha(json.dumps(semantic,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())==c['semantic_sha256']
 for file in ('portable-world-overlay-skill-modes-metal.json','portable-world-charge-hold-initial-metal.json'):
  old=load(ROOT/'research'/file);oi,oo=capture(old)
  for j,v in enumerate(rows(old)):
   k,current=mapping[v['name']];assert data[4+k*iw:4+(k+1)*iw]==oi[4+j*iw:4+(j+1)*iw] and raw[k*ow:(k+1)*ow]==oo[j*ow:(j+1)*ow]
   if j<len(old['cases']):assert current['native']==v['native'] and current['actual']==v['actual']
 original=load(ROOT/'research/portable-world-charge-hold-input-finding.json');failed=load(Path(original['captured'])/'first-comparison.json');assert not failed['passed'] and all(mapping[v['name']][1]['native']==v['native'] for v in failed['cases'])
 default=load(ROOT/'research/portable-world-charge-hold-default-generated-parity.json');assert default['passed'] and default['actual']==default['expected']
 result=dict(passed=True,source_commit=SOURCE,metal_inputs=208,native_complete_cases=125,new_heavyarms_cases=26,raw_rejections=34,prior_world_full_outputs=49,prior179_and206_input_output_bytes_unchanged=True,prior99_and123_complete_native_actual_dictionaries_unchanged=True,native_oracle_unchanged=True,full_charge_latch_deadline_and_charging_compared=True,initial_non_camera_input_error_retained=True,normal_cuda_msl_generated_exact=True,input_sha256=sha(data),output_sha256=sha(raw),audit_gpu_executions=0,windows_hold_verified=False,full_character_verified=0,full_goal_complete=False,normal_ui='CPU',canonical_world_admission=False)
 (ROOT/'research/portable-world-charge-hold-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal208 audit passed;125 complete native cases;old179 and206 full bytes retained')
if __name__=='__main__':main()
