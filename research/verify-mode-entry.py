"""Canonical entry/queued-reference fixtures; shared CUDA/Metal and native gates."""
import argparse,array,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime as runtime
from portable_specs import LIMITS as L
from portable_mode_entry_oracle import observe as entry_observe
from portable_pending_reference_oracle import observe as pending_observe
from portable_pending_reference_context import data_context
from portable_mode_entry_validation import rejection_programs

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--native-only',action='store_true');p.add_argument('--family',choices=['entry','pending','all'],default='all');a=p.parse_args()
 spec=importlib.util.spec_from_file_location('entry_core',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 names=['portable-mode-entry.json','portable-pending-reference.json']
 if a.family!='all':names=names[:1] if a.family=='entry' else names[1:]
 cases=sum([json.loads((ROOT/'tests/fixtures'/n).read_text())['cases'] for n in names],[])
 programs=[v.compile_case(c) for c in cases]
 bad,rejected=rejection_programs(cases,v.compile_case) if a.family!='pending' else ([],[])
 evidence={};out=None;folder=None
 if not a.native_only:
  folder=ROOT/'research/portable-build'/('mode-entry-'+a.family+'-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
  (folder/'input.bin').write_bytes(runtime.pack_programs(programs+bad))
  raw,evidence=runtime.dispatch_programs(programs+bad,backend=a.backend)
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
  out=array.array('I');out.frombytes(raw)
  if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  native=actual=None
  try:
   if c.get('mode_entry_reference'):native=entry_observe(c)
   else:
    with data_context(c):native=pending_observe(c)
   v.contains(native['queries'],c['expected_queries'],c['name']+'.authored')
   if out is not None:
    actual=runtime.decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);assert actual['status']==0,actual['status']
    v.contains(actual['queries'],native['queries'],c['name']+'.native')
    if c.get('mode_entry_reference'):
     v.contains(actual['weapons'],native['weapons'],c['name']+'.physical-clock')
     if 'mode_entry_wait_until' in actual:v.contains(actual['mode_entry_wait_until'],native['mode_entry_wait_until'],c['name']+'.entry-clock')
    else:v.contains(actual['trace'],native['packets'],c['name']+'.packets')
  except Exception as e:rows.append(dict(name=c['name'],passed=False,error=repr(e),native=native,actual=actual))
  else:rows.append(dict(name=c['name'],passed=True,native=native,actual=actual))
 statuses=[] if out is None else [out[(len(cases)+i)*L['OUTPUT_WORDS']] for i in range(len(bad))]
 passed=all(r['passed'] for r in rows) and (out is None or statuses==[r['status'] for r in rejected])
 paths=['research/verify-mode-entry.py','scripts/portable_mode_entry_oracle.py','scripts/portable_pending_reference_oracle.py','scripts/portable_pending_reference_context.py','scripts/portable_mode_entry_validation.py']+['tests/fixtures/'+n for n in names]
 result=dict(passed=passed,cases=rows,rejected_cases=rejected,actual_rejection_statuses=statuses,captured=str(folder) if folder else None,cpu_trace_used_as_gpu_input=False,scope='Native components; whole authored profiles verified separately',validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},**evidence)
 suffix='native' if a.native_only else a.backend
 (ROOT/f'research/portable-mode-entry-{a.family}-{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 assert passed,[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),a.family,'cases passed',suffix)
if __name__=='__main__':main()
