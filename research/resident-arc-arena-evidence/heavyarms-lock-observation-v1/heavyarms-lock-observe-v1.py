"""Passive observation of original full25 named-carrier behavior; GPU0."""
import copy,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path.cwd();BASE=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
import engine_worker
from calculator.buff_manager import BuffManager
original_activate=BuffManager._activate;original_state=BuffManager.enemy_has_state;original_any=BuffManager._has_target_state;original_buffs=BuffManager.get_buffs
activate=[];queries=[];numeric=[]
def activation(manager,effect,caster,t,*args,**kwargs):
 result=original_activate(manager,effect,caster,t,*args,**kwargs)
 if effect.get('stat')=='lock_on':
  active=[dict(caster=a.caster,targets=list(a.target_chars or []),stack=a.stack,expires='infinite' if math.isinf(a.expires_at) else a.expires_at) for a in manager._active if a.effect.get('name')==effect.get('name')]
  activate.append(dict(time=t,caster=caster,name=effect.get('name'),active=active))
 return result
def state(manager,enemy,name):
 result=original_state(manager,enemy,name)
 if name=='록 온':queries.append(dict(query='enemy_has_state',target=enemy,value=result))
 return result
def any_state(manager,name):
 result=original_any(manager,name)
 if name=='록 온':queries.append(dict(query='any_target_state',value=result))
 return result
def buffs(manager,caster,target,t,*args,**kwargs):
 result=original_buffs(manager,caster,target,t,*args,**kwargs)
 if 'lock_on' in result:numeric.append(dict(time=t,caster=caster,target=target,value=result['lock_on']))
 return result
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
with cli.forbid_gpu():
 spec=importlib.util.spec_from_file_location('lock_factory',ROOT/'research/verify-world-projectile-rosters.py');factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
 name='스노우 화이트 : 헤비암즈';body=dict(factory.body_for(factory.policy.roster_for(name),30),burst_gauge_mode='accumulate',seed=2427)
 prepared=engine_worker.evaluate(dict(body,_portable_static_inputs=True));skills=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())[name];assert len(skills)==25
 before=copy.deepcopy(body);started=time.perf_counter()
 with patch.object(BuffManager,'_activate',activation),patch.object(BuffManager,'enemy_has_state',state),patch.object(BuffManager,'_has_target_state',any_state),patch.object(BuffManager,'get_buffs',buffs):observed=factory.native_reference(body)
 observed_seconds=time.perf_counter()-started;assert body==before
 started=time.perf_counter();baseline=factory.native_reference(body);baseline_seconds=time.perf_counter()-started
 assert observed==baseline,'Passive observer changed the complete native result or shot trace'
 result=dict(schema='heavyarms-lock-observation-v1',passed=True,character=name,original_skill_definitions=25,prepared_definitions=len(prepared['effects']),observed_seconds=observed_seconds,baseline_seconds=baseline_seconds,native_result_and_shots_equal=True,native_sha256=digest(observed),activation_calls=len(activate),active_marker_samples=sum(bool(r['active']) for r in activate),named_query_calls=len(queries),named_query_true=sum(bool(r['value']) for r in queries),numeric_reader_samples=len(numeric),activate=activate,queries=queries,numeric=numeric,gpu_calls=0,gpu_supported=False,full_character_verified=False,scope='Native logical named-marker observation only; dedicated Lock On selection, target-count extension and typed projectile full25 remain unverified')
 with (BASE/'heavyarms-lock-observe-v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k not in ('activate','queries','numeric')},ensure_ascii=False,indent=2))
