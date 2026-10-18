"""Read-only CPU references for the next integrated down/revive state machine.

No active combat query is added by an observer. These are not GPU successes.
"""
import copy,hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('down_reference',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from calculator.buff_manager import BuffManager
from calculator.timeline import CharState
rows=[]
for case in ('down','revive','preserve-marker','restore-passive-not-periodic','shared-passive-no-double-stack','once-only-revive','no-hp-threshold-on-revive','whole-squad-hit-order'):
 b=v.body(1);b['enemy']['patterns']=[dict(id='lethal',kind='attack',delay=.1,until={'time':.7},spec=dict(coeff=100,atk=100000000,target='all' if case=='whole-squad-hit-order' else 'slot:1',hits=2 if case=='once-only-revive' else 1,interval=.3))]
 extra={v.NAMES[0]:[v.B('own permanent','atk_pct',10),v.B('shared permanent','atk_pct',10,target='all_allies',max_stack=3)],v.NAMES[1]:[]}
 if case!='down':extra[v.NAMES[1]].append(v.E('revive ally','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
 if case=='preserve-marker':extra[v.NAMES[0]].append(v.B('preserved','atk_pct',7,persist_on_revive=True))
 if case=='restore-passive-not-periodic':extra[v.NAMES[0]]+=[v.B('passive hp','max_hp_pct',25),v.B('periodic permanent','atk_pct',5,event='every:0.03s')]
 if case=='no-hp-threshold-on-revive':extra[v.NAMES[0]].append(v.B('low hp reaction','atk_pct',77,event='hp_below:60'))
 events=[];states=[];actions=[]
 def snapshot(self,event,name,t):
  state=self.state
  return dict(event=event,name=name,time=t,down=sorted(state.get('down',[])),hp=copy.deepcopy(state['hp']),hp_pct=copy.deepcopy(state['hp_pct']),active=[dict(name=a.effect.get('name',''),caster=a.caster,targets=copy.deepcopy(a.target_chars),stacks=a.stack) for a in self._active],counts=copy.deepcopy(self._event_counts))
 notify=BuffManager.notify;knock=BuffManager.knock_down;revive=BuffManager.revive;on_down=CharState.on_down;on_revive=CharState.on_revive
 def notified(self,event,t,caster,**kw):
  if event in ('received_hit','event:lethal_hit','event:self_down','event:ally_down') or event.startswith('hp_below:'):events.append(dict(event=event,time=t,caster=caster))
  return notify(self,event,t,caster,**kw)
 def knocked(self,name,t):
  states.append(snapshot(self,'before-down',name,t));result=knock(self,name,t);states.append(snapshot(self,'after-down',name,t));return result
 def revived(self,name,t,pct):
  states.append(snapshot(self,'before-revive',name,t));result=revive(self,name,t,pct);states.append(snapshot(self,'after-revive',name,t));return result
 def action(self,t,bm,fn,event):
  result=fn(self,t,bm);actions.append(dict(event=event,time=t,name=self.name,ammo=self.ammo,next_fire=self.next_fire_time,reload_until=self.reloading_until,charge_full=self._charge_full_t,hold_release=self._hold_release_t));return result
 with v.context('controlled',extra),patch.object(BuffManager,'notify',notified),patch.object(BuffManager,'knock_down',knocked),patch.object(BuffManager,'revive',revived),patch.object(CharState,'on_down',lambda self,t,bm:action(self,t,bm,on_down,'down')),patch.object(CharState,'on_revive',lambda self,t,bm:action(self,t,bm,on_revive,'revive')):
  cpu=v.v.a.evaluate(b)
 downs=[s for s in states if s['event']=='after-down'];ups=[s for s in states if s['event']=='after-revive']
 assert downs and all(s['hp'][s['name']]==0 and s['name'] in s['down'] for s in downs)
 assert len(ups)==(0 if case=='down' else 1),(case,len(ups))
 for up in ups:assert up['hp'][up['name']]>0 and up['name'] not in up['down']
 for act in actions:assert act['reload_until']==-1 and act['charge_full']==-1 and act['hold_release']==-1
 if case=='preserve-marker':assert any(a['name']=='preserved' and v.NAMES[0] in (a['targets'] or []) for a in downs[0]['active'])
 if case=='restore-passive-not-periodic':
  up=ups[0];assert any(a['name']=='passive hp' for a in up['active']) and not any(a['name']=='periodic permanent' and v.NAMES[0] in (a['targets'] or []) for a in up['active'])
 if case=='shared-passive-no-double-stack':
  shared=[a for a in ups[0]['active'] if a['name']=='shared permanent'];assert len(shared)==1 and shared[0]['stacks']==1 and shared[0]['targets'][-1]==v.NAMES[0]
 if case=='once-only-revive':assert len(downs)==2 and len(ups)==1
 if case=='no-hp-threshold-on-revive':assert not any(e['event'].startswith('hp_below:') for e in events)
 if case=='revive':
  broadcast=[e['caster'] for e in events if e['event']=='event:ally_down'];assert broadcast==v.NAMES[1:],broadcast
 rows.append(dict(name=case,cpu_reference_verified=True,gpu_implemented=False,total=cpu['total_damage'],events=events,states=states,actions=actions))
 print(json.dumps(dict(name=case,downs=len(downs),revives=len(ups),cpu_reference_verified=True,gpu_implemented=False)),flush=True)
files=['scripts/audit-down-revive.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-down-revive-cpu-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
