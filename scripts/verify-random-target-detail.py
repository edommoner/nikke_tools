"""Whole battles and final MT state, without CPU draws/choices as GPU inputs."""
import copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('random_lifecycle',ROOT/'scripts/audit-random-target-lifecycle.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import evaluate_full
E=v.E;OWNER=v.OWNER

def extra_cases():
 for count in range(6):
  yield 'random-count-'+str(count),[E('random stat','buff','atk_pct',20,'allies_random:'+str(count),event='every:1s',duration=.7)]
 yield 'ordered-list-duplicates',[E('ordered refill','instant','ammo_charge_flat',1,['allies_random:2','self','allies_random:2'],event='every:1s')]
 yield 'one-bullet-lazy',[E('random bullet','buff','atk_pct',100,'allies_random:2',event='on_attack_count:3',duration_bullets=1)]
 yield 'refresh-lazy-target',[E('random refresh','buff','atk_pct',5,'allies_random:2',event='every:1s',duration=3,max_stack=4)]
 yield 'singleton-harmful-pool-consumes-rng',[E('harm','buff','atk_pct',-20,'self',polarity='harmful'),E('clean','instant','debuff_cleanse',0,'allies_random_with_debuff:1',event='every:1s')]
 yield 'irremovable-sampled-but-retained',[E('permanent harm','buff','atk_pct',-20,'all_allies',polarity='harmful_irremovable'),E('clean','instant','debuff_cleanse',0,'allies_random_with_debuff:3',event='every:1s')]
 yield 'shared-lazy-harmful-stats',[E('harm','buff','atk_pct',-20,'allies_random:2',polarity='harmful'),E('same group','buff','crit_dmg',40,'allies_random:2'),E('clean','instant','debuff_cleanse',0,'allies_random_with_debuff:2',event='every:1s')]
 yield 'unread-inert-random-at-fullburst-snapshot',[E('unread','buff','',0,'allies_random:1',duration=7)]
 yield 'unread-dot-at-fullburst-snapshot',[E('unread dot','damage','dot_damage',100,'allies_random:1',tick_interval=.5,duration=7)]
 yield 'caster-atk-special-lazy-target',[E('special random','buff','atk_caster_based_pct',20,'allies_random:2')]
 yield 'hp-conversion-special-lazy-target',[E('special random hp','buff','atk_from_hp_pct',5,'allies_random:2')]

def compare(device,label,body,effects,backend,injected=False):
 context=v.v.c.p.custom_effects(effects)
 if injected:
  spec=importlib.util.spec_from_file_location('random_raw',ROOT/'scripts/verify-cleanse-detail.py');raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw);context=raw.injected_effects(effects)
 with context:
  compiled=v.v.c.a.evaluate({**body,'_compile_gpu_detail':True})
  gpu=evaluate_full(device,compiled,module_backend=backend)
  state=random.getstate()
  try:
   cpu=v.v.c.a.evaluate(body);final=list(random.getstate()[1])
  finally:random.setstate(state)
 checks={k:cpu[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode','seed')}
 checks['final_random_state']=final==gpu['_random_state']
 row=dict(name=label,seed=body['seed'],mode=body.get('burst_gauge_mode','fixed'),backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cpu_rng_index=final[-1],gpu_rng_index=gpu['_random_state'][-1])
 if not row['passed']:row['cpu_members']=cpu['members'];row['gpu_members']=gpu['members']
 return row

def real_cases():
 names=['코코아']+[n for n in v.v.NAMES if n!='코코아'][:4]
 for seed in (0,12345,4294967295):
  for mode in ('fixed','accumulate'):
   body=v.v.c.body_for(names,35,True);body.update(seed=seed,_debug_random_state=True,burst_gauge_mode=mode,shooting_policy='character')
   yield 'real-cocoa-positive-cleanse',body,{names[1]:[E('renewed verification harm','buff','atk_pct',-20,'all_allies',event='every:2s',polarity='harmful')]}

def verify(device,backend='native',quick=False,only_case=None):
 rows=[]
 for seed in (0,12345):
  for label,effects in list(v.scenarios())+([] if quick else list(extra_cases())):
   if only_case and label!=only_case:continue
   for mode in (('fixed',) if quick else ('fixed','accumulate')):
    body=v.v.c.body_for(v.v.NAMES,35 if label in ('caster-atk-special-lazy-target','hp-conversion-special-lazy-target') else 5,True);body.update(seed=seed,_debug_random_state=True,burst_gauge_mode=mode)
    try:row=compare(device,label,body,{OWNER:effects},backend)
    except Exception as error:row=dict(name=label,seed=seed,mode=mode,backend=backend,passed=False,error=str(error))
    rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 if not quick:
  for label,body,effects in real_cases():
   if only_case and label!=only_case:continue
   try:row=compare(device,label,body,effects,backend,injected=True)
   except Exception as error:row=dict(name=label,seed=body['seed'],mode=body['burst_gauge_mode'],backend=backend,passed=False,error=str(error))
   rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 return rows

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');p.add_argument('--native-only',action='store_true');p.add_argument('--ptx-only',action='store_true');p.add_argument('--case');p.add_argument('--output',default='research/detail-random-target-verification.json');args=p.parse_args()
 device=v.v.c.Cuda()
 try:rows=sum((verify(device,b,args.quick,args.case) for b in (('ptx',) if args.ptx_only else ('native',) if args.native_only else ('native','ptx'))),[])
 finally:device.close()
 files=['scripts/verify-random-target-detail.py','scripts/audit-random-target-lifecycle.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),quick=args.quick,native_only=args.native_only,cpu_trace_used_as_gpu_input=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
