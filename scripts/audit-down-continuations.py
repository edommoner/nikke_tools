"""CPU-only evidence for pre-cast timers, new triggers and shared counters after down."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('down_continuations',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from calculator.buff_manager import BuffManager
from calculator import timeline
rows=[]
for case in ('registered-dot','registered-heal','new-every-trigger','normal-shots-stop','global-ammo-counter','personal-attack-counter'):
 b=v.body(2);b['enemy']['patterns']=[dict(id='lethal',kind='attack',delay=.35,until={'time':.1},spec=dict(coeff=100,atk=100000000,target='slot:1'))]
 extra={v.NAMES[0]:[],v.NAMES[1]:[]};owner=v.NAMES[0]
 if case=='registered-dot':extra[owner]=[v.E('observed dot','damage','dot_damage',100,'target',tick_interval=.2,duration=1)]
 if case=='registered-heal':extra[owner]=[v.B('room for healing','max_hp_only_pct',100,'all_allies'),v.E('observed heal','instant','heal_hp_pct',1,'all_allies',tick_interval=.2,duration=1)]
 if case=='new-every-trigger':extra[owner]=[v.B('observed every','atk_pct',5,'all_allies',event='every:0.2s',duration=.4)]
 if case.endswith('counter'):
  timing='squad_ammo_consume:10' if case.startswith('global') else 'on_attack_count:10'
  extra[owner]=[v.B('observed counter','atk_pct',1,'all_allies',event=timing,max_stack=100)]
  extra[v.NAMES[1]]=[v.E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]
 callbacks=[];activations=[];dispatches=[];captured={}
 damage_register=BuffManager.register_damage_handler;activate=BuffManager._activate;dispatch=BuffManager._dispatch_instant
 def registered(self,fn):
  def observed(eff,caster,t):
   if eff.get('name')=='observed dot':callbacks.append(dict(name=eff['name'],caster=caster,time=t,down=self.is_down(caster)))
   return fn(eff,caster,t)
  return damage_register(self,observed)
 def activated(self,eff,caster,t,*args,**kwargs):
  if str(eff.get('name','')).startswith('observed '):activations.append(dict(name=eff['name'],caster=caster,time=t,down=self.is_down(caster),counts=copy.deepcopy(self._event_counts)))
  return activate(self,eff,caster,t,*args,**kwargs)
 def dispatched(self,eff,caster,t,from_tick=False):
  if eff.get('name')=='observed heal':dispatches.append(dict(name=eff['name'],caster=caster,time=t,down=self.is_down(caster),from_tick=from_tick))
  return dispatch(self,eff,caster,t,from_tick=from_tick)
 code=timeline.simulate.__code__
 def trace(frame,event,arg):
  if frame.f_code is not code:return None
  if event=='return':captured.update(state=copy.deepcopy({k:frame.f_locals['state'].get(k) for k in ('down','hp','hp_pct')}),hits=[dict(time=h.t,caster=h.caster) for h in arg.hits if h.caster==owner])
  return trace
 previous=sys.gettrace()
 with v.context('controlled',extra),patch.object(BuffManager,'register_damage_handler',registered),patch.object(BuffManager,'_activate',activated),patch.object(BuffManager,'_dispatch_instant',dispatched):
  try:sys.settrace(trace);cpu=v.v.a.evaluate(b)
  finally:sys.settrace(previous)
 final=captured['state'];revived=case.endswith('counter')
 assert (owner in final['down'])!=revived
 if not revived:assert final['hp'][owner]==0
 if case=='registered-dot':assert any(c['time']>.35 and c['down'] for c in callbacks)
 if case=='registered-heal':assert any(c['time']>.35 and c['down'] and c['from_tick'] for c in dispatches)
 if case=='new-every-trigger':assert activations and all(c['time']<.35 for c in activations)
 if case=='normal-shots-stop':assert captured['hits'] and all(h['time']<=.35+1e-9 for h in captured['hits'])
 if revived:
  after=[c for c in activations if c['time']>=.8];assert after
  key='__squad__' if case.startswith('global') else owner;event='squad_ammo_consume' if case.startswith('global') else 'on_attack'
  assert all(c['counts'][key][event]%10==0 for c in after),(case,after)
 final['down']=sorted(final['down'])
 row=dict(name=case,cpu_reference_verified=True,gpu_implemented=False,total=cpu['total_damage'],callbacks=callbacks,instant_dispatches=dispatches,activation_attempts=activations,final_state=final,owner_hit_times=captured['hits'])
 rows.append(row);print(json.dumps(dict(name=case,cpu_reference_verified=True,gpu_implemented=False,post_down_dot_ticks=sum(c['down'] for c in callbacks),post_down_instant_ticks=sum(c['down'] and c['from_tick'] for c in dispatches),activation_times=[c['time'] for c in activations])),flush=True)
files=['scripts/audit-down-continuations.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-down-continuations-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
