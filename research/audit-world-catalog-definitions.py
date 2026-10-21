"""Real base/favorite definition inventory; no simulation, GPU or support enabling."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker as adapter
import portable_backend
from calculator import timeline
from detail_coverage import body_for
from portable_runtime import validate_effect
def main():
 names=[n for n,d in adapter.META.items() if isinstance(d,dict) and not n.startswith(('_','test_')) and not adapter.spec.is_preview(n)]
 rows=[];issues=Counter();calls=dict(cpu_battle=0,gpu_build=0,gpu_execute=0)
 def forbidden(kind):
  def stop(*args,**kwargs):calls[kind]+=1;raise AssertionError('Forbidden in static world inventory:'+kind)
  return stop
 with patch.object(timeline,'simulate',forbidden('cpu_battle')),patch.object(portable_backend,'build',forbidden('gpu_build')),patch.object(portable_backend,'execute',forbidden('gpu_execute')),patch.object(portable_backend,'execute_batches',forbidden('gpu_execute')):
  for name in names:
   stages=(0,1,2,3) if adapter.META[name].get('favorite_item') else (0,)
   for stage in stages:
    roster=[name]+[n for n in ('모더니아','루주','마스트 : 로망틱 메이드','도라','얀') if n!=name][:4]
    body=body_for(roster,1);body['profile']['chars'][name]['favorite_stage']=stage
    if stage:body['profile']['chars'][name]['collection_stage']='SR15'
    prepared=adapter.evaluate(dict(body,_portable_static_inputs=True));assert prepared['cpu_battle_executed'] is False and prepared['all_character_effects_included'] is True
    definitions=[]
    for item in prepared['effects']:
     if item['owner']!=name:continue
     e=item['effect'];issue=None
     try:validate_effect(e,combat=dict(weapons=prepared['weapons']),world_frame=True)
     except (ValueError,TypeError) as error:issue=str(error);issues[issue]+=1
     definitions.append(dict(name=e.get('name'),type=e.get('type'),stat=e.get('stat'),target=e.get('target'),source=e.get('source'),fields=sorted(e),timings=e.get('trigger',{}).get('timing',[]),conditions=e.get('trigger',{}).get('condition',[]),preflight_passed=issue is None,issue=issue))
    rows.append(dict(character=name,favorite_stage=stage,own_effect_count=len(definitions),all_own_definitions_preflight_passed=all(x['preflight_passed'] for x in definitions),definitions=definitions,complete_roster_effect_count=len(prepared['effects']),cpu_battle_executed=False,gpu_execution_performed=False,full_character_verified=False))
 assert len(names)==203 and len(rows)==266 and calls==dict(cpu_battle=0,gpu_build=0,gpu_execute=0)
 tracked=[ROOT/'research/audit-world-catalog-definitions.py']+[p for p in (ROOT/'app').glob('*.py')]
 tracked += [p for p in (ROOT/'research/upstream/nikke-calc-master/data').glob('*.json')]
 result=dict(passed=True,catalog_characters=203,base_and_favorite_profiles=266,all_favorite_item_characters=21,base_own_effect_preflight_passed=sum(x['all_own_definitions_preflight_passed'] for x in rows if x['favorite_stage']==0),all_profile_own_effect_preflight_passed=sum(x['all_own_definitions_preflight_passed'] for x in rows),issues=dict(issues.most_common()),profiles=rows,forbidden_calls=calls,assumptions='Real complete owned/growth preparation; favorite0 for all203 and favorite1/2/3 for all21 favorite-item characters; fixed real five-member roster, no cube; definition validation only. GPU kind admission, policy wiring, capacities and full battle parity remain unproven.',source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(tracked))},normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-catalog-definition-readiness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('catalog_characters','base_and_favorite_profiles','base_own_effect_preflight_passed','all_profile_own_effect_preflight_passed','forbidden_calls')},ensure_ascii=False))
if __name__=='__main__':main()
