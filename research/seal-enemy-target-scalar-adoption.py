"""Seal measured candidate and both canonical backend proofs without GPU work."""
import datetime,hashlib,json,statistics,subprocess
from pathlib import Path
R=Path('/Users/edo/Documents/ChatGPT/nikke_tools');P=R/'research'
S='73570451569dce424667e37f4729e475ea6b0a86';B='782a13ca6249a52c30003b88870420cbd5b2f7ee'
def load(n):return json.loads((P/(n+'.json')).read_text())
def git(c,p):return subprocess.check_output(['git','show',c+':'+p],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
b=load('portable-enemy-target-scalar-benchmark');assert b['passed'] and b['criteria_met'] and b['source_commit']==B
barrier=b['timing_order'];assert barrier['passed'] and barrier['source_commit']==B and barrier['all_current_mac_gates_complete'] and barrier['windows_execution_and_transfer_terminal'] and not barrier['verification_processes']
a=json.loads((Path(b['captured'])/'candidate-source-audit.json').read_text());assert a['passed'] and a['changed_files']==['gpu/enemy_target_runtime.slang'] and a['runtime_layout_unchanged']
assert sha(git(S,'gpu/enemy_target_runtime.slang'))==a['candidate_module_sha256']==sha((R/'gpu/enemy_target_runtime.slang').read_bytes())
assert a['tool_sha256']==b['tool_sha256']==sha(git(S,'research/benchmark-enemy-target-scalar.py'))
paths=subprocess.check_output(['git','diff','--name-only',B,S,'--','gpu'],cwd=R,text=True).splitlines();assert paths==a['changed_files']
assert git(B,'gpu/event_runtime.slang')==git(S,'gpu/event_runtime.slang')
rows={}
for name,w in b['workloads'].items():
 assert w['programs']==1024
 med={};ranges={};digests=set()
 for side,samples in w['samples'].items():
  assert len(samples)==4 and sum(s['warmup'] for s in samples)==1
  for s in samples:
   assert s['gpu_execution_verified'] and s['backend']=='metal' and s['transport']['command_status']=='completed' and s['transport']['device']=='Apple M5'
   digests.add((s['input_sha256'],s['output_sha256']))
  times=[s['transport']['gpu_seconds'] for s in samples if not s['warmup']]
  assert len(times)==3;med[side]=statistics.median(times);ranges[side]=[min(times),max(times)]
 assert len(digests)==1 and med==w['median_gpu_seconds'] and ranges==w['ranges']
 ratio=med['candidate']/med['control'];improves=ratio<=0.98 and ranges['candidate'][1]<ranges['control'][0];regresses=ratio>=1.02 and ranges['candidate'][0]>ranges['control'][1]
 assert ratio==w['candidate_to_control_ratio'] and improves==w['improves'] and regresses==w['regresses']
 rows[name]=dict(candidate_to_control_ratio=ratio,improves=improves,regresses=regresses)
assert len(rows)==7 and not any(w['regresses'] for w in rows.values()) and any(rows[n]['improves'] for n in ('random-dense','rank-dense','slot-dense'))
for group in b['parity'].values():
 c=group['control'];v=group['candidate'];assert c['gpu_execution_verified'] and v['gpu_execution_verified']
 assert c['input_sha256']==v['input_sha256'] and c['output_sha256']==v['output_sha256']
core=load('portable-enemy-target-scalar-canonical-core');assert core['passed'] and core['source_commit']==S and core['full4682_input_words_equal'] and core['full4682_output_words_equal']
assert all(x['equal'] and x['canonical_normalized']==x['isolated_normalized'] for x in core['generated_body_comparison'].values())
mac=load('portable-enemy-target-scalar-broad-validation');assert mac['passed'] and mac['source_commit']==S and mac['mac_gates']==52 and mac['real_profiles']==158
roster=load('portable-enemy-target-scalar-roster-parity');assert roster['passed'] and roster['source_commit']==S and roster['all158_input_words_equal'] and roster['all158_output_words_equal'] and roster['changed_gpu_source_paths']==a['changed_files']
cuda=load('portable-enemy-target-scalar-transfer-completed');assert cuda['passed'] and cuda['source_commit']==S and cuda['core_programs']==4682 and cuda['remaining_verification_processes']==0
assert cuda['input_sha256']==core['input_sha256'] and cuda['output_sha256']==core['output_sha256']
assert cuda['normalized_generated_sha256']=={k:v['canonical_normalized'] for k,v in core['generated_body_comparison'].items()}
terminal=load('portable-enemy-target-scalar-timing-order');assert terminal['passed'] and terminal['source_commit']==S and terminal['all_current_mac_gates_complete'] and terminal['windows_execution_and_transfer_terminal'] and not terminal['verification_processes']
result=dict(passed=True,production_adopted=True,source_commit=S,baseline_source_commit=B,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),changed_gpu_paths=paths,runtime_and_io_layout_unchanged=True,benchmark_only_after_baseline_all_gates_and_transfer_terminal=True,isolated_and_canonical_generated_bodies_equal=True,canonical_metal4682_all_input_output_words_equal_to_baseline=True,canonical_cuda4682_all_input_output_words_equal_to_metal=True,canonical_metal_roster158_all_input_output_words_equal_to_baseline=True,mac_gates=52,unit_tests=278,node_tests=4,workloads=rows,cuda_gpu_invocations=1,cuda_elapsed_seconds=cuda['windows_execution']['elapsed_seconds'],no_extra_gpu_execution_for_this_audit=True,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,initial_unlocalized_metal_finding_open=True,scope='M5 local synthetic enemy-selection workloads only;no CUDA speed,full-roster speed or physical peak-memory claim. General enemy-world scheduler,manual controls,revive and remaining effects are incomplete.')
(P/'portable-enemy-target-scalar-adoption.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Measured scalar candidate adopted only after canonical Metal52 and fresh CUDA4682 exact parity;full goal remains incomplete')
