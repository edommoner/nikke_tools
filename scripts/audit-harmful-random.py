"""Seeded CPU references for Cocoa-style random recipients; not GPU support."""
import hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('random_cleanse',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def run():
 cases=[];owner=v.NAMES[0]
 from calculator.buff_manager import BuffManager
 original=BuffManager._resolve_target
 for seed in (0,1,12345):
  for pool in ('empty','all-harmful','mixed-irremovable'):
   effects={owner:[v.E('random cleanse','instant','debuff_cleanse',1,'allies_random_with_debuff:2',event='every:1s')]}
   if pool!='empty':effects[owner].insert(0,v.E('harm','buff','atk_pct',-50,'all_allies',polarity='harmful'))
   if pool=='mixed-irremovable':
    effects[owner][0]['target']=v.NAMES[1:3]
    effects[owner].insert(0,v.E('irremovable','buff','atk_pct',-10,'self',polarity='harmful_irremovable'))
   samples=[]
   def target(self,rule,caster,*args,**kw):
    result=original(self,rule,caster,*args,**kw)
    if isinstance(rule,str) and rule.startswith('allies_random_with_debuff:'):samples.append({'rule':rule,'caster':caster,'time':self._cur_t,'selected':list(result)})
    return result
   body=v.c.body_for(v.NAMES,5,True);body['seed']=seed;state=random.getstate()
   try:
    random.seed(seed)
    with v.c.p.custom_effects(effects),patch.object(BuffManager,'_resolve_target',target),v.observe() as cleanups:result=v.c.a.evaluate(body)
   finally:random.setstate(state)
   cases.append(dict(seed=seed,pool=pool,input=body,authored_effects=effects,samples=samples,cleanups=cleanups,cpu_total=result['total_damage']))
   assert samples
   print(json.dumps({'seed':seed,'pool':pool,'selections':[s['selected'] for s in samples]},ensure_ascii=True),flush=True)
 files=['scripts/audit-harmful-random.py','scripts/audit-debuff-cleanse.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,cpu_trace_used_as_gpu_input=False,
             note='Seeds are authored inputs. Selected recipients are CPU observations and must never be supplied as GPU battle inputs.',cases=cases,
             source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/'research/detail-harmful-random-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':run()
