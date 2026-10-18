"""Independent complete battles from authored cleanse inputs only."""
import copy,hashlib,importlib.util,json,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('cleanse_cases',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import evaluate_full

@contextmanager
def injected_effects(effects):
 from calculator import buff_manager,timeline
 original=buff_manager.BuffManager
 class Injected(original):
  def char_effects(self,name):return copy.deepcopy(super().char_effects(name))+copy.deepcopy(effects.get(name,[]))
 buff_manager.BuffManager=timeline.BuffManager=Injected
 try:yield
 finally:buff_manager.BuffManager=timeline.BuffManager=original

def real_cases():
 before=json.loads((ROOT/'research/detail-coverage-burst-stage.json').read_text(encoding='utf-8'))
 after=json.loads((ROOT/'research/detail-coverage-cleanse.json').read_text(encoding='utf-8'))
 was={r['character'] for r in before['results'] if r['supported']}
 for entry in after['results']:
  if not entry['supported'] or entry['character'] in was:continue
  who=entry['character'];names=[who]+[n for n in v.NAMES if n!=who][:4]
  operations=[('character',None)]
  if who=='크러스트':operations=[('authored-tap',{who:{'tap_fire':{'rate':3.6,'release':.03}}}),('authored-hold',{who:{'sequence':[{'t':0,'action':'hold','until':3},{'t':4,'action':'hold','until':7},{'t':8,'action':'hold','until':11}]}})]
  for operation,controls in operations:
   for mode in ('fixed','accumulate'):
    body=v.c.body_for(names,35,True);body['burst_gauge_mode']=mode;body['shooting_policy']='character'
    yield who+'-'+operation+'-'+mode,body,{names[1]:[v.E('verification harm','buff','atk_pct',-20,'all_allies',polarity='harmful')]},controls

def verify(device,backend='native'):
 cases=[]
 for name,effects,seconds in v.scenarios():
  for mode in ('fixed','accumulate'):
   body=v.c.body_for(v.NAMES,seconds,True);body['burst_gauge_mode']=mode
   with v.c.p.custom_effects(effects):
    compiled=v.c.a.evaluate({**body,'_compile_gpu_detail':True})
    gpu=evaluate_full(device,compiled,module_backend=backend)
    with v.observe() as cleanups:cpu=v.c.a.evaluate(body)
   checks={k:cpu[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode')}
   checks['cleanse_exercised']=bool(cleanups)
   # Atomic cleanse does not emit state-end callbacks, even when fully stripped.
   checks['cpu_no_end_callbacks']=not any(r['notifications'] for r in cleanups)
   row=dict(name=name+'-'+mode,backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'])
   cases.append(row);print(json.dumps(row),flush=True)
 for name,body,effects,controls in real_cases():
  with injected_effects(effects),v.c.configured(controls):
   compiled=v.c.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
   with v.observe() as cleanups:cpu=v.c.a.evaluate(body)
  changed=0
  for call in cleanups:
   after={ab['uid']:ab for ab in call['after']}
   changed+=sum(ab['polarity']=='harmful' and (ab['uid'] not in after or ab['targets']!=after[ab['uid']]['targets']) for ab in call['before'])
  checks={k:cpu[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode')};checks['positive_cleanse']=changed>0
  row=dict(name='real-'+name,backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cleanse_calls=len(cleanups),changed_harmful_instances=changed,authored_controls=controls)
  cases.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 d=v.c.Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 files=['scripts/verify-cleanse-detail.py','scripts/audit-debuff-cleanse.py','scripts/verify-control-detail.py','scripts/verify-periodic-detail.py','research/detail-coverage-cleanse.json','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in cases),cpu_trace_used_as_gpu_input=False,cases=cases,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/'research/detail-cleanse-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
