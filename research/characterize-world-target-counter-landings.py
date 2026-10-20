"""Actual full native battle baseline before connecting the shared GPU bridge."""
import argparse,copy,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('counter_battle_packer',ROOT/'research/compile-world-target-counter-battles.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
from world_frame_native import observe

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'research/portable-world-target-counter-battle-native-contract.json');args=parser.parse_args()
 rows=p.fixtures();results=[]
 with patch('portable_backend.build',side_effect=AssertionError('GPU forbidden')),patch('portable_backend.execute',side_effect=AssertionError('GPU forbidden')),patch('portable_backend.execute_batches',side_effect=AssertionError('GPU forbidden')):
  for case in rows:
   words,_,_=p.compile_case(case);native=observe(case);counter=native['target_counters'];events=counter['events'];completions=[(i,e) for i,e in enumerate(events) if e['event'].startswith('event:target_counter_complete:') and e['phase']=='before']
   plain=copy.deepcopy(case);plain['observe_target_counters']=False
   assert {k:v for k,v in native.items() if k!='target_counters'}==observe(plain),case['name']
   for at,event in completions:
    next_heal=next(i for i in range(at+1,len(events)) if events[i]['event']=='event:heal_received' and events[i]['phase']=='before' and events[i]['time']==event['time'])
    assert at<next_heal
   results.append(dict(name=case['name'],input_sha256=hashlib.sha256(struct.pack('<'+'I'*len(words),*words)).hexdigest(),native=native))
 by={r['name']:r['native'] for r in results}
 for name in ('body','add','add-survives','add-hit-hp'):
  result=by[name+'-completion-versus-lifesteal-order'];assert result['allies'][0]['hp']==984 and len(result['target_counters']['completions'])==1
 assert by['add-completion-versus-lifesteal-order']['target_counters']['completions'][0]['impact']['damage']==50
 assert by['add-hit-hp-completion-versus-lifesteal-order']['target_counters']['completions'][0]['impact']['damage']==1
 part=by['part-50-completion-versus-lifesteal-order'];assert part['allies'][0]['hp']==1000 and part['target_counters']['completions'][0]['impact']['damage']==968
 for name in ('vanish','shield'):
  result=by[name+'-does-not-synthesize-blocked-impact'];assert result['target_counters']['events']==[] and result['target_counters']['resources'][0]['credit']==0 and result['allies'][0]['hp']==500
 assert by['skill-mode-1-pellets-credit-family-skill']['target_counters']['completions']==[]
 assert by['skill-mode-single-physical-weapon-family-positive']['target_counters']['completions'][0]['impact']['family']==0
 assert by['shotgun-three-pellets-credit-second-before-heal']['allies'][0]['hp']==855.3
 old=json.loads((ROOT/'research/portable-world-actor-stack-metal.json').read_text());prior=[]
 for case,stored in zip(p.stack.fixtures(),old['cases']):
  actual=p.stack.status.recipient.state.fields.pool.observe(case);assert json.loads(json.dumps(actual))==stored['native'],case['name'];prior.append(case['name'])
 result=dict(passed=True,scope='Actual full native simulate plus literal-only physical-world input packing;GPU verification separate',source_parent=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),cases=results,old53_native_dictionaries_exact=prior,observer_preserves_all_battle_fields=True,observer_preserved_cases=len(rows),publish_and_synchronous_completion_before_lifesteal=True,parts_use_original_damage_adds_use_clipped_receipt=True,zero_base_attack_has_native_minimum_damage_one=True,physical_skill_mode_impact_family_remains_weapon=True,boss_sentinel_binding_explicit=True,gpu_executions=0,windows_additional_runs=0,cpu_state_used_as_gpu_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');print('Full native counter battles',len(rows),'old53 dictionaries exact;physical inputs packed;GPU0')
if __name__=='__main__':main()
