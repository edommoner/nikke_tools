"""Exact compact fingerprints;full reports and raw readbacks stay on each host."""
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import source_hashes
from portable_specs import LIMITS

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def file_sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def comparison(report):
 evidence=report['evidence'];folder=Path(report['captured']);iw=LIMITS['WORLD_OVERLAY_INPUT_WORDS']*4;ow=LIMITS['WORLD_FRAME_OUTPUT_WORDS']*4
 data=(folder/'input.bin').read_bytes();raw=(folder/'readback.bin').read_bytes()
 groups=[report['cases'],report['rejected_cases'],report['preserved_world49']];rows=sum(groups,[])
 assert len(rows)>0 and int.from_bytes(data[:4],'little')==len(rows)
 assert len(data)==4+iw*len(rows) and len(raw)==ow*len(rows)
 assert hashlib.sha256(data).hexdigest()==evidence['input_sha256'] and hashlib.sha256(raw).hexdigest()==evidence['output_sha256']
 assert report['passed'] and all(r['passed'] for r in rows)
 assert source_hashes('gpu/world_overlay_entry.slang')==evidence['source_sha256']
 spec=importlib.util.spec_from_file_location('overlay_normalized',ROOT/'research/summarize-portable-cross-gpu.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 generated={}
 for backend,suffix in [('cuda','cu'),('metal','metal')]:
  p=ROOT/'research/portable-build'/('world_overlay_entry.'+suffix)
  assert file_sha(p)==evidence['generated_sha256'][backend]
  generated[backend]=m.normalized(p.read_bytes())
 cases=[]
 for i,row in enumerate(rows):
  semantic={k:v for k,v in row.items() if k not in ('input_sha256','output_sha256','expected_sha256')}
  cases.append(dict(name=row['name'],input_sha256=hashlib.sha256(data[4+i*iw:4+(i+1)*iw]).hexdigest(),output_sha256=hashlib.sha256(raw[i*ow:(i+1)*ow]).hexdigest(),semantic_sha256=digest(semantic)))
 return dict(input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'],source_sha256=evidence['source_sha256'],generated_normalized_sha256=generated,cases=cases,native_cases=len(report['cases']),rejected_cases=len(report['rejected_cases']),preserved_cases=len(report['preserved_world49']))

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--expected',type=Path);a=p.parse_args()
 r=json.loads(a.report.read_text());actual=comparison(r);expected=json.loads(a.expected.read_text())['comparison'] if a.expected else actual
 changed=sorted(k for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k))
 result=dict(passed=not changed,changed_keys=changed,comparison=actual,backend=r['evidence']['backend'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),expected_sha256=file_sha(a.expected) if a.expected else None,report_sha256=file_sha(a.report),captured=r['captured'],cpu_trace_used_as_gpu_input=False,full_character_verified=0,full_goal_complete=False,scope=f'Exact all{len(actual["cases"])} input and output bytes plus full native/actual semantic dictionaries;no outputs normalized;raw retained locally')
 a.out.write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],changed
 print('Exact world overlay fingerprints:',len(actual['cases']),'passed')
if __name__=='__main__':main()
