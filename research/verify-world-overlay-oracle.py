"""CPU replay keeps all17 established full-simulation oracle results unchanged."""
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
from world_frame_native import observe

def main():
 spec=importlib.util.spec_from_file_location('overlay_prior_cases',ROOT/'research/verify-world-frame.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 prior=ROOT/'research/portable-world-frame-metal.json';saved=json.loads(prior.read_text());assert saved['passed']
 expected={x['name']:x['native'] for x in saved['cases']};cases=module.fixtures();assert len(cases)==len(expected)==17
 rows=[]
 for case in cases:
  actual=observe(case);original=expected[case['name']];changed=sorted(k for k in set(actual)|set(original) if actual.get(k)!=original.get(k))
  rows.append(dict(name=case['name'],passed=not changed,changed=changed))
 report=dict(passed=all(x['passed'] for x in rows),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('research/world_frame_native.py','research/verify-world-overlay-oracle.py','research/verify-world-frame.py')},prior_report_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),cases=rows,gpu_executions=0,scope='All17 previous native full simulations exactly preserved after optional authored enemy/weapon inputs;does not reexecute or certify GPU overlays',full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-overlay-oracle-parity.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],rows
 print('All17 complete native result dictionaries preserved')
if __name__=='__main__':main()
