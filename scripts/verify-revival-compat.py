"""CPU bridge acceptance before comparing the staged survival GPU runtime."""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v=load('revival_compat_oracle','scripts/verify-incoming-detail.py')
import engine_compat
engine_compat.install();engine_compat.install()
from calculator.buff_manager import BuffManager
from calculator import timeline
rows=[]
for character in ('앨리스','솔린','크라운'):
 names=[character]+[n for n in v.NAMES if n!=character][:4];b=v.body(1,True,names);b['burst_gauge_mode']='fixed'
 b['enemy']['patterns']=[dict(id='lethal',kind='attack',delay=.35,until={'time':.1},spec=dict(coeff=100,atk=100000000,target='slot:1',pierce=True))]
 extra={names[-1]:[v.E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]}
 with v.context('raw-probe',extra):r=v.v.a.evaluate(b)
 assert any(h['down'] for h in r['incoming_hits'])
 rows.append(dict(name='raw-'+character,passed=True,total=r['total_damage'],gpu_implemented=False))
for pct in (50,100):
 b=v.body(1);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[dict(id='lethal',kind='attack',delay=.35,until={'time':.1},spec=dict(coeff=100,atk=100000000,target='slot:1',pierce=True))]
 owner=v.NAMES[0];extra={owner:[v.B('larger maximum','max_hp_pct',25),v.B('healthy','atk_pct',50,event='passive',condition=['self_hp_above:80']),v.B('low threshold','atk_pct',77,event='hp_below:60')],v.NAMES[1]:[v.E('late revive','instant','revive',pct,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1),v.B('adjacent threshold','atk_pct',88,event='event:adjacent_hp_below:60')]}
 captured={};thresholds=[];original_notify=BuffManager.notify;code=timeline.simulate.__code__
 def notified(self,event,t,caster,**kw):
  if event.startswith(('hp_below:','event:adjacent_hp_below:')):thresholds.append(dict(event=event,time=t,caster=caster))
  return original_notify(self,event,t,caster,**kw)
 def trace(frame,event,arg):
  if frame.f_code is not code:return None
  if event=='return':
   bm=frame.f_locals['bm'];captured.update(hp=bm.state['hp'][owner],pct=bm.state['hp_pct'][owner],down=owner in bm.state.get('down',set()),max_hp=bm.effective_max_hp(owner),atk_pct=bm.get_buffs(owner,'__enemy__',1).get('atk_pct',0))
  return trace
 previous=sys.gettrace()
 with v.context('controlled',extra),patch.object(BuffManager,'notify',notified):
  try:sys.settrace(trace);result=v.v.a.evaluate(b)
  finally:sys.settrace(previous)
 assert not captured['down'] and math.isclose(captured['pct'],pct,abs_tol=1e-10)
 assert math.isclose(captured['hp'],captured['max_hp']*pct/100,abs_tol=1e-8)
 assert captured['atk_pct']==(50 if pct==100 else 0),captured
 assert not thresholds,thresholds
 rows.append(dict(name='controlled-revive-'+str(pct),passed=True,state=captured,threshold_events=thresholds,gpu_implemented=False))
files=['scripts/verify-revival-compat.py','app/survival_compat.py','scripts/probe-revive-hp-passives.py','scripts/verify-incoming-detail.py','app/engine_compat.py','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,gpu_implemented=False,cases=rows,scope='Production CPU revival HP-condition fix, raw Alice/Soline/Crown and controlled HP thresholds. Not survival GPU parity.',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-survival-cpu-compat-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(rows),gpu_implemented=False)))
