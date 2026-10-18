"""End-to-end differential checks: complete real squads and owned growth adapter.
GPU independently chooses all burst and shot times. No CPU event replay.
"""
import copy,json,sys,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker as adapter
from detail_gpu import evaluate_full
from gpu_selector import Cuda

def fixture(duration=180,policy='auto',grown=False,reverse=False):
 names=['모더니아','루주','마스트 : 로망틱 메이드','도라','얀']
 if reverse:names=['얀','도라','루주','모더니아','마스트 : 로망틱 메이드']
 chars={n:{k:copy.deepcopy(v) for k,v in adapter.spec.DEFAULT_CHAR.items() if k in adapter.spec.GROWTH_KEYS} for n in names}
 cube_names=[n for n,data in adapter.spec.CUBES.items() if data['stat'] in ('accuracy_pct','charge_speed_pct','reload_speed_pct','max_ammo_pct')]
 for i,(n,c) in enumerate(chars.items()):
  c['cube']={'name':cube_names[i%len(cube_names)] if grown else '__none__','level':1+i*3 if grown else 1}
  c['favorite_stage']=0;c['collection_stage']='SR15' if grown else '없음'
  if grown:
   c['breakthrough']=i%4;c['core_enhancement']=4 if i%4==3 else 0;c['affinity']=1+i*7
   c['skill_levels']={'1':1+i*2,'2':10-i,'3':3+i}
   for gear in c['equipment'].values():gear['level']=i%6
 return {'profile':{'chars':chars,'_account':{'console':adapter.spec.DEFAULT_CHAR['console']}},'squad':names,'duration':duration,'level':400,'enemy':{'def':31784,'code':'풍압','core_px':0 if reverse else 50,'distance':25},'burst_policy':policy,'patches':{'루주':{'skill_levels':{'1':8},'equip_skills':{'max_ammo_pct':71.12,'charge_speed_pct':12.34}}} if grown else {},'stat_deltas':{'마스트 : 로망틱 메이드':{'atk':12345,'hp':100000,'def':345}} if grown else {}}

def verify(device):
 cases=[]
 for name,body in [('full-auto-180',fixture()),('full-mast3-180',fixture(policy='mast3')),('owned-equipment-cube-collection-60',fixture(60,grown=True)),('positions-element-core-growth-60',fixture(60,'mast3',True,True))]:
  started=time.perf_counter();compiled=adapter.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled);cpu=adapter.evaluate(body)
  case={'name':name,'duration':body['duration'],'total_equal':gpu['total_damage']==cpu['total_damage'],'members_equal':gpu['members']==cpu['members'],'burst_timeline_equal':gpu['burst_timeline']==cpu['burst_timeline'],'base_stats_equal':gpu['base_stats']==cpu['base_stats'],'cpu_total':cpu['total_damage'],'gpu_total':gpu['total_damage'],'members':[{'name':a['name'],'cpu':a['damage'],'gpu':b['damage']} for a,b in zip(cpu['members'],gpu['members'])],'gpu_bursts':gpu['burst_timeline'],'cpu_bursts':cpu['burst_timeline'],'gpu_ms':gpu['compute']['elapsed_ms'],'wall_seconds':round(time.perf_counter()-started,3)}
  case['passed']=all(case[k] for k in ('total_equal','members_equal','burst_timeline_equal','base_stats_equal'));cases.append(case)
  print(json.dumps({'case':name,'passed':case['passed'],'members':case['members'],'bursts_equal':case['burst_timeline_equal']},ensure_ascii=True),flush=True)
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'engine_revision':adapter.REVISION,'device':device.name,'passed':all(c['passed'] for c in cases),'full_squad_verified':all(c['passed'] for c in cases),'scope':'listed complete real five-member fixtures, static enemy, auto shooting, fixed-gauge model; not every character','cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/gpu_selector.py','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.cu','app/detail_effects.ptx','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/damage.py']}}

if __name__=='__main__':
 device=Cuda()
 try:report=verify(device)
 finally:device.close()
 (ROOT/'research/detail-full-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
