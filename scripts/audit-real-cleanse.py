"""Show that new raw characters actually remove an authored harmful effect."""
import copy,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('real_cleanse',ROOT/'scripts/verify-cleanse-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def main():
 rows=[]
 for name,body,effects,controls in v.real_cases():
  with v.injected_effects(effects),v.v.c.configured(controls):
   compiled=v.v.c.a.evaluate({**body,'_compile_gpu_detail':True})
   with v.v.c.observe() as (_,_,operations),v.v.observe() as cleanups:result=v.v.c.a.evaluate(body)
  changed=0
  for call in cleanups:
   after={ab['uid']:ab for ab in call['after']}
   changed+=sum(ab['polarity']=='harmful' and (ab['uid'] not in after or ab['targets']!=after[ab['uid']]['targets']) for ab in call['before'])
  row=dict(name=name,input=body,injected_effects=effects,authored_controls=controls,hold_events=operations['holds'],compiler_rows=len(compiled['program']['effects']),cleanse_calls=len(cleanups),changed_harmful_instances=changed,cpu_total=result['total_damage'])
  rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
  assert changed>0,name
 files=['scripts/audit-real-cleanse.py','scripts/verify-cleanse-detail.py','scripts/audit-debuff-cleanse.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/'research/detail-real-cleanse-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
