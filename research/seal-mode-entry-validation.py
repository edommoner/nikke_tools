"""Completed shared-runtime correctness and isolated efficiency decision; no GPU."""
import datetime,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='39bce8aa5c9c5f29f0653e80fc69855f19ad5ad6'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,r):(P/(n+'.json')).write_text(json.dumps(r,indent=2)+'\n')
def main():
 broad=load('portable-mode-entry-broad-validation');transfer=load('portable-mode-entry-transfer-completed');bench=load('portable-mode-entry-hp-cache-benchmark');parity=load('portable-mode-entry-hp-cache-parity');barrier=load('portable-mode-entry-timing-order')
 for r in (broad,transfer,bench,parity,barrier):assert r['passed'] and r['source_commit']==SOURCE
 assert broad['mac_gates']==47 and broad['unit_tests']==263 and broad['real_profiles']==136
 assert transfer['artifact_transfer_complete'] and transfer['actual_windows_gpu_verification_sessions']==1 and transfer['remaining_verification_processes']==0
 assert barrier['all_current_mac_gates_complete'] and barrier['windows_execution_and_transfer_terminal'] and not barrier['verification_processes']
 assert not bench['production_adopted'] and bench['parity']==parity['parity']
 for label,count in [('core',4070),('physical',80),('health',20)]:
  control,candidate=(parity['parity'][label][n] for n in ('control','candidate'))
  assert control['transport']['cases']==count and candidate['transport']['cases']==count
  assert control['input_sha256']==candidate['input_sha256'] and control['output_sha256']==candidate['output_sha256']
 rows={}
 for name,row in bench['workloads'].items():
  assert row['programs']==1024 and all(len(v)==4 and v[0]['warmup'] and not any(e['warmup'] for e in v[1:]) for v in row['samples'].values())
  ratio=row['median_gpu_seconds']['candidate']/row['median_gpu_seconds']['control'];ranges=row['ranges']
  improves=ratio<=.98 and ranges['candidate'][1]<ranges['control'][0];regresses=ratio>=1.02 and ranges['candidate'][0]>ranges['control'][1]
  assert ratio==row['candidate_to_control_ratio'] and improves==row['improves'] and regresses==row['regresses']
  rows[name]=dict(ratio=ratio,improves=improves,regresses=regresses,ranges=ranges)
 criteria=any(r['improves'] for k,r in rows.items() if k!='ordinary') and not any(r['regresses'] for r in rows.values());assert criteria==bench['criteria_met']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True)
 decision=dict(passed=True,source_commit=SOURCE,evaluated=True,adoption_criteria='At least one feature workload median improves2% with disjoint ranges; no workload regresses2% with disjoint ranges.',criteria_met=criteria,production_change_adopted=False,adoption_pending_new_fixed_source_verification=criteria,workloads=rows,scope=bench['scope'],all4070_plus80_plus20_input_output_equal=True)
 save('portable-mode-entry-efficiency-decision',decision)
 report=dict(passed=True,source_commit=SOURCE,previous_partial_proof_commit='d181fcd9ec57734bac2b3e08c75d828509a8b668',previous_complete_proof_commit='ba9015c41157c4fa698422ee3638a1ba4f4fba19',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  mac_gates=47,unit_tests=263,core_programs=4070,positive_cases=3540,rejections=530,hp_attack_native_cases=185,mode_entry_native_cases=400,pending_reference_native_cases=120,
  additional_metal_physical_cases=80,conditional_hp_metal_cases=20,real_profiles=136,native_projection_exact_profiles=134,known_native_hp_gap_profiles=2,
  prior3539_input_projection_outputs_decoded_native_preserved=True,prior134_successful_profiles_preserved=True,prior2_refused_laplace_profiles_now_verified=True,
  cuda_core_inputs=4070,windows_v76_actual_gpu_sessions=1,windows_v76_elapsed_seconds=transfer['windows_execution']['elapsed_seconds'],transfer_complete=True,artifact_commit=transfer['artifact_commit'],all4070_cross_backend_input_output_bytes_equal=True,
  efficiency_evaluated=True,production_optimization_adopted=False,efficiency_decision=decision,
  own_effect_preflight_passed=broad['own_effect_preflight_passed'],unadmitted_effects=broad['unadmitted_effects'],favorite_preflight_contexts=broad['favorite_preflight_contexts'],all_four_stages_preflight_characters=broad['all_four_stages_preflight_characters'],
  full_character_verified=0,full_goal_complete=False,normal_ui='CPU',initial_unlocalized_metal_finding_open=True,
  proof_reports=['portable-mode-entry-broad-validation.json','portable-mode-entry-transfer-completed.json','portable-mode-entry-hp-cache-parity.json','portable-mode-entry-hp-cache-benchmark.json','portable-mode-entry-efficiency-decision.json'],
  scope='Shared runtime mechanics,136 fixed simple-boss profiles and existing API regression. Full characters/variants and general enemy-world scheduling remain incomplete. Additional80 physical and20 conditional-HP fresh execution is Mac only.')
 save('portable-mode-entry-validation',report);save('portable-combat-checkpoint',report)
 print('Fixed39bce8a correctness sealed; efficiency criteria:',criteria,'production unchanged; full goal remains incomplete')
if __name__=='__main__':main()
