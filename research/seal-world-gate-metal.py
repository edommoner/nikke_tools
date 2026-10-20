"""Read-only CPU audit of the frozen100-input Metal gate checkpoint."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 report=load(ROOT/'research/portable-world-overlay-gates-metal.json');assert report['passed']
 assert [len(report[k]) for k in ('cases','rejected_cases','preserved_world49')]==[35,16,49]
 evidence=report['evidence'];folder=Path(report['captured']);composition=evidence['execution_composition']
 assert composition['changed_indices']==[28,29]
 source=subprocess.check_output(['git','rev-parse','fe684ee'],cwd=ROOT,text=True).strip()
 for name,sha in evidence['source_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',source+':'+name],cwd=ROOT)).hexdigest()==sha,name
 parent=Path(composition['prior_capture']);prior=load(parent/'evidence.json');fresh=load(folder/'dispatch-evidence.json')
 for e in (evidence,prior,fresh):assert e['backend']=='metal' and e['gpu_execution_verified'] and e['source_sha256']==evidence['source_sha256'] and e['generated_sha256']==evidence['generated_sha256']
 for where,e,inp,out in [(folder,evidence,'input.bin','readback.bin'),(parent,prior,'input.bin','readback.bin'),(folder,fresh,'dispatch-input.bin','dispatch-readback.bin')]:assert digest(where/inp)==e['input_sha256'] and digest(where/out)==e['output_sha256']
 data=(folder/'input.bin').read_bytes();raw=(folder/'readback.bin').read_bytes();old=(parent/'input.bin').read_bytes();oldraw=(parent/'readback.bin').read_bytes();new=(folder/'dispatch-input.bin').read_bytes();newraw=(folder/'dispatch-readback.bin').read_bytes();iw=89376*4;ow=225280*4
 assert int.from_bytes(data[:4],'little')==100 and int.from_bytes(new[:4],'little')==2 and len(raw)==100*ow and len(newraw)==2*ow
 for i in range(100):
  if i in composition['changed_indices']:
   j=composition['changed_indices'].index(i);assert data[4+i*iw:4+(i+1)*iw]==new[4+j*iw:4+(j+1)*iw] and raw[i*ow:(i+1)*ow]==newraw[j*ow:(j+1)*ow]
  else:assert data[4+i*iw:4+(i+1)*iw]==old[4+i*iw:4+(i+1)*iw] and raw[i*ow:(i+1)*ow]==oldraw[i*ow:(i+1)*ow]
 for case in report['cases']:
  assert case['passed'] and case['actual']['status']==0
  for key in ('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history'):assert case['actual'][key]==case['native'][key],(case['name'],key)
  if 'world_nodes' in case['native']:
   for key in ('gauge','world_nodes'):assert case['actual'][key]==case['native'][key],(case['name'],key)
 assert all(r['passed'] and r['status']==64 for r in report['rejected_cases'])
 golden=load(ROOT/'research/portable-world-suite-golden.json')
 for row,expected in zip(report['preserved_world49'],golden['cases']):assert row['passed'] and row['name']==expected['name'] and row['output_sha256']==expected['output_sha256']
 print('Frozen Metal100:35 exact native,16 rejects,49 old full outputs;98 preserved+2 actual corrected GPU cases')
if __name__=='__main__':main()
