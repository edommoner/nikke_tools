"""Seal frozen common source proofs without GPU execution or tolerance changes."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path('/Users/edo/Documents/ChatGPT/nikke_tools');P=ROOT/'research'
SOURCE='73570451569dce424667e37f4729e475ea6b0a86';PRIOR='89c19e32c7951a839a9db1970403dd299ad66a4b'
def load(n):return json.loads((P/(n+'.json')).read_text())
def git_bytes(p,c=SOURCE):return subprocess.check_output(['git','show',c+':'+p],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
TRACKED=None;PINNED=None
def check_hashes(d,groups=('source_sha256','validation_sha256')):
 global TRACKED,PINNED
 if TRACKED is None:
  TRACKED=set(subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE],cwd=ROOT,text=True).splitlines())
  PINNED=json.loads(git_bytes('research/portable-roster-battles-metal.json',PRIOR))['validation_sha256']
 for group in groups:
  for p,digest in d.get(group,{}).items():
   assert file_sha(ROOT/p)==digest,(group,p)
   if p in TRACKED:assert sha(git_bytes(p))==digest,(group,p)
   else:assert p.startswith('research/upstream/nikke-calc-master/') and PINNED.get(p)==digest,('pinned upstream',group,p)

def main():
 gates=load('portable-enemy-target-global-gates');assert gates['passed'] and gates['complete'] and len(gates['gates'])==52 and gates['source_commit']==SOURCE
 assert all(g['exit_code']==0 and g['source_commit']==SOURCE for g in gates['gates'])
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests','server.mjs'],cwd=ROOT,check=True)
 # Fixed-source research verifiers are hashed below;new CPU proof auditors are outside the compute source.
 inventory={}
 for p in subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE],cwd=ROOT,text=True).splitlines():
  if not (p.startswith(('app/','scripts/','gpu/','tests/')) or p=='server.mjs' or p.startswith('research/') and p.endswith('.py')):continue
  expected=sha(git_bytes(p));assert file_sha(ROOT/p)==expected,p;inventory[p]=expected
 core=load('portable-combat-metal');parity=core['enemy_target_existing_parity'];check_hashes(core)
 assert core['passed'] and core['gpu_execution_verified'] and core['backend']=='metal' and core['duplicate_results_verified'] and 'results' not in core
 assert len(core['cases'])==4112 and len(core['rejected_cases'])==570 and len(core['enemy_target_cpu_regressions'])==548
 assert parity['passed'] and parity['compute_worktree_clean'] and parity['source_commit']==SOURCE and parity['prior_proof_commit']==PRIOR
 assert parity['prior_inputs']==4070 and parity['current_inputs']==4682 and parity['gpu_execution_reused'] and parity['all_old_output_words_equal'] and not parity['changed'] and parity['no_output_normalization']
 fresh=Path(parity['replay_source']);evidence=json.loads((fresh/'evidence.json').read_text());assert evidence['gpu_execution_verified'] and evidence['backend']=='metal';check_hashes(evidence,('source_sha256',))
 for n,k in [('input.bin','input_sha256'),('readback.bin','output_sha256')]:assert file_sha(fresh/n)==evidence[k]==core[k]
 for f,k in [('input_path','input_sha256'),('raw_path','output_sha256')]:assert file_sha(parity[f])==core[k]
 prior=json.loads(git_bytes('research/portable-combat-metal.json',PRIOR))
 assert core['cases'][:3540]==prior['cases'] and core['rejected_cases'][:530]==prior['rejected_cases']
 for k in prior:
  if k=='known_health_cpu_differences':
   resolved={'max-hp-expiry-clamps-to-current-maximum','maximum-hp-expiry-can-reach-adjacent-full','lazy-max-hp-first-consumption-and-derived-percentage'}
   assert core[k]==[r for r in prior[k] if r['name'] not in resolved]
   assert {r['name'] for r in core['resolved_native_hp_differences']}==resolved and all(r['passed'] for r in core['resolved_native_hp_differences'])
  elif k.endswith('_cpu_regressions') or k.startswith('known_'):assert core[k]==prior[k],k
 adopted=parity['adoption4658_parity'];assert adopted['passed'] and adopted['inputs']==4658 and adopted['all_input_words_equal'] and adopted['all_output_words_equal'] and adopted['decoded_cases_and_rejections_preserved'] and not adopted['changed']
 assert len(core['mode_enemy_name_cpu_regressions'])==24
 witness=next(c for c in core['cases'] if c['name']=='enemy-source-time-between-frames');assert [x['targets'] for x in witness['actual']['enemy_selection']]==[[0],[1]]
 longcases=[c for c in core['cases'] if c['name'].startswith('enemy-long-rng-')];assert len(longcases)==2
 for c in longcases:assert (c['actual']['enemy_rng']['draws'],c['actual']['enemy_rng']['index'])==(627,3)
 roster=load('portable-roster-battles-metal');old=json.loads(git_bytes('research/portable-roster-battles-metal.json',PRIOR));assert roster['passed'] and all(c['passed'] for c in roster['cases']) and len(old['cases'])==136
 assert roster['known_cpu_difference_cases']==old['known_cpu_difference_cases'] and len(roster['known_cpu_difference_cases'])==2
 current={(c['character'],c['grown']):c for c in roster['cases']};preserved=[]
 for c in old['cases']:
  now=current[c['character'],c['grown']];assert c['passed'] and all(k=='cpu_reference_wall_seconds' or c.get(k)==now.get(k) for k in set(c)|set(now)),c['character'];preserved.append([c['character'],c['grown']])
 new=[c for c in roster['cases'] if (c['character'],c['grown']) not in {(o['character'],o['grown']) for o in old['cases']}]
 assert all(not c['differences'] for c in new)
 for batch in roster['gpu_batches']:
  for f,k in [('input_path','input_sha256'),('readback_path','output_sha256')]:assert file_sha(batch['captured'][f])==batch[k]
 check_hashes(roster,('validation_sha256',))
 units={}
 for name,count in {'unit':278,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(g for g in gates['gates'] if g['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
 row=next(g for g in gates['gates'] if g['name']=='http-seed-policy');text=Path(row['log']).read_text();assert any(x in text.splitlines() for x in ('# pass 4','ℹ pass 4')) and any(x in text.splitlines() for x in ('# fail 0','ℹ fail 0')) and any(x in text.splitlines() for x in ('# skipped 0','ℹ skipped 0')) and any(x in text.splitlines() for x in ('# cancelled 0','ℹ cancelled 0'));units['http-seed-policy']=dict(tests=4,output=text)
 for n,count in [('portable-enemy-victims-native',548),('portable-enemy-target-spec-native',51),('portable-taunt-edge-native-study',25),('portable-hp-attack-native',185),('portable-mode-entry-entry-native',400),('portable-mode-entry-pending-native',120)]:
  d=load(n);assert d['passed'] and len(d['cases'])==count,(n,d.keys());check_hashes(d,('validation_sha256',))
 rng=load('portable-target-rng-metal');assert rng['passed'] and rng['gpu_execution_verified'] and len(rng['cases'])==31
 for path,digest in rng['source_sha256_local'].items():assert file_sha(ROOT/path)==sha(git_bytes(path))==digest,path
 folder=Path(rng['captured'])
 for name,key in [('input.bin','input_sha256'),('readback.bin','output_sha256')]:assert file_sha(folder/name)==rng[key]
 http=load('portable-enemy-target-http-metal');assert http['passed'] and http['test_server_exited'] and not http['original4317_service_restarted'] and not http['observer_changes_math'];check_hashes(http,('validation_sha256',))
 folder=Path(http['captured']);assert file_sha(folder/'input.bin')==http['expected_input_sha256'] and file_sha(folder/'readback.bin')==http['expected_output_sha256']
 physical=load('portable-hp-attack-physical-metal');assert physical['passed'] and physical['gpu_execution_verified'] and len(physical['cases'])==80;check_hashes(physical)
 folder=Path(physical['captured']);assert file_sha(folder/'input.bin')==physical['input_sha256'] and file_sha(folder/'readback.bin')==physical['output_sha256']
 hp=load('portable-health-runtime-metal');assert hp['passed'] and len(hp['cases'])==20
 assert load('portable-api-metal')['passed']
 preservation=load('portable-enemy-target-scalar-roster-parity');assert preservation['passed'] and preservation['profiles']==158 and preservation['all158_input_words_equal'] and preservation['all158_output_words_equal']
 audit=load('portable-catalog-readiness');fav=load('portable-favorite-readiness');assert audit['full_character_verified']==0 and fav['passed'] and fav['audited_contexts']==812
 result=dict(audit_tool_sha256=sha(Path(__file__).read_bytes()),passed=True,all_current_gates_passed=True,source_commit=SOURCE,previous_proof_commit=PRIOR,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),mac_gates=52,unit_tests=278,node_tests=4,core_programs=4682,positive_cases=4112,rejections=570,enemy_target_native_cases=548,prior4070_inputs_outputs_decoded_preserved=True,prior4658_input_output_decoded_preserved=True,resolved_finite_hp_exceptions=3,mode_enemy_name_native_cases=24,prior136_successful_profiles_preserved=True,real_profiles=len(roster['cases']),new_profiles=[[c['character'],c['grown']] for c in new],native_projection_exact_profiles=len(roster['cases'])-2,known_native_hp_gap_profiles=2,long_rng_cases=2,long_rng_draws=627,source_time_boundary_fixed=True,http_uint64_decimal_seed_exact=True,additional_physical_metal_cases=80,conditional_hp_metal_cases=20,unit_groups=units,complete_compute_and_test_source_sha256=inventory,pinned_upstream_source_sha256={p:h for p,h in PINNED.items() if p.startswith('research/upstream/')},own_effect_preflight_passed=audit['own_effect_preflight_passed'],unadmitted_effects=sum(audit['issues'].values()),favorite_preflight_contexts=fav['own_effect_preflight_contexts_passed'],all_four_stages_preflight_characters=fav['all_four_stages_preflight_characters'],full_character_verified=0,full_goal_complete=False,normal_ui='CPU',initial_unlocalized_metal_finding_open=True,efficiency_evaluated=True,scope='Fixed-source Mac proof only.CUDA and transfer not yet verified for this source;general enemy-world scheduler,revive and control remain incomplete.')
 (P/'portable-enemy-target-scalar-broad-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('52 Mac gates sealed;full goal remains incomplete',len(roster['cases']),'roster profiles')
if __name__=='__main__':main()
