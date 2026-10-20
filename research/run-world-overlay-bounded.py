"""One isolated shared overlay validation;reuse tested native containment."""
import argparse,hashlib,importlib.util,json,runpy,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_phase_audit import Journal,observe
s=importlib.util.spec_from_file_location('world_containment',ROOT/'research/run-world-bounded.py');bounded=importlib.util.module_from_spec(s);s.loader.exec_module(bounded)

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--timeout',type=int,default=180);p.add_argument('--_child',action='store_true');a=p.parse_args()
 if not 1<=a.timeout<=180:p.error('Timeout must be1..180 seconds')
 folder=a.capture.resolve()
 if a._child:
  deadline=time.monotonic()+10
  while not (folder/'start.json').exists():
   if time.monotonic()>=deadline:raise RuntimeError('Containment gate not released;no GPU started')
   time.sleep(.02)
  import portable_backend
  journal=Journal(folder/'phases.jsonl')
  with observe(portable_backend,journal):
   sys.argv=['verify-world-overlay-body.py','--backend',a.backend,'--cleanse']
   journal.invoke('shared_world_overlay_suite',runpy.run_path,str(ROOT/'research/verify-world-overlay-body.py'),run_name='__main__')
  sys.argv=['summarize-world-overlay.py','--report',str(ROOT/f'research/portable-world-overlay-cleanse-{a.backend}.json'),'--out',str(folder/'summary.json'),'--expected',str(ROOT/'research/portable-world-cleanse-expected.json')]
  runpy.run_path(str(ROOT/'research/summarize-world-overlay.py'),run_name='__main__');return
 folder.mkdir(parents=True,exist_ok=False)
 paths=['research/run-world-overlay-bounded.py','research/run-world-bounded.py','research/portable_phase_audit.py','research/verify-world-overlay-body.py','research/summarize-world-overlay.py','research/portable-world-cleanse-expected.json']
 (folder/'manifest.json').write_text(json.dumps(dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),backend=a.backend,inputs=146,files={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in paths},normal4682_repeated=False),indent=2)+'\n')
 facts=bounded.run_bounded([sys.executable,str(Path(__file__).resolve()),'--_child','--backend',a.backend,'--capture',str(folder),'--timeout',str(a.timeout)],folder,a.timeout)
 print(json.dumps(facts));raise SystemExit(0 if facts['passed'] else 124 if facts['timed_out'] else 1)
if __name__=='__main__':main()
