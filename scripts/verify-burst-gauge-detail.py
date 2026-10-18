"""Pending accumulated-gauge GPU port: independent complete-battle oracle.
Reference files supply authored inputs only, never CPU gauge/shot/damage traces.
"""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('burst_gauge_control',ROOT/'scripts/verify-control-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from detail_gpu import evaluate_full
from detail_coverage import coverage
E=c.E;NAMES=c.NAMES

def scenarios():
 references=json.loads((ROOT/'research/detail-burst-gauge-cpu-references.json').read_text(encoding='utf-8'))
 for case in references['cases']:
  body=copy.deepcopy(case['input']);body['burst_gauge_mode']=case['config_override']['burst_gauge_mode']
  yield case['name'],case['authored_effects'],None,None,body
 references=json.loads((ROOT/'research/detail-burst-gauge-boundary-references.json').read_text(encoding='utf-8'))
 for case in references['cases']:
  body=c.body_for(NAMES,30,True);body['burst_gauge_mode']=case['mode']
  yield 'boundary-'+case['mode']+'-'+case['timing'],case['authored_effects'],None,None,body
 for camera in ('',NAMES[2]):
  body=c.body_for(NAMES,30,True);body['burst_gauge_mode']='accumulate'
  yield 'charge-camera-'+str(bool(camera)),{},None,camera,body
 body=c.body_for(NAMES,30,True);body['burst_gauge_mode']='accumulate'
 mode={'source':'스킬3','name':'gauge weapon mode','type':'weapon_change','target':'self','weapon_type':'SMG','max_ammo':30,'duration_bullets':30,'damage_coeff':{'10':251},'trigger':{'timing':['burst_cast'],'condition':[]}}
 yield 'charge-to-auto-mode-energy',{NAMES[2]:[mode]},None,None,body
 who='라피 : 레드 후드';names=[who]+NAMES[:4];body=c.body_for(names,30,True);body['burst_gauge_mode']='accumulate'
 yield 'skill-energy-exception',{who:[E('부착형 유탄 4','damage','damage',100,'target',event='on_attack_count:3')]},None,None,body

def compare(device,name,body,backend):
 compiled=c.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
 with c.observe() as (_,manager,_):cpu=c.a.evaluate(body)
 checks={k:cpu[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode')}
 state=manager['bm'].state;g=gpu['compute']['burst_gauge']
 checks['gauge_amount']=math.isclose(state['burst_gauge'],g['amount'],rel_tol=1e-12,abs_tol=1e-8)
 checks['charging_flag']=state['burst_gauge_charging']==g['charging']
 return {'name':name,'backend':backend,'passed':all(checks.values()),'checks':checks,'cpu_total':cpu['total_damage'],'gpu_total':gpu['total_damage'],'cpu_gauge':state['burst_gauge'],'gpu_gauge':g,'cpu_bursts':cpu['burst_timeline'],'gpu_bursts':gpu['burst_timeline']}

def verify(d,backend):
 out=[]
 for name,effects,controls,camera,body in scenarios():
  with c.p.custom_effects(effects),c.configured(controls,camera):r=compare(d,name,body,backend)
  out.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
 old=json.loads((ROOT/'research/detail-coverage-infinite.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']}
 pinned=json.loads((ROOT/'research/detail-coverage-burst-gauge.json').read_text(encoding='utf-8'));subjects={r['character'] for r in pinned['results'] if r['supported']} - was
 current=coverage();assert subjects <= {r['character'] for r in current['results'] if r['supported']}
 for entry in current['results']:
  if entry['character'] not in subjects:continue
  who=entry['character'];names=[who]+[n for n in NAMES if n!=who][:4]
  for mode in ('fixed','accumulate'):
   body=c.body_for(names,30,True);body['burst_gauge_mode']=mode;r=compare(d,'real-'+who+'-'+mode,body,backend);out.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
 return out

if __name__=='__main__':
 d=c.Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','scripts/verify-burst-gauge-detail.py']
 r={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(x['passed'] for x in cases),'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-burst-gauge-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
