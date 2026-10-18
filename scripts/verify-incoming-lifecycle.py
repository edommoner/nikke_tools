"""Autonomous boss shot scheduling and same-frame target reaction ordering."""
import hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('incoming_lifecycle',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)

def fixtures():
 for delay in (0,.1):
  b=v.body(2);b['enemy']['patterns']=[dict(id='cycle',kind='attack',delay=delay,until={'time':.2},after=['start','cycle'],repeat=0,spec=dict(coeff=100,atk=1,target='random:2',hits=4,interval=.07))]
  yield 'repeat-close-reopen-delay-'+str(delay),b,{}
 b=v.body(2);first={**v.attack('slot:4',hits=3,interval=.5),'id':'first'};second={**v.attack('random:1',hits=3,interval=.5),'id':'second'};b['enemy']['patterns']=[first,second]
 yield 'same-frame-cloak-changes-second-shot-pool',b,{v.NAMES[3]:[v.B('reactive cloak','stealth',event='received_hit',duration=.2)]}
 b=v.body(2);first={**v.attack('slot:1',hits=3,interval=.5),'id':'first'};second={**v.attack('slot:4',hits=3,interval=.5),'id':'second'};b['enemy']['patterns']=[first,second]
 yield 'same-frame-hidden-taunt-steals-second-slot-shot',b,{v.NAMES[0]:[v.B('reactive taunt','taunt',event='received_hit',duration=.2),v.B('reactive cloak','stealth',event='received_hit',duration=.2)]}

if __name__=='__main__':
 files=['scripts/verify-incoming-lifecycle.py','scripts/verify-incoming-detail.py','app/detail_gpu.py','app/detail_boss.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
 sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
 d=v.v.v.Cuda();rows=[]
 try:
  for name,b,extra in fixtures():
   with v.context(name,extra):control=v.v.a.evaluate(b)
   hits=control['incoming_hits']
   if name.startswith('repeat-'):assert len(hits)>8 and sum(e['event']=='start' for e in control['boss_timeline'])>2
   if 'cloak-changes' in name:assert all(h['target']!=v.NAMES[3] for h in hits if h['pattern']=='second') and all(h['target']==v.NAMES[3] for h in hits if h['pattern']=='first')
   if 'taunt-steals' in name:assert all(h['target']==v.NAMES[0] for h in hits)
   row=v.compare(d,name,b,extra,'native');rows.append(row)
   if not row['passed']:break
 finally:d.close()
 assert hashes=={p:sha(p) for p in files}
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==4 and all(r['passed'] for r in rows),objective_complete=False,planned_cases=4,not_run_cases=4-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
 (ROOT/'research/detail-incoming-lifecycle-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
