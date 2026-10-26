"""Explore full original25 through the existing opt-in projectile input path."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
ROOT=Path.cwd();BASE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_typed_input import compile_coordinate_typed
import engine_worker
from calculator import timeline
s=importlib.util.spec_from_file_location('roster_factory',ROOT/'research/verify-world-projectile-rosters.py');factory=importlib.util.module_from_spec(s);s.loader.exec_module(factory)
character='스노우 화이트 : 헤비암즈';calls=dict(cpu_battle=0,gpu=0);rows=[];diagnostics=[]
import portable_runtime
original_validate=portable_runtime.validate_effect
def diagnostic_validate(effect,*args,**kwargs):
 try:return original_validate(effect,*args,**kwargs)
 except BaseException:
  diagnostics.append({k:effect.get(k) for k in ('name','type','stat','target','source')});raise

def stop(*args,**kwargs):calls['cpu_battle']+=1;raise AssertionError('Static packing forbids native battle')
try:
 with cli.forbid_gpu(),patch.object(timeline,'simulate',stop),patch.object(timeline.CharState,'tick',stop),patch.object(portable_runtime,'validate_effect',diagnostic_validate):
  original=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())[character]
  assert len(original)==25
  for duration in (3,30):
   for capacity in (1.,1e12):
    body=dict(factory.body_for(factory.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=2427)
    literal=dict(name=f'original-projectile-full/{duration}s/capacity{capacity:g}',body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='declared-projectiles',kind='idle',until=dict(time=duration+1))])
    c,p=prepare_case(literal);before=copy.deepcopy(p)
    matches=[i for i,item in enumerate(p['effects']) if item['owner']==character and item['effect'].get('target')=='all_projectiles'];assert len(matches)==1
    probe=matches[0];effect=p['effects'][probe]['effect'];assert effect['name']==original[24]['name'] and effect['target']=='all_projectiles'
    bindings=[dict(node='declared-projectiles',kind=2,identity=i+1,capacity=capacity,label=f'original-projectile:{i+1}') for i in range(3)]
    words,meta,actors,scene=compile_coordinate_typed(p,bindings,probe,max_attacks=128)
    assert p==before and len(words)==115680 and meta['coordinate_original_input']['all_effects_included']
    assert set(meta['binding_source_indices'])==set(range(len(p['effects'])))
    owners=[item['effect'] for item in p['effects'] if item['owner']==character]
    assert [e['name'] for e in owners[:25]]==[e['name'] for e in original]
    rows.append(dict(name=c['name'],character=character,original_skill_definitions=25,prepared_definitions=len(p['effects']),prepared_owner_definitions=len(owners),probe_source=probe,probe_name=effect['name'],input_words=len(words),bound_definitions=len(meta['binding_source_indices']),all_original_definitions_included=True,input_sha256=hashlib.sha256(__import__('array').array('I',words).tobytes()).hexdigest()))
 result=dict(schema='original-projectile-full-static-v1',passed=True,rows=rows,forbidden_calls=calls,diagnostics=diagnostics,gpu_admission_verified=False,calculation_verified=False,full_character_verified=False,scope='Static full25 original profile packing through existing declared three-projectile model; no battle or GPU proof')
except BaseException as error:
 result=dict(schema='original-projectile-full-static-v1',passed=False,completed=rows,error=type(error).__name__+': '+str(error),forbidden_calls=calls,diagnostics=diagnostics,gpu_admission_verified=False,calculation_verified=False)
 with (BASE/'heavyarms-full-static-v3.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 raise
with (BASE/'heavyarms-full-static-v3.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
