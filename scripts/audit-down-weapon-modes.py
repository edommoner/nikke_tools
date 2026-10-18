"""Raw Modernia/Maxwell weapon-mode down/revive CPU references, no GPU claim."""
import hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('down_weapon_modes',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from calculator.buff_manager import BuffManager
from calculator.timeline import CharState
rows=[]
for character in ('모더니아','맥스웰'):
 for restore in (False,True):
  names=[v.NAMES[0],v.NAMES[1],character,v.NAMES[3],v.NAMES[4]];b=v.body(8,True,names);b['burst_gauge_mode']='fixed'
  b['enemy']['patterns']=[dict(id='lethal',kind='attack',delay=3.8,until={'time':.1},spec=dict(coeff=100,atk=100000000,target='slot:3',pierce=True))]
  extra={names[-1]:[v.E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]} if restore else {}
  events=[];ticks=[];knock=BuffManager.knock_down;end=BuffManager.end_weapon_change;down=CharState.on_down;up=CharState.on_revive;tick=CharState.tick
  def actor_state(self):return {k:getattr(self,k) for k in ('ammo','next_fire_time','reloading_until','_in_weapon_change','_wc_shots','_wc_ammo_restored','_charge_phase','_charge_full_t','_hold_release_t')}
  def knocked(self,name,t):
   if name==character:
    mode=self.state.get('weapon_change',{}).get(name);events.append(dict(event='before-down',time=t,mode_name=(mode or {}).get('effect',{}).get('name',''),hp=self.state['hp'][name]))
   return knock(self,name,t)
  def ended(self,name,t=None):
   if name==character:events.append(dict(event='end-mode',time=t,already_down=self.is_down(name)))
   return end(self,name,t)
  def action(self,t,bm,fn,label):
   result=fn(self,t,bm)
   if self.name==character:events.append(dict(event=label,time=t,down=bm.is_down(self.name),state=actor_state(self)))
   return result
  def ticked(self,t,bm,enemy,cfg):
   result=tick(self,t,bm,enemy,cfg)
   if self.name==character:
    if bm.is_down(self.name):assert not result
    if abs(t-3.8)<.04 or abs(t-5.5)<.08:ticks.append(dict(time=t,down=bm.is_down(self.name),state=actor_state(self),hits=len(result)))
   return result
  with v.context('raw-mode',extra),patch.object(BuffManager,'knock_down',knocked),patch.object(BuffManager,'end_weapon_change',ended),patch.object(CharState,'on_down',lambda self,t,bm:action(self,t,bm,down,'after-down')),patch.object(CharState,'on_revive',lambda self,t,bm:action(self,t,bm,up,'after-revive')),patch.object(CharState,'tick',ticked):cpu=v.v.a.evaluate(b)
  entered=[e for e in events if e['event']=='before-down'];assert len(entered)==1 and entered[0]['mode_name'],(character,entered)
  exits=[e for e in events if e['event']=='end-mode' and abs(e['time']-3.8)<1e-6];assert exits and all(e['already_down'] for e in exits)
  for e in events:
   if e['event'] in ('after-down','after-revive'):assert e['state']['reloading_until']==-1 and e['state']['_charge_full_t']==-1 and e['state']['_hold_release_t']==-1
  revived=[e for e in events if e['event']=='after-revive'];assert len(revived)==int(restore)
  if restore:assert any(t['time']>=revived[0]['time'] and not t['state']['_in_weapon_change'] and not t['down'] for t in ticks)
  rows.append(dict(character=character,revive=restore,cpu_reference_verified=True,gpu_implemented=False,total=cpu['total_damage'],events=events,action_ticks=ticks))
  print(json.dumps(dict(character=character,revive=restore,mode_at_down=entered[0]['mode_name'],cpu_reference_verified=True,gpu_implemented=False),ensure_ascii=True),flush=True)
files=['scripts/audit-down-weapon-modes.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-down-weapon-modes-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
