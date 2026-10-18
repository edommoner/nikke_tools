"""Independent full-battle references for variable burst stages and reentry."""
import copy, hashlib, importlib.util, json, sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('stage_control',ROOT/'scripts/verify-control-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from detail_gpu import evaluate_full
E=c.E;NAMES=c.NAMES

@contextmanager
def configured(stages=None):
 original=c.a.sim.prepare
 def prepare(request):
  p=original(request)
  for ch in p.squad:
   if ch['name'] in (stages or {}):ch['burst_stage']=stages[ch['name']]
  return p
 with patch.object(c.a.sim,'prepare',prepare):yield

def scenarios():
 a,b,d,x,z=NAMES
 for stage,owner,stages in [(1,a,{}),(2,b,{z:'2'}),(3,d,{})]:
  for kind in ('instant','buff'):
   stat='burst_reentry' if kind=='instant' else f'burst_stage_override:reenter{stage}'
   yield f'reentry-{stage}-{kind}',{owner:[E('open reentry',kind,stat,stage,event='burst_cast')]},stages,35
 yield 'two-reentrants-one-opening',{a:[E('first reentry','instant','burst_reentry',1,event='burst_cast')],z:[E('second reentry','instant','burst_reentry',1,event='burst_cast')]},{},35
 yield 'request-number-does-not-change-current-stage',{a:[E('other stage request','instant','burst_reentry',2,event='burst_cast')]},{},12
 yield 'pending-startup-request-consumed-once',{a:[E('pending request','instant','burst_reentry',1)]},{},35
 yield 'state-presence-with-zero-value',{a:[E('zero state','buff','burst_stage_override:reenter1',0)]},{},35
 yield 'reentry-waits-for-own-cooldown',{b:[E('only candidate','instant','burst_reentry',2,event='burst_cast')]},{},35
 yield 'reentry-enter-notification-repeats-while-waiting',{b:[E('only candidate','instant','burst_reentry',2,event='burst_cast'),E('enter power','buff','atk_pct',1,event='burst_enter:2',max_stack=100)]},{},35
 yield 'removed-reentry-state',{a:[E('gone reentry','buff','burst_stage_override:reenter1',0,duration=1)]},{},12
 for target_stage in ('1','2','3','A'):
  yield 'stage-override-'+target_stage,{z:[E('new stage','buff','burst_stage_override:'+target_stage,0)]},{},35
 yield 'stage-override-expiry',{b:[E('temporary stage','buff','burst_stage_override:1',0,duration=4)]},{},35
 yield 'stage-override-last-active-wins',{z:[E('first stage','buff','burst_stage_override:3',0),E('second stage','buff','burst_stage_override:2',0,duration=5)]},{},35
 yield 'stage-update-on-next-controller-tick',{b:[E('stage at entry','buff','burst_stage_override:1',0,event='burst_enter:1',duration=1)]},{},12
 yield 'all-stage-explicit-fast-cooldown',{a:[E('no cooldown','buff','burst_cooldown',100)]},{a:'A',b:'3',z:'3'},12
 yield 'stage-and-ally-burst-notifications',{a:[E('reentry','instant','burst_reentry',1,event='burst_cast'),E('stage event','buff','atk_pct',4,event='squad_burst_cast:1'),E('ally event','buff','crit_dmg',2,event='event:ally_burst_cast',max_stack=30)]},{},35
 yield 'dynamic-stage-ally-condition',{b:[E('move b1','buff','burst_stage_override:1',0,duration=4)],a:[E('b1 present','buff','atk_pct',100,event='every:0.5s',condition=['has_burst1_ally'],duration=.5),E('b1 absent','buff','crit_dmg',50,event='every:0.5s',condition=['no_burst1_ally'],duration=.5)]},{z:'3'},12
 yield 'same-b3-reentry-keeps-both-deferred-hits',{d:[E('no cooldown','buff','burst_cooldown',100),E('reentry','instant','burst_reentry',3,event='burst_cast'),E('deferred hit','damage','bonus_damage',251,'target',event='burst_cast'),E('later buff','buff','atk_pct',100,event='burst_cast')]},{},12
 yield 'innate-b3-deferred-while-explicit-b1',{d:[E('no cooldown','buff','burst_cooldown',100),E('deferred hit','damage','bonus_damage',251,'target',event='burst_cast')]},{a:'3',d:'1',z:'3'},12

def compare(device,name,body,backend):
 compiled=c.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
 cpu=c.a.evaluate(body)
 checks={k:cpu[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode')}
 return dict(name=name,backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cpu_bursts=cpu['burst_timeline'],gpu_bursts=gpu['burst_timeline'])

def verify(device,backend):
 cases=[]
 for name,effects,stages,seconds in scenarios():
  for mode in ('fixed','accumulate'):
   body=c.body_for(NAMES,seconds,True);body['burst_gauge_mode']=mode
   with c.p.custom_effects(effects),configured(stages):
    row=compare(device,name+'-'+mode,body,backend)
   cases.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 previous=json.loads((ROOT/'research/detail-coverage-burst-gauge.json').read_text(encoding='utf-8'))
 current=json.loads((ROOT/'research/detail-coverage-burst-stage.json').read_text(encoding='utf-8'))
 was={r['character'] for r in previous['results'] if r['supported']}
 for entry in current['results']:
  if not entry['supported'] or entry['character'] in was:continue
  who=entry['character'];names=[who]+[n for n in NAMES if n!=who][:4]
  for mode in ('fixed','accumulate'):
   body=c.body_for(names,35,True);body['burst_gauge_mode']=mode
   row=compare(device,'real-'+who+'-'+mode,body,backend)
   row['reentry_observed']=any(r['event'].startswith('reenter:') for r in row['gpu_bursts']);row['passed'] &= row['reentry_observed']
   cases.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 return cases

def cpu_references():
 cases=[]
 for name,effects,stages,seconds in scenarios():
  body=c.body_for(NAMES,seconds,True)
  with c.p.custom_effects(effects),configured(stages):result=c.a.evaluate(body)
  cases.append(dict(name=name,authored_effects=effects,stages=stages,input=body,cpu_total=result['total_damage'],burst_timeline=result['burst_timeline']))
  print(json.dumps(dict(name=name,total=result['total_damage'],bursts=result['burst_timeline'][:8]),ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 cpu_only='--cpu-only' in sys.argv
 if cpu_only:cases=cpu_references()
 else:
  d=c.Cuda()
  try:cases=verify(d,'native')+verify(d,'ptx')
  finally:d.close()
 files=['research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','scripts/verify-burst-stage-detail.py','scripts/verify-control-detail.py','scripts/verify-periodic-detail.py','app/engine_worker.py','app/engine_compat.py']
 if not cpu_only:files+=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=cpu_only,cpu_trace_used_as_gpu_input=False,passed=cpu_only or all(r['passed'] for r in cases),cases=cases,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 suffix='cpu-references' if cpu_only else 'verification'
 (ROOT/f'research/detail-burst-stage-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
