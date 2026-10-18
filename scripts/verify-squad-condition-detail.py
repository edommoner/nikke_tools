"""Whole-squad composition predicates, with independent CPU simulation and RNG."""
import copy,hashlib,importlib.util,json,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
r=module('squad_random','scripts/verify-random-target-detail.py');a=r.v.v.c.a
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda

@contextmanager
def supporter_without_skills(name):
 original=BuffManager.char_effects
 def effects(self,who):return [] if who==name else original(self,who)
 with patch.object(BuffManager,'char_effects',effects):yield

def real_cases():
 for who,buddy,positive,supporter in [('누아르','루주',True,None),('누아르','리타',False,None),('람','렘',True,'렘'),('람','리타',False,None)]:
  names=[who,buddy]+[n for n in ['리타','크라운','앨리스','모더니아'] if n not in (who,buddy)][:3]
  if supporter:names=[who,buddy,'리타','크라운','모더니아']
  body=r.v.v.c.body_for(names,35,True);body['shooting_policy']='character';body['stat_deltas']={who:{'atk':1234}}
  yield who+('-with-buddy' if positive else '-without-buddy'),body,positive,supporter

def verify(device,backend='native',quick=False):
 refs=json.loads((ROOT/'research/detail-squad-condition-cpu-references.json').read_text(encoding='utf-8'));rows=[]
 for ref in refs['cases']:
  for seed in ((0,) if quick else (0,12345)):
   for mode in ('fixed','accumulate'):
    body=copy.deepcopy(ref['input']);body.update(seed=seed,burst_gauge_mode=mode,_debug_random_state=True)
    try:row=r.compare(device,ref['name']+('-positive' if ref['has_buddy'] else '-negative'),body,ref['authored_effects'],backend)
    except Exception as e:row=dict(name=ref['name'],backend=backend,seed=seed,mode=mode,passed=False,error=str(e))
    rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 if not quick:
  for name,template,positive,supporter in real_cases():
   for seed in (0,12345):
    for mode in ('fixed','accumulate'):
     body=copy.deepcopy(template);body.update(seed=seed,burst_gauge_mode=mode,_debug_random_state=True);observed=[];original=BuffManager._condition_ok
     def check(self,conditions,caster,t,eff=None):
      result=original(self,conditions,caster,t,eff)
      if caster==body['squad'][0] and 'squad_ally_exists' in conditions:observed.append(result)
      return result
     try:
      with patch.object(BuffManager,'_condition_ok',check),supporter_without_skills(supporter):row=r.compare(device,name,body,{},backend,injected=True)
      row['checks']['condition_exercised']=positive in observed;row['passed'] &= row['checks']['condition_exercised'];row['authored_supporter_without_skills']=supporter
     except Exception as e:row=dict(name=name,backend=backend,seed=seed,mode=mode,passed=False,error=str(e))
     rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 return rows

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--native-only',action='store_true');p.add_argument('--quick',action='store_true');p.add_argument('--output',default='research/detail-squad-condition-verification.json');args=p.parse_args();d=Cuda()
 try:rows=verify(d,'native',args.quick)+([] if args.native_only else verify(d,'ptx',args.quick))
 finally:d.close()
 files=['scripts/verify-squad-condition-detail.py','scripts/audit-squad-condition.py','research/detail-squad-condition-cpu-references.json','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(x['passed'] for x in rows),native_only=args.native_only,quick=args.quick,cpu_trace_used_as_gpu_input=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
