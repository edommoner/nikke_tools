"""CPU-only authored cleanse references; no battle trace is a GPU input."""
import copy,hashlib,importlib.util,json,math,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('cleanse_control',ROOT/'scripts/verify-control-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
E=c.E;NAMES=c.NAMES

def scenarios():
 owner=NAMES[0]
 def harmful(name,value=-20,**kw):return E(name,'buff','atk_pct',value,'all_allies',**{'polarity':'harmful',**kw})
 def cleanse(value,target='all_allies',event='burst_cast'):
  e=E('cleanse','instant','debuff_cleanse',value,target,event=event)
  if value is None:del e['fixed_value']
  return e
 base=[harmful('old harm'),E('negative beneficial','buff','atk_pct',-5,'all_allies',polarity='beneficial'),harmful('new harm',-30),harmful('irremovable',-10,polarity='harmful_irremovable')]
 for value in (1,2,0,-1,None,.5):yield 'per-recipient-limit-'+str(value),{owner:base+[cleanse(value)]},8
 yield 'partial-right-recipients',{owner:base+[cleanse(1,'allies_right:2')]},8
 yield 'duplicate-recipient-does-not-consume-again',{owner:base+[cleanse(1,[NAMES[0],NAMES[0],NAMES[1]])]},8
 yield 'single-recipient-all-harms',{owner:base+[cleanse(0,'self')]},8
 yield 'limited-cleanse-and-state-end-does-not-fire',{owner:base+[E('should not fire','buff','atk_pct',1000,event='event:state_end:old harm'),cleanse(1)]},8
 yield 'oldest-activation-not-definition-order',{owner:[harmful('later registered first',event='every:1s',max_trigger=1),harmful('earlier registered second'),cleanse(1)]},8
 yield 'merged-refresh-does-not-change-priority',{owner:[harmful('merged harm',event='every:1s',max_stack=4),harmful('after merge'),cleanse(1)]},8
 yield 'lazy-unresolved-is-not-stripped',{owner:[E('lazy harm','buff','atk_pct',-50,'allies_top_atk:1',polarity='harmful'),cleanse(0,event='battle_start')]},5
 yield 'lazy-resolved-is-stripped',{owner:[E('lazy harm','buff','atk_pct',-50,'allies_top_atk:1',polarity='harmful'),cleanse(0)]},8
 yield 'partial-bullet-carrier-preserves-maps',{owner:[harmful('bullet harm',duration_bullets=1000),cleanse(1,'self')]},8
 yield 'partial-shield-carrier-preserves-maps',{owner:[E('harmful shield','buff','shield_from_max_hp_pct',50,'all_allies',polarity='harmful'),E('shield gate','buff','atk_pct',100,'all_allies',event='passive',condition=['during_shield']),cleanse(1,'self')]},8
 yield 'runtime-gated-harm-is-still-cleansed',{owner:[harmful('gated harm',event='passive',condition=['during_full_burst']),cleanse(1)]},8
 yield 'periodic-damage-cleanse-retains-timer',{owner:[E('harmful dot','damage','dot_damage',100,'all_allies',polarity='harmful',tick_interval=.5,duration=7),cleanse(0)]},8
 yield 'periodic-cleanse-repeated',{owner:base+[E('periodic cleanse','instant','debuff_cleanse',1,'all_allies',tick_interval=1,duration=4)]},8
 yield 'level-dependent-limit',{owner:base+[dict(source='skill3',name='level cleanse',type='instant',stat='debuff_cleanse',values={'10':2},target='all_allies',trigger={'timing':['burst_cast'],'condition':[]})]},8
 yield 'cleansed-own-stack-dot-with-live-timer',{owner:[E('own stacked dot','damage','dot_damage',100,'all_allies',polarity='harmful',tick_interval=.5,duration=7,scaling='stack_count',max_stack=10),cleanse(0)]},8
 ref=E('growing reference','buff','atk_pct',0,max_stack=10);ref['trigger']['timing']=['battle_start','every:1s']
 yield 'cleansed-captured-dot-falls-back-to-live-reference',{owner:[ref,E('captured dot','damage','dot_damage',100,'all_allies',polarity='harmful',tick_interval=.5,duration=7,scaling='stack_count',scaling_ref='growing reference'),cleanse(0)]},8

def finite(value):return None if isinstance(value,float) and not math.isfinite(value) else value

@contextmanager
def observe():
 from calculator.buff_manager import BuffManager
 dispatch=BuffManager._dispatch_instant;notify=BuffManager.notify;events=[];cleanups=[]
 def snapshot(bm):
  return [{'uid':ab.uid,'name':ab.effect.get('name'),'caster':ab.caster,'stat':ab.effect.get('stat'),'polarity':ab.effect.get('polarity'),'targets':copy.deepcopy(ab.target_chars),'stack':ab.stack,'expires':finite(ab.expires_at),'bullets':copy.deepcopy(ab.bullets_per_target),'shield':copy.deepcopy(ab.shield_per_target)} for ab in bm._active]
 def timers(bm):
  names={id(e):e.get('name') for e,_ in bm._effects}
  return [{'name':names.get(key),'caster':v[0],'next':finite(v[1]),'expires':finite(v[2])} for key,v in bm._dot_timers.items()]
 def instant(self,eff,caster,t,*,from_tick=False):
  if eff.get('stat')!='debuff_cleanse':return dispatch(self,eff,caster,t,from_tick=from_tick)
  before=snapshot(self);before_timers=timers(self);event_at=len(events)
  result=dispatch(self,eff,caster,t,from_tick=from_tick)
  cleanups.append({'time':t,'name':eff['name'],'before':before,'after':snapshot(self),'timers_before':before_timers,'timers_after':timers(self),'notifications':events[event_at:]})
  return result
 def event(self,event,t,caster=None,**kw):
  if event.startswith('event:state_end:'):events.append([event,t,caster])
  return notify(self,event,t,caster,**kw)
 with patch.object(BuffManager,'_dispatch_instant',instant),patch.object(BuffManager,'notify',event):yield cleanups

def main():
 cases=[]
 for name,effects,seconds in scenarios():
  body=c.body_for(NAMES,seconds,True)
  with c.p.custom_effects(effects),observe() as cleanups:result=c.a.evaluate(body)
  assert cleanups,name
  case=dict(name=name,input=body,authored_effects=effects,cleanups=cleanups,cpu_total=result['total_damage'],burst_timeline=result['burst_timeline'])
  cases.append(case)
  print(json.dumps({'name':name,'total':case['cpu_total'],'cleanups':len(cleanups),'first_before':len(cleanups[0]['before']),'first_after':len(cleanups[0]['after']),'state_end_notifications':sum(len(r['notifications']) for r in cleanups)},ensure_ascii=True),flush=True)
 files=['scripts/audit-debuff-cleanse.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
 r=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,cpu_trace_used_as_gpu_input=False,cases=cases,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/'research/detail-cleanse-cpu-references.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
