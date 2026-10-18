"""Infinite ammunition: whole-squad damage and independent magazine state."""
import hashlib,importlib.util,json,sys,math
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('infinite_control',ROOT/'scripts/verify-control-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
spec=importlib.util.spec_from_file_location('infinite_cpu',ROOT/'scripts/audit-infinite-ammo.py');cpu=importlib.util.module_from_spec(spec);spec.loader.exec_module(cpu)
from detail_gpu import evaluate_full
from detail_coverage import coverage
E=c.E;NAMES=c.NAMES

def placeholders(d,backend):
 spec=importlib.util.spec_from_file_location('placeholder_oracle',ROOT/'scripts/verify-detail.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
 from detail_gpu import run
 out=[];stats={n:{'atk':100000,'def':1000,'hp':1000000} for n in NAMES}
 for paired in (False,True):
  for values in (False,True):
   e=E('placeholder probe','buff','atk_pct',1,event='non_full_charge_fire_count:{0}',max_stack=100)
   if paired:e['trigger']['timing'].append('non_full_charge_fire_count:5')
   if values:e['trigger_values']={'10':5}
   p=o.program(o.characters(NAMES),[(e,NAMES[0])]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[(i+1)/10,0,40,0,0,-1,0,0] for i in range(9)]+[[1,2,0,0,p['states']['placeholder probe'],0,0,0]]
   expected,_=o.oracle(p,script,[31784,0],stats);gpu=run(d,[p],script,[[31784,0]],[stats],module_backend=backend)
   want=2 if paired else 0;r={'name':f'placeholder-{paired}-{values}','backend':backend,'passed':expected[0][37]==gpu['queries'][0][0][37]==want,'cpu_count':expected[0][37],'gpu_count':gpu['queries'][0][0][37]};out.append(r);print(json.dumps(r),flush=True)
 return out

def scenarios():
 for who in (NAMES[0],NAMES[2]):
  for forced in (False,True):
   es=[E('one round','buff','max_ammo_flat',-10000),E('temporary infinite','buff','infinite_ammo',0,event='every:1s',duration=.4,max_trigger=4),E('count consumption','buff','atk_pct',1,event='squad_ammo_consume:1',max_stack=100),E('last fire','buff','crit_dmg',1,event='last_bullet_fire',max_stack=100)]
   if forced:es.append(E('force inside window','instant','force_reload',0,event='every:1.1s',max_trigger=3))
   yield 'temporary-'+who+'-'+str(forced),{who:es},{},7,True
 for kind in ('SMG','SR'):
  who=NAMES[2];es=[E('infinite','buff','infinite_ammo',0,event='burst_cast',duration=5),{'source':'스킬3','name':'mode','type':'weapon_change','target':'self','weapon_type':kind,'max_ammo':3,'duration_bullets':3,'damage_coeff':{'10':251},'trigger':{'timing':['burst_cast'],'condition':[]}}]
  yield 'finite-mode-'+kind,{who:es},{},20,False
 yield 'tap-and-infinite',{NAMES[2]:[E('one round','buff','max_ammo_flat',-10000),E('infinite','buff','infinite_ammo',0,event='burst_cast',duration=10)]},{NAMES[2]:{'tap_fire':{'rate':3.6,'release':.03}}},20,False
 yield 'runtime-infinite-gate',{NAMES[0]:[E('one round','buff','max_ammo_flat',-10000),E('infinite','buff','infinite_ammo',0,event='passive',condition=['during_full_burst'])]}, {},25,True
 yield 'last-fire-does-not-change-current-auto-shot',{NAMES[0]:[E('one round','buff','max_ammo_flat',-10000),E('infinite on last fire','buff','infinite_ammo',0,event='last_bullet_fire',duration=.5)]},{},8,False
 yield 'pellet-callback-does-not-change-charge-ammo-snapshot',{NAMES[2]:[E('one round','buff','max_ammo_flat',-10000),E('three pellets','buff','pellet_count_fixed',3),E('infinite on pellet','buff','infinite_ammo',0,event='pellet_hit',duration=1)]},{},12,False

def compare(d,name,body,backend):
 compiled=c.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(d,compiled,module_backend=backend)
 with cpu.observe() as (states,events):result=c.a.evaluate(body)
 checks={k:result[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline')}
 # Magazine readback is added by the v16 kernel, independent of the CPU run.
 errors=[]
 for who,cs in states.items():
  g=gpu['compute']['final_control'][who]
  for k,val in {'ammo':cs.ammo,'reloading_until':cs.reloading_until}.items():
   if not math.isclose(g[k],val,rel_tol=1e-12,abs_tol=1e-8):errors.append([who,k,val,g[k]])
 checks['magazines']=not errors
 return {'name':name,'backend':backend,'passed':all(checks.values()),'checks':checks,'errors':errors,'cpu_total':result['total_damage'],'gpu_total':gpu['total_damage'],'observations':events}

def verify(d,backend):
 out=placeholders(d,backend)
 for name,effects,controls,seconds,cancel in scenarios():
  with c.p.custom_effects(effects),c.configured(controls):r=compare(d,name,c.body_for(NAMES,seconds,True),backend)
  if cancel:r['passed'] &= bool(r['observations']['cancel_reload'])
  out.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
 old=json.loads((ROOT/'research/detail-coverage-counts.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']}
 feature=json.loads((ROOT/'research/detail-coverage-infinite.json').read_text(encoding='utf-8'));expected={r['character'] for r in feature['results'] if r['supported']} - was
 current={r['character']:r for r in coverage()['results']}
 assert all(current[n]['supported'] for n in expected),'Previously verified feature character lost GPU support'
 for entry in feature['results']:
  if entry['character'] not in expected:continue
  who=entry['character'];names=[who]+[n for n in NAMES if n!=who][:4]
  r=compare(d,'real-'+who,c.body_for(names,30,True),backend);out.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
 return out

if __name__=='__main__':
 d=c.Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-infinite-detail.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(r['passed'] for r in cases),'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-infinite-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
