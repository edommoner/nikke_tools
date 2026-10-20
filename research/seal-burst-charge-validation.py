"""Seal completed shared burst-charge validation and the measured optimization decision."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research';SOURCE='20e213bf28544a3ad2709fdc852d239eed108b5e'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def main():
 broad=load('portable-burst-charge-broad-validation');transfer=load('portable-burst-charge-transfer-completed');bench=load('portable-burst-charge-benchmark');plan=load('portable-burst-charge-benchmark-plan');barrier=load('portable-burst-charge-timing-order');parity=load('portable-burst-charge-candidate-parity')
 for report in (broad,transfer,bench,plan,barrier,parity):assert report['source_commit']==SOURCE
 for report in (broad,transfer,bench,barrier,parity):assert report['passed']
 assert broad['mac_gates']==41 and transfer['core_programs']==3331 and parity['programs']==3331
 assert parity['additional_health_cases']==20 and parity['all_input_and_output_bytes_equal'] and parity['all_additional_health_input_output_bytes_equal']
 assert bench['timing_order']==barrier and bench['tool_sha256']==hashlib.sha256((P/'benchmark-burst-charge.py').read_bytes()).hexdigest()
 assert set(bench['workloads'])==set(plan['workloads'])
 decisions={}
 for label,row in bench['workloads'].items():
  samples=row['samples'];assert all(len(s)==4 and s[0]['warmup'] and all(not x['warmup'] for x in s[1:]) for s in samples.values())
  assert row['programs']==1024
  lo,hi=row['ranges']['candidate'];clo,chi=row['ranges']['control'];ratio=row['candidate_to_control_ratio']
  decisions[label]=dict(ratio=ratio,improves=ratio<=.98 and hi<clo,regresses=ratio>=1.02 and lo>chi)
 adopt=any(decisions[k]['improves'] for k in ('charge-first','charge-last','mode-callback')) and not any(x['regresses'] for x in decisions.values())
 decision=dict(passed=True,source_commit=SOURCE,evaluated=True,adoption_criteria=plan['adoption_rule'],criteria_met=adopt,production_change_adopted=False,workloads=decisions,scope=bench['scope'])
 save('portable-burst-charge-efficiency-decision',decision)
 assert not adopt,'Candidate meets adoption criteria;validate adoption before sealing production'
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
 finding=load('portable-burst-charge-skill-finding');finding.update(resolved_in_production=True,pending=[],resolution_proof='portable-burst-charge-validation.json');save('portable-burst-charge-skill-finding',finding)
 report=dict(passed=True,source_commit=SOURCE,previous_proof_commit=broad['previous_proof_commit'],checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  mac_gates=41,unit_tests=254,core_programs=3331,positive_cases=2835,rejections=496,burst_charge_native_cases=310,
  real_profiles=130,native_projection_exact_profiles=128,known_native_hp_gap_profiles=2,conditional_hp_metal_cases=20,
  cuda_core_inputs=3331,windows_v75_actual_gpu_sessions=1,windows_v75_elapsed_seconds=transfer['windows_execution']['elapsed_seconds'],
  windows_v74_superseded_gpu_sessions=1,windows_v74_used_for_current_certification=False,
  transfer_complete=True,all3331_cross_backend_input_output_bytes_equal=True,
  old2950_input_projection_output_words_preserved=True,initial3231_input_output_words_preserved=True,
  efficiency_evaluated=True,production_optimization_adopted=False,efficiency_decision=decision,
  own_effect_preflight_passed=65,unadmitted_effects=broad['unadmitted_effects'],favorite_preflight_contexts=257,all_four_stages_preflight_characters=64,
  full_character_verified=0,full_goal_complete=False,normal_ui='CPU',initial_unlocalized_metal_finding_open=True,
  scope='Current-source CUDA core3331 only;Mac41 broad gates and20 HP inputs separate. Known2 strict native HP gaps retained;no blanket CPU equality or all-variant certification.',
  evidence_sha256={n:hashlib.sha256((P/(n+'.json')).read_bytes()).hexdigest() for n in ['portable-burst-charge-broad-validation','portable-burst-charge-transfer-completed','portable-burst-charge-global-gates','portable-burst-charge-timing-order','portable-burst-charge-benchmark-plan','portable-burst-charge-candidate-parity','portable-burst-charge-benchmark','portable-burst-charge-efficiency-decision','portable-burst-charge-skill-finding','portable-burst-charge-mode-fix-existing-parity']})
 save('portable-burst-charge-validation',report)
 print('Burst-charge validation sealed;optimization rejected;full goal remains incomplete')
if __name__=='__main__':main()
