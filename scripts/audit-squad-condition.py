"""Independent CPU references for the next squad-composition predicate port."""
import copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('squad_cpu',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.buff_manager import BuffManager,_NIKKE

def scenarios():
 for timing,duration in [('battle_start',-1),('passive',-1),('burst_cast',5),('every:1s',.5),('on_attack_count:3',.4),('passive',1)]:
  yield timing+'-'+str(duration),[v.E('squad probe','buff','atk_pct',30,'all_allies',event=timing,duration=duration,condition=['squad_ally_exists'])]
 yield 'lazy-random-permanent-passive',[v.E('squad probe','buff','atk_pct',30,'allies_random:1',event='passive',condition=['squad_ally_exists'])]
 yield 'mixed-runtime-gate',[v.E('squad probe','buff','atk_pct',30,'all_allies',event='passive',condition=['squad_ally_exists','self_state:gate']),v.E('gate','buff','',0,event='every:1s',max_trigger=1)]

def main():
 primitive=[]
 for caster,names,down in [
  ('누아르',['누아르','루주'],[]),('누아르',['누아르','리타'],[]),('누아르',['누아르'],[]),
  ('누아르',['누아르','루주'],['루주']),('마스트 : 로망틱 메이드',['마스트 : 로망틱 메이드','헬름 : 아쿠아마린'],[]),
  ('unregistered',['unregistered','another dummy'],[])]:
  bm=BuffManager.__new__(BuffManager);bm.squad_names=names;bm.state={'down':set(down)}
  actual=bm._condition_ok(['squad_ally_exists'],caster,0)
  squad=_NIKKE.get(caster,{}).get('squad');expected=bool(squad and any(n!=caster and _NIKKE.get(n,{}).get('squad')==squad for n in names))
  assert actual==expected
  primitive.append(dict(caster=caster,names=names,down=down,expected=expected,actual=actual))
 cases=[];original=BuffManager.__init__;check=BuffManager._condition_ok
 for buddy in ('루주','리타'):
  names=['누아르',buddy,'크라운','앨리스','모더니아']
  for label,effects in scenarios():
   managers=[];checks=[]
   def construct(self,*args,**kw):original(self,*args,**kw);managers.append(self)
   def condition(self,conditions,caster,t,eff=None):
    result=check(self,conditions,caster,t,eff)
    if eff and eff.get('name')=='squad probe':checks.append(dict(time=t,result=result))
    return result
   body=v.c.body_for(names,6,True);body['seed']=0;state=random.getstate()
   try:
    with v.c.p.custom_effects({names[0]:effects}),patch.object(BuffManager,'__init__',construct),patch.object(BuffManager,'_condition_ok',condition):cpu=v.c.a.evaluate(body)
    final_random=list(random.getstate()[1])
   finally:random.setstate(state)
   active=[dict(name=ab.effect.get('name'),targets=ab.target_chars,stack=ab.stack,runtime=ab.has_runtime_conditions) for ab in managers[-1]._active if ab.effect.get('name')=='squad probe']
   cases.append(dict(name=label,buddy=buddy,has_buddy=buddy=='루주',input=body,authored_effects={names[0]:effects},condition_checks=checks,active_at_end=active,cpu_total=cpu['total_damage'],members=cpu['members'],base_stats=cpu['base_stats'],burst_timeline=cpu['burst_timeline'],final_random_state=final_random))
   print(json.dumps(dict(name=label,has_buddy=buddy=='루주',condition_results=sorted(set(r['result'] for r in checks)),active=len(active),cpu_total=cpu['total_damage'])),flush=True)
 files=['scripts/audit-squad-condition.py','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/data/parsed_nikke.json']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,cpu_trace_used_as_gpu_input=False,primitives=primitive,cases=cases,
 note='Pinned CPU passive-registration semantics are oracle outputs, including any static-condition treatment. No GPU support claim. Current v20 host/kernel remain unchanged.',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/'research/detail-squad-condition-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
