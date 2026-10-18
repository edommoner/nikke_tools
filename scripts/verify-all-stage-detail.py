"""Exercise Red Hood's A-stage selection, including default B3-only buttons."""
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('all_stage_base',ROOT/'scripts/verify-burst-stage-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
WHO='레드 후드';NAMES=[WHO]+v.NAMES[:4];E=v.E

def scenarios():
 yield 'default-A-is-B3-only',[],{}
 yield 'explicit-A-all-stages',[],{WHO:'A'}
 yield 'explicit-A-zero-cooldown',[E('no cooldown','buff','burst_cooldown',100)],{WHO:'A'}
 yield 'explicit-B2-zero-cooldown',[E('no cooldown','buff','burst_cooldown',100)],{WHO:'2'}
 yield 'override-A-opens-all-buttons',[E('all buttons','buff','burst_stage_override:A',0),E('no cooldown','buff','burst_cooldown',100)],{}
 yield 'override-B1-expires-back-to-A',[E('temporary B1','buff','burst_stage_override:1',0,duration=4)],{}
 yield 'override-B3-is-explicitly-active',[E('B3','buff','burst_stage_override:3',0)],{}
 yield 'A-reentry-each-stage-once',[E('all buttons','buff','burst_stage_override:A',0),E('no cooldown','buff','burst_cooldown',100),E('request','instant','burst_reentry',1,event='burst_cast')],{}

def run(device=None,backend='native'):
 rows=[]
 for name,effects,stages in scenarios():
  for mode in ('fixed','accumulate'):
   body=v.c.body_for(NAMES,12,True);body['burst_gauge_mode']=mode
   with v.c.p.custom_effects({WHO:effects}),v.configured(stages):
    if device is None:
     result=v.c.a.evaluate(body);row={'name':name+'-'+mode,'input':body,'authored_effects':{WHO:effects},'stages':stages,'cpu_total':result['total_damage'],'cpu_bursts':result['burst_timeline']}
    else:row=v.compare(device,name+'-'+mode,body,backend)
   # Six casts demonstrate the per-stage guard, not a permanently blocked slot.
   casts=[r for r in row['cpu_bursts'] if r['character']==WHO and r['event'].endswith('사용')]
   if name=='A-reentry-each-stage-once':assert len(casts)==6,(name,mode,casts)
   rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 return rows

if __name__=='__main__':
 cpu_only='--cpu-only' in sys.argv
 if cpu_only:rows=run()
 else:
  d=v.c.Cuda()
  try:rows=run(d,'native')+run(d,'ptx')
  finally:d.close()
 files=['scripts/verify-all-stage-detail.py','scripts/verify-burst-stage-detail.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 if not cpu_only:files+=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-build.json','app/detail_effects-sm86.json']
 report={'cpu_reference_only':cpu_only,'cpu_trace_used_as_gpu_input':False,'passed':cpu_only or all(r['passed'] for r in rows),'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'Synthetic complete raw effect replacement for A-stage behavior; not full real Red Hood skill parity','cases':rows,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 suffix='cpu-references' if cpu_only else 'verification'
 (ROOT/f'research/detail-all-stage-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
