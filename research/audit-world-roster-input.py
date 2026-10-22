"""Complete prepared five-member inputs for all real base/favorite profiles; GPU0."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts')]
import engine_worker as adapter
import portable_backend
from calculator import timeline
from detail_coverage import body_for
from portable_world_roster_input import compile_world_battle
from portable_readiness import inspect_effects,summarize,issue,diagnostic_sources
from portable_readiness_semantics import work_lanes

def roster_for(name):
 stage=str(adapter.META[name]['burst_stage'])
 fillers={'1':['도라','드레이크','N102','메어리','미란다'],'2':['미란다','드레이크','N102','메어리','도라'],'3':['미란다','도라','N102','메어리','드레이크'],'A':['미란다','도라','드레이크','메어리','N102']}
 if stage not in fillers:raise ValueError('No complete roster policy for stage '+stage)
 return [name]+[n for n in fillers[stage] if n!=name][:4]

def main(*,compiler=compile_world_battle,destination='portable-world-roster-input-readiness.json',quiet=False):
 rows=[];errors=Counter();calls=dict(cpu_battle=0,gpu=0)
 def stop(kind):
  def forbidden(*a,**k):calls[kind]+=1;raise AssertionError('Static inventory forbidden '+kind)
  return forbidden
 with patch.object(timeline,'simulate',stop('cpu_battle')),patch.object(timeline.CharState,'tick',stop('cpu_battle')),patch.object(portable_backend,'execute',stop('gpu')),patch.object(portable_backend,'build',stop('gpu')),patch.object(portable_backend,'execute_batches',stop('gpu')):
  for name,data in adapter.META.items():
   if not isinstance(data,dict) or name.startswith(('_','test_')) or adapter.spec.is_preview(name):continue
   for stage in ((0,1,2,3) if data.get('favorite_item') else (0,)):
    r=dict(character=name,favorite_stage=stage,input_packed=False,gpu_admission_verified=False,full_character_verified=False)
    try:
     body=dict(body_for(roster_for(name),30),burst_gauge_mode='accumulate');body['profile']['chars'][name]['favorite_stage']=stage
     if stage:body['profile']['chars'][name]['collection_stage']='SR15'
     p=adapter.evaluate(dict(body,_portable_static_inputs=True));r['effect_blockers']=inspect_effects(p);w,m=compiler(p)
     import array
     b=array.array('I',w)
     if sys.byteorder!='little':b.byteswap()
     r.update(input_packed=True,input_sha256=hashlib.sha256(b.tobytes()).hexdigest(),squad=body['squad'],prepared_effects=len(p['effects']),bound_effects=len(m['effects']),input_words=len(w))
    except (ValueError,KeyError,TypeError) as error:r['error']=str(error);r['program_issue']=issue(error,phase='program');errors[str(error)]+=1
    rows.append(r)
 assert len(rows)==266 and calls==dict(cpu_battle=0,gpu=0)
 result=dict(passed=True,classification=dict(method='Independent lowered definition validation plus complete program packing',exhaustive_within_effect=False,unlock_counts_are_predictions=False),priorities=summarize(rows),profiles=rows,profile_count=266,base_count=203,packed_profiles=sum(r['input_packed'] for r in rows),packed_base=sum(r['input_packed'] and r['favorite_stage']==0 for r in rows),issues=dict(errors.most_common()),forbidden_calls=calls,full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False,scope='Complete real 30-second all-effect five-member input packing, default growth/no cube and all favorite stages; GPU admission and battle certification remain unproven.')
 result['classification']['diagnostic_sources']=diagnostic_sources(rows)
 result['classification']['reference_readiness_scope']='Conservative recorded native prerequisites; not runtime validation, exhaustive semantics or GPU support'
 result['work_lanes']=work_lanes(result['priorities'])
 (ROOT/'research'/destination).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if not quiet:
  print(json.dumps({k:v for k,v in result.items() if k not in ('profiles','issues','priorities')},ensure_ascii=False));print('Top issues:',dict(errors.most_common(6)))
 return result
if __name__=='__main__':main()
