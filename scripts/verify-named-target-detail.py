"""Named attack repetition, phase ordering and four real five-member squads.

Reuses the existing independent whole-squad comparator. CPU observations below
only prove that gated effects actually fired; they never feed GPU execution.
"""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from detail_gpu import evaluate_full_many
from gpu_selector import Cuda
from calculator.buff_manager import BuffManager
spec=importlib.util.spec_from_file_location('named_periodic',ROOT/'scripts/verify-periodic-detail.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
E=p.effect

def phase_cases(device,backend):
 names=p.NAMES;owner=names[2];outputs={};rows=[]
 # The stack is 1 at burst_cast and 2 at full_burst_start. The later ATK
 # buff must be excluded from deferred bonus damage, in authored order.
 for mode in ('absent','ordinary','named'):
  effects=[E('coefficient','buff','',0,max_stack=9),E('original attack','damage','sequential_damage:3',100,'enemies_random',event='burst_cast')]
  effects[0]['trigger']['timing']=['battle_start','full_burst_start']
  if mode!='absent':effects.append(E('additional attack','damage','bonus_damage',10,'same_target:original attack' if mode=='named' else 'target',event='burst_cast',scaling='stack_count',scaling_ref='coefficient'))
  effects.append(E('later ATK','buff','atk_pct',200,event='burst_cast',duration=1))
  with p.custom_effects({owner:effects}):
   body=body_for(names,8,True);row=p.full.compare(device,'phase-'+mode,body,module_backend=backend)
  assert row['passed'],row
  outputs[mode]=next(member['gpu'] for member in row['members'] if member['name']==owner)
  rows.append(row)
 extra=outputs['ordinary']-outputs['absent'];repeated=outputs['named']-outputs['absent']
 assert extra>0 and abs(repeated-3*extra)<=2,(outputs,extra,repeated)
 rows.append(dict(name='independent-three-hit-ratio',passed=True,ordinary_extra=extra,named_extra=repeated,rounding_tolerance=2))
 return rows

def real_cases(device,backend):
 rows=[];original=BuffManager.register_damage_handler
 prepared=[]
 for name in ('신데렐라','율하','길로틴','파워'):
  names=[name]+[n for n in ['리타','크라운','앨리스','모더니아'] if n!=name][:4]
  body=body_for(names,100,True);body.update(seed=12345,shooting_policy='character')
  if name=='율하':body['enemy']['patterns']=[dict(id='received-hit-gate',kind='attack',delay=.1,until={'time':1.8},spec=dict(coeff=100,atk=20000,target='slot:1',hits=30,interval=.05,pierce=True))]
  prepared.append((name,body))
 outputs=evaluate_full_many(device,[a.evaluate({**body,'_compile_gpu_detail':True}) for name,body in prepared],module_backend=backend)
 for (name,body),gpu in zip(prepared,outputs):
  observed=[]
  def register(manager,handler):
   def watch(eff,caster,t):
    if caster==name and str(eff.get('target','')).startswith('same_target:'):observed.append(dict(name=eff.get('name'),time=t))
    return handler(eff,caster,t)
   return original(manager,watch)
  with patch.object(BuffManager,'register_damage_handler',register):row=p.full.compare(device,'real-named-'+name,body,module_backend=backend,gpu_result=gpu)
  row['named_bonus_activations']=observed;row['passed']=row['passed'] and bool(observed)
  rows.append(row);print(json.dumps(dict(name=row['name'],passed=row['passed'],activations=len(observed),cpu=row['cpu_total'],gpu=row['gpu_total']),ensure_ascii=True),flush=True)
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');args=ap.parse_args()
 files=['app/named_target_specs.py','app/detail_gpu.py','app/detail_effects.cu','scripts/verify-named-target-detail.py','scripts/verify-extended-detail.py']
 files+=['app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'] if args.backend=='native' else ['app/detail_effects.ptx','app/detail_effects-build.json']
 def hashes():return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
 before=hashes();device=Cuda()
 try:rows=phase_cases(device,args.backend)+real_cases(device,args.backend)
 finally:device.close()
 assert hashes()==before
 report=dict(passed=all(r['passed'] for r in rows),backend=args.backend,cases=rows,source_sha256=before,cpu_trace_used_as_gpu_input=False,scope='Named direct-attack bonus repetitions in the single-aimed-enemy world; periodic ramps excluded')
 (ROOT/f'research/named-target-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
