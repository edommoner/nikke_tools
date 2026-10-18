"""Exhaustive definition inventory plus favorite-stage compilation matrix.
A compiler acceptance is not damage parity. No unsupported definition is dropped.
The goal remains all characters/effects; this report records the incomplete work.
"""
import sys,json,collections,hashlib,copy
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from detail_gpu import UnsupportedDetail
SOURCE=ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json'

def audit():
 raw=json.loads(SOURCE.read_text(encoding='utf-8'));features={key:collections.defaultdict(list) for key in ('types','stats','fields','targets','timings','conditions')}
 definitions=[]
 for character,effects in raw.items():
  if not isinstance(effects,list):continue
  for index,e in enumerate(effects):
   if not isinstance(e,dict):continue
   tag={'character':character,'index':index,'name':e.get('name'),'favorite':e.get('favorite')}
   definitions.append(tag)
   values={'types':[e.get('type','')],'stats':[e.get('stat','')],'fields':list(e),'targets':[json.dumps(e.get('target','self'),ensure_ascii=False,sort_keys=True)],'timings':e.get('trigger',{}).get('timing',[]),'conditions':e.get('trigger',{}).get('condition',[])}
   for key,items in values.items():
    for item in items:features[key][str(item)].append(tag)
 matrix=[]
 for n,data in a.META.items():
  if not isinstance(data,dict) or n.startswith(('_','test_')) or a.spec.is_preview(n):continue
  names=[n]+[x for x in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if x!=n][:4]
  for stage in range(4):
   b=body_for(names);b['profile']['chars'][n]['favorite_stage']=stage
   record={'character':n,'favorite_stage':stage}
   try:a.evaluate({**b,'_compile_gpu_detail':True});record.update(accepted=True)
   except UnsupportedDetail as e:record.update(accepted=False,issues=e.issues)
   except (Exception,SystemExit) as e:record.update(accepted=False,setup_error=str(e))
   matrix.append(record)
 cube_path=SOURCE.parent/'base_stat_tables/cube.json';cube_raw=json.loads(cube_path.read_text(encoding='utf-8'))
 from calculator.buff_manager import BuffManager
 from detail_gpu import compile_effects
 known=['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'];chars=[{'name':n,'_weapon':a.META[n],'skill_levels':{'1':10,'2':10,'3':10}} for n in known]
 cube_matrix=[];upstream_cube_gaps=[]
 for cube,entry in cube_raw.items():
  if cube.startswith('_') or not isinstance(entry,dict):continue
  if entry.get('unsupported'):upstream_cube_gaps.append({'cube':cube,'definition':entry})
  for level in (1,7,15):
   effects=BuffManager._make_cube_effects(None,cube,level)
   record={'cube':cube,'level':level,'upstream_omitted':bool(entry.get('unsupported'))}
   try:compile_effects(chars,[(e,known[0]) for e in effects]);record['gpu_compiler_accepted_emitted_effects']=True
   except UnsupportedDetail as e:record.update(gpu_compiler_accepted_emitted_effects=False,issues=e.issues)
   cube_matrix.append(record)
 reasons=collections.Counter(i.get('reason','') for row in matrix for i in row.get('issues',[]))
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'objective':'all characters and all special effects on GPU','complete':False,'engine_revision':a.REVISION,'raw_definition_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'cube_matrix':cube_matrix,'upstream_cube_gaps':upstream_cube_gaps,'cube_source_sha256':hashlib.sha256(cube_path.read_bytes()).hexdigest(),'raw_characters':len(raw),'raw_definitions':len(definitions),'completion_requirements':['Every available character and favorite variant compiles without omitted effects','Every special effect field, stat, condition, target and event executes on GPU','Upstream omissions are resolved rather than accepted as GPU success','Whole-squad results and event ordering are validated against independent evidence','Normal application requests execute GPU without per-character CPU fallback'],'compiled_context':'one target character in a known five-member squad, skill level 10, no cube, static boss; compilation is not damage parity','favorite_stage_matrix':matrix,'accepted_contexts':sum(r['accepted'] for r in matrix),'total_contexts':len(matrix),'remaining_reasons':dict(reasons.most_common()),'features':{key:{name:{'count':len(items),'definitions':items} for name,items in sorted(entries.items())} for key,entries in features.items()}}
if __name__=='__main__':
 report=audit()
 report['compiler_source_sha256']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['scripts/audit-detail-support.py','scripts/detail_coverage.py','app/detail_gpu.py','app/gpu_combat.py','app/engine_worker.py','app/engine_compat.py']}
 destination=ROOT/'research/detail-all-effects-audit.json';destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ('raw_characters','raw_definitions','accepted_contexts','total_contexts','complete')}))
