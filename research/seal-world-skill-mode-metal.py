"""CPU audit of fixed Metal179,including byte preservation of prior CUDA146 set."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='c953d3b'
def load(path):return json.loads(path.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def rows(r):return r['cases']+r['rejected_cases']+r['preserved_world49']
def capture(r):
 p=Path(r['captured']);i=(p/'input.bin').read_bytes();o=(p/'readback.bin').read_bytes();e=r['evidence'];n=len(rows(r));assert len(i)==4+n*89376*4 and len(o)==n*225280*4 and int.from_bytes(i[:4],'little')==n;assert sha(i)==e['input_sha256'] and sha(o)==e['output_sha256'];return i,o
def main():
 r=load(ROOT/'research/portable-world-overlay-skill-modes-metal.json');old=load(ROOT/'research/portable-world-overlay-cleanse-metal.json');expected=load(ROOT/'research/portable-world-skill-mode-expected.json');finding=load(ROOT/'research/portable-world-skill-mode-finding.json');failed=load(Path(finding['captured'])/'first-comparison.json');iw=89376*4;ow=225280*4
 assert r['passed'] and expected['passed'] and len(r['cases'])==99 and len(r['rejected_cases'])==31 and len(r['preserved_world49'])==49 and not failed['passed']
 data,raw=capture(r);olddata,oldraw=capture(old);failuredata,failureraw=capture(failed)
 for path,h in r['evidence']['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h
 assert r['evidence']['source_sha256']==expected['comparison']['source_sha256'] and sha(data)==expected['comparison']['input_sha256'] and sha(raw)==expected['comparison']['output_sha256']
 mapping={v['name']:(j,v) for j,v in enumerate(rows(r))};failuremap={v['name']:(j,v) for j,v in enumerate(rows(failed))}
 for j,(v,c) in enumerate(zip(rows(r),expected['comparison']['cases'])):
  assert v['passed'] and v['name']==c['name'] and sha(data[4+j*iw:4+(j+1)*iw])==c['input_sha256'] and sha(raw[j*ow:(j+1)*ow])==c['output_sha256']
  semantic={k:x for k,x in v.items() if k not in ('input_sha256','output_sha256','expected_sha256')};assert sha(json.dumps(semantic,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())==c['semantic_sha256']
 for i,v in enumerate(rows(old)):
  j,current=mapping[v['name']];k,_=failuremap[v['name']]
  assert data[4+j*iw:4+(j+1)*iw]==olddata[4+i*iw:4+(i+1)*iw]==failuredata[4+k*iw:4+(k+1)*iw]
  assert raw[j*ow:(j+1)*ow]==oldraw[i*ow:(i+1)*ow]==failureraw[k*ow:(k+1)*ow]
  if i<70:assert current['native']==v['native'] and current['actual']==v['actual']
 assert all(mapping[v['name']][1]['native']==v['native'] for v in failed['cases'])
 default=load(ROOT/'research/portable-world-skill-mode-default-generated-parity.json');assert default['passed'] and default['actual']==default['expected']
 receipt=dict(passed=True,source_commit=SOURCE,metal_inputs=179,native_complete_cases=99,new_skill_mode_cases=29,raw_rejections=31,prior_world_full_outputs=49,prior_cuda146_inputs_and_full_outputs_preserved=True,prior70_native_actual_dictionaries_preserved=True,failed175_raw_retained=True,native_reference_unchanged=True,normal_cuda_msl_generated_unchanged=True,input_sha256=sha(data),output_sha256=sha(raw),expected_sha256=sha((ROOT/'research/portable-world-skill-mode-expected.json').read_bytes()),audit_gpu_executions=0,windows_new_skill_mode_verified=False,full_character_verified=0,full_goal_complete=False,canonical_world_admission=False,normal_ui='CPU')
 (ROOT/'research/portable-world-skill-mode-validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Frozen Metal179 audited;old146 complete input/output bytes retained in both executions')
if __name__=='__main__':main()
