import importlib.util,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'app')]
spec=importlib.util.spec_from_file_location('positive_random',ROOT/'scripts/verify-random-target-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
spec=importlib.util.spec_from_file_location('raw_cleanse_injection',ROOT/'scripts/verify-cleanse-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from calculator.buff_manager import BuffManager
from unittest.mock import patch
rows=[];original=BuffManager._resolve_target
for label,body,effects in v.real_cases():
 selected=[]
 def resolve(self,target,caster):
  result=original(self,target,caster)
  if isinstance(target,str) and target.startswith('allies_random_with_debuff:'):selected.append(list(result))
  return result
 state=random.getstate()
 try:
  with c.injected_effects(effects),c.v.observe() as cleanups,patch.object(BuffManager,'_resolve_target',resolve):cpu=v.v.v.c.a.evaluate(body)
 finally:random.setstate(state)
 changed=0
 for call in cleanups:
  after={ab['uid']:ab for ab in call['after']}
  changed+=sum(ab['polarity']=='harmful' and (ab['uid'] not in after or ab['targets']!=after[ab['uid']]['targets']) for ab in call['before'])
 row=dict(name=label,seed=body['seed'],mode=body['burst_gauge_mode'],positive_random_picks=sum(bool(x) for x in selected),changed_harmful_instances=changed,cpu_total=cpu['total_damage'])
 assert row['positive_random_picks']>0 and changed>0,row
 rows.append(row);print(json.dumps(row),flush=True)
(ROOT/'research/detail-random-real-positive.json').write_text(json.dumps({'passed':True,'cpu_reference_only':True,'cases':rows},indent=2)+'\n',encoding='utf-8')
