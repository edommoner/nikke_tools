"""Audit fixed-source Mac gates and separate physical proof;never dispatch GPU."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE=subprocess.check_output(['git','rev-parse','0ae6a14'],cwd=ROOT,text=True).strip()
PRIOR='ba9015c41157c4fa698422ee3638a1ba4f4fba19'
def load(n):return json.loads((P/(n+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(path,commit=SOURCE):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while chunk:=f.read(8*1024*1024):h.update(chunk)
 return h.hexdigest()
def main():
 gates=load('portable-hp-attack-global-gates');assert gates['passed'] and gates['complete'] and len(gates['gates'])==44 and gates['source_commit']==SOURCE
 assert all(r['exit_code']==0 and r['source_commit']==SOURCE for r in gates['gates'])
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
 inventory={}
 for path in subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,text=True).splitlines():
  expected=sha(git_bytes(path));assert file_sha(ROOT/path)==expected,path;inventory[path]=expected
 core=load('portable-combat-metal');parity=core['hp_attack_existing_parity']
 assert core['passed'] and core['gpu_execution_verified'] and core['backend']=='metal'
 assert len(core['cases'])==3020 and len(core['rejected_cases'])==519 and len(core['hp_attack_cpu_regressions'])==185
 assert parity['passed'] and parity['source_commit']==SOURCE and parity['compute_worktree_clean']
 assert parity['prior_inputs']==3331 and parity['current_inputs']==3539 and parity['gpu_execution_reused']
 assert parity['all_old_output_words_equal'] and not parity['changed'] and parity['no_output_normalization']
 for group in ('source_sha256','validation_sha256'):
  for path,digest in core[group].items():assert file_sha(ROOT/path)==sha(git_bytes(path))==digest,path
 fresh=Path(parity['replay_source']);evidence=json.loads((fresh/'evidence.json').read_text());assert evidence['gpu_execution_verified'] and evidence['backend']=='metal'
 for path,digest in evidence['source_sha256'].items():assert sha(git_bytes(path))==digest,path
 for name,field in [('input.bin','input_sha256'),('readback.bin','output_sha256')]:assert file_sha(fresh/name)==evidence[field]==core[field]
 for field,key in [('input_path','input_sha256'),('raw_path','output_sha256')]:assert file_sha(parity[field])==core[key]
 roster=load('portable-roster-battles-metal');assert roster['passed'] and len(roster['cases'])==136 and all(c['passed'] for c in roster['cases']);assert len(roster['known_cpu_difference_cases'])==2
 prior=json.loads(git_bytes('research/portable-roster-battles-metal.json',PRIOR));assert len(prior['cases'])==130
 lookup={(r['character'],r['grown']):r for r in roster['cases']}
 for old in prior['cases']:
  current=lookup[old['character'],old['grown']];assert all(k=='cpu_reference_wall_seconds' or old.get(k)==current.get(k) for k in set(old)|set(current)),old['character']
 for batch in roster['gpu_batches']:
  for field,key in [('input_path','input_sha256'),('readback_path','output_sha256')]:assert file_sha(batch['captured'][field])==batch[key]
 for path,digest in roster['validation_sha256'].items():assert file_sha(ROOT/path)==digest,path
 unit={}
 for name,count in {'unit':258,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(g for g in gates['gates'] if g['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');unit[name]=dict(tests=count,output=text)
 native=load('portable-hp-attack-native');assert native['passed'] and len(native['cases'])==185
 component=load('portable-hp-attack-metal');assert component['passed'] and component['gpu_execution_verified'] and len(component['cases'])==185 and component['actual_rejection_statuses']==[64]*21+[16]*2
 physical=load('portable-hp-attack-physical-metal');assert physical['passed'] and physical['gpu_execution_verified'] and len(physical['cases'])==80
 for report in (component,physical):
  for path,digest in report['source_sha256'].items():assert sha(git_bytes(path))==digest,path
  for path,digest in report['validation_sha256'].items():assert file_sha(ROOT/path)==digest,path
  folder=Path(report['captured'])
  assert file_sha(folder/'input.bin')==report['input_sha256'] and file_sha(folder/'readback.bin')==report['output_sha256']
 hp=load('portable-health-runtime-metal');assert hp['passed'] and len(hp['cases'])==20
 assert load('portable-api-metal')['passed']
 audit=load('portable-catalog-readiness');favorite=load('portable-favorite-readiness');assert audit['own_effect_preflight_passed']==68 and audit['full_character_verified']==0;assert favorite['passed'] and favorite['audited_contexts']==812
 report=dict(passed=True,source_commit=SOURCE,previous_proof_commit=PRIOR,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),all_current_gates_passed=True,
  mac_gates=44,unit_tests=258,core_programs=3539,positive_cases=3020,rejections=519,hp_attack_native_cases=185,additional_physical_metal_cases=80,
  prior3331_inputs_projected_outputs_decoded_native_preserved=True,prior130_profiles_preserved=True,real_profiles=136,native_projection_exact_profiles=134,known_native_hp_gap_profiles=2,
  conditional_hp_metal_cases=20,unit_groups=unit,complete_compute_and_test_source_sha256=inventory,
  own_effect_preflight_passed=68,unadmitted_effects=sum(audit['issues'].values()),favorite_preflight_contexts=favorite['own_effect_preflight_contexts_passed'],all_four_stages_preflight_characters=favorite['all_four_stages_preflight_characters'],
  full_character_verified=0,full_goal_complete=False,normal_ui='CPU',initial_unlocalized_metal_finding_open=True,efficiency_evaluated=False,
  scope='Mac only. Fixed3539 core plus separate80 physical damage inputs. Existing API regression,without new HP-specific API cases. CUDA and transfer remain unverified for this source.')
 (P/'portable-hp-attack-broad-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('44 Mac gates and3539+80 inputs sealed;full goal remains incomplete')
if __name__=='__main__':main()
