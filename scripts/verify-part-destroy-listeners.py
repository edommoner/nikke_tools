"""Raw accepted destruction listeners, exercised by actual GPU part destruction."""
import argparse,hashlib,importlib.util,json,random,sys
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('listener_parts',ROOT/'scripts/verify-live-parts-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from calculator.buff_manager import BuffManager
from detail_gpu import evaluate_full
from gpu_service import resolve_verification
SUBJECTS=['레이븐','아크레인저 블랙','로산나 : 시크 오션','E.H.','모리']

def verify(device,backend):
 rows=[]
 for subject in SUBJECTS:
  for mode in ('fixed','accumulate'):
   body=v.p.body_for([subject,'리타','크라운','앨리스','모더니아'],14,True);body.update(seed=12345,burst_policy='rules',burst_gauge_mode=mode,_debug_random_state=True)
   body['profile']['chars'][subject]['skill_levels']={'1':10,'2':10,'3':10}
   body['enemy']['parts']=[dict(name='part'+str(i),hp=5,reach=(i%5)+1) for i in range(32)]
   effects={'리타':[v.E('authored destroy stimulus','damage','damage',100,'all_enemies',event='every:0.5s',max_trigger=1,hits_parts=True)]}
   original=BuffManager.notify;events=[]
   def observe(self,event,t,caster,*args,**kwargs):
    if event=='event:part_destroy' and caster==subject:events.append(t)
    return original(self,event,t,caster,*args,**kwargs)
   with v.raw.injected_effects(effects):
    compiled=v.p.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
    with patch.object(BuffManager,'notify',observe):cpu=v.p.a.evaluate(body)
    rng=list(random.getstate()[1])
   result=resolve_verification(gpu,cpu);checks=result['compute']['cpu_verification'].copy()
   checks.update(actual_gpu=result['compute']['backend']=='cuda_detail',final_random_state=rng==gpu['_random_state'],raw_events_exercised=len(events)==32,all_32_parts_destroyed=all(p['destroyed'] for p in cpu['parts_state']))
   row=dict(character=subject,mode=mode,backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],raw_skills_retained=True,part_events=events)
   if not row['passed']:row.update(cpu_members=cpu['members'],gpu_members=gpu['members'],cpu_bursts=cpu['burst_timeline'],gpu_bursts=gpu['burst_timeline'],cpu_parts=cpu['parts_state'],gpu_parts=gpu.get('parts_state'))
   rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 return rows

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx','both'],default='both');args=p.parse_args()
 files=['scripts/verify-part-destroy-listeners.py','scripts/verify-live-parts-detail.py','app/detail_gpu.py','app/detail_world.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
 hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};d=v.Cuda()
 try:rows=[row for backend in (('native','ptx') if args.backend=='both' else (args.backend,)) for row in verify(d,backend)]
 finally:d.close()
 assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'Sources changed during verification'
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),objective_complete=False,cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,
             scope='Five accepted raw part-destroy listener characters, fixed/accumulated gauge, 32 real part destructions; one authored damage stimulus added on Liter.')
 (ROOT/'research/detail-part-destroy-listeners-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
