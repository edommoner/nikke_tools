"""Read-only proof audit of frozen146 Metal inputs,outputs and native dictionaries."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FROZEN='4057d19'
def load(p):return json.loads(p.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 report=load(ROOT/'research/portable-world-overlay-cleanse-metal.json');expected=load(ROOT/'research/portable-world-cleanse-expected.json');comparison=expected['comparison'];e=report['evidence']
 folder=Path(report['captured']);data=(folder/'input.bin').read_bytes();raw=(folder/'readback.bin').read_bytes();iw=89376*4;ow=225280*4
 assert report['passed'] and expected['passed'] and len(report['cases'])==70 and len(report['rejected_cases'])==27 and len(report['preserved_world49'])==49
 assert int.from_bytes(data[:4],'little')==146 and len(data)==4+146*iw and len(raw)==146*ow
 assert sha(data)==e['input_sha256']==comparison['input_sha256'] and sha(raw)==e['output_sha256']==comparison['output_sha256']
 for path,value in e['source_sha256'].items():
  assert sha(subprocess.check_output(['git','show',FROZEN+':'+path],cwd=ROOT))==value
 rows=report['cases']+report['rejected_cases']+report['preserved_world49']
 for i,(row,c) in enumerate(zip(rows,comparison['cases'])):
  assert row['passed'] and row['name']==c['name']
  assert sha(data[4+i*iw:4+(i+1)*iw])==c['input_sha256'] and sha(raw[i*ow:(i+1)*ow])==c['output_sha256']
  semantic={k:v for k,v in row.items() if k not in ('input_sha256','output_sha256','expected_sha256')}
  assert sha(json.dumps(semantic,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())==c['semantic_sha256']
 old=load(ROOT/'research/portable-world-overlay-gates-metal.json');oldraw=(Path(old['captured'])/'readback.bin').read_bytes();newmap={r['name']:(i,r) for i,r in enumerate(report['cases'])}
 for i,row in enumerate(old['cases']):
  j,current=newmap[row['name']];assert current['actual']==row['actual'] and current['native']==row['native'];assert raw[j*ow:(j+1)*ow]==oldraw[i*ow:(i+1)*ow]
 finding=load(ROOT/'research/portable-world-cleanse-integer-finding.json');failed=load(Path(finding['captured'])/'first-comparison.json')
 assert not failed['passed'] and len(finding['failed'])==2
 assert all(newmap[row['name']][1]['native']==row['native'] for row in failed['cases'])
 default=load(ROOT/'research/portable-world-cleanse-default-generated-parity.json');assert default['passed'] and default['actual']==default['expected']
 receipt=dict(passed=True,calculation_source=FROZEN,report_sha256=sha((ROOT/'research/portable-world-overlay-cleanse-metal.json').read_bytes()),expected_sha256=sha((ROOT/'research/portable-world-cleanse-expected.json').read_bytes()),input_sha256=sha(data),output_sha256=sha(raw),actual_metal_inputs=146,native_complete_dictionaries=70,raw_rejections=27,old_world_full_outputs=49,old_gate_full_outputs=35,old_native_oracle_changed=False,failed_initial_run_retained=True,cpu_audit_gpu_executions=0,normal_generated_unchanged=True,full_character_verified=0,full_goal_complete=False,canonical_world_admission=False,normal_ui='CPU')
 (ROOT/'research/portable-world-cleanse-validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Frozen Metal146 audit passed;old35 complete output bytes preserved')
if __name__=='__main__':main()
