"""Coverage expansion evidence: independently simulated complete real squads.
No CPU burst times, shot times, selected targets or buff states feed CUDA.
"""
import copy,json,sys,time,hashlib,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'app'))
from detail_coverage import body_for,coverage,a
from detail_gpu import evaluate_full
from gpu_selector import Cuda

def scenarios(include_coverage=True):
 out=[]
 if include_coverage:
  for r in coverage()['results']:
   if r['supported']:
    names=[r['character']]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=r['character']][:4]
    out.append(('coverage:'+r['character'],body_for(names,60)))
 names=['리타','마스트 : 로망틱 메이드','앨리스','모더니아','N102']
 out.append(('liter-alice-owned-180',body_for(names,180,True)))
 b=body_for(['N102','도라','앨리스','모더니아','얀'],180);out.append(('rank-refresh-alice-burst-180',b))
 b=body_for(['마스트 : 로망틱 메이드','루주','앨리스','도라','모더니아'],180,True);b['burst_policy']='mast3';b['stat_deltas']={'루주':{'hp':9000000}};b['profile']['chars']['앨리스']['cube']={'name':'렐릭 피어싱 큐브','level':7};out.append(('hp-threshold-lifesteal-pierce-mast3-180',b))
 b=body_for(['미하라','리타','마스트 : 로망틱 메이드','앨리스','모더니아'],180);out.append(('mihara-deferred-b3-and-last-bullet-180',b))
 b=body_for(['히메노','미란다','앨리스','모더니아','루드밀라'],180,True);b['enemy']['core_px']=0;b['enemy']['code']='작열';out.append(('sr-targets-exclude-caster-enemy-defense-180',b))
 for lv in (1,7,10):
  b=body_for(['리타','크라운','앨리스','모더니아','N102'],180,True)
  b['profile']['chars']['크라운']['skill_levels']={'1':lv,'2':lv,'3':lv}
  out.append((f'crown-stack-heal-shield-lv{lv}-180',b))
 b=body_for(['루주','크라운','앨리스','마스트 : 로망틱 메이드','모더니아'],180,True)
 b['burst_policy']='mast3'
 b['profile']['chars']['앨리스']['cube']={'name':'렐릭 베어 큐브','level':7}
 b['patches']={'크라운':{'skill_levels':{'1':10,'2':10}},'앨리스':{'equip_skills':{'charge_speed_pct':[4.3,4.3,6.2]}}}
 b['stat_deltas']={'크라운':{'hp':500000},'앨리스':{'atk':12345}}
 out.append(('crown-charge-cover-auto-reload-owned-180',b))
 b=body_for(['리타','키리','크라운','루드밀라','크로우'],60,True)
 out.append(('kiri-two-of-three-defenders-owned-60',b))
 return out

def compare(device,name,body,module_backend='auto',gpu_result=None):
 start=time.perf_counter()
 if gpu_result is None:
  compiled=a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=module_backend)
 else:gpu=gpu_result
 from calculator.buff_manager import BuffManager
 captured={};observed={'hp_below_80':False,'lifesteal_active':False,'pierce_active':False};crown={'stack20':0,'heal_received':0,'shield_applied':0,'auto_reload':0,'heal_damage_buff':False}
 from calculator.timeline import CharState
 original_init=BuffManager.__init__;original_get=BuffManager.get_buffs;original_notify=BuffManager.notify;original_reload=CharState._auto_reload
 def init(self,*args,**kwargs):
  original_init(self,*args,**kwargs)
  if 'hp' in self.state:captured['manager']=self
 def get(self,*args,**kwargs):
  result=original_get(self,*args,**kwargs)
  if args and args[0]=='앨리스':
   observed['hp_below_80']|=self.state.get('hp_pct',{}).get('앨리스',100)<80
   observed['lifesteal_active']|=result.get('lifesteal_pct',0)>0
   observed['pierce_active']|=bool(result.get('pierce_enabled'))
  if args and args[0]=='크라운':crown['heal_damage_buff']|=any(ab.effect.get('name')=='로얄 에타이어 4' for ab in self._active)
  return result
 def notify(self,event,t,char,*args,**kwargs):
  if char=='크라운':
   if event=='stack_reach:릴렉스:20':crown['stack20']+=1
   if event=='event:heal_received':crown['heal_received']+=1
   if event=='event:shield_applied':crown['shield_applied']+=1
  return original_notify(self,event,t,char,*args,**kwargs)
 def reload(self,*args,**kwargs):
  if self.name=='앨리스':crown['auto_reload']+=1
  return original_reload(self,*args,**kwargs)
 BuffManager.__init__=init;BuffManager.get_buffs=get;BuffManager.notify=notify;CharState._auto_reload=reload
 try:cpu=a.evaluate(body)
 finally:BuffManager.__init__=original_init;BuffManager.get_buffs=original_get;BuffManager.notify=original_notify;CharState._auto_reload=original_reload
 bm=captured['manager'];health={n:{'hp':bm.state['hp'][n],'hp_pct':bm.state['hp_pct'][n],'max_hp':bm.effective_max_hp(n)} for n in body['squad']}
 health_equal=all(math.isclose(health[n][k],gpu['compute']['final_hp'][n][k],rel_tol=1e-12,abs_tol=1e-6) for n in health for k in health[n])
 keys={'total_equal':'total_damage','members_equal':'members','burst_timeline_equal':'burst_timeline','base_stats_equal':'base_stats'}
 checks={k:gpu[v]==cpu[v] for k,v in keys.items()};checks['final_health_equal']=health_equal
 if name.startswith('hp-threshold'):checks['conditions_exercised']=all(observed.values())
 if name.startswith('crown-'):checks['crown_conditions_exercised']=all(crown[k] for k in ('stack20','heal_received','shield_applied','heal_damage_buff'))
 if name.startswith('crown-charge'):checks['automatic_reload_exercised']=crown['auto_reload']>0
 return {'name':name,'squad':body['squad'],'duration':body['duration'],'passed':all(checks.values()),**checks,'cpu_total':cpu['total_damage'],'gpu_total':gpu['total_damage'],'cpu_health':health,'gpu_health':gpu['compute']['final_hp'],'observed_cpu_conditions':observed,'observed_crown_conditions':crown,'members':[{'name':x['name'],'cpu':x['damage'],'gpu':y['damage']} for x,y in zip(cpu['members'],gpu['members'])],'cpu_bursts':cpu['burst_timeline'],'gpu_bursts':gpu['burst_timeline'],'gpu_module_backend':gpu['compute']['module_backend'],'gpu_execution_ms':gpu['compute']['elapsed_ms'],'module_initialization_ms':gpu['compute']['initialization_ms'],'wall_seconds':round(time.perf_counter()-start,3)}

def verify(device,include_coverage=True):
 results=[]
 for name,body in scenarios(include_coverage):
  try:case=compare(device,name,body)
  except (Exception,SystemExit) as e:case={'name':name,'squad':body['squad'],'passed':False,'error':str(e)}
  results.append(case);print(json.dumps({'name':name,'passed':case['passed'],**({'error':case['error']} if 'error' in case else {'cpu':case['cpu_total'],'gpu':case['gpu_total'],'bursts_equal':case['burst_timeline_equal']})},ensure_ascii=True),flush=True)
 before=json.loads((ROOT/'research/detail-coverage-before.json').read_text(encoding='utf-8'));after=coverage()
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'engine_revision':a.REVISION,'device':device.name,'passed':all(c['passed'] for c in results),'scope':'all compiler-accepted characters in specified compatible five-member rosters, plus named 180-second scenarios; static enemy and favorite stage zero, not every combination or favorite stage','cpu_trace_used_as_gpu_input':False,'compile_coverage_before':before['supported'],'compile_coverage_after':after['supported'],'catalog_size':after['characters'],'cases':results,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/gpu_selector.py','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.cu','app/detail_effects.ptx','app/gpu_service.py','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/damage.py']}}
if __name__=='__main__':
 d=Cuda()
 try:report=verify(d)
 finally:d.close()
 (ROOT/'research/detail-expanded-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
