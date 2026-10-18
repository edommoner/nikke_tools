"""Full-squad CPU/GPU checks for list burst priorities and owned charge weapons."""
import copy,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from detail_gpu import evaluate_full,weapon_rows,UnsupportedDetail
from gpu_selector import Cuda

def scenarios():
 names=['리타','도라','앨리스','모더니아','얀']
 for label,patterns in [('list-priority',{'앨리스':[1,3],'모더니아':[2,4]}),('empty-list-is-low-priority',{'리타':[],'얀':[1,3]}),('both-empty-still-cast',{'앨리스':[],'모더니아':[]})]:
  b=body_for(names,60,True)
  b['patches']={'앨리스':{'skill_levels':{'1':9,'2':8,'3':10},'equip_skills':{'charge_speed_pct':[4.3,4.3,6.2],'max_ammo_pct':[11.12,11.12,12.34]}}}
  b['stat_deltas']={'앨리스':{'atk':12345,'hp':54321,'def':321}}
  yield label,b,patterns
 b=body_for(['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'],60,True)
 yield 'list-fallback-after-early-cycles',b,{'마스트 : 로망틱 메이드':[1],'도라':[2]}
 b=body_for(['리타','도라','앨리스','모더니아','얀'],30,True);b['burst_policy']='mast3'
 yield 'mast-absent-charge-equipment',b,{}

def verify(device,backend='auto'):
 cases=[]
 for label,body,patterns in scenarios():
  prepare=a.sim.prepare
  def configured(request):
   run=prepare(request);run.config['burst_pattern']=copy.deepcopy(patterns);return run
  started=time.perf_counter()
  with patch.object(a.sim,'prepare',configured):
   compiled=a.evaluate({**body,'_compile_gpu_detail':True})
   gpu=evaluate_full(device,compiled,module_backend=backend);cpu=a.evaluate(body)
  matches={key:gpu[key]==cpu[key] for key in ('total_damage','members','base_stats','burst_timeline','burst_policy')}
  # Require actual firing and a complete chain; matching empty outputs is insufficient.
  passed=all(matches.values()) and all(m['damage']>0 for m in gpu['members']) and any(e['event'].startswith('stage:3') for e in gpu['burst_timeline'])
  case={'name':label,'passed':passed,'matches':matches,'patterns':patterns,'total':gpu['total_damage'],'cpu_total':cpu['total_damage'],'members':gpu['members'],'burst_timeline':gpu['burst_timeline'],'module_backend':gpu['compute']['module_backend'],'wall_seconds':round(time.perf_counter()-started,3)}
  cases.append(case);print(json.dumps({'case':label,'passed':passed,'matches':matches,'bursts':gpu['burst_timeline']},ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 device=Cuda()
 try:cases=verify(device,'native')+verify(device,'ptx')
 finally:device.close()
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'scope':'five complete squads on native and PTX; fixed static enemy and automatic full-charge weapons','cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/engine_worker.py']}}
 (ROOT/'research/detail-burst-lists-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
