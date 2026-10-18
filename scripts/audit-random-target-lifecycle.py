"""CPU target-resolution timing, budgets and periodic dispatch references."""
import copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('target_lifecycle',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.E;OWNER=v.NAMES[0]
def scenarios():
 def buff(**kw):return E('random buff','buff','atk_pct',20,'allies_random:1',event='every:1s',duration=.5,**kw)
 yield 'buff-no-budget',[buff()]
 yield 'buff-budget-two',[buff(max_trigger=2)]
 yield 'exhausted-budget-no-draw',[buff(max_trigger=0)]
 yield 'list-children-no-string-probe',[{**buff(max_trigger=2),'target':['allies_random:1','allies_random:1']}]
 harm=E('harm','buff','atk_pct',-30,'all_allies',polarity='harmful')
 yield 'cleanse-budget-two',[harm,E('random cleanse','instant','debuff_cleanse',1,'allies_random_with_debuff:2',event='every:1s',max_trigger=2)]
 yield 'empty-probe-keeps-budget',[{**harm,'trigger':{'timing':['every:2s'],'condition':[]}},E('random cleanse','instant','debuff_cleanse',1,'allies_random_with_debuff:2',event='every:1s',max_trigger=1)]
 yield 'periodic-instant-no-budget',[E('periodic heal','instant','heal_hp_pct',1,'allies_random:1',tick_interval=.5,duration=3)]
 yield 'periodic-instant-lazy-budget-no-registration-probe',[E('periodic heal','instant','heal_hp_pct',1,'allies_random:1',tick_interval=.5,duration=3,max_trigger=1)]
 yield 'periodic-cleanse-eager-budget-registration-probe',[harm,E('periodic cleanse','instant','debuff_cleanse',1,'allies_random_with_debuff:2',tick_interval=.5,duration=3,max_trigger=1)]
 yield 'periodic-damage-lazy-carrier',[E('periodic damage','damage','dot_damage',100,'allies_random:1',tick_interval=.5,duration=3)]
 yield 'failed-condition-no-draw',[{**buff(),'trigger':{'timing':['every:1s'],'condition':['self_state:unregistered']}}]
 yield 'same-owner-time-lazy-targets-share-one-draw',[E('first lazy','buff','atk_pct',20,'allies_random:1'),E('second lazy','buff','crit_dmg',30,'allies_random:1')]
 yield 'removed-carrier-cache-survives-later-group',[
  E('old lazy A','buff','atk_pct',20,'allies_random:1',event='passive',condition=['self_state:gate A']),
  E('old lazy B','buff','crit_dmg',30,'allies_random:1',event='passive',condition=['self_state:gate B']),
  E('gate A','buff','',0,event='every:1s',max_trigger=1),
  E('remove first','instant','remove_named_buff',0,event='every:2s',target_effect='old lazy A',max_trigger=1),
  E('later lazy C','buff','atk_pct',50,'allies_random:1',event='every:2s',max_trigger=1),
  E('gate B','buff','',0,event='every:3s',max_trigger=1)]

def main():
 from calculator.buff_manager import BuffManager
 original=BuffManager._resolve_target;init=BuffManager.__init__;resolve_lazy=BuffManager._resolve_lazy;cases=[]
 for seed in (0,12345):
  for name,effects in scenarios():
   observed=[];managers=[];lazy=[]
   def construct(self,*args,**kw):init(self,*args,**kw);managers.append(self)
   def target(self,rule,caster,*args,**kw):
    frame=sys._getframe(1);result=original(self,rule,caster,*args,**kw)
    if isinstance(rule,str) and rule.startswith(('allies_random:','allies_random_with_debuff:')):
     observed.append({'time':self._cur_t,'target':rule,'selected':list(result),'caller':frame.f_code.co_name,'line':frame.f_lineno})
    return result
   def lazy_target(self,ab):
    needed=ab.target_chars is None;key=(ab.caster,ab.activated_at,str(ab.effect.get('target','self')));hit=key in self._lazy_target_cache
    result=resolve_lazy(self,ab)
    if needed:lazy.append({'name':ab.effect.get('name'),'time':self._cur_t,'activation_time':ab.activated_at,'cache_hit':hit,'targets':list(ab.target_chars or [])})
    return result
   state=random.getstate();random.seed(seed);initial=list(random.getstate()[1]);body=v.c.body_for(v.NAMES,5,True);body['seed']=seed
   try:
    with v.c.p.custom_effects({OWNER:effects}),patch.object(BuffManager,'__init__',construct),patch.object(BuffManager,'_resolve_target',target),patch.object(BuffManager,'_resolve_lazy',lazy_target):result=v.c.a.evaluate(body)
    final=list(random.getstate()[1])
   finally:random.setstate(state)
   manager=managers[-1];budgets={e['name']:manager._trigger_counts.get(id(e),0) for e,_ in manager._effects if 'max_trigger' in e}
   if name in ('exhausted-budget-no-draw','failed-condition-no-draw'):assert not observed and initial==final
   if name=='buff-budget-two':assert len(observed)==2,(name,len(observed),observed)
   if name=='list-children-no-string-probe':assert len(observed)==4
   if name=='same-owner-time-lazy-targets-share-one-draw':assert len(observed)==1
   if name=='periodic-cleanse-eager-budget-registration-probe':assert len(observed)==6
   if name=='removed-carrier-cache-survives-later-group':
    first=next(r for r in lazy if r['name']=='old lazy A');last=next(r for r in lazy if r['name']=='old lazy B')
    assert last['cache_hit'] and last['targets']==first['targets'] and len(observed)==2,(lazy,observed)
   cases.append(dict(name=name,seed=seed,input=body,authored_effects={OWNER:effects},target_observations=observed,lazy_resolutions=lazy,budgets=budgets,initial_state=initial,final_state=final,cpu_total=result['total_damage']))
   print(json.dumps({'name':name,'seed':seed,'target_calls':len(observed),'budgets':budgets}),flush=True)
 files=['scripts/audit-random-target-lifecycle.py','scripts/audit-debuff-cleanse.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,cpu_trace_used_as_gpu_input=False,cases=cases,
             note='Authored effects, seed and initial state are inputs; recipient choices, budgets, totals and final states are oracle outputs only.',
             source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/'research/detail-random-target-lifecycle-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
