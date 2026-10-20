"""Read native override semantics while the fixed transport gates are running.

This is CPU characterization only, never a GPU effect-admission claim.
"""
import copy,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES
from calculator.timeline import CharState

def main():
 rows=[]
 for target in ('self','all_allies','all_allies_excl_self'):
  for code in (None,'','전격','작열','unknown:code'):
   for value in (None,0,-10,100):
    e=dict(name='override',type='buff',stat='element_code_override',source='스킬1',target=target,target_code='전격',duration=1,trigger=dict(timing=['battle_start'],condition=[]))
    if value is not None:e['fixed_value']=value
    bm=manager([e]);bm.notify('battle_start',0,NAMES[0]);times=[]
    for t in (0,.999,1,1.001):
     bm.tick(t);override=[bm.element_override_match(n,code) for n in NAMES]
     members=[n for ab in bm._active if ab.effect.get('stat')=='element_code_override' for n in ab.target_chars or []]
     assert override==[bool(code) and code=='전격' and n in members for n in NAMES]
     expected=NAMES[:1] if target=='self' else NAMES if target=='all_allies' else NAMES[1:]
     assert members==(list(expected) if t<1 else []),(target,t,members)
     for base in (False,True):
      for i,n in enumerate(NAMES):
       cs=object.__new__(CharState);cs.name=n;cs.enemy_code=code;cs.base_element_match=base
       assert cs.element_match(bm)==(base or override[i])
     times.append(dict(time=t,override=override,recipient_names=members))
    rows.append(dict(target=target,enemy_code=code,fixed_value=value,observations=times))
 # Characterize native permanent-condition behavior directly; do not assume the
 # normal numeric-buff query filter is also used by this presence helper.
 conditional=[]
 for duration in (-1,1):
  for timing in ('passive','battle_start'):
   e=dict(name='conditional',type='buff',stat='element_code_override',source='스킬1',target='self',target_code='전격',duration=duration,trigger=dict(timing=[timing],condition=['self_state:missing']))
   bm=manager([e]);bm.notify('battle_start',0,NAMES[0]);bm.tick(0)
   conditional.append(dict(duration=duration,timing=timing,override=bm.element_override_match(NAMES[0],'전격'),active=len(bm._active)))
 lazy=[]
 for target in ('allies_top_atk:1','allies_lowest_hp:1'):
  e=dict(name='lazy-override',type='buff',stat='element_code_override',source='스킬1',target=target,target_code='전격',duration=1,trigger=dict(timing=['battle_start'],condition=[]))
  bm=manager([e]);bm.notify('battle_start',0,NAMES[0]);bm.tick(0)
  before=[bm.element_override_match(n,'전격') for n in NAMES]
  for n in NAMES:bm.get_buffs(n,'__enemy__',0)
  after=[bm.element_override_match(n,'전격') for n in NAMES]
  lazy.append(dict(target=target,before_numeric_queries=before,after_numeric_queries=after,target_names=[ab.target_chars for ab in bm._active]))
 authored=json.loads((R/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())
 effects=[dict(character=n,effect=e) for n,es in authored.items() for e in es if e.get('stat')=='element_code_override']
 files=['research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','tests/test_target_counter_runtime.py','research/characterize-element-override.py']
 result=dict(passed=True,cpu_only=True,gpu_execution_performed=False,gpu_admission_enabled=False,cases=len(rows),rows=rows,conditional_presence=conditional,lazy_presence=lazy,authored_effects=effects,rules=['Presence, not numeric amount or sign, grants override to active resolved recipients','Missing/empty enemy code returnsfalse; exact strings match','Base roster element advantage is ORed with live override','Override does not change roster element identity','Native active carrier expiry and membership are authoritative; characterize query filters separately'],source_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in files})
 (R/'research/portable-element-override-native-characterization.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('native',len(rows),'cases; conditional',conditional)
if __name__=='__main__':main()
